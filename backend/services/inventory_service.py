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

        enriched_products = []

        for product in in_store_products:
            # Get supplier info
            supplier = fournisseurs_dict.get(product.fournisseur_id)
            supplier_name = supplier.name if supplier else "Unknown Supplier"

            # Get all available options for this product (by product ID)
            available_options = available_by_product_id.get(product.id, [])

            # Find best price (lowest)
            best_price = product.price
            best_supplier_id = product.fournisseur_id
            best_supplier_name = supplier_name

            if available_options:
                best_option = min(available_options, key=lambda x: x.price)
                if best_option.price < product.price:
                    best_price = best_option.price
                    best_supplier_id = best_option.fournisseur
                    best_supplier = fournisseurs_dict.get(best_option.fournisseur)
                    if best_supplier:
                        best_supplier_name = best_supplier.name

            # Calculate margins (assuming a standard markup of 50% for sell price)
            # This is a simplified calculation - in real app, sell price would come from data
            sell_price = product.price * 1.5  # 50% markup
            current_margin = ((sell_price - product.price) / sell_price) * 100
            best_margin = ((sell_price - best_price) / sell_price) * 100

            # Determine product type (in-house vs external)
            # For now, all in-store products are "in-house"
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
                    "bestPrice": round(best_price, 2),
                    "sellPrice": round(sell_price, 2),
                    "currentMargin": round(current_margin, 1),
                    "bestMargin": round(best_margin, 1),
                    "stock": product.stock,
                    "weeklyUse": weekly_use,
                    "stockoutDate": stockout_date,
                    "status": status,
                }
            )

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
