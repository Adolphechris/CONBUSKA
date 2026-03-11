# Generated manually - Remove taux from Parametre (taux now in TauxEchange)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parametres', '0003_parametre_taux'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='parametre',
            name='taux',
        ),
    ]
