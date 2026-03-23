import django.db.models.deletion
from django.db import migrations, models


def map_devise_to_fk(apps, schema_editor):
    """Map old string devise values ('$', 'FC') to Devise FK."""
    Commande = apps.get_model('commandes', 'Commande')
    Devise = apps.get_model('parametres', 'Devise')

    try:
        usd = Devise.objects.get(code='USD')
        cdf = Devise.objects.get(code='CDF')
    except Devise.DoesNotExist:
        return

    for commande in Commande.objects.filter(devise_old__isnull=False):
        if commande.devise_old in ('$', 'USD'):
            commande.devise = usd
        elif commande.devise_old in ('FC', 'CDF'):
            commande.devise = cdf
        else:
            commande.devise = usd  # fallback
        commande.save(update_fields=['devise'])


class Migration(migrations.Migration):

    dependencies = [
        ('commandes', '0008_detailscommande_commande'),
        ('parametres', '0006_devise_alter_tauxechange'),
    ]

    operations = [
        # 1. Rename old CharField to a temp name
        migrations.RenameField(
            model_name='commande',
            old_name='devise',
            new_name='devise_old',
        ),
        # 2. Add new FK field (nullable during migration)
        migrations.AddField(
            model_name='commande',
            name='devise',
            field=models.ForeignKey(
                'parametres.Devise',
                on_delete=django.db.models.deletion.PROTECT,
                null=True, blank=True,
                verbose_name='Devise',
            ),
        ),
        # 3. Data migration
        migrations.RunPython(map_devise_to_fk, migrations.RunPython.noop),
        # 4. Remove temp field
        migrations.RemoveField(model_name='commande', name='devise_old'),
        # 5. Widen taux precision
        migrations.AlterField(
            model_name='commande',
            name='taux',
            field=models.DecimalField(default=0.0, max_digits=12, decimal_places=4),
        ),
    ]
