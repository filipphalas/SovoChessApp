# turns games played here into pgn
# moves are saved as squares (e2e4) but pgn needs normal notation (Nf3, exd5, O-O)
# so we replay the game and work it out move by move
import os
import sys

sys.path.append(os.path.dirname(__file__))
from game import Game as ChessGame  # noqa: E402

FILES = 'abcdefgh'
PIECE_LETTER = {'King': 'K', 'Queen': 'Q', 'Rook': 'R', 'Bishop': 'B', 'Knight': 'N', 'Pawn': ''}
RESULT_TO_PGN = {'win': '1-0', 'loss': '0-1', 'draw': '1/2-1/2'}


def square_to_pos(square):
    return (8 - int(square[1]), ord(square[0]) - ord('a'))


def pos_to_square(pos):
    row, col = pos
    return FILES[col] + str(8 - row)


def _legal_moves(chess_game):
    return [
        (f, t) for f, t in chess_game.get_all_valid_moves(chess_game.current_turn)
        if not chess_game._would_be_in_check(f, t)
    ]


def _san_before_move(chess_game, from_pos, to_pos):
    # notation for a move without + or #, that gets added after the move
    piece = chess_game.board.get_piece(*from_pos)
    kind = type(piece).__name__
    # en passant lands on an empty square so check if the pawn changed file
    capture = chess_game.board.get_piece(*to_pos) is not None or (kind == 'Pawn' and from_pos[1] != to_pos[1])

    if kind == 'King' and abs(to_pos[1] - from_pos[1]) == 2:
        return 'O-O' if to_pos[1] > from_pos[1] else 'O-O-O'

    if kind == 'Pawn':
        san = (FILES[from_pos[1]] + 'x' if capture else '') + pos_to_square(to_pos)
        if to_pos[0] in (0, 7):
            san += '=Q'  # always promotes to queen in our game
        return san

    # if 2 of the same piece can go there we need to add the file/rank (like Nbd7)
    rivals = [
        f for f, t in _legal_moves(chess_game)
        if t == to_pos and f != from_pos and type(chess_game.board.get_piece(*f)).__name__ == kind
    ]
    disambiguation = ''
    if rivals:
        if all(f[1] != from_pos[1] for f in rivals):
            disambiguation = FILES[from_pos[1]]
        elif all(f[0] != from_pos[0] for f in rivals):
            disambiguation = str(8 - from_pos[0])
        else:
            disambiguation = pos_to_square(from_pos)

    return PIECE_LETTER[kind] + disambiguation + ('x' if capture else '') + pos_to_square(to_pos)


def moves_to_san(square_moves):
    # ['e2e4', 'e7e5'] -> ['e4', 'e5'], stops if a move is invalid
    chess_game = ChessGame()
    sans = []
    for m in square_moves:
        from_pos, to_pos = square_to_pos(m[:2]), square_to_pos(m[2:4])
        if not chess_game.board.get_piece(*from_pos):
            break
        san = _san_before_move(chess_game, from_pos, to_pos)
        if not chess_game.make_move(from_pos, to_pos):
            break
        if chess_game.is_checkmate():
            san += '#'
        elif chess_game.is_in_check(chess_game.current_turn):
            san += '+'
        sans.append(san)
    return sans


def _header(key, value):
    value = str(value).replace('\\', '\\\\').replace('"', '\\"')
    return f'[{key} "{value}"]'


def build_pgn(headers, sans, result='*'):
    lines = [_header(k, v) for k, v in headers.items()]
    tokens = []
    for i, san in enumerate(sans):
        if i % 2 == 0:
            tokens.append(f'{i // 2 + 1}.')
        tokens.append(san)
    tokens.append(result)

    # max ~80 chars per line like other pgn files
    movetext, line = [], ''
    for tok in tokens:
        if line and len(line) + 1 + len(tok) > 80:
            movetext.append(line)
            line = tok
        else:
            line = f'{line} {tok}' if line else tok
    movetext.append(line)
    return '\n'.join(lines) + '\n\n' + '\n'.join(movetext) + '\n'


def played_game_to_pgn(game_obj):
    # user is white, SovoBot is black
    moves = [m.from_square + m.to_square for m in game_obj.moves.order_by('move_number')]
    sans = moves_to_san(moves)
    result = RESULT_TO_PGN.get(game_obj.result, '*')
    headers = {
        'Event': 'SovoChess casual game',
        'Site': 'SovoChess',
        'Date': game_obj.date_played.strftime('%Y.%m.%d'),
        'Round': '-',
        'White': game_obj.white_player.username,
        'Black': 'SovoBot',
        'Result': result,
        'TimeControl': f'{game_obj.time_base}+{game_obj.time_increment}' if game_obj.is_timed else '-',
    }
    if game_obj.termination:
        headers['Termination'] = game_obj.get_termination_display()
    if game_obj.opening_name:
        headers['Opening'] = game_obj.opening_name
    return build_pgn(headers, sans, result), len(sans)
