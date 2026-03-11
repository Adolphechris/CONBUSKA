from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin

# ---------------------------------------------------------------------------
# Role slug constants — must match TypeProfile.slug values in the database
# ---------------------------------------------------------------------------
ROLE_ADMIN = 'admin'
ROLE_FACTURIER = 'facturier'
ROLE_CAISSIER = 'caissier'
ROLE_GERANT_STOCK = 'gerant_stock'
ROLE_GERANT_MAGASIN = 'gerant_magasin'

ALL_ROLES = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_CAISSIER, ROLE_GERANT_STOCK, ROLE_GERANT_MAGASIN]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_user_role(user):
    """Return the slug of the user's TypeProfile, or None."""
    if user.is_authenticated and user.type_profile_id:
        return user.type_profile.slug
    return None


def user_has_role(user, *roles):
    """Return True if the user's role slug is in roles, or if the user is a superuser."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return get_user_role(user) in roles


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------

class RoleRequiredMixin(LoginRequiredMixin):
    """
    Restrict a view to users whose TypeProfile.slug is in allowed_roles.
    Superusers bypass the check.
    Inherits from LoginRequiredMixin so unauthenticated users are redirected to login.

    Usage:
        class MyView(RoleRequiredMixin, ListView):
            allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER]
    """
    allowed_roles: list = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not user_has_role(request.user, *self.allowed_roles):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ReadOnlyForRolesMixin(AccessMixin):
    """
    Makes a view read-only (blocks unsafe HTTP methods) for users whose role
    is in readonly_roles. Users with full_write_roles (or superusers) retain
    full access. Users in neither list are denied access entirely.

    Usage:
        class MyView(ReadOnlyForRolesMixin, UpdateView):
            readonly_roles = [ROLE_CAISSIER, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
            full_write_roles = [ROLE_ADMIN]
    """
    readonly_roles: list = []
    full_write_roles: list = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if user_has_role(request.user, *self.full_write_roles):
            return super().dispatch(request, *args, **kwargs)

        if user_has_role(request.user, *self.readonly_roles):
            if request.method not in ('GET', 'HEAD', 'OPTIONS'):
                raise PermissionDenied
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_read_only'] = (
            not user_has_role(self.request.user, *self.full_write_roles)
            and user_has_role(self.request.user, *self.readonly_roles)
        )
        return context


class CaisseAccessMixin(AccessMixin):
    """
    Controls access to a Caisse view according to the caissier rule:
      - Admin / Gérant Magasin  → full access to any caisse
      - Caissier                → write access only on their own caisse;
                                   read (GET) access to any caisse
      - Other roles             → access denied

    Views using this mixin must implement get_caisse() returning a Caisse instance.
    """
    allowed_roles = [ROLE_ADMIN, ROLE_CAISSIER, ROLE_GERANT_MAGASIN]

    def get_caisse(self):
        """Override in the view to return the relevant Caisse instance."""
        raise NotImplementedError("Implement get_caisse() in your view.")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not user_has_role(request.user, *self.allowed_roles):
            raise PermissionDenied

        role = get_user_role(request.user)
        if role == ROLE_CAISSIER and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            try:
                caisse = self.get_caisse()
                caissier = request.user.caissier
                if caissier.caisse_id != caisse.pk:
                    raise PermissionDenied
            except PermissionDenied:
                raise
            except Exception:
                raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = get_user_role(self.request.user)
        if role == ROLE_CAISSIER and not self.request.user.is_superuser:
            try:
                caisse = self.get_caisse()
                caissier = self.request.user.caissier
                context['is_read_only'] = caissier.caisse_id != caisse.pk
            except Exception:
                context['is_read_only'] = True
        else:
            context['is_read_only'] = False
        return context
