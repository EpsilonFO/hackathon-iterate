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


class Order(BaseModel):
    """Order model for customer orders to suppliers."""

    order_id: str
    product_name: str
    quantity: int = Field(ge=1, description="Quantity ordered")
    fournisseur_id: str
    estimated_time_arrival: str
    time_of_arrival: Optional[str] = Field(None, description="Actual arrival time, None if not yet delivered")
    order_date: str

    new_price: float | None = None
    new_delivery_time: int | None = None
