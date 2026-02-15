#!/usr/bin/env python3

import requests
import json
import uuid
import time
from typing import Dict, Any

# Configuration
BASE_URL = "https://price-compare-175.preview.emergentagent.com"
API_PREFIX = "/api"

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL + API_PREFIX
        self.token = None
        self.user_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        self.user_password = "password123"
        self.user_name = "Test User"
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        print(f"[{level}] {message}")
        
    def make_request(self, method: str, endpoint: str, data: dict = None, headers: dict = None) -> dict:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if self.token:
            default_headers["Authorization"] = f"Bearer {self.token}"
            
        if headers:
            default_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=default_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            # Log request details
            self.log(f"{method} {url} -> {response.status_code}")
            
            try:
                response_data = response.json()
            except:
                response_data = {"error": "No JSON response", "text": response.text}
                
            return {
                "status_code": response.status_code,
                "data": response_data,
                "success": response.status_code < 400
            }
            
        except requests.exceptions.Timeout:
            return {"status_code": 408, "data": {"error": "Request timeout"}, "success": False}
        except requests.exceptions.RequestException as e:
            return {"status_code": 500, "data": {"error": str(e)}, "success": False}
    
    def test_user_registration(self) -> bool:
        """Test user registration"""
        self.log("=== Testing User Registration ===")
        
        response = self.make_request("POST", "/auth/register", {
            "email": self.user_email,
            "password": self.user_password,
            "name": self.user_name
        })
        
        if response["success"]:
            self.token = response["data"].get("token")
            self.log(f"✅ Registration successful. Token obtained.")
            return True
        else:
            self.log(f"❌ Registration failed: {response['data']}", "ERROR")
            return False
    
    def test_catalog_stats_empty(self) -> bool:
        """Test catalog stats when no products exist"""
        self.log("=== Testing Catalog Stats (Empty) ===")
        
        response = self.make_request("GET", "/catalog/stats")
        
        if response["success"]:
            data = response["data"]
            expected_fields = [
                "total_products", "compared_products", "profitable_products",
                "total_potential_margin", "avg_margin_percentage", 
                "best_opportunity_margin", "amazon_fee_percentage", 
                "brands", "categories"
            ]
            
            missing_fields = [field for field in expected_fields if field not in data]
            if missing_fields:
                self.log(f"❌ Missing fields in stats: {missing_fields}", "ERROR")
                return False
                
            # Verify new fields exist
            if "profitable_products" not in data:
                self.log(f"❌ Missing new field 'profitable_products'", "ERROR")
                return False
                
            if "amazon_fee_percentage" not in data:
                self.log(f"❌ Missing new field 'amazon_fee_percentage'", "ERROR")
                return False
                
            # Check Amazon fee percentage is 15%
            if data.get("amazon_fee_percentage") != 15.0:
                self.log(f"❌ Amazon fee percentage should be 15%, got {data.get('amazon_fee_percentage')}", "ERROR")
                return False
                
            self.log(f"✅ Catalog stats working correctly. Stats: {data}")
            return True
        else:
            self.log(f"❌ Catalog stats failed: {response['data']}", "ERROR")
            return False
    
    def test_catalog_products_empty(self) -> bool:
        """Test catalog products when no products exist"""
        self.log("=== Testing Catalog Products (Empty) ===")
        
        response = self.make_request("GET", "/catalog/products")
        
        if response["success"]:
            data = response["data"]
            if "products" in data and "total" in data:
                if data["total"] == 0 and len(data["products"]) == 0:
                    self.log(f"✅ Catalog products empty as expected")
                    return True
                else:
                    self.log(f"❌ Expected empty catalog, got {data['total']} products", "ERROR")
                    return False
            else:
                self.log(f"❌ Missing products/total fields in response", "ERROR")
                return False
        else:
            self.log(f"❌ Catalog products failed: {response['data']}", "ERROR")
            return False
    
    def test_catalog_opportunities_empty(self) -> bool:
        """Test catalog opportunities when no products exist"""
        self.log("=== Testing Catalog Opportunities (Empty) ===")
        
        response = self.make_request("GET", "/catalog/opportunities")
        
        if response["success"]:
            data = response["data"]
            if "opportunities" in data and "total" in data:
                if data["total"] == 0 and len(data["opportunities"]) == 0:
                    self.log(f"✅ Catalog opportunities empty as expected")
                    return True
                else:
                    self.log(f"❌ Expected empty opportunities, got {data['total']} opportunities", "ERROR")
                    return False
            else:
                self.log(f"❌ Missing opportunities/total fields in response", "ERROR")
                return False
        else:
            self.log(f"❌ Catalog opportunities failed: {response['data']}", "ERROR")
            return False
    
    def test_compare_nonexistent_product(self) -> bool:
        """Test comparison with nonexistent product ID"""
        self.log("=== Testing Compare Nonexistent Product ===")
        
        fake_product_id = "nonexistent-product-id"
        response = self.make_request("POST", f"/catalog/compare/{fake_product_id}")
        
        if response["status_code"] == 404:
            self.log(f"✅ Correctly returned 404 for nonexistent product")
            return True
        else:
            self.log(f"❌ Expected 404, got {response['status_code']}: {response['data']}", "ERROR")
            return False
    
    def test_compare_batch_empty(self) -> bool:
        """Test batch comparison with empty list"""
        self.log("=== Testing Compare Batch (Empty List) ===")
        
        response = self.make_request("POST", "/catalog/compare-batch", [])
        
        if response["success"]:
            data = response["data"]
            if "success" in data and "failed" in data and "results" in data and "errors" in data:
                if data["success"] == 0 and data["failed"] == 0:
                    self.log(f"✅ Batch compare with empty list worked correctly")
                    return True
                else:
                    self.log(f"❌ Expected success=0, failed=0 for empty list, got success={data.get('success')}, failed={data.get('failed')}", "ERROR")
                    return False
            else:
                self.log(f"❌ Missing required fields in batch compare response", "ERROR")
                return False
        else:
            self.log(f"❌ Batch compare failed: {response['data']}", "ERROR")
            return False
    
    def test_authentication_required(self) -> bool:
        """Test that endpoints require authentication"""
        self.log("=== Testing Authentication Required ===")
        
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        endpoints_to_test = [
            "/catalog/stats",
            "/catalog/products", 
            "/catalog/opportunities",
            "/catalog/compare/test-id"
        ]
        
        all_failed_correctly = True
        
        for endpoint in endpoints_to_test:
            method = "POST" if "compare" in endpoint else "GET"
            response = self.make_request(method, endpoint)
            
            # Accept both 401 (Unauthorized) and 403 (Forbidden) as valid auth failures
            if response["status_code"] not in [401, 403]:
                self.log(f"❌ Expected 401/403 for {endpoint}, got {response['status_code']}", "ERROR")
                all_failed_correctly = False
            else:
                self.log(f"✅ {endpoint} correctly requires authentication (got {response['status_code']})")
        
        # Restore token
        self.token = original_token
        return all_failed_correctly
    
    def test_api_structure_consistency(self) -> bool:
        """Test that API responses have consistent structure"""
        self.log("=== Testing API Response Structure ===")
        
        # Test catalog stats structure
        response = self.make_request("GET", "/catalog/stats")
        if not response["success"]:
            self.log(f"❌ Stats endpoint failed", "ERROR")
            return False
            
        stats_data = response["data"]
        required_numeric_fields = [
            "total_products", "compared_products", "profitable_products",
            "total_potential_margin", "avg_margin_percentage", 
            "best_opportunity_margin", "amazon_fee_percentage"
        ]
        
        for field in required_numeric_fields:
            if field not in stats_data or not isinstance(stats_data[field], (int, float)):
                self.log(f"❌ Stats field '{field}' missing or not numeric", "ERROR")
                return False
        
        # Test products structure
        response = self.make_request("GET", "/catalog/products")
        if not response["success"]:
            self.log(f"❌ Products endpoint failed", "ERROR")
            return False
            
        products_data = response["data"]
        required_fields = ["products", "total", "skip", "limit"]
        for field in required_fields:
            if field not in products_data:
                self.log(f"❌ Products field '{field}' missing", "ERROR")
                return False
        
        self.log(f"✅ API structure consistency verified")
        return True
    
    def test_compare_all_empty_catalog(self) -> bool:
        """Test compare-all endpoint when catalog is empty"""
        self.log("=== Testing Compare All Products (Empty Catalog) ===")
        
        response = self.make_request("POST", "/catalog/compare-all")
        
        if response["status_code"] == 404:
            if "Aucun produit dans le catalogue" in str(response["data"]):
                self.log(f"✅ Compare-all correctly returns 404 for empty catalog")
                return True
            else:
                self.log(f"❌ Got 404 but wrong message: {response['data']}", "ERROR")
                return False
        else:
            self.log(f"❌ Expected 404 for empty catalog, got {response['status_code']}: {response['data']}", "ERROR")
            return False
    
    def test_catalog_import(self) -> bool:
        """Test catalog import with sample file"""
        self.log("=== Testing Catalog Import ===")
        
        try:
            # Upload the catalog file
            with open('/app/test_catalog_simple.xlsx', 'rb') as file:
                files = {'file': ('test_catalog_simple.xlsx', file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                
                url = f"{self.base_url}/catalog/import"
                headers = {"Authorization": f"Bearer {self.token}"}
                
                response = requests.post(url, files=files, headers=headers, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    imported = data.get('imported', 0)
                    if imported > 0:
                        self.log(f"✅ Catalog import successful. Imported {imported} products")
                        return True
                    else:
                        self.log(f"❌ Import succeeded but 0 products imported: {data}", "ERROR")
                        return False
                else:
                    self.log(f"❌ Catalog import failed: {response.status_code} - {response.text}", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Catalog import error: {str(e)}", "ERROR")
            return False
    
    def test_compare_all_with_products(self) -> bool:
        """Test compare-all endpoint after importing products"""
        self.log("=== Testing Compare All Products (With Products) ===")
        
        response = self.make_request("POST", "/catalog/compare-all")
        
        if response["success"]:
            data = response["data"]
            
            # Check required fields
            required_fields = ['total', 'success', 'failed', 'results', 'errors']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log(f"❌ Missing fields in compare-all response: {missing_fields}", "ERROR")
                return False
            
            # Validate field types and values
            if not isinstance(data['total'], int) or data['total'] <= 0:
                self.log(f"❌ Total should be positive integer, got {data['total']}", "ERROR")
                return False
                
            if not isinstance(data['success'], int) or data['success'] < 0:
                self.log(f"❌ Success count should be non-negative integer, got {data['success']}", "ERROR")
                return False
                
            if not isinstance(data['failed'], int) or data['failed'] < 0:
                self.log(f"❌ Failed count should be non-negative integer, got {data['failed']}", "ERROR")
                return False
                
            if data['total'] != (data['success'] + data['failed']):
                self.log(f"❌ Total ({data['total']}) should equal success ({data['success']}) + failed ({data['failed']})", "ERROR")
                return False
                
            if not isinstance(data['results'], list):
                self.log(f"❌ Results should be a list, got {type(data['results'])}", "ERROR")
                return False
                
            if not isinstance(data['errors'], list):
                self.log(f"❌ Errors should be a list, got {type(data['errors'])}", "ERROR")
                return False
            
            # Check that results count matches success count
            if len(data['results']) != data['success']:
                self.log(f"❌ Results array length ({len(data['results'])}) doesn't match success count ({data['success']})", "ERROR")
                return False
                
            # Check that errors count matches failed count
            if len(data['errors']) != data['failed']:
                self.log(f"❌ Errors array length ({len(data['errors'])}) doesn't match failed count ({data['failed']})", "ERROR")
                return False
            
            self.log(f"✅ Compare-all successful. Total: {data['total']}, Success: {data['success']}, Failed: {data['failed']}")
            return True
        else:
            self.log(f"❌ Compare-all failed: {response['data']}", "ERROR")
            return False

    def test_mock_data_availability(self) -> bool:
        """Test that mock data is available when no API keys configured"""
        self.log("=== Testing Mock Data Availability ===")
        
        # Check if API keys are set (should be empty for new test user)
        response = self.make_request("GET", "/settings/api-keys")
        if not response["success"]:
            self.log(f"❌ Cannot check API keys status", "ERROR")
            return False
        
        api_keys_data = response["data"]
        if api_keys_data.get("keepa_api_key_set", True) or api_keys_data.get("google_api_key_set", True):
            self.log(f"⚠️  API keys are configured, mock data test may not apply", "WARN")
        
        # Test text search which should use mock data
        response = self.make_request("POST", "/search/text", {
            "query": "iPhone 15",
            "search_type": "text"
        })
        
        if not response["success"]:
            self.log(f"❌ Text search failed", "ERROR")
            return False
        
        search_data = response["data"]
        
        # Check if keepa_data exists and contains mock_data flag
        keepa_data = search_data.get("keepa_data", {})
        if not keepa_data:
            self.log(f"❌ No keepa_data in search result", "ERROR")
            return False
        
        if keepa_data.get("mock_data") != True:
            self.log(f"❌ Expected mock_data=True, got {keepa_data.get('mock_data')}", "ERROR")
            return False
        
        # Verify mock Amazon reference price exists
        amazon_reference_price = search_data.get("amazon_reference_price")
        if not amazon_reference_price or not isinstance(amazon_reference_price, (int, float)):
            self.log(f"❌ Mock Amazon reference price missing or invalid", "ERROR")
            return False
        
        self.log(f"✅ Mock data working correctly - Amazon price: €{amazon_reference_price}")
        return True
    
    def run_all_tests(self):
        """Run all backend tests"""
        self.log("🚀 Starting Backend Catalog Comparison Tests")
        self.log(f"Testing against: {self.base_url}")
        
        test_results = {}
        
        # Test user registration first
        test_results["user_registration"] = self.test_user_registration()
        if not test_results["user_registration"]:
            self.log("❌ Cannot proceed without authentication", "ERROR")
            return test_results
        
        # Test authentication requirements
        test_results["authentication_required"] = self.test_authentication_required()
        
        # Test catalog endpoints with empty catalog
        test_results["catalog_stats_empty"] = self.test_catalog_stats_empty()
        test_results["catalog_products_empty"] = self.test_catalog_products_empty()
        test_results["catalog_opportunities_empty"] = self.test_catalog_opportunities_empty()
        
        # Test comparison endpoints with empty catalog
        test_results["compare_nonexistent_product"] = self.test_compare_nonexistent_product()
        test_results["compare_batch_empty"] = self.test_compare_batch_empty()
        test_results["compare_all_empty_catalog"] = self.test_compare_all_empty_catalog()
        
        # Test catalog import (adds products to the catalog)
        test_results["catalog_import"] = self.test_catalog_import()
        
        # Test compare-all endpoint after importing products
        if test_results["catalog_import"]:
            test_results["compare_all_with_products"] = self.test_compare_all_with_products()
        else:
            self.log("⚠️  Skipping compare-all with products test due to import failure", "WARN")
            test_results["compare_all_with_products"] = False
        
        # Test API consistency
        test_results["api_structure_consistency"] = self.test_api_structure_consistency()
        
        # Test mock data functionality
        test_results["mock_data_availability"] = self.test_mock_data_availability()
        
        # Summary
        passed = sum(1 for result in test_results.values() if result)
        total = len(test_results)
        
        self.log("\n" + "="*50)
        self.log("🏁 TEST SUMMARY")
        self.log("="*50)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
        
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED!")
        else:
            self.log(f"⚠️  {total - passed} tests failed")
        
        return test_results

def main():
    """Main test execution"""
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Exit code based on results
    if all(results.values()):
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()