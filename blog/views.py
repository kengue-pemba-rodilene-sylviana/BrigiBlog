
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django import forms
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef, Prefetch
from django.utils.http import url_has_allowed_host_and_scheme

from .models import User, Article, Like, Commentaire

class InscriptionForm(UserCreationForm):

    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=150,
        help_text=(
            "Obligatoire. 150 caractères maximum. "
            "Lettres, chiffres et @/./+/-/_ uniquement."
        ),
        error_messages={
            'required': "Le nom d'utilisateur est obligatoire.",
            'max_length': "Le nom d'utilisateur ne doit pas dépasser 150 caractères."
        }
    )

    first_name = forms.CharField(
        label="Prénom",
        required=False
    )

    last_name = forms.CharField(
        label="Nom",
        required=False
    )

    email = forms.EmailField(
        label="Adresse e-mail",
        required=True,
        error_messages={
            'required': "L'adresse e-mail est obligatoire.",
            'invalid': "Veuillez saisir une adresse e-mail valide."
        }
    )

    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput,
        help_text=(
            "Votre mot de passe doit contenir au moins 8 caractères, "
            "ne pas être trop simple et ne pas être uniquement numérique."
        )
    )

    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput,
        help_text="Saisissez à nouveau le même mot de passe pour vérification."
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2'
        ]



class ArticleForm(forms.ModelForm):

    class Meta:
        model = Article
        fields = ['contenu', 'image', 'fichier_pdf', 'video']

        widgets = {
            'contenu': forms.Textarea(attrs={
                'placeholder': "Qu’aimerais-tu partager ?",
                'rows': 4,
                'class': 'form-control'
            }),

            'image': forms.ClearableFileInput(attrs={
                'accept': 'image/jpeg,image/png,image/webp'
            }),

            'fichier_pdf': forms.ClearableFileInput(attrs={
                'accept': 'application/pdf'
            }),

            'video': forms.ClearableFileInput(attrs={
                'accept': 'video/mp4,video/webm,video/quicktime'
            })
        }

    def clean(self):
        cleaned_data = super().clean()

        contenu = (cleaned_data.get('contenu') or '').strip()
        image = cleaned_data.get('image')
        fichier_pdf = cleaned_data.get('fichier_pdf')
        video = cleaned_data.get('video')

        if not contenu and not image and not fichier_pdf and not video:
            raise forms.ValidationError(
                "Ajoute un texte, une image, un PDF ou une vidéo."
            )

        if image and image.size > 5 * 1024 * 1024:
            self.add_error(
                'image',
                "L'image ne doit pas dépasser 5 Mo."
            )

        if fichier_pdf and fichier_pdf.size > 10 * 1024 * 1024:
            self.add_error(
                'fichier_pdf',
                "Le PDF ne doit pas dépasser 10 Mo."
            )

        if video and video.size > 50 * 1024 * 1024:
            self.add_error(
                'video',
                "La vidéo ne doit pas dépasser 50 Mo."
            )

        return cleaned_data


class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'placeholder': "Écrire un commentaire...",
                'rows': 2
            })
        }

    def clean_contenu(self):
        contenu = self.cleaned_data['contenu'].strip()

        if not contenu:
            raise forms.ValidationError(
                "Le commentaire ne peut pas être vide."
            )

        return contenu


class ProfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'photo',
            'bio'
        ]

def accueil(request):
    commentaires_principaux = Commentaire.objects.filter(
        parent__isnull=True
    ).select_related(
        'auteur'
    ).prefetch_related(
        'reponses__auteur'
    )

    publications = Article.objects.select_related(
        'auteur'
    ).annotate(
        nombre_likes=Count('likes', distinct=True),
        nombre_commentaires=Count('commentaires', distinct=True)
    ).prefetch_related(
        Prefetch(
            'commentaires',
            queryset=commentaires_principaux,
            to_attr='commentaires_principaux'
        )
    ).order_by('-date_creation')

    if request.user.is_authenticated:
        publications = publications.annotate(
            est_aime=Exists(
                Like.objects.filter(
                    article_id=OuterRef('pk'),
                    utilisateur=request.user
                )
            )
        )

    paginator = Paginator(publications, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accueil.html', {
        'publications': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'form_commentaire': CommentaireForm(),
    })


def inscription(request):

    if request.user.is_authenticated:
        return redirect('feed')

    if request.method == 'POST':
        form = InscriptionForm(request.POST)

        if form.is_valid():
            utilisateur = form.save()
            login(request, utilisateur)

            messages.success(
                request,
                "Bienvenue sur Brigi+ Chat !"
            )

            return redirect('feed')

    else:
        form = InscriptionForm()

    return render(request, 'inscription.html', {
        'form': form
    })


def connexion(request):

    if request.user.is_authenticated:
        return redirect('feed')

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        utilisateur = authenticate(
            request,
            username=username,
            password=password
        )

        if utilisateur is not None:
            login(request, utilisateur)
            return redirect('feed')

        messages.error(
            request,
            "Nom d'utilisateur ou mot de passe incorrect."
        )

    return render(request, 'connexion.html')


