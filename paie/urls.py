from django.urls import path
from .views import (AgentsView, AgentCreateView, AgentDetailsView, AgentUpdateView, AgentDeleteView, ListePaiesView,
                    PaieAgentCreateView, PaieAgentDetailsView)

urlpatterns = [
    path('agents', AgentsView.as_view(), name='agents'),
    path('agent/<int:pk>', AgentDetailsView.as_view(), name='agent_details'),
    path('agent/create', AgentCreateView.as_view(), name='agent_create'),
    path('agent/update/<int:pk>', AgentUpdateView.as_view(), name='agent_update'),
    path('agent/delete/<int:pk>', AgentDeleteView.as_view(), name='agent_delete'),
    path('listes_paie', ListePaiesView.as_view(), name='listes_paie'),
    path('paie/agent/<int:pk>/create', PaieAgentCreateView.as_view(), name='paie_agent_create'),
    path('paie/<int:pk>/agent/<int:agent_pk>/details', PaieAgentDetailsView.as_view(), name='paie_agent_details'),
]