"""
Exemple complet d'utilisation du système de parsing et mise à jour des commandes.

Ce script démontre le flux complet:
1. Parser une conversation téléphonique sur les livraisons
2. Prévisualiser les changements sur orders.csv
3. Appliquer les mises à jour au CSV
"""

import os
import sys
import json
import pandas as pd

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.order_delivery_parser_service import OrderDeliveryParser
from backend.services.order_updater_service import OrderUpdater


def load_supplier_mapping(csv_path: str = "../data/fournisseur.csv") -> dict:
    """Charge le mapping nom -> ID des fournisseurs."""
    df = pd.read_csv(csv_path)
    return dict(zip(df["name"], df["id"]))


def complete_order_workflow_example():
    """Exemple de workflow complet pour les mises à jour de commandes."""

    print("=" * 80)
    print("WORKFLOW COMPLET : PARSING ET MISE À JOUR DES COMMANDES")
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
    Pharmacie: Bonjour, c'est la pharmacie Martin. J'ai besoin d'informations sur mes commandes.
    
    Fournisseur: Bonjour ! Bien sûr, je vous écoute.
    
    Pharmacie: Pour ma commande de Paracétamol 500mg, où en est la livraison ?
    
    Fournisseur: La commande de Paracétamol sera livrée avec 4 jours de retard malheureusement,
    à cause de problèmes d'approvisionnement.
    
    Pharmacie: Et pour l'Ibuprofène 400mg ?
    
    Fournisseur: Excellente nouvelle ! Nous avons accéléré la production et nous pourrons vous 
    livrer 2 jours plus tôt que prévu.
    
    Pharmacie: Parfait, merci !
    """

    supplier_name = "MedSupply Network Pro South"

    print(f"Fournisseur: {supplier_name}")
    print(f"Longueur de la transcription: {len(conversation_transcript)} caractères")
    print()

    # ========== ÉTAPE 3: PARSING ==========
    print("🤖 ÉTAPE 3: Analyse avec Claude")
    print("-" * 80)

    try:
        parser = OrderDeliveryParser(api_key=api_key)
        print("✓ Parser initialisé")

        print("⏳ Analyse en cours...")
        parsed_updates = parser.parse_conversation(
            transcript=conversation_transcript, supplier_name=supplier_name
        )
        print(f"✓ Analyse terminée : {len(parsed_updates)} mise(s) à jour trouvée(s)")
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
        updater = OrderUpdater()
        updater.load_csv()
        print(f"✓ CSV des commandes chargé : {len(updater.df)} lignes")
        
        # Afficher quelques stats
        pending_orders = updater.df[updater.df["time_of_arrival"].isna()]
        print(f"  - {len(pending_orders)} commandes en attente de livraison")
        delivered_orders = updater.df[~updater.df["time_of_arrival"].isna()]
        print(f"  - {len(delivered_orders)} commandes déjà livrées")
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
            print("\nCommandes qui seront modifiées:")
            print()

            # Affichage formaté
            for _, row in preview_df.iterrows():
                print(f"📦 Commande: {row['order_id']}")
                print(f"   Produit: {row['product_name']}")
                print(f"   Quantité: {row['quantity']} unités")
                print(f"   Date de commande: {row['order_date']}")
                print(f"   📅 Date estimée actuelle: {row['current_eta']}")
                print(f"   📅 Nouvelle date estimée: {row['new_eta']}")
                
                if row['change_type'] == 'delay':
                    delay = row['change_value']
                    if delay > 0:
                        print(f"   ⏱️  Changement: +{delay} jours de retard")
                    else:
                        print(f"   ⚡ Changement: {delay} jours (livraison avancée)")
                else:
                    print(f"   📆 Nouvelle date: {row['change_value']}")
                
                print()
        else:
            print("⚠️  Aucune commande correspondante trouvée")
            print("   Vérifiez que:")
            print("   - Les produits existent dans orders.csv")
            print("   - Le fournisseur correspond")
            print("   - Les commandes ne sont pas déjà livrées")
            print()

    except Exception as e:
        print(f"❌ Erreur lors de la prévisualisation: {e}")
        return

    # ========== ÉTAPE 6: CONFIRMATION ==========
    print("=" * 80)
    print("❓ Voulez-vous appliquer ces changements ?")
    print("=" * 80)
    print()
    print("Mode démo: Les changements ne seront PAS sauvegardés")
    print("Pour appliquer réellement, modifiez le code et décommentez updater.save_csv()")
    print()

    # ========== ÉTAPE 7: APPLICATION (MODE DÉMO) ==========
    print("✅ ÉTAPE 6: Application des changements (MODE DÉMO)")
    print("-" * 80)

    try:
        successes, failures = updater.apply_updates(parsed_updates, supplier_mapping)

        if successes:
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
    complete_order_workflow_example()
