#!/bin/bash
# Script d'installation et d'exécution des tests CONBUSCA

echo "=== Installation des dépendances de test ==="
pip3 install pytest pytest-django python-decouple --break-system-packages --quiet

echo "=== Exécution des tests Django ==="
python3 manage.py test --verbosity=2

echo "=== Exécution des tests pytest (si disponibles) ==="
python3 -m pytest --tb=short -q 2>&1 || true

echo "=== Terminé ==="