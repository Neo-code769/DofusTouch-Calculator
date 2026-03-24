"""
Logique métier pure du calculateur Dofus Touch.
Ce module ne contient aucune dépendance GUI et peut être testé indépendamment.
"""

import json
import os
from tabulate import tabulate

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "save.json")
DOFUS_TOUCH_RECIPES_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "dofus_touch_recipes.json"
)


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


def load_dofus_touch_recipes(filepath=None):
    """Charge les recettes importées depuis l'encyclopédie Dofus Touch (crawlit).

    Le fichier est généré par scripts/import_dofus_touch_data.py.

    Args:
        filepath: chemin optionnel (utilise DOFUS_TOUCH_RECIPES_FILE par défaut)

    Returns:
        dict {nom_recette: {nom_ressource: {"needed": int, "value": int}}}
        Retourne un dict vide si le fichier n'existe pas ou est corrompu.
    """
    filepath = filepath or DOFUS_TOUCH_RECIPES_FILE
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Validation minimale : doit être un dict de dicts
        if not isinstance(data, dict):
            return {}
        return data
    except (json.JSONDecodeError, IOError):
        return {}


# ---------------------------------------------------------------------------
# Axe 1 — Rentabilité HDV
# ---------------------------------------------------------------------------

SELL_PRICES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sell_prices.json")


def load_sell_prices(filepath=None):
    """Charge les prix de vente HDV sauvegardés.

    Returns:
        dict {nom_recette: int}
    """
    filepath = filepath or SELL_PRICES_FILE
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, IOError):
        return {}


def save_sell_prices(sell_prices, filepath=None):
    """Sauvegarde les prix de vente HDV dans un fichier JSON."""
    filepath = filepath or SELL_PRICES_FILE
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(sell_prices, f, ensure_ascii=False, indent=2)


def calculate_profitability(craft_cost, sell_price):
    """Calcule la rentabilité d'un craft.

    Args:
        craft_cost: coût total du craft en kamas
        sell_price: prix de vente HDV en kamas

    Returns:
        dict avec les clés:
            profit: int (peut être négatif)
            margin_pct: float (peut être négatif)
            is_profitable: bool
    """
    profit = sell_price - craft_cost
    margin_pct = (profit / craft_cost * 100) if craft_cost > 0 else 0.0
    return {
        "profit": profit,
        "margin_pct": round(margin_pct, 1),
        "is_profitable": profit > 0,
    }


# ---------------------------------------------------------------------------
# Axe 2 — Agrégateur de courses multi-recettes
# ---------------------------------------------------------------------------

def aggregate_shopping_list(selected_recipe_names, recipes, inventory):
    """Agrège les ressources manquantes pour plusieurs recettes simultanément.

    Args:
        selected_recipe_names: list de noms de recettes à considérer
        recipes: dict complet des recettes
        inventory: dict {nom_ressource: int}

    Returns:
        list de dicts triés par manquant décroissant:
            [{"resource": str, "needed": int, "acquired": int, "missing": int, "unit_value": int, "total_cost": int}]
    """
    aggregated = {}

    for name in selected_recipe_names:
        recipe = recipes.get(name, {})
        for resource, data in recipe.items():
            if resource not in aggregated:
                aggregated[resource] = {"needed": 0, "value": data.get("value", 0)}
            aggregated[resource]["needed"] += data.get("needed", 0)
            # Garde la valeur unitaire la plus récente (cohérente entre recettes)
            aggregated[resource]["value"] = data.get("value", aggregated[resource]["value"])

    result = []
    for resource, data in aggregated.items():
        acquired = inventory.get(resource, 0)
        missing = max(0, data["needed"] - acquired)
        result.append({
            "resource": resource,
            "needed": data["needed"],
            "acquired": acquired,
            "missing": missing,
            "unit_value": data["value"],
            "total_cost": missing * data["value"],
        })

    result.sort(key=lambda x: x["missing"], reverse=True)
    return result


# ---------------------------------------------------------------------------
# Axe 3 — Mise à jour automatique des prix via DofusDB
# ---------------------------------------------------------------------------

def fetch_prices_from_dofusdb(resource_name_to_id, timeout=10):
    """Récupère les prix HDV depuis l'API DofusDB (best-effort).

    Args:
        resource_name_to_id: dict {nom_ressource: id_item (str ou int)}
        timeout: secondes avant abandon par requête

    Returns:
        dict {nom_ressource: prix_int}  — les ressources sans prix sont absentes du résultat
    """
    try:
        import requests
    except ImportError:
        return {}

    prices = {}
    base_url = "https://api.dofusdb.fr/items"

    for resource_name, item_id in resource_name_to_id.items():
        if not item_id:
            continue
        try:
            resp = requests.get(f"{base_url}/{item_id}", timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                # DofusDB retourne avgPrice ou price selon l'endpoint
                price = data.get("avgPrice") or data.get("price") or 0
                if price and int(price) > 0:
                    prices[resource_name] = int(price)
        except Exception:
            continue

    return prices


# ---------------------------------------------------------------------------
# Axe 5 — Historique et statistiques de progression
# ---------------------------------------------------------------------------

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "history.json")


def record_snapshot(recipe_name, completed, total, kamas_manquant, filepath=None):
    """Enregistre un instantané de progression pour une recette.

    Args:
        recipe_name: nom de la recette
        completed: nombre de ressources complètes
        total: nombre total de ressources
        kamas_manquant: coût total des ressources manquantes
        filepath: chemin optionnel (utilise HISTORY_FILE par défaut)
    """
    import datetime
    filepath = filepath or HISTORY_FILE
    history = load_history(filepath)

    if recipe_name not in history:
        history[recipe_name] = []

    pct = int(completed / total * 100) if total > 0 else 100
    history[recipe_name].append({
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "completed": completed,
        "total": total,
        "pct": pct,
        "kamas_manquant": kamas_manquant,
    })

    # Garde uniquement les 100 derniers snapshots par recette
    history[recipe_name] = history[recipe_name][-100:]

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_history(filepath=None):
    """Charge l'historique de progression.

    Returns:
        dict {nom_recette: [{"date": str, "completed": int, "total": int, "pct": int, "kamas_manquant": int}]}
    """
    filepath = filepath or HISTORY_FILE
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, IOError):
        return {}
