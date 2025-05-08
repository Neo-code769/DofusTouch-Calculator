''' 
    DOFUS 3.0 / Touch Upgrade
    Script pour calculer les ressources manquantes, ajouter des recettes, gérer l'inventaire, mettre à jour les valeurs des ressources et gérer la fortune personnelle.
'''

from tabulate import tabulate
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk  # Pour gérer l'image de fond
import requests  # Pour télécharger l'image depuis l'URL

# Définir les recettes et leurs ressources
recipes = {
    "Cape Cérémonial de Mazin Lyn": {
        "orbe_irisé": {"needed": 63, "value": 35000},
        "andésite": {"needed": 25, "value": 20000},
        "galets_brasiliant": {"needed": 3, "value": 190000},
        "cuir_de_godruche": {"needed": 64, "value": 12000},
        "moustache_de_klime": {"needed": 10, "value": 2500},
        "scalp_de_klime": {"needed": 2, "value": 220000},
        "cuir_de_peunch": {"needed": 62, "value": 1500},
        "etoffe_de_cuirasse": {"needed": 31, "value": 350},
    },
}

# Inventaire global
inventory = {
    "orbe_irisé": 51,
    "andésite": 10,
    "galets_brasiliant": 3,
    "cuir_de_godruche": 0,
    "moustache_de_klime": 0,
    "scalp_de_klime": 0,
    "cuir_de_peunch": 0,
    "etoffe_de_cuirasse": 0,
}

# Variable globale pour la fortune personnelle
current_kamas = 3700000  # Valeur initiale en kamas

# Fonction pour calculer les ressources manquantes et leur coût
def calculate_missing_resources(recipe_name, resources):
    kamas_manquant = 0
    table = []

    for resource, data in resources.items():
        acquired = inventory.get(resource, 0)  # Récupérer la quantité dans l'inventaire
        lack = data["needed"] - acquired
        if lack > 0:
            kamas_manquant += lack * data["value"]
        table.append([
            resource.replace('_', ' '),  # Nom de la ressource
            data["needed"],             # Quantité requise
            acquired,                   # Quantité acquise
            lack,                       # Quantité manquante
            f"{data['value']:,}".replace(",", " "),  # Valeur unitaire formatée
        ])

    # Convertir le tableau en texte formaté
    table_text = tabulate(table, headers=["Ressource", "Requis", "Acquis", "Manquant", "Valeur unitaire"], tablefmt="grid")
    return table_text, kamas_manquant

# Fonction pour afficher les résultats dans une fenêtre
def show_results(recipe_name, table_text, kamas_manquant):
    result_window = tk.Toplevel()
    result_window.title(f"Résultats pour {recipe_name}")

    # Centrer la fenêtre
    center_window(result_window)

    # Afficher le tableau
    text_widget = tk.Text(result_window, wrap="none", width=100, height=20)
    text_widget.insert("1.0", table_text)
    text_widget.config(state="disabled")  # Rendre le texte non modifiable
    text_widget.pack(padx=10, pady=10)

    # Afficher le coût total manquant
    total_label = tk.Label(result_window, text=f"Il me manque : {kamas_manquant:,}".replace(",", " ") + " kamas", font=("Arial", 12, "bold"))
    total_label.pack(pady=10)

    # Bouton pour fermer la fenêtre
    close_button = tk.Button(result_window, text="Fermer", command=result_window.destroy)
    close_button.pack(pady=10)

