from django.db import models
from django.conf import settings


COULEURS_SD = [
    ('#003F7F', 'Bleu CIE (défaut)'),
    ('#0056A8', 'Bleu clair'),
    ('#1a7cc1', 'Bleu azur'),
    ('#17a2b8', 'Cyan'),
    ('#28a745', 'Vert'),
    ('#20c997', 'Vert menthe'),
    ('#6f42c1', 'Violet'),
    ('#e83e8c', 'Rose'),
    ('#fd7e14', 'Orange'),
    ('#F5A623', 'Or CIE'),
    ('#dc3545', 'Rouge'),
    ('#6c757d', 'Gris'),
]


class SousDirection(models.Model):
    code        = models.CharField(max_length=20, unique=True)
    libelle     = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    couleur     = models.CharField(
        max_length=7, default='#003F7F',
        choices=COULEURS_SD,
        help_text="Couleur d'identité visuelle de la sous-direction"
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sous_directions_responsable'
    )
    actif       = models.BooleanField(default=True)
    ordre       = models.PositiveSmallIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordre', 'code']
        verbose_name = 'Sous-Direction'
        verbose_name_plural = 'Sous-Directions'

    def __str__(self):
        return f"{self.code} — {self.libelle}"

    def couleur_texte(self):
        """Retourne noir ou blanc selon la luminosité de la couleur de fond"""
        hex_col = self.couleur.lstrip('#')
        r, g, b = int(hex_col[0:2], 16), int(hex_col[2:4], 16), int(hex_col[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b)
        return '#000000' if luminance > 160 else '#FFFFFF'

    def get_modules(self):
        MODULES_PAR_SD = {
            'SDCC': [
                {'nom': 'NMPF',              'href': '/sdcc/nmpf/',              'icone': 'bi-bar-chart-line', 'disponible': False},
                {'nom': 'Suivi Facturation', 'href': '/sdcc/suivi-facturation/', 'icone': 'bi-receipt',        'disponible': False},
            ],
            'SDPCC': [
                {'nom': 'Projet Comptable',  'href': '/sdpcc/projet-comptable/', 'icone': 'bi-folder2-open',   'disponible': False},
            ],
        }
        return MODULES_PAR_SD.get(self.code, [])

    def get_stats(self):
        """Statistiques panoramiques pour la card portail"""
        from apps.authentication.models import Utilisateur
        # Membres dans cette SD (via sections)
        nb_membres = Utilisateur.objects.filter(
            sections_lien__section__sous_direction=self,
            est_actif_cie=True
        ).distinct().count()

        stats = {
            'nb_membres':   nb_membres,
            'nb_sections':  self.sections.filter(actif=True).count(),
            'nb_activites_ouvertes':  0,
            'nb_activites_en_retard': 0,
            'nb_activites_en_attente': 0,
        }

        # Statistiques activités (disponibles en P2)
        try:
            from apps.operations.models import Activite
            from django.utils import timezone
            today = timezone.now().date()
            activites = Activite.objects.filter(section__sous_direction=self)
            stats['nb_activites_ouvertes']   = activites.filter(statut__in=['ouverte', 'en_cours']).count()
            stats['nb_activites_en_retard']  = activites.filter(statut__in=['ouverte', 'en_cours'], date_butoir__lt=today).count()
            stats['nb_activites_en_attente'] = activites.filter(statut='en_attente').count()
        except Exception:
            pass  # Module operations pas encore disponible (P2)

        return stats


class Section(models.Model):
    sous_direction  = models.ForeignKey(SousDirection, on_delete=models.CASCADE, related_name='sections')
    code            = models.CharField(max_length=20)
    libelle         = models.CharField(max_length=200)
    description     = models.TextField(blank=True)
    responsable     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sections_responsable'
    )
    actif           = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sous_direction', 'code']
        unique_together = [('sous_direction', 'code')]
        verbose_name = 'Section'
        verbose_name_plural = 'Sections'

    def __str__(self):
        return f"{self.sous_direction.code} / {self.code} — {self.libelle}"


class UtilisateurSection(models.Model):
    utilisateur      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sections_lien')
    section          = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='utilisateurs_lien')
    est_principale   = models.BooleanField(default=True)
    date_affectation = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = [('utilisateur', 'section')]
        verbose_name = 'Affectation Section'
        verbose_name_plural = 'Affectations Sections'

    def __str__(self):
        return f"{self.utilisateur} → {self.section}"


class PIP(models.Model):
    code           = models.CharField(max_length=30, unique=True)
    libelle        = models.CharField(max_length=200)
    description    = models.TextField(blank=True)
    email          = models.EmailField(blank=True)
    telephone      = models.CharField(max_length=20, blank=True)
    sous_direction = models.ForeignKey(
        SousDirection, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pips'
    )
    actif      = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'PIP'
        verbose_name_plural = 'PIP'

    def __str__(self):
        return f"{self.code} — {self.libelle}"
