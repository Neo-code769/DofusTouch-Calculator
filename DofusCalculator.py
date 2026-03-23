'''
    DOFUS 1.5 / Touch — Version 2.0
    Calculateur de ressources manquantes pour les crafts.
    Gestion de l'inventaire, des recettes personnalisées et des valeurs en kamas.
    Sauvegarde automatique des données en local (data/save.json).
'''

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
from Recettes import recipes
from Inventory import inventory
from calculator_logic import (
    calculate_missing_resources,
    get_recipe_completion,
    parse_resource_updates,
    parse_inventory_updates,
    parse_new_recipe,
    load_saved_data,
    save_data,
)

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# Noms des recettes ajoutées par l'utilisateur (non incluses dans Recettes.py)
custom_recipe_names = set()


def _apply_saved_data():
    """Applique les données sauvegardées (inventaire, valeurs, recettes custom) au démarrage."""
    saved = load_saved_data()

    for resource, qty in saved["inventory"].items():
        inventory[resource] = qty

    for recipe_name, values in saved["recipe_values"].items():
        if recipe_name in recipes:
            for resource, value in values.items():
                if resource in recipes[recipe_name]:
                    recipes[recipe_name][resource]["value"] = value

    for recipe_name, resources_data in saved["custom_recipes"].items():
        recipes[recipe_name] = resources_data
        custom_recipe_names.add(recipe_name)


def _completion_bar(pct):
    """Retourne une barre de progression textuelle pour un pourcentage donné."""
    filled = pct // 10
    return "█" * filled + "░" * (10 - filled)


def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


# ---------------------------------------------------------------------------
# Fenêtre de résultats
# ---------------------------------------------------------------------------

def show_results(recipe_name, table_text, kamas_manquant, resources=None):
    result_window = tk.Toplevel()
    result_window.title(f"Résultats — {recipe_name}")
    result_window.geometry("700x580")
    result_window.resizable(True, True)
    center_window(result_window)

    frame = ttk.Frame(result_window, padding=10)
    frame.pack(fill="both", expand=True)

    text_widget = tk.Text(frame, wrap="none", width=100, height=20, font=("Courier", 10))
    text_widget.insert("1.0", table_text)
    text_widget.config(state="disabled")

    sy = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
    sx = ttk.Scrollbar(frame, orient="horizontal", command=text_widget.xview)
    text_widget.config(yscrollcommand=sy.set, xscrollcommand=sx.set)

    text_widget.grid(row=0, column=0, sticky="nsew")
    sy.grid(row=0, column=1, sticky="ns")
    sx.grid(row=1, column=0, sticky="ew")

    # Barre de complétion
    if resources is not None:
        completed, total, pct = get_recipe_completion(resources, inventory)
        bar = _completion_bar(pct)
        ttk.Label(
            frame,
            text=f"Complétion : {bar} {pct}%  ({completed} / {total} ressources complètes)",
            font=("Courier", 11),
        ).grid(row=2, column=0, columnspan=2, pady=5)

    kamas_str = f"{kamas_manquant:,}".replace(",", " ")
    ttk.Label(frame, text=f"Il me manque : {kamas_str} kamas", font=("Arial", 12, "bold")).grid(
        row=3, column=0, columnspan=2, pady=5
    )
    ttk.Button(frame, text="Fermer", command=result_window.destroy, bootstyle="danger").grid(
        row=4, column=0, columnspan=2, pady=10
    )

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)


# ---------------------------------------------------------------------------
# Mise à jour des valeurs des ressources
# ---------------------------------------------------------------------------

