"""
Script to generate fake datasets for the hackathon project.
Generates:
- Fournisseur (Suppliers)
- In store products
- Available products (can have multiple suppliers per product)
- Orders (Customer orders to suppliers)
"""

import random
import uuid
from datetime import datetime, timedelta

import pandas as pd

# Set random seed for reproducibility
random.seed(42)


# Generate Fournisseur (Suppliers)
def generate_fournisseurs(n=50):
    """Generate fake supplier data"""
    suppliers = []
    company_names = [
        "PharmaDistrib",
        "MedSupply Co.",
        "Health Products Inc.",
        "Pharmaceutical Express",
        "MediCare Distributors",
        "Pharma Solutions",
        "Medical Supply Pro",
        "Health Warehouse",
        "Pharma Direct",
        "MediSupply Network",
        "Pharmaceutical Hub",
        "Health Distributors",
        "MedSupply Express",
        "Pharma Central",
        "Medical Products Ltd",
        "Health Supply Chain",
        "Pharma Depot",
        "MediCare Solutions",
        "Pharmaceutical Network",
        "Health Express Pro",
        "MedSupply Direct",
        "Pharma Warehouse",
        "Medical Distributors",
        "Health Products Pro",
        "Pharma Solutions Plus",
        "MediCare Express",
        "Pharmaceutical Depot",
        "Health Supply Network",
        "MedSupply Central",
        "Pharma Network Pro",
        "Medical Express",
        "Health Distributors Plus",
        "Pharma Direct Pro",
        "MediCare Warehouse",
        "Pharmaceutical Solutions",
        "Health Supply Express",
        "MedSupply Network Pro",
        "Pharma Central Plus",
        "Medical Products Express",
        "Health Distributors Pro",
        "Pharma Depot Plus",
        "MediCare Direct",
        "Pharmaceutical Network Pro",
        "Health Express Network",
        "MedSupply Solutions",
        "Pharma Warehouse Pro",
        "Medical Distributors Plus",
        "Health Products Express",
        "Pharma Solutions Network",
        "MediCare Supply Pro",
        "Pharmaceutical Direct",
    ]

    for i in range(1, n + 1):
        # Generate UUID with supp_ prefix
        supplier_id = f"supp_{uuid.uuid4()}"
        name = (
            random.choice(company_names)
            + f" {random.choice(['North', 'South', 'East', 'West', 'International', 'Global'])}"
        )
        # Generate French phone numbers
        phone = f"+33 {random.randint(1, 9)}{random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)}"
        suppliers.append({"id": supplier_id, "name": name, "phone_number": phone})

    return pd.DataFrame(suppliers)


# Generate In Store Products from Available Products
def generate_in_store_products(available_products_df, n=200):
    """Generate in-store products as a subset of available products.
    Each product name appears only once with one supplier, and price matches available_products.
    """
    products = []

    # Get unique product names from available products
    unique_product_names = available_products_df["name"].unique().tolist()

    # Randomly select which products will be in-store (up to n products)
    products_to_include = random.sample(
        unique_product_names, min(n, len(unique_product_names))
    )

    for product_name in products_to_include:
        # Get all available entries for this product (with different suppliers)
        product_entries = available_products_df[
            available_products_df["name"] == product_name
        ]

        # Randomly select one supplier for this product
        selected_entry = product_entries.sample(1).iloc[0]

        # Stock between 0 and 500
        stock = random.randint(0, 500)

        products.append(
            {
                "id": selected_entry["id"],
                "name": selected_entry["name"],
                "price": selected_entry["price"],  # Use price from available_products
                "fournisseur_id": selected_entry[
                    "fournisseur"
                ],  # Use supplier from available_products
                "stock": stock,
            }
        )

    return pd.DataFrame(products)


