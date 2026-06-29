"""
conbuska_ai/views.py

Vues du module Conbuska AI.
Interface de chat avec l'assistant intelligent.
"""

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.contrib import messages

from users.permissions import ROLE_ADMIN, RoleRequiredMixin

from .services import ai_service


class ConbuskaAIChatView(RoleRequiredMixin, View):
    """Vue principale du chatbot Conbuska AI."""
    allowed_roles = [ROLE_ADMIN]
    template_name = 'conbuska_ai/chat.html'

    def get(self, request):
        """Affiche l'interface de chat."""
        return render(request, self.template_name, {
            'title': 'Conbuska AI - Assistant Intelligent',
        })

    def post(self, request):
        """Traite un message de l'utilisateur."""
        message = request.POST.get('message', '').strip()
        
        if not message:
            return JsonResponse({
                'response': 'Veuillez saisir un message.',
                'error': True
            })
        
        # Contexte métier
        context = {
            'module': request.POST.get('module', 'general'),
            'user_role': 'admin',
        }
        
        # Appeler le service IA
        result = ai_service.chat(message, context=context)
        
        return JsonResponse(result)


class ConbuskaAIAnalyseView(RoleRequiredMixin, View):
    """Vue pour les analyses automatiques."""
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, module):
        """Retourne l'analyse d'un module."""
        try:
            if module == 'stock':
                analyse = ai_service.analyser_stock()
            elif module == 'ventes':
                periode = int(request.GET.get('periode', 30))
                analyse = ai_service.analyser_ventes(periode_jours=periode)
            elif module == 'paie':
                analyse = ai_service.analyser_paie()
            else:
                return JsonResponse({
                    'error': 'Module non reconnu',
                    'error': True
                }, status=400)
            
            return JsonResponse({
                'analyse': analyse,
                'error': False
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'error': True
            }, status=500)


class ConbuskaAIRecommandationsView(RoleRequiredMixin, View):
    """Vue pour les recommandations automatiques."""
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, module):
        """Retourne les recommandations pour un module."""
        try:
            recommandations = ai_service.recommander_action(module)
            return JsonResponse({
                'recommandations': recommandations,
                'error': False
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'error': True
            }, status=500)


class ConbuskaAIRapportView(RoleRequiredMixin, View):
    """Vue pour générer des rapports automatiques."""
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, type_rapport):
        """Génère un rapport automatique."""
        try:
            rapport = ai_service.generer_rapport_automatique(type_rapport)
            return JsonResponse({
                'rapport': rapport,
                'type': type_rapport,
                'error': False
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'error': True
            }, status=500)