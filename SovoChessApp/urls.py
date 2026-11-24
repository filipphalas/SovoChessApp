from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from sovochess import views, library_views, site_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # playing
    path('game/start/', views.start_game, name='start_game'),
    path('game/<int:game_id>/', views.game_view, name='game'),
    path('game/<int:game_id>/move/', views.make_move, name='make_move'),
    path('game/<int:game_id>/position/', views.get_position, name='get_position'),
    path('game/<int:game_id>/flag/', views.flag_game, name='flag_game'),
    path('game/<int:game_id>/resign/', views.resign_game, name='resign_game'),
    path('game/<int:game_id>/result/', views.post_game, name='post_game'),

    # analysis + game library
    path('analysis/', library_views.analysis, name='analysis'),
    path('analysis/save/', library_views.save_analysis, name='save_analysis'),
    path('analysis/prep/save/', library_views.prep_save, name='prep_save'),
    path('analysis/prep/<int:pk>/', library_views.prep_open, name='prep_open'),
    path('analysis/prep/<int:pk>/delete/', library_views.prep_delete, name='prep_delete'),
    path('library/', library_views.library, name='library'),
    path('library/import/', library_views.library_import, name='library_import'),
    path('library/export.pgn', library_views.library_export, name='library_export'),
    path('library/game/<int:pk>/', library_views.saved_game, name='saved_game'),
    path('library/game/<int:pk>/delete/', library_views.saved_game_delete, name='saved_game_delete'),
    path('library/collections/new/', library_views.collection_create, name='collection_create'),
    path('library/collections/<int:pk>/delete/', library_views.collection_delete, name='collection_delete'),

    # site
    path('news/', site_views.news_page, name='news'),
    path('read/', RedirectView.as_view(pattern_name='news', permanent=False)),
    path('guides/', site_views.articles, name='articles'),
    path('guides/<slug:slug>/', site_views.article_detail, name='article'),
    path('news.json', site_views.news_json, name='news_json'),
    path('privacy/', site_views.privacy, name='privacy'),
    path('terms/', site_views.terms, name='terms'),
    path('licenses/', site_views.licenses, name='licenses'),
    path('account/', site_views.account, name='account'),
    path('account/export/', site_views.account_export, name='account_export'),
    path('account/delete/', site_views.account_delete, name='account_delete'),
]
