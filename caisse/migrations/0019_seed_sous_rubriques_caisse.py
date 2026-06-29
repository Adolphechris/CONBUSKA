"""Data migration : insère les sous-rubriques de caisse manquantes
selon le cahier des charges (Livre de Caisse).
"""
from django.db import migrations


def seed_sous_rubriques(apps, schema_editor):
    RubriqueCaisse = apps.get_model('caisse', 'RubriqueCaisse')
    SousRubriqueCaisse = apps.get_model('caisse', 'SousRubriqueCaisse')

    # 1. Créer la rubrique "Autres entrées" si elle n'existe pas
    autres_entrees, _ = RubriqueCaisse.objects.get_or_create(
        nom="Autres entrées",
        defaults={
            "description": "Entrées exceptionnelles ne rentrant pas dans les autres catégories",
            "visible": True,
        },
    )

    # 2. Créer / Vérifier les sous-rubriques pour "Charges exploitation"
    charges_exploitation, _ = RubriqueCaisse.objects.get_or_create(
        nom="Charges exploitation",
        defaults={
            "description": "Dépenses vitales et récurrentes de fonctionnement",
            "visible": True,
            "classification_metier": "CHARGE_EXPLOITATION",
        },
    )

    sous_rubriques_exploitation = [
        "Loyers",
        "Intérêts bancaires",
        "Impôt et taxes",
        "Offrandes et dîmes",
        "Communication Tel & Int.",
        "Électricité",
        "Achats matériels",
        "Entretiens",
    ]

    for nom in sous_rubriques_exploitation:
        SousRubriqueCaisse.objects.get_or_create(
            rubrique=charges_exploitation,
            nom=nom,
            defaults={"description": f"Sous-rubrique : {nom}"},
        )

    # 3. Créer / Vérifier les sous-rubriques pour "Charges personnelles"
    charges_personnelles, _ = RubriqueCaisse.objects.get_or_create(
        nom="Charges personnelles",
        defaults={
            "description": "Dépenses privées des propriétaires",
            "visible": True,
            "classification_metier": "CHARGE_PERSONNELLE",
        },
    )

    sous_rubriques_personnelles = [
        "Maison Adolphe",
        "Maison Albert",
        "Benoît et Gabriel",
        "Maman et Famille",
        "Épargne (Personnelle)",
        "Projets (Personnels)",
        "Don",
        "Scolarité",
        "Soins de Santé",
    ]

    for nom in sous_rubriques_personnelles:
        SousRubriqueCaisse.objects.get_or_create(
            rubrique=charges_personnelles,
            nom=nom,
            defaults={"description": f"Sous-rubrique : {nom}"},
        )


def reverse_seed(apps, schema_editor):
    """Annule les créations (get_or_create n'affecte que les nouveaux)."""
    RubriqueCaisse = apps.get_model('caisse', 'RubriqueCaisse')
    SousRubriqueCaisse = apps.get_model('caisse', 'SousRubriqueCaisse')

    # Supprimer les sous-rubriques créées
    SousRubriqueCaisse.objects.filter(nom__in=[
        "Loyers", "Intérêts bancaires", "Impôt et taxes",
        "Offrandes et dîmes", "Communication Tel & Int.",
        "Électricité", "Achats matériels", "Entretiens",
        "Maison Adolphe", "Maison Albert", "Benoît et Gabriel",
        "Maman et Famille", "Épargne (Personnelle)",
        "Projets (Personnels)", "Don", "Scolarité", "Soins de Santé",
    ]).delete()

    # Supprimer la rubrique "Autres entrées" si elle n'a pas de sous-rubriques
    RubriqueCaisse.objects.filter(nom="Autres entrées").delete()


class Migration(migrations.Migration):
    dependencies = [
        ('caisse', '0018_caissecourante_solde_final_usd_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_sous_rubriques, reverse_seed),
    ]