# Generate Available Products (can have multiple suppliers per product)
def generate_available_products(
    product_names_list, fournisseur_df, product_id_map=None
):
    """Generate fake available product data with multiple suppliers per product"""
    available_products = []

    # Use provided product_id_map or create a new one
    if product_id_map is None:
        product_id_map = {}

    # Generate entries where each product can have multiple suppliers
    for product_name in product_names_list:
        # Generate a unique ID for this product name (if not already created)
        if product_name not in product_id_map:
            product_id_map[product_name] = f"prod_{uuid.uuid4()}"

        # Use the same ID for all entries with this product name
        product_id = product_id_map[product_name]

        # Each product can be available from 1 to 4 suppliers
        num_suppliers = random.randint(1, 4)
        selected_suppliers = random.sample(
            fournisseur_df["id"].tolist(), min(num_suppliers, len(fournisseur_df))
        )

        for supplier_id in selected_suppliers:
            # Price can vary by supplier (wholesale vs retail)
            base_price = random.uniform(2, 150)
            # Supplier price might be 10-30% different from store price
            price = round(base_price * random.uniform(0.7, 1.3), 2)

            # Delivery time between 1 and 14 days
            delivery_time = random.randint(1, 14)

            # Last information update between 1 and 90 days ago
            days_ago = random.randint(1, 90)
            last_update = (datetime.now() - timedelta(days=days_ago)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            available_products.append(
                {
                    "id": product_id,
                    "name": product_name,
                    "fournisseur": supplier_id,
                    "price": price,
                    "delivery_time": delivery_time,
                    "last_information_update": last_update,
                }
            )

    # Add some additional products that might not be in store
    additional_products = [
        "Amoxicilline 500mg",
        "Ciprofloxacine 500mg",
        "Azithromycine 250mg",
        "Doxycycline 100mg",
        "Métronidazole 500mg",
        "Insuline Glulisine",
        "Métformine 500mg",
        "Atorvastatine 20mg",
        "Amlodipine 5mg",
        "Lisinopril 10mg",
        "Oméprazole 20mg",
        "Lansoprazole 30mg",
        "Montélukast 10mg",
        "Salbutamol Spray",
        "Fluticasone Nasal",
    ]

    for product_name in additional_products:
        # Generate a unique ID for this product name (if not already created)
        if product_name not in product_id_map:
            product_id_map[product_name] = f"prod_{uuid.uuid4()}"

        # Use the same ID for all entries with this product name
        product_id = product_id_map[product_name]

        num_suppliers = random.randint(1, 3)
        selected_suppliers = random.sample(
            fournisseur_df["id"].tolist(), min(num_suppliers, len(fournisseur_df))
        )

        for supplier_id in selected_suppliers:
            base_price = random.uniform(5, 100)
            price = round(base_price * random.uniform(0.7, 1.3), 2)
            delivery_time = random.randint(1, 14)
            days_ago = random.randint(1, 90)
            last_update = (datetime.now() - timedelta(days=days_ago)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            available_products.append(
                {
                    "id": product_id,
                    "name": product_name,
                    "fournisseur": supplier_id,
                    "price": price,
                    "delivery_time": delivery_time,
                    "last_information_update": last_update,
                }
            )

    return pd.DataFrame(available_products)


# Generate Orders
def generate_orders(available_products_df, n=100):
    """Generate fake order data.
    
    Args:
        available_products_df: DataFrame of available products
        n: Number of orders to generate
    
    Returns:
        DataFrame with columns: order_id, product_name, quantity, fournisseur_id, 
                               estimated_time_arrival, time_of_arrival, order_date
    """
    orders = []
    
    for i in range(n):
        # Select a random product from available products
        product_entry = available_products_df.sample(1).iloc[0]
        
        # Generate order ID
        order_id = f"order_{uuid.uuid4()}"
        
        # Quantity between 10 and 500 units
        quantity = random.randint(10, 500)
        
        # Order date between 1 and 180 days ago
        days_ago = random.randint(1, 180)
        order_date = datetime.now() - timedelta(days=days_ago)
        
        # Estimated delivery time from the product's delivery_time (convert to int)
        estimated_delivery_days = int(product_entry['delivery_time'])
        estimated_time_arrival = order_date + timedelta(days=estimated_delivery_days)
        
        # Time of arrival: 
        # - 70% of orders have arrived (time_of_arrival is filled)
        # - 30% are still pending (time_of_arrival is None/NaT)
        # For delivered orders, actual arrival can be early (-2 days) or late (+5 days)
        if random.random() < 0.7 and order_date < datetime.now() - timedelta(days=estimated_delivery_days):
            # Order has been delivered
            delay = random.randint(-2, 5)  # Can be early or late
            time_of_arrival = estimated_time_arrival + timedelta(days=delay)
            # Make sure arrival is not in the future
            if time_of_arrival > datetime.now():
                time_of_arrival = datetime.now() - timedelta(days=random.randint(1, 3))
        else:
            # Order is still pending
            time_of_arrival = None
        
        orders.append({
            'order_id': order_id,
            'product_name': product_entry['name'],
            'quantity': quantity,
            'fournisseur_id': product_entry['fournisseur'],
            'estimated_time_arrival': estimated_time_arrival.strftime('%Y-%m-%d %H:%M:%S'),
            'time_of_arrival': time_of_arrival.strftime('%Y-%m-%d %H:%M:%S') if time_of_arrival else None,
            'order_date': order_date.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return pd.DataFrame(orders)


# Main execution
if __name__ == "__main__":
    print("Generating fake datasets...")

    # Define product names list
    product_names = [
        "Paracétamol 500mg",
        "Ibuprofène 400mg",
        "Aspirine 500mg",
        "Doliprane 1000mg",
        "Spasfon 80mg",
        "Smecta Sachets",
        "Strepsils Pastilles",
        "Vicks Vaporub 50g",
        "Biafine Crème",
        "Bétadine Solution",
        "Pansements Adhésifs",
        "Compresses Stériles",
        "Seringues 5ml",
        "Thermomètre Digital",
        "Tensiomètre Électronique",
        "Gants Nitrile Boîte",
        "Masque Chirurgical",
        "Alcool à 70°",
        "Sérum Physiologique",
        "Vitamine D3 1000UI",
        "Vitamine C 1000mg",
        "Magnésium 300mg",
        "Fer 14mg",
        "Oméga 3 Capsules",
        "Probiotiques Gélules",
        "Mélatonine 1mg",
        "Ginkgo Biloba",
        "Ginseng Extrait",
        "Echinacée Gélules",
        "Millepertuis",
        "Valériane Comprimés",
        "Passiflore Gélules",
        "Aubépine Tisane",
        "Camomille Sachets",
        "Tilleul Infusion",
        "Sirop Toux Sèche",
        "Sirop Toux Grasse",
        "Pastilles Miel Citron",
        "Spray Nasal Salin",
        "Collyre Larmes Artificielles",
        "Bain de Bouche",
        "Dentifrice Fluoré",
        "Brosse à Dents",
        "Fil Dentaire",
        "Bain de Bouche Antiseptique",
        "Crème Solaire SPF50",
        "Crème Hydratante Visage",
        "Shampoing Antipelliculaire",
        "Savon Dermatologique",
        "Crème Réparatrice Mains",
    ]

    # Generate datasets
    fournisseurs = generate_fournisseurs(50)

    # Create a shared product ID mapping so products with the same name
    # have the same ID in both in_store_product and available_product
    product_id_map = {}

    # Generate available_products first (with all products and multiple suppliers)
    available_products = generate_available_products(
        product_names, fournisseurs, product_id_map
    )

    # Generate in_store_products as a subset of available_products
    # Each product name appears only once with one supplier, price matches available_products
    in_store_products = generate_in_store_products(available_products, 200)
    
    # Generate orders based on available products
    orders = generate_orders(available_products, 100)

    # Save to CSV files
    fournisseurs.to_csv("fournisseur.csv", index=False)
    in_store_products.to_csv("in_store_product.csv", index=False)
    available_products.to_csv("available_product.csv", index=False)
    orders.to_csv("orders.csv", index=False)

    print(f"✓ Generated {len(fournisseurs)} suppliers")
    print(f"✓ Generated {len(in_store_products)} in-store products")
    print(f"✓ Generated {len(available_products)} available product entries")
    print(f"✓ Generated {len(orders)} orders")
    print("\nFiles created:")
    print("  - fournisseur.csv")
    print("  - in_store_product.csv")
    print("  - available_product.csv")
    print("  - orders.csv")
