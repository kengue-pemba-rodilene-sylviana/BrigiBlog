from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Adresse e-mail")
    photo = models.ImageField(
        upload_to="profils/",
        blank=True,
        null=True,
        verbose_name="Photo de profil"
    )
    bio = models.TextField(blank=True, verbose_name="Présentation")

    groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="blog_users",
        related_query_name="blog_user",
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        blank=True,
        related_name="blog_users",
        related_query_name="blog_user",
    )

    def __str__(self):
        return self.username
    
class Article(models.Model):

    auteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='articles'
    )

    contenu = models.TextField(
        verbose_name="Contenu de la publication",
        blank=True
    )

    image = models.ImageField(
        upload_to="publications/images/",
        blank=True,
        null=True,
        verbose_name="Image"
    )

    fichier_pdf = models.FileField(
        upload_to="publications/documents/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf'])
        ],
        verbose_name="Document PDF"
    )
    
    video = models.FileField(
    upload_to="publications/videos/",
    blank=True,
    null=True,
    validators=[
        FileExtensionValidator(
            allowed_extensions=['mp4', 'webm', 'mov']
        )
    ],
    verbose_name="Vidéo"
)

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-date_creation']

    def clean(self):
        super().clean()
        if (
            not (self.contenu or '').strip()
            and not self.image
            and not self.fichier_pdf
            and not self.video
        ):
            raise ValidationError(
                "Ajoute un texte, une image, un document PDF ou une vidéo."
            )

    def __str__(self):
        return f"Publication de {self.auteur.username}"



class Like(models.Model):

    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes'
    )

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='likes'
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['utilisateur', 'article'],
                name='unique_like_utilisateur_article'
            )
        ]

    def __str__(self):
        return f"{self.utilisateur.username} aime {self.article_id}"

class Commentaire(models.Model):

    auteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='commentaires'
    )

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='commentaires'
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='reponses'
    )

    contenu = models.TextField(
        verbose_name="Contenu du commentaire"
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['date_creation']

    def clean(self):
        super().clean()

        if self.parent:
            if self.parent_id == self.pk:
                raise ValidationError(
                    "Un commentaire ne peut pas être sa propre réponse."
                )

            if self.parent.parent_id is not None:
                raise ValidationError(
                    "Les réponses imbriquées ne sont pas autorisées."
                )

            if self.parent.article_id != self.article_id:
                raise ValidationError(
                    "La réponse doit concerner la même publication."
                )

    def __str__(self):
        return f"Commentaire de {self.auteur.username}"