def update_resource_values():
    def save_updates():
        try:
            text = text_widget.get("1.0", "end").strip()
            updates = parse_resource_updates(text, recipes)
            for resource_name, new_value in updates:
                for recipe in recipes.values():
                    if resource_name in recipe:
                        recipe[resource_name]["value"] = new_value
            save_data(inventory, recipes, custom_recipe_names)
            messagebox.showinfo("Succès", "Valeurs mises à jour et sauvegardées.")
            win.destroy()
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))

    win = tk.Toplevel()
    win.title("Mettre à jour les valeurs des ressources")
    win.geometry("800x600")
    win.resizable(True, True)
    center_window(win)

    frame = ttk.Frame(win, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Format : nom_ressource, valeur_kamas", font=("Arial", 12, "bold")).pack(pady=10)

    text_widget = tk.Text(frame, wrap="none", width=70, height=20, font=("Courier", 10))

    # Pré-remplir avec les valeurs actuelles (dédupliquées)
    unique = {}
    for recipe_resources in recipes.values():
        for rname, data in recipe_resources.items():
            if rname not in unique:
                unique[rname] = data["value"]
    text_widget.insert("1.0", "\n".join(f"{r}, {v}" for r, v in sorted(unique.items())))
    text_widget.pack(side="left", fill="both", expand=True, padx=5, pady=5)

    sy = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
    sx = ttk.Scrollbar(frame, orient="horizontal", command=text_widget.xview)
    text_widget.config(yscrollcommand=sy.set, xscrollcommand=sx.set)
    sy.pack(side="right", fill="y")
    sx.pack(side="bottom", fill="x")

    ttk.Button(frame, text="Sauvegarder", command=save_updates, bootstyle="success").pack(pady=10)
    ttk.Button(frame, text="Fermer", command=win.destroy, bootstyle="danger").pack(pady=5)


# ---------------------------------------------------------------------------
# Gestion de l'inventaire
# ---------------------------------------------------------------------------

def manage_inventory():
    def save_inventory():
        try:
            text = text_widget.get("1.0", "end").strip()
            updates = parse_inventory_updates(text, set(inventory.keys()))
            for resource_name, quantity in updates:
                inventory[resource_name] = quantity
            save_data(inventory, recipes, custom_recipe_names)
            messagebox.showinfo("Succès", "Inventaire mis à jour et sauvegardé.")
            win.destroy()
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))

    win = tk.Toplevel()
    win.title("Gérer l'inventaire")
    win.geometry("600x500")
    win.resizable(True, True)
    center_window(win)

    frame = ttk.Frame(win, padding=10)
    frame.pack(fill="both", expand=True)

    text_widget = tk.Text(frame, wrap="none", width=50, height=20, font=("Arial", 12))
    text_widget.insert("1.0", "\n".join(f"{r}, {q}" for r, q in inventory.items()))

    sy = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
    sx = ttk.Scrollbar(frame, orient="horizontal", command=text_widget.xview)
    text_widget.config(yscrollcommand=sy.set, xscrollcommand=sx.set)

    text_widget.grid(row=0, column=0, sticky="nsew")
    sy.grid(row=0, column=1, sticky="ns")
    sx.grid(row=1, column=0, sticky="ew")

    ttk.Button(frame, text="Sauvegarder", command=save_inventory, bootstyle="success").grid(
        row=2, column=0, columnspan=2, pady=10
    )

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)


# ---------------------------------------------------------------------------
# Calcul de toutes les recettes
# ---------------------------------------------------------------------------

def calculate_all_recipes():
    all_results = ""
    total_kamas = 0

    for recipe_name, resources in recipes.items():
        table_text, kamas_manquant = calculate_missing_resources(resources, inventory)
        completed, total, pct = get_recipe_completion(resources, inventory)
        bar = _completion_bar(pct)
        kamas_str = f"{kamas_manquant:,}".replace(",", " ")
        all_results += (
            f"=== {recipe_name} ===\n"
            f"Complétion : {bar} {pct}% ({completed}/{total} ressources)\n"
            f"{table_text}\n"
            f"Il me manque : {kamas_str} kamas\n\n"
        )
        total_kamas += kamas_manquant

    win = tk.Toplevel()
    win.title("Récapitulatif de toutes les recettes")
    win.geometry("900x700")
    center_window(win)

    frame = ttk.Frame(win, padding=10)
    frame.pack(fill="both", expand=True)

    text_widget = tk.Text(frame, wrap="none", width=120, height=30, font=("Courier", 10))
    text_widget.insert("1.0", all_results)
    text_widget.config(state="disabled")

    sy = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
    sx = ttk.Scrollbar(frame, orient="horizontal", command=text_widget.xview)
    text_widget.config(yscrollcommand=sy.set, xscrollcommand=sx.set)

    text_widget.grid(row=0, column=0, sticky="nsew")
    sy.grid(row=0, column=1, sticky="ns")
    sx.grid(row=1, column=0, sticky="ew")

    total_kamas_str = f"{total_kamas:,}".replace(",", " ")
    ttk.Label(
        frame,
        text=f"Coût total manquant : {total_kamas_str} kamas",
        font=("Arial", 12, "bold"),
    ).grid(row=2, column=0, columnspan=2, pady=10)
    ttk.Button(frame, text="Fermer", command=win.destroy, bootstyle="danger").grid(
        row=3, column=0, columnspan=2, pady=10
    )

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)


# ---------------------------------------------------------------------------
# Interface principale
# ---------------------------------------------------------------------------

