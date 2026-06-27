#!/usr/bin/env python3
"""
Script d'ajout automatique du dual currency display sur les templates.
Remplace les patterns FC seuls par des dual_amount quand c'est pertinent.
"""

import re
import os
from pathlib import Path

# Templates à traiter
TEMPLATES = {
    "produits": [
        "templates/produits/article/article_details.html",
    ],
    "factures": [
        "templates/factures/facture_details.html",
        "templates/factures/factures.html",
        "templates/factures/partials/facture_summary_partial.html",
        "templates/factures/partials/lines_table.html",
    ],
    "approvisionnements": [
        "templates/approvisionnements/approvisionnement_form.html",
        "templates/approvisionnements/partials/lines_table.html",
    ],
    "rapports": [
        "templates/rapports/rapport_ventes.html",
        "templates/rapports/rapport_resultat.html",
        "templates/rapports/rapport_articles.html",
        "templates/rapports/rapport_caisses.html",
    ],
    "paie": [
        "templates/paie/paie_details.html",
        "templates/paie/paies.html",
        "templates/paie/agent_details.html",
    ],
}

# Patterns à remplacer (FC seul → dual_amount)
# On cible les montants significatifs, pas les compteurs
PATTERNS = [
    # Pattern: {{ montant|floatformat:0 }} FC
    (r'(\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\|floatformat:0\s*\}\})\s*<small[^>]*>FC</small>',
     r'{% if \2_usd %}{% autoescape off %}{{ \2_usd|dual_amount }}{% endautoescape %}{% else %}{{ \1 }}{% endif %}'),
    
    # Pattern: {{ montant|floatformat:2 }} FC
    (r'(\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\|floatformat:2\s*\}\})\s*<small[^>]*>FC</small>',
     r'{% if \2_usd %}{% autoescape off %}{{ \2_usd|dual_amount }}{% endautoescape %}{% else %}{{ \1 }}{% endif %}'),
]

# Ajout du load tag si absent
LOAD_TAG = "{% load currency_tags %}"


def process_template(filepath):
    """Ajoute le dual currency display à un template."""
    path = Path(filepath)
    if not path.exists():
        print(f"  ⚠️  Fichier non trouvé: {filepath}")
        return False
    
    content = path.read_text(encoding='utf-8')
    original = content
    
    # Ajouter le load tag si absent
    if LOAD_TAG not in content:
        # Insérer après {% load static %} ou au début du block
        if '{% load static %}' in content:
            content = content.replace('{% load static %}', '{% load static %}\n' + LOAD_TAG)
        elif '{% load caisse_tags %}' in content:
            content = content.replace('{% load caisse_tags %}', '{% load caisse_tags %}\n' + LOAD_TAG)
        else:
            # Ajouter après la première ligne
            lines = content.split('\n')
            lines.insert(1, LOAD_TAG)
            content = '\n'.join(lines)
    
    # Appliquer les patterns de remplacement
    for pattern, replacement in PATTERNS:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        path.write_text(content, encoding='utf-8')
        print(f"  ✅ Modifié: {filepath}")
        return True
    else:
        print(f"  ➖ Aucun changement: {filepath}")
        return False


def main():
    print("🚀 Ajout du dual currency display sur les templates...")
    print()
    
    modified = 0
    for module, files in TEMPLATES.items():
        print(f"📁 {module.upper()}:")
        for filepath in files:
            if process_template(filepath):
                modified += 1
        print()
    
    print(f"✨ Terminé: {modified} fichier(s) modifié(s)")


if __name__ == "__main__":
    main()