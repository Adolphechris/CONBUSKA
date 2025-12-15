import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, FormView, DeleteView
from django.shortcuts import redirect, get_object_or_404, render, HttpResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.template.loader import render_to_string
from .models import (Caisse, CaisseCourante, MouvementCaisse, RubriqueCaisse, MouvementCaisseFournisseur,
                     MouvementCaisseClient, MouvementCaisseCreancier, MouvementCaisseAgent, MouvementCaisseDebiteur)
from clients.models import Client
from fournisseurs.models import Fournisseur
from creanciers.models import Creancier, Debiteur
from factures.models import Facture
from users.models import Caissier
from paie.models import Agent
from .forms import OuvertureCaisseValidateForm, ClotureCaisseValidateForm, CaisseForm


def get_total_ventes():
    factures = Facture.objects.filter(date_creation__date=datetime.datetime.now().date())
    total_factures = sum(i.total for i in factures)
    return total_factures


class OuvertureCaisseView(LoginRequiredMixin, FormView):
    form_class = OuvertureCaisseValidateForm
    template_name = 'caisse/ouvrir_caisse.html'

    def get_caisse(self):
        """
        Cette methode vérifie si l'url envoie un pk de caisse. Si oui, alors elle renvoie la caisse
        en parametre. Sinon elle cherche la caisse associée à l'utilisateur. Un user de type Admin
        prend par défaut la caisse principale. Les autres users de profile caissier, sont associés
        à leurs caisses respectives.
        :return:
        """
        try:
            caisse = Caisse.objects.get(pk=self.kwargs['pk'])
        except (Caisse.DoesNotExist, KeyError):
            if self.request.user.type_profile.nom == 'Admin':
                caisse = Caisse.objects.get(is_principal=True)
            else:
                check_caisse = Caissier.objects.get(user=self.request.user)
                caisse = Caisse.objects.get(pk=check_caisse.caisse.pk)
        return caisse

    def solde_initial(self):
        caisse = self.get_caisse()
        get_solde = CaisseCourante.objects.filter(caisse=caisse, est_ouverte=False).last()
        try:
            solde = get_solde.solde_final
        except AttributeError:
            solde = 0
        return solde

    def dispatch(self, request, *args, **kwargs):
        # Vérifier si l'utilisateur a déjà une caisse ouverte
        if CaisseCourante.objects.filter(est_ouverte=True, ouvert_par=self.request.user).exists():
            get_caisse = CaisseCourante.objects.get(est_ouverte=True, ouvert_par=self.request.user)
            # messages.warning(request, "Vous avez déjà une caisse ouverte.")
            return redirect('caisse_details', get_caisse.pk)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        caisse = self.get_caisse()
        nouvelle_caisse = CaisseCourante(
            caisse=caisse,
            ouvert_par=self.request.user,
            solde_initial=self.solde_initial()
        )
        nouvelle_caisse.save()
        return redirect('caisse_details', pk=nouvelle_caisse.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ouverture caisse'
        context['message'] = 'Voulez-vous ouvrir la caisse ?'
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Oui'
        return context


@require_GET
def get_update_caisse_form(request, pk):
    instance = get_object_or_404(MouvementCaisse, pk=pk)
    form = CaisseForm(instance=instance, caisse_pk=instance.caisse.pk)
    return render(request, "caisse/partials/update_form.html",
                  {"update_form": form, "caisse_pk": instance.caisse.pk, "mouvement_pk": pk})


def rubrique_champ_view(request, caisse_pk):
    print("************* ", request.GET)
    rubrique_id = request.GET.get('rubrique')
    champ_html = ""

    if rubrique_id:
        try:
            rubrique = RubriqueCaisse.objects.get(pk=rubrique_id)
        except RubriqueCaisse.DoesNotExist:
            return HttpResponse(champ_html)  # Rien à afficher

        if rubrique.nom.lower() == "clients":
            champ_html = render_to_string("caisse/partials/field_client.html",
                                          context={'clients': Client.objects.all()})

        elif rubrique.nom.lower() == "fournisseurs":
            champ_html = render_to_string("caisse/partials/field_fournisseur.html",
                                          context={'fournisseurs': Fournisseur.objects.all()})

        elif rubrique.nom.lower() == "créanciers":
            champ_html = render_to_string("caisse/partials/field_creancier.html",
                                          context={'creanciers': Creancier.objects.all()})

        elif rubrique.nom.lower() == "débiteurs":
            champ_html = render_to_string("caisse/partials/field_debiteur.html",
                                          context={'debiteurs': Debiteur.objects.all()})

        elif rubrique.nom.lower() == "transfert caisse":
            caisses = Caisse.objects.exclude(pk=caisse_pk)
            champ_html = render_to_string("caisse/partials/field_caisse.html",
                                          context={'caisses': caisses})

        elif rubrique.nom.lower() in ["transport", "avance sur salaire", "restauration", "assistance sociale"]:
            champ_html = render_to_string("caisse/partials/field_agent.html",
                                          context={'agents': Agent.objects.all()})

    return HttpResponse(champ_html)


class CaisseView(LoginRequiredMixin, DetailView):
    model = CaisseCourante
    context_object_name = 'caisse_courante'
    template_name = 'caisse/caisse.html'
    success_url = reverse_lazy('historique_caisse')

    def get_caisse(self):
        return get_object_or_404(Caisse, pk=self.get_object().caisse.pk)

    def get_mouvements_entree_caisse(self):
        mouvements = MouvementCaisse.objects.filter(caisse=self.kwargs['pk'], type_mouvement='ENTREE')
        return mouvements

    def get_mouvements_sortie_caisse(self):
        mouvements = MouvementCaisse.objects.filter(caisse=self.kwargs['pk'], type_mouvement='SORTIE')
        return mouvements

    def get_total_entrees(self):
        solde_initial = self.get_object().solde_initial
        entrees = sum(i.montant for i in self.get_mouvements_entree_caisse())
        return solde_initial + get_total_ventes() + entrees

    def get_total_sorties(self):
        sorties = sum(i.montant for i in self.get_mouvements_sortie_caisse())
        return sorties

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['add_form'] = CaisseForm(caisse_pk=self.get_caisse().pk)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if request.headers.get('HX-Request') == 'true':
            form_type = request.POST.get('form_type')

            if form_type == 'add':
                form = CaisseForm(request.POST, caisse_pk=self.get_caisse().pk)
                if form.is_valid():
                    mouvement = form.save(commit=False)
                    mouvement.caisse = self.get_object()
                    mouvement.effectue_par = self.request.user
                    mouvement.save()

                    if mouvement.rubrique.nom.lower() == "fournisseurs":
                        fournisseur_pk = request.POST.get('fournisseur')
                        fournisseur = Fournisseur.objects.get(id=fournisseur_pk)

                        MouvementCaisseFournisseur.objects.create(
                            mouvement_caisse=mouvement,
                            fournisseur=fournisseur
                        )

                    elif mouvement.rubrique.nom.lower() == "clients":
                        client_pk = request.POST.get('client')
                        client = Client.objects.get(id=client_pk)

                        MouvementCaisseClient.objects.create(
                            mouvement_caisse=mouvement,
                            client=client
                        )

                    elif mouvement.rubrique.nom.lower() == "créanciers":
                        creancier_pk = request.POST.get('creancier')
                        creancier = Creancier.objects.get(id=creancier_pk)

                        MouvementCaisseCreancier.objects.create(
                            mouvement_caisse=mouvement,
                            creancier=creancier
                        )

                    elif mouvement.rubrique.nom.lower() == "débiteurs":
                        debiteur_pk = request.POST.get('debiteur')
                        debiteur = Debiteur.objects.get(id=debiteur_pk)

                        MouvementCaisseDebiteur.objects.create(
                            mouvement_caisse=mouvement,
                            debiteur=debiteur
                        )

                    elif mouvement.rubrique.nom.lower() in ["transport", "avance sur salaire", "restauration",
                                                            "assistance sociale"]:
                        agent_pk = request.POST.get('agent')
                        if agent_pk:
                            agent = Agent.objects.get(pk=agent_pk)
                            MouvementCaisseAgent.objects.create(
                                mouvement_caisse=mouvement,
                                agent=agent
                            )

                    elif mouvement.rubrique.nom.lower() == "transfert caisse":
                        get_caisse_ouverte = CaisseCourante.objects.filter(caisse=mouvement.caisse_destination,
                                                                           est_ouverte=True).first()
                        if get_caisse_ouverte:
                            MouvementCaisse.objects.create(
                                caisse=get_caisse_ouverte,
                                type_mouvement="ENTREE",
                                rubrique=mouvement.rubrique,
                                montant=mouvement.montant,
                                motif=mouvement.motif,
                                effectue_par=self.request.user
                            )

                    total_entrees = self.get_total_entrees()
                    total_sorties = self.get_total_sorties()

                    html = render_to_string("caisse/partials/add_form_and_table.html", {
                        "add_form": CaisseForm(caisse_pk=self.get_caisse().pk),
                        "caisse": self.get_caisse(),
                        "caisse_courante": self.get_object(),
                        "mouvements_entree": self.get_mouvements_entree_caisse(),
                        "mouvements_sortie": self.get_mouvements_sortie_caisse(),
                        "total_entrees": total_entrees,
                        "total_sorties": total_sorties,
                    }, request=request)

                    html_totaux = render_to_string('caisse/partials/caisse_totaux_oob.html', {
                        "total_entrees": total_entrees,
                        "total_sorties": total_sorties,
                        "solde_caisse": total_entrees - total_sorties,
                    })

                    return HttpResponse(html + html_totaux)
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

            else:
                instance = get_object_or_404(MouvementCaisse, pk=int(request.POST.get('id')))
                form = CaisseForm(request.POST, instance=instance, caisse_pk=self.get_caisse().pk)
                if form.is_valid():
                    mouvement = form.save(commit=False)
                    # mouvement.caisse = self.get_object()
                    mouvement.save()

                    if mouvement.rubrique.nom.lower() == "fournisseurs":
                        fournisseur_pk = request.POST.get('fournisseur')
                        fournisseur = Fournisseur.objects.get(id=fournisseur_pk)

                        get_mc_fournisseur = MouvementCaisseFournisseur.objects.get(mouvement_caisse=mouvement.pk)
                        get_mc_fournisseur.fournisseur = fournisseur
                        get_mc_fournisseur.save()

                    elif mouvement.rubrique.nom.lower() == "clients":
                        client_pk = request.POST.get('client')
                        client = Client.objects.get(id=client_pk)

                        get_mc_client = MouvementCaisseClient.objects.get(mouvement_caisse=mouvement.pk)
                        get_mc_client.client = client
                        get_mc_client.save()

                    elif mouvement.rubrique.nom.lower() == "creanciers":
                        creancier_pk = request.POST.get('creancier')
                        creancier = Creancier.objects.get(id=creancier_pk)

                        get_mc_creancier = MouvementCaisseCreancier.objects.get(mouvement_caisse=mouvement.pk)
                        get_mc_creancier.creancier = creancier
                        get_mc_creancier.save()

                    elif mouvement.rubrique.nom.lower() == "debiteurs":
                        debiteur_pk = request.POST.get('debiteur')
                        debiteur = Debiteur.objects.get(id=debiteur_pk)

                        get_mc_debiteur = MouvementCaisseDebiteur.objects.get(mouvement_caisse=mouvement.pk)
                        get_mc_debiteur.debiteur = debiteur
                        get_mc_debiteur.save()

                    elif mouvement.rubrique.nom.lower() in ["transport", "avance sur salaire", "restauration",
                                                            "assistance sociale"]:
                        agent_pk = request.POST.get('agent')
                        if agent_pk:
                            agent = Agent.objects.get(pk=agent_pk)
                            get_mc_agent = MouvementCaisseAgent.objects.get(mouvement_caisse=mouvement.pk)
                            get_mc_agent.agent = agent
                            get_mc_agent.save()

                    total_entrees = self.get_total_entrees()
                    total_sorties = self.get_total_sorties()

                    html = render_to_string("caisse/partials/add_form_and_table.html", {
                        "add_form": CaisseForm(caisse_pk=self.get_caisse().pk),
                        "caisse_courante": self.get_object(),
                        "mouvements_entree": self.get_mouvements_entree_caisse(),
                        "mouvements_sortie": self.get_mouvements_sortie_caisse(),
                        "total_entrees": total_entrees,
                        "total_sorties": total_sorties,
                    }, request=request)

                    html_totaux = render_to_string('caisse/partials/caisse_totaux_oob.html', {
                        "total_entrees": total_entrees,
                        "total_sorties": total_sorties,
                        "solde_caisse": total_entrees - total_sorties,
                    })

                    return HttpResponse(html + html_totaux)
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

        return JsonResponse({'error': 'Invalid request'}, status=400)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['caisse'] = self.get_caisse()
        context['mouvements_entree'] = self.get_mouvements_entree_caisse()
        context['mouvements_sortie'] = self.get_mouvements_sortie_caisse()
        context['ventes'] = get_total_ventes()
        context['total_entrees'] = self.get_total_entrees()
        context['total_sorties'] = self.get_total_sorties()
        context['solde_caisse'] = self.get_total_entrees() - self.get_total_sorties()
        return context


class ClotureCaisseView(LoginRequiredMixin, FormView):
    form_class = ClotureCaisseValidateForm
    template_name = 'caisse/cloturer_caisse.html'

    def get_caisse_courante(self):
        """
        """
        caisse_courante = CaisseCourante.objects.get(pk=self.kwargs['pk'])
        return caisse_courante

    def get_mouvements_entree_caisse(self):
        mouvements_qs = MouvementCaisse.objects.filter(caisse=self.get_caisse_courante().pk, type_mouvement='ENTREE')
        return sum(i.montant for i in mouvements_qs)

    def get_mouvements_sortie_caisse(self):
        mouvements_qs = MouvementCaisse.objects.filter(caisse=self.get_caisse_courante().pk, type_mouvement='SORTIE')
        return sum(i.montant for i in mouvements_qs)

    def get_total_ventes(self):
        caisse = self.get_caisse_courante()
        factures = Facture.objects.filter(date_creation__date=caisse.date_ouverture.date())
        total_factures = sum(i.total for i in factures)
        return total_factures

    def solde_final(self):
        solde_initial = self.get_caisse_courante().solde_initial
        entrees = self.get_mouvements_entree_caisse()
        sorties = self.get_mouvements_sortie_caisse()
        solde_final = solde_initial + entrees - sorties
        return solde_final

    def post(self, request, *args, **kwargs):
        caisse_courante = self.get_caisse_courante()
        caisse_courante.solde_final = self.solde_final()
        caisse_courante.ferme_par = self.request.user
        caisse_courante.date_fermeture = datetime.datetime.now()
        caisse_courante.est_ouverte = False
        caisse_courante.save()

        if self.request.user.type_profile.nom == 'Admin':
            caisse = Caisse.objects.get(is_principal=True)
            # Redirection vers l'historique
            response = HttpResponse()
            response["HX-Redirect"] = reverse('historique_caisse', kwargs={'pk': caisse.pk})
            return response

        else:
            response = HttpResponse()
            response["HX-Redirect"] = reverse('index')
            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Clôture caisse'
        context['message'] = 'Êtes-vous sûr de vouloir clôturer cette caisse ? Cette action est irréversible.'
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Oui'
        context['solde_final'] = self.solde_final()
        context['caisse_courante'] = self.get_caisse_courante()
        return context


class MouvementCaisseDeleteView(LoginRequiredMixin, DeleteView):
    model = MouvementCaisse
    context_object_name = 'mouvement_caisse'
    template_name = 'caisse/mouvement_caisse_confirm_delete.html'

    def get_caisse_courante(self):
        return get_object_or_404(CaisseCourante, pk=self.kwargs['caisse_pk'])

    def get_caisse(self):
        return get_object_or_404(Caisse, pk=self.get_caisse_courante().caisse.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Supprimer un mouvement de caisse"
        context['message'] = (f"Êtes-vous sûr de vouloir supprimer le mouvement : #{self.get_object().motif} ? "
                              f"Cette action est irréversible.")
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        context['caisse'] = self.get_caisse_courante()
        return context

    def get_success_url(self):
        return reverse('caisse_details', kwargs={'pk': self.object.pk})

    def delete(self, request, *args, **kwargs):
        mouvement_caisse = self.get_object()
        caisse_courante = mouvement_caisse.caisse

        mouvement_caisse.delete()

        mouvements_entree = MouvementCaisse.objects.filter(caisse=caisse_courante, type_mouvement='ENTREE')
        mouvements_sortie = MouvementCaisse.objects.filter(caisse=caisse_courante, type_mouvement='SORTIE')

        total_entrees = sum(i.montant for i in mouvements_entree) + get_total_ventes() + caisse_courante.solde_initial
        total_sorties = sum(i.montant for i in mouvements_sortie)

        html_table = render_to_string('caisse/partials/lines_table.html', {
            "caisse": self.get_caisse(),
            "caisse_courante": caisse_courante,
            "mouvements_entree": mouvements_entree,
            "mouvements_sortie": mouvements_sortie,
        })

        html_totaux = render_to_string('caisse/partials/caisse_totaux_oob.html', {
            "solde_caisse": total_entrees - total_sorties,
            "total_entrees": total_entrees,
            "total_sorties": total_sorties,
        })

        response = HttpResponse(html_table + html_totaux)
        response["HX-Trigger"] = "closeModal"
        return response


class CaissesView(LoginRequiredMixin, ListView):
    model = Caisse
    context_object_name = 'liste_caisses'
    template_name = 'caisse/caisses.html'

    def get_queryset(self):
        user = self.request.user
        if user.type_profile.nom == 'Admin':
            caisses = Caisse.objects.all()
        else:
            check_caisse = Caissier.objects.get(user=user)
            caisses = Caisse.objects.filter(pk=check_caisse.caisse.pk)

        return caisses


class HistoriqueCaisseView(LoginRequiredMixin, DetailView):
    model = Caisse
    template_name = 'caisse/caisse_historique.html'

    def get_liste_caisses_courantes(self):
        return CaisseCourante.objects.filter(caisse=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['caisse'] = self.object
        context['liste_caisses'] = self.get_liste_caisses_courantes()
        return context