'''
    DOFUS 1.5 / Touch Upgrade
    Script pour calculer les ressources manquantes, ajouter des recettes, gérer l'inventaire, mettre à jour les valeurs des ressources.
'''

import tkinter as tk    # Pour l'interface graphique
from tkinter import messagebox  # Pour les boîtes de dialogue et messages d'erreur
from PIL import Image, ImageTk  # Pour gérer l'image de fond
import requests  # Pour télécharger l'image depuis l'URL
from Recettes import recipes
from Inventory import inventory
from calculator_logic import (
    calculate_missing_resources,
    parse_resource_updates,
    parse_inventory_updates,
)

import ttkbootstrap as ttk  # Pour le thème moderne de l'interface graphique
from ttkbootstrap.constants import *  # Pour les styles de boutons et autres constantes


# Fonction pour afficher les résultats dans une fenêtre
def show_results(recipe_name, table_text, kamas_manquant):
    result_window = tk.Toplevel()
    result_window.title(f"Résultats pour {recipe_name}")
    result_window.geometry("700x500")
    result_window.resizable(True, True)

    center_window(result_window)

    result_frame = ttk.Frame(result_window, padding=10)
    result_frame.pack(fill="both", expand=True)

    text_widget = tk.Text(result_frame, wrap="none", width=100, height=20, font=("Courier", 10))
    text_widget.insert("1.0", table_text)
    text_widget.config(state="disabled")

    scrollbar_y = ttk.Scrollbar(result_frame, orient="vertical", command=text_widget.yview)
    scrollbar_x = ttk.Scrollbar(result_frame, orient="horizontal", command=text_widget.xview)
    text_widget.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

    text_widget.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")

    kamas_str = f"{kamas_manquant:,}".replace(",", " ")
    total_label = ttk.Label(result_frame, text=f"Il me manque : {kamas_str} kamas", font=("Arial", 12, "bold"))
    total_label.grid(row=2, column=0, columnspan=2, pady=10)

    close_button = ttk.Button(result_frame, text="Fermer", command=result_window.destroy, bootstyle="danger")
    close_button.grid(row=3, column=0, columnspan=2, pady=10)

    result_frame.rowconfigure(0, weight=1)
    result_frame.columnconfigure(0, weight=1)


# Fonction pour centrer une fenêtre
def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


# Fonction pour mettre à jour les valeurs des ressources
def update_resource_values():
    def save_updates():
        try:
            text = updates_text_widget.get("1.0", "end").strip()
            updates = parse_resource_updates(text, recipes)
            for resource_name, new_value in updates:
                for recipe in recipes.values():
                    if resource_name in recipe:
                        recipe[resource_name]["value"] = new_value
            messagebox.showinfo("Succès", "Les valeurs des ressources ont été mises à jour.")
            update_window.destroy()
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))

    update_window = tk.Toplevel()
    update_window.title("Mettre à jour les valeurs des ressources")
    update_window.geometry("800x600")
    update_window.resizable(True, True)

    center_window(update_window)

    update_frame = ttk.Frame(update_window, padding=10)
    update_frame.pack(fill="both", expand=True)

    instructions_label = ttk.Label(
        update_frame,
        text="Mises à jour (format : nom, nouvelle valeur) :",
        font=("Arial", 12, "bold"),
        anchor="center"
    )
    instructions_label.pack(pady=10)

    updates_text_widget = tk.Text(update_frame, wrap="none", width=70, height=20, font=("Courier", 10))
    updates_text_widget.pack(side="left", fill="both", expand=True, padx=5, pady=5)

    # Pré-remplir avec les ressources existantes
    existing_resources = set()
    for recipe in recipes.values():
        existing_resources.update(recipe.keys())
    updates_text_widget.insert("1.0", "\n".join([f"{r}, 0" for r in sorted(existing_resources)]))

    scrollbar_y = ttk.Scrollbar(update_frame, orient="vertical", command=updates_text_widget.yview)
    scrollbar_x = ttk.Scrollbar(update_frame, orient="horizontal", command=updates_text_widget.xview)
    updates_text_widget.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

    scrollbar_y.pack(side="right", fill="y")
    scrollbar_x.pack(side="bottom", fill="x")

    save_button = ttk.Button(update_frame, text="Sauvegarder", command=save_updates, bootstyle="success")
    save_button.pack(pady=10)

    close_button = ttk.Button(update_frame, text="Fermer", command=update_window.destroy, bootstyle="danger")
    close_button.pack(pady=5)


