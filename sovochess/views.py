from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Article, User, Game, Move, PlayerProfile, Preparation, SavedGame
from .pgn_export import played_game_to_pgn, RESULT_TO_PGN
from .engine_adapter import choose_bot_move

import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))
from game import Game as ChessGame, ChessBot

OPENINGS = {
    'e2e4': 'King\'s Pawn Opening',
    'e2e4 e7e5': 'Open Game',
    'e2e4 c7c5': 'Sicilian Defense',
    'e2e4 e7e6': 'French Defense',
    'e2e4 c7c6': 'Caro-Kann Defense',
    'e2e4 d7d5': 'Scandinavian Defense',
    'e2e4 g8f6': 'Alekhine\'s Defense',
    'e2e4 d7d6': 'Pirc Defense',
    'e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 a7a6': 'Sicilian Najdorf',
    'e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6': 'Sicilian Dragon',
    'e2e4 c7c5 g1f3 e7e6 d2d4 c5d4 f3d4 a7a6': 'Sicilian Kan',
    'e2e4 c7c5 b1c3': 'Closed Sicilian',
    'e2e4 c7c5 c2c3': 'Alapin Variation',
    'e2e4 e7e6 d2d4 d7d5 b1c3 g8f6': 'French Classical',
    'e2e4 e7e6 d2d4 d7d5 e4e5': 'French Advance',
    'e2e4 e7e6 d2d4 d7d5 b1d2': 'French Tarrasch',
    'e2e4 c7c6 d2d4 d7d5 e4e5': 'Caro-Kann Advance',
    'e2e4 c7c6 d2d4 d7d5 e4d5 c6d5': 'Caro-Kann Exchange',
    'e2e4 d7d5 e4d5 d8d5': 'Scandinavian Center Counter',
    'd2d4': 'Queen\'s Pawn Opening',
    'd2d4 d7d5': 'Closed Game',
    'd2d4 g8f6 c2c4 g7g6': 'King\'s Indian Defense',
    'd2d4 g8f6 c2c4 e7e6': 'Nimzo-Indian Defense',
    'd2d4 d7d5 c2c4': 'Queen\'s Gambit',
    'd2d4 d7d5 c2c4 e7e6': 'Queen\'s Gambit Declined',
    'd2d4 d7d5 c2c4 d5c4': 'Queen\'s Gambit Accepted',
    'd2d4 d7d5 c2c4 c7c6': 'Slav Defense',
    'd2d4 g8f6 c2c4 e7e6 g1f3 b7b6': 'Queen\'s Indian Defense',
    'd2d4 g8f6 c2c4 c7c5': 'Benoni Defense',
    'c2c4': 'English Opening',
    'c2c4 e7e5': 'English Reversed Sicilian',
    'c2c4 c7c5': 'Symmetrical English',
    'g1f3': 'Réti Opening',
    'f2f4': 'Bird\'s Opening',
    'b2b3': 'Larsen\'s Opening',
    'b2b4': 'Polish Opening',
    'e2e4 e7e5 g1f3 b8c6 f1b5': 'Ruy Lopez',
    'e2e4 e7e5 g1f3 b8c6 f1c4': 'Italian Game',
    'e2e4 e7e5 g1f3 b8c6 f1c4 f8c5': 'Giuoco Piano',
    'e2e4 e7e5 g1f3 b8c6 f1c4 g8f6': 'Two Knights Defense',
    'e2e4 e7e5 f2f4': 'King\'s Gambit',
    'e2e4 e7e5 g1f3 b8c6 d2d4': 'Scotch Game',
    'e2e4 e7e5 b1c3': 'Vienna Game',
    'd2d4 g8f6 g1f3 e7e6 c1f4': 'London System',
    'd2d4 g8f6 g1f3 e7e6 c1g5': 'Torre Attack',
    'd2d4 d7d5 g1f3 g8f6 e2e3': 'Colle System',
    'd2d4 g8f6 c2c4 e7e6 g1f3 d7d5 g2g3': 'Catalan Opening',
    'e2e4 e7e5 f1c4 b8c6 d1h5 g8f6 h5f7': 'Scholar\'s Mate',
    'f2f3 e7e5 g2g4 d8h4': 'Fool\'s Mate',
}

