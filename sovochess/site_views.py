# news, legal pages, account stuff and articles
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from .models import Article, Game, Preparation, SavedGame

ATOM = '{http://www.w3.org/2005/Atom}'
NEWS_CACHE_KEY = 'news:v2'
NEWS_STALE_KEY = 'news:stale:v2'
PER_SOURCE = 8  # so one site cant fill the whole page


# news: only headlines + links, no article text or pics (see NEWS_FEEDS in settings)

def _parse_date(text):
    if not text:
        return None
    text = text.strip()
    try:
        return parsedate_to_datetime(text)  # rss dates
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00'))  # atom dates
    except ValueError:
        return None


def _text(el):
    return html.unescape(re.sub(r'<[^>]+>', '', (el.text or '') if el is not None else '')).strip()


def _fetch_feed(feed):
    req = urllib.request.Request(feed['url'], headers={'User-Agent': 'SovoChess news reader (+headlines only)'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        root = ET.fromstring(resp.read(2_000_000))

    items = []
    for item in root.iter('item'):  # rss
        link = (item.findtext('link') or '').strip()
        items.append({'title': _text(item.find('title')), 'url': link,
                      'date': _parse_date(item.findtext('pubDate'))})
    for entry in root.iter(f'{ATOM}entry'):  # atom
        link_el = entry.find(f"{ATOM}link[@rel='alternate']")
        if link_el is None:  # cant use `or` here, empty elements count as False
            link_el = entry.find(f'{ATOM}link')
        items.append({'title': _text(entry.find(f'{ATOM}title')),
                      'url': link_el.get('href', '') if link_el is not None else '',
                      'date': _parse_date(entry.findtext(f'{ATOM}published') or entry.findtext(f'{ATOM}updated'))})

    out = []
    for it in items[:15]:
        if it['title'] and it['url'].startswith('https://'):
            out.append({'title': it['title'][:200], 'url': it['url'], 'source': feed['name'],
                        'timestamp': it['date'].timestamp() if it['date'] else 0})
    return out


def get_news(limit=40):
    news = cache.get(NEWS_CACHE_KEY)
    if news is not None:
        return news[:limit]

    feeds = getattr(settings, 'NEWS_FEEDS', [])
    items = []
    with ThreadPoolExecutor(max_workers=max(1, len(feeds))) as pool:
        for result in pool.map(lambda f: _safe_fetch(f), feeds):
            items.extend(result)

    if not items:  # every feed failed so just show the old ones
        return cache.get(NEWS_STALE_KEY, [])

    # newest first
    items.sort(key=lambda i: i['timestamp'], reverse=True)
    picked, per_source = [], {}
    for it in items:
        if per_source.get(it['source'], 0) < PER_SOURCE:
            picked.append(it)
            per_source[it['source']] = per_source.get(it['source'], 0) + 1

    cache.set(NEWS_CACHE_KEY, picked, 60 * 30)  # fetch again every 30 min
    cache.set(NEWS_STALE_KEY, picked, 60 * 60 * 24 * 7)
    return picked[:limit]


def _safe_fetch(feed):
    try:
        return _fetch_feed(feed)
    except Exception:  # dont want a broken feed to break the home page
        return []


def news_json(request):
    return JsonResponse({'items': get_news(int(request.GET.get('limit', 8)) if request.GET.get('limit', '').isdigit() else 8)})


def news_page(request):
    items = get_news(limit=60)
    for it in items:
        it['date'] = datetime.fromtimestamp(it['timestamp'], tz=dt_timezone.utc) if it['timestamp'] else None
    feeds = getattr(settings, 'NEWS_FEEDS', [])
    source = request.GET.get('source', '')
    if source in [f['name'] for f in feeds]:
        items = [it for it in items if it['source'] == source]
    return render(request, 'news.html', {
        'items': items,
        'feeds': feeds,
        'source': source,
        'guides': Article.objects.filter(is_published=True)[:4],
    })


# legal pages

def privacy(request):
    return render(request, 'legal/privacy.html')


def terms(request):
    return render(request, 'legal/terms.html')


def licenses(request):
    return render(request, 'legal/licenses.html')


# account page: download your data / delete account (gdpr)

@login_required
def account(request):
    return render(request, 'account.html', {
        'saved_count': SavedGame.objects.filter(owner=request.user).count(),
        'played_count': Game.objects.filter(white_player=request.user).count(),
        'prep_count': Preparation.objects.filter(owner=request.user).count(),
    })


@login_required
def account_export(request):
    user = request.user
    data = {
        'account': {
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'rating': user.current_rating,
        },
        'profile': None,
        'played_games': [],
        'library': [],
    }
    profile = getattr(user, 'profile', None)
    if profile:
        data['profile'] = {'total_games': profile.total_games, 'total_wins': profile.total_wins,
                           'total_losses': profile.total_losses, 'favourite_opening': profile.favourite_opening}
    for g in Game.objects.filter(white_player=user).prefetch_related('moves'):
        data['played_games'].append({
            'id': g.id, 'date': g.date_played.isoformat(), 'result': g.result, 'termination': g.termination,
            'time_control': g.time_control_label, 'opening': g.opening_name,
            'moves': [m.from_square + m.to_square for m in g.moves.order_by('move_number')],
        })
    for s in SavedGame.objects.filter(owner=user).select_related('collection'):
        data['library'].append({'collection': s.collection.name if s.collection else None, 'notes': s.notes,
                                'pgn': s.pgn, 'added': s.created.isoformat()})
    data['preparations'] = [{'title': p.title, 'side': p.side, 'opponent': p.opponent, 'notes': p.notes,
                             'pgn': p.pgn, 'start_fen': p.start_fen, 'updated': p.updated.isoformat()}
                            for p in Preparation.objects.filter(owner=user)]

    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="sovochess-data-{user.username}.json"'
    return response


@login_required
@require_POST
def account_delete(request):
    if not request.user.check_password(request.POST.get('password', '')):
        messages.error(request, "That password isn't right, so your account was not deleted.")
        return redirect('account')
    user = request.user
    logout(request)
    user.delete()  # deletes all their games, library etc too
    messages.success(request, 'Your account and all of its data have been deleted.')
    return redirect('home')


# articles (read page)

BOARD_RE = re.compile(r'^\[board (.*)\]$')
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def _inline(text):
    # escape the text first, then only *italic* is allowed
    return mark_safe(re.sub(r'\*([^*\n]+)\*', r'<em>\1</em>', html.escape(text)))


def article_blocks(body):
    # splits the article text into paragraphs, headings, quotes and boards
    blocks = []
    for chunk in re.split(r'\n\s*\n', body.strip()):
        chunk = chunk.strip()
        board = BOARD_RE.match(chunk)
        if board:
            attrs = dict(ATTR_RE.findall(board.group(1)))
            blocks.append({'type': 'board', 'fen': attrs.get('fen', ''), 'moves': attrs.get('moves', ''),
                           'caption': attrs.get('caption', ''), 'orientation': attrs.get('orientation', 'white')})
        elif chunk.startswith('## '):
            blocks.append({'type': 'h2', 'html': _inline(chunk[3:])})
        elif chunk.startswith('> '):
            blocks.append({'type': 'quote', 'html': _inline(chunk[2:])})
        else:
            blocks.append({'type': 'p', 'html': _inline(chunk)})
    return blocks


def articles(request):
    items = Article.objects.filter(is_published=True)
    category = request.GET.get('c', '')
    if category in dict(Article.CATEGORY_CHOICES):
        items = items.filter(category=category)
    items = list(items)
    return render(request, 'articles.html', {
        'lead': items[0] if items else None,
        'rest': items[1:],
        'categories': Article.CATEGORY_CHOICES,
        'active': category,
    })


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    more = Article.objects.filter(is_published=True).exclude(pk=article.pk)[:3]
    return render(request, 'article_detail.html', {
        'article': article, 'blocks': article_blocks(article.body), 'more': more,
    })
