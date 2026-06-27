from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='dual_from_mouvement')
def dual_from_mouvement(mouvement):
    """Return dual display HTML using related mouvement child with valeur_usd when available.

    Falls back to plain FC display when no USD value is available.
    """
    # Try known related names that contain valeur_usd
    related_names = [
        'mouvements_caisse_c',
        'mouvements_caisse_f',
        'mouvements_caisse_cr',
        'mouvements_caisse_db',
    ]

    valeur_usd = None
    for rel in related_names:
        qs = getattr(mouvement, rel).all()
        if qs:
            obj = qs[0]
            valeur_usd = getattr(obj, 'valeur_usd', None)
            break

    if valeur_usd is not None:
        # Avoid circular import: import dual_amount directly
        from parametres.templatetags.currency_tags import dual_amount
        return mark_safe(dual_amount(valeur_usd))

    # Fallback: show FC only
    amt = getattr(mouvement, 'montant', None)
    if amt is None:
        return ''
    return mark_safe(f'<span class="fc-value">FC {amt:,.0f}</span>')
