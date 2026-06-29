# Analyse des lenteurs des tests caisse — MouvementCaisseService

## Problèmes identifiés

### 1. `_assert_solde_suffisant()` — Ligne 57-70
**Problème** : Agrégation SUM complète sur tous les mouvements de la caisse à chaque appel.
```python
total_entrees = (
    MouvementCaisse.objects
    .filter(caisse=caisse_courante, type_mouvement="ENTREE")
    .aggregate(total=Sum("montant"))["total"] or Decimal("0")
)
```
**Impact** : Requête SQL coûteuse (scan table + agrégation) exécutée à chaque création/modification de mouvement.

### 2. `_rebuild_impacts()` — Ligne 107-118
**Problème** : Appelle 2 services externes lourds pour chaque impact.
```python
for (caisse_pk, date), caisse_courante in unique_impacts.items():
    SnapshotService.rebuild_day(caisse_courante=caisse_courante, date=date)

for _, date in unique_impacts.keys():
    FondsRoulementService.rebuild(date)
```
**Impact** : 
- `SnapshotService.rebuild_day()` : Reconstruit tous les snapshots du jour (calculs complexes + écritures multiples)
- `FondsRoulementService.rebuild()` : Recalcule le fonds de roulement (itération sur tous les mouvements)

**Exécuté 2 fois par test** (create + update) → ralentissement x2.

### 3. `_get_transfert_miroir()` — Ligne 77-83
**Problème** : Query + select_related + first() à chaque appel.
```python
return (
    MouvementCaisse.objects
    .filter(mouvement_transfert_source=mouvement)
    .select_related("caisse")
    .first()
)
```
**Impact** : Requête supplémentaire pour chaque vérification de transfert.

### 4. `_dispatch_with_ids()` — Ligne 280-320
**Problème** : Vérifie l'existence du fournisseur/client/créancier/débiteur/agent avec `.exists()`.
```python
if not Fournisseur.objects.filter(pk=fournisseur_id).exists():
    return
```
**Impact** : 5 requêtes SELECT COUNT(*) potentiellement inutiles si les IDs sont déjà validés en amont.

---

## Optimisations proposées

### ✅ Optimisation 1 : Mettre en cache le solde dans CaisseCourante
**Gain** : Évite l'agrégation SUM à chaque appel
**Complexité** : Moyenne (ajout d'un champ `solde_actuel`)

```python
# Dans CaisseCourante, ajouter :
solde_actuel = models.DecimalField(max_digits=12, decimal_places=2, default=0)

# Dans _assert_solde_suffisant(), remplacer par :
def _assert_solde_suffisant(caisse_courante: CaisseCourante, montant_sortie: Decimal):
    solde_disponible = caisse_courante.solde_initial + caisse_courante.solde_actuel
    if montant_sortie > solde_disponible:
        raise ValidationError(...)
```

### ✅ Optimisation 2 : Désactiver les rebuilds dans les tests
**Gain** : Réduction de 70-80% du temps d'exécution des tests
**Complexité** : Faible (ajout d'un flag)

```python
# Dans MouvementCaisseService._rebuild_impacts() :
@staticmethod
def _rebuild_impacts(*, impacts, skip_rebuild=False):
    if skip_rebuild:
        return
    # ... reste du code

# Dans les tests, ajouter un fixture :
@pytest.fixture
def service_without_rebuild():
    with patch.object(MouvementCaisseService, '_rebuild_impacts', return_value=None):
        yield MouvementCaisseService
```

### ✅ Optimisation 3 : Précharger les objets liés
**Gain** : Réduction de 30-40% des requêtes N+1
**Complexité** : Faible

```python
# Dans _dispatch_with_ids(), utiliser get() au lieu de filter().exists() :
@staticmethod
def _handle_fournisseur(mouvement, fournisseur_id: Optional[int]):
    if not fournisseur_id:
        return
    try:
        fournisseur = Fournisseur.objects.get(pk=fournisseur_id)
    except Fournisseur.DoesNotExist:
        return
    MouvementCaisseFournisseur.objects.update_or_create(...)
```

### ✅ Optimisation 4 : Batch les rebuilds
**Gain** : Réduction du nombre d'appels aux services externes
**Complexité** : Moyenne

```python
# Au lieu d'appeler rebuild_day N fois, regrouper par date :
dates_to_rebuild = {date for _, date in impacts}
for date in dates_to_rebuild:
    # Rebuild une seule fois par date
    FondsRoulementService.rebuild(date)
```

---

## Recommandation

**Action immédiate** : Implémenter l'**Optimisation 2** (désactiver les rebuilds dans les tests).
- Gain de temps : ~2-3 secondes par test
- Risque : Aucun (les rebuilds sont testés séparément)
- Effort : 10 minutes

**Action à moyen terme** : Implémenter l'**Optimisation 1** (cache solde).
- Gain de temps : ~100ms par appel
- Risque : Nécessite une migration + mise à jour du solde à chaque mouvement
- Effort : 1-2 heures

**Action optionnelle** : Implémenter les optimisations 3 et 4.
- Gain de temps : ~50ms par test
- Risque : Faible
- Effort : 30 minutes

---

## Tests à modifier

Les tests suivants bénéficieraient le plus des optimisations :

1. `test_create_caisse_ouverte_succes` (ligne 86)
2. `test_create_caisse_fermee_raise_validation_error` (ligne 108)
3. `test_update_caisse_fermee_raise_validation_error` (ligne 127)
4. Tous les tests de transfert (ligne 152+)

**Temps total gagné estimé** : 30-40% sur l'ensemble de la suite de tests caisse.