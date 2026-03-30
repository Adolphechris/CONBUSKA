"""
paie/constants.py

Constantes du module paie.
Centralise les noms de rubriques pour éviter les strings hardcodées
dans les services, selectors et vues.
"""


class RubriquePaie:
    """
    Noms canoniques des rubriques de paie.
    Référencent les RubriqueCaisse par leur nom exact.

    Usage :
        RubriqueCaisse.objects.get(nom=RubriquePaie.AVANCE_SALAIRE)
    """

    # ── Ligne de base du bulletin ──────────────────────────────────────
    SALAIRE_BASE = "Salaire de base"

    # ── Gains (versements périodiques via caisse) ──────────────────────
    TRANSPORT    = "Transport"
    RESTAURATION = "Restauration"
    ASSISTANCE   = "Assistance sociale"
    AUTRE_PRIME  = "Autre prime"

    # ── Retenues ──────────────────────────────────────────────────────
    AVANCE_SALAIRE = "Avance sur salaire"

    # ── Décaissement final du salaire ──────────────────────────────────
    # Mouvement caisse créé lors de la validation de la paie.
    # = salaire_brut − total_avances_du_mois
    SOLDE_SALAIRE = "Solde sur salaire"

    # ── Réservés — intégration légale future (taux = 0 pour l'instant) ─
    CNSS_SALARIALE = "CNSS salariale"
    IPR            = "IPR"
    AUTRE_RETENUE  = "Autre retenue"

    # ── Groupes pour les requêtes ──────────────────────────────────────
    # Rubriques caisse dont les montants s'ajoutent au salaire brut
    RUBRIQUES_PRIMES: list[str] = [TRANSPORT, RESTAURATION, ASSISTANCE]

    # Rubriques caisse déduites du salaire brut
    RUBRIQUES_RETENUES: list[str] = [AVANCE_SALAIRE]
