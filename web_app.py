"""
Interface web Flask pour le Dofus Touch Calculator.

Axe 4 — accès via navigateur sans dépendance tkinter.

Usage :
    pip install flask
    python web_app.py
    Ouvre http://localhost:5000 dans ton navigateur.
"""

from flask import Flask, jsonify, render_template, request

from calculator_logic import (
    aggregate_shopping_list,
    calculate_missing_resources,
    calculate_profitability,
    get_recipe_completion,
    load_dofus_touch_recipes,
    load_saved_data,
    load_sell_prices,
    save_sell_prices,
)
from Inventory import inventory as _base_inventory
from Recettes import recipes as _base_recipes

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Chargement des données au démarrage
# ---------------------------------------------------------------------------

def _build_state():
    """Construit l'état (recettes + inventaire) en fusionnant les sources."""
    recipes = dict(_base_recipes)
    inv = dict(_base_inventory)

    # Recettes crawlit (non-destructif)
    for name, res in load_dofus_touch_recipes().items():
        if name not in recipes:
            recipes[name] = res
        for rname in res:
            if rname not in inv:
                inv[rname] = 0

    # Données sauvegardées
    saved = load_saved_data()
    for resource, qty in saved["inventory"].items():
        inv[resource] = qty
    for recipe_name, values in saved["recipe_values"].items():
        if recipe_name in recipes:
            for resource, value in values.items():
                if resource in recipes[recipe_name]:
                    recipes[recipe_name][resource]["value"] = value
    for recipe_name, res_data in saved["custom_recipes"].items():
        recipes[recipe_name] = res_data

    return recipes, inv


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    recipes, _ = _build_state()
    return render_template("index.html", recipe_names=sorted(recipes.keys()))


@app.route("/api/recipes")
def api_recipes():
    recipes, _ = _build_state()
    return jsonify(sorted(recipes.keys()))


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    data = request.get_json(force=True)
    recipe_name = data.get("recipe_name", "")
    recipes, inv = _build_state()

    if recipe_name not in recipes:
        return jsonify({"error": f"Recette '{recipe_name}' introuvable."}), 404

    resources = recipes[recipe_name]
    _, kamas_manquant = calculate_missing_resources(resources, inv)
    completed, total, pct = get_recipe_completion(resources, inv)

    sell_prices = load_sell_prices()
    sell_price = sell_prices.get(recipe_name, 0)
    profitability = calculate_profitability(kamas_manquant, sell_price) if sell_price else None

    rows = []
    for rname, rdata in resources.items():
        acquired = inv.get(rname, 0)
        missing = max(0, rdata["needed"] - acquired)
        rows.append({
            "resource": rname.replace("_", " "),
            "needed": rdata["needed"],
            "acquired": acquired,
            "missing": missing,
            "unit_value": rdata["value"],
            "total_cost": missing * rdata["value"],
        })

    return jsonify({
        "recipe_name": recipe_name,
        "rows": rows,
        "kamas_manquant": kamas_manquant,
        "completed": completed,
        "total": total,
        "pct": pct,
        "sell_price": sell_price,
        "profitability": profitability,
    })


@app.route("/api/sell-price", methods=["POST"])
def api_set_sell_price():
    data = request.get_json(force=True)
    recipe_name = data.get("recipe_name", "")
    try:
        sell_price = int(data.get("sell_price", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Prix invalide."}), 400

    sell_prices = load_sell_prices()
    sell_prices[recipe_name] = sell_price
    save_sell_prices(sell_prices)
    return jsonify({"ok": True})


@app.route("/api/shopping-list", methods=["POST"])
def api_shopping_list():
    data = request.get_json(force=True)
    selected = data.get("recipe_names", [])
    recipes, inv = _build_state()

    if not selected:
        return jsonify({"error": "Sélectionnez au moins une recette."}), 400

    items = aggregate_shopping_list(selected, recipes, inv)
    total_cost = sum(it["total_cost"] for it in items)
    return jsonify({"items": items, "total_cost": total_cost})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
