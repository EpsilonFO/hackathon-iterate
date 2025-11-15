"""
Service pour mettre à jour le CSV available_product.csv avec les résultats du parser.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple
import os


class ProductUpdater:
    """
    Met à jour le fichier CSV des produits disponibles avec les informations
    extraites des conversations téléphoniques.
    """
    
    def __init__(self, csv_path: str = None):
        """
        Initialise l'updater avec le chemin du CSV.
        
        Args:
            csv_path: Chemin vers le fichier available_product.csv
        """
        if csv_path is None:
            # Chemin par défaut
            csv_path = os.path.join(
                os.path.dirname(__file__), 
                "../../data/available_product.csv"
            )
        
        self.csv_path = csv_path
        self.df = None
    
    def load_csv(self) -> pd.DataFrame:
        """Charge le CSV des produits disponibles."""
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
            self.df.to_csv(backup_path, index=False)
            print(f"Backup created: {backup_path}")
        
        self.df.to_csv(self.csv_path, index=False)
        print(f"CSV updated: {self.csv_path}")
    
    def apply_updates(
        self, 
        updates: Dict[str, Dict[str, float]],
        fournisseur_mapping: Dict[str, str] = None
    ) -> Tuple[List[str], List[str]]:
        """
        Applique les mises à jour du parser au CSV.
        
        Args:
            updates: Dictionnaire des mises à jour depuis le parser
                    Format: {"[Product, Supplier]": {"price": 10.5, "delivery_time": 5}}
            fournisseur_mapping: Mapping optionnel nom_fournisseur -> id_fournisseur
                    
        Returns:
            Tuple (successes, failures) avec les messages de succès et d'échec
        """
        if self.df is None:
            self.load_csv()
        
        successes = []
        failures = []
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for product_supplier_key, changes in updates.items():
            try:
                # Parser la clé "[product_name, supplier_name]"
                if not product_supplier_key.startswith('[') or not product_supplier_key.endswith(']'):
                    failures.append(f"Invalid key format: {product_supplier_key}")
                    continue
                
                # Enlever les crochets et split sur ", "
                content = product_supplier_key[1:-1]
                parts = content.split(', ', 1)
                
                if len(parts) != 2:
                    failures.append(f"Invalid key format: {product_supplier_key}")
                    continue
                
                product_name = parts[0]
                supplier_name = parts[1]
                
                # Trouver le fournisseur_id si un mapping est fourni
                if fournisseur_mapping and supplier_name in fournisseur_mapping:
                    supplier_id = fournisseur_mapping[supplier_name]
                    # Chercher par ID
                    mask = (self.df['name'] == product_name) & (self.df['fournisseur'] == supplier_id)
                else:
                    # Chercher par nom (peut être ambigu)
                    mask = (self.df['name'] == product_name)
                
                # Vérifier qu'on a trouvé des lignes
                matching_rows = self.df[mask]
                if len(matching_rows) == 0:
                    failures.append(f"No match found for: {product_name} from {supplier_name}")
                    continue
                
                # Appliquer les mises à jour
                updated_fields = []
                if 'price' in changes:
                    self.df.loc[mask, 'price'] = changes['price']
                    updated_fields.append(f"price={changes['price']}")
                
                if 'delivery_time' in changes:
                    self.df.loc[mask, 'delivery_time'] = changes['delivery_time']
                    updated_fields.append(f"delivery_time={changes['delivery_time']}")
                
                # Mettre à jour la date de dernière modification
                self.df.loc[mask, 'last_information_update'] = current_time
                
                successes.append(
                    f"Updated {product_name} from {supplier_name}: {', '.join(updated_fields)}"
                )
                
            except Exception as e:
                failures.append(f"Error updating {product_supplier_key}: {str(e)}")
        
        return successes, failures
    
    def preview_updates(
        self, 
        updates: Dict[str, Dict[str, float]],
        fournisseur_mapping: Dict[str, str] = None
    ) -> pd.DataFrame:
        """
        Prévisualise les changements sans les appliquer.
        
        Args:
            updates: Dictionnaire des mises à jour depuis le parser
            fournisseur_mapping: Mapping optionnel nom_fournisseur -> id_fournisseur
                    
        Returns:
            DataFrame avec les lignes qui seraient modifiées
        """
        if self.df is None:
            self.load_csv()
        
        preview_data = []
        
        for product_supplier_key, changes in updates.items():
            if not product_supplier_key.startswith('[') or not product_supplier_key.endswith(']'):
                continue
            
            # Enlever les crochets et split sur ", "
            content = product_supplier_key[1:-1]
            parts = content.split(', ', 1)
            
            if len(parts) != 2:
                continue
            
            product_name = parts[0]
            supplier_name = parts[1]
            
            # Trouver les lignes correspondantes
            if fournisseur_mapping and supplier_name in fournisseur_mapping:
                supplier_id = fournisseur_mapping[supplier_name]
                mask = (self.df['name'] == product_name) & (self.df['fournisseur'] == supplier_id)
            else:
                mask = (self.df['name'] == product_name)
            
            matching_rows = self.df[mask]
            
            for _, row in matching_rows.iterrows():
                preview_row = {
                    'product_name': product_name,
                    'supplier': supplier_name,
                    'current_price': row['price'],
                    'new_price': changes.get('price', row['price']),
                    'current_delivery': row['delivery_time'],
                    'new_delivery': changes.get('delivery_time', row['delivery_time']),
                    'price_changed': 'price' in changes,
                    'delivery_changed': 'delivery_time' in changes
                }
                preview_data.append(preview_row)
        
        return pd.DataFrame(preview_data)


# Exemple d'utilisation
if __name__ == "__main__":
    import json
    
    # Exemple de mises à jour du parser
    parser_updates = {
        "[Paracétamol 500mg, MedSupply Network Pro South]": {
            "price": 3.62,
            "delivery_time": 10
        },
        "[Ibuprofène 400mg, MedSupply Network Pro South]": {
            "price": 4.20,
            "delivery_time": 6
        }
    }
    
    # Mapping nom -> ID des fournisseurs (à charger depuis fournisseur.csv)
    supplier_mapping = {
        "MedSupply Network Pro South": "supp_ec9af13b-265a-460c-b444-3f1fcf0ee58b"
    }
    
    # Initialiser l'updater
    updater = ProductUpdater()
    updater.load_csv()
    
    print("=" * 80)
    print("PREVIEW DES CHANGEMENTS")
    print("=" * 80)
    print()
    
    # Prévisualiser
    preview = updater.preview_updates(parser_updates, supplier_mapping)
    print(preview.to_string(index=False))
    print()
    
    # Appliquer les mises à jour
    print("=" * 80)
    print("APPLICATION DES CHANGEMENTS")
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
