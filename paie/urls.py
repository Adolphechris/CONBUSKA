from django.urls import path

from .views import (
    AgentCreateView,
    AgentDeleteView,
    AgentDetailsView,
    AgentUpdateView,
    AgentsView,
    ListePaiesView,
    PaieAgentCreateView,
    PaieAgentDeleteView,
    PaieAgentDetailsView,
    PaiePdfView,
    PaieValiderView,
)

urlpatterns = [
    path('agents', AgentsView.as_view(), name='agents'),
    path('agent/<int:pk>', AgentDetailsView.as_view(), name='agent_details'),
    path('agent/create', AgentCreateView.as_view(), name='agent_create'),
    path('agent/update/<int:pk>', AgentUpdateView.as_view(), name='agent_update'),
    path('agent/delete/<int:pk>', AgentDeleteView.as_view(), name='agent_delete'),
    path('listes_paie', ListePaiesView.as_view(), name='listes_paie'),
    path('paie/agent/<int:pk>/create', PaieAgentCreateView.as_view(), name='paie_agent_create'),
    path('paie/<int:pk>/agent/<int:agent_pk>/details', PaieAgentDetailsView.as_view(), name='paie_agent_details'),
    path('paie/<int:pk>/agent/<int:agent_pk>/delete', PaieAgentDeleteView.as_view(), name='paie_agent_delete'),
    path('paie/<int:pk>/agent/<int:agent_pk>/valider', PaieValiderView.as_view(), name='paie_agent_valider'),
    path('paie/<int:pk>/agent/<int:agent_pk>/pdf', PaiePdfView.as_view(), name='paie_pdf'),
]
