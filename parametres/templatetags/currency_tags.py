from django import template
from django.utils.safestring import mark_safe
from decimal import Decimal

register = template.Library()

@register.filter(name='dual_amount')
def dual_amount(usd_value, rate=None):
    if usd_value is None:
        usd_value = Decimal('0')
    else:
        usd_value = Decimal(str(usd_value))

    from parametres.models import get_taux_usd_cdf
    if rate is None:
        try:
            rate = get_taux_usd_cdf()
        except Exception:
            rate = Decimal('2500.00')
    else:
        rate = Decimal(str(rate))

    fc_value = usd_value * rate

    html = (
        f'<div class="dual-currency" style="display: inline-block; text-align: right;">'
        f'<span class="usd-value" style="display: block; font-size: 0.75em; color: #6c757d; line-height: 1;">USD {usd_value:,.2f}</span>'
        f'<span class="fc-value" style="display: block; font-size: 1.1em; font-weight: 600; line-height: 1.2; margin-top: 2px;">FC {fc_value:,.0f}</span>'
        f'</div>'
    )
    return mark_safe(html)
