"""
conbuska_ai/urls.py

URLs du module Conbuska AI.
"""

from django.urls import path

from .views import (
    ConbuskaAIAnalyseView,
    ConbuskaAIChatView,
    ConbuskaAIRapportView,
    ConbuskaAIRecommandationsView,
)

urlpatterns = [
    # Chat principal
    path('chat', ConbuskaAIChatView.as_view(), name='conbuska_ai_chat'),
    
    # API endpoints
    path('api/chat', ConbuskaAIChatView.as_view(), name='conbuska_ai_api_chat'),
    path('api/analyse/<str:module>', ConbuskaAIAnalyseView.as_view(), name='conbuska_ai_analyse'),
    path('api/recommandations/<str:module>', ConbuskaAIRecommandationsView.as_view(), name='conbuska_ai_recommandations'),
    path('api/rapport/<str:type_rapport>', ConbuskaAIRapportView.as_view(), name='conbuska_ai_rapport'),
]