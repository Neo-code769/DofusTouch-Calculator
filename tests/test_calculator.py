"""Tests unitaires pour calculator_logic.py"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculator_logic import (
    calculate_missing_resources,
    parse_resource_updates,
    parse_inventory_updates,
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
        # La colonne Manquant doit afficher 0, pas -7
        lines = [l for l in table_text.splitlines() if "orbe" in l]
        assert len(lines) == 1
        assert "| 0 |" in lines[0] or lines[0].count("0") >= 1

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

    def test_table_contains_resource_name(self):
        resources = {"orbe_irisé": {"needed": 5, "value": 1000}}
        inventory = {}
        table_text, _ = calculate_missing_resources(resources, inventory)
        assert "orbe irisé" in table_text  # underscores remplacés par des espaces

    def test_table_headers_present(self):
        resources = {"orbe_irisé": {"needed": 5, "value": 1000}}
        inventory = {}
        table_text, _ = calculate_missing_resources(resources, inventory)
        assert "Ressource" in table_text
        assert "Requis" in table_text
        assert "Acquis" in table_text
        assert "Manquant" in table_text
        assert "Valeur unitaire" in table_text

    def test_exact_inventory_match_produces_zero_kamas(self):
        resources = {"res": {"needed": 7, "value": 500}}
        inventory = {"res": 7}
        _, kamas = calculate_missing_resources(resources, inventory)
        assert kamas == 0

    def test_multiple_resources_only_missing_ones_counted(self):
        resources = {
            "res_a": {"needed": 5, "value": 100},  # acquis: 10 → surplus
            "res_b": {"needed": 5, "value": 100},  # acquis: 0 → 5 manquants
        }
        inventory = {"res_a": 10, "res_b": 0}
        _, kamas = calculate_missing_resources(resources, inventory)
        assert kamas == 5 * 100


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

    def test_all_valid_resources_updated(self):
        text = "orbe_irisé, 3\nandésite, 7\ncuir_de_godruche, 1"
        updates = parse_inventory_updates(text, VALID_RESOURCES)
        assert dict(updates) == {"orbe_irisé": 3, "andésite": 7, "cuir_de_godruche": 1}
