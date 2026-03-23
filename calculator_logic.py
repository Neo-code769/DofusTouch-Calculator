"""
Logique métier pure du calculateur Dofus Touch.
Ce module ne contient aucune dépendance GUI et peut être testé indépendamment.
"""

from tabulate import tabulate


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
            max(0, lack),  # Afficher 0 si on a un surplus, pas une valeur négative
            f"{data['value']:,}".replace(",", " "),
        ])

    table_text = tabulate(
        table,
        headers=["Ressource", "Requis", "Acquis", "Manquant", "Valeur unitaire"],
        tablefmt="grid"
    )
    return table_text, kamas_manquant


def parse_resource_updates(text, recipes):
    """Parse le texte de mise à jour des ressources (format: nom, valeur).

    Args:
        text: str avec une entrée "nom, valeur" par ligne
        recipes: dict des recettes pour valider les noms de ressources

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
    """Parse le texte de mise à jour de l'inventaire (format: nom, quantité).

    Args:
        text: str avec une entrée "nom, quantité" par ligne
        valid_resources: collection des noms de ressources valides

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
