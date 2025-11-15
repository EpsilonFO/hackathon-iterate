# Parser de Conversations Téléphoniques

Cette nouvelle brique permet d'analyser automatiquement les transcriptions de conversations téléphoniques avec les fournisseurs et d'extraire les mises à jour de prix et délais de livraison.

## 🎯 Objectif

Mettre à jour automatiquement le CSV `available_product.csv` à partir de retranscriptions de conversations téléphoniques avec les fournisseurs.

## 🔧 Configuration

### 1. Installer les dépendances

```bash
cd backend
pip install -e .
```

### 2. Configurer la clé API Anthropic

Créez un fichier `.env` à la racine du projet :

```bash
ANTHROPIC_API_KEY=votre_cle_api_anthropic
```

Vous pouvez obtenir votre clé API sur [console.anthropic.com](https://console.anthropic.com/)

## 📖 Utilisation

### Utilisation Programmatique

```python
from backend.services.parser_service import ConversationParser

# Initialiser le parser
parser = ConversationParser()

# Transcription de la conversation
transcript = """
Pharmacie: Bonjour, pour le Paracétamol 500mg, quel est votre prix ?
Fournisseur: Nous le proposons à 3.50 euros avec livraison en 7 jours.
"""

# Parser la conversation
result = parser.parse_conversation(
    transcript=transcript,
    supplier_name="Pharma Depot"
)

# Résultat:
# {
#     "Paracétamol 500mg X Pharma Depot": {
#         "price": 3.50,
#         "delivery_time": 7
#     }
# }
```

### Utilisation via l'API REST

Démarrez le serveur FastAPI :

```bash
cd backend
uvicorn backend.api.main:app --reload
```

Envoyez une requête POST à `/parser/parse-conversation` :

```bash
curl -X POST "http://localhost:8000/parser/parse-conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Bonjour, le Paracétamol 500mg est à 3.50 euros, livraison en 7 jours.",
    "supplier_name": "Pharma Depot"
  }'
```

Réponse :

```json
{
  "updates": {
    "Paracétamol 500mg X Pharma Depot": {
      "price": 3.50,
      "delivery_time": 7
    }
  },
  "message": "Successfully parsed 1 product update(s)"
}
```

### Script de Test

Un script de test complet est fourni :

```bash
export ANTHROPIC_API_KEY=votre_cle_api
cd backend
python test_parser.py
```

## 📊 Format de Sortie

La classe `ConversationParser` retourne un dictionnaire avec :

- **Clés** : Format `"nom_produit X nom_fournisseur"`
- **Valeurs** : Dictionnaire contenant les champs mis à jour
  - `price` (float) : Nouveau prix du produit
  - `delivery_time` (int) : Nouveau délai de livraison en jours (1-14)

Exemple :

```python
{
    "Paracétamol 500mg X Pharma Depot": {
        "price": 3.50,
        "delivery_time": 7
    },
    "Ibuprofène 400mg X Pharma Depot": {
        "price": 5.20
    }
}
```

## 🧩 Architecture

### Fichiers créés

```
backend/
├── services/
│   └── parser_service.py          # Classe ConversationParser
├── controllers/
│   └── parser_controller.py       # Endpoints API REST
├── api/
│   └── main.py                    # (modifié) Enregistrement du router
└── test_parser.py                 # Script de test
```

### Classe ConversationParser

```python
class ConversationParser:
    def __init__(self, api_key: Optional[str] = None):
        """Initialise avec la clé API Anthropic"""
        
    def parse_conversation(
        self, 
        transcript: str, 
        supplier_name: str
    ) -> Dict[str, Dict[str, float]]:
        """Parse une transcription et extrait les mises à jour"""
```

## 🎨 Fonctionnalités

### ✅ Ce qui est extrait

- ✅ Nom des produits mentionnés
- ✅ Nouveaux prix (en euros)
- ✅ Nouveaux délais de livraison (en jours, 1-14)

### ❌ Ce qui est ignoré

- ❌ Informations sur les stocks
- ❌ Disponibilités futures
- ❌ Commentaires généraux
- ❌ Autres détails non-prix/délai

## 🔒 Validation

Le parser valide automatiquement :

- Les prix sont des nombres positifs
- Les délais de livraison sont entre 1 et 14 jours
- Seules les informations explicitement mentionnées sont extraites

## 🚀 Prochaines Étapes

Pour intégrer cette brique avec la mise à jour du CSV :

1. **Créer un service de mise à jour CSV** qui :
   - Lit le fichier `available_product.csv`
   - Applique les mises à jour du parser
   - Sauvegarde le CSV modifié

2. **Créer un endpoint complet** :
   ```python
   POST /parser/parse-and-update
   ```
   Qui combine parsing + mise à jour du CSV

3. **Ajouter une interface frontend** pour :
   - Uploader/coller la transcription
   - Sélectionner le fournisseur
   - Visualiser les changements avant validation
   - Appliquer les mises à jour

## 📝 Exemple Complet

```python
import os
from backend.services.parser_service import ConversationParser

# Configuration
os.environ["ANTHROPIC_API_KEY"] = "votre_cle"
parser = ConversationParser()

# Conversation
transcript = """
Pharmacie: Bonjour, je voudrais mettre à jour mes tarifs.
Fournisseur: Pour le Paracétamol 500mg : 3.62 euros, livraison 10 jours.
Fournisseur: Ibuprofène 400mg : 4.20 euros, 6 jours.
"""

# Parsing
updates = parser.parse_conversation(transcript, "MedSupply Network")

# Résultat
print(updates)
# {
#     "Paracétamol 500mg X MedSupply Network": {
#         "price": 3.62,
#         "delivery_time": 10
#     },
#     "Ibuprofène 400mg X MedSupply Network": {
#         "price": 4.20,
#         "delivery_time": 6
#     }
# }
```

## 🐛 Dépannage

### Erreur : "API key must be provided"

→ Vérifiez que `ANTHROPIC_API_KEY` est défini dans votre environnement

### Erreur : "Import anthropic could not be resolved"

→ Réinstallez les dépendances : `pip install -e .`

### Aucune mise à jour extraite

→ Vérifiez que la transcription mentionne explicitement les prix et/ou délais

## 📚 Technologies Utilisées

- **Claude 3.5 Sonnet** (Anthropic) : Modèle LLM pour l'analyse de texte
- **FastAPI** : Framework API REST
- **Pydantic** : Validation de données
- **Python 3.10+**
