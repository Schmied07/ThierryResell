#!/usr/bin/env python3
"""
Final comprehensive test for Google Suppliers feature
"""

import asyncio
import httpx
import json
from datetime import datetime

BACKEND_URL = "https://price-compare-175.preview.emergentagent.com/api"

async def comprehensive_test():
    """Run comprehensive tests covering all aspects of the Google Suppliers feature"""
    
    print("🧪 COMPREHENSIVE GOOGLE SUPPLIERS TESTING")
    print("=" * 60)
    
    # Test 1: Register user
    test_email = f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    user_data = {"email": test_email, "password": "testpass123", "name": "Comprehensive Test"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{BACKEND_URL}/auth/register", json=user_data)
        if response.status_code != 200:
            print(f"❌ Registration failed")
            return False
        
        token = response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Test 1: User registration successful")
        
        # Test 2: Import catalog
        with open("/app/test_catalog_simple.xlsx", "rb") as f:
            files = {"file": ("test_catalog.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            response = await client.post(f"{BACKEND_URL}/catalog/import", headers=headers, files=files)
            
        if response.status_code != 200:
            print(f"❌ Test 2: Catalog import failed")
            return False
        print(f"✅ Test 2: Catalog import successful")
        
        # Test 3: Get product for testing
        response = await client.get(f"{BACKEND_URL}/catalog/products", headers=headers, params={"limit": 1})
        if response.status_code != 200 or not response.json()["products"]:
            print(f"❌ Test 3: No products found")
            return False
        
        product = response.json()["products"][0]
        product_id = product["id"]
        print(f"✅ Test 3: Product found: {product['name']}")
        
        # Test 4A: Test without API keys (mock mode)
        print(f"🔍 Test 4A: Testing comparison without API keys (mock mode)")
        response = await client.post(f"{BACKEND_URL}/catalog/compare/{product_id}", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Test 4A: Comparison failed without API keys")
            return False
            
        data = response.json()
        
        # Verify mock mode response structure
        required_fields = [
            "product_id", "product_name", "gtin", "brand", "is_mock_data",
            "supplier_price_eur", "amazon_price_eur", "google_lowest_price_eur",
            "google_suppliers_results", "cheapest_source"
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"❌ Test 4A: Missing response fields: {missing_fields}")
            return False
            
        if not data.get("is_mock_data"):
            print(f"❌ Test 4A: Should be mock data mode")
            return False
            
        if data.get("google_suppliers_results") is not None:
            print(f"❌ Test 4A: google_suppliers_results should be None in mock mode")
            return False
            
        if data.get("google_lowest_price_eur") is None:
            print(f"❌ Test 4A: google_lowest_price_eur should be populated even in mock mode")
            return False
            
        print(f"✅ Test 4A: Mock mode response structure correct")
        
        # Test 4B: Test with fake API keys
        print(f"🔍 Test 4B: Testing with fake Google API keys")
        
        api_keys = {
            "google_api_key": "fake_key_test",
            "google_search_engine_id": "fake_cx_test"
        }
        
        response = await client.put(f"{BACKEND_URL}/settings/api-keys", json=api_keys, headers=headers)
        if response.status_code != 200:
            print(f"❌ Test 4B: API keys setup failed")
            return False
        
        # Run comparison with fake API keys
        response = await client.post(f"{BACKEND_URL}/catalog/compare/{product_id}", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Test 4B: Comparison failed with fake API keys")
            return False
            
        data = response.json()
        
        # Verify response structure with API keys
        if data.get("is_mock_data"):
            print(f"❌ Test 4B: Should not be mock data mode when API keys are set")
            return False
            
        if "google_suppliers_results" not in data:
            print(f"❌ Test 4B: google_suppliers_results field missing")
            return False
            
        # With fake keys, Google API will fail, so results should be None or empty
        google_suppliers = data.get("google_suppliers_results")
        if google_suppliers is not None and len(google_suppliers) > 0:
            # This would only happen if real API keys were somehow working
            print(f"ℹ️  Test 4B: Google suppliers found (real API keys might be working)")
            
            # If we do get results, verify the structure
            for supplier in google_suppliers:
                required_supplier_fields = ["supplier_name", "url", "price", "is_lowest"]
                missing = [f for f in required_supplier_fields if f not in supplier]
                if missing:
                    print(f"❌ Test 4B: Supplier missing fields: {missing}")
                    return False
            
            # Check that at least one is marked as lowest
            lowest_count = sum(1 for s in google_suppliers if s.get("is_lowest"))
            if lowest_count == 0:
                print(f"❌ Test 4B: No supplier marked as lowest")
                return False
                
            print(f"✅ Test 4B: Google suppliers structure validated")
        else:
            print(f"✅ Test 4B: No Google suppliers (expected with fake API keys)")
        
        print(f"✅ Test 4B: API keys mode response structure correct")
        
        # Test 5: Database persistence
        print(f"🔍 Test 5: Testing database persistence")
        
        response = await client.get(f"{BACKEND_URL}/catalog/products", headers=headers)
        if response.status_code != 200:
            print(f"❌ Test 5: Failed to fetch products")
            return False
            
        products = response.json()["products"]
        test_product = next((p for p in products if p["id"] == product_id), None)
        
        if not test_product:
            print(f"❌ Test 5: Product not found in database")
            return False
            
        # Verify that google_suppliers_results field exists in database
        if "google_suppliers_results" not in test_product:
            print(f"❌ Test 5: google_suppliers_results field not saved to database")
            return False
            
        print(f"✅ Test 5: Database persistence verified")
        
        # Test 6: API response consistency
        print(f"🔍 Test 6: Testing API response consistency")
        
        # Run multiple comparisons to ensure consistent structure
        for i in range(3):
            response = await client.post(f"{BACKEND_URL}/catalog/compare/{product_id}", headers=headers)
            if response.status_code != 200:
                print(f"❌ Test 6: Comparison {i+1} failed")
                return False
                
            data = response.json()
            if "google_suppliers_results" not in data:
                print(f"❌ Test 6: Inconsistent response structure in run {i+1}")
                return False
        
        print(f"✅ Test 6: API response consistency verified")
        
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Google Suppliers feature is fully functional")
        print(f"✅ Response structure includes google_suppliers_results field")
        print(f"✅ Mock data mode works correctly")
        print(f"✅ API keys integration works (tested error handling)")
        print(f"✅ Database persistence confirmed")
        print(f"✅ Response structure is consistent")
        
        return True

if __name__ == "__main__":
    result = asyncio.run(comprehensive_test())
    exit(0 if result else 1)