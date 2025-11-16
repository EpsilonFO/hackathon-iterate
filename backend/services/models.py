"""Pydantic models for data structures."""

from typing import List, Optional

from pydantic import BaseModel, Field


class Fournisseur(BaseModel):
    """Supplier model."""

    id: str
    name: str
    phone_number: str


class InStoreProduct(BaseModel):
    """In-store product model."""

    id: str
    name: str
    price: float
    fournisseur_id: str
    stock: int


class AvailableProduct(BaseModel):
    """Available product from supplier model."""

    id: str
    name: str
    fournisseur: str
    price: float
    delivery_time: int = Field(ge=1, le=14, description="Delivery time in days")
    last_information_update: str


class SupplierInfo(BaseModel):
    """Supplier information for responses."""

    id: str
    name: str
    phone: str


class CheaperAlternative(BaseModel):
    """Model for cheaper supplier alternative."""

    product_id: str
    product_name: str
    current_price: float
    current_supplier_id: str
    current_supplier_name: str
    current_stock: int
    alternative_supplier_id: str
    alternative_supplier_name: str
    alternative_supplier_phone: str
    alternative_price: float
    savings_amount: float
    savings_percent: float = Field(ge=0, description="Savings percentage")
    delivery_time: int
    last_information_update: str


class InnovativeProduct(BaseModel):
    """Model for innovative product not in store."""

    product_name: str
    supplier_count: int = Field(ge=1, description="Number of suppliers")
    avg_price: float
    min_price: float
    max_price: float
    min_delivery_time: int
    avg_delivery_time: float
    suppliers: List[SupplierInfo]


class CheaperAlternativesResponse(BaseModel):
    """Response model for cheaper alternatives endpoint."""

    alternatives: List[CheaperAlternative]
    total_count: int
    min_savings_percent: float


class InnovativeProductsResponse(BaseModel):
    """Response model for innovative products endpoint."""

    products: List[InnovativeProduct]
    total_count: int
    min_suppliers: int


class ModifiedProductInformation(BaseModel):
    """Model for modified product information."""

    product_name: str
    fournisseur_name: str
    new_last_information_update: str
    product_id: str | None = None
    fournisseur_id: str | None = None
    new_price: float | None = None
    new_delivery_time: int | None = None


class Order(BaseModel):
    """Order model for customer orders to suppliers."""

    order_id: str
    product_name: str
    quantity: int = Field(ge=1, description="Quantity ordered")
    fournisseur_id: str
    estimated_time_arrival: str
    time_of_arrival: Optional[str] = Field(
        None, description="Actual arrival time, None if not yet delivered"
    )
    order_date: str

    new_price: float | None = None
    new_delivery_time: int | None = None


class PerformanceBreakdown(BaseModel):
    """Detailed breakdown of performance calculation."""

    delivery_score: float = Field(
        ge=0, le=100, description="Delivery performance score (0-100)"
    )
    delivery_on_time_rate: float = Field(
        ge=0, le=100, description="On-time delivery rate (%)"
    )
    delivery_total_deliveries: int = Field(
        ge=0, description="Total number of deliveries"
    )
    delivery_on_time: int = Field(ge=0, description="Number of on-time deliveries")
    delivery_late: int = Field(ge=0, description="Number of late deliveries")

    price_score: float = Field(
        ge=0, le=100, description="Price competitiveness score (0-100)"
    )
    price_cheaper_alternatives: int = Field(
        ge=0, description="Number of cheaper alternatives found"
    )
    price_product_count: int = Field(
        ge=0, description="Number of products from this supplier"
    )

    volume_score: float = Field(ge=0, le=100, description="Order volume score (0-100)")
    volume_monthly_spend: float = Field(ge=0, description="Monthly spend amount")

    diversity_score: float = Field(
        ge=0, le=100, description="Product diversity score (0-100)"
    )
    diversity_product_count: int = Field(ge=0, description="Number of unique products")


class SupplierROI(BaseModel):
    """Model for supplier ROI and performance metrics."""

    id: str
    name: str
    performance: float = Field(ge=0, le=100, description="Performance score (0-100)")
    monthly_spend: float = Field(ge=0, description="Monthly spending in euros")
    status: str = Field(description="Status: excellent, good, fair, warning")
    trend: str = Field(description="Trend: up, stable, down")
    issues: List[str] = Field(default_factory=list, description="List of active issues")
    phone_number: str
    performance_breakdown: Optional[PerformanceBreakdown] = Field(
        None, description="Detailed breakdown of performance calculation"
    )


class SupplierROIResponse(BaseModel):
    """Response model for supplier ROI endpoint."""

    suppliers: List[SupplierROI]
    total_count: int
    total_monthly_spend: float
    avg_performance: float
    excellent_count: int
    warning_count: int


class InventoryProduct(BaseModel):
    """Enriched in-store product with inventory information."""

    id: str
    sku: str
    name: str
    category: str
    supplier: str
    supplier_id: str
    type: str  # "in-house" or "external"
    currentPrice: float
    currentPriceSupplier: str
    bestPrice: float
    bestPriceSupplier: str
    bestPriceSupplierId: str
    sellPrice: float
    currentMargin: float
    bestMargin: float
    currentDeliveryTime: Optional[int] = None
    currentDeliverySupplier: str
    bestDeliveryTime: Optional[int] = None
    bestDeliverySupplier: str
    bestDeliverySupplierId: str
    marginImprovementPossible: bool = False
    deliveryImprovementPossible: bool = False
    dualImprovementSameSupplier: bool = False
    stock: int
    weeklyUse: int
    stockoutDate: str
    status: str  # "healthy", "low", "critical"


class InventoryProductsResponse(BaseModel):
    """Response model for in-store products endpoint."""

    products: List[InventoryProduct]
    total_count: int


class ActivePurchaseOrder(BaseModel):
    """Active purchase order model."""

    order_id: str
    product_name: str
    quantity: int
    supplier_name: str
    estimated_delivery: str
    actual_delivery: Optional[str]
    status: str  # "on_track", "delayed", "pending"
    order_date: str


class PurchaseOrdersResponse(BaseModel):
    """Response model for active purchase orders endpoint."""

    orders: List[ActivePurchaseOrder]
    total_count: int


class SupplierOption(BaseModel):
    """Supplier option for a product."""

    id: str
    name: str
    price: float
    delivery_time: str
    rating: int
    phone: str


class SupplierOptionsResponse(BaseModel):
    """Response model for product suppliers endpoint."""

    suppliers: List[SupplierOption]
    current_supplier_id: Optional[str]
