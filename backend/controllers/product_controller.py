"""Product controller for innovative products endpoints."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from backend.services.data_loader import get_data_loader
from backend.services.models import (
    InnovativeProductsResponse,
    Order,
)
from backend.services.product_discovery_service import ProductDiscoveryService

router = APIRouter(prefix="/api/products", tags=["products"])

# Initialize services
product_service = ProductDiscoveryService()
data_loader = get_data_loader()


@router.get("/innovative", response_model=InnovativeProductsResponse)
async def get_innovative_products(min_suppliers: int = 1, sort_by: str = "suppliers"):
    """
    Get list of innovative products not currently in store.

    Args:
        min_suppliers: Minimum number of suppliers required (default: 1)
        sort_by: Sort criteria - 'price', 'suppliers', or 'delivery_time' (default: 'suppliers')

    Returns:
        List of innovative products with supplier information
    """
    if sort_by not in ["price", "suppliers", "delivery_time"]:
        sort_by = "suppliers"

    products = product_service.find_innovative_products(
        min_suppliers=min_suppliers, sort_by=sort_by
    )

    return InnovativeProductsResponse(
        products=products, total_count=len(products), min_suppliers=min_suppliers
    )


@router.get("/in-store")
async def get_in_store_products():
    """
    Get all in-store products with inventory information.

    Returns:
        List of in-store products with calculated stock status
    """
    try:
        in_store_products = data_loader.load_in_store_products_models()
        fournisseurs = data_loader.load_fournisseurs_models()
        orders = _load_orders()

        # Create supplier lookup
        fournisseurs_dict = {f.id: f for f in fournisseurs}

        # Group orders by product name for weekly use estimation
        orders_by_product = {}
        for order in orders:
            if order.product_name not in orders_by_product:
                orders_by_product[order.product_name] = []
            orders_by_product[order.product_name].append(order)

        result = []
        for product in in_store_products:
            supplier = fournisseurs_dict.get(product.fournisseur_id)

            # Estimate weekly use from orders
            product_orders = orders_by_product.get(product.name, [])
            weekly_use = _estimate_weekly_use(product.stock, product_orders)

            # Calculate stockout date and status
            stockout_date = _calculate_stockout_date(product.stock, weekly_use)
            status = _calculate_status(product.stock, weekly_use)

            # Generate SKU from product ID
            sku = product.id[:8].upper().replace("-", "")

            result.append(
                {
                    "id": product.id,
                    "sku": sku,
                    "name": product.name,
                    "category": "General",  # Could be enhanced with actual category data
                    "stock": product.stock,
                    "weekly_use": weekly_use,
                    "stockout_date": stockout_date,
                    "status": status,
                    "supplier": supplier.name if supplier else "Unknown",
                    "supplier_id": product.fournisseur_id,
                    "price": product.price,
                }
            )
        return {"products": result, "total_count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading products: {str(e)}")


@router.get("/orders")
async def get_orders():
    """
    Get all active purchase orders.

    Returns:
        List of active purchase orders
    """
    orders = _load_orders()
    fournisseurs = data_loader.load_fournisseurs_models()
    fournisseurs_dict = {f.id: f for f in fournisseurs}
    active_orders = []
    for order in orders:
        # Only include orders that haven't been delivered or are recent
        if order.time_of_arrival:
            # Skip delivered orders older than 7 days
            try:
                delivery_date = datetime.fromisoformat(
                    order.time_of_arrival.replace(" ", "T")
                )
                if (datetime.now() - delivery_date).days > 7:
                    continue
            except (ValueError, AttributeError):
                pass
        else:
            # Include pending orders
            pass

        supplier = fournisseurs_dict.get(order.fournisseur_id)
        supplier_name = supplier.name if supplier else "Unknown"

        # Determine status
        if order.time_of_arrival:
            status = "on_track"
        elif order.estimated_time_arrival:
            try:
                eta = datetime.fromisoformat(
                    order.estimated_time_arrival.replace(" ", "T")
                )
                if eta < datetime.now():
                    status = "delayed"
                else:
                    status = "pending"
            except (ValueError, AttributeError):
                status = "pending"
        else:
            status = "pending"

        active_orders.append(
            {
                "order_id": order.order_id,
                "product_name": order.product_name,
                "quantity": order.quantity,
                "supplier_name": supplier_name,
                "estimated_delivery": order.estimated_time_arrival,
                "actual_delivery": order.time_of_arrival,
                "status": status,
                "order_date": order.order_date,
            }
        )

    # Sort by order date (most recent first)
    active_orders.sort(key=lambda x: x["order_date"], reverse=True)

    return {
        "orders": active_orders[:10],
        "total_count": len(active_orders),
    }  # Return top 10 most recent


@router.get("/{product_id}/suppliers")
async def get_product_suppliers(product_id: str):
    """
    Get all available suppliers for a specific product.

    Args:
        product_id: Product ID

    Returns:
        List of supplier options with pricing
    """
    try:
        in_store_products = data_loader.load_in_store_products_models()
        available_products = data_loader.load_available_products_models()
        fournisseurs = data_loader.load_fournisseurs_models()

        # Find product
        product = next((p for p in in_store_products if p.id == product_id), None)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Find all available products with same name
        matching_available = [
            ap for ap in available_products if ap.name == product.name
        ]

        # Create supplier lookup
        fournisseurs_dict = {f.id: f for f in fournisseurs}

        suppliers = []
        for avail in matching_available:
            supplier = fournisseurs_dict.get(avail.fournisseur)
            if not supplier:
                continue

            # Calculate rating based on delivery time and price (simple heuristic)
            rating = (
                100
                - (int(avail.delivery_time) * 2)
                - int((avail.price / product.price - 1) * 50)
            )
            rating = max(50, min(100, rating))

            suppliers.append(
                {
                    "id": supplier.id,
                    "name": supplier.name,
                    "price": float(avail.price),
                    "delivery_time": f"{int(avail.delivery_time)}-{int(avail.delivery_time) + 2} days",
                    "rating": rating,
                    "phone": supplier.phone_number,
                }
            )

        # Sort by rating (descending)
        suppliers.sort(key=lambda x: x["rating"], reverse=True)

        return {"suppliers": suppliers, "current_supplier_id": product.fournisseur_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading suppliers: {str(e)}"
        )


def _load_orders() -> List[Order]:
    """Load orders from CSV file."""
    data_dir = Path(__file__).parent.parent.parent / "data"
    orders_file = data_dir / "orders.csv"
    if not orders_file.exists():
        return []

    df = pd.read_csv(orders_file)
    df["time_of_arrival"] = df["time_of_arrival"].replace(np.nan, None)
    return [Order(**row) for row in df.to_dict("records")]


def _estimate_weekly_use(stock: int, historical_orders: List[Order]) -> int:
    """Estimate weekly use based on historical orders."""
    if not historical_orders:
        return max(1, stock // 8)  # Default to 8 weeks if no history

    # Get orders from last 4 weeks
    four_weeks_ago = datetime.now() - timedelta(weeks=4)
    recent_orders = [
        o
        for o in historical_orders
        if datetime.fromisoformat(o.order_date.replace(" ", "T")) >= four_weeks_ago
    ]

    if recent_orders:
        total_quantity = sum(o.quantity for o in recent_orders)
        return max(1, total_quantity // 4)

    return max(1, stock // 8)


def _calculate_stockout_date(stock: int, weekly_use: int) -> str:
    """Calculate projected stockout date."""
    if weekly_use <= 0:
        return "N/A"
    weeks_remaining = stock / weekly_use
    stockout_date = datetime.now() + timedelta(weeks=weeks_remaining)
    return stockout_date.strftime("%Y-%m-%d")


def _calculate_status(stock: int, weekly_use: int) -> str:
    """Calculate stock status based on stock and weekly use."""
    if weekly_use <= 0:
        return "healthy"
    weeks_remaining = stock / weekly_use
    if weeks_remaining < 1:
        return "critical"
    elif weeks_remaining < 2:
        return "low"
    else:
        return "healthy"
