from django.urls import path
from .views import (AgentsView, AgentCreateView, AgentDetailsView, AgentUpdateView, AgentDeleteView, ListePaiesView,
                    PaieCreateView, PaieDetailsView, PaieAgentCreateView)

urlpatterns = [
    path('agents', AgentsView.as_view(), name='agents'),
    path('agent/<int:pk>', AgentDetailsView.as_view(), name='agent_details'),
    path('agent/create', AgentCreateView.as_view(), name='agent_create'),
    path('agent/update/<int:pk>', AgentUpdateView.as_view(), name='agent_update'),
    path('agent/delete/<int:pk>', AgentDeleteView.as_view(), name='agent_delete'),
    path('listes_paie', ListePaiesView.as_view(), name='listes_paie'),
    path('paie/create', PaieCreateView.as_view(), name='paie_create'),
    path('paie/<int:pk>/details', PaieDetailsView.as_view(), name='paie_details'),
    path('paie/<int:pk>/agent/<int:agent_pk>/create', PaieAgentCreateView.as_view(), name='paie_agent_create'),
]