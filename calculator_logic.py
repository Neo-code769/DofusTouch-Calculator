"""
Logique métier pure du calculateur Dofus Touch.
Ce module ne contient aucune dépendance GUI et peut être testé indépendamment.
"""

import json
import os
from tabulate import tabulate

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "save.json")


# ---------------------------------------------------------------------------
# Calcul des ressources
# ---------------------------------------------------------------------------

def calculate_missing_resources(resources, inventory):
    """Calcule les ressources manquantes et le coût en kamas pour une recette.

    Args:
        resources: dict {nom_ressource: {"needed": int, "value": int}}
        inventory: dict {nom_ressource: int}

    Returns:
        (table_text: str, kamas_manquant: int)
    """
    kamas_manquant = 0
    table = []

    for resource, data in resources.items():
        acquired = inventory.get(resource, 0)
        lack = data["needed"] - acquired
        if lack > 0:
            kamas_manquant += lack * data["value"]
        table.append([
            resource.replace('_', ' '),
            data["needed"],
            acquired,
            max(0, lack),
            f"{data['value']:,}".replace(",", " "),
        ])

    table_text = tabulate(
        table,
        headers=["Ressource", "Requis", "Acquis", "Manquant", "Valeur unitaire"],
        tablefmt="grid"
    )
    return table_text, kamas_manquant


def get_recipe_completion(resources, inventory):
    """Calcule le taux de complétion d'une recette (ressources dont on a la quantité requise).

    Returns:
        (completed_count: int, total_count: int, completion_pct: int)
    """
    total = len(resources)
    if total == 0:
        return 0, 0, 100
    completed = sum(
        1 for resource, data in resources.items()
        if inventory.get(resource, 0) >= data["needed"]
    )
    pct = int(completed / total * 100)
    return completed, total, pct


# ---------------------------------------------------------------------------
# Parsing des entrées utilisateur
# ---------------------------------------------------------------------------

def parse_resource_updates(text, recipes):
    """Parse le texte de mise à jour des valeurs de ressources (format : nom, valeur).

    Returns:
        list de tuples (nom_ressource, nouvelle_valeur)
    Raises:
        ValueError si le format est invalide ou la ressource introuvable
    """
    if not text.strip():
        raise ValueError("Les mises à jour ne peuvent pas être vides.")

    updates = []
    for line in text.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) != 2:
            raise ValueError(f"Format incorrect : '{line.strip()}'. Utilisez : nom, nouvelle valeur")
        resource_name = parts[0].strip()
        try:
            new_value = int(parts[1].strip())
        except ValueError:
            raise ValueError(f"Valeur invalide pour '{resource_name}'. Doit être un entier.")
        found = any(resource_name in recipe for recipe in recipes.values())
        if not found:
            raise ValueError(f"Ressource '{resource_name}' introuvable dans les recettes.")
        updates.append((resource_name, new_value))
    return updates


def parse_inventory_updates(text, valid_resources):
    """Parse le texte de mise à jour de l'inventaire (format : nom, quantité).

    Returns:
        list de tuples (nom_ressource, quantité)
    Raises:
        ValueError si le format est invalide ou la ressource introuvable
    """
    if not text.strip():
        raise ValueError("L'inventaire ne peut pas être vide.")

    updates = []
    for line in text.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) != 2:
            raise ValueError(f"Format incorrect : '{line.strip()}'. Utilisez : nom, quantité")
        resource_name = parts[0].strip()
        try:
            quantity = int(parts[1].strip())
        except ValueError:
            raise ValueError(f"Quantité invalide pour '{resource_name}'. Doit être un entier.")
        if resource_name not in valid_resources:
            raise ValueError(f"Ressource '{resource_name}' introuvable dans l'inventaire.")
        updates.append((resource_name, quantity))
    return updates


def parse_new_recipe(name, text):
    """Parse le texte d'une nouvelle recette personnalisée.

    Format attendu : une ressource par ligne → nom, quantité, valeur_kamas

    Returns:
        dict {nom_ressource: {"needed": int, "value": int}}
    Raises:
        ValueError si le format est invalide
    """
    if not name.strip():
        raise ValueError("Le nom de la recette ne peut pas être vide.")
    if not text.strip():
        raise ValueError("La recette doit contenir au moins une ressource.")

    resources = {}
    for line in text.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) != 3:
            raise ValueError(
                f"Format incorrect : '{line.strip()}'. Utilisez : nom, quantité, valeur_kamas"
            )
        resource_name = parts[0].strip()
        try:
            needed = int(parts[1].strip())
            value = int(parts[2].strip())
        except ValueError:
            raise ValueError(
                f"Quantité et valeur doivent être des entiers pour '{resource_name}'."
            )
        if needed <= 0:
            raise ValueError(f"La quantité doit être positive pour '{resource_name}'.")
        resources[resource_name] = {"needed": needed, "value": value}

    if not resources:
        raise ValueError("La recette doit contenir au moins une ressource.")
    return resources


# ---------------------------------------------------------------------------
# Persistance locale (JSON)
# ---------------------------------------------------------------------------

def load_saved_data(filepath=None):
    """Charge les données sauvegardées depuis le fichier JSON.

    Returns:
        dict avec les clés 'inventory', 'recipe_values', 'custom_recipes'
    """
    filepath = filepath or DATA_FILE
    empty = {"inventory": {}, "recipe_values": {}, "custom_recipes": {}}
    if not os.path.exists(filepath):
        return empty
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "inventory": data.get("inventory", {}),
            "recipe_values": data.get("recipe_values", {}),
            "custom_recipes": data.get("custom_recipes", {}),
        }
    except (json.JSONDecodeError, IOError):
        return empty


def save_data(inventory, recipes, custom_recipe_names, filepath=None):
    """Sauvegarde l'inventaire et les recettes dans un fichier JSON.

    Args:
        inventory: dict de l'inventaire actuel
        recipes: dict de toutes les recettes (base + personnalisées)
        custom_recipe_names: set des noms de recettes personnalisées
        filepath: chemin optionnel (utilise DATA_FILE par défaut)
    """
    filepath = filepath or DATA_FILE
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    recipe_values = {}
    custom_recipes = {}
    for recipe_name, resources in recipes.items():
        if recipe_name in custom_recipe_names:
            custom_recipes[recipe_name] = {r: d.copy() for r, d in resources.items()}
        else:
            recipe_values[recipe_name] = {r: d["value"] for r, d in resources.items()}

    data = {
        "inventory": dict(inventory),
        "recipe_values": recipe_values,
        "custom_recipes": custom_recipes,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