# Fonction pour ajouter une nouvelle recette
def add_recipe():
    global recipe_combobox  # Make recipe_combobox accessible
    def save_recipe():
        try:
            # Récupérer le nom de la recette
            recipe_name = recipe_name_entry.get().strip()
            if not recipe_name:
                raise ValueError("Le nom de la recette ne peut pas être vide.")
            if recipe_name in recipes:
                raise ValueError("Cette recette existe déjà.")

            # Récupérer les ressources
            resources_text = resources_text_widget.get("1.0", "end").strip()
            if not resources_text:
                raise ValueError("Les ressources ne peuvent pas être vides.")

            # Convertir les ressources en dictionnaire
            resources = {}
            for line in resources_text.split("\n"):
                parts = line.split(",")
                if len(parts) != 3:
                    raise ValueError("Format incorrect. Utilisez : nom, requis, valeur")
                resource_name = parts[0].strip()
                needed = int(parts[1].strip())
                value = int(parts[2].strip())
                resources[resource_name] = {"needed": needed, "value": value}

            # Ajouter la recette au dictionnaire
            recipes[recipe_name] = resources
            recipe_combobox["values"] = list(recipes.keys())  # Mettre à jour la liste déroulante
            messagebox.showinfo("Succès", f"La recette '{recipe_name}' a été ajoutée avec succès.")
            add_recipe_window.destroy()
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))

    # Fenêtre pour ajouter une recette
    add_recipe_window = tk.Toplevel()
    add_recipe_window.title("Ajouter une nouvelle recette")

    # Centrer la fenêtre
    center_window(add_recipe_window)

    # Entrée pour le nom de la recette
    tk.Label(add_recipe_window, text="Nom de la recette :", font=("Arial", 12)).pack(pady=5)
    recipe_name_entry = tk.Entry(add_recipe_window, width=40, font=("Arial", 12))
    recipe_name_entry.pack(pady=5)

    # Zone de texte pour les ressources
    tk.Label(add_recipe_window, text="Ressources (format : nom, requis, valeur) :", font=("Arial", 12)).pack(pady=5)
    resources_text_widget = tk.Text(add_recipe_window, width=50, height=10, font=("Arial", 12))
    resources_text_widget.pack(pady=5)

    # Bouton pour sauvegarder
    save_button = tk.Button(add_recipe_window, text="Sauvegarder", command=save_recipe, font=("Arial", 12))
    save_button.pack(pady=10)

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
            updates_text = updates_text_widget.get("1.0", "end").strip()
            if not updates_text:
                raise ValueError("Les mises à jour ne peuvent pas être vides.")
            for line in updates_text.split("\n"):
                parts = line.split(",")
                if len(parts) != 2:
                    raise ValueError("Format incorrect. Utilisez : nom, nouvelle valeur")
                resource_name = parts[0].strip()
                new_value = int(parts[1].strip())
                
                # Mettre à jour la valeur dans toutes les recettes
                updated = False
                for recipe in recipes.values():
                    if resource_name in recipe:
                        recipe[resource_name]["value"] = new_value
                        updated = True
                
                if not updated:
                    raise ValueError(f"Ressource '{resource_name}' introuvable dans les recettes.")
            
            messagebox.showinfo("Succès", "Les valeurs des ressources ont été mises à jour.")
            update_window.destroy()
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))

    # Fenêtre pour mettre à jour les ressources
    update_window = tk.Toplevel()
    update_window.title("Mettre à jour les valeurs des ressources")

    # Centrer la fenêtre
    center_window(update_window)

    # Zone de texte pour les mises à jour
    tk.Label(update_window, text="Mises à jour (format : nom, nouvelle valeur) :", font=("Arial", 12)).pack(pady=5)
    updates_text_widget = tk.Text(update_window, width=50, height=15, font=("Arial", 12))
    updates_text_widget.pack(pady=5)

    # Pré-remplir avec les ressources existantes
    existing_resources = set()
    for recipe in recipes.values():
        existing_resources.update(recipe.keys())
    updates_text_widget.insert("1.0", "\n".join([f"{resource}, 0" for resource in existing_resources]))

    # Bouton pour sauvegarder
    save_button = tk.Button(update_window, text="Sauvegarder", command=save_updates, font=("Arial", 12))
    save_button.pack(pady=10)

