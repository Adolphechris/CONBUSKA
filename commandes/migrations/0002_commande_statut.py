# Generated migration for adding statut field to Commande
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commandes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='commande',
            name='statut',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('BROUILLON', 'Brouillon'),
                    ('VALIDEE', 'Validée'),
                    ('TRANSFORMEE', 'Transformée'),
                ],
                default='BROUILLON',
                verbose_name='Statut'
            ),
        ),
    ]