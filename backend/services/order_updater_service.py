"""
Service pour mettre à jour le CSV orders.csv avec les résultats du parser de livraison.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import os


class OrderUpdater:
    """
    Met à jour le fichier CSV des commandes avec les informations
    extraites des conversations téléphoniques concernant les livraisons.
    """

    def __init__(self, csv_path: str = None):
        """
        Initialise l'updater avec le chemin du CSV.

        Args:
            csv_path: Chemin vers le fichier orders.csv
        """
        if csv_path is None:
            # Chemin par défaut
            csv_path = os.path.join(
                os.path.dirname(__file__), "../../data/orders.csv"
            )

        self.csv_path = csv_path
        self.df = None

    def load_csv(self) -> pd.DataFrame:
        """Charge le CSV des commandes."""
        self.df = pd.read_csv(self.csv_path)
        return self.df

    def save_csv(self, backup: bool = True) -> None:
        """
        Sauvegarde le CSV mis à jour.

        Args:
            backup: Si True, crée une copie de sauvegarde avant d'écraser
        """
        if self.df is None:
            raise ValueError("No data to save. Call load_csv() first.")

        if backup:
            backup_path = f"{self.csv_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            # Copy current file to backup
            import shutil
            if os.path.exists(self.csv_path):
                shutil.copy2(self.csv_path, backup_path)
                print(f"Backup created: {backup_path}")

        self.df.to_csv(self.csv_path, index=False)
        print(f"CSV updated: {self.csv_path}")

    def apply_updates(
        self,
        updates: Dict[str, Dict[str, any]],
        fournisseur_mapping: Dict[str, str] = None,
    ) -> Tuple[List[str], List[str]]:
        """
        Applique les mises à jour du parser au CSV orders.

        Args:
            updates: Dictionnaire des mises à jour depuis le parser
                    Format: {"[Product, Supplier]": {"new_date": "2025-12-20", "delay_days": 5}}
            fournisseur_mapping: Mapping optionnel nom_fournisseur -> id_fournisseur

        Returns:
            Tuple (successes, failures) avec les messages de succès et d'échec
        """
        if self.df is None:
            self.load_csv()

        successes = []
        failures = []

        for product_supplier_key, changes in updates.items():
            try:
                # Parser la clé "[product_name, supplier_name]"
                if not product_supplier_key.startswith("[") or not product_supplier_key.endswith("]"):
                    failures.append(f"Invalid key format: {product_supplier_key}")
                    continue

                # Enlever les crochets et split sur ", "
                content = product_supplier_key[1:-1]
                parts = content.split(", ", 1)

                if len(parts) != 2:
                    failures.append(f"Invalid key format: {product_supplier_key}")
                    continue

                product_name = parts[0]
                supplier_name = parts[1]

                # Trouver le fournisseur_id si un mapping est fourni
                if fournisseur_mapping and supplier_name in fournisseur_mapping:
                    supplier_id = fournisseur_mapping[supplier_name]
                    # Chercher par produit ET fournisseur
                    mask = (self.df["product_name"] == product_name) & (
                        self.df["fournisseur_id"] == supplier_id
                    )
                else:
                    # Chercher par nom de produit uniquement
                    mask = self.df["product_name"] == product_name

                # Vérifier qu'on a trouvé des commandes
                matching_orders = self.df[mask]
                if len(matching_orders) == 0:
                    failures.append(
                        f"No orders found for: {product_name} from {supplier_name}"
                    )
                    continue

                # Filtrer les commandes non encore livrées (time_of_arrival est None/NaN)
                pending_mask = mask & (self.df["time_of_arrival"].isna())
                pending_orders = self.df[pending_mask]

                if len(pending_orders) == 0:
                    failures.append(
                        f"No pending orders found for: {product_name} from {supplier_name}"
                    )
                    continue

                # Appliquer les mises à jour
                updated_fields = []

                if "new_date" in changes:
                    # Nouvelle date explicite
                    new_date = changes["new_date"]
                    # Convertir en datetime et formater avec heure
                    new_datetime = datetime.strptime(new_date, "%Y-%m-%d")
                    # Garder l'heure de l'estimation originale si possible
                    for idx in pending_orders.index:
                        original_eta = self.df.loc[idx, "estimated_time_arrival"]
                        try:
                            original_datetime = pd.to_datetime(original_eta)
                            # Garder l'heure, changer la date
                            final_datetime = new_datetime.replace(
                                hour=original_datetime.hour,
                                minute=original_datetime.minute,
                                second=original_datetime.second,
                            )
                        except:
                            # Si erreur, utiliser midi par défaut
                            final_datetime = new_datetime.replace(hour=12, minute=0, second=0)
                        
                        self.df.loc[idx, "estimated_time_arrival"] = final_datetime.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    
                    updated_fields.append(f"new_date={new_date}")

                elif "delay_days" in changes:
                    # Délai en jours (positif = retard, négatif = avance)
                    delay_days = changes["delay_days"]
                    
                    for idx in pending_orders.index:
                        original_eta = self.df.loc[idx, "estimated_time_arrival"]
                        try:
                            original_datetime = pd.to_datetime(original_eta)
                            new_datetime = original_datetime + timedelta(days=delay_days)
                            self.df.loc[idx, "estimated_time_arrival"] = new_datetime.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        except Exception as e:
                            failures.append(
                                f"Error updating order {self.df.loc[idx, 'order_id']}: {str(e)}"
                            )
                            continue
                    
                    updated_fields.append(f"delay={delay_days} days")

                if updated_fields:
                    num_updated = len(pending_orders)
                    successes.append(
                        f"Updated {num_updated} order(s) for {product_name} from {supplier_name}: {', '.join(updated_fields)}"
                    )
                else:
                    failures.append(
                        f"No valid updates found for {product_name} from {supplier_name}"
                    )

            except Exception as e:
                failures.append(f"Error updating {product_supplier_key}: {str(e)}")

        return successes, failures

    def preview_updates(
        self,
        updates: Dict[str, Dict[str, any]],
        fournisseur_mapping: Dict[str, str] = None,
    ) -> pd.DataFrame:
        """
        Prévisualise les changements sans les appliquer.

        Args:
            updates: Dictionnaire des mises à jour depuis le parser
            fournisseur_mapping: Mapping optionnel nom_fournisseur -> id_fournisseur

        Returns:
            DataFrame avec les commandes qui seraient modifiées
        """
        if self.df is None:
            self.load_csv()

        preview_data = []

        for product_supplier_key, changes in updates.items():
            if (
                not product_supplier_key.startswith("[")
                or not product_supplier_key.endswith("]")
            ):
                continue

            # Enlever les crochets et split sur ", "
            content = product_supplier_key[1:-1]
            parts = content.split(", ", 1)

            if len(parts) != 2:
                continue

            product_name = parts[0]
            supplier_name = parts[1]

            # Trouver les commandes correspondantes
            if fournisseur_mapping and supplier_name in fournisseur_mapping:
                supplier_id = fournisseur_mapping[supplier_name]
                mask = (self.df["product_name"] == product_name) & (
                    self.df["fournisseur_id"] == supplier_id
                )
            else:
                mask = self.df["product_name"] == product_name

            # Filtrer les commandes non livrées
            pending_mask = mask & (self.df["time_of_arrival"].isna())
            pending_orders = self.df[pending_mask]

            for _, order in pending_orders.iterrows():
                current_eta = order["estimated_time_arrival"]
                
                # Calculer la nouvelle date
                if "new_date" in changes:
                    new_date = changes["new_date"]
                    try:
                        original_datetime = pd.to_datetime(current_eta)
                        new_datetime = datetime.strptime(new_date, "%Y-%m-%d")
                        new_eta = new_datetime.replace(
                            hour=original_datetime.hour,
                            minute=original_datetime.minute,
                            second=original_datetime.second,
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        new_eta = f"{new_date} 12:00:00"
                elif "delay_days" in changes:
                    delay_days = changes["delay_days"]
                    try:
                        original_datetime = pd.to_datetime(current_eta)
                        new_datetime = original_datetime + timedelta(days=delay_days)
                        new_eta = new_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        new_eta = current_eta
                else:
                    new_eta = current_eta

                preview_row = {
                    "order_id": order["order_id"],
                    "product_name": product_name,
                    "supplier": supplier_name,
                    "quantity": order["quantity"],
                    "order_date": order["order_date"],
                    "current_eta": current_eta,
                    "new_eta": new_eta,
                    "change_type": "new_date" if "new_date" in changes else "delay",
                    "change_value": changes.get("new_date") or changes.get("delay_days"),
                }
                preview_data.append(preview_row)

        return pd.DataFrame(preview_data)


# Exemple d'utilisation
if __name__ == "__main__":
    import json

    # Exemple de mises à jour du parser
    parser_updates = {
        "[Paracétamol 500mg, Pharma Depot]": {"new_date": "2025-12-20"},
        "[Ibuprofène 400mg, Pharma Depot]": {"delay_days": -3},
    }

    # Mapping nom -> ID des fournisseurs (à charger depuis fournisseur.csv)
    supplier_mapping = {"Pharma Depot": "supp_089749f2-a3d0-4259-a235-65a044759d9a"}

    # Initialiser l'updater
    updater = OrderUpdater()
    updater.load_csv()

    print("=" * 80)
    print("PREVIEW DES CHANGEMENTS")
    print("=" * 80)
    print()

    # Prévisualiser
    preview = updater.preview_updates(parser_updates, supplier_mapping)
    if len(preview) > 0:
        print(preview.to_string(index=False))
    else:
        print("Aucune commande correspondante trouvée")
    print()

    # Appliquer les mises à jour (commenté pour le test)
    print("=" * 80)
    print("APPLICATION DES CHANGEMENTS (MODE DEMO)")
    print("=" * 80)
    print()

    successes, failures = updater.apply_updates(parser_updates, supplier_mapping)

    print("✅ Succès:")
    for msg in successes:
        print(f"  - {msg}")

    if failures:
        print()
        print("❌ Échecs:")
        for msg in failures:
            print(f"  - {msg}")

    # Sauvegarder (commenté pour le test)
    # updater.save_csv(backup=True)