# Fonction principale pour l'interface graphique
def main_gui():
    def on_calculate():
        # Récupérer la recette sélectionnée
        selected_recipe_index = recipe_combobox.current()
        if selected_recipe_index == -1 or recipe_combobox.get() == "Veuillez sélectionner une recette":
            messagebox.showerror("Erreur", "Veuillez sélectionner une recette.")
            return

        recipe_name = recipe_names[selected_recipe_index]
        resources = recipes[recipe_name]

        # Calculer les ressources manquantes
        table_text, kamas_manquant = calculate_missing_resources(recipe_name, resources)

        # Afficher les résultats
        show_results(recipe_name, table_text, kamas_manquant)

    # Fenêtre principale
    root = tk.Tk()
    root.title("Calculateur de Recettes DOFUS")
    root.geometry("840x460")  # Taille fixe de la fenêtre
    center_window(root)

    # Télécharger et charger l'image de fond
    image_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR3aJKGjBvG53T_9XuPu4UXTCIMb9fVqjRmug&s"
    response = requests.get(image_url, stream=True)
    response.raw.decode_content = True
    background_image = Image.open(response.raw)

    # Redimensionner l'image à 840x460 pixels
    background_image = background_image.resize((840, 460))

    # Convertir l'image pour tkinter
    background_photo = ImageTk.PhotoImage(background_image)

    # Ajouter l'image de fond
    background_label = tk.Label(root, image=background_photo)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)

    # Style global
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12), padding=5)
    style.configure("TLabel", font=("Arial", 14), background="#f0f0f0", borderwidth=0)
    style.configure("TCombobox", font=("Arial", 12))

    # Label pour le titre
    title_label = tk.Label(root, text="Dofus Calculator :", font=("Arial", 18, "bold"), bg="#f0f0f0", borderwidth=0)
    title_label.pack(pady=10)

    # Label pour la fortune actuelle
    global current_kamas
    kamas_label = tk.Label(root, text=f"Fortune actuelle : {current_kamas:,} kamas".replace(",", " "), font=("Arial", 14), bg="#f0f0f0", borderwidth=0)
    kamas_label.pack(pady=5)

    # Liste déroulante pour les recettes
    recipe_names = list(recipes.keys())
    recipe_combobox = ttk.Combobox(root, values=recipe_names, state="readonly", width=50, font=("Arial", 12))
    recipe_combobox.set("Veuillez sélectionner une recette")  # Valeur par défaut
    recipe_combobox.pack(pady=10)

    # Bouton pour calculer
    calculate_button = ttk.Button(root, text="Calculer", command=on_calculate)
    calculate_button.pack(pady=10)

    # Fonction pour gérer l'inventaire
    def manage_inventory():
        messagebox.showinfo("Gérer l'inventaire", "Cette fonctionnalité n'est pas encore implémentée.")

    # Bouton pour gérer l'inventaire
    manage_inventory_button = ttk.Button(root, text="Gérer l'inventaire", command=manage_inventory)
    manage_inventory_button.pack(pady=10)

    # Bouton pour ajouter une recette
    add_recipe_button = ttk.Button(root, text="Ajouter une recette", command=add_recipe)
    add_recipe_button.pack(pady=10)

    # Fonction pour mettre à jour la fortune personnelle
    def update_kamas():
        global current_kamas
        try:
            new_kamas = int(tk.simpledialog.askstring("Mettre à jour ma fortune", "Entrez votre nouvelle fortune en kamas :"))
            current_kamas = new_kamas
            kamas_label.config(text=f"Fortune actuelle : {current_kamas:,} kamas".replace(",", " "))
            messagebox.showinfo("Succès", "Votre fortune a été mise à jour avec succès.")
        except (ValueError, TypeError):
            messagebox.showerror("Erreur", "Veuillez entrer un nombre valide.")

    # Bouton pour mettre à jour la fortune personnelle
    update_kamas_button = ttk.Button(root, text="Mettre à jour ma fortune", command=update_kamas)
    update_kamas_button.pack(pady=10)

    # Bouton pour mettre à jour les valeurs des ressources
    update_resources_button = ttk.Button(root, text="Mettre à jour les ressources", command=update_resource_values)
    update_resources_button.pack(pady=10)

    # Lancer la boucle principale
    root.mainloop()

# Lancer l'interface graphique
if __name__ == "__main__":
    main_gui()

