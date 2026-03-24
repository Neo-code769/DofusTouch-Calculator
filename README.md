# Dofus Touch Calculator

**Version 3.0** — Auteur : Pierre Trublereau

Outil Python pour le jeu **DOFUS Touch** (version 1.5 / mobile) permettant de calculer les ressources manquantes pour un craft, gérer son inventaire, analyser la rentabilité HDV et suivre sa progression dans le temps.

![DofusTouchCalculator-background](https://github.com/user-attachments/assets/f80194ac-c25a-4d22-901f-13f981cac853)

---

## Fonctionnalités

### Calcul de ressources
- Sélectionne une recette dans un menu déroulant
- Affiche un tableau détaillé : quantité requise, acquise, manquante, valeur unitaire
- Calcule le coût total en kamas des ressources manquantes
- Barre de progression indiquant le taux de complétion de la recette
- Vue récapitulative de toutes les recettes en une seule fenêtre

### Gestion de l'inventaire
- Interface dédiée pour saisir les quantités détenues de chaque ressource
- Sauvegarde automatique dans `data/save.json` à chaque modification
- Enregistrement automatique d'un snapshot de progression à chaque sauvegarde

### Valeurs en kamas
- Mise à jour manuelle des prix unitaires de chaque ressource
- Valeurs persistées entre les sessions

### Rentabilité HDV *(nouveau v3.0)*
- Saisie du prix de vente HDV directement dans la fenêtre de résultats
- Calcul en temps réel du bénéfice et de la marge en pourcentage
- Affichage en vert (rentable) ou rouge (déficitaire)
- Prix de vente persistés dans `data/sell_prices.json`

### Liste de courses multi-recettes *(nouveau v3.0)*
- Sélection de plusieurs recettes simultanément (Ctrl+clic)
- Agrégation des ressources communes : les quantités sont additionnées
- Tableau trié par ressource la plus manquante en premier
- Coût total estimé de l'ensemble de la commande

### Mise à jour automatique des prix via DofusDB *(nouveau v3.0)*
- Interroge l'API `api.dofusdb.fr` pour récupérer les prix HDV réels
- Fonctionne en arrière-plan (thread), sans bloquer l'interface
- Fenêtre de log en temps réel pendant la mise à jour
- Gestion gracieuse des erreurs réseau (best-effort, silencieux si indisponible)

### Import des recettes Dofus Touch *(nouveau v2.0)*
- Télécharge automatiquement les recettes depuis l'encyclopédie crawlit (dofapi)
- Catégories couvertes : équipements, armes, consommables
- Import en arrière-plan avec fenêtre de progression
- Les valeurs kamas personnalisées sont préservées après chaque import
- Identifiants de ressources stockés pour les requêtes DofusDB

### Recettes personnalisées
- Ajout de recettes custom via une interface dédiée
- Format : `nom_ressource, quantité, valeur_kamas`
- Recettes sauvegardées dans `data/save.json`

### Historique et statistiques *(nouveau v3.0)*
- Snapshot automatique de la progression à chaque sauvegarde d'inventaire
- Stockage des 100 derniers snapshots par recette dans `data/history.json`
- Graphiques matplotlib intégrés : taux de complétion et kamas manquants dans le temps
- Visualisation par recette dans une fenêtre dédiée

### Interface web Flask *(nouveau v3.0)*
- Application web accessible via navigateur, sans dépendance tkinter
- Thème Bootstrap 5 sombre
- Fonctionnalités disponibles :
  - Calcul d'une recette avec barre de progression et tableau
  - Calcul de rentabilité HDV (saisie du prix de vente)
  - Liste de courses multi-recettes
- API REST JSON (`/api/calculate`, `/api/shopping-list`, `/api/sell-price`, `/api/recipes`)

### Conteneurisation Docker
- Image basée sur `python:3.11-slim` avec support X11 pour la GUI tkinter
- Volume `/app/data` pour la persistance des données utilisateur

---

## Installation

### Prérequis

- Python 3.10 ou supérieur
- `pip`

### Dépendances

```bash
pip install -r requirements.txt
```

Dépendances incluses : `tabulate`, `Pillow`, `requests`, `ttkbootstrap`, `pytest`, `flask`, `matplotlib`

---

## Lancement

### Interface graphique (tkinter)

```bash
python DofusCalculator.py
```

### Interface web (Flask)

```bash
python web_app.py
```

Ouvre ensuite [http://localhost:5000](http://localhost:5000) dans ton navigateur.

### Import des recettes Dofus Touch (script standalone)

```bash
python scripts/import_dofus_touch_data.py
```

Télécharge les recettes depuis l'encyclopédie crawlit et les enregistre dans `data/dofus_touch_recipes.json`.

---

## Docker

### Construction de l'image

```bash
docker build -t dofus-touch-calculator .
```

### Lancement (Linux avec X11)

```bash
docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/data:/app/data dofus-touch-calculator
```

---

## Structure du projet

```
DofusTouch-Calculator/
├── DofusCalculator.py          # Interface graphique principale (tkinter + ttkbootstrap)
├── web_app.py                  # Interface web Flask
├── calculator_logic.py         # Logique métier pure (sans GUI)
├── Recettes.py                 # 6 recettes hardcodées
├── Inventory.py                # Inventaire de base (36 ressources)
├── requirements.txt            # Dépendances Python
├── Dockerfile                  # Image Docker
├── scripts/
│   └── import_dofus_touch_data.py  # Import crawlit depuis GitHub
├── templates/
│   └── index.html              # Interface web Bootstrap 5
├── tests/
│   └── test_calculator.py      # 95 tests unitaires (pytest)
└── data/                       # Données utilisateur (ignoré par git)
    ├── save.json               # Inventaire + valeurs + recettes custom
    ├── sell_prices.json        # Prix de vente HDV par recette
    ├── history.json            # Historique de progression
    └── dofus_touch_recipes.json  # Recettes importées depuis crawlit
```

---

## Tests

```bash
python -m pytest tests/test_calculator.py -v
```

**95 tests** couvrant :

| Classe de test | Tests | Fonctionnalités |
|---|---|---|
| `TestCalculateMissingResources` | 12 | Calcul des ressources manquantes et kamas |
| `TestGetRecipeCompletion` | 6 | Taux de complétion d'une recette |
| `TestParseResourceUpdates` | 11 | Parsing des mises à jour de valeurs |
| `TestParseInventoryUpdates` | 10 | Parsing des mises à jour d'inventaire |
| `TestParseNewRecipe` | 11 | Parsing des recettes personnalisées |
| `TestPersistence` | 6 | Sauvegarde / chargement JSON |
| `TestLoadDofusTouchRecipes` | 5 | Chargement des recettes crawlit |
| `TestImportConversion` | 9 | Conversion des données crawlit |
| `TestCalculateProfitability` | 5 | Calcul de rentabilité HDV |
| `TestSellPricesPersistence` | 4 | Persistance des prix de vente |
| `TestAggregateShoppingList` | 8 | Agrégation multi-recettes |
| `TestHistory` | 8 | Historique de progression |

---

## API REST (interface web)

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/` | Interface web principale |
| `GET` | `/api/recipes` | Liste de toutes les recettes |
| `POST` | `/api/calculate` | Calcul d'une recette `{"recipe_name": "..."}` |
| `POST` | `/api/sell-price` | Enregistre un prix HDV `{"recipe_name": "...", "sell_price": 500000}` |
| `POST` | `/api/shopping-list` | Liste de courses `{"recipe_names": ["...", "..."]}` |

---

## Source des données

Les recettes Dofus Touch sont importées depuis le projet open-source **crawlit** :
[dofapi/crawlit-dofus-encyclopedia-parser](https://github.com/dofapi/crawlit-dofus-encyclopedia-parser)

Ces données sont spécifiques à **Dofus Touch** (version mobile 1.5) et n'incluent pas les données de Dofus 3 PC.

---

## Historique des versions

| Version | Changements |
|---|---|
| **3.0** | Rentabilité HDV, liste de courses multi-recettes, mise à jour prix DofusDB, interface web Flask, historique matplotlib, 95 tests |
| **2.1** | Séparation logique métier / GUI (`calculator_logic.py`), barre de complétion, 68 tests |
| **2.0** | Import recettes crawlit Dofus Touch, recettes personnalisées, sauvegarde locale JSON, Docker |
| **1.4** | Mise à jour des valeurs kamas depuis l'interface |
| **1.3** | Amélioration gestion des erreurs et UX |
| **1.2** | Amélioration interface graphique, image de fond |
| **1.1** | Mise à jour des valeurs des ressources |
| **1.0** | Script de base pour le calcul des ressources |
