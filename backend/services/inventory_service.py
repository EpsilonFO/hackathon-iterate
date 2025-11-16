"""Service for inventory and order management."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd

from backend.services.data_loader import get_data_loader


class InventoryService:
    """Service for managing inventory products and orders."""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the inventory service.

        Args:
            data_dir: Path to the data directory.
        """
        self.data_loader = get_data_loader(data_dir)

    def get_in_store_products_enriched(self) -> List[dict]:
        """
        Get in-store products enriched with supplier info, best prices, and margins.

        Returns:
            List of enriched product dictionaries
        """
        in_store_products = self.data_loader.load_in_store_products_models()
        available_products = self.data_loader.load_available_products_models()
        fournisseurs = self.data_loader.load_fournisseurs_models()

        # Create lookups
        fournisseurs_dict = {f.id: f for f in fournisseurs}
        available_by_product_id = {}
        for avail in available_products:
            if avail.id not in available_by_product_id:
                available_by_product_id[avail.id] = []
            available_by_product_id[avail.id].append(avail)

        # Get set of in-store product names for comparison (normalized: lowercase, stripped)
        in_store_product_names = {p.name.strip().lower() for p in in_store_products}

        enriched_products = []

        # Process in-store products (these are "in-house")
        for product in in_store_products:
            # Get supplier info
            supplier = fournisseurs_dict.get(product.fournisseur_id)
            supplier_name = supplier.name if supplier else "Unknown Supplier"

            # Get all available options for this product (by product ID)
            available_options = available_by_product_id.get(product.id, [])

            # Find current supplier's delivery time
            current_delivery_time = None
            for avail in available_options:
                if avail.fournisseur == product.fournisseur_id:
                    current_delivery_time = avail.delivery_time
                    break

            # Find best price (lowest) and its supplier
            best_price = product.price
            best_price_supplier_id = product.fournisseur_id
            best_price_supplier_name = supplier_name
            best_delivery_time = current_delivery_time
            best_delivery_supplier_id = product.fournisseur_id
            best_delivery_supplier_name = supplier_name

            if available_options:
                # Find best price option
                best_price_option = min(available_options, key=lambda x: x.price)
                if best_price_option.price < product.price:
                    best_price = best_price_option.price
                    best_price_supplier = fournisseurs_dict.get(
                        best_price_option.fournisseur
                    )
                    if best_price_supplier:
                        best_price_supplier_id = best_price_option.fournisseur
                        best_price_supplier_name = best_price_supplier.name

                # Find fastest delivery option
                fastest_option = min(available_options, key=lambda x: x.delivery_time)
                if fastest_option.delivery_time < (current_delivery_time or 14):
                    best_delivery_time = fastest_option.delivery_time
                    best_delivery_supplier = fournisseurs_dict.get(
                        fastest_option.fournisseur
                    )
                    if best_delivery_supplier:
                        best_delivery_supplier_id = fastest_option.fournisseur
                        best_delivery_supplier_name = best_delivery_supplier.name

            # Calculate margins (assuming a standard markup of 50% for sell price)
            # This is a simplified calculation - in real app, sell price would come from data
            sell_price = product.price * 1.5  # 50% markup
            current_margin = ((sell_price - product.price) / sell_price) * 100
            best_margin = ((sell_price - best_price) / sell_price) * 100

            # Determine if improvements are possible
            margin_improvement_possible = (
                best_margin > current_margin + 0.5
            )  # At least 0.5% improvement
            delivery_improvement_possible = (
                best_delivery_time is not None
                and current_delivery_time is not None
                and best_delivery_time < current_delivery_time
            )

            # Check if same supplier has both best price and delivery
            dual_improvement_same_supplier = (
                best_price_supplier_id == best_delivery_supplier_id
                and best_price_supplier_id != product.fournisseur_id
                and margin_improvement_possible
                and delivery_improvement_possible
            )

            # Determine product type (in-house vs external)
            # Products in in_store_products are "in-house"
            product_type = "in-house"

            # Estimate weekly use based on stock (simplified: assume 4 weeks supply)
            weekly_use = max(1, product.stock // 4) if product.stock > 0 else 10

            # Estimate stockout date (simplified calculation)
            days_until_stockout = (
                (product.stock / weekly_use * 7) if weekly_use > 0 else 0
            )
            stockout_date = (
                (datetime.now() + timedelta(days=int(days_until_stockout))).strftime(
                    "%Y-%m-%d"
                )
                if days_until_stockout > 0
                else "N/A"
            )

            # Determine status
            if product.stock == 0:
                status = "critical"
            elif product.stock < weekly_use * 2:  # Less than 2 weeks supply
                status = "critical"
            elif product.stock < weekly_use * 4:  # Less than 4 weeks supply
                status = "low"
            else:
                status = "healthy"

            enriched_products.append(
                {
                    "id": product.id,
                    "sku": product.id[:8].upper(),  # Generate SKU from ID
                    "name": product.name,
                    "category": "General",  # Default category - could be enriched from data
                    "supplier": supplier_name,
                    "supplier_id": product.fournisseur_id,
                    "type": product_type,
                    "currentPrice": round(product.price, 2),
                    "currentPriceSupplier": supplier_name,
                    "bestPrice": round(best_price, 2),
                    "bestPriceSupplier": best_price_supplier_name,
                    "bestPriceSupplierId": best_price_supplier_id,
                    "sellPrice": round(sell_price, 2),
                    "currentMargin": round(current_margin, 1),
                    "bestMargin": round(best_margin, 1),
                    "currentDeliveryTime": current_delivery_time,
                    "currentDeliverySupplier": supplier_name,
                    "bestDeliveryTime": best_delivery_time,
                    "bestDeliverySupplier": best_delivery_supplier_name,
                    "bestDeliverySupplierId": best_delivery_supplier_id,
                    "marginImprovementPossible": margin_improvement_possible,
                    "deliveryImprovementPossible": delivery_improvement_possible,
                    "dualImprovementSameSupplier": dual_improvement_same_supplier,
                    "stock": product.stock,
                    "weeklyUse": weekly_use,
                    "stockoutDate": stockout_date,
                    "status": status,
                }
            )

        # Process available products that are NOT in store (these are "external"/new products)
        # Group available products by name to find unique products (normalized: lowercase, stripped)
        available_by_name = {}
        for avail in available_products:
            normalized_name = avail.name.strip().lower()
            if normalized_name not in available_by_name:
                available_by_name[normalized_name] = []
            available_by_name[normalized_name].append(avail)

        # Find products available from suppliers but not in store
        external_count = 0
        for normalized_name, product_entries in available_by_name.items():
            if normalized_name not in in_store_product_names:
                external_count += 1
                # Get the original name from the first entry
                product_name = product_entries[0].name
                # This is a new product (external) - not in store yet
                # Find best price and fastest delivery
                best_price_option = min(product_entries, key=lambda x: x.price)
                fastest_option = min(product_entries, key=lambda x: x.delivery_time)

                best_price = best_price_option.price
                best_price_supplier = fournisseurs_dict.get(
                    best_price_option.fournisseur
                )
                best_price_supplier_name = (
                    best_price_supplier.name
                    if best_price_supplier
                    else "Unknown Supplier"
                )
                best_price_supplier_id = best_price_option.fournisseur

                best_delivery_time = fastest_option.delivery_time
                best_delivery_supplier = fournisseurs_dict.get(
                    fastest_option.fournisseur
                )
                best_delivery_supplier_name = (
                    best_delivery_supplier.name
                    if best_delivery_supplier
                    else "Unknown Supplier"
                )
                best_delivery_supplier_id = fastest_option.fournisseur

                # Use first product ID from available products for this name
                product_id = product_entries[0].id

                # Calculate margin (assuming 50% markup)
                sell_price = best_price * 1.5
                best_margin = ((sell_price - best_price) / sell_price) * 100

                # For external products, no improvements are possible (no baseline to compare)
                # But we can note if same supplier has both best price and delivery for reference
                # (not used for improvement badges, just informational)

                enriched_products.append(
                    {
                        "id": product_id,
                        "sku": product_id[:8].upper(),
                        "name": product_name,
                        "category": "General",
                        "supplier": best_price_supplier_name,  # Best supplier as default
                        "supplier_id": best_price_supplier_id,
                        "type": "external",  # New product, not in store
                        "currentPrice": 0,  # Not purchased yet
                        "currentPriceSupplier": "N/A",
                        "bestPrice": round(best_price, 2),
                        "bestPriceSupplier": best_price_supplier_name,
                        "bestPriceSupplierId": best_price_supplier_id,
                        "sellPrice": round(sell_price, 2),
                        "currentMargin": 0,  # No current margin (not purchased)
                        "bestMargin": round(best_margin, 1),
                        "currentDeliveryTime": None,  # No current delivery time
                        "currentDeliverySupplier": "N/A",
                        "bestDeliveryTime": best_delivery_time,
                        "bestDeliverySupplier": best_delivery_supplier_name,
                        "bestDeliverySupplierId": best_delivery_supplier_id,
                        "marginImprovementPossible": False,  # Can't improve if not purchased
                        "deliveryImprovementPossible": False,  # Can't improve if not purchased
                        "dualImprovementSameSupplier": False,  # No improvements for external products
                        "stock": 0,  # No stock (not in store)
                        "weeklyUse": 0,  # No usage data
                        "stockoutDate": "N/A",
                        "status": "healthy",  # Default status
                    }
                )

        # Debug: print count of external products found
        print(f"DEBUG: Found {external_count} external products (not in store)")
        print(f"DEBUG: Total enriched products: {len(enriched_products)}")

        return enriched_products

    def get_active_orders(self) -> List[dict]:
        """
        Get active purchase orders.

        Returns:
            List of order dictionaries
        """
        orders_df = self.data_loader.load_orders()
        fournisseurs = self.data_loader.load_fournisseurs_models()
        fournisseurs_dict = {f.id: f for f in fournisseurs}

        active_orders = []

        for _, row in orders_df.iterrows():
            # Check if order is active (not delivered or delivery date in future)
            estimated_delivery = datetime.strptime(
                row["estimated_time_arrival"], "%Y-%m-%d %H:%M:%S"
            )
            actual_delivery = (
                datetime.strptime(row["time_of_arrival"], "%Y-%m-%d %H:%M:%S")
                if pd.notna(row["time_of_arrival"])
                else None
            )

            # Order is active if not delivered yet (actual_delivery is None)
            is_active = actual_delivery is None

            if is_active:
                supplier = fournisseurs_dict.get(row["fournisseur_id"])
                supplier_name = supplier.name if supplier else "Unknown Supplier"

                # Determine status
                if actual_delivery:
                    if actual_delivery <= estimated_delivery:
                        status = "on_track"
                    else:
                        status = "delayed"
                else:
                    # Check if estimated delivery has passed
                    if estimated_delivery < datetime.now():
                        status = "delayed"
                    else:
                        # Check if we have ETA
                        status = (
                            "pending"
                            if pd.notna(row["estimated_time_arrival"])
                            else "pending"
                        )

                active_orders.append(
                    {
                        "order_id": row["order_id"],
                        "product_name": row["product_name"],
                        "quantity": int(row["quantity"]),
                        "supplier_name": supplier_name,
                        "estimated_delivery": row["estimated_time_arrival"],
                        "actual_delivery": (
                            row["time_of_arrival"]
                            if pd.notna(row["time_of_arrival"])
                            else None
                        ),
                        "status": status,
                        "order_date": row["order_date"],
                    }
                )

        return active_orders

    def get_product_suppliers(self, product_id: str) -> dict:
        """
        Get all available suppliers for a product.

        Args:
            product_id: Product ID

        Returns:
            Dictionary with suppliers list and current supplier ID
        """
        available_products = self.data_loader.load_available_products_models()
        in_store_products = self.data_loader.load_in_store_products_models()
        fournisseurs = self.data_loader.load_fournisseurs_models()

        # Find current supplier from in-store products
        current_supplier_id = None
        for product in in_store_products:
            if product.id == product_id:
                current_supplier_id = product.fournisseur_id
                break

        # Get all suppliers offering this product
        fournisseurs_dict = {f.id: f for f in fournisseurs}
        suppliers_list = []

        # Get all available options for this product
        for avail in available_products:
            if avail.id == product_id:
                supplier = fournisseurs_dict.get(avail.fournisseur)
                if supplier:
                    # Calculate rating (simplified: based on price competitiveness)
                    # In real app, this would come from historical data
                    base_rating = 75
                    if avail.price < 50:
                        rating = min(100, base_rating + 15)
                    elif avail.price < 100:
                        rating = base_rating
                    else:
                        rating = max(50, base_rating - 15)

                    # Format delivery time
                    delivery_time_str = (
                        f"{avail.delivery_time}-{avail.delivery_time + 2} days"
                    )

                    suppliers_list.append(
                        {
                            "id": supplier.id,
                            "name": supplier.name,
                            "price": round(avail.price, 2),
                            "delivery_time": delivery_time_str,
                            "rating": rating,
                            "phone": supplier.phone_number,
                        }
                    )

        return {
            "suppliers": suppliers_list,
            "current_supplier_id": current_supplier_id,
        }