# Fonction pour gérer l'inventaire
def manage_inventory():
    def save_inventory():
        try:
            text = inventory_text_widget.get("1.0", "end").strip()
            updates = parse_inventory_updates(text, set(inventory.keys()))
            for resource_name, quantity in updates:
                inventory[resource_name] = quantity
            messagebox.showinfo("Succès", "L'inventaire a été mis à jour.")
            inventory_window.destroy()
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))

    inventory_window = tk.Toplevel()
    inventory_window.title("Gérer l'inventaire")
    inventory_window.geometry("600x500")
    inventory_window.resizable(True, True)

    center_window(inventory_window)

    inventory_frame = ttk.Frame(inventory_window, padding=10)
    inventory_frame.pack(fill="both", expand=True)

    inventory_text_widget = tk.Text(inventory_frame, wrap="none", width=50, height=20, font=("Arial", 12))
    inventory_text_widget.insert("1.0", "\n".join([f"{r}, {q}" for r, q in inventory.items()]))

    scrollbar_y = ttk.Scrollbar(inventory_frame, orient="vertical", command=inventory_text_widget.yview)
    scrollbar_x = ttk.Scrollbar(inventory_frame, orient="horizontal", command=inventory_text_widget.xview)
    inventory_text_widget.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

    inventory_text_widget.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")

    save_button = ttk.Button(inventory_frame, text="Sauvegarder", command=save_inventory, bootstyle="success")
    save_button.grid(row=2, column=0, columnspan=2, pady=10)

    inventory_frame.rowconfigure(0, weight=1)
    inventory_frame.columnconfigure(0, weight=1)


# Fonction pour calculer toutes les recettes
def calculate_all_recipes():
    all_results = ""
    total_kamas = 0
    for recipe_name, resources in recipes.items():
        table_text, kamas_manquant = calculate_missing_resources(resources, inventory)
        kamas_str = f"{kamas_manquant:,}".replace(",", " ")
        all_results += f"=== {recipe_name} ===\n{table_text}\nIl me manque : {kamas_str} kamas\n\n"
        total_kamas += kamas_manquant

    result_window = tk.Toplevel()
    result_window.title("Récapitulatif de toutes les recettes")
    result_window.geometry("900x700")
    center_window(result_window)

    result_frame = ttk.Frame(result_window, padding=10)
    result_frame.pack(fill="both", expand=True)

    text_widget = tk.Text(result_frame, wrap="none", width=120, height=30, font=("Courier", 10))
    text_widget.insert("1.0", all_results)
    text_widget.config(state="disabled")

    scrollbar_y = ttk.Scrollbar(result_frame, orient="vertical", command=text_widget.yview)
    scrollbar_x = ttk.Scrollbar(result_frame, orient="horizontal", command=text_widget.xview)
    text_widget.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

    text_widget.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")

    total_kamas_str = f"{total_kamas:,}".replace(",", " ")
    total_label = ttk.Label(
        result_frame,
        text=f"Coût total manquant pour toutes les recettes : {total_kamas_str} kamas",
        font=("Arial", 12, "bold")
    )
    total_label.grid(row=2, column=0, columnspan=2, pady=10)

    close_button = ttk.Button(result_frame, text="Fermer", command=result_window.destroy, bootstyle="danger")
    close_button.grid(row=3, column=0, columnspan=2, pady=10)

    result_frame.rowconfigure(0, weight=1)
    result_frame.columnconfigure(0, weight=1)


