# library, pgn import/export, analysis board + prep
import json
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Collection, Preparation, SavedGame
from .views import identify_opening_str

MAX_IMPORT_GAMES = 500          # per import
MAX_PGN_CHARS = 100_000         # per game
MAX_LIBRARY_GAMES = 5000        # per user
HEADER_FIELDS = {               # PGN tag -> (model field, max length)
    'White': ('white', 100), 'Black': ('black', 100), 'Result': ('result', 10),
    'Event': ('event', 150), 'Date': ('date', 20), 'ECO': ('eco', 10), 'Opening': ('opening', 150),
}
UCI_RE = re.compile(r'^([a-h][1-8][a-h][1-8][qrbn]?)( [a-h][1-8][a-h][1-8][qrbn]?)*$')


def _clean(value, max_len):
    value = str(value or '').strip()
    return '' if value in ('?', '-') else value[:max_len]


@login_required
def library(request):
    games = SavedGame.objects.filter(owner=request.user).select_related('collection')
    collections = Collection.objects.filter(owner=request.user).annotate(n=Count('games'))

    active = request.GET.get('collection', '')
    if active == 'played':
        games = games.filter(source='played')
    elif active == 'none':
        games = games.filter(collection__isnull=True, source='import')
    elif active.isdigit():
        games = games.filter(collection_id=int(active))

    q = request.GET.get('q', '').strip()
    if q:
        games = games.filter(Q(white__icontains=q) | Q(black__icontains=q) | Q(event__icontains=q)
                             | Q(opening__icontains=q) | Q(eco__iexact=q) | Q(notes__icontains=q))

    total = SavedGame.objects.filter(owner=request.user).count()
    return render(request, 'library.html', {
        'games': games[:300],
        'shown_limited': games.count() > 300,
        'collections': collections,
        'active': active,
        'q': q,
        'total': total,
        'played_count': SavedGame.objects.filter(owner=request.user, source='played').count(),
    })


@login_required
@require_POST
def library_import(request):
    # games come in already split up by the js in the browser
    try:
        data = json.loads(request.body)
        incoming = data['games']
        assert isinstance(incoming, list)
    except (ValueError, KeyError, AssertionError, TypeError):
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    if not incoming:
        return JsonResponse({'error': 'No games found in that PGN.'}, status=400)
    if len(incoming) > MAX_IMPORT_GAMES:
        return JsonResponse({'error': f'Please import at most {MAX_IMPORT_GAMES} games at a time.'}, status=400)
    if SavedGame.objects.filter(owner=request.user).count() + len(incoming) > MAX_LIBRARY_GAMES:
        return JsonResponse({'error': f'Your library is limited to {MAX_LIBRARY_GAMES} games.'}, status=400)

    collection = None
    new_name = _clean(data.get('new_collection'), 80)
    if new_name:
        collection, _ = Collection.objects.get_or_create(owner=request.user, name=new_name)
    elif str(data.get('collection_id', '')).isdigit():
        collection = get_object_or_404(Collection, id=int(data['collection_id']), owner=request.user)

    to_create = []
    for item in incoming:
        if not isinstance(item, dict):
            continue
        pgn = str(item.get('pgn', '')).strip()
        if not pgn or len(pgn) > MAX_PGN_CHARS:
            continue
        headers = item.get('headers') if isinstance(item.get('headers'), dict) else {}
        fields = {field: _clean(headers.get(tag), n) for tag, (field, n) in HEADER_FIELDS.items()}

        # no Opening tag, try our own openings list instead
        uci = str(item.get('uci', ''))[:400].strip()
        if not fields['opening'] and uci and UCI_RE.match(uci):
            name = identify_opening_str(uci)
            fields['opening'] = '' if name == 'Unknown Opening' else name

        try:
            plies = max(0, min(int(item.get('plies', 0)), 2000))
        except (TypeError, ValueError):
            plies = 0
        to_create.append(SavedGame(owner=request.user, collection=collection, source='import',
                                   pgn=pgn, ply_count=plies, **fields))

    SavedGame.objects.bulk_create(to_create)
    return JsonResponse({'imported': len(to_create), 'skipped': len(incoming) - len(to_create),
                         'collection_id': collection.id if collection else None})


@login_required
def saved_game(request, pk):
    game = get_object_or_404(SavedGame, pk=pk, owner=request.user)
    if request.method == 'POST':
        game.notes = request.POST.get('notes', '')[:10_000]
        col = request.POST.get('collection', '')
        game.collection = (get_object_or_404(Collection, id=int(col), owner=request.user)
                           if col.isdigit() else None)
        game.save()
        if request.headers.get('x-requested-with') == 'fetch':
            return JsonResponse({'ok': True})
        messages.success(request, 'Saved.')
        return redirect('saved_game', pk=game.pk)
    return render(request, 'analysis.html', _analysis_context(request, saved_game=game))


@login_required
@require_POST
def saved_game_delete(request, pk):
    game = get_object_or_404(SavedGame, pk=pk, owner=request.user)
    game.delete()
    messages.success(request, 'Game deleted from your library.')
    return redirect('library')


@login_required
@require_POST
def save_analysis(request):
    pgn = request.POST.get('pgn', '').strip()
    if not pgn or len(pgn) > MAX_PGN_CHARS:
        messages.error(request, 'There was nothing to save.')
        return redirect('analysis')
    headers = dict(re.findall(r'^\[(\w+)\s+"((?:[^"\\]|\\.)*)"\]\s*$', pgn, flags=re.M))
    fields = {field: _clean(headers.get(tag), n) for tag, (field, n) in HEADER_FIELDS.items()}
    try:
        plies = max(0, min(int(request.POST.get('plies', 0)), 2000))
    except ValueError:
        plies = 0
    game = SavedGame.objects.create(owner=request.user, source='import', pgn=pgn, ply_count=plies, **fields)
    messages.success(request, 'Saved to your library.')
    return redirect('saved_game', pk=game.pk)


