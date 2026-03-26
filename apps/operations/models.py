from django.db import models
from django.conf import settings
from django.utils import timezone


class Dossier(models.Model):
    titre          = models.CharField(max_length=200)
    description    = models.TextField(blank=True)
    section        = models.ForeignKey('organisation.Section', on_delete=models.CASCADE, related_name='dossiers')
    responsable    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='dossiers_responsable')
    est_actif      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dossier'
        verbose_name_plural = 'Dossiers'

    def __str__(self):
        return self.titre

    @property
    def nb_activites(self):
        return self.activites.count()

    @property
    def taux_completion(self):
        total = self.activites.count()
        if not total:
            return 0
        return round(self.activites.filter(statut='cloturee').count() / total * 100)


class Activite(models.Model):
    STATUTS = [
        ('ouverte',    'Ouverte'),
        ('en_cours',   'En cours'),
        ('en_attente', 'En attente'),
        ('cloturee',   'Clôturée'),
    ]
    TYPES = [
        ('ponctuelle', 'Ponctuelle'),
        ('mensuelle',  'Mensuelle récurrente'),
        ('trimestrielle', 'Trimestrielle'),
    ]

    # Identification
    titre           = models.CharField(max_length=300)
    description     = models.TextField(blank=True)
    type_activite   = models.CharField(max_length=20, choices=TYPES, default='ponctuelle')
    statut          = models.CharField(max_length=20, choices=STATUTS, default='ouverte')

    # Organisation
    dossier         = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='activites')
    section         = models.ForeignKey('organisation.Section', on_delete=models.CASCADE, related_name='activites')
    pips            = models.ManyToManyField('organisation.PIP', through='ActivitePIP', blank=True)

    # Dates — les 4 demandées
    date_ouverture          = models.DateField(default=timezone.now)
    date_butoir             = models.DateField(verbose_name="Date butoir (échéance)")
    date_intermediaire      = models.DateField(null=True, blank=True, verbose_name="Date intermédiaire")
    date_intermediaire_init = models.DateField(null=True, blank=True, verbose_name="Date intermédiaire initiale")
    date_realisation        = models.DateField(null=True, blank=True, verbose_name="Date de réalisation effective")
    nb_reports              = models.PositiveSmallIntegerField(default=0)

    # Avancement
    etat_avancement = models.PositiveSmallIntegerField(default=0, help_text="0 à 100 %")

    # Indicateurs calculés
    est_dans_delai  = models.BooleanField(null=True, blank=True,
                                          help_text="True si clôturée avant ou à la date butoir")
    est_kpi         = models.BooleanField(default=False)
    est_arrete      = models.BooleanField(default=False, verbose_name="Arrêté comptable")

    # Clonage mensuel
    activite_parente = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='clones')
    mois_reference   = models.CharField(max_length=7, blank=True, help_text="YYYY-MM")

    # Clôture
    cloture_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='activites_cloturees')
    cloture_le  = models.DateTimeField(null=True, blank=True)

    created_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='activites_creees')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)  # soft delete

    class Meta:
        ordering = ['date_butoir', '-created_at']
        verbose_name = 'Activité'
        verbose_name_plural = 'Activités'

    def __str__(self):
        return self.titre

    def get_statut_display_badge(self):
        colors = {
            'ouverte':    ('dbeafe', '1d4ed8'),
            'en_cours':   ('d1fae5', '065f46'),
            'en_attente': ('fef3c7', '92400e'),
            'cloturee':   ('f3f4f6', '374151'),
        }
        bg, fg = colors.get(self.statut, ('f3f4f6', '374151'))
        return bg, fg

    @property
    def est_en_retard(self):
        if self.statut in ('cloturee',):
            return False
        return self.date_butoir < timezone.now().date()

    @property
    def jours_restants(self):
        delta = self.date_butoir - timezone.now().date()
        return delta.days

    @property
    def couleur_jauge(self):
        if self.etat_avancement < 31:
            return '#dc3545'
        elif self.etat_avancement < 70:
            return '#F5A623'
        return '#28a745'

    def calculer_est_dans_delai(self):
        """Appelé à la clôture : True si réalisée avant ou à la date butoir"""
        if self.statut == 'cloturee' and self.date_realisation:
            return self.date_realisation <= self.date_butoir
        return None


class ActiviteActeur(models.Model):
    ROLES = [
        ('responsable', 'Responsable'),
        ('acteur',      'Acteur'),
    ]
    activite          = models.ForeignKey(Activite, on_delete=models.CASCADE, related_name='acteurs')
    utilisateur       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activites_acteur')
    role_activite     = models.CharField(max_length=20, choices=ROLES, default='acteur')
    peut_recevoir_mail = models.BooleanField(default=True)
    date_affectation  = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = [('activite', 'utilisateur')]
        verbose_name = 'Acteur d\'activité'

    def __str__(self):
        return f"{self.utilisateur} — {self.get_role_activite_display()} sur {self.activite}"


class ActivitePIP(models.Model):
    activite = models.ForeignKey(Activite, on_delete=models.CASCADE)
    pip      = models.ForeignKey('organisation.PIP', on_delete=models.CASCADE)
    note     = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = [('activite', 'pip')]


class CommentaireActivite(models.Model):
    TYPES = [
        ('commentaire',  'Commentaire'),
        ('mise_a_jour',  'Mise à jour'),
        ('alerte',       'Alerte'),
        ('cloture',      'Clôture'),
    ]
    activite      = models.ForeignKey(Activite, on_delete=models.CASCADE, related_name='commentaires')
    auteur        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    type_comment  = models.CharField(max_length=20, choices=TYPES, default='commentaire')
    contenu       = models.TextField()
    avancement    = models.PositiveSmallIntegerField(default=0, help_text="Avancement déclaré au moment du commentaire")
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Commentaire'

    def __str__(self):
        return f"{self.get_type_comment_display()} par {self.auteur} sur {self.activite}"


class HistoriqueActivite(models.Model):
    activite        = models.ForeignKey(Activite, on_delete=models.CASCADE, related_name='historique')
    utilisateur     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    champ_modifie   = models.CharField(max_length=100)
    ancienne_valeur = models.TextField(blank=True)
    nouvelle_valeur = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Historique activité'

    def __str__(self):
        return f"{self.champ_modifie} modifié par {self.utilisateur}"


class AlerteMail(models.Model):
    TYPES = [
        ('ouverture', 'Ouverture'),
        ('rappel',    'Rappel'),
        ('report',    'Report de date'),
        ('cloture',   'Clôture'),
        ('clonage',   'Clonage'),
        ('manuelle',  'Alerte manuelle'),
    ]
    activite        = models.ForeignKey(Activite, on_delete=models.CASCADE, related_name='alertes')
    type_alerte     = models.CharField(max_length=20, choices=TYPES)
    destinataires   = models.TextField(help_text="Emails séparés par virgule")
    envoye_le       = models.DateTimeField(auto_now_add=True)
    succes          = models.BooleanField(default=True)

    class Meta:
        ordering = ['-envoye_le']
        verbose_name = 'Alerte mail'
