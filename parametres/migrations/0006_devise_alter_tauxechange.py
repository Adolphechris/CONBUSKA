import django.db.models.deletion
from django.db import migrations, models


def create_initial_devises(apps, schema_editor):
    Devise = apps.get_model('parametres', 'Devise')
    initial = [
        {'code': 'USD', 'nom': 'Dollar US',         'symbole': '$',  'actif': True},
        {'code': 'CDF', 'nom': 'Franc Congolais',   'symbole': 'FC', 'actif': True},
        {'code': 'EUR', 'nom': 'Euro',               'symbole': '€',  'actif': True},
    ]
    for d in initial:
        Devise.objects.get_or_create(code=d['code'], defaults=d)


class Migration(migrations.Migration):

    dependencies = [
        ('parametres', '0005_historicaltauxechange_tauxechange'),
    ]

    operations = [
        # 1. Create Devise model
        migrations.CreateModel(
            name='Devise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=5, unique=True, verbose_name='Code')),
                ('nom', models.CharField(max_length=50, verbose_name='Nom')),
                ('symbole', models.CharField(max_length=5, verbose_name='Symbole')),
                ('actif', models.BooleanField(default=True, verbose_name='Active')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Devise',
                'verbose_name_plural': 'Devises',
                'ordering': ['code'],
            },
        ),
        # 2. Populate initial devises
        migrations.RunPython(create_initial_devises, migrations.RunPython.noop),
        # 3. Widen TauxEchange CharField from max_length=3 to max_length=5 (removes choices)
        migrations.AlterField(
            model_name='tauxechange',
            name='devise_source',
            field=models.CharField(default='USD', max_length=5, verbose_name='Devise source'),
        ),
        migrations.AlterField(
            model_name='tauxechange',
            name='devise_cible',
            field=models.CharField(default='CDF', max_length=5, verbose_name='Devise cible'),
        ),
        # 4. Same for historical model
        migrations.AlterField(
            model_name='historicaltauxechange',
            name='devise_source',
            field=models.CharField(default='USD', max_length=5, verbose_name='Devise source'),
        ),
        migrations.AlterField(
            model_name='historicaltauxechange',
            name='devise_cible',
            field=models.CharField(default='CDF', max_length=5, verbose_name='Devise cible'),
        ),
    ]