@login_required
@require_POST
def collection_create(request):
    name = _clean(request.POST.get('name'), 80)
    if name:
        try:
            c = Collection.objects.create(owner=request.user, name=name,
                                          description=_clean(request.POST.get('description'), 200))
            return redirect(f"/library/?collection={c.id}")
        except IntegrityError:
            messages.error(request, 'You already have a collection with that name.')
    return redirect('library')


@login_required
@require_POST
def collection_delete(request, pk):
    c = get_object_or_404(Collection, pk=pk, owner=request.user)
    if request.POST.get('with_games'):
        c.games.all().delete()
    c.delete()
    messages.success(request, f'Collection "{c.name}" deleted.')
    return redirect('library')


@login_required
def library_export(request):
    # download one game, a collection or everything as a .pgn
    games = SavedGame.objects.filter(owner=request.user).order_by('created')
    name = 'sovochess-library'
    if request.GET.get('game', '').isdigit():
        games = games.filter(pk=int(request.GET['game']))
        name = f'sovochess-game-{request.GET["game"]}'
    elif request.GET.get('collection', '').isdigit():
        c = get_object_or_404(Collection, pk=int(request.GET['collection']), owner=request.user)
        games = games.filter(collection=c)
        name = re.sub(r'[^A-Za-z0-9_-]+', '-', c.name).strip('-') or 'collection'
    body = '\n\n'.join(g.pgn.strip() for g in games) + '\n'
    response = HttpResponse(body, content_type='application/x-chess-pgn; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{name}.pgn"'
    return response


MAX_PREPS = 300
MAX_PREP_PGN_CHARS = 300_000
FEN_RE = re.compile(r'^[1-8pnbrqkPNBRQK/]{15,71} [wb] [KQkq-]{1,4} [a-h1-8-]{1,2} \d+ \d+$')


def _analysis_context(request, saved_game=None, prep=None):
    ctx = {'saved_game': saved_game, 'prep': prep, 'preps': [], 'collections': []}
    if request.user.is_authenticated:
        ctx['preps'] = Preparation.objects.filter(owner=request.user).only('id', 'title', 'side', 'opponent', 'updated')
        ctx['collections'] = Collection.objects.filter(owner=request.user)
    ctx['page_data'] = {
        'mode': 'game' if saved_game else 'prep' if prep else 'free',
        'loggedIn': request.user.is_authenticated,
        'pieces': static('img/chesspieces/wikipedia/'),
        'stockfish': static('vendor/stockfish/stockfish-19-lite-single.js'),
        'prep': {'id': prep.id, 'pgn': prep.pgn, 'startFen': prep.start_fen, 'side': prep.side} if prep else None,
        'game': {'id': saved_game.id, 'pgn': saved_game.pgn,
                 'saveUrl': reverse('saved_game', args=[saved_game.id])} if saved_game else None,
        'urls': {'prepSave': reverse('prep_save'), 'libraryImport': reverse('library_import'),
                 'library': reverse('library')},
    }
    return ctx


def analysis(request):
    # stockfish runs in the browser so the server doesnt do anything here
    return render(request, 'analysis.html', _analysis_context(request))


@login_required
def prep_open(request, pk):
    prep = get_object_or_404(Preparation, pk=pk, owner=request.user)
    return render(request, 'analysis.html', _analysis_context(request, prep=prep))


@login_required
@require_POST
def prep_save(request):
    # create or update a prep, json comes from analysis.js
    try:
        data = json.loads(request.body)
        assert isinstance(data, dict)
    except (ValueError, AssertionError):
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    title = _clean(data.get('title'), 120) or 'Untitled preparation'
    pgn = str(data.get('pgn', ''))
    if len(pgn) > MAX_PREP_PGN_CHARS:
        return JsonResponse({'error': 'This preparation is too large to save.'}, status=400)
    start_fen = str(data.get('start_fen', '')).strip()
    if start_fen and not FEN_RE.match(start_fen):
        return JsonResponse({'error': 'Invalid starting position.'}, status=400)
    fields = {
        'title': title,
        'side': 'b' if data.get('side') == 'b' else 'w',
        'opponent': _clean(data.get('opponent'), 100),
        'notes': str(data.get('notes', ''))[:20_000],
        'pgn': pgn,
        'start_fen': start_fen,
    }

    prep_id = str(data.get('id', ''))
    if prep_id.isdigit():
        prep = get_object_or_404(Preparation, pk=int(prep_id), owner=request.user)
        for k, v in fields.items():
            setattr(prep, k, v)
        prep.save()
    else:
        if Preparation.objects.filter(owner=request.user).count() >= MAX_PREPS:
            return JsonResponse({'error': f'You can keep up to {MAX_PREPS} preparations.'}, status=400)
        prep = Preparation.objects.create(owner=request.user, **fields)
    return JsonResponse({'id': prep.id, 'title': prep.title,
                         'url': reverse('prep_open', args=[prep.id]),
                         'updated': prep.updated.strftime('%d %b %Y, %H:%M')})


@login_required
@require_POST
def prep_delete(request, pk):
    prep = get_object_or_404(Preparation, pk=pk, owner=request.user)
    prep.delete()
    messages.success(request, f'"{prep.title}" deleted.')
    return redirect('analysis')
