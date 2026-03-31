from django.db import models
from django.conf import settings


class BgImport(models.Model):
    """Registre des imports de Balance Générale."""
    STATUTS = [
        ('en_attente',  'En attente de traitement'),
        ('traitement',  'En cours de traitement'),
        ('traite',      'Traité — en attente validation'),
        ('valide',      'Validé par la DF'),
        ('rejete',      'Rejeté'),
        ('gele',        'Gelé — période clôturée'),
    ]
    fichier_nom       = models.CharField(max_length=255)
    fichier_path      = models.CharField(max_length=500)
    exercice          = models.IntegerField(help_text="Année comptable ex: 2025")
    periode           = models.IntegerField(help_text="Numéro de période G/L (1-16)")
    date_import       = models.DateTimeField(auto_now_add=True)
    importe_par       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='bg_imports')
    statut            = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    nb_lignes         = models.IntegerField(default=0)
    nb_anomalies      = models.IntegerField(default=0)
    valide_par        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bg_validations')
    date_validation   = models.DateTimeField(null=True, blank=True)
    commentaire_df    = models.TextField(blank=True)
    erreur_traitement = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_import']
        verbose_name = 'Import Balance Générale'
        verbose_name_plural = 'Imports Balance Générale'
        unique_together = [('exercice', 'periode')]

    def __str__(self):
        return f"BG {self.exercice} — P{self.periode:02d}"

    @property
    def label_periode(self):
        mois = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc']
        if 1 <= self.periode <= 12:
            return f"{mois[self.periode-1]} {self.exercice}"
        return f"P{self.periode} {self.exercice}"

    @property
    def est_valide(self):
        return self.statut in ('valide', 'gele')

    @property
    def peut_etre_valide(self):
        return self.statut == 'traite' and self.nb_anomalies == 0


class BgLigne(models.Model):
    """Données brutes par compte et entité."""
    ENTITES = [
        ('CIE',        'CIE'),
        ('Secteur',    'Secteur'),
        ('Exploitant', 'Exploitant'),
    ]
    SENS = [('D', 'Débiteur'), ('C', 'Créditeur')]

    bg_import         = models.ForeignKey(BgImport, on_delete=models.CASCADE, related_name='lignes')
    num_compte        = models.CharField(max_length=20)
    intitule          = models.CharField(max_length=255)
    classe            = models.IntegerField()
    entite            = models.CharField(max_length=20, choices=ENTITES)
    report            = models.BigIntegerField(default=0)
    activite_periode  = models.BigIntegerField(default=0)
    activite_exercice = models.BigIntegerField(default=0)
    total             = models.BigIntegerField(default=0)
    is_interco        = models.BooleanField(default=False)
    is_ran            = models.BooleanField(default=False)
    sens_normal       = models.CharField(max_length=1, choices=SENS, default='D')

    class Meta:
        ordering = ['num_compte', 'entite']
        indexes = [
            models.Index(fields=['bg_import', 'entite']),
            models.Index(fields=['bg_import', 'classe']),
            models.Index(fields=['num_compte']),
        ]

    def __str__(self):
        return f"{self.num_compte} — {self.entite}"


class BgAgregat(models.Model):
    """Agrégats financiers calculés par classe et entité."""
    ENTITES = [('CIE','CIE'),('Secteur','Secteur'),('Exploitant','Exploitant')]
    TYPES   = [
        ('classe',      'Agrégat par classe'),
        ('bilan_actif', 'Bilan actif'),
        ('bilan_passif','Bilan passif'),
        ('resultat',    'Compte de résultat'),
        ('tresorerie',  'Trésorerie nette'),
        ('kpi',         'KPI calculé'),
    ]
    bg_import        = models.ForeignKey(BgImport, on_delete=models.CASCADE, related_name='agregats')
    type_agregat     = models.CharField(max_length=20, choices=TYPES)
    entite           = models.CharField(max_length=20, choices=ENTITES)
    libelle          = models.CharField(max_length=100)
    classe           = models.IntegerField(null=True, blank=True)
    valeur_report    = models.BigIntegerField(default=0)
    valeur_periode   = models.BigIntegerField(default=0)
    valeur_exercice  = models.BigIntegerField(default=0)
    valeur_total     = models.BigIntegerField(default=0)

    class Meta:
        ordering = ['entite', 'classe']

    def __str__(self):
        return f"{self.libelle} — {self.entite} ({self.bg_import})"


