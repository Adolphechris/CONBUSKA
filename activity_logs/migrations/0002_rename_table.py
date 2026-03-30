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
            # Conditionnel : sur une DB existante, renomme l'ancienne table.
            # Sur une DB fraîche (tests), 0001_initial crée déjà le bon nom — no-op.
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'logs_activitylog'
                    ) THEN
                        ALTER TABLE logs_activitylog
                            RENAME TO activity_logs_activitylog;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'activity_logs_activitylog'
                    ) THEN
                        ALTER TABLE activity_logs_activitylog
                            RENAME TO logs_activitylog;
                    END IF;
                END $$;
            """,
        ),
    ]