def identify_opening(move_list):
    moves_str = ' '.join([m.from_square + m.to_square for m in move_list])
    return identify_opening_str(moves_str)


def identify_opening_str(moves_str):
    # moves_str looks like 'e2e4 e7e5 g1f3'
    best_match = 'Unknown Opening'
    best_length = 0
    for moves, name in OPENINGS.items():
        if moves_str.startswith(moves) and len(moves) > best_length:
            best_match = name
            best_length = len(moves)
    return best_match


def calculate_elo(winner_rating, loser_rating, k=32):
    expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    expected_loser = 1 / (1 + 10 ** ((winner_rating - loser_rating) / 400))
    new_winner_rating = round(winner_rating + k * (1 - expected_winner))
    new_loser_rating = round(loser_rating + k * (0 - expected_loser))
    return new_winner_rating, new_loser_rating


# time controls for the new game buttons, key -> (base secs, increment secs)
TIME_CONTROLS = {
    'none': (0, 0),
    '1+0': (60, 0),
    '3+0': (180, 0),
    '3+2': (180, 2),
    '5+0': (300, 0),
    '10+0': (600, 0),
    '15+10': (900, 10),
    '30+0': (1800, 0),
}


def square_to_pos(square):
    col = ord(square[0]) - ord('a')
    row = 8 - int(square[1])
    return (row, col)


def pos_to_square(pos):
    row, col = pos
    return chr(col + ord('a')) + str(8 - row)


def is_square(value):
    return isinstance(value, str) and len(value) == 2 and value[0] in 'abcdefgh' and value[1] in '12345678'


def replay(game_obj):
    # rebuild the board from the moves saved in the db
    chess_game = ChessGame()
    for move in Move.objects.filter(game=game_obj).order_by('move_number'):
        chess_game.make_move(square_to_pos(move.from_square), square_to_pos(move.to_square))
    return chess_game


def get_own_game(request, game_id):
    # 404 if its not your game so ppl cant move in other peoples games
    return get_object_or_404(Game, id=game_id, white_player=request.user)


def white_time_left_ms(game_obj, now=None):
    # only whites clock actually runs, the bot moves instantly
    if not game_obj.is_timed:
        return None
    remaining = game_obj.white_time_ms
    if game_obj.last_move_at and not game_obj.is_finished:
        now = now or timezone.now()
        remaining -= int((now - game_obj.last_move_at).total_seconds() * 1000)
    return max(remaining, 0)


def clock_state(game_obj, now=None):
    if not game_obj.is_timed:
        return None
    return {
        'white_ms': white_time_left_ms(game_obj, now),
        'black_ms': game_obj.black_time_ms,
        # clock starts after whites first move
        'running': 'w' if (game_obj.last_move_at and not game_obj.is_finished) else None,
    }


def finish_game(game_obj, result, termination):
    # saves the result, updates stats and puts the game in the library
    if game_obj.is_finished:
        return
    game_obj.result = result
    game_obj.termination = termination
    game_obj.opening_name = identify_opening(Move.objects.filter(game=game_obj).order_by('move_number'))
    user = game_obj.white_player
    # user is saved as both players so winner is only set on a win
    game_obj.winner = user if result == 'win' else None
    game_obj.save()

    # update player profiles
    profile, _ = PlayerProfile.objects.get_or_create(user=user)
    profile.total_games += 1
    if result == 'win':
        profile.total_wins += 1
    elif result == 'loss':
        profile.total_losses += 1
    if game_obj.opening_name and game_obj.opening_name != 'Unknown Opening':
        profile.favourite_opening = game_obj.opening_name
    profile.save()

    pgn, plies = played_game_to_pgn(game_obj)
    SavedGame.objects.update_or_create(
        played_game=game_obj,
        defaults=dict(
            owner=user, source='played', white=user.username, black='SovoBot',
            result=RESULT_TO_PGN.get(result, '*'), event='SovoChess casual game',
            date=game_obj.date_played.strftime('%Y.%m.%d'), opening=game_obj.opening_name,
            ply_count=plies, pgn=pgn,
        ),
    )


def game_over_payload(game_obj):
    return {
        'game_over': True,
        'result': game_obj.result,
        'termination': game_obj.termination,
        'opening': game_obj.opening_name,
        'result_url': reverse('post_game', args=[game_obj.id]),
    }


