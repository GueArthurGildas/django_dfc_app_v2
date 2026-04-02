import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse
from django.utils import timezone
from apps.organisation.models import SousDirection
from apps.operations.views import (
    get_qs_activites, calcul_stats_qs, get_user_sd,
    appliquer_filtre_periode, get_annees_disponibles, TRIMESTRES
)

# ── Prompt système pour l'IA DFC/CIE ─────────────────────────────────────────
SYSTEM_PROMPT = """Tu es ARIA, l'assistante intelligente de la Direction Financière et Comptable (DFC) de la Compagnie Ivoirienne d'Électricité (CIE).

Tu es experte en :
- Comptabilité générale et analytique (Plan Comptable SYSCOHADA)
- Finance d'entreprise et analyse financière
- Arrêtés comptables, Balance Générale, Grand Livre, lettrage
- Facturation, recouvrement, gestion des impayés
- Trésorerie, rapprochement bancaire
- Gestion du stress professionnel et bien-être au travail
- Management et organisation des équipes comptables

Ton style :
- Tu réponds en français, de manière professionnelle mais accessible
- Tu es proactive : tu poses des questions pour mieux cerner le besoin
- Tu donnes des exemples concrets tirés du contexte CIE/DFC quand c'est utile
- Tes réponses sont structurées, claires, avec des points clés mis en évidence
- Tu encourages l'approfondissement : "Veux-tu que j'explique en détail ?", "As-tu des questions sur ce point ?"
- Tu adaptes le niveau de complexité à l'interlocuteur

À la première question ou quand la conversation s'ouvre, présente-toi brièvement et propose 3 thèmes d'entrée en matière sous forme de questions engageantes.

Ne sauvegarde aucune information entre les conversations. Chaque session est fraîche."""


def get_mes_activites(user):
    from apps.operations.models import Activite
    today = timezone.now().date()
    qs = Activite.objects.filter(
        acteurs__utilisateur=user,
        deleted_at__isnull=True
    ).exclude(statut='cloturee').select_related(
        'section__sous_direction', 'dossier'
    ).distinct().order_by('date_butoir')
    return {
        'toutes':         qs,
        'en_retard':      qs.filter(date_butoir__lt=today),
        'urgentes':       qs.filter(date_butoir__gte=today, date_butoir__lte=today + timezone.timedelta(days=7)),
        'normales':       qs.filter(date_butoir__gt=today + timezone.timedelta(days=7)),
        'responsable':    qs.filter(acteurs__utilisateur=user, acteurs__role_activite='responsable').distinct(),
        'total':          qs.count(),
        'nb_retard':      qs.filter(date_butoir__lt=today).count(),
        'nb_urgentes':    qs.filter(date_butoir__gte=today, date_butoir__lte=today + timezone.timedelta(days=7)).count(),
        'nb_responsable': qs.filter(acteurs__utilisateur=user, acteurs__role_activite='responsable').distinct().count(),
    }


class DashboardView(LoginRequiredMixin, View):
    template_name = 'dashboard/index.html'

    def get(self, request):
        today     = timezone.now().date()
        user      = request.user
        sd_id     = request.GET.get('sd', 'all')
        annee     = request.GET.get('annee', '')
        trimestre = request.GET.get('trimestre', '')
        user_sd   = get_user_sd(user)

        if user_sd is None:
            sous_directions = SousDirection.objects.filter(actif=True).order_by('ordre')
        else:
            sous_directions = SousDirection.objects.filter(pk=user_sd.pk)
            sd_id = str(user_sd.pk)

        qs_global = get_qs_activites(user)
        qs_global = appliquer_filtre_periode(qs_global, annee, trimestre)
        if sd_id and sd_id != 'all':
            try:
                qs_global = qs_global.filter(section__sous_direction_id=int(sd_id))
            except (ValueError, TypeError):
                pass

        stats = calcul_stats_qs(qs_global)

        activites_urgentes = qs_global.filter(
            statut__in=['ouverte', 'en_cours'],
            date_butoir__lte=today + timezone.timedelta(days=7)
        ).select_related('section__sous_direction').order_by('date_butoir')[:6]

        mes_activites = get_mes_activites(user)

        stats_par_sd = []
        for sd in sous_directions:
            qs_sd = appliquer_filtre_periode(
                get_qs_activites(user).filter(section__sous_direction=sd),
                annee, trimestre
            )
            s = calcul_stats_qs(qs_sd)
            stats_par_sd.append({'id': sd.pk, 'code': sd.code, 'couleur': sd.couleur, 'label': sd.libelle[:20], **s})

        context = {
            'sous_directions':    sous_directions,
            'sd_selectionnee':    sd_id,
            'afficher_filtre_sd': user_sd is None,
            'stats':              stats,
            'stats_par_sd':       json.dumps(stats_par_sd),
            'sd_cards':           stats_par_sd,
            'activites_urgentes': activites_urgentes,
            'mes_activites':      mes_activites,
            'filtre_annee':       annee,
            'filtre_trimestre':   trimestre,
            'annees_dispo':       get_annees_disponibles(),
            'trimestres':         TRIMESTRES,
            'today':              today,
            'ia_suggestions': [
                'Balance Générale', 'Grand Livre', 'Lettrage comptable',
                'Arrêté mensuel', 'Gestion du stress', 'SYSCOHADA',
            ],
        }
        return render(request, self.template_name, context)


class IAChatView(LoginRequiredMixin, View):
    """Proxy vers Ollama — stream SSE vers le front."""

    OLLAMA_URL = 'http://localhost:11434/api/chat'

    def post(self, request):
        try:
            body     = json.loads(request.body)
            messages = body.get('messages', [])
            # Injecter le system prompt si premier message
            full_messages = [{'role': 'system', 'content': SYSTEM_PROMPT}] + messages
        except Exception:
            return JsonResponse({'error': 'Payload invalide'}, status=400)

        def stream():
            import urllib.request
            payload = json.dumps({
                'model':    'gemma2:9b',
                'messages': full_messages,
                'stream':   True,
            }).encode('utf-8')
            req = urllib.request.Request(
                self.OLLAMA_URL,
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    for line in resp:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get('message', {}).get('content', '')
                            if content:
                                yield f"data: {json.dumps({'content': content})}\n\n"
                            if chunk.get('done'):
                                yield "data: [DONE]\n\n"
                                break
                        except Exception:
                            continue
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                yield "data: [DONE]\n\n"

        response = StreamingHttpResponse(stream(), content_type='text/event-stream')
        response['Cache-Control']  = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
