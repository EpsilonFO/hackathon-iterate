"""FastAPI application main file."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.controllers.agent_controller import router as agent_router
from backend.controllers.order_parser_controller import router as order_parser_router
from backend.controllers.parser_controller import router as parser_router
from backend.controllers.product_controller import router as product_router
from backend.controllers.root_controller import router as root_router
from backend.controllers.supplier_controller import router as supplier_router

app = FastAPI(
    title="Supplier Optimization API",
    description="API for finding cheaper suppliers and discovering innovative products",
    version="0.1.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(root_router)
app.include_router(supplier_router)
app.include_router(product_router)
app.include_router(parser_router)
app.include_router(order_parser_router)
app.include_router(agent_router)
