#!/bin/bash

# Script pour lancer Chrome avec profil natif et exécuter les tâches

echo "🚀 Lancement de Chrome avec profil natif..."
echo "   (fermez d'abord Chrome si ouvert)"

# Tuer les processus Chrome existants
pkill -f chrome 2>/dev/null
sleep 2

# Lancer Chrome avec le profil natif et le port de debug
google-chrome \
  --user-data-dir=/home/adolphe/.config/google-chrome \
  --remote-debugging-port=9222 \
  --no-first-run \
  --no-default-browser-check \
  &

echo "⏳ Attente du démarrage de Chrome..."
sleep 5

echo "✅ Chrome lancé avec profil natif"
echo "📱 Connexion au port 9222..."

# Exécuter les tâches
cd /home/adolphe/CONBUSCA/boutique
node auto_chrome_tasks_v2.cjs