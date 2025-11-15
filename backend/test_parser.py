"""
Script de test pour le parser de conversations.

Ce script démontre comment utiliser la classe ConversationParser pour parser
une conversation téléphonique et mettre à jour les informations des produits.
"""

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.transcript_parser_service import TranscriptParserService


def test_conversation_parser():
    """Test du parser avec un exemple de conversation."""

    # Exemple de transcription de conversation téléphonique
    example_transcript = """
    Pharmacie: Bonjour, c'est la pharmacie Martin à l'appareil. Je souhaiterais mettre à jour nos tarifs.
    
    Fournisseur: Bonjour ! Bien sûr, je vous écoute.
    
    Pharmacie: Pour le Paracétamol 500mg, quel est votre nouveau tarif ?
    
    Fournisseur: Nous avons revu nos prix. Le Paracétamol 500mg est maintenant à 3.62 euros l'unité.
    
    Pharmacie: D'accord. Et le délai de livraison ?
    
    Fournisseur: Pour celui-ci, nous pouvons vous livrer en 10 jours.
    
    Pharmacie: Parfait. J'ai aussi besoin d'informations sur l'Ibuprofène 400mg.
    
    Fournisseur: L'Ibuprofène 400mg est proposé à 4.20 euros avec un délai de livraison de 6 jours.
    
    Pharmacie: Et pour l'Aspirine 500mg ?
    
    Fournisseur: L'Aspirine 500mg coûte 2.80 euros. Pas de changement sur le délai, toujours 12 jours.
    
    Pharmacie: Très bien, merci pour ces informations.
    
    Fournisseur: Je vous en prie. À bientôt !
    """

    supplier_name = "MedSupply Network Pro South"

    print("=" * 80)
    print("TEST DU PARSER DE CONVERSATIONS")
    print("=" * 80)
    print()
    print(f"Fournisseur: {supplier_name}")
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
        print("Initialisation du parser...")
        parser = TranscriptParserService(
            api_key=api_key,
            data_dir=os.path.join(os.path.dirname(__file__), "..", "data"),
        )
        print("✓ Parser initialisé")
        print()

        # Parser la conversation
        print("Analyse de la conversation en cours...")
        result = parser.parse_conversation(
            transcript=example_transcript, supplier_name=supplier_name
        )
        print("✓ Analyse terminée")
        print()

        # Afficher les résultats
        print("=" * 80)
        print("RÉSULTATS")
        print("=" * 80)
        print()

        if result:
            print(f"Nombre de mises à jour extraites: {len(result)}")
            print()
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print()

            # Afficher les détails
            print("Détails des mises à jour:")
            print("-" * 80)
            for product_key, updates in result.items():
                print(f"\n📦 {product_key}")
                if "price" in updates:
                    print(f"   💰 Nouveau prix: {updates['price']} €")
                if "delivery_time" in updates:
                    print(f"   🚚 Nouveau délai: {updates['delivery_time']} jours")
        else:
            print("Aucune mise à jour trouvée dans la conversation.")

        print()
        print("=" * 80)

    except ValueError as e:
        print(f"❌ Erreur de configuration: {e}")
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_conversation_parser()
