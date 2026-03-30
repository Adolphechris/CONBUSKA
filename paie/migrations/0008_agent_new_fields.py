"""
0008 — Nouveaux champs Agent :
  poste, departement, type_contrat, actif, date_creation, date_modification
"""

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('paie', '0007_alter_agent_salaire'),
    ]

    operations = [
        migrations.AddField(
            model_name='agent',
            name='poste',
            field=models.CharField(blank=True, max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='agent',
            name='departement',
            field=models.CharField(blank=True, max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='agent',
            name='type_contrat',
            field=models.CharField(
                choices=[('CDI', 'CDI'), ('CDD', 'CDD'), ('CONSULTANT', 'Consultant')],
                default='CDI',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='agent',
            name='actif',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='agent',
            name='date_creation',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='agent',
            name='date_modification',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='agent',
            name='telephone',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='agent',
            name='ville',
            field=models.CharField(max_length=50),
        ),
    ]
