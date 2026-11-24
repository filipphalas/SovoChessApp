from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Article, Collection, Game, PlayerProfile, Preparation, SavedGame, User

admin.site.register(User, UserAdmin)
admin.site.register(PlayerProfile)
admin.site.register(Game)
admin.site.register(Collection)
admin.site.register(SavedGame)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'published', 'is_published')
    list_filter = ('category', 'is_published')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Preparation)
class PreparationAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'side', 'opponent', 'updated')
