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
BACKEND_URL = "https://catalog-column-issue.preview.emergentagent.com/api"

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
            
            if response.status_code == 201:
                data = response.json()
                self.auth_token = data.get("token")
                self.log(f"User registered successfully: {data.get('user', {}).get('email')}")
                return True
            elif response.status_code == 400 and "already exists" in response.text.lower():
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
                expected_keys = ["columns", "sample_data", "total_rows", "suggested_mapping", "required_fields", "optional_fields"]
                for key in expected_keys:
                    if key not in data:
                        self.error(f"Preview response missing key: {key}")
                        return False
                
                columns = data["columns"]
                suggested_mapping = data["suggested_mapping"]
                total_rows = data["total_rows"]
                sample_data = data["sample_data"]
                
                self.log(f"Preview successful - Found {len(columns)} columns, {total_rows} total rows")
                self.log(f"Columns detected: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                
                # Check that we don't have metadata columns like "Qogita Catalog", "Unnamed: 1"
                bad_columns = [col for col in columns if "Qogita Catalog" in col or col.startswith("Unnamed")]
                if bad_columns:
                    self.error(f"Found metadata/unnamed columns that should have been skipped: {bad_columns}")
                    return False
                else:
                    self.log("✓ No metadata columns found - header detection working correctly")
                
                # Check suggested mapping has required fields
                required_fields = ["GTIN", "Name", "Category", "Brand", "Price"]
                mapped_fields = [field for field in required_fields if field in suggested_mapping and suggested_mapping[field]]
                
                if len(mapped_fields) >= 3:  # At least 3/5 required fields should be detected
                    self.log(f"Auto-detection working - mapped {len(mapped_fields)}/5 required fields: {mapped_fields}")
                else:
                    self.error(f"Auto-detection failed - only mapped {len(mapped_fields)}/5 required fields: {mapped_fields}")
                    self.error(f"Suggested mapping: {suggested_mapping}")
                    return False
                
                # Check total rows is reasonable (around 453 as mentioned)
                if total_rows > 400 and total_rows < 500:
                    self.log(f"Total rows count looks correct: {total_rows}")
                else:
                    self.log(f"Total rows count: {total_rows} (expected around 453)")
                
                # Check sample data
                if len(sample_data) > 0:
                    self.log(f"Sample data provided: {len(sample_data)} rows")
                    # Check that sample data contains actual product data, not metadata
                    first_row = sample_data[0]
                    if any("Qogita" in str(val) for val in first_row.values() if val):
                        self.error("Sample data contains metadata - header detection may be wrong")
                        return False
                    else:
                        self.log("✓ Sample data looks like actual product data")
                else:
                    self.error("No sample data provided")
                    return False
                
                return True
                
            else:
                self.error(f"Catalog preview failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Catalog preview test failed: {e}")
            return False
    
    def test_catalog_import(self):
        """Test catalog import endpoint"""
        try:
            # Check if test file exists
            test_file_path = Path("/tmp/test_catalog.xlsx")
            if not test_file_path.exists():
                self.error("Test catalog file not found at /tmp/test_catalog.xlsx")
                return False
            
            # First get the column mapping from preview
            with open(test_file_path, "rb") as f:
                files = {"file": (test_file_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                
                response = self.session.post(
                    f"{BACKEND_URL}/catalog/preview",
                    files=files,
                    headers=self.get_headers()
                )
            
            if response.status_code != 200:
                self.error(f"Failed to get preview for import test: {response.status_code}")
                return False
                
            preview_data = response.json()
            suggested_mapping = preview_data["suggested_mapping"]
            
            # Test import with suggested mapping
            with open(test_file_path, "rb") as f:
                files = {"file": (test_file_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                data = {"column_mapping_json": json.dumps(suggested_mapping)}
                
                response = self.session.post(
                    f"{BACKEND_URL}/catalog/import",
                    files=files,
                    data=data,
                    headers=self.get_headers()
                )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                expected_keys = ["success", "imported", "skipped", "total", "exchange_rate"]
                for key in expected_keys:
                    if key not in data:
                        self.error(f"Import response missing key: {key}")
                        return False
                
                if data["success"]:
                    imported = data["imported"]
                    skipped = data["skipped"]
                    total = data["total"]
                    
                    self.log(f"Catalog import successful: {imported} imported, {skipped} skipped, {total} total")
                    
                    # Should have imported some products
                    if imported > 0:
                        self.log(f"✓ Successfully imported {imported} products")
                        return True
                    else:
                        self.error("No products were imported - possible column mapping issue")
                        return False
                else:
                    self.error(f"Import marked as not successful: {data}")
                    return False
                    
            elif response.status_code == 400:
                error_text = response.text
                if "missing columns" in error_text.lower() or "colonnes manquantes" in error_text.lower():
                    self.error(f"Import failed with missing columns error: {error_text}")
                    self.error(f"This suggests column auto-detection or mapping is not working properly")
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
        
        # Test 3: Catalog Preview
        print("\n3. Testing Catalog Preview Endpoint")
        preview_ok = self.test_catalog_preview() if auth_ok else False
        
        # Test 4: Catalog Import
        print("\n4. Testing Catalog Import Endpoint")
        import_ok = self.test_catalog_import() if auth_ok else False
        
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