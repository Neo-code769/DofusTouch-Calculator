#!/usr/bin/env python3
"""
Import des recettes Dofus Touch depuis l'encyclopédie crawlit (dofapi).

Source : https://github.com/dofapi/crawlit-dofus-encyclopedia-parser
Données couvertes :
  - allequipments.json  (armures, chapeaux, capes, bottes, etc.)
  - allweapons.json     (épées, bâtons, arcs, etc.)
  - consumable.json     (potions, nourritures, etc.)

Seuls les objets possédant une recette non vide sont conservés.
Les valeurs en kamas sont initialisées à 0 (à mettre à jour via l'interface).

Usage :
    python scripts/import_dofus_touch_data.py
"""

import json
import os
import sys

import requests

BASE_URL = (
    "https://raw.githubusercontent.com/dofapi/"
    "crawlit-dofus-encyclopedia-parser/master/data/dofus-touch"
)

CATEGORIES = ["allequipments", "allweapons", "consumable"]

OUTPUT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "dofus_touch_recipes.json"
)


def _convert_item(item):
    """Convertit un objet crawlit en entrée de recette pour le calculateur.

    Format retourné :
        {nom_ressource: {"needed": int, "value": int}, ...}

    Returns None si l'objet n'a pas de recette.
    """
    raw = item.get("recipe", [])
    if not raw:
        return None

    resources = {}
    for ingredient in raw:
        for resource_name, data in ingredient.items():
            try:
                resources[resource_name] = {
                    "needed": int(data["quantity"]),
                    "value": 0,
                }
            except (KeyError, ValueError, TypeError):
                continue

    return resources if resources else None


def run(progress_callback=None):
    """Télécharge et convertit les données crawlit Dofus Touch.

    Args:
        progress_callback: callable(str) appelé à chaque étape pour le suivi.

    Returns:
        dict {nom_recette: {nom_ressource: {"needed": int, "value": int}}}

    Raises:
        requests.RequestException si le téléchargement échoue.
    """
    recipes = {}

    for category in CATEGORIES:
        url = f"{BASE_URL}/{category}.json"
        if progress_callback:
            progress_callback(f"Téléchargement : {category}.json …")

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        items = response.json()

        added = 0
        for item in items:
            recipe = _convert_item(item)
            if recipe is not None:
                name = item.get("name", "").strip()
                if name and name not in recipes:
                    recipes[name] = recipe
                    added += 1

        if progress_callback:
            progress_callback(f"  → {added} recettes trouvées dans {category}.json")

    output_path = os.path.abspath(OUTPUT_FILE)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)

    if progress_callback:
        progress_callback(f"\nTotal : {len(recipes)} recettes → {output_path}")

    return recipes


if __name__ == "__main__":
    try:
        run(progress_callback=print)
    except requests.RequestException as e:
        print(f"Erreur réseau : {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)