def time_control_choices():
    out = []
    for key, (base, inc) in TIME_CONTROLS.items():
        if base == 0:
            kind = 'Untimed'
        else:
            estimate = base + 40 * inc  # same way lichess decides bullet/blitz/rapid
            kind = 'Bullet' if estimate < 180 else 'Blitz' if estimate < 480 else 'Rapid' if estimate < 1500 else 'Classical'
        out.append({'key': key, 'label': '∞' if base == 0 else key, 'kind': kind})
    return out


# only one home view with leaderboard
def home(request):
    top_players = User.objects.order_by('-current_rating')[:10]
    context = {
        'top_players': top_players,
        'time_controls': time_control_choices(),
        'articles': Article.objects.filter(is_published=True)[:3],
    }
    if request.user.is_authenticated:
        context['recent_games'] = SavedGame.objects.filter(owner=request.user)[:6]
        context['preps'] = Preparation.objects.filter(owner=request.user)[:4]
        context['prep_count'] = Preparation.objects.filter(owner=request.user).count()
        context['open_game'] = (Game.objects.filter(white_player=request.user, result='', moves__isnull=False)
                                .order_by('-date_played').distinct().first())
    return render(request, 'home.html', context)


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '')
            if next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Wrong username or password!')
    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST['username'].strip()
        email = request.POST['email'].strip()
        password = request.POST['password']
        if not username or not password:
            messages.error(request, 'Please choose a username and a password.')
        elif not request.POST.get('accept_terms'):
            messages.error(request, 'Please accept the Terms of Use and Privacy Policy to create an account.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken!')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            # create a profile for the new user
            PlayerProfile.objects.create(user=user)
            login(request, user)
            return redirect('home')
    return render(request, 'register.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def game_view(request, game_id):
    game = get_own_game(request, game_id)
    moves = [m.from_square + m.to_square for m in game.moves.order_by('move_number')]
    return render(request, 'game.html', {
        'game': game,
        'game_state': {
            'moves': moves,
            'clock': clock_state(game),
            'over': game_over_payload(game) if game.is_finished else None,
            'urls': {'move': reverse('make_move', args=[game.id]), 'position': reverse('get_position', args=[game.id]),
                     'flag': reverse('flag_game', args=[game.id]), 'resign': reverse('resign_game', args=[game.id])},
        },
    })


@login_required
def start_game(request):
    base, increment = TIME_CONTROLS.get(request.GET.get('tc', 'none'), (0, 0))
    game = Game.objects.create(
        white_player=request.user,
        black_player=request.user,
        time_base=base,
        time_increment=increment,
        white_time_ms=base * 1000,
        black_time_ms=base * 1000,
    )
    return redirect('game', game_id=game.id)


# game api, game.html calls these with fetch

@login_required
@require_POST
def make_move(request, game_id):
    try:
        data = json.loads(request.body)
        from_square, to_square = data['from'], data['to']
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'error': 'Invalid request'}, status=400)
    if not (is_square(from_square) and is_square(to_square)):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    with transaction.atomic():
        game_obj = get_object_or_404(Game.objects.select_for_update(), id=game_id, white_player=request.user)
        if game_obj.is_finished:
            return JsonResponse({'valid': False, **game_over_payload(game_obj)})

        now = timezone.now()

        # ran out of time before the move got here
        remaining = white_time_left_ms(game_obj, now)
        if game_obj.is_timed and remaining <= 0:
            game_obj.white_time_ms = 0
            finish_game(game_obj, 'loss', 'timeout')
            return JsonResponse({'valid': False, 'clock': clock_state(game_obj), **game_over_payload(game_obj)})

        chess_game = replay(game_obj)
        move_count = Move.objects.filter(game=game_obj).count()

        if not chess_game.make_move(square_to_pos(from_square), square_to_pos(to_square)):
            return JsonResponse({'valid': False, 'clock': clock_state(game_obj, now)})

        Move.objects.create(game=game_obj, move_number=move_count + 1,
                            from_square=from_square, to_square=to_square)
        if game_obj.is_timed:
            game_obj.white_time_ms = remaining + game_obj.time_increment * 1000

        response = {'valid': True}

        # check checkmate after player move
        if chess_game.is_checkmate():
            game_obj.save()
            finish_game(game_obj, 'win', 'checkmate')
            response.update(game_over_payload(game_obj))
        # check stalemate after player move
        elif chess_game.is_stalemate():
            game_obj.save()
            finish_game(game_obj, 'draw', 'stalemate')
            response.update(game_over_payload(game_obj))
        else:
            # bot makes a move for black
            # which engine plays is set in settings SOVO_ENGINE, see engine_adapter.py
            bot_move = choose_bot_move(chess_game, fullmove=move_count // 2 + 1)
            if bot_move:
                bot_from_pos, bot_to_pos = bot_move
                chess_game.make_move(bot_from_pos, bot_to_pos)
                bot_from_square, bot_to_square = pos_to_square(bot_from_pos), pos_to_square(bot_to_pos)
                Move.objects.create(game=game_obj, move_number=move_count + 2,
                                    from_square=bot_from_square, to_square=bot_to_square)
                response['bot_move'] = bot_from_square + bot_to_square
                if game_obj.is_timed:
                    game_obj.black_time_ms += game_obj.time_increment * 1000

            game_obj.last_move_at = now  # whites clock runs again from here
            game_obj.save()

            # check checkmate after bot move
            if chess_game.is_checkmate():
                finish_game(game_obj, 'loss', 'checkmate')
                response.update(game_over_payload(game_obj))
            # check stalemate after bot move
            elif chess_game.is_stalemate():
                finish_game(game_obj, 'draw', 'stalemate')
                response.update(game_over_payload(game_obj))

        response['clock'] = clock_state(game_obj)
        return JsonResponse(response)


@login_required
@require_POST
def flag_game(request, game_id):
    # page calls this when whites clock hits 0, server checks the time again just in case
    with transaction.atomic():
        game_obj = get_object_or_404(Game.objects.select_for_update(), id=game_id, white_player=request.user)
        if not game_obj.is_finished and game_obj.is_timed and white_time_left_ms(game_obj) <= 0:
            game_obj.white_time_ms = 0
            finish_game(game_obj, 'loss', 'timeout')
        payload = {'clock': clock_state(game_obj)}
        if game_obj.is_finished:
            payload.update(game_over_payload(game_obj))
        return JsonResponse(payload)


@login_required
@require_POST
def resign_game(request, game_id):
    with transaction.atomic():
        game_obj = get_object_or_404(Game.objects.select_for_update(), id=game_id, white_player=request.user)
        if not game_obj.is_finished:
            if game_obj.is_timed:
                game_obj.white_time_ms = white_time_left_ms(game_obj)
            finish_game(game_obj, 'loss', 'resign')
    return JsonResponse(game_over_payload(game_obj))


@login_required
def get_position(request, game_id):
    game_obj = get_own_game(request, game_id)
    chess_game = replay(game_obj)
    return JsonResponse({'fen': board_to_fen(chess_game.board), 'clock': clock_state(game_obj)})


def board_to_fen(board):
    fen = ''
    for row in range(8):
        empty = 0
        for col in range(8):
            piece = board.get_piece(row, col)
            if piece is None:
                empty += 1
            else:
                if empty > 0:
                    fen += str(empty)
                    empty = 0
                symbols = {
                    'Pawn': ('P', 'p'), 'Rook': ('R', 'r'),
                    'Knight': ('N', 'n'), 'Bishop': ('B', 'b'),
                    'Queen': ('Q', 'q'), 'King': ('K', 'k')
                }
                piece_type = type(piece).__name__
                white_sym, black_sym = symbols[piece_type]
                fen += white_sym if piece.color == 'w' else black_sym
        if empty > 0:
            fen += str(empty)
        if row < 7:
            fen += '/'
    return fen


@login_required
def post_game(request, game_id):
    game = get_own_game(request, game_id)

    if game.is_finished:
        result = game.result
    else:
        # old games from before results were saved, replay to see how it ended
        chess_game = replay(game)
        if chess_game.is_checkmate():
            # side to move is the one that got mated, user is always white
            result = 'loss' if chess_game.current_turn == 'w' else 'win'
        elif chess_game.is_stalemate():
            result = 'draw'
        else:
            result = 'unfinished'

    saved = getattr(game, 'saved', None) if game.is_finished else None
    return render(request, 'post_game.html', {
        'game': game,
        'result': result,
        'user_won': result == 'win',
        'saved_game': saved,
    })
