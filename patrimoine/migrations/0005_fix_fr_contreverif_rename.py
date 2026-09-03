from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patrimoine', '0004_add_fonds_roulement_snapshot'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fondsroulementsnapshot',
            old_name='fr_contreverif',
            new_name='fr_calcule',
        ),
        migrations.AddField(
            model_name='snapshotmensuel',
            name='taux_mensuel',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='snapshotmensuel',
            name='solde_fin_mois_usd',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True),
        ),
    ]