#pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from game import Game, ChessBot
from pieces import Pawn, Rook, Knight, Bishop, Queen, King
from board import Board

#board
# should have 32 pieces at the start (16 white + 16 black)

def test_board_setup():
    board = Board()
    pieces = 0
    for row in range(8):
        for col in range(8):
            if board.get_piece(row, col):
                pieces += 1
    assert pieces == 32
 # tries to get a board piece
def test_board_get_piece():
    board = Board()     # white rook should be at bottom left corner (row 7, col 0)

    piece = board.get_piece(7, 0)
    assert piece is not None
    assert type(piece).__name__ == 'Rook'
    assert piece.color == 'w'
#checks board
def test_board_is_empty():     # middle of board should be empty at the start
    board = Board()
    assert board.is_empty(4, 4) == True
    assert board.is_empty(7, 0) == False


def test_board_out_of_bounds():
    board = Board()     # getting a piece out of bounds should return none

    assert board.get_piece(-1, 0) is None
    assert board.get_piece(8, 0) is None
    assert board.get_piece(0, 8) is None

# KNIGHT TESTS

def test_knight_moves_at_start():
    board = Board()
    knight = board.get_piece(7, 1)
    moves = knight.get_valid_moves(board)     # knight can jump over pieces so it should have moves at start

    assert len(moves) > 0

def test_knight_l_shape(): #test L shape
    board = Board()
    board.grid[4][4] = Knight('w', (4, 4))
    knight = board.get_piece(4, 4)
    moves = knight.get_valid_moves(board)
    assert (2, 3) in moves  # up 2 left 1
    assert (2, 5) in moves  # up 2 right 1
    assert (3, 2) in moves  # up 1 left 2
    assert (3, 6) in moves  # up 1 right 2

def test_knight_cannot_move_straight():     # knight should not be able to move straight

    board = Board()
    board.grid[4][4] = Knight('w', (4, 4))
    knight = board.get_piece(4, 4)
    moves = knight.get_valid_moves(board)
    assert (4, 5) not in moves  # straight right
    assert (5, 4) not in moves  # straight down

    # have no moves at start because pawns are blocking diagonals
#bishop test
def test_bishop_blocked_at_start():
    board = Board()
    bishop = board.get_piece(7, 2)
    moves = bishop.get_valid_moves(board)
    assert len(moves) == 0


#queen test

def test_queen_blocked_at_start():
    board = Board()
    queen = board.get_piece(7, 3)
    moves = queen.get_valid_moves(board)
    assert len(moves) == 0

def test_queen_moves_all_directions():
    board = Board()
    board.grid[4][4] = Queen('w', (4, 4))
    queen = board.get_piece(4, 4)
    moves = queen.get_valid_moves(board)
    assert (4, 5) in moves  # right
    assert (4, 3) in moves  # left
    assert (3, 4) in moves  # up
    assert (5, 4) in moves  # down
    assert (3, 3) in moves  # diagonal up left
    assert (3, 5) in moves  # diagonal up right
# king should only be able to move one square in any direction


def test_king_moves_one_square():
    board = Board()
    board.grid[4][4] = King('w', (4, 4))
    king = board.get_piece(4, 4)
    moves = king.get_valid_moves(board)
    assert (3, 4) in moves  # one square up
    assert (5, 4) in moves  # one square down
    assert (4, 3) in moves  # one square left
    assert (4, 5) in moves  # one square right
    assert (2, 4) not in moves  # two squares up should not work

def test_king_exists():
    game = Game()
    assert game.king_exists('w') == True
    assert game.king_exists('b') == True

def test_king_castling_moves_available():
    board = Board()
    board.grid[7][5] = None  # remove bishop
    board.grid[7][6] = None  # remove knight
    king = board.get_piece(7, 4)
    moves = king.get_valid_moves(board)
    assert (7, 6) in moves  # kingside castling move


def test_game_initial_turn():
    game = Game()
    assert game.current_turn == 'w'

def test_game_switch_turn():
    game = Game()
    game.switch_turn()
    assert game.current_turn == 'b'
def test_game_valid_move():
    #moving white pawn from e2 to e4 should valid
    game = Game()
    result = game.make_move((6, 4), (4, 4))
    assert result == True

def test_game_invalid_move():
    # move pawn backwards should not be valid
    game = Game()
    result = game.make_move((6, 4), (7, 4))
    assert result == False

def test_game_wrong_turn():
    #trying to move a piece on whites turn should fail
    game = Game()
    result = game.make_move((1, 0), (2, 0))
    assert result == False



def test_game_move_updates_turn():
    #after white moves it should   be blacks turn
    game = Game()
    game.make_move((6, 4), (4, 4))
    assert game.current_turn == 'b'

def test_game_status_starts_ongoing():
    #game status should be ongoing at the start
    game = Game()
    assert game.status == 'ongoing'

def test_not_checkmate_at_start():
    #game should not be in checkmate at the start
    game = Game()
    assert game.is_checkmate() == False

def test_not_stalemate_at_start():
    # game should not be in stalemate at the start
    game = Game()
    assert game.is_stalemate() == False

def test_not_in_check_at_start():
    # neither player should be in check at the start
    game = Game()
    assert game.is_in_check('w') == False
    assert game.is_in_check('b') == False

