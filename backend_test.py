#!/usr/bin/env python3
"""
Backend API Testing for Flexible Catalog Import Feature
Tests that only GTIN and Price are required fields for catalog import.
Name, Category, Brand are now optional fields.
"""

import requests
import json
import sys
import openpyxl
from pathlib import Path

# Backend URL from environment
BACKEND_URL = "https://price-id-import.preview.emergentagent.com/api"

# Test authentication credentials for flexible catalog import testing
TEST_EMAIL = "flextest@test.com"
TEST_PASSWORD = "test123"
TEST_NAME = "FlexTest"

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
    
    def create_minimal_excel_file(self):
        """Create a minimal Excel file with just EAN and price columns"""
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(['EAN', 'prix_achat'])
            ws.append(['8718951388574', 5.99])
            ws.append(['3014260033279', 3.50])
            
            file_path = '/tmp/test_minimal.xlsx'
            wb.save(file_path)
            self.log(f"Created minimal test Excel file: {file_path}")
            return file_path
        except Exception as e:
            self.error(f"Failed to create minimal Excel file: {e}")
            return None
    
    def test_catalog_preview_flexible_fields(self):
        """Test catalog preview endpoint returns correct required/optional fields"""
        try:
            # Use existing catalog sample file first
            test_file_path = Path("/app/catalog_sample.xlsx")
            if not test_file_path.exists():
                test_file_path = Path("/app/test_catalog.xlsx")
                if not test_file_path.exists():
                    self.error("No test catalog file found at /app/catalog_sample.xlsx or /app/test_catalog.xlsx")
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
                
                # Validate response structure includes new flexible field structure
                expected_keys = ["columns", "sample_data", "total_rows", "suggested_mapping", "required_fields", "optional_fields"]
                for key in expected_keys:
                    if key not in data:
                        self.error(f"Preview response missing key: {key}")
                        return False
                
                required_fields = data["required_fields"]
                optional_fields = data["optional_fields"]
                
                self.log(f"Preview successful - Required fields: {required_fields}")
                self.log(f"Optional fields: {optional_fields}")
                
                # CRITICAL TEST: Verify required_fields contains ONLY ['GTIN', 'Price']
                expected_required = ['GTIN', 'Price']
                if required_fields == expected_required:
                    self.log(f"✅ CRITICAL: Required fields correct: {required_fields}")
                else:
                    self.error(f"❌ CRITICAL: Required fields incorrect! Expected: {expected_required}, Got: {required_fields}")
                    return False
                
                # CRITICAL TEST: Verify optional_fields includes Name, Category, Brand, Image
                expected_optional = ['Name', 'Category', 'Brand', 'Image']
                for field in expected_optional:
                    if field in optional_fields:
                        self.log(f"✅ Optional field present: {field}")
                    else:
                        self.error(f"❌ Missing expected optional field: {field}")
                        return False
                
                return True
                
            else:
                self.error(f"Catalog preview failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Catalog preview test failed: {e}")
            return False
    
    def test_catalog_import_minimal_fields(self):
        """Test catalog import with ONLY GTIN and Price mapped (no Name, Category, Brand)"""
        try:
            # Create minimal Excel file with just EAN and price columns
            minimal_file_path = self.create_minimal_excel_file()
            if not minimal_file_path:
                return False
            
            # Test import with ONLY GTIN and Price mapped (other fields should get defaults)
            minimal_mapping = {
                'GTIN': 'EAN',
                'Price': 'prix_achat'
                # Deliberately omitting Name, Category, Brand - they should get 'Non spécifié' defaults
            }
            
            self.log(f"Testing minimal import with only required fields mapped: {minimal_mapping}")
            
            # Test import with minimal mapping
            with open(minimal_file_path, "rb") as f:
                files = {"file": ("test_minimal.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                data = {"column_mapping_json": json.dumps(minimal_mapping)}
                
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
                    
                    self.log(f"✅ CRITICAL: Minimal catalog import successful: {imported} imported, {skipped} skipped, {total} total")
                    
                    # Should have imported 2 products from minimal file
                    if imported == 2:
                        self.log(f"✅ Successfully imported all {imported} products with only GTIN+Price mapping")
                        
                        # Verify products were imported with 'Non spécifié' defaults
                        return self.verify_minimal_imported_products()
                    else:
                        self.error(f"Expected to import 2 products, but imported {imported}")
                        return False
                else:
                    self.error(f"Import marked as not successful: {data}")
                    return False
                    
            else:
                self.error(f"❌ CRITICAL: Minimal catalog import failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Minimal catalog import test failed: {e}")
            return False
    
    def verify_minimal_imported_products(self):
        """Verify that minimal products were imported with 'Non spécifié' defaults"""
        try:
            response = self.session.get(
                f"{BACKEND_URL}/catalog/products",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                
                if len(products) >= 2:
                    self.log(f"✓ Found {len(products)} products in catalog")
                    
                    # Check for specific test products with 'Non spécifié' defaults
                    expected_gtins = ['8718951388574', '3014260033279']
                    
                    found_products = 0
                    for expected_gtin in expected_gtins:
                        for product in products:
                            if product.get("gtin") == expected_gtin:
                                found_products += 1
                                
                                # CRITICAL TEST: Verify default values for unmapped fields
                                name = product.get("name")
                                category = product.get("category")
                                brand = product.get("brand")
                                price = product.get("supplier_price_eur")
                                
                                self.log(f"Product {expected_gtin}: name='{name}', category='{category}', brand='{brand}', price={price}€")
                                
                                # Check that unmapped fields have 'Non spécifié' default
                                if name == 'Non spécifié':
                                    self.log(f"✅ CRITICAL: Product {expected_gtin} has correct default name: '{name}'")
                                else:
                                    self.error(f"❌ CRITICAL: Product {expected_gtin} should have name='Non spécifié', got '{name}'")
                                    return False
                                    
                                if category == 'Non spécifié':
                                    self.log(f"✅ CRITICAL: Product {expected_gtin} has correct default category: '{category}'")
                                else:
                                    self.error(f"❌ CRITICAL: Product {expected_gtin} should have category='Non spécifié', got '{category}'")
                                    return False
                                    
                                if brand == 'Non spécifié':
                                    self.log(f"✅ CRITICAL: Product {expected_gtin} has correct default brand: '{brand}'")
                                else:
                                    self.error(f"❌ CRITICAL: Product {expected_gtin} should have brand='Non spécifié', got '{brand}'")
                                    return False
                                
                                # Check that price was imported correctly
                                expected_price = 5.99 if expected_gtin == '8718951388574' else 3.50
                                # Allow for small conversion/rounding differences
                                if abs(price - expected_price) < 0.1:
                                    self.log(f"✅ Product {expected_gtin} has correct price: {price}€")
                                else:
                                    self.error(f"❌ Product {expected_gtin} has incorrect price. Expected ~{expected_price}€, got {price}€")
                                    return False
                                
                                break
                    
                    if found_products == 2:
                        self.log("✅ CRITICAL: All minimal test products imported correctly with 'Non spécifié' defaults")
                        return True
                    else:
                        self.error(f"Only found {found_products}/2 expected products in catalog")
                        return False
                else:
                    self.error(f"Expected at least 2 products in catalog, found {len(products)}")
                    return False
            else:
                self.error(f"Failed to retrieve catalog products: {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Minimal product verification failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all flexible catalog import tests"""
        print("🧪 Starting Flexible Catalog Import Testing")
        print("Testing that only GTIN and Price are required fields")
        print("=" * 60)
        
        # Test 1: Health check
        print("\n1. Testing Health Endpoint")
        health_ok = self.test_health_endpoint()
        
        # Test 2: Authentication with new test user
        print("\n2. Authentication (flextest@test.com)")
        auth_ok = self.authenticate() if health_ok else False
        
        # Test 2.5: Cleanup existing catalog
        print("\n2.5. Cleaning up existing catalog")
        cleanup_ok = self.cleanup_catalog() if auth_ok else False
        
        # Test 3: Catalog Preview - Check Required/Optional Fields
        print("\n3. Testing Catalog Preview - Required/Optional Fields Structure")
        preview_ok = self.test_catalog_preview_flexible_fields() if auth_ok and cleanup_ok else False
        
        # Test 4: Minimal Catalog Import - GTIN + Price Only
        print("\n4. CRITICAL TEST: Import with Only GTIN + Price Mapped")
        minimal_import_ok = self.test_catalog_import_minimal_fields() if auth_ok and cleanup_ok else False
        
        # Test 5: Verify products have 'Non spécifié' defaults
        print("\n5. Verified products have correct default values")
        # This is already included in minimal_import_ok verification
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 Flexible Catalog Import Test Summary:")
        print(f"Health Endpoint: {'✅' if health_ok else '❌'}")
        print(f"Authentication: {'✅' if auth_ok else '❌'}")
        print(f"Required/Optional Fields Structure: {'✅' if preview_ok else '❌'}")
        print(f"MINIMAL Import (GTIN+Price only): {'✅' if minimal_import_ok else '❌'}")
        
        total_tests = 4
        passed_tests = sum([health_ok, auth_ok, preview_ok, minimal_import_ok])
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        # Critical results
        if preview_ok and minimal_import_ok:
            print("\n🎉 FLEXIBLE CATALOG IMPORT FEATURE: ✅ WORKING")
            print("✅ Only GTIN and Price are required")
            print("✅ Name, Category, Brand are optional with 'Non spécifié' defaults")
        else:
            print("\n❌ FLEXIBLE CATALOG IMPORT FEATURE: FAILED")
            if not preview_ok:
                print("❌ Preview endpoint doesn't return correct required/optional fields")
            if not minimal_import_ok:
                print("❌ Import with only GTIN+Price fails or doesn't set proper defaults")
        
        return {
            "health": health_ok,
            "authentication": auth_ok,
            "preview": preview_ok,
            "minimal_import": minimal_import_ok,
            "total_passed": passed_tests,
            "total_tests": total_tests
        }

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Exit with error code if any critical tests failed
    if not results["health"] or not results["authentication"]:
        sys.exit(1)
    elif not results["preview"] or not results["minimal_import"]:
        sys.exit(2)  # Flexible catalog import failures
    else:
        sys.exit(0)  # All tests passed