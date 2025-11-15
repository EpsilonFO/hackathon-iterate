"""Simple test for the parser pipeline: parse transcript -> update CSV (including new products)."""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from dotenv import load_dotenv

from backend.services.transcript_parser_service import TranscriptParserService

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory with sample CSV files."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "data"
    data_dir.mkdir()

    # Create sample fournisseurs CSV
    fournisseurs_df = pd.DataFrame(
        {
            "id": ["supp_1", "supp_2"],
            "name": ["Supplier A", "Supplier B"],
            "phone_number": ["+33 1 23 45 67 89", "+33 1 23 45 67 90"],
        }
    )
    fournisseurs_df.to_csv(data_dir / "fournisseur.csv", index=False)

    # Create sample available products CSV (one existing product)
    available_products_df = pd.DataFrame(
        {
            "id": ["prod_1"],
            "name": ["Paracétamol 500mg"],
            "fournisseur": ["supp_1"],
            "price": [10.0],
            "delivery_time": [5],
            "last_information_update": ["2025-01-01 10:00:00"],
        }
    )
    available_products_df.to_csv(data_dir / "available_product.csv", index=False)

    return data_dir


def test_parser_pipeline_update_existing_and_add_new(temp_data_dir):
    """Test the full pipeline: parse transcript, find products, update CSV (existing + new products)."""

    # Initialize parser with temp data directory
    parser = TranscriptParserService(
        api_key=api_key,
        data_dir=temp_data_dir,
    )

    # Sample transcript
    transcript = """
    Pharmacie: Bonjour, je voudrais mettre à jour nos tarifs.
    Fournisseur: Bonjour ! Je vous écoute.
    Pharmacie: Pour le Paracétamol 500mg, quel est votre nouveau prix ?
    Fournisseur: Le Paracétamol 500mg est maintenant à 12.50 euros.
    Pharmacie: Et le délai de livraison ?
    Fournisseur: 7 jours pour ce produit.
    Pharmacie: Parfait. Et pour l'Ibuprofène 400mg ?
    Fournisseur: L'Ibuprofène 400mg est à 8.30 euros, livraison en 3 jours.
    """

    supplier_name = "Supplier A"

    # Run the full pipeline
    modified_products = parser.parse_and_update_csv(
        transcript=transcript,
        supplier_name=supplier_name,
        save=True,
    )

    # Verify results
    assert len(modified_products) == 2

    # Check that Paracétamol was found (existing product)
    paracetamol = next(
        (p for p in modified_products if p.product_name == "Paracétamol 500mg"),
        None,
    )
    assert paracetamol is not None
    assert paracetamol.new_price == 12.50
    assert paracetamol.new_delivery_time == 7
    assert paracetamol.product_id == "prod_1"  # Should match existing product
    assert paracetamol.fournisseur_id == "supp_1"  # Should match Supplier A

    # Check that Ibuprofène was found (new product)
    ibuprofene = next(
        (p for p in modified_products if p.product_name == "Ibuprofène 400mg"), None
    )
    assert ibuprofene is not None
    assert ibuprofene.new_price == 8.30
    assert ibuprofene.new_delivery_time == 3
    assert ibuprofene.fournisseur_id == "supp_1"  # Should match Supplier A
    # New product should have a generated product_id
    assert ibuprofene.product_id is not None
    assert ibuprofene.product_id.startswith("prod_")

    # Verify CSV was updated
    updated_df = pd.read_csv(temp_data_dir / "available_product.csv")

    # Check existing product was updated
    paracetamol_row = updated_df[
        (updated_df.name == "Paracétamol 500mg") & (updated_df.fournisseur == "supp_1")
    ]
    assert len(paracetamol_row) == 1
    assert paracetamol_row.iloc[0]["price"] == 12.50
    assert paracetamol_row.iloc[0]["delivery_time"] == 7

    # Check new product was added
    ibuprofene_row = updated_df[
        (updated_df.name == "Ibuprofène 400mg") & (updated_df.fournisseur == "supp_1")
    ]
    assert len(ibuprofene_row) == 1
    assert ibuprofene_row.iloc[0]["price"] == 8.30
    assert ibuprofene_row.iloc[0]["delivery_time"] == 3

    # Verify total number of rows increased
    assert len(updated_df) == 2  # Original 1 + new 1
