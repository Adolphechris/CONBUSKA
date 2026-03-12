from django.db import migrations


class Migration(migrations.Migration):
    """
    Renomme la table DB 'logs_activitylog' en 'activity_logs_activitylog'
    suite au renommage de l'app Django 'logs' → 'activity_logs'.
    """

    dependencies = [
        ('activity_logs', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE logs_activitylog RENAME TO activity_logs_activitylog;",
            reverse_sql="ALTER TABLE activity_logs_activitylog RENAME TO logs_activitylog;",
        ),
    ]
