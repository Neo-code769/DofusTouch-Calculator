"""Tests unitaires pour calculator_logic.py"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculator_logic import (
    calculate_missing_resources,
    get_recipe_completion,
    parse_resource_updates,
    parse_inventory_updates,
    parse_new_recipe,
    load_saved_data,
    save_data,
    load_dofus_touch_recipes,
    calculate_profitability,
    load_sell_prices,
    save_sell_prices,
    aggregate_shopping_list,
    record_snapshot,
    load_history,
)


# ---------------------------------------------------------------------------
# calculate_missing_resources
# ---------------------------------------------------------------------------

class TestCalculateMissingResources:

    def test_basic_missing(self):
        resources = {"orbe_irisé": {"needed": 10, "value": 1000}}
        inventory = {"orbe_irisé": 3}
        _, kamas = calculate_missing_resources(resources, inventory)
        assert kamas == 7 * 1000

    def test_all_resources_available(self):
        resources = {"orbe_irisé": {"needed": 5, "value": 1000}}
        inventory = {"orbe_irisé": 10}
        _, kamas = calculate_missing_resources(resources, inventory)
        assert kamas == 0

    def test_resource_absent_from_inventory_defaults_to_zero(self):
        resources = {"orbe_irisé": {"needed": 5, "value": 2000}}
        inventory = {}
        _, kamas = calculate_missing_resources(resources, inventory)
        assert kamas == 5 * 2000

    def test_surplus_not_counted_in_kamas(self):
        resources = {"orbe_irisé": {"needed": 3, "value": 1000}}
        inventory = {"orbe_irisé": 10}
        _, kamas = calculate_missing_resources(resources, inventory)
        assert kamas == 0

    def test_surplus_shows_zero_in_table(self):
        resources = {"orbe_irisé": {"needed": 3, "value": 1000}}
        inventory = {"orbe_irisé": 10}
        table_text, _ = calculate_missing_resources(resources, inventory)
        lines = [l for l in table_text.splitlines() if "orbe" in l]
        assert len(lines) == 1
        # La colonne Manquant doit contenir 0 (pas une valeur négative)
        assert "| -" not in lines[0]
        assert "0" in lines[0]

    def test_empty_recipe(self):
        _, kamas = calculate_missing_resources({}, {})
        assert kamas == 0

    def test_zero_value_resource_adds_nothing_to_kamas(self):
        resources = {"docteur": {"needed": 1, "value": 0}}
        inventory = {}
        _, kamas = calculate_missing_resources(resources, inventory)
        assert kamas == 0

    def test_kamas_sum_across_multiple_resources(self):
        resources = {
            "res_a": {"needed": 10, "value": 5000},
            "res_b": {"needed": 20, "value": 200},
        }
        inventory = {"res_a": 4, "res_b": 10}
        _, kamas = calculate_missing_resources(resources, inventory)
        assert kamas == 6 * 5000 + 10 * 200

    def test_table_contains_resource_name_without_underscore(self):
        resources = {"orbe_irisé": {"needed": 5, "value": 1000}}
        inventory = {}
        table_text, _ = calculate_missing_resources(resources, inventory)
        assert "orbe irisé" in table_text

    def test_table_headers_present(self):
        resources = {"orbe_irisé": {"needed": 5, "value": 1000}}
        inventory = {}
        table_text, _ = calculate_missing_resources(resources, inventory)
        for header in ["Ressource", "Requis", "Acquis", "Manquant", "Valeur unitaire"]:
            assert header in table_text

    def test_exact_inventory_match_produces_zero_kamas(self):
        resources = {"res": {"needed": 7, "value": 500}}
        inventory = {"res": 7}
        _, kamas = calculate_missing_resources(resources, inventory)
        assert kamas == 0

    def test_only_missing_resources_counted(self):
        resources = {
            "res_a": {"needed": 5, "value": 100},  # surplus
            "res_b": {"needed": 5, "value": 100},  # manquant
        }
        inventory = {"res_a": 10, "res_b": 0}
        _, kamas = calculate_missing_resources(resources, inventory)
        assert kamas == 5 * 100


# ---------------------------------------------------------------------------
# get_recipe_completion
# ---------------------------------------------------------------------------

class TestGetRecipeCompletion:

    def test_all_complete(self):
        resources = {"a": {"needed": 5, "value": 0}, "b": {"needed": 3, "value": 0}}
        inventory = {"a": 10, "b": 5}
        completed, total, pct = get_recipe_completion(resources, inventory)
        assert completed == 2
        assert total == 2
        assert pct == 100

    def test_none_complete(self):
        resources = {"a": {"needed": 5, "value": 0}}
        inventory = {}
        completed, total, pct = get_recipe_completion(resources, inventory)
        assert completed == 0
        assert total == 1
        assert pct == 0

    def test_partial_completion(self):
        resources = {
            "a": {"needed": 5, "value": 0},  # have 5 → complet
            "b": {"needed": 3, "value": 0},  # have 1 → incomplet
        }
        inventory = {"a": 5, "b": 1}
        completed, total, pct = get_recipe_completion(resources, inventory)
        assert completed == 1
        assert total == 2
        assert pct == 50

    def test_empty_recipe_returns_100_percent(self):
        completed, total, pct = get_recipe_completion({}, {})
        assert pct == 100
        assert total == 0

    def test_exact_quantity_counts_as_complete(self):
        resources = {"a": {"needed": 7, "value": 0}}
        inventory = {"a": 7}
        completed, _, pct = get_recipe_completion(resources, inventory)
        assert completed == 1
        assert pct == 100

    def test_one_less_than_needed_is_incomplete(self):
        resources = {"a": {"needed": 7, "value": 0}}
        inventory = {"a": 6}
        completed, _, _ = get_recipe_completion(resources, inventory)
        assert completed == 0


# ---------------------------------------------------------------------------
# parse_resource_updates
# ---------------------------------------------------------------------------

RECIPES_FIXTURE = {
    "recette_test": {
        "orbe_irisé": {"needed": 10, "value": 0},
        "andésite": {"needed": 5, "value": 0},
    }
}


class TestParseResourceUpdates:

    def test_valid_single_update(self):
        updates = parse_resource_updates("orbe_irisé, 5000", RECIPES_FIXTURE)
        assert updates == [("orbe_irisé", 5000)]

    def test_valid_multiple_updates(self):
        updates = parse_resource_updates("orbe_irisé, 100\nandésite, 200", RECIPES_FIXTURE)
        assert updates == [("orbe_irisé", 100), ("andésite", 200)]

    def test_empty_text_raises(self):
        with pytest.raises(ValueError, match="vide"):
            parse_resource_updates("", RECIPES_FIXTURE)

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="vide"):
            parse_resource_updates("   \n  ", RECIPES_FIXTURE)

    def test_missing_comma_raises(self):
        with pytest.raises(ValueError, match="Format incorrect"):
            parse_resource_updates("orbe_irisé 5000", RECIPES_FIXTURE)

    def test_non_integer_value_raises(self):
        with pytest.raises(ValueError, match="invalide"):
            parse_resource_updates("orbe_irisé, abc", RECIPES_FIXTURE)

    def test_float_value_raises(self):
        with pytest.raises(ValueError, match="invalide"):
            parse_resource_updates("orbe_irisé, 1.5", RECIPES_FIXTURE)

    def test_unknown_resource_raises(self):
        with pytest.raises(ValueError, match="introuvable"):
            parse_resource_updates("ressource_inconnue, 1000", RECIPES_FIXTURE)

    def test_zero_value_accepted(self):
        updates = parse_resource_updates("orbe_irisé, 0", RECIPES_FIXTURE)
        assert updates == [("orbe_irisé", 0)]

    def test_blank_lines_skipped(self):
        text = "orbe_irisé, 100\n\nandésite, 200\n"
        updates = parse_resource_updates(text, RECIPES_FIXTURE)
        assert len(updates) == 2

    def test_resource_in_second_recipe(self):
        recipes = {
            "recette_a": {"res_a": {"needed": 1, "value": 0}},
            "recette_b": {"res_b": {"needed": 1, "value": 0}},
        }
        updates = parse_resource_updates("res_b, 999", recipes)
        assert updates == [("res_b", 999)]


# ---------------------------------------------------------------------------
# parse_inventory_updates
# ---------------------------------------------------------------------------

VALID_RESOURCES = {"orbe_irisé", "andésite", "cuir_de_godruche"}


class TestParseInventoryUpdates:

    def test_valid_single_update(self):
        updates = parse_inventory_updates("orbe_irisé, 10", VALID_RESOURCES)
        assert updates == [("orbe_irisé", 10)]

    def test_valid_multiple_updates(self):
        updates = parse_inventory_updates("orbe_irisé, 10\nandésite, 5", VALID_RESOURCES)
        assert updates == [("orbe_irisé", 10), ("andésite", 5)]

    def test_empty_text_raises(self):
        with pytest.raises(ValueError, match="vide"):
            parse_inventory_updates("", VALID_RESOURCES)

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="vide"):
            parse_inventory_updates("  \n  ", VALID_RESOURCES)

    def test_missing_comma_raises(self):
        with pytest.raises(ValueError, match="Format incorrect"):
            parse_inventory_updates("orbe_irisé 10", VALID_RESOURCES)

    def test_non_integer_quantity_raises(self):
        with pytest.raises(ValueError, match="invalide"):
            parse_inventory_updates("orbe_irisé, dix", VALID_RESOURCES)

    def test_unknown_resource_raises(self):
        with pytest.raises(ValueError, match="introuvable"):
            parse_inventory_updates("ressource_inconnue, 5", VALID_RESOURCES)

    def test_zero_quantity_accepted(self):
        updates = parse_inventory_updates("orbe_irisé, 0", VALID_RESOURCES)
        assert updates == [("orbe_irisé", 0)]

    def test_blank_lines_skipped(self):
        text = "orbe_irisé, 10\n\nandésite, 5\n"
        updates = parse_inventory_updates(text, VALID_RESOURCES)
        assert len(updates) == 2

    def test_all_valid_resources(self):
        text = "orbe_irisé, 3\nandésite, 7\ncuir_de_godruche, 1"
        updates = parse_inventory_updates(text, VALID_RESOURCES)
        assert dict(updates) == {"orbe_irisé": 3, "andésite": 7, "cuir_de_godruche": 1}


# ---------------------------------------------------------------------------
# parse_new_recipe
# ---------------------------------------------------------------------------

class TestParseNewRecipe:

    def test_valid_recipe(self):
        result = parse_new_recipe("Ma Recette", "orbe_irisé, 10, 5000\nandésite, 5, 2000")
        assert result == {
            "orbe_irisé": {"needed": 10, "value": 5000},
            "andésite": {"needed": 5, "value": 2000},
        }

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="nom"):
            parse_new_recipe("", "orbe_irisé, 10, 5000")

    def test_whitespace_name_raises(self):
        with pytest.raises(ValueError, match="nom"):
            parse_new_recipe("   ", "orbe_irisé, 10, 5000")

    def test_empty_resources_raises(self):
        with pytest.raises(ValueError, match="ressource"):
            parse_new_recipe("Ma Recette", "")

    def test_whitespace_resources_raises(self):
        with pytest.raises(ValueError, match="ressource"):
            parse_new_recipe("Ma Recette", "   \n  ")

    def test_missing_value_column_raises(self):
        with pytest.raises(ValueError, match="Format incorrect"):
            parse_new_recipe("Ma Recette", "orbe_irisé, 10")

    def test_invalid_numbers_raise(self):
        with pytest.raises(ValueError, match="entiers"):
            parse_new_recipe("Ma Recette", "orbe_irisé, dix, 5000")

    def test_zero_needed_raises(self):
        with pytest.raises(ValueError, match="positive"):
            parse_new_recipe("Ma Recette", "orbe_irisé, 0, 5000")

    def test_negative_needed_raises(self):
        with pytest.raises(ValueError, match="positive"):
            parse_new_recipe("Ma Recette", "orbe_irisé, -1, 5000")

    def test_blank_lines_skipped(self):
        result = parse_new_recipe("Ma Recette", "orbe_irisé, 10, 5000\n\nandésite, 5, 2000\n")
        assert len(result) == 2

    def test_zero_value_accepted(self):
        result = parse_new_recipe("Ma Recette", "docteur, 1, 0")
        assert result == {"docteur": {"needed": 1, "value": 0}}


# ---------------------------------------------------------------------------
# save_data / load_saved_data
# ---------------------------------------------------------------------------

class TestPersistence:

    def test_load_returns_empty_when_file_missing(self, tmp_path):
        filepath = str(tmp_path / "nonexistent.json")
        saved = load_saved_data(filepath=filepath)
        assert saved == {"inventory": {}, "recipe_values": {}, "custom_recipes": {}}

    def test_load_returns_empty_on_corrupted_file(self, tmp_path):
        filepath = str(tmp_path / "save.json")
        with open(filepath, "w") as f:
            f.write("{ invalid json }")
        saved = load_saved_data(filepath=filepath)
        assert saved == {"inventory": {}, "recipe_values": {}, "custom_recipes": {}}

    def test_save_and_load_roundtrip(self, tmp_path):
        filepath = str(tmp_path / "save.json")
        inv = {"orbe_irisé": 51, "andésite": 10}
        recs = {
            "Cape": {"orbe_irisé": {"needed": 63, "value": 32000}},
            "Custom": {"res": {"needed": 5, "value": 1000}},
        }
        custom_names = {"Custom"}

        save_data(inv, recs, custom_names, filepath=filepath)
        saved = load_saved_data(filepath=filepath)

        assert saved["inventory"] == inv
        assert saved["recipe_values"]["Cape"]["orbe_irisé"] == 32000
        assert saved["custom_recipes"]["Custom"]["res"] == {"needed": 5, "value": 1000}
        assert "Custom" not in saved["recipe_values"]

    def test_save_creates_directory_if_needed(self, tmp_path):
        filepath = str(tmp_path / "subdir" / "save.json")
        save_data({"res": 1}, {}, set(), filepath=filepath)
        assert os.path.exists(filepath)

    def test_base_recipes_saved_as_values_only(self, tmp_path):
        filepath = str(tmp_path / "save.json")
        recs = {"Cape": {"orbe_irisé": {"needed": 63, "value": 32000}}}
        save_data({}, recs, set(), filepath=filepath)
        saved = load_saved_data(filepath=filepath)
        # Les recettes de base ne sauvegardent que la valeur kamas, pas "needed"
        assert saved["recipe_values"]["Cape"]["orbe_irisé"] == 32000
        assert "needed" not in saved["recipe_values"]["Cape"]

    def test_inventory_updates_persisted(self, tmp_path):
        filepath = str(tmp_path / "save.json")
        inv = {"orbe_irisé": 0}
        save_data(inv, {}, set(), filepath=filepath)
        inv["orbe_irisé"] = 99
        save_data(inv, {}, set(), filepath=filepath)
        saved = load_saved_data(filepath=filepath)
        assert saved["inventory"]["orbe_irisé"] == 99


# ---------------------------------------------------------------------------
# load_dofus_touch_recipes
# ---------------------------------------------------------------------------

class TestLoadDofusTouchRecipes:

    def test_returns_empty_when_file_missing(self, tmp_path):
        filepath = str(tmp_path / "nonexistent.json")
        result = load_dofus_touch_recipes(filepath=filepath)
        assert result == {}

    def test_returns_empty_on_corrupted_file(self, tmp_path):
        filepath = str(tmp_path / "recipes.json")
        with open(filepath, "w") as f:
            f.write("not valid json {{{")
        result = load_dofus_touch_recipes(filepath=filepath)
        assert result == {}

    def test_returns_empty_on_non_dict_content(self, tmp_path):
        filepath = str(tmp_path / "recipes.json")
        with open(filepath, "w", encoding="utf-8") as f:
            import json
            json.dump([1, 2, 3], f)
        result = load_dofus_touch_recipes(filepath=filepath)
        assert result == {}

    def test_loads_valid_recipes(self, tmp_path):
        filepath = str(tmp_path / "recipes.json")
        data = {
            "Épée du Granduk": {
                "Ventouse du Kralamoure géant": {"needed": 8, "value": 0},
                "Bave de Boufton Blanc": {"needed": 4, "value": 0},
            },
            "Potion de soin": {
                "Eau": {"needed": 1, "value": 0},
            },
        }
        with open(filepath, "w", encoding="utf-8") as f:
            import json
            json.dump(data, f, ensure_ascii=False)
        result = load_dofus_touch_recipes(filepath=filepath)
        assert len(result) == 2
        assert result["Épée du Granduk"]["Ventouse du Kralamoure géant"]["needed"] == 8
        assert result["Potion de soin"]["Eau"]["value"] == 0

    def test_value_defaults_to_zero_in_loaded_recipes(self, tmp_path):
        filepath = str(tmp_path / "recipes.json")
        data = {"Recette Test": {"res_a": {"needed": 5, "value": 0}}}
        with open(filepath, "w", encoding="utf-8") as f:
            import json
            json.dump(data, f)
        result = load_dofus_touch_recipes(filepath=filepath)
        assert result["Recette Test"]["res_a"]["value"] == 0


# ---------------------------------------------------------------------------
# scripts/import_dofus_touch_data — conversion locale (sans réseau)
# ---------------------------------------------------------------------------

class TestImportConversion:
    """Tests unitaires de la logique de conversion crawlit → format projet."""

    def setup_method(self):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from scripts.import_dofus_touch_data import _convert_item
        self._convert = _convert_item

    def test_item_with_recipe(self):
        item = {
            "name": "Épée Test",
            "recipe": [
                {"Ventouse du Kralamoure géant": {"quantity": "8", "type": "Ressources"}},
                {"Bave de Boufton": {"quantity": "4", "type": "Ressources"}},
            ],
        }
        result = self._convert(item)
        assert result is not None
        assert result["Ventouse du Kralamoure géant"]["needed"] == 8
        assert result["Ventouse du Kralamoure géant"]["value"] == 0
        assert result["Bave de Boufton"]["needed"] == 4
        assert result["Bave de Boufton"]["value"] == 0

    def test_item_without_recipe_returns_none(self):
        item = {"name": "Objet sans recette", "recipe": []}
        assert self._convert(item) is None

    def test_item_missing_recipe_key_returns_none(self):
        item = {"name": "Objet sans clé recipe"}
        assert self._convert(item) is None

    def test_invalid_quantity_skipped(self):
        item = {
            "name": "Épée Test",
            "recipe": [
                {"Res valide": {"quantity": "5", "type": "X"}},
                {"Res invalide": {"quantity": "pas_un_nombre", "type": "X"}},
            ],
        }
        result = self._convert(item)
        assert result is not None
        assert "Res valide" in result
        assert "Res invalide" not in result

    def test_all_invalid_quantities_returns_none(self):
        item = {
            "name": "Épée Test",
            "recipe": [{"Res": {"quantity": "invalide"}}],
        }
        assert self._convert(item) is None

    def test_value_always_zero(self):
        item = {
            "name": "Épée Test",
            "recipe": [{"Res": {"quantity": "10"}}],
        }
        result = self._convert(item)
        assert result["Res"]["value"] == 0

    def test_run_saves_to_file(self, tmp_path):
        """Test de run() avec un mock réseau — vérifie uniquement l'écriture du fichier."""
        from unittest.mock import patch, MagicMock
        import json as json_mod
        from scripts.import_dofus_touch_data import run

        fake_items = [
            {
                "name": "Chapeau Test",
                "recipe": [{"Res A": {"quantity": "3"}}],
            },
            {
                "name": "Chapeau sans recette",
                "recipe": [],
            },
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = fake_items
        mock_response.raise_for_status.return_value = None

        output = str(tmp_path / "out.json")
        with patch("scripts.import_dofus_touch_data.OUTPUT_FILE", output):
            with patch("scripts.import_dofus_touch_data.requests.get", return_value=mock_response):
                result = run()

        assert "Chapeau Test" in result
        assert "Chapeau sans recette" not in result
        assert os.path.exists(output)
        with open(output, encoding="utf-8") as f:
            saved = json_mod.load(f)
        assert "Chapeau Test" in saved

    def test_id_stored_in_resource(self):
        """Vérifie que l'id est stocké dans chaque ressource après modification."""
        from scripts.import_dofus_touch_data import _convert_item
        item = {
            "name": "Épée Test",
            "recipe": [
                {"Res A": {"quantity": "5", "id": 42}},
            ],
        }
        result = _convert_item(item)
        assert result is not None
        assert result["Res A"]["id"] == "42"

    def test_id_defaults_to_empty_string_if_missing(self):
        """Vérifie que l'id vaut '' si absent."""
        from scripts.import_dofus_touch_data import _convert_item
        item = {
            "name": "Épée Test",
            "recipe": [{"Res A": {"quantity": "5"}}],
        }
        result = _convert_item(item)
        assert result["Res A"]["id"] == ""


# ---------------------------------------------------------------------------
# calculate_profitability
# ---------------------------------------------------------------------------

class TestCalculateProfitability:

    def test_profitable_craft(self):
        result = calculate_profitability(100_000, 150_000)
        assert result["profit"] == 50_000
        assert result["is_profitable"] is True
        assert result["margin_pct"] == 50.0

    def test_losing_craft(self):
        result = calculate_profitability(200_000, 150_000)
        assert result["profit"] == -50_000
        assert result["is_profitable"] is False
        assert result["margin_pct"] < 0

    def test_break_even(self):
        result = calculate_profitability(100_000, 100_000)
        assert result["profit"] == 0
        assert result["is_profitable"] is False
        assert result["margin_pct"] == 0.0

    def test_zero_craft_cost_no_division(self):
        result = calculate_profitability(0, 50_000)
        assert result["profit"] == 50_000
        assert result["margin_pct"] == 0.0

    def test_margin_rounding(self):
        result = calculate_profitability(3, 4)
        assert result["margin_pct"] == round(100 / 3, 1)


# ---------------------------------------------------------------------------
# load_sell_prices / save_sell_prices
# ---------------------------------------------------------------------------

class TestSellPricesPersistence:

    def test_returns_empty_when_file_missing(self, tmp_path):
        filepath = str(tmp_path / "nonexistent.json")
        result = load_sell_prices(filepath=filepath)
        assert result == {}

    def test_returns_empty_on_corrupted_file(self, tmp_path):
        filepath = str(tmp_path / "prices.json")
        with open(filepath, "w") as f:
            f.write("{{invalid}}")
        result = load_sell_prices(filepath=filepath)
        assert result == {}

    def test_roundtrip(self, tmp_path):
        filepath = str(tmp_path / "prices.json")
        prices = {"Cape Cérémoniale": 500_000, "Sandales": 120_000}
        save_sell_prices(prices, filepath=filepath)
        loaded = load_sell_prices(filepath=filepath)
        assert loaded == prices

    def test_creates_directory(self, tmp_path):
        filepath = str(tmp_path / "sub" / "prices.json")
        save_sell_prices({"r": 1}, filepath=filepath)
        assert os.path.exists(filepath)


# ---------------------------------------------------------------------------
# aggregate_shopping_list
# ---------------------------------------------------------------------------

class TestAggregateShoppingList:

    RECIPES = {
        "Cape": {
            "orbe_irisé": {"needed": 10, "value": 1000},
            "andésite": {"needed": 5, "value": 500},
        },
        "Sandales": {
            "orbe_irisé": {"needed": 3, "value": 1000},
            "bois": {"needed": 8, "value": 200},
        },
    }

    def test_single_recipe_no_inventory(self):
        items = aggregate_shopping_list(["Cape"], self.RECIPES, {})
        assert any(i["resource"] == "orbe_irisé" and i["needed"] == 10 for i in items)

    def test_two_recipes_aggregates_shared_resource(self):
        items = aggregate_shopping_list(["Cape", "Sandales"], self.RECIPES, {})
        orbe = next(i for i in items if i["resource"] == "orbe_irisé")
        assert orbe["needed"] == 13

    def test_inventory_reduces_missing(self):
        inv = {"orbe_irisé": 5}
        items = aggregate_shopping_list(["Cape"], self.RECIPES, inv)
        orbe = next(i for i in items if i["resource"] == "orbe_irisé")
        assert orbe["missing"] == 5
        assert orbe["acquired"] == 5

    def test_fully_stocked_resource_has_zero_missing(self):
        inv = {"orbe_irisé": 20}
        items = aggregate_shopping_list(["Cape"], self.RECIPES, inv)
        orbe = next(i for i in items if i["resource"] == "orbe_irisé")
        assert orbe["missing"] == 0

    def test_sorted_by_missing_descending(self):
        inv = {"orbe_irisé": 9}  # manque 1 orbe, manque 5 andésite
        items = aggregate_shopping_list(["Cape"], self.RECIPES, inv)
        missings = [i["missing"] for i in items]
        assert missings == sorted(missings, reverse=True)

    def test_empty_selection_returns_empty(self):
        items = aggregate_shopping_list([], self.RECIPES, {})
        assert items == []

    def test_unknown_recipe_name_skipped(self):
        items = aggregate_shopping_list(["Recette Inconnue"], self.RECIPES, {})
        assert items == []

    def test_total_cost_computed(self):
        items = aggregate_shopping_list(["Cape"], self.RECIPES, {})
        orbe = next(i for i in items if i["resource"] == "orbe_irisé")
        assert orbe["total_cost"] == orbe["missing"] * orbe["unit_value"]


# ---------------------------------------------------------------------------
# record_snapshot / load_history
# ---------------------------------------------------------------------------

class TestHistory:

    def test_load_returns_empty_when_missing(self, tmp_path):
        filepath = str(tmp_path / "history.json")
        result = load_history(filepath=filepath)
        assert result == {}

    def test_load_returns_empty_on_corrupted_file(self, tmp_path):
        filepath = str(tmp_path / "history.json")
        with open(filepath, "w") as f:
            f.write("{bad}")
        result = load_history(filepath=filepath)
        assert result == {}

    def test_record_creates_entry(self, tmp_path):
        filepath = str(tmp_path / "history.json")
        record_snapshot("Cape", 5, 10, 50_000, filepath=filepath)
        history = load_history(filepath=filepath)
        assert "Cape" in history
        assert len(history["Cape"]) == 1
        entry = history["Cape"][0]
        assert entry["completed"] == 5
        assert entry["total"] == 10
        assert entry["pct"] == 50
        assert entry["kamas_manquant"] == 50_000

    def test_multiple_snapshots_accumulated(self, tmp_path):
        filepath = str(tmp_path / "history.json")
        record_snapshot("Cape", 3, 10, 70_000, filepath=filepath)
        record_snapshot("Cape", 7, 10, 30_000, filepath=filepath)
        history = load_history(filepath=filepath)
        assert len(history["Cape"]) == 2

    def test_capped_at_100_entries(self, tmp_path):
        filepath = str(tmp_path / "history.json")
        for i in range(110):
            record_snapshot("Cape", i % 11, 10, 1000, filepath=filepath)
        history = load_history(filepath=filepath)
        assert len(history["Cape"]) == 100

    def test_multiple_recipes_tracked_independently(self, tmp_path):
        filepath = str(tmp_path / "history.json")
        record_snapshot("Cape", 5, 10, 50_000, filepath=filepath)
        record_snapshot("Sandales", 2, 6, 20_000, filepath=filepath)
        history = load_history(filepath=filepath)
        assert "Cape" in history
        assert "Sandales" in history
        assert len(history["Cape"]) == 1
        assert len(history["Sandales"]) == 1

    def test_pct_zero_when_nothing_done(self, tmp_path):
        filepath = str(tmp_path / "history.json")
        record_snapshot("Cape", 0, 10, 100_000, filepath=filepath)
        entry = load_history(filepath=filepath)["Cape"][0]
        assert entry["pct"] == 0

    def test_pct_100_when_complete(self, tmp_path):
        filepath = str(tmp_path / "history.json")
        record_snapshot("Cape", 10, 10, 0, filepath=filepath)
        entry = load_history(filepath=filepath)["Cape"][0]
        assert entry["pct"] == 100
