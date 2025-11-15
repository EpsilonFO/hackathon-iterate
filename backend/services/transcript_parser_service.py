"""Service for parsing phone conversation transcripts to update product information."""

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import anthropic
import pandas as pd
from dotenv import load_dotenv

from backend.services.data_loader import get_data_loader
from backend.services.models import ModifiedProductInformation

load_dotenv()


class TranscriptParserService:
    """
    Parses phone conversation transcripts to extract product price and delivery time updates,
    and optionally updates CSV files with the parsed information.

    This class uses Claude API from Anthropic to analyze conversation transcripts
    and extract structured product information updates. It can also convert parsed
    results to ModifiedProductInformation format and update CSV files.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        data_dir: Optional[Path] = None,
    ):
        """
        Initialize the conversation parser with Claude API.

        Args:
            api_key: Anthropic API key. If not provided, will use ANTHROPIC_API_KEY env variable.
            data_dir: Path to the data directory. If None, uses ../data relative to this file.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided either as parameter or ANTHROPIC_API_KEY environment variable"
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Initialize data directory and loader for CSV operations
        if data_dir is None:
            backend_dir = Path(__file__).parent.parent
            data_dir = backend_dir.parent / "data"
        self.data_dir = Path(data_dir)
        self.data_loader = get_data_loader(self.data_dir)

        # Store dataframes for CSV operations (will be loaded when needed)
        self._available_products = None
        self._fournisseurs = None

    def _parse_json_transcript(self, json_input: Union[str, Path, Dict]) -> Dict:
        """
        Parse JSON transcript from file path, JSON string, or dict.

        Args:
            json_input: Can be a file path (str or Path), JSON string, or dict

        Returns:
            Parsed JSON dictionary
        """
        if isinstance(json_input, dict):
            return json_input
        elif isinstance(json_input, (str, Path)):
            path = Path(json_input)
            if path.exists():
                # It's a file path
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # Try to parse as JSON string
                try:
                    return json.loads(json_input)
                except json.JSONDecodeError:
                    raise ValueError(
                        f"Could not parse JSON from string or file: {json_input}"
                    )
        else:
            raise ValueError(
                f"Unsupported input type for JSON transcript: {type(json_input)}"
            )

    def _json_to_transcript(self, json_data: Dict) -> str:
        """
        Convert JSON transcript format to a formatted text transcript.

        Args:
            json_data: Dictionary with 'messages' array containing 'role' and 'text' fields

        Returns:
            Formatted transcript string
        """
        if "messages" not in json_data:
            raise ValueError("JSON transcript must contain a 'messages' field")

        messages = json_data["messages"]
        transcript_lines = []

        for msg in messages:
            role = msg.get("role", "unknown")
            text = msg.get("text", "")

            # Map roles to French labels for consistency
            if role == "agent":
                label = "Pharmacie"
            elif role == "user":
                label = "Fournisseur"
            else:
                label = role.capitalize()

            transcript_lines.append(f"{label}: {text}")

        return "\n".join(transcript_lines)

    def _normalize_transcript(self, transcript: Union[str, Path, Dict]) -> str:
        """
        Normalize transcript input to a string format.

        Args:
            transcript: Can be a string, file path, or JSON dict/string

        Returns:
            Normalized transcript string
        """
        if isinstance(transcript, str):
            # Check if it's a JSON string or file path
            transcript_stripped = transcript.strip()
            if transcript_stripped.startswith("{") or transcript_stripped.startswith(
                "["
            ):
                # It's a JSON string
                json_data = self._parse_json_transcript(transcript)
                return self._json_to_transcript(json_data)
            else:
                # Check if it's a file path
                path = Path(transcript)
                if path.exists() and path.suffix == ".json":
                    json_data = self._parse_json_transcript(path)
                    return self._json_to_transcript(json_data)
                else:
                    # It's a plain text transcript
                    return transcript
        elif isinstance(transcript, Path):
            # It's a file path
            if transcript.suffix == ".json":
                json_data = self._parse_json_transcript(transcript)
                return self._json_to_transcript(json_data)
            else:
                # Read as plain text
                with open(transcript, "r", encoding="utf-8") as f:
                    return f.read()
        elif isinstance(transcript, dict):
            # It's a JSON dict
            return self._json_to_transcript(transcript)
        else:
            raise ValueError(
                f"Unsupported transcript type: {type(transcript)}. "
                "Expected str, Path, or dict."
            )

    def parse_conversation(
        self, transcript: Union[str, Path, Dict], supplier_name: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Parse a phone conversation transcript to extract product updates.

        Args:
            transcript: The transcript can be:
                - A plain text string
                - A JSON string with messages array
                - A file path (str or Path) to a JSON or text file
                - A dictionary with 'messages' array containing 'role' and 'text' fields
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
        # Normalize transcript to string format
        normalized_transcript = self._normalize_transcript(transcript)
        print(normalized_transcript)

        prompt = self._build_prompt(normalized_transcript, supplier_name)
        print(prompt)

        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract the response text
            response_text = message.content[0].text
            print(response_text)
            # Parse the structured response
            result = self._parse_claude_response(response_text, supplier_name)
            print(result)
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
        prompt = f"""
Tu es un assistant spécialisé dans l'analyse de conversations téléphoniques entre pharmacies et fournisseurs.

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
        self, response: str, supplier_name: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Parse Claude's response into the expected format.

        Args:
            response: Raw response from Claude
            supplier_name: Supplier name to append to product names

        Returns:
            Formatted dictionary with product updates
        """
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

    def parse_to_modified_products(
        self,
        parsed_updates: Dict[str, Dict[str, float]],
    ) -> List[ModifiedProductInformation]:
        """
        Convert parsed updates dictionary to a list of ModifiedProductInformation objects.

        Args:
            parsed_updates: Dictionary with keys in format "[product_name, supplier_name]"
                          and values containing 'price' and/or 'delivery_time' fields.

        Returns:
            List of ModifiedProductInformation objects
        """
        modified_products = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for product_supplier_key, updates in parsed_updates.items():
            # Parse the key "[product_name, supplier_name]"
            if not product_supplier_key.startswith(
                "["
            ) or not product_supplier_key.endswith("]"):
                continue

            content = product_supplier_key[1:-1]
            parts = content.split(", ", 1)

            if len(parts) != 2:
                continue

            product_name = parts[0]
            supplier_name = parts[1]

            # Create ModifiedProductInformation object
            modified_product = ModifiedProductInformation(
                product_name=product_name,
                fournisseur_name=supplier_name,
                new_last_information_update=current_time,
                new_price=updates.get("price"),
                new_delivery_time=updates.get("delivery_time"),
            )

            modified_products.append(modified_product)

        return modified_products

    def _load_dataframes(self):
        """Load and cache dataframes for CSV operations."""
        if self._available_products is None:
            self._available_products = self.data_loader.load_available_products()
        if self._fournisseurs is None:
            self._fournisseurs = self.data_loader.load_fournisseurs()

    def prepare_product_information(
        self,
        modified_products: List[ModifiedProductInformation],
    ) -> None:
        """
        Prepare product information by matching product and supplier IDs.

        Args:
            modified_products: List of ModifiedProductInformation objects to prepare
        """
        self._load_dataframes()

        for product in modified_products:
            # Match product ID
            product_match = self._available_products[
                self._available_products.name == product.product_name
            ]
            if len(product_match) > 0:
                product.product_id = product_match.iloc[0]["id"]

            # Match supplier ID
            supplier_match = self._fournisseurs[
                self._fournisseurs.name == product.fournisseur_name
            ]
            if len(supplier_match) > 0:
                product.fournisseur_id = supplier_match.iloc[0]["id"]

    def update_product_information(
        self,
        modified_products: List[ModifiedProductInformation],
    ) -> None:
        """
        Update product information in the loaded CSV data.

        Args:
            modified_products: List of ModifiedProductInformation objects with IDs set
        """
        self._load_dataframes()

        for product in modified_products:
            if product.product_id and product.fournisseur_id:
                # Select the row matching both product_id and fournisseur_id
                # Note: CSV uses 'fournisseur' column, not 'fournisseur_id'
                mask = (self._available_products.id == product.product_id) & (
                    self._available_products.fournisseur == product.fournisseur_id
                )

                # Check if row exists
                if mask.any():
                    # Update existing row
                    if product.new_price is not None:
                        self._available_products.loc[mask, "price"] = product.new_price

                    if product.new_delivery_time is not None:
                        self._available_products.loc[mask, "delivery_time"] = (
                            product.new_delivery_time
                        )

                    self._available_products.loc[mask, "last_information_update"] = (
                        product.new_last_information_update
                    )
                else:
                    # Product exists but not with this supplier - add new row
                    new_row = {
                        "id": product.product_id,
                        "name": product.product_name,
                        "fournisseur": product.fournisseur_id,
                        "price": product.new_price,
                        "delivery_time": product.new_delivery_time,
                        "last_information_update": product.new_last_information_update,
                    }
                    self._available_products = pd.concat(
                        [self._available_products, pd.DataFrame([new_row])],
                        ignore_index=True,
                    )
            elif product.fournisseur_id:
                # New product - need to generate product ID
                # Check if product name already exists to reuse ID
                existing_product = self._available_products[
                    self._available_products.name == product.product_name
                ]
                if len(existing_product) > 0:
                    product_id = existing_product.iloc[0]["id"]
                else:
                    product_id = f"prod_{uuid.uuid4()}"

                # Update the ModifiedProductInformation object with the generated ID
                product.product_id = product_id

                # Add new product row
                new_row = {
                    "id": product_id,
                    "name": product.product_name,
                    "fournisseur": product.fournisseur_id,
                    "price": product.new_price,
                    "delivery_time": product.new_delivery_time,
                    "last_information_update": product.new_last_information_update,
                }
                self._available_products = pd.concat(
                    [self._available_products, pd.DataFrame([new_row])],
                    ignore_index=True,
                )

    def save_to_csv(self) -> None:
        """Save modified product information to CSV."""
        self._load_dataframes()
        self._available_products.to_csv(
            self.data_dir / "available_product.csv", index=False
        )

    def parse_and_update_csv(
        self,
        transcript: Union[str, Path, Dict],
        supplier_name: str,
        save: bool = False,
    ) -> List[ModifiedProductInformation]:
        """
        Parse a conversation transcript and update the CSV file.

        This is a convenience method that combines parsing, conversion, and CSV update.

        Args:
            transcript: The transcript can be:
                - A plain text string
                - A JSON string with messages array
                - A file path (str or Path) to a JSON or text file
                - A dictionary with 'messages' array containing 'role' and 'text' fields
            supplier_name: The name of the supplier involved in the conversation
            save: If True, save the updated data to CSV file

        Returns:
            List of ModifiedProductInformation objects that were processed
        """
        # Parse the conversation
        parsed_updates = self.parse_conversation(transcript, supplier_name)
        # Convert to ModifiedProductInformation format
        modified_products = self.parse_to_modified_products(parsed_updates)
        # Prepare product information (match IDs)
        self.prepare_product_information(modified_products)
        # Update product information
        self.update_product_information(modified_products)
        # Save to CSV if requested
        if save:
            self.save_to_csv()

        return modified_products
