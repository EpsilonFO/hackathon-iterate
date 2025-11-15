"""
Script de test pour le parser de conversations concernant les livraisons de commandes.

Ce script démontre comment utiliser la classe OrderDeliveryParser pour parser
une conversation téléphonique et mettre à jour les dates de livraison dans orders.csv.
"""

import os
import sys
import json
from dotenv import load_dotenv
load_dotenv()

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.order_delivery_parser_service import OrderDeliveryParser


def test_order_delivery_parser():
    """Test du parser avec un exemple de conversation sur les livraisons."""

    print("=" * 80)
    print("TEST DU PARSER DE CONVERSATIONS - MISES À JOUR DE LIVRAISONS")
    print("=" * 80)
    print()

    # Exemple de transcription de conversation téléphonique
    example_transcript = """
    Pharmacie: Bonjour, c'est la pharmacie Martin. Je vous appelle au sujet de mes commandes en cours.
    
    Fournisseur: Bonjour ! Bien sûr, que puis-je faire pour vous ?
    
    Pharmacie: J'ai commandé du Paracétamol 500mg la semaine dernière. Où en est la livraison ?
    
    Fournisseur: Ah oui, je vois votre commande. Malheureusement, nous avons un léger retard 
    à cause de problèmes logistiques. La livraison sera reportée au 20 décembre 2025.
    
    Pharmacie: C'est dommage. Et pour l'Ibuprofène 400mg ?
    
    Fournisseur: Pour l'Ibuprofène, bonne nouvelle ! Nous avons pu accélérer la production. 
    Nous pourrons vous livrer 3 jours plus tôt que prévu initialement.
    
    Pharmacie: Excellent ! Et l'Aspirine 500mg ?
    
    Fournisseur: L'Aspirine sera livrée comme prévu, pas de changement sur cette commande.
    
    Pharmacie: Parfait. Et ma commande de Doliprane 1000mg ?
    
    Fournisseur: Le Doliprane aura environ 5 jours de retard malheureusement.
    
    Pharmacie: D'accord, je note. Merci pour ces informations.
    
    Fournisseur: Je vous en prie. Désolé pour les retards.
    """

    supplier_name = "Pharma Depot Plus North"

    print(f"📞 Fournisseur: {supplier_name}")
    print()
    print("Transcription de la conversation:")
    print("-" * 80)
    print(example_transcript)
    print("-" * 80)
    print()

    # Vérifier que la clé API est configurée
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "❌ ERREUR: La variable d'environnement ANTHROPIC_API_KEY n'est pas définie."
        )
        print()
        print("Pour configurer votre clé API:")
        print("1. Créez un fichier .env à la racine du projet")
        print("2. Ajoutez la ligne: ANTHROPIC_API_KEY=votre_cle_api")
        print("3. Ou exportez la variable: export ANTHROPIC_API_KEY=votre_cle_api")
        print()
        return

    try:
        # Initialiser le parser
        print("🤖 Initialisation du parser...")
        parser = OrderDeliveryParser(api_key=api_key)
        print("✓ Parser initialisé")
        print()

        # Parser la conversation
        print("⏳ Analyse de la conversation en cours...")
        result = parser.parse_conversation(
            transcript=example_transcript, supplier_name=supplier_name
        )
        print(f"✓ Analyse terminée : {len(result)} mise(s) à jour trouvée(s)")
        print()

        # Afficher les résultats
        print("=" * 80)
        print("RÉSULTATS DU PARSING")
        print("=" * 80)
        print()

        if result:
            print("JSON brut:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print()

            # Afficher les détails de manière formatée
            print("Détails des mises à jour de livraison:")
            print("-" * 80)
            for product_key, updates in result.items():
                print(f"\n📦 {product_key}")
                if "new_date" in updates:
                    print(f"   📅 Nouvelle date de livraison: {updates['new_date']}")
                if "delay_days" in updates:
                    delay = updates["delay_days"]
                    if delay > 0:
                        print(f"   ⏱️  Retard: +{delay} jours")
                    elif delay < 0:
                        print(f"   ⚡ Avance: {delay} jours (livraison plus tôt)")
                    else:
                        print(f"   ✓ Pas de changement")
        else:
            print("⚠️  Aucune mise à jour de livraison trouvée dans la conversation.")

        print()
        print("=" * 80)
        print()
        print("💡 Pour appliquer ces mises à jour au fichier orders.csv:")
        print("   1. Utilisez la classe OrderUpdater")
        print("   2. Ou utilisez l'API endpoint /order-parser/parse-delivery-updates")
        print()

    except ValueError as e:
        print(f"❌ Erreur de configuration: {e}")
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_order_delivery_parser()
