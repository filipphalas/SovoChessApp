# first articles for the read page, more can be added in /admin/
import datetime

from django.db import migrations

ARTICLES = [
    {
        'slug': 'the-opera-game',
        'title': 'The Opera Game, move by move',
        'dek': 'Paris, 1858. Paul Morphy plays two aristocrats in a theatre box during an opera and '
               'produces the most-taught game in chess history.',
        'category': 'classics',
        'image': '',
        'cover_fen': '1n1Rkb1r/p4ppp/4q3/4p1B1/4P3/8/PPP2PPP/2K5 b k - 1 17',
        'published': datetime.date(2026, 11, 20),
        'body': """\
In 1858 Paul Morphy, a 21-year-old from New Orleans, was touring Europe and beating everyone. One evening at the Paris opera he was invited into the private box of the Duke of Brunswick, who, with Count Isouard, insisted on a game against him. Morphy sat with his back to the stage. The game lasted seventeen moves.

What makes it so useful to study is that nothing in it is mysterious. Every one of Morphy's moves follows a principle that you can apply in your own games tomorrow.

## The opening: giving up the centre

The allies chose the Philidor Defence and then pinned the knight with 3...Bg4, a move that looks active but gives up the bishop pair after 4.dxe5 Bxf3 5.Qxf3.

[board moves="e4 e5 Nf3 d6 d4 Bg4 dxe5 Bxf3 Qxf3 dxe5" caption="1.e4 e5 2.Nf3 d6 3.d4 Bg4 4.dxe5 Bxf3 5.Qxf3 dxe5"]

White's queen now eyes f7 and b7 at the same time. Black can't defend both comfortably.

## Development over material

Morphy brings his bishop to c4, attacks b7 and keeps bringing pieces out. When Black finally blocks with ...c6 and ...b5, Morphy does not retreat. He sacrifices a knight to open lines towards the black king, which is still in the centre.

[board fen="rn2kb1r/p3qppp/2p2n2/1p2p1B1/2B1P3/1QN5/PPP2PPP/R3K2R w KQkq - 0 10" moves="Nxb5 cxb5 Bxb5+ Nbd7 O-O-O" caption="10.Nxb5! cxb5 11.Bxb5+ Nbd7 12.O-O-O"]

Count the pieces after 12.O-O-O. White has given up a knight, but every white piece is attacking. Black's bishop on f8 and rook on h8 haven't moved.

## The finish

> "Help your pieces so they can help you." — Paul Morphy

Morphy gives up a whole rook to remove the defender on d7, then sacrifices the queen to drag the last knight away from d8.

[board fen="3rkb1r/p2nqppp/5n2/1B2p1B1/4P3/1Q6/PPP2PPP/2KR3R w k - 3 13" moves="Rxd7 Rxd7 Rd1 Qe6 Bxd7+ Nxd7 Qb8+ Nxb8 Rd8#" caption="13.Rxd7 Rxd7 14.Rd1 Qe6 15.Bxd7+ Nxd7 16.Qb8+! Nxb8 17.Rd8#"]

## What to take from it

Get your pieces out before you go hunting. Keep your king safe, and punish an opponent who leaves theirs in the middle. When you're ahead in development, open lines, even if it costs material. A lead in development doesn't last, so use it while you have it.
""",
    },
    {
        'slug': 'five-opening-principles',
        'title': 'Five opening principles that actually win games',
        'dek': "You don't need to memorise 20 moves of theory. You need five ideas, and to know "
               'when each one applies.',
        'category': 'openings',
        'image': 'img/art/anguissola-chess-game.jpg',
        'image_credit': 'Sofonisba Anguissola, The Chess Game (1555). Public domain.',
        'cover_fen': '',
        'published': datetime.date(2026, 11, 12),
        'body': """\
Most club games are decided by move 15, and most of those by a mistake that breaks one of the same handful of rules. Learn the rules first and the opening names will follow.

## 1. Fight for the centre

Pawns on e4 and d4 (or e5 and d5) control the squares your pieces want to use. A knight on f3 covers more of the board than a knight on h3.

[board moves="e4 e5 Nf3 Nc6 Bc4 Bc5" caption="The Italian Game: both sides take the centre and develop towards it."]

## 2. Knights before bishops

You usually know where a knight belongs (f3, c3) before you know which diagonal a bishop wants. Develop the pieces you're sure about first.

## 3. Don't bring the queen out early

It's tempting, and against a beginner it sometimes works. But every time your opponent develops a piece *with tempo* by attacking your queen, you fall a move further behind.

[board moves="e4 e5 Qh5 Nc6 Bc4 g6 Qf3 Nf6 Qb3 Nd4" caption="White's queen has moved three times. Black has two pieces out and is already attacking."]

## 4. Castle early

A king in the centre gets caught when the centre opens. Castling moves it to safety and brings a rook towards the middle in a single move.

## 5. Every move should do something

Before each move in the opening, ask: does this develop a piece, take the centre, or make my king safer? If the answer is no, look for a better move.

## The trap to watch out for

Here's what happens when Black forgets about f7, the weakest square in the starting position:

[board moves="e4 e5 Bc4 Nc6 Qh5 Nf6 Qxf7#" caption="Scholar's Mate. 3...g6 or 3...Qe7 would have stopped it."]
""",
    },
    {
        'slug': 'the-immortal-game',
        'title': 'The Immortal Game: Anderssen sacrifices everything',
        'dek': 'London, 1851. Adolf Anderssen gives up both rooks, a bishop and his queen, then '
               'mates with three minor pieces.',
        'category': 'history',
        'image': 'img/art/daumier-chess-players.jpg',
        'image_credit': 'Honoré Daumier, The Chess Players (c. 1863). Public domain.',
        'cover_fen': '',
        'published': datetime.date(2026, 11, 3),
        'body': """\
Adolf Anderssen and Lionel Kieseritzky played this as a casual game during a break at the first international tournament, held in London in 1851. It was published soon afterwards, and an Austrian magazine called it "the Immortal Game".

It belongs to the Romantic era of chess, when players gambled pawns for open lines and declining a sacrifice was considered a little cowardly. By modern standards both sides make mistakes. It's still a wonderful game to replay.

## The King's Gambit

Anderssen offers a pawn on move two. Kieseritzky takes it and immediately checks with his queen, forcing the white king to give up castling.

[board moves="e4 e5 f4 exf4 Bc4 Qh4+ Kf1 b5 Bxb5 Nf6 Nf3 Qh6" caption="1.e4 e5 2.f4 exf4 3.Bc4 Qh4+ 4.Kf1 b5 5.Bxb5 Nf6 6.Nf3 Qh6"]

## The sacrifices begin

From move 17 White stops counting material altogether. First a bishop, then a rook, then the other rook, then the queen.

[board fen="rnb1k1nr/p2p1ppp/3B4/1p1NPN1P/6P1/3P1Q2/P1P5/q4Kb1 w kq - 0 20" moves="Ke2 Na6 Nxg7+ Kd8 Qf6+ Nxf6 Be7#" caption="20.Ke2 Na6 21.Nxg7+ Kd8 22.Qf6+! Nxf6 23.Be7#"]

At the end, Black has every major piece still on the board and is mated by two knights and a bishop.

## Why it still matters

Modern engines find improvements for both sides. But the final position shows something engines can't teach on their own: material only matters if it's taking part. Black's extra rooks and queen are sitting in the corners, doing nothing.
""",
    },
    {
        'slug': 'lucena-position',
        'title': 'Building a bridge: the Lucena position',
        'dek': 'The most important rook endgame to know. Once you understand it, you will win '
               'positions that used to end in a draw.',
        'category': 'endgames',
        'image': '',
        'cover_fen': '1K6/1P1k4/8/8/8/8/r7/2R5 w - - 0 1',
        'published': datetime.date(2026, 10, 24),
        'body': """\
Rook endgames are the most common endgames in practice, and the Lucena position is where many of them end. It's named after Luis Ramírez de Lucena, although it doesn't appear in his 1497 book. Every serious player knows it.

## The set-up

White has a pawn on the seventh rank and a king in front of it. Black's king is cut off from the pawn. The problem is that White's king is in the way. If it steps out, Black's rook checks it from behind and from the side.

[board fen="1K6/1P1k4/8/8/8/8/r7/2R5 w - - 0 1" caption="White to play and win."]

## Step one: push the black king further away

A check on the d-file drives the black king one more file away from the pawn.

## Step two: build the bridge

The key move is to put the rook on the fourth rank. White's king then walks out, and when the checks come, the rook blocks them. That's the "bridge".

[board fen="1K6/1P1k4/8/8/8/8/r7/2R5 w - - 0 1" moves="Rd1+ Ke7 Rd4 Rb2 Kc7 Rc2+ Kb6 Rb2+ Kc6 Rc2+ Kb5 Rb2+ Rb4" caption="1.Rd1+ Ke7 2.Rd4! Rb2 3.Kc7 Rc2+ 4.Kb6 Rb2+ 5.Kc6 Rc2+ 6.Kb5 Rb2+ 7.Rb4 and the pawn queens."]

## Remember it by the rook

Rook to the fourth rank. If you remember that, you can work out everything else at the board.
""",
    },
    {
        'slug': 'four-tactics',
        'title': 'Four tactics you will see in every game',
        'dek': 'The fork, the skewer, the back-rank mate and the discovered attack. Learn to spot '
               "them and you'll stop losing pieces, and start winning them.",
        'category': 'tactics',
        'image': 'img/art/eakins-chess-players.jpg',
        'image_credit': 'Thomas Eakins, The Chess Players (1876). Public domain.',
        'cover_fen': '',
        'published': datetime.date(2026, 10, 10),
        'body': """\
Most games below master level are decided by tactics: short, forcing sequences that win material or give mate. You can't calculate everything, but you can learn the patterns.

## The fork

One piece attacks two things at once. Knights are the best at it because their attacks are hard to see coming.

[board fen="r3k3/8/8/1N6/8/8/8/4K3 w - - 0 1" moves="Nc7+ Kd7 Nxa8" caption="Nc7+ checks the king and attacks the rook."]

## The skewer

A fork's cousin: attack a valuable piece, and when it moves, take whatever was behind it.

[board fen="8/8/8/3k3q/8/8/8/R5K1 w - - 0 1" moves="Ra5+ Ke4 Rxh5" caption="The king has to step off the rank and the queen falls."]

## The back-rank mate

If your king is behind its own pawns and your rooks have left the back rank, one check can be the end.

[board fen="6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1" moves="Rd8#" caption="Black's own pawns trap the king. Making room with ...h6 earlier would have prevented this."]

## The discovered attack

Move one piece out of the way and the piece behind it attacks. If the piece that moves also makes a threat, the opponent can only deal with one of them.

[board fen="4k3/8/8/8/7q/4B3/8/4R1K1 w - - 0 1" moves="Bg5+ Kd7 Bxh4" caption="Bg5+ uncovers a check from the rook and attacks the queen at the same time. Black has to answer the check, so the queen is lost."]

## How to practise

Before every move, check three things: every check, every capture and every threat, for both sides. It feels slow at first. After a few weeks it becomes automatic.
""",
    },
]


def seed(apps, schema_editor):
    Article = apps.get_model('chess', 'Article')
    for data in ARTICLES:
        Article.objects.update_or_create(slug=data['slug'], defaults=data)


def unseed(apps, schema_editor):
    apps.get_model('chess', 'Article').objects.filter(slug__in=[a['slug'] for a in ARTICLES]).delete()


class Migration(migrations.Migration):
    dependencies = [('chess', '0004_prep_and_articles')]
    operations = [migrations.RunPython(seed, unseed)]
