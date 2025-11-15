#!/usr/bin/env python3
"""
Script to parse conversation transcripts and update product information.

Usage:
    python script.py <transcript_path> <supplier_name> [--save] [--data-dir DATA_DIR]
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to Python path for imports
# Script is in backend/services/, so we need to go up two levels to get to project root
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(script_dir))

from backend.services.transcript_parser_service import TranscriptParserService

load_dotenv()


def main():
    """Main function to run the transcript parser."""
    parser = argparse.ArgumentParser(
        description="Parse conversation transcripts and update product information"
    )
    parser.add_argument(
        "transcript_path",
        type=str,
        help="Path to the transcript file (JSON or text)",
    )
    parser.add_argument(
        "supplier_name",
        type=str,
        help="Name of the supplier in the conversation",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the updated product information to CSV",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Path to the data directory (default: ../data relative to backend)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Anthropic API key (default: from ANTHROPIC_API_KEY env variable)",
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Error: API key must be provided via --api-key or ANTHROPIC_API_KEY environment variable"
        )
        sys.exit(1)

    # Validate transcript path (resolve relative to current working directory)
    transcript_path = Path(args.transcript_path).resolve()
    if not transcript_path.exists():
        print(f"Error: Transcript file not found: {transcript_path}")
        sys.exit(1)

    # Initialize parser
    try:
        parser_service = TranscriptParserService(
            api_key=api_key,
            data_dir=args.data_dir,
        )
    except Exception as e:
        print(f"Error initializing parser: {e}")
        sys.exit(1)

    # Parse and update
    try:
        print(f"Parsing transcript: {transcript_path}")
        print(f"Supplier: {args.supplier_name}")
        print("-" * 50)

        modified_products = parser_service.parse_and_update_csv(
            transcript=transcript_path,
            supplier_name=args.supplier_name,
            save=args.save,
        )

        # Display results
        if not modified_products:
            print("No products found or updated in the transcript.")
        else:
            print(f"\nFound {len(modified_products)} product(s) to update:\n")
            for i, product in enumerate(modified_products, 1):
                print(f"{i}. {product.product_name}")
                if product.product_id:
                    print(f"   Product ID: {product.product_id}")
                if product.fournisseur_id:
                    print(f"   Supplier ID: {product.fournisseur_id}")
                if product.new_price is not None:
                    print(f"   Price: {product.new_price} euros")
                if product.new_delivery_time is not None:
                    print(f"   Delivery time: {product.new_delivery_time} days")
                print()

        if args.save:
            print("✓ Product information saved to CSV")
        else:
            print("Note: Use --save flag to persist changes to CSV")

    except Exception as e:
        print(f"Error parsing transcript: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
