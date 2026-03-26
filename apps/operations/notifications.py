"""AlerteMailService — envoi des emails liés aux activités."""
from django.core.mail import send_mail
from django.conf import settings


class AlerteMailService:

    @staticmethod
    def _destinataires(activite):
        return [
            a.utilisateur.email
            for a in activite.acteurs.filter(peut_recevoir_mail=True)
            if a.utilisateur.email
        ]

    @staticmethod
    def _send(subject, message, destinataires):
        if not destinataires:
            return
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, destinataires, fail_silently=True)
        except Exception:
            pass

    @staticmethod
    def envoyer_ouverture(activite):
        dest = AlerteMailService._destinataires(activite)
        AlerteMailService._send(
            f"[CIE Manager] Nouvelle activité : {activite.titre}",
            f"L'activité « {activite.titre} » a été ouverte.\nDate butoir : {activite.date_butoir}",
            dest
        )

    @staticmethod
    def envoyer_rappel(activite):
        dest = AlerteMailService._destinataires(activite)
        jours = activite.jours_restants
        AlerteMailService._send(
            f"[CIE Manager] Rappel — {activite.titre} ({jours}j restants)",
            f"Rappel : l'activité « {activite.titre} » expire dans {jours} jour(s).\nDate butoir : {activite.date_butoir}",
            dest
        )

    @staticmethod
    def envoyer_alerte_report(activite, motif):
        dest = AlerteMailService._destinataires(activite)
        AlerteMailService._send(
            f"[CIE Manager] Report de date — {activite.titre}",
            f"La date intermédiaire de « {activite.titre} » a été reportée.\nNouvelle date : {activite.date_intermediaire}\nMotif : {motif}",
            dest
        )

    @staticmethod
    def envoyer_cloture(activite):
        dest = AlerteMailService._destinataires(activite)
        dans_delai = "dans les délais ✓" if activite.est_dans_delai else "hors délais ✗"
        AlerteMailService._send(
            f"[CIE Manager] Clôture — {activite.titre}",
            f"L'activité « {activite.titre} » a été clôturée {dans_delai}.\nDate de réalisation : {activite.date_realisation}",
            dest
        )

    @staticmethod
    def envoyer_clonage(activite):
        dest = AlerteMailService._destinataires(activite)
        AlerteMailService._send(
            f"[CIE Manager] Nouvelle instance mensuelle — {activite.titre}",
            f"Une nouvelle instance de « {activite.titre} » a été créée pour {activite.mois_reference}.\nDate butoir : {activite.date_butoir}",
            dest
        )
