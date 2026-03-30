from django.db import migrations, models


def backfill_rubrique_classification(apps, schema_editor):
    RubriqueCaisse = apps.get_model("caisse", "RubriqueCaisse")

    classification_map = {
        "charges exploitation": "CHARGE_EXPLOITATION",
        "transport": "CHARGE_EXPLOITATION",
        "restauration": "CHARGE_EXPLOITATION",
        "avance sur salaire": "CHARGE_EXPLOITATION",
        "assistance sociale": "CHARGE_EXPLOITATION",
        "charges personnelles": "CHARGE_PERSONNELLE",
    }

    for rubrique in RubriqueCaisse.objects.all():
        rubrique.classification_metier = classification_map.get(
            (rubrique.nom or "").strip().lower(),
            "NONE",
        )
        rubrique.save(update_fields=["classification_metier"])


class Migration(migrations.Migration):
    dependencies = [
        ("caisse", "0015_alter_caissecourante_solde_final_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="rubriquecaisse",
            name="classification_metier",
            field=models.CharField(
                choices=[
                    ("NONE", "Aucune"),
                    ("CHARGE_EXPLOITATION", "Charge d'exploitation"),
                    ("CHARGE_PERSONNELLE", "Charge personnelle"),
                ],
                db_index=True,
                default="NONE",
                max_length=32,
            ),
        ),
        migrations.RunPython(
            backfill_rubrique_classification,
            migrations.RunPython.noop,
        ),
    ]
