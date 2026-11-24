from django.db import models
from django.contrib.auth.models import AbstractUser

# for password hashing django is using a hash + salt method so it is hard to break through even if there was a possible database leak
class User(AbstractUser):
    current_rating = models.IntegerField(default=1200)

    def update_rating(self, new_rating):
        self.current_rating = new_rating #update to the new rating
        self.save()

    def __str__(self):
        return self.username

class PlayerProfile(models.Model): #PROFILE checker
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_games = models.IntegerField(default=0)
    total_wins = models.IntegerField(default=0)
    total_losses = models.IntegerField(default=0)
    favourite_opening = models.CharField(max_length=100, blank=True)

    def update_stats(self, won, opening):
        self.total_games += 1
        if won:
            self.total_wins += 1
        else:
            self.total_losses += 1
        # update favourite opening if this one appears more than current favourite
        if opening and opening != 'Unknown Opening':
            self.favourite_opening = opening
        self.save()

    def __str__(self):
        return f"{self.user.username}'s profile"

class Game(models.Model):
    RESULT_CHOICES = [('', 'In progress'), ('win', 'Win'), ('loss', 'Loss'), ('draw', 'Draw')]
    TERMINATION_CHOICES = [('', ''), ('checkmate', 'Checkmate'), ('stalemate', 'Stalemate'),
                           ('timeout', 'Time out'), ('resign', 'Resignation')]

    white_player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='white_games')
    black_player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='black_games')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_games')
    opening_name = models.CharField(max_length=100, blank=True)
    date_played = models.DateTimeField(auto_now_add=True)
    move_history = models.TextField(blank=True)

    # time control, base 0 = no clock
    time_base = models.PositiveIntegerField(default=0)       # seconds
    time_increment = models.PositiveIntegerField(default=0)  # seconds
    white_time_ms = models.IntegerField(default=0)
    black_time_ms = models.IntegerField(default=0)
    last_move_at = models.DateTimeField(null=True, blank=True)  # when the clock last switched

    # result is from the users side (white)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, blank=True, default='')
    termination = models.CharField(max_length=20, choices=TERMINATION_CHOICES, blank=True, default='')

    @property
    def is_timed(self):
        return self.time_base > 0

    @property
    def is_finished(self):
        return self.result != ''

    @property
    def time_control_label(self):
        if not self.is_timed:
            return 'No clock'
        return f"{self.time_base // 60}+{self.time_increment}"

    def __str__(self):
        return f"{self.white_player} vs {self.black_player}"


class Collection(models.Model):
    # folder in the library, like "Sicilian games"
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = [('owner', 'name')]

    def __str__(self):
        return self.name


class SavedGame(models.Model):
    # game in the library, either played here or imported
    SOURCE_CHOICES = [('played', 'Played on SovoChess'), ('import', 'Imported PGN')]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_games')
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True, related_name='games')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='import')
    played_game = models.OneToOneField(Game, on_delete=models.SET_NULL, null=True, blank=True, related_name='saved')

    white = models.CharField(max_length=100, blank=True)
    black = models.CharField(max_length=100, blank=True)
    result = models.CharField(max_length=10, blank=True)   # 1-0, 0-1, 1/2-1/2, *
    event = models.CharField(max_length=150, blank=True)
    date = models.CharField(max_length=20, blank=True)     # can be like 2024.??.?? so not a DateField
    eco = models.CharField(max_length=10, blank=True)
    opening = models.CharField(max_length=150, blank=True)
    ply_count = models.PositiveIntegerField(default=0)
    pgn = models.TextField()
    notes = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.white or '?'} vs {self.black or '?'} ({self.result or '*'})"

class Move(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='moves')
    move_number = models.IntegerField(default=0)
    from_square = models.CharField(max_length=2)
    to_square = models.CharField(max_length=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Move {self.move_number}: {self.from_square} to {self.to_square}"

class OpeningDatabase(models.Model):
    name = models.CharField(max_length=100)
    moves = models.TextField()

    def __str__(self):
        return self.name




class Preparation(models.Model):
    # opening prep, the lines are saved as pgn with variations
    SIDE_CHOICES = [('w', 'White'), ('b', 'Black')]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preparations')
    title = models.CharField(max_length=120)
    side = models.CharField(max_length=1, choices=SIDE_CHOICES, default='w')
    opponent = models.CharField(max_length=100, blank=True)   # optional
    notes = models.TextField(blank=True)
    pgn = models.TextField(blank=True)
    start_fen = models.CharField(max_length=100, blank=True)  # empty = normal start
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated']

    def __str__(self):
        return self.title


class Article(models.Model):
    # body: empty line = new paragraph, ## = heading, > = quote
    # [board fen="..." moves="e4 e5 Nf3" caption="..."] = animated board
    CATEGORY_CHOICES = [('history', 'History'), ('openings', 'Openings'),
                        ('endgames', 'Endgames'), ('tactics', 'Tactics'), ('classics', 'Classic games')]

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    dek = models.CharField(max_length=300, blank=True)       # short line under the title
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='history')
    author = models.CharField(max_length=80, default='SovoChess')
    image = models.CharField(max_length=120, blank=True)     # path in static, like img/art/x.jpg
    image_credit = models.CharField(max_length=200, blank=True)
    cover_fen = models.CharField(max_length=100, blank=True) # board shown if theres no image
    body = models.TextField()
    published = models.DateField()
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-published', 'title']

    @property
    def reading_minutes(self):
        return max(1, round(len(self.body.split()) / 220))

    def __str__(self):
        return self.title