@login_required
def deconnexion(request):

    if request.method == 'POST':
        logout(request)
        return redirect('accueil')

    return redirect('feed')


@login_required
def feed(request):

    publications = Article.objects.select_related(
        'auteur'
    ).annotate(
        nombre_likes=Count('likes', distinct=True),
        nombre_commentaires=Count('commentaires', distinct=True)
    ).order_by('-date_creation')

    paginator = Paginator(publications, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'feed.html', {
        'publications': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'form': ArticleForm()
    })

@login_required
def creer_article(request):

    if request.method != 'POST':
        return redirect('feed')

    # Récupérer les données ET les fichiers envoyés
    form = ArticleForm(request.POST, request.FILES)

    if form.is_valid():
        article = form.save(commit=False)
        article.auteur = request.user
        article.save()

        messages.success(
            request,
            "Publication ajoutée avec succès."
        )
        return redirect('feed')

    # En cas d'erreur, conserver les erreurs dans le formulaire
    publications = Article.objects.select_related(
        'auteur'
    ).annotate(
        nombre_likes=Count('likes', distinct=True),
        nombre_commentaires=Count('commentaires', distinct=True)
    ).order_by('-date_creation')

    paginator = Paginator(publications, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'feed.html', {
        'publications': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'form': form
    })

@login_required
def detail_article(request, article_id):

    article = get_object_or_404(
        Article.objects.select_related('auteur'),
        pk=article_id
    )

    commentaires = article.commentaires.filter(
        parent__isnull=True
    ).select_related(
        'auteur'
    ).prefetch_related(
        'reponses__auteur'
    )

    return render(request, 'detail_article.html', {
        'article': article,
        'commentaires': commentaires,
        'form': CommentaireForm()
    })

@login_required
def aimer_article(request, article_id):

    if request.method == 'POST':

        article = get_object_or_404(
            Article,
            pk=article_id
        )

        like, created = Like.objects.get_or_create(
            utilisateur=request.user,
            article=article
        )

        if not created:
            like.delete()

    next_url = request.POST.get('next')

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(next_url)

    return redirect(
        request.META.get('HTTP_REFERER', 'feed')
    )
    
@login_required
def ajouter_commentaire(request, article_id):

    article = get_object_or_404(
        Article,
        pk=article_id
    )

    if request.method == 'POST':

        form = CommentaireForm(request.POST)

        if form.is_valid():

            commentaire = form.save(commit=False)
            commentaire.auteur = request.user
            commentaire.article = article
            commentaire.save()

            messages.success(
                request,
                "Commentaire ajouté."
            )

    next_url = request.POST.get('next')

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(next_url)

    return redirect(
        'detail_article',
        article_id=article.id
    )


@login_required
def repondre_commentaire(request, commentaire_id):

    parent = get_object_or_404(
        Commentaire,
        pk=commentaire_id,
        parent__isnull=True
    )

    if request.method == 'POST':

        form = CommentaireForm(request.POST)

        if form.is_valid():

            reponse = form.save(commit=False)
            reponse.auteur = request.user
            reponse.article = parent.article
            reponse.parent = parent
            reponse.save()

            messages.success(
                request,
                "Réponse ajoutée."
            )

    return redirect(
        'detail_article',
        article_id=parent.article.id
    )


@login_required
def supprimer_commentaire(request, commentaire_id):

    commentaire = get_object_or_404(
        Commentaire,
        pk=commentaire_id
    )

    if request.method == 'POST':

        if commentaire.auteur == request.user:

            article_id = commentaire.article_id
            commentaire.delete()

            messages.success(
                request,
                "Commentaire supprimé."
            )

            return redirect(
                'detail_article',
                article_id=article_id
            )

        messages.error(
            request,
            "Tu ne peux pas supprimer ce commentaire."
        )

    return redirect(
        'detail_article',
        article_id=commentaire.article_id
    )

@login_required
def profil(request, username=None):

    utilisateur = get_object_or_404(
        User,
        username=username
    ) if username else request.user

    publications = utilisateur.articles.select_related(
        'auteur'
    ).annotate(
        nombre_likes=Count('likes', distinct=True)
    ).order_by('-date_creation')

    return render(request, 'profil.html', {
        'profil': utilisateur,
        'publications': publications,
        'form': ProfilForm(instance=utilisateur)
        if utilisateur == request.user else None
    })


@login_required
def modifier_profil(request):

    if request.method != 'POST':
        return redirect('profil')

    form = ProfilForm(
        request.POST,
        request.FILES,
        instance=request.user
    )

    if form.is_valid():
        form.save()

        messages.success(
            request,
            "Ton profil a été mis à jour avec succès !"
        )

        return redirect('profil')

    # En cas d'erreur, conserver le formulaire et afficher les erreurs
    publications = request.user.articles.select_related(
        'auteur'
    ).annotate(
        nombre_likes=Count('likes', distinct=True)
    ).order_by('-date_creation')

    messages.error(
        request,
        "Certaines informations n'ont pas été enregistrées. Vérifie les erreurs ci-dessous."
    )

    return render(request, 'profil.html', {
        'profil': request.user,
        'publications': publications,
        'form': form
    })
