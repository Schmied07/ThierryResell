#!/usr/bin/env python3

import requests
import json
import uuid
import time
from typing import Dict, Any

# Configuration - Use the correct backend URL from frontend/.env
BASE_URL = "https://catalog-mapper-1.preview.emergentagent.com"
API_PREFIX = "/api"

# Real Keepa API key provided in review request
REAL_KEEPA_API_KEY = "ju7cgn79dp9ehsp8473lldrvsi8a0cdiglba9gu6fpl61quncl0h870q0o01qbaq"

class KeepaIntegrationTester:
    def __init__(self):
        self.base_url = BASE_URL + API_PREFIX
        self.token = None
        self.user_email = f"keepa_test_{uuid.uuid4().hex[:8]}@example.com"
        self.user_password = "password123"
        self.user_name = "Keepa Test User"
        self.product_id = None  # Store first product ID from catalog
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        print(f"[{level}] {message}")
        
    def make_request(self, method: str, endpoint: str, data: dict = None, headers: dict = None, files: dict = None) -> dict:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {}
        
        # Only add Content-Type for JSON requests
        if not files:
            default_headers["Content-Type"] = "application/json"
        
        if self.token:
            default_headers["Authorization"] = f"Bearer {self.token}"
            
        if headers:
            default_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=60)
            elif method.upper() == "POST":
                if files:
                    # Remove Content-Type for file uploads to let requests handle boundary
                    auth_headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
                    response = requests.post(url, files=files, headers=auth_headers, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=default_headers, timeout=60)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=default_headers, timeout=60)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=default_headers, timeout=60)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            # Log request details
            self.log(f"{method} {url} -> {response.status_code}")
            
            try:
                response_data = response.json()
            except:
                response_data = {"error": "No JSON response", "text": response.text[:500]}
                
            return {
                "status_code": response.status_code,
                "data": response_data,
                "success": response.status_code < 400
            }
            
        except requests.exceptions.Timeout:
            return {"status_code": 408, "data": {"error": "Request timeout"}, "success": False}
        except requests.exceptions.RequestException as e:
            return {"status_code": 500, "data": {"error": str(e)}, "success": False}
    
    def step1_register_user(self) -> bool:
        """Step 1: Register a new user"""
        self.log("=== STEP 1: Registering New User ===")
        
        response = self.make_request("POST", "/auth/register", {
            "email": self.user_email,
            "password": self.user_password,
            "name": self.user_name
        })
        
        if response["success"]:
            self.token = response["data"].get("token")
            self.log(f"✅ User registration successful. JWT token obtained.")
            return True
        else:
            self.log(f"❌ User registration failed: {response['data']}", "ERROR")
            return False
    
    def step2_configure_keepa_api_key(self) -> bool:
        """Step 2: Configure Keepa API key"""
        self.log("=== STEP 2: Configuring Keepa API Key ===")
        
        response = self.make_request("PUT", "/settings/api-keys", {
            "keepa_api_key": REAL_KEEPA_API_KEY
        })
        
        if response["success"]:
            self.log(f"✅ Keepa API key configured successfully")
            
            # Verify the key was set
            verify_response = self.make_request("GET", "/settings/api-keys")
            if verify_response["success"]:
                api_keys_status = verify_response["data"]
                if api_keys_status.get("keepa_api_key_set", False):
                    self.log(f"✅ Keepa API key verified as set")
                    return True
                else:
                    self.log(f"❌ Keepa API key verification failed", "ERROR")
                    return False
            else:
                self.log(f"❌ Could not verify API key status", "ERROR")
                return False
        else:
            self.log(f"❌ Keepa API key configuration failed: {response['data']}", "ERROR")
            return False
    
    def step3_import_catalog(self) -> bool:
        """Step 3: Import the catalog file"""
        self.log("=== STEP 3: Importing Catalog ===")
        
        try:
            # Try the main catalog file first
            catalog_file = '/app/catalog_sample.xlsx'
            try:
                with open(catalog_file, 'rb') as file:
                    files = {'file': ('catalog_sample.xlsx', file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                    response = self.make_request("POST", "/catalog/import", files=files)
            except FileNotFoundError:
                # Fallback to test catalog
                self.log("Main catalog file not found, trying test catalog", "WARN")
                catalog_file = '/app/test_catalog_simple.xlsx'
                with open(catalog_file, 'rb') as file:
                    files = {'file': ('test_catalog_simple.xlsx', file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                    response = self.make_request("POST", "/catalog/import", files=files)
            
            if response["success"]:
                data = response["data"]
                imported = data.get('imported', 0)
                skipped = data.get('skipped', 0)
                total = data.get('total', 0)
                
                if imported > 0:
                    self.log(f"✅ Catalog import successful. Imported: {imported}, Skipped: {skipped}, Total: {total}")
                    return True
                else:
                    self.log(f"❌ Import succeeded but 0 products imported: {data}", "ERROR")
                    return False
            else:
                self.log(f"❌ Catalog import failed: {response['data']}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Catalog import error: {str(e)}", "ERROR")
            return False
    
    def step4_get_first_product(self) -> bool:
        """Step 4: Get the first product from catalog"""
        self.log("=== STEP 4: Getting First Product from Catalog ===")
        
        response = self.make_request("GET", "/catalog/products?limit=1")
        
        if response["success"]:
            data = response["data"]
            products = data.get("products", [])
            
            if len(products) > 0:
                product = products[0]
                self.product_id = product.get("id")
                self.log(f"✅ First product retrieved: {product.get('name', 'N/A')} (ID: {self.product_id})")
                self.log(f"   GTIN: {product.get('gtin', 'N/A')}, Brand: {product.get('brand', 'N/A')}")
                return True
            else:
                self.log(f"❌ No products found in catalog", "ERROR")
                return False
        else:
            self.log(f"❌ Failed to get catalog products: {response['data']}", "ERROR")
            return False
    
    def step5_compare_product(self) -> bool:
        """Step 5: Compare that product using real Keepa data"""
        self.log("=== STEP 5: Comparing Product with Real Keepa Data ===")
        
        if not self.product_id:
            self.log("❌ No product ID available for comparison", "ERROR")
            return False
        
        response = self.make_request("POST", f"/catalog/compare/{self.product_id}")
        
        if response["success"]:
            data = response["data"]
            
            # Critical check: should NOT be mock data
            is_mock_data = data.get("is_mock_data", True)
            if is_mock_data:
                self.log(f"❌ CRITICAL: Response indicates mock data (is_mock_data: {is_mock_data})", "ERROR")
                self.log(f"   This means the Keepa API integration is not working with real data", "ERROR")
                return False
            
            # Check Amazon price is present and is a number (not null)
            amazon_price_eur = data.get("amazon_price_eur")
            if amazon_price_eur is None:
                self.log(f"❌ CRITICAL: amazon_price_eur is null - no real price data", "ERROR")
                return False
            
            if not isinstance(amazon_price_eur, (int, float)):
                self.log(f"❌ CRITICAL: amazon_price_eur is not a number: {type(amazon_price_eur)}", "ERROR")  
                return False
            
            self.log(f"✅ CRITICAL SUCCESS: Real Keepa data received!")
            self.log(f"   is_mock_data: {is_mock_data}")
            self.log(f"   amazon_price_eur: €{amazon_price_eur}")
            self.log(f"   Product: {data.get('product_name', 'N/A')}")
            self.log(f"   GTIN: {data.get('gtin', 'N/A')}")
            
            # Log other key data points
            cheapest_source = data.get("cheapest_source")
            amazon_fees = data.get("amazon_fees_eur")
            supplier_margin = data.get("supplier_margin_eur")
            
            self.log(f"   cheapest_source: {cheapest_source}")
            self.log(f"   amazon_fees_eur: €{amazon_fees}" if amazon_fees else "   amazon_fees_eur: None")
            self.log(f"   supplier_margin_eur: €{supplier_margin}" if supplier_margin else "   supplier_margin_eur: None")
            
            return True
        else:
            self.log(f"❌ Product comparison failed: {response['data']}", "ERROR")
            return False
    
    def step6_compare_all_products(self) -> bool:
        """Step 6: Test compare-all endpoint"""
        self.log("=== STEP 6: Testing Compare All Products ===")
        
        response = self.make_request("POST", "/catalog/compare-all")
        
        if response["success"]:
            data = response["data"]
            
            # Check required fields
            required_fields = ['total', 'success', 'failed', 'results', 'errors']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log(f"❌ Missing fields in compare-all response: {missing_fields}", "ERROR")
                return False
            
            total = data['total']
            success = data['success']
            failed = data['failed']
            results = data['results']
            
            self.log(f"✅ Compare-all completed: Total: {total}, Success: {success}, Failed: {failed}")
            
            # Check at least some products were processed
            if total == 0:
                self.log(f"❌ No products were processed", "ERROR")
                return False
            
            # Check for real data in results (sample first few)
            real_data_found = False
            mock_data_count = 0
            
            for i, result in enumerate(results[:3]):  # Check first 3 results
                is_mock = result.get("is_mock_data", True)
                amazon_price = result.get("amazon_price_eur")
                
                if not is_mock and amazon_price is not None:
                    real_data_found = True
                    self.log(f"   Product {i+1}: Real data - Amazon: €{amazon_price}")
                else:
                    mock_data_count += 1
                    self.log(f"   Product {i+1}: {'Mock data' if is_mock else 'No Amazon price'}")
            
            if real_data_found:
                self.log(f"✅ CRITICAL: Real Keepa data found in compare-all results")
                return True
            else:
                self.log(f"❌ CRITICAL: No real Keepa data found in any results", "ERROR")
                return False
                
        else:
            self.log(f"❌ Compare-all failed: {response['data']}", "ERROR")
            return False
    
    def step7_test_text_search(self) -> bool:
        """Step 7: Test text search with real Keepa data"""
        self.log("=== STEP 7: Testing Text Search ===")
        
        search_query = "Elmex Junior Toothpaste 75 ml"
        response = self.make_request("POST", "/search/text", {
            "query": search_query
        })
        
        if response["success"]:
            data = response["data"]
            
            # Check keepa_data exists
            keepa_data = data.get("keepa_data", {})
            if not keepa_data:
                self.log(f"❌ No keepa_data in text search response", "ERROR")
                return False
            
            # Check if it's real data
            is_mock = keepa_data.get("mock_data", True)
            current_price = keepa_data.get("current_price")
            
            if is_mock:
                self.log(f"⚠️  Text search returned mock data - API might not have found the product")
                self.log(f"   Query: {search_query}")
                self.log(f"   This is acceptable as text search depends on product availability in Keepa")
                return True  # This is acceptable for text search
            else:
                self.log(f"✅ Text search found real Keepa data!")
                self.log(f"   Query: {search_query}")
                self.log(f"   Current Price: €{current_price}" if current_price else "   Current Price: None")
                self.log(f"   ASIN: {keepa_data.get('asin', 'N/A')}")
                return True
        else:
            self.log(f"❌ Text search failed: {response['data']}", "ERROR")
            return False
    
    def run_keepa_integration_test(self):
        """Run the complete Keepa integration test sequence"""
        self.log("🚀 Starting KEEPA INTEGRATION TEST")
        self.log("="*60)
        self.log(f"Testing Keepa API fix: /search -> /product endpoint change")
        self.log(f"Using REAL Keepa API key: {REAL_KEEPA_API_KEY[:20]}...")
        self.log(f"Backend URL: {self.base_url}")
        self.log("="*60)
        
        test_results = {}
        
        # Execute test steps in sequence
        test_results["step1_register_user"] = self.step1_register_user()
        if not test_results["step1_register_user"]:
            self.log("❌ Cannot proceed without user registration", "ERROR")
            return test_results
        
        test_results["step2_configure_keepa_api_key"] = self.step2_configure_keepa_api_key()
        if not test_results["step2_configure_keepa_api_key"]:
            self.log("❌ Cannot proceed without Keepa API key", "ERROR")
            return test_results
        
        test_results["step3_import_catalog"] = self.step3_import_catalog()
        if not test_results["step3_import_catalog"]:
            self.log("❌ Cannot proceed without catalog data", "ERROR")
            return test_results
        
        test_results["step4_get_first_product"] = self.step4_get_first_product()
        if not test_results["step4_get_first_product"]:
            self.log("❌ Cannot proceed without product data", "ERROR")
            return test_results
        
        # Critical test: Single product comparison with real Keepa data
        test_results["step5_compare_product"] = self.step5_compare_product()
        
        # Test compare-all endpoint  
        test_results["step6_compare_all_products"] = self.step6_compare_all_products()
        
        # Test text search
        test_results["step7_test_text_search"] = self.step7_test_text_search()
        
        # Summary
        self.log("\n" + "="*60)
        self.log("🏁 KEEPA INTEGRATION TEST RESULTS")
        self.log("="*60)
        
        critical_tests = ["step5_compare_product", "step6_compare_all_products"]
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            critical_mark = " [CRITICAL]" if test_name in critical_tests else ""
            self.log(f"{test_name}: {status}{critical_mark}")
        
        # Check critical success
        critical_passed = all(test_results.get(test, False) for test in critical_tests)
        total_passed = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        self.log(f"\nOverall: {total_passed}/{total_tests} tests passed")
        
        if critical_passed:
            self.log("🎉 CRITICAL SUCCESS: Keepa API integration is working with REAL data!")
            self.log("✅ The fix from /search to /product endpoint is working correctly")
        else:
            self.log("❌ CRITICAL FAILURE: Keepa API integration not working with real data")
            self.log("❌ The API may still be using mock data or the fix needs review")
        
        return test_results, critical_passed

def main():
    """Main test execution"""
    tester = KeepaIntegrationTester()
    results, critical_success = tester.run_keepa_integration_test()
    
    # Exit code based on critical results
    if critical_success:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()