class BgAlerte(models.Model):
    """Anomalies et alertes détectées lors du traitement."""
    NIVEAUX = [
        ('critique', 'Critique — bloque la validation'),
        ('haute',    'Haute — justification requise'),
        ('moyenne',  'Moyenne — surveillance'),
        ('info',     'Information'),
    ]
    STATUTS = [
        ('ouverte',   'Ouverte'),
        ('justifiee', 'Justifiée'),
        ('resolue',   'Résolue'),
        ('ignoree',   'Ignorée'),
    ]
    bg_import        = models.ForeignKey(BgImport, on_delete=models.CASCADE, related_name='alertes')
    niveau           = models.CharField(max_length=10, choices=NIVEAUX)
    code_regle       = models.CharField(max_length=50)
    message          = models.TextField()
    num_compte       = models.CharField(max_length=20, blank=True)
    entite           = models.CharField(max_length=20, blank=True)
    valeur_constatee = models.BigIntegerField(null=True, blank=True)
    statut           = models.CharField(max_length=15, choices=STATUTS, default='ouverte')
    justification    = models.TextField(blank=True)
    traite_par       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='alertes_bg_traitees')
    traite_le        = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['niveau', 'num_compte']

    def __str__(self):
        return f"[{self.niveau.upper()}] {self.code_regle} — {self.message[:60]}"


class BgComparaison(models.Model):
    """Comparaison N/N-1 par compte et entité."""
    bg_import_courant  = models.ForeignKey(BgImport, on_delete=models.CASCADE, related_name='comparaisons_courantes')
    bg_import_precedent= models.ForeignKey(BgImport, on_delete=models.CASCADE, related_name='comparaisons_precedentes', null=True, blank=True)
    num_compte         = models.CharField(max_length=20)
    entite             = models.CharField(max_length=20)
    total_courant      = models.BigIntegerField(default=0)
    total_precedent    = models.BigIntegerField(default=0)
    variation_absolue  = models.BigIntegerField(default=0)
    variation_pct      = models.FloatField(null=True, blank=True)
    is_variation_forte = models.BooleanField(default=False)

    class Meta:
        ordering = ['num_compte', 'entite']


class BgAuditTrail(models.Model):
    """Journal d'audit de toutes les actions sur les BG."""
    ACTIONS = [
        ('import',     'Import fichier'),
        ('validation', 'Validation DF'),
        ('rejet',      'Rejet'),
        ('gel',        'Gel période'),
        ('alerte',     'Traitement alerte'),
        ('export',     'Export rapport'),
    ]
    bg_import  = models.ForeignKey(BgImport, on_delete=models.CASCADE, related_name='audit')
    action     = models.CharField(max_length=20, choices=ACTIONS)
    utilisateur= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    detail     = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} — {self.bg_import} — {self.created_at:%d/%m/%Y %H:%M}"


class BgRegleAlerte(models.Model):
    """Règles d'alerte paramétrables par la DF."""
    NIVEAUX = [('critique','Critique'),('haute','Haute'),('moyenne','Moyenne')]
    code          = models.CharField(max_length=50, unique=True)
    libelle       = models.CharField(max_length=200)
    niveau        = models.CharField(max_length=10, choices=NIVEAUX)
    description   = models.TextField(blank=True)
    seuil         = models.FloatField(null=True, blank=True, help_text="Seuil numérique si applicable")
    active        = models.BooleanField(default=True)
    ordre         = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'code']

    def __str__(self):
        return f"[{self.niveau}] {self.code}"
