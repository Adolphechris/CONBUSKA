from users.permissions import RoleRequiredMixin, ROLE_ADMIN
from django.views.generic import FormView, ListView, CreateView, DetailView
from django.views.generic.edit import UpdateView
from django.template.loader import render_to_string
from django.shortcuts import redirect, render, HttpResponse
from django.urls import reverse_lazy
from .models import Parametre, Magasin, TauxEchange, Devise
from .forms import ParametresForm, ParametresEditForm, MagasinCreateForm, TauxEchangeForm, DeviseForm


class ParametresView(RoleRequiredMixin, FormView):
    allowed_roles = [ROLE_ADMIN]
    model = Parametre
    context_object_name = 'parametres'
    form_class = ParametresForm
    template_name = 'parametres/parametres.html'

    @staticmethod
    def get_parametres():
        params = Parametre.objects.get(code='Params')
        return params

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parametres'] = self.get_parametres()
        return context

    def get_initial(self):
        initial = super().get_initial()
        params = self.get_parametres()
        initial['sigle'] = params.sigle
        initial['societe'] = params.societe
        initial['rccm'] = params.rccm
        initial['idnat'] = params.idnat
        initial['impot'] = params.impot
        initial['tva'] = params.tva
        initial['adresse'] = params.adresse
        initial['pays'] = params.pays
        initial['ville'] = params.ville
        initial['telephone'] = params.telephone
        initial['email'] = params.email
        return initial


class ParametresUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = Parametre
    context_object_name = 'parametres'
    form_class = ParametresEditForm
    success_url = reverse_lazy('parametres')
    template_name = 'parametres/parametres_form.html'


class MagasinsView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN]
    model = Magasin
    context_object_name = 'liste_magasins'
    template_name = 'parametres/magasins.html'


class MagasinCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = Magasin
    template_name = 'parametres/magasin_create_form.html'
    form_class = MagasinCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Creation magasin'
        context['title_page'] = 'Create'
        context['title_form'] = "Formulaire de creation d'un magasin"
        return context


class MagasinUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = Magasin
    template_name = 'parametres/magasin_create_form.html'
    form_class = MagasinCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modification magasin'
        context['title_page'] = 'Update'
        context['title_form'] = 'Formulaire de modification du magasin #{}'.format(self.get_object().nom)
        return context


class TauxEchangeListView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN]
    model = TauxEchange
    context_object_name = 'taux_list'
    template_name = 'parametres/taux_echange_list.html'
    ordering = ['-date_modification']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_form'] = TauxEchangeForm()
        return context


class TauxEchangeCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = TauxEchange
    template_name = 'parametres/taux_echange_form.html'
    form_class = TauxEchangeForm
    success_url = reverse_lazy('taux_echange_list')

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('HX-Request') == 'true':
            # Get the latest taux and render the taux content section
            latest_taux = TauxEchange.objects.order_by('-date_modification').first()
            html = render_to_string('parametres/taux_echange_list_partial.html', {
                'latest_taux': latest_taux,
                'taux_form': TauxEchangeForm()
            })
            return HttpResponse(html)
        return redirect(self.success_url)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request') == 'true':
            return render(self.request, self.template_name, {'form': form})
        return super().form_invalid(form)


class TauxEchangeUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = TauxEchange
    template_name = 'parametres/taux_echange_form.html'
    form_class = TauxEchangeForm
    success_url = reverse_lazy('taux_echange_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['taux'] = self.object
        return context

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('HX-Request') == 'true':
            latest_taux = TauxEchange.objects.order_by('-date_modification').first()
            html = render_to_string('parametres/taux_echange_list_partial.html', {
                'latest_taux': latest_taux
            })
            return HttpResponse(html)
        return redirect(self.success_url)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request') == 'true':
            return render(self.request, self.template_name, {'form': form, 'taux': self.object})
        return super().form_invalid(form)


class TauxEchangeHistoryView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
    model = TauxEchange
    template_name = 'parametres/taux_echange_history.html'
    context_object_name = 'taux'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        history = list(self.object.history.all().order_by('-history_date'))
        for i, record in enumerate(history):
            if i + 1 < len(history):
                prev = history[i + 1]
                # Use names without underscores
                record.prev = prev
                diff = {}
                for field in self.model._meta.fields:
                    field_name = field.name
                    if field_name == 'date_modification':
                        continue
                    old = getattr(prev, field_name, None)
                    new = getattr(record, field_name, None)
                    if old != new:
                        diff[field_name] = {'old': old, 'new': new}
                record.diff = diff
            else:
                record.prev = None
                record.diff = {}
        context['history_records'] = history
        return context


# ── Devises ───────────────────────────────────────────────────────────────────

class DevisesView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN]
    model = Devise
    context_object_name = 'devises'
    template_name = 'parametres/devises.html'
    ordering = ['code']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_form'] = DeviseForm()
        return context


class DeviseCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = Devise
    form_class = DeviseForm
    template_name = 'parametres/devise_form.html'
    success_url = reverse_lazy('devises')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouvelle devise'
        context['cancel_url'] = reverse_lazy('devises')
        return context


class DeviseUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = Devise
    form_class = DeviseForm
    template_name = 'parametres/devise_form.html'
    success_url = reverse_lazy('devises')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Modifier — {self.object.code}'
        context['cancel_url'] = reverse_lazy('devises')
        return context