def main_gui():
    _apply_saved_data()

    def on_calculate():
        idx = recipe_combobox.current()
        if idx == -1 or recipe_combobox.get() == "Veuillez sélectionner une recette":
            messagebox.showerror("Erreur", "Veuillez sélectionner une recette.")
            return
        recipe_name = recipe_names[idx]
        resources = recipes[recipe_name]
        table_text, kamas_manquant = calculate_missing_resources(resources, inventory)
        show_results(recipe_name, table_text, kamas_manquant, resources=resources)

    def on_add_recipe():
        """Fenêtre pour créer une recette personnalisée."""
        def save_new_recipe():
            try:
                name = name_entry.get().strip()
                text = resources_text.get("1.0", "end").strip()
                new_resources = parse_new_recipe(name, text)
                if name in recipes:
                    messagebox.showerror("Erreur", f"Une recette '{name}' existe déjà.")
                    return
                recipes[name] = new_resources
                custom_recipe_names.add(name)
                recipe_names.append(name)
                recipe_combobox["values"] = recipe_names
                save_data(inventory, recipes, custom_recipe_names)
                messagebox.showinfo("Succès", f"Recette '{name}' ajoutée et sauvegardée.")
                win.destroy()
            except ValueError as e:
                messagebox.showerror("Erreur", str(e))

        win = tk.Toplevel()
        win.title("Ajouter une recette")
        win.geometry("700x550")
        win.resizable(True, True)
        center_window(win)

        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Nom de la recette :", font=("Arial", 12, "bold")).pack(pady=(10, 2))
        name_entry = ttk.Entry(frame, width=60, font=("Arial", 12))
        name_entry.pack(pady=(0, 10))

        ttk.Label(
            frame,
            text="Ressources (format : nom_ressource, quantité, valeur_kamas) :",
            font=("Arial", 12, "bold"),
        ).pack(pady=(0, 2))

        resources_text = tk.Text(frame, wrap="none", width=70, height=17, font=("Courier", 10))
        resources_text.insert("1.0", "nom_ressource, 10, 5000\n")
        resources_text.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(frame, text="Ajouter la recette", command=save_new_recipe, bootstyle="success").pack(pady=10)
        ttk.Button(frame, text="Fermer", command=win.destroy, bootstyle="danger").pack(pady=5)

    # ---- Fenêtre principale ----
    root = ttk.Window(themename="darkly")
    root.title("Dofus Touch Calculator v2.0")
    root.geometry("1100x800")
    root.resizable(False, False)

    # Image de fond (optionnelle — ignore les erreurs réseau)
    try:
        image_url = "https://github.com/Neo-code769/DofusTouch-Calculator/blob/main/DofusTouchCalculator-background.png?raw=true"
        response = requests.get(image_url, stream=True, timeout=5)
        response.raw.decode_content = True
        bg = Image.open(response.raw).resize((1100, 800))
        bg_photo = ImageTk.PhotoImage(bg)
        root.bg_photo = bg_photo
        ttk.Label(root, image=bg_photo, borderwidth=0).place(x=0, y=0, relwidth=1, relheight=1)
    except Exception:
        pass

    # Styles
    style = ttk.Style()
    style.configure("BrownFrame.TFrame", background="#8B4513", borderwidth=3, relief="solid")
    style.configure(
        "Brown.TCombobox",
        fieldbackground="#8B4513", background="#8B4513", foreground="white",
        borderwidth=0, relief="flat", font=("Segoe UI", 16),
    )
    style.map(
        "Brown.TCombobox",
        fieldbackground=[("readonly", "#8B4513"), ("active", "#A0522D")],
        foreground=[("readonly", "white"), ("active", "white")],
    )
    style.configure(
        "Brown.TButton",
        background="#8B4513", foreground="white",
        borderwidth=0, focusthickness=0, font=("Segoe UI", 12), relief="flat",
    )
    style.map(
        "Brown.TButton",
        background=[("active", "#A0522D"), ("pressed", "#5C3317")],
        foreground=[("active", "white"), ("pressed", "white")],
    )

    # Menu déroulant des recettes
    recipe_names = list(recipes.keys())
    ttk.Frame(root, style="BrownFrame.TFrame", padding=5).place(relx=0.5, rely=0.45, anchor="center")
    recipe_combobox = ttk.Combobox(
        root, values=recipe_names, state="readonly",
        width=75, font=("Segoe UI", 16), style="Brown.TCombobox",
    )
    recipe_combobox.set("Veuillez sélectionner une recette")
    recipe_combobox.place(relx=0.5, rely=0.5, anchor="center")

    # Boutons d'action
    button_frame = ttk.Frame(root, style="BrownFrame.TFrame", padding=5)
    button_frame.place(relx=0.5, rely=0.63, anchor="center", width=1050)

    buttons = [
        ("Gérer l'inventaire",          manage_inventory,        0),
        ("Calculer",                     on_calculate,            1),
        ("Ajouter une recette",          on_add_recipe,           2),
        ("Mettre à jour les valeurs",    update_resource_values,  3),
        ("Calculer toutes les recettes", calculate_all_recipes,   4),
    ]
    for label, cmd, col in buttons:
        ttk.Button(button_frame, text=label, command=cmd, width=20, style="Brown.TButton").grid(
            row=0, column=col, padx=8
        )

    root.mainloop()


if __name__ == "__main__":
    main_gui()
