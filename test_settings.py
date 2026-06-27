"""Test settings override: import existing dev settings, switch DB to sqlite3 in-memory
and remove activity_logs to avoid problematic migrations during unit tests.
"""
from importlib import import_module

# Import the project's dev settings
dev = import_module('esm.settings.dev')

# Import all names from dev into this module
from esm.settings.dev import *  # noqa: F401,F403

# Use an in-memory sqlite DB for tests to avoid interacting with Postgres templates
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Remove activity_logs to skip its migrations which cause index conflicts in this environment
INSTALLED_APPS = [a for a in INSTALLED_APPS if a != 'activity_logs']

# Avoid running activity_logs migrations (they contain Postgres-specific SQL)
MIGRATION_MODULES = {
    'activity_logs': None,
}
