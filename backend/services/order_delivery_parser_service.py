"""Service for parsing phone conversation transcripts to update order delivery information."""

import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import anthropic
from dotenv import load_dotenv
from pathlib import Path

# Load .env from backend directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

print(f"DEBUG - API Key loaded: {os.getenv('ANTHROPIC_API_KEY')}")
print(f"DEBUG - API Key length: {len(os.getenv('ANTHROPIC_API_KEY') or '')}")
print(f"DEBUG - .env path: {env_path}")


class OrderDeliveryParser:
    """
    Parses phone conversation transcripts to extract order delivery updates.

    This class uses Claude API from Anthropic to analyze conversation transcripts
    and extract order delivery time updates (estimated_time_arrival).
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the order delivery parser with Claude API.

        Args:
            api_key: Anthropic API key. If not provided, will use ANTHROPIC_API_KEY env variable.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided either as parameter or ANTHROPIC_API_KEY environment variable"
            )
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def parse_conversation(
        self, transcript: str, supplier_name: str
    ) -> Dict[str, Dict[str, str]]:
        """
        Parse a phone conversation transcript to extract order delivery updates.

        Args:
            transcript: The full text transcript of the phone conversation
            supplier_name: The name of the supplier involved in the conversation

        Returns:
            Dictionary with keys in format "[product_name, supplier_name]" and values as dict
            containing 'estimated_time_arrival' field with updated date.

            Example:
            {
                "[Paracétamol 500mg, Pharma Depot]": {
                    "estimated_time_arrival": "2025-12-20",
                    "delay_days": 5
                },
                "[Ibuprofène 400mg, Pharma Depot]": {
                    "estimated_time_arrival": "2025-12-15",
                    "delay_days": -2
                }
            }
        """
        prompt = self._build_prompt(transcript, supplier_name)

        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            # Extract the response text
            response_text = message.content[0].text

            # Parse the structured response
            result = self._parse_claude_response(response_text, supplier_name)

            return result

        except Exception as e:
            raise Exception(f"Error calling Claude API: {str(e)}")

    def _build_prompt(self, transcript: str, supplier_name: str) -> str:
        """
        Build the prompt for Claude API.

        Args:
            transcript: The conversation transcript
            supplier_name: The supplier name

        Returns:
            Formatted prompt string
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""Tu es un assistant spécialisé dans l'analyse de conversations téléphoniques entre pharmacies et fournisseurs concernant les commandes en cours.

Date actuelle: {current_date}

Analyse la transcription suivante d'une conversation avec le fournisseur "{supplier_name}".

Transcription:
{transcript}

Extrais UNIQUEMENT les informations suivantes pour chaque produit/commande mentionné(e):
- Le nom exact du produit
- La nouvelle date de livraison estimée OU le délai de retard/avance (en jours)

Règles importantes:
1. N'extrais QUE les informations explicitement mentionnées dans la conversation
2. Si une date de livraison ou un délai n'est pas mentionné pour un produit, ne l'inclus pas
3. Les dates doivent être au format YYYY-MM-DD (ex: 2025-12-20)
4. Les délais peuvent être:
   - Positifs pour un retard (ex: +5 jours signifie 5 jours de retard)
   - Négatifs pour une avance (ex: -2 jours signifie 2 jours d'avance)
5. Accepte différentes formulations:
   - "La livraison est prévue pour le 20 décembre"
   - "Il y aura 5 jours de retard"
   - "Nous livrerons 2 jours plus tôt"
   - "La commande arrivera la semaine prochaine" (calcule la date approximative)
6. Ignore les informations sur les prix, stocks, ou autres détails non liés à la livraison

Format de réponse STRICT (JSON):
{{
    "product_name_1": {{
        "new_date": "2025-12-20",
        "delay_days": 5
    }},
    "product_name_2": {{
        "delay_days": -2
    }},
    "product_name_3": {{
        "new_date": "2025-12-25"
    }}
}}

Notes:
- Si une date exacte est mentionnée, utilise "new_date"
- Si un délai est mentionné, utilise "delay_days"
- Tu peux fournir les deux si les deux informations sont disponibles
- Les délais positifs = retard, négatifs = avance

Si aucune information pertinente n'est trouvée, retourne un objet JSON vide: {{}}

Réponds UNIQUEMENT avec le JSON, sans texte additionnel."""

        return prompt

    def _parse_claude_response(
        self, response: str, supplier_name: str
    ) -> Dict[str, Dict[str, str]]:
        """
        Parse Claude's response into the expected format.

        Args:
            response: Raw response from Claude
            supplier_name: Supplier name to append to product names

        Returns:
            Formatted dictionary with order delivery updates
        """
        import json
        import re

        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            return {}

        try:
            parsed_data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return {}

        # Format the result with "[product_name, supplier_name]" string keys
        result = {}
        for product_name, updates in parsed_data.items():
            key = f"[{product_name}, {supplier_name}]"

            # Validate and clean the updates
            cleaned_updates = {}

            if "new_date" in updates:
                try:
                    # Validate date format
                    date_str = updates["new_date"]
                    datetime.strptime(date_str, "%Y-%m-%d")
                    cleaned_updates["new_date"] = date_str
                except (ValueError, TypeError):
                    pass

            if "delay_days" in updates:
                try:
                    delay_days = int(updates["delay_days"])
                    cleaned_updates["delay_days"] = delay_days
                except (ValueError, TypeError):
                    pass

            if cleaned_updates:
                result[key] = cleaned_updates

        return result


# Example usage
if __name__ == "__main__":
    import json

    # Example transcript
    example_transcript = """
    Pharmacie: Bonjour, c'est la pharmacie Martin. Je vous appelle au sujet de ma commande de Paracétamol 500mg.
    
    Fournisseur: Bonjour ! Oui, je vois votre commande. 
    
    Pharmacie: Est-ce qu'elle arrivera comme prévu ?
    
    Fournisseur: Malheureusement, nous avons un petit retard. La livraison du Paracétamol 500mg 
    sera reportée au 20 décembre 2025 au lieu de la date initiale.
    
    Pharmacie: D'accord, et pour l'Ibuprofène 400mg que j'ai aussi commandé ?
    
    Fournisseur: Bonne nouvelle pour celui-ci ! Nous pourrons vous livrer 3 jours plus tôt que prévu.
    
    Pharmacie: Parfait, merci pour ces informations.
    """

    supplier_name = "Pharma Depot"

    # Initialize parser (you would need to set ANTHROPIC_API_KEY env variable)
    try:
        parser = OrderDeliveryParser()
        result = parser.parse_conversation(
            transcript=example_transcript, supplier_name=supplier_name
        )
        print("Parsed result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set ANTHROPIC_API_KEY environment variable")
