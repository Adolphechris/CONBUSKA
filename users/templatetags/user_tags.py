from django import template
from users.permissions import ROLE_ADMIN

register = template.Library()


@register.filter(name='has_role')
def has_role(user, roles_str):
    """
    Check if the user's TypeProfile slug is among the given roles.
    Roles are passed as a comma-separated string.

    Usage: {% if user|has_role:"admin,facturier,gerant_magasin" %}
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if not user.type_profile_id:
        return False
    roles = [r.strip() for r in roles_str.split(',')]
    return user.type_profile.slug in roles


@register.filter(name='is_admin')
def is_admin(user):
    """Shorthand: {% if user|is_admin %}"""
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or (user.type_profile_id and user.type_profile.slug == ROLE_ADMIN)