# Fonction principale pour l'interface graphique
def main_gui():
    def on_calculate():
        selected_recipe_index = recipe_combobox.current()
        if selected_recipe_index == -1 or recipe_combobox.get() == "Veuillez sélectionner une recette":
            messagebox.showerror("Erreur", "Veuillez sélectionner une recette.")
            return
        recipe_name = recipe_names[selected_recipe_index]
        resources = recipes[recipe_name]
        table_text, kamas_manquant = calculate_missing_resources(resources, inventory)
        show_results(recipe_name, table_text, kamas_manquant)

    root = ttk.Window(themename="darkly")
    root.title("Dofus Touch Calculator")
    root.geometry("1100x800")
    root.resizable(False, False)

    # Télécharger et charger l'image de fond (avec gestion d'erreur réseau)
    try:
        image_url = "https://github.com/Neo-code769/DofusTouch-Calculator/blob/main/DofusTouchCalculator-background.png?raw=true"
        response = requests.get(image_url, stream=True, timeout=5)
        response.raw.decode_content = True
        background_image = Image.open(response.raw).resize((1100, 800))
        background_photo = ImageTk.PhotoImage(background_image)
        root.background_photo = background_photo
        background_label = ttk.Label(root, image=background_photo, borderwidth=0)
        background_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception:
        pass  # Continuer sans image si le téléchargement échoue

    # Styles
    style = ttk.Style()
    style.configure("BrownFrame.TFrame", background="#8B4513", borderwidth=3, relief="solid")
    style.configure(
        "Brown.TCombobox",
        fieldbackground="#8B4513",
        background="#8B4513",
        foreground="white",
        borderwidth=0,
        relief="flat",
        font=("Segoe UI", 16)
    )
    style.map(
        "Brown.TCombobox",
        fieldbackground=[("readonly", "#8B4513"), ("active", "#A0522D")],
        foreground=[("readonly", "white"), ("active", "white")]
    )
    style.configure(
        "Brown.TButton",
        background="#8B4513",
        foreground="white",
        borderwidth=0,
        focusthickness=0,
        font=("Segoe UI", 14),
        relief="flat"
    )
    style.map(
        "Brown.TButton",
        background=[("active", "#A0522D"), ("pressed", "#5C3317")],
        foreground=[("active", "white"), ("pressed", "white")]
    )

    # Menu déroulant pour les recettes
    recipe_names = list(recipes.keys())
    recipe_combobox_frame = ttk.Frame(root, style="BrownFrame.TFrame", padding=5)
    recipe_combobox_frame.place(relx=0.5, rely=0.45, anchor="center")

    recipe_combobox = ttk.Combobox(
        root,
        values=recipe_names,
        state="readonly",
        width=75,
        font=("Segoe UI", 16),
        style="Brown.TCombobox"
    )
    recipe_combobox.set("Veuillez sélectionner une recette")
    recipe_combobox.place(relx=0.5, rely=0.5, anchor="center")

    # Cadre pour les boutons
    button_frame = ttk.Frame(root, style="BrownFrame.TFrame", padding=5)
    button_frame.place(relx=0.5, rely=0.6, anchor="center", width=900)

    # Bouton : Gérer l'inventaire
    ttk.Button(
        button_frame,
        text="Gérer l'inventaire",
        command=manage_inventory,
        width=22,
        style="Brown.TButton"
    ).grid(row=0, column=0, padx=10)

    # Bouton : Calculer (recette sélectionnée)
    ttk.Button(
        button_frame,
        text="Calculer",
        command=on_calculate,
        width=22,
        style="Brown.TButton"
    ).grid(row=0, column=1, padx=10)

    # Bouton : Mettre à jour les valeurs
    ttk.Button(
        button_frame,
        text="Mettre à jour les valeurs",
        command=update_resource_values,
        width=22,
        style="Brown.TButton"
    ).grid(row=0, column=2, padx=10)

    # Bouton : Calculer toutes les recettes
    ttk.Button(
        button_frame,
        text="Calculer toutes les recettes",
        command=calculate_all_recipes,
        width=28,
        style="Brown.TButton"
    ).grid(row=0, column=3, padx=10)

    root.mainloop()


# Lancer l'interface graphique
if __name__ == "__main__":
    main_gui()
