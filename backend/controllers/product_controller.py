"""Product controller for innovative products endpoints."""

from fastapi import APIRouter

from backend.services.inventory_service import InventoryService
from backend.services.models import (
    InnovativeProductsResponse,
    InventoryProductsResponse,
    PurchaseOrdersResponse,
    SupplierOptionsResponse,
)
from backend.services.product_discovery_service import ProductDiscoveryService

router = APIRouter(prefix="/api/products", tags=["products"])

# Initialize services
product_service = ProductDiscoveryService()
inventory_service = InventoryService()


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


@router.get("/in-store", response_model=InventoryProductsResponse)
async def get_in_store_products():
    """
    Get all in-store products with enriched inventory information.

    Returns:
        List of in-store products with supplier info, prices, margins, and stock status
    """
    products = inventory_service.get_in_store_products_enriched()
    return InventoryProductsResponse(products=products, total_count=len(products))


@router.get("/orders", response_model=PurchaseOrdersResponse)
async def get_active_orders():
    """
    Get all active purchase orders.

    Returns:
        List of active purchase orders with status and delivery information
    """
    orders = inventory_service.get_active_orders()
    return PurchaseOrdersResponse(orders=orders, total_count=len(orders))


@router.get("/{product_id}/suppliers", response_model=SupplierOptionsResponse)
async def get_product_suppliers(product_id: str):
    """
    Get all available suppliers for a specific product.

    Args:
        product_id: Product ID

    Returns:
        List of suppliers offering this product with prices and ratings
    """
    result = inventory_service.get_product_suppliers(product_id)
    return SupplierOptionsResponse(
        suppliers=result["suppliers"],
        current_supplier_id=result["current_supplier_id"],
    )