def test_pawn_promotion():
    # when a white pawn reaches row 0 it should become a queen
    game = Game()
    game.board.grid[1][4] = Pawn('w', (1, 4))
    game.board.grid[0][4] = None  # clear the destination square
    game.make_move((1, 4), (0, 4))
    piece = game.board.get_piece(0, 4)
    assert type(piece).__name__ == 'Queen'

def test_king_cannot_walk_into_check():
    # king should not be allowed to move to a square attacked by the enemy
    game = Game()
    # clear everything and set up a simple scenario
    for row in range(8):
        for col in range(8):
            game.board.grid[row][col] = None
    game.board.grid[4][4] = King('w', (4, 4))
    game.board.grid[4][6] = Rook('b', (4, 6))  # black rook attacks row 4
    king = game.board.get_piece(4, 4)
    moves = king.get_valid_moves(game.board)
    # king should not move to any square in row 4 since rook controls that row
    # filter out moves that would leave king in check
    legal_moves = [m for m in moves if not game._would_be_in_check((4, 4), m)]
    assert (4, 5) not in legal_moves  # would still be in rooks line of fire

def test_is_in_check():
    # king should be detected as in check when enemy attacks it
    game = Game()
    for row in range(8):
        for col in range(8):
            game.board.grid[row][col] = None
    game.board.grid[4][4] = King('w', (4, 4))
    game.board.grid[4][7] = Rook('b', (4, 7))  #rookattack white king
    assert game.is_in_check('w') == True

def test_not_in_check_when_blocked():
                # king should not be in check if a piece is blocking
    game = Game()
    for row in range(8):
        for col in range(8):
            game.board.grid[row][col] = None
    game.board.grid[4][4] = King('w', (4, 4))
    game.board.grid[4][6] = Rook('w', (4, 6))  # friendly rook blocking
    game.board.grid[4][7] = Rook('b', (4, 7))  #black rook is behind
    assert game.is_in_check('w') == False

def test_bot_move_is_valid():
    #the move the    bot picks should actually be a valid move
    game = Game()
    game.make_move((6, 4), (4, 4))
    bot = ChessBot(color='b')
    move = bot.get_random_move(game)
    from_pos, to_pos = move
    piece = game.board.get_piece(*from_pos)
    assert piece is not None
    assert piece.color == 'b'



# EN PASSANT TESTS

def sq(name):  # 'e4' -> (row, col)
    return (8 - int(name[1]), 'abcdefgh'.index(name[0]))


def play(game, *moves):
    for m in moves:
        assert game.make_move(sq(m[:2]), sq(m[2:])), f'{m} should be legal'


def test_en_passant_white_captures():
    game = Game()
    play(game, 'e2e4', 'a7a6', 'e4e5', 'd7d5')  # black pawn goes past d6 next to our pawn
    assert game.board.en_passant_target == sq('d6')
    assert sq('d6') in game.board.get_piece(*sq('e5')).get_valid_moves(game.board)
    play(game, 'e5d6')
    assert game.board.get_piece(*sq('d5')) is None  # captured pawn should be gone
    assert type(game.board.get_piece(*sq('d6'))).__name__ == 'Pawn'


def test_en_passant_black_captures():
    game = Game()
    play(game, 'a2a3', 'd7d5', 'a3a4', 'd5d4', 'e2e4', 'd4e3')
    assert game.board.get_piece(*sq('e4')) is None
    assert game.board.get_piece(*sq('e3')).color == 'b'


def test_en_passant_only_on_the_next_move():
    game = Game()
    play(game, 'e2e4', 'a7a6', 'e4e5', 'd7d5', 'h2h3', 'h7h6')  # white waits so its too late
    assert game.board.en_passant_target is None
    assert sq('d6') not in game.board.get_piece(*sq('e5')).get_valid_moves(game.board)
    assert not game.make_move(sq('e5'), sq('d6'))


def test_no_en_passant_after_single_steps():
    game = Game()
    play(game, 'e2e4', 'd7d6', 'e4e5', 'd6d5')  # pawn moved 1 square twice so no en passant
    assert game.board.en_passant_target is None
    assert not game.make_move(sq('e5'), sq('d6'))


def test_en_passant_that_exposes_the_king_is_illegal():
    # king a5 and enemy rook h5 with only the 2 pawns in between
    # taking en passant removes both pawns so the king would be in check
    from pieces import King, Pawn, Rook
    game = Game()
    game.board.grid = [[None] * 8 for _ in range(8)]
    for cls, color, name in [(King, 'w', 'a5'), (Pawn, 'w', 'e5'), (Rook, 'b', 'h5'),
                             (King, 'b', 'h8'), (Pawn, 'b', 'd7')]:
        game.board.grid[sq(name)[0]][sq(name)[1]] = cls(color, sq(name))
    game.board.get_piece(*sq('e5')).has_moved = True
    game.current_turn = 'b'
    play(game, 'd7d5')
    assert game.board.en_passant_target == sq('d6')
    assert game._would_be_in_check(sq('e5'), sq('d6'))
    assert not game.make_move(sq('e5'), sq('d6'))


def test_en_passant_in_pgn_export():
    from pgn_export import moves_to_san
    assert moves_to_san(['e2e4', 'a7a6', 'e4e5', 'd7d5', 'e5d6']) == ['e4', 'a6', 'e5', 'd5', 'exd6']
