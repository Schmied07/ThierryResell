#!/usr/bin/env python3
"""
Backend API Testing for Catalog Upload and Column Detection
Tests the catalog file upload and column detection functionality.
"""

import requests
import json
import sys
from pathlib import Path

# Backend URL from environment
BACKEND_URL = "https://catalog-mapper-1.preview.emergentagent.com/api"

# Test authentication credentials
TEST_EMAIL = "testuser@test.com"
TEST_PASSWORD = "testpass123"
TEST_NAME = "Test User"

class BackendTester:
    def __init__(self):
        self.auth_token = None
        self.session = requests.Session()
        
    def log(self, message):
        print(f"✓ {message}")
        
    def error(self, message):
        print(f"✗ {message}")
        
    def test_health_endpoint(self):
        """Test health endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log("Health endpoint working correctly")
                    return True
                else:
                    self.error(f"Health endpoint returned unexpected data: {data}")
                    return False
            else:
                self.error(f"Health endpoint failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.error(f"Health endpoint test failed: {e}")
            return False
            
    def authenticate(self):
        """Register or login user and get auth token"""
        try:
            # Try to register first
            register_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": TEST_NAME
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.auth_token = data.get("token")
                self.log(f"User registered successfully: {data.get('user', {}).get('email')}")
                return True
            elif response.status_code == 400 and ("already exists" in response.text.lower() or "already registered" in response.text.lower()):
                # User already exists, try to login
                login_data = {
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                }
                
                response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("token")
                    self.log(f"User logged in successfully: {data.get('user', {}).get('email')}")
                    return True
                else:
                    self.error(f"Login failed with status {response.status_code}: {response.text}")
                    return False
            else:
                self.error(f"Registration failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Authentication failed: {e}")
            return False
    
    def get_headers(self):
        """Get headers with auth token"""
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def cleanup_catalog(self):
        """Clean up existing catalog data before testing"""
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/catalog/products",
                headers=self.get_headers()
            )
            
            if response.status_code in [200, 404]:
                self.log("✓ Catalog cleaned up for fresh testing")
                return True
            else:
                self.log(f"Catalog cleanup returned status {response.status_code} (continuing anyway)")
                return True  # Don't fail the test if cleanup fails
                
        except Exception as e:
            self.log(f"Catalog cleanup failed: {e} (continuing anyway)")
            return True  # Don't fail the test if cleanup fails
    
    def test_catalog_preview(self):
        """Test catalog preview endpoint with test file"""
        try:
            # Check if test file exists
            test_file_path = Path("/tmp/test_catalog.xlsx")
            if not test_file_path.exists():
                self.error("Test catalog file not found at /tmp/test_catalog.xlsx")
                return False
            
            # Upload file for preview
            with open(test_file_path, "rb") as f:
                files = {"file": (test_file_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                
                response = self.session.post(
                    f"{BACKEND_URL}/catalog/preview",
                    files=files,
                    headers=self.get_headers()
                )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                expected_keys = ["columns", "sample_data", "total_rows", "suggested_mapping"]
                for key in expected_keys:
                    if key not in data:
                        self.error(f"Preview response missing key: {key}")
                        return False
                
                columns = data["columns"]
                suggested_mapping = data["suggested_mapping"]
                total_rows = data["total_rows"]
                sample_data = data["sample_data"]
                
                self.log(f"Preview successful - Found {len(columns)} columns, {total_rows} total rows")
                self.log(f"Columns detected: {columns}")
                
                # Verify expected columns from test file
                expected_columns = ['Product Code', 'Product Title', 'Product Type', 'Manufacturer', 'Supplier Price', 'Product Image URL']
                if columns == expected_columns:
                    self.log("✓ All expected columns detected correctly")
                else:
                    self.error(f"Column mismatch. Expected: {expected_columns}, Got: {columns}")
                    return False
                
                # Check suggested mapping auto-detects the fields
                self.log(f"Suggested mapping: {suggested_mapping}")
                
                # Note: 'Product Code' is not auto-detected as GTIN since it's not in the keyword list
                # This is expected behavior - the auto-detection looks for keywords like 'gtin', 'ean', 'barcode'
                # But 'Product Code' doesn't match these patterns, which is fine
                
                # Verify auto-detection maps the fields it can detect
                expected_auto_mappings = {
                    'Name': 'Product Title', 
                    'Category': 'Product Type',
                    'Brand': 'Manufacturer',
                    'Price': 'Supplier Price',
                    'Image': 'Product Image URL'
                }
                
                mapping_correct = True
                for app_field, expected_column in expected_auto_mappings.items():
                    if suggested_mapping.get(app_field) == expected_column:
                        self.log(f"✓ {app_field} correctly auto-detected as '{expected_column}'")
                    else:
                        self.error(f"✗ {app_field} auto-detection incorrect. Expected: '{expected_column}', Got: '{suggested_mapping.get(app_field)}'")
                        mapping_correct = False
                
                # Check that GTIN is not auto-detected (expected for 'Product Code')
                if 'GTIN' not in suggested_mapping or not suggested_mapping['GTIN']:
                    self.log("✓ GTIN not auto-detected for 'Product Code' (expected - requires manual mapping)")
                else:
                    self.log(f"Note: GTIN was auto-detected as '{suggested_mapping['GTIN']}'")
                
                if not mapping_correct:
                    return False
                
                # Check total rows (should be 3 for test file)
                if total_rows == 3:
                    self.log(f"✓ Total rows count correct: {total_rows}")
                else:
                    self.error(f"Total rows count incorrect. Expected: 3, Got: {total_rows}")
                    return False
                
                # Check sample data has 3 rows
                if len(sample_data) == 3:
                    self.log(f"✓ Sample data provided: {len(sample_data)} rows")
                    
                    # Verify sample data contains expected product data
                    first_row = sample_data[0]
                    if 'Product Code' in first_row and str(first_row['Product Code']) == '3574661517506':
                        self.log("✓ Sample data contains expected product data (Elmex Junior)")
                    else:
                        self.error(f"Sample data doesn't match expected content: {first_row}")
                        return False
                else:
                    self.error(f"Sample data count incorrect. Expected: 3, Got: {len(sample_data)}")
                    return False
                
                return True
                
            else:
                self.error(f"Catalog preview failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Catalog preview test failed: {e}")
            return False
    
    def test_catalog_import(self):
        """Test catalog import endpoint with manual column mapping"""
        try:
            # Check if test file exists
            test_file_path = Path("/tmp/test_catalog.xlsx")
            if not test_file_path.exists():
                self.error("Test catalog file not found at /tmp/test_catalog.xlsx")
                return False
            
            # Test import with manual column mapping as specified in review request
            manual_mapping = {
                'GTIN': 'Product Code',
                'Name': 'Product Title',
                'Category': 'Product Type', 
                'Brand': 'Manufacturer',
                'Price': 'Supplier Price',
                'Image': 'Product Image URL'
            }
            
            self.log(f"Testing import with manual column mapping: {manual_mapping}")
            
            # Test import with manual mapping
            with open(test_file_path, "rb") as f:
                files = {"file": (test_file_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                data = {"column_mapping_json": json.dumps(manual_mapping)}
                
                response = self.session.post(
                    f"{BACKEND_URL}/catalog/import",
                    files=files,
                    data=data,
                    headers=self.get_headers()
                )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                expected_keys = ["success", "imported", "skipped", "total"]
                for key in expected_keys:
                    if key not in data:
                        self.error(f"Import response missing key: {key}")
                        return False
                
                if data["success"]:
                    imported = data["imported"]
                    skipped = data["skipped"]
                    total = data["total"]
                    
                    self.log(f"Catalog import successful: {imported} imported, {skipped} skipped, {total} total")
                    
                    # Should have imported 3 products from test file
                    if imported == 3:
                        self.log(f"✓ Successfully imported all {imported} products from test file")
                        
                        # Verify products were imported correctly by checking catalog
                        return self.verify_imported_products()
                    else:
                        self.error(f"Expected to import 3 products, but imported {imported}")
                        return False
                else:
                    self.error(f"Import marked as not successful: {data}")
                    return False
                    
            elif response.status_code == 400:
                error_text = response.text
                if "missing columns" in error_text.lower() or "colonnes manquantes" in error_text.lower():
                    self.error(f"Import failed with missing columns error: {error_text}")
                    self.error(f"This suggests column mapping is not working properly")
                    return False
                else:
                    self.error(f"Import failed with validation error: {error_text}")
                    return False
            else:
                self.error(f"Catalog import failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Catalog import test failed: {e}")
            return False
    
    def verify_imported_products(self):
        """Verify that products were imported correctly"""
        try:
            response = self.session.get(
                f"{BACKEND_URL}/catalog/products",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                
                if len(products) >= 3:
                    self.log(f"✓ Found {len(products)} products in catalog")
                    
                    # Check for specific test products
                    expected_products = [
                        {"gtin": "3574661517506", "name": "Elmex Junior", "brand": "Elmex"},
                        {"gtin": "3574661517513", "name": "Colgate Max Fresh", "brand": "Colgate"},
                        {"gtin": "8410076404117", "name": "Oral-B Pro Expert", "brand": "Oral-B"}
                    ]
                    
                    found_products = 0
                    for expected in expected_products:
                        for product in products:
                            if (product.get("gtin") == expected["gtin"] and 
                                expected["name"] in product.get("name", "") and
                                product.get("brand") == expected["brand"]):
                                found_products += 1
                                self.log(f"✓ Found expected product: {expected['name']} (GTIN: {expected['gtin']})")
                                break
                    
                    if found_products == 3:
                        self.log("✓ All test products imported correctly with proper field mapping")
                        return True
                    else:
                        self.error(f"Only found {found_products}/3 expected products in catalog")
                        return False
                else:
                    self.error(f"Expected at least 3 products in catalog, found {len(products)}")
                    return False
            else:
                self.error(f"Failed to retrieve catalog products: {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Product verification failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all catalog-related tests"""
        print("🧪 Starting Backend Catalog Testing")
        print("=" * 50)
        
        # Test 1: Health check
        print("\n1. Testing Health Endpoint")
        health_ok = self.test_health_endpoint()
        
        # Test 2: Authentication
        print("\n2. Authentication")
        auth_ok = self.authenticate() if health_ok else False
        
        # Test 2.5: Cleanup existing catalog
        print("\n2.5. Cleaning up existing catalog")
        cleanup_ok = self.cleanup_catalog() if auth_ok else False
        
        # Test 3: Catalog Preview
        print("\n3. Testing Catalog Preview Endpoint")
        preview_ok = self.test_catalog_preview() if auth_ok and cleanup_ok else False
        
        # Test 4: Catalog Import
        print("\n4. Testing Catalog Import Endpoint")
        import_ok = self.test_catalog_import() if auth_ok and cleanup_ok else False
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 Test Summary:")
        print(f"Health Endpoint: {'✅' if health_ok else '❌'}")
        print(f"Authentication: {'✅' if auth_ok else '❌'}")
        print(f"Catalog Preview: {'✅' if preview_ok else '❌'}")
        print(f"Catalog Import: {'✅' if import_ok else '❌'}")
        
        total_tests = 4
        passed_tests = sum([health_ok, auth_ok, preview_ok, import_ok])
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        return {
            "health": health_ok,
            "authentication": auth_ok,
            "preview": preview_ok,
            "import": import_ok,
            "total_passed": passed_tests,
            "total_tests": total_tests
        }

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Exit with error code if any critical tests failed
    if not results["health"] or not results["authentication"]:
        sys.exit(1)
    elif not results["preview"] or not results["import"]:
        sys.exit(2)  # Catalog-specific failures
    else:
        sys.exit(0)  # All tests passed