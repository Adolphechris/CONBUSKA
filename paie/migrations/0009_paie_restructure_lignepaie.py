"""
0009 — Restructuration Paie + création LignePaie :
  - RenameField montant_percu → net_a_payer
  - Rename related_name agent_paie_details → paies
  - AddField salaire_base, salaire_brut, total_primes, total_retenues
  - AlterField salaire → salaire_base (rename via RenameField)
  - Rename related_names cree_par / modifie_par
  - AlterUniqueTogether (agent, mois)
  - CreateModel LignePaie
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def supprimer_doublons_paie(apps, schema_editor):
    """
    Supprime les doublons (agent_id, mois) en ne conservant que la paie
    avec le pk le plus élevé (la plus récente) pour chaque paire.
    Nécessaire avant de poser la contrainte unique_together.
    """
    Paie = apps.get_model('paie', 'Paie')
    from django.db.models import Count

    paires_dupliquees = (
        Paie.objects
        .values('agent_id', 'mois')
        .annotate(nb=Count('id'))
        .filter(nb__gt=1)
    )
    for paire in paires_dupliquees:
        ids_a_supprimer = list(
            Paie.objects
            .filter(agent_id=paire['agent_id'], mois=paire['mois'])
            .order_by('-id')
            .values_list('id', flat=True)[1:]   # garde le plus récent, supprime le reste
        )
        Paie.objects.filter(id__in=ids_a_supprimer).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('paie', '0008_agent_new_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Paie : renommages de champs ───────────────────────────────
        migrations.RenameField(
            model_name='paie',
            old_name='montant_percu',
            new_name='net_a_payer',
        ),
        migrations.RenameField(
            model_name='paie',
            old_name='salaire',
            new_name='salaire_base',
        ),

        # ── Paie : ajout des champs de snapshot ───────────────────────
        migrations.AddField(
            model_name='paie',
            name='salaire_brut',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='paie',
            name='total_primes',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='paie',
            name='total_retenues',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),

        # ── Paie : correction des précisions décimales ────────────────
        migrations.AlterField(
            model_name='paie',
            name='salaire_base',
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
        migrations.AlterField(
            model_name='paie',
            name='net_a_payer',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),

        # ── Paie : mise à jour des related_names ─────────────────────
        migrations.AlterField(
            model_name='paie',
            name='agent',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='paies',
                to='paie.agent',
            ),
        ),
        migrations.AlterField(
            model_name='paie',
            name='cree_par',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='paie_cree_par',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='paie',
            name='modifie_par',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='paie_modifie_par',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # ── Paie : nettoyage des doublons avant la contrainte unique ─────
        migrations.RunPython(
            supprimer_doublons_paie,
            reverse_code=migrations.RunPython.noop,
        ),

        # ── Paie : contrainte unique (agent, mois) ────────────────────
        migrations.AlterUniqueTogether(
            name='paie',
            unique_together={('agent', 'mois')},
        ),

        # ── LignePaie : nouveau modèle ────────────────────────────────
        migrations.CreateModel(
            name='LignePaie',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('libelle', models.CharField(max_length=150)),
                ('type_ligne', models.CharField(
                    choices=[('GAIN', 'Gain'), ('RETENUE', 'Retenue')],
                    max_length=10,
                )),
                ('montant', models.DecimalField(decimal_places=2, max_digits=12)),
                ('ordre', models.PositiveSmallIntegerField(default=0)),
                ('paie', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='lignes',
                    to='paie.paie',
                )),
            ],
            options={
                'verbose_name': 'Ligne de paie',
                'verbose_name_plural': 'Lignes de paie',
                'ordering': ['ordre', 'id'],
            },
        ),
    ]
