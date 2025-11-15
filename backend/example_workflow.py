"""
Exemple complet d'utilisation du système de parsing et mise à jour.

Ce script démontre le flux complet:
1. Parser une conversation téléphonique
2. Prévisualiser les changements
3. Appliquer les mises à jour au CSV
"""

import os
import sys
import json
import pandas as pd

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.parser_service import ConversationParser
from backend.services.product_updater_service import ProductUpdater


def load_supplier_mapping(csv_path: str = "../data/fournisseur.csv") -> dict:
    """Charge le mapping nom -> ID des fournisseurs."""
    df = pd.read_csv(csv_path)
    return dict(zip(df['name'], df['id']))


def complete_workflow_example():
    """Exemple de workflow complet."""
    
    print("=" * 80)
    print("WORKFLOW COMPLET : PARSING ET MISE À JOUR")
    print("=" * 80)
    print()
    
    # ========== ÉTAPE 1: CONFIGURATION ==========
    print("📋 ÉTAPE 1: Configuration")
    print("-" * 80)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERREUR: ANTHROPIC_API_KEY non définie")
        print("Définissez la variable d'environnement ou créez un fichier .env")
        return
    
    print("✓ Clé API configurée")
    print()
    
    # ========== ÉTAPE 2: TRANSCRIPTION ==========
    print("📞 ÉTAPE 2: Transcription de la conversation")
    print("-" * 80)
    
    conversation_transcript = """
    Pharmacie Martin: Bonjour, c'est la pharmacie Martin. Je voudrais mettre à jour nos informations.
    
    MedSupply: Bonjour ! Bien sûr, je vous écoute.
    
    Pharmacie: Pour le Paracétamol 500mg, quel est votre nouveau tarif ?
    
    MedSupply: Nous avons mis à jour nos prix. Le Paracétamol 500mg est maintenant à 3.62 euros.
    
    Pharmacie: Et le délai de livraison ?
    
    MedSupply: 10 jours pour ce produit.
    
    Pharmacie: Parfait. J'ai aussi besoin de l'Aspirine 500mg.
    
    MedSupply: L'Aspirine 500mg est à 50.76 euros avec un délai de 12 jours.
    
    Pharmacie: Très bien, merci !
    """
    
    supplier_name = "MedSupply Network Pro South"
    
    print(f"Fournisseur: {supplier_name}")
    print(f"Longueur de la transcription: {len(conversation_transcript)} caractères")
    print()
    
    # ========== ÉTAPE 3: PARSING ==========
    print("🤖 ÉTAPE 3: Analyse avec Claude")
    print("-" * 80)
    
    try:
        parser = ConversationParser(api_key=api_key)
        print("✓ Parser initialisé")
        
        print("⏳ Analyse en cours...")
        parsed_updates = parser.parse_conversation(
            transcript=conversation_transcript,
            supplier_name=supplier_name
        )
        print(f"✓ Analyse terminée : {len(parsed_updates)} produit(s) trouvé(s)")
        print()
        
        print("Résultats du parsing:")
        print(json.dumps(parsed_updates, indent=2, ensure_ascii=False))
        print()
        
    except Exception as e:
        print(f"❌ Erreur lors du parsing: {e}")
        return
    
    # ========== ÉTAPE 4: CHARGEMENT DES DONNÉES ==========
    print("📊 ÉTAPE 4: Chargement des données")
    print("-" * 80)
    
    try:
        # Charger le mapping des fournisseurs
        supplier_mapping = load_supplier_mapping()
        print(f"✓ {len(supplier_mapping)} fournisseurs chargés")
        
        # Initialiser l'updater
        updater = ProductUpdater()
        updater.load_csv()
        print(f"✓ CSV chargé : {len(updater.df)} lignes")
        print()
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return
    
    # ========== ÉTAPE 5: PREVIEW ==========
    print("👁️  ÉTAPE 5: Prévisualisation des changements")
    print("-" * 80)
    
    try:
        preview_df = updater.preview_updates(parsed_updates, supplier_mapping)
        
        if len(preview_df) > 0:
            print("\nChangements à appliquer:")
            print()
            
            # Affichage formaté
            for _, row in preview_df.iterrows():
                print(f"📦 {row['product_name']}")
                print(f"   Fournisseur: {row['supplier']}")
                
                if row['price_changed']:
                    print(f"   💰 Prix: {row['current_price']:.2f}€ → {row['new_price']:.2f}€")
                else:
                    print(f"   💰 Prix: {row['current_price']:.2f}€ (inchangé)")
                
                if row['delivery_changed']:
                    print(f"   🚚 Délai: {row['current_delivery']} → {row['new_delivery']} jours")
                else:
                    print(f"   🚚 Délai: {row['current_delivery']} jours (inchangé)")
                
                print()
        else:
            print("⚠️  Aucun changement à appliquer")
            print()
        
    except Exception as e:
        print(f"❌ Erreur lors de la prévisualisation: {e}")
        return
    
    # ========== ÉTAPE 6: CONFIRMATION ==========
    print("=" * 80)
    print("❓ Voulez-vous appliquer ces changements ?")
    print("=" * 80)
    print()
    print("Mode démo: Les changements ne seront PAS appliqués")
    print("Pour appliquer réellement, modifiez le code et décommentez updater.save_csv()")
    print()
    
    # ========== ÉTAPE 7: APPLICATION (MODE DÉMO) ==========
    print("✅ ÉTAPE 6: Application des changements (MODE DÉMO)")
    print("-" * 80)
    
    try:
        successes, failures = updater.apply_updates(parsed_updates, supplier_mapping)
        
        print("\n✅ Succès:")
        for msg in successes:
            print(f"  ✓ {msg}")
        
        if failures:
            print("\n❌ Échecs:")
            for msg in failures:
                print(f"  ✗ {msg}")
        
        print()
        print("⚠️  MODE DÉMO : Changements appliqués en mémoire uniquement")
        print("Pour sauvegarder, décommentez : updater.save_csv(backup=True)")
        print()
        
        # Pour appliquer réellement:
        # updater.save_csv(backup=True)
        
    except Exception as e:
        print(f"❌ Erreur lors de l'application: {e}")
        return
    
    print("=" * 80)
    print("🎉 WORKFLOW TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    complete_workflow_example()
