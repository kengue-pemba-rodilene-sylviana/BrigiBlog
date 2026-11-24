
from django.urls import path
from . import views

urlpatterns = [
    # Pages publiques
    path('', views.accueil, name='accueil'),
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),

    # Fil d'actualité
    path('feed/', views.feed, name='feed'),

    # Publications
    path('article/creer/', views.creer_article, name='creer_article'),
    path(
        'article/<int:article_id>/',
        views.detail_article,
        name='detail_article'
    ),
    path(
        'article/<int:article_id>/aimer/',
        views.aimer_article,
        name='aimer_article'
    ),

    # Commentaires
    path(
        'article/<int:article_id>/commenter/',
        views.ajouter_commentaire,
        name='ajouter_commentaire'
    ),
    path(
        'commentaire/<int:commentaire_id>/repondre/',
        views.repondre_commentaire,
        name='repondre_commentaire'
    ),
    path(
        'commentaire/<int:commentaire_id>/supprimer/',
        views.supprimer_commentaire,
        name='supprimer_commentaire'
    ),

    # Profils
    path('profil/', views.profil, name='profil'),
    path('profil/modifier/', views.modifier_profil, name='modifier_profil'),
    path('profil/<str:username>/', views.profil, name='profil_utilisateur'),
]
