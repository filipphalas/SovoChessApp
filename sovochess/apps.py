from django.apps import AppConfig


class ChessConfig(AppConfig):
    # folder is sovochess bc python-chess is also called chess
    # label stays chess so the db tables and migrations dont change
    name = 'sovochess'
    label = 'chess'
