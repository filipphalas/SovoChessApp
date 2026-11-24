# connects the site to the chess engine
# make_move in views calls choose_bot_move(), which engine plays is set in settings SOVO_ENGINE
#   {'name': 'random'} = random bot
#   {'name': 'neural', 'checkpoint': 'engine/checkpoints/best.pt', 'time_limit_ms': 1500} = my engine
# if the engine breaks (crash, too slow, illegal move) it just plays a random move instead
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

from django.conf import settings

sys.path.append(os.path.dirname(__file__))
from game import ChessBot  # noqa: E402

log = logging.getLogger(__name__)

FILES = 'abcdefgh'
_engine = None
_engine_failed = False
_lock = threading.Lock()
_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='sovo-engine')


# board <-> fen / uci

def _sq(pos):
    row, col = pos
    return FILES[col] + str(8 - row)


def _pos(square):
    return 8 - int(square[1]), FILES.index(square[0])


def game_to_fen(chess_game, fullmove=1):
    # full fen (all 6 parts) from our Game object
    from .views import board_to_fen  # imported here bc views imports this file too

    board = chess_game.board

    def unmoved(row, col, kind, color):
        p = board.get_piece(row, col)
        return p is not None and type(p).__name__ == kind and p.color == color and not p.has_moved

    castling = ''
    if unmoved(7, 4, 'King', 'w'):
        castling += 'K' if unmoved(7, 7, 'Rook', 'w') else ''
        castling += 'Q' if unmoved(7, 0, 'Rook', 'w') else ''
    if unmoved(0, 4, 'King', 'b'):
        castling += 'k' if unmoved(0, 7, 'Rook', 'b') else ''
        castling += 'q' if unmoved(0, 0, 'Rook', 'b') else ''
    ep = _sq(board.en_passant_target) if board.en_passant_target else '-'
    return f'{board_to_fen(board)} {chess_game.current_turn} {castling or "-"} {ep} 0 {fullmove}'


def _legal_moves(chess_game):
    return [(f, t) for f, t in chess_game.get_all_valid_moves(chess_game.current_turn)
            if not chess_game._would_be_in_check(f, t)]


# loading the engine

def get_engine():
    # loads the engine once, None means use the random bot
    global _engine, _engine_failed
    cfg = getattr(settings, 'SOVO_ENGINE', {'name': 'random'})
    if cfg.get('name', 'random') == 'random' or _engine_failed:
        return None
    if _engine is None:
        with _lock:
            if _engine is None:
                try:
                    if cfg['name'] == 'neural':
                        from engine.neural_engine import NeuralEngine
                        kwargs = {'checkpoint': cfg['checkpoint']} if cfg.get('checkpoint') else {}
                        _engine = NeuralEngine(**kwargs)
                    else:
                        raise ValueError(f"Unknown engine {cfg['name']!r} in SOVO_ENGINE")
                    log.info('Loaded chess engine %s', cfg['name'])
                except Exception:
                    _engine_failed = True  # dont try again every move, restart server after fixing
                    log.exception('Could not load engine %r, using the random bot instead', cfg.get('name'))
                    return None
    return _engine


# views.py only uses this

def choose_bot_move(chess_game, fullmove=1):
    # returns (from_pos, to_pos) or None if there are no moves
    legal = _legal_moves(chess_game)
    if not legal:
        return None

    engine = get_engine()
    if engine is not None:
        cfg = settings.SOVO_ENGINE
        limit = int(cfg.get('time_limit_ms', 1000))
        fen = game_to_fen(chess_game, fullmove)
        try:
            uci = _pool.submit(engine.best_move, fen, limit).result(timeout=limit / 1000 + 5)
            move = (_pos(uci[:2]), _pos(uci[2:4]))
            if move in legal:
                if len(uci) == 5 and uci[4] != 'q':
                    log.info('Engine chose underpromotion %s; our rules always promote to a queen', uci)
                return move
            log.warning('Engine returned %r, which is not legal under our rules in %s', uci, fen)
        except FutureTimeout:
            log.warning('Engine took longer than %s ms on %s', limit, fen)
        except Exception:
            log.exception('Engine crashed on %s', fen)

    return ChessBot(color=chess_game.current_turn).get_random_move(chess_game)
