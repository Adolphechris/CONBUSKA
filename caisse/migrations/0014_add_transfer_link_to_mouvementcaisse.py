from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0013_add_caisse_destination_to_mouvementcaisse'),
    ]

    operations = [
        migrations.AddField(
            model_name='mouvementcaisse',
            name='mouvement_transfert_source',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='mouvement_transfert_miroir',
                to='caisse.mouvementcaisse',
            ),
        ),
    ]
