import datetime

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView, RedirectView, FormView, DeleteView
from django.shortcuts import redirect, get_object_or_404, render, HttpResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.template.loader import render_to_string
from .models import (Caisse, CaisseCourante, MouvementCaisse, RubriqueCaisse, MouvementCaisseFournisseur,
                     MouvementCaisseClient, MouvementCaisseCreancier)
from clients.models import Client
from fournisseurs.models import Fournisseur
from creanciers.models import Creancier
from factures.models import Facture
from users.models import Caissier
from .forms import OuvertureCaisseValidateForm, ClotureCaisseValidateForm, CaisseForm


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
        except Caisse.DoesNotExists:
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

        elif rubrique.nom.lower() == "transfert caisse":
            caisses = Caisse.objects.exclude(pk=caisse_pk)
            champ_html = render_to_string("caisse/partials/field_caisse.html",
                                          context={'caisses': caisses})

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

    def get_total_ventes(self):
        factures = Facture.objects.filter(date_creation__date=datetime.datetime.now().date())
        total_factures = sum(i.total for i in factures)
        return total_factures

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['add_form'] = CaisseForm(caisse_pk=self.get_caisse().pk)
        context['update_form'] = CaisseForm(
            caisse_pk=self.get_caisse().pk,
            instance=MouvementCaisse.objects.filter(caisse=self.kwargs['pk']).first()
        )
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

                    print(mouvement)
                    print(form)

                    if mouvement.rubrique.nom.lower() == "fournisseurs":
                        MouvementCaisseFournisseur.objects.create(
                            mouvement_caisse=mouvement,
                            fournisseur=mouvement.fournisseur
                        )

                    elif mouvement.rubrique.nom.lower() == "clients":
                        MouvementCaisseClient.objects.create(
                            mouvement_caisse=mouvement,
                            client=mouvement.client
                        )

                    elif mouvement.rubrique.nom.lower() == "creanciers":
                        MouvementCaisseCreancier.objects.create(
                            mouvement_caisse=mouvement,
                            creancier=mouvement.creancier
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

                    mouvement.save()

                    html = render_to_string("caisse/partials/add_form_and_table.html", {
                        "add_form": CaisseForm(caisse_pk=self.get_caisse().pk),
                        "caisse_courante": self.get_object(),
                        "mouvements_entree": self.get_mouvements_entree_caisse(),
                        "mouvements_sortie": self.get_mouvements_sortie_caisse(),
                    }, request=request)

                    return HttpResponse(html)
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

            else:
                instance = get_object_or_404(MouvementCaisse, pk=request.POST.get('id'))
                form = CaisseForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()

                    html = render_to_string("caisse/partials/add_form_and_table.html", {
                        "add_form": CaisseForm(caisse_pk=self.get_caisse().pk),
                        "caisse_courante": self.get_object(),
                        "mouvements_entree": self.get_mouvements_entree_caisse(),
                        "mouvements_sortie": self.get_mouvements_sortie_caisse(),
                    }, request=request)

                    return HttpResponse(html)
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

        return JsonResponse({'error': 'Invalid request'}, status=400)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['caisse'] = self.get_caisse()
        context['mouvements_entree'] = self.get_mouvements_entree_caisse()
        context['mouvements_sortie'] = self.get_mouvements_sortie_caisse()
        context['ventes'] = self.get_total_ventes()
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
            return redirect('historique_caisse', pk=caisse.pk)
        else:
            return redirect('index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cloture caisse'
        context['message'] = 'Voulez-vous cloturer la caisse ?'
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Oui'
        return context



class MouvementCaisseDeleteView(LoginRequiredMixin, DeleteView):
    model = MouvementCaisse
    template_name = 'caisse/mouvement_caisse_confirm_delete.html'

    def get_caisse(self):
        return get_object_or_404(CaisseCourante, pk=self.kwargs['caisse_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Supprimer un mouvement de caisse"
        context['message'] = f"Voulez-vous supprimer le mouvement {self.get_object().motif} ?"
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        context['approvisionnement'] = self.get_caisse()
        return context

    def get_success_url(self):
        return reverse('caisse_details', kwargs={'pk': self.object.pk})

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        caisse = self.object.caisse

        self.object.delete()

        if request.headers.get('HX-Request') == 'true':
            mouvements_entree = MouvementCaisse.objects.filter(caisse=caisse, type_mouvement='ENTREE')
            mouvements_sortie = MouvementCaisse.objects.filter(caisse=caisse, type_mouvement='SORTIE')
            context = {
                "caisse": caisse,
                "mouvements_entree": mouvements_entree,
                "mouvements_sortie": mouvements_sortie,
            }
            return render(request, "caisse/partials/lines_table.html", context)

        return redirect(self.get_success_url())


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