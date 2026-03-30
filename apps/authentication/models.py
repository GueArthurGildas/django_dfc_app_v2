from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    """Rôles applicatifs : Admin, DFC, DA, SD, Chef de Section, Cadre, Maitrise, Visiteur"""
    ROLES = [
        ('admin',       'Administrateur'),
        ('dfc',         'Directeur Financier'),
        ('da',          'Directeur Adjoint'),
        ('sd',          'Sous-Directeur'),
        ('chef',        'Chef de Section'),
        ('cadre',       'Cadre'),
        ('maitrise',    'Agent de Maîtrise'),
        ('visiteur',    'Visiteur'),
    ]
    code        = models.CharField(max_length=20, choices=ROLES, unique=True)
    libelle     = models.CharField(max_length=100)
    niveau      = models.PositiveSmallIntegerField(help_text="Plus le niveau est bas, plus le rôle est élevé")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['niveau']
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'

    def __str__(self):
        return self.libelle


class Utilisateur(AbstractUser):
    """Utilisateur personnalisé CIE Manager"""
    matricule       = models.CharField(max_length=20, unique=True, null=True, blank=True)
    telephone       = models.CharField(max_length=20, blank=True)
    role            = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='utilisateurs')
    photo           = models.ImageField(upload_to='photos/', null=True, blank=True)
    est_actif_cie   = models.BooleanField(default=True, help_text="Actif dans CIE (distinct du is_active Django)")
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.get_full_name() or self.username}"

    @property
    def nom_complet(self):
        return self.get_full_name() or self.username

    @property
    def role_code(self):
        return self.role.code if self.role else None

    def get_section(self):
        """Retourne la section principale de l'utilisateur"""
        lien = self.sections_lien.filter(est_principale=True).select_related('section').first()
        if lien:
            return lien.section
        lien = self.sections_lien.select_related('section').first()
        return lien.section if lien else None

    def get_sous_direction(self):
        """Retourne la sous-direction via la section principale"""
        section = self.get_section()
        return section.sous_direction if section else None

    def peut_voir_sous_direction(self, sd):
        """Vérifie si l'utilisateur a accès à une sous-direction donnée"""
        if not self.role:
            return False
        code = self.role.code
        if code in ('admin', 'dfc', 'da'):
            return True
        if code == 'sd':
            return self.get_sous_direction() == sd
        return self.get_sous_direction() == sd


class Annonce(models.Model):
    """Message d'information affiché à tous les utilisateurs lors de la connexion."""
    titre       = models.CharField(max_length=200)
    description = models.TextField()
    image       = models.ImageField(upload_to='annonces/', null=True, blank=True)
    date_debut  = models.DateTimeField(help_text="Date de début d'affichage")
    date_fin    = models.DateTimeField(help_text="Date de fin d'affichage")
    actif       = models.BooleanField(default=True)
    created_by  = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, related_name='annonces_creees')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_debut']
        verbose_name = 'Annonce'
        verbose_name_plural = 'Annonces'

    def __str__(self):
        return self.titre

    @classmethod
    def get_actives(cls):
        from django.utils import timezone
        now = timezone.now()
        return cls.objects.filter(actif=True, date_debut__lte=now, date_fin__gte=now)
