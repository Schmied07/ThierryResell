#!/usr/bin/env python3
"""
Debug script to check what products are actually in the catalog
"""

import requests
import json

BACKEND_URL = "https://metal-box-finder.preview.emergentagent.com/api"
TEST_EMAIL = "flextest@test.com"
TEST_PASSWORD = "test123"

def get_auth_token():
    """Login and get auth token"""
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get("token")
    return None

def debug_catalog():
    """Check what products are in the catalog"""
    token = get_auth_token()
    if not token:
        print("Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BACKEND_URL}/catalog/products", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        products = data.get("products", [])
        print(f"Found {len(products)} products in catalog:")
        
        for i, product in enumerate(products, 1):
            print(f"\nProduct {i}:")
            print(f"  GTIN: {product.get('gtin')}")
            print(f"  Name: {product.get('name')}")
            print(f"  Category: {product.get('category')}")
            print(f"  Brand: {product.get('brand')}")
            print(f"  Price (EUR): {product.get('supplier_price_eur')}")
            print(f"  Price (GBP): {product.get('supplier_price_gbp')}")
    else:
        print(f"Failed to get products: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    debug_catalog()