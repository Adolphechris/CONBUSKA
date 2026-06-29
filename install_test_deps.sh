#!/bin/bash
# Installation des dépendances de test pour CONBUSCA

echo "=== Installation de python-decouple ==="
pip3 install python-decouple --break-system-packages --quiet

echo "=== Installation de pytest et pytest-django ==="
pip3 install pytest pytest-django --break-system-packages --quiet

echo "=== Installation des dépendances du projet ==="
pip3 install -r requirements.txt --break-system-packages --quiet 2>&1 | grep -v "Requirement already satisfied" || true

echo "=== Vérification ==="
python3 -c "import decouple; print('decouple OK')"
python3 -c "import pytest; print('pytest OK')"

echo "=== Installation terminée ==="