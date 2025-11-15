"""Service for parsing phone conversation transcripts to update product information."""

import os
from typing import Dict, Optional
import anthropic


class ConversationParser:
    """
    Parses phone conversation transcripts to extract product price and delivery time updates.
    
    This class uses Claude API from Anthropic to analyze conversation transcripts
    and extract structured product information updates.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the conversation parser with Claude API.
        
        Args:
            api_key: Anthropic API key. If not provided, will use ANTHROPIC_API_KEY env variable.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided either as parameter or ANTHROPIC_API_KEY environment variable")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def parse_conversation(
        self, 
        transcript: str, 
        supplier_name: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Parse a phone conversation transcript to extract product updates.
        
        Args:
            transcript: The full text transcript of the phone conversation
            supplier_name: The name of the supplier involved in the conversation
            
        Returns:
            Dictionary with keys in format "[product_name, supplier_name]" and values as dict
            containing 'price' and/or 'delivery_time' fields with updated values.
            
            Example:
            {
                "[Paracétamol 500mg, Pharma Depot]": {
                    "price": 12.50,
                    "delivery_time": 5
                },
                "[Ibuprofène 400mg, Pharma Depot]": {
                    "price": 8.30
                }
            }
        """
        prompt = self._build_prompt(transcript, supplier_name)
        
        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ]
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
        prompt = f"""Tu es un assistant spécialisé dans l'analyse de conversations téléphoniques entre pharmacies et fournisseurs.

Analyse la transcription suivante d'une conversation avec le fournisseur "{supplier_name}".

Transcription:
{transcript}

Extrais UNIQUEMENT les informations suivantes pour chaque produit mentionné:
- Le nom exact du produit
- Le nouveau prix (si mentionné)
- Le nouveau délai de livraison en jours (si mentionné)

Règles importantes:
1. N'extrais QUE les informations explicitement mentionnées dans la conversation
2. Si un prix ou délai n'est pas mentionné pour un produit, ne l'inclus pas
3. Les prix doivent être en nombres décimaux (ex: 12.50)
4. Les délais de livraison doivent être en jours (nombre entier entre 1 et 14)
5. Ignore les informations sur les stocks, disponibilités futures, ou autres détails non demandés

Format de réponse STRICT (JSON):
{{
    "product_name_1": {{
        "price": 12.50,
        "delivery_time": 5
    }},
    "product_name_2": {{
        "price": 8.30
    }}
}}

Si aucune information pertinente n'est trouvée, retourne un objet JSON vide: {{}}

Réponds UNIQUEMENT avec le JSON, sans texte additionnel."""

        return prompt
    
    def _parse_claude_response(
        self, 
        response: str, 
        supplier_name: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Parse Claude's response into the expected format.
        
        Args:
            response: Raw response from Claude
            supplier_name: Supplier name to append to product names
            
        Returns:
            Formatted dictionary with product updates
        """
        import json
        import re
        
        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
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
            
            if "price" in updates:
                try:
                    price = float(updates["price"])
                    if price > 0:
                        cleaned_updates["price"] = price
                except (ValueError, TypeError):
                    pass
            
            if "delivery_time" in updates:
                try:
                    delivery_time = int(updates["delivery_time"])
                    if 1 <= delivery_time <= 14:
                        cleaned_updates["delivery_time"] = delivery_time
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
    Bonjour, c'est la pharmacie Martin à l'appareil.
    
    Oui bonjour, que puis-je faire pour vous ?
    
    Je voulais avoir des informations sur vos produits. 
    Pour le Paracétamol 500mg, quel est votre meilleur prix ?
    
    Nous pouvons vous le proposer à 3.50 euros l'unité.
    
    D'accord, et pour le délai de livraison ?
    
    On peut vous livrer en 7 jours.
    
    Parfait. Et pour l'Ibuprofène 400mg ?
    
    L'Ibuprofène 400mg est à 5.20 euros, livraison en 5 jours.
    
    Très bien, merci pour ces informations.
    """
    
    # Initialize parser (you would need to set ANTHROPIC_API_KEY env variable)
    try:
        parser = ConversationParser()
        result = parser.parse_conversation(
            transcript=example_transcript,
            supplier_name="Pharma Depot"
        )
        print("Parsed result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set ANTHROPIC_API_KEY environment variable")
