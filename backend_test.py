#!/usr/bin/env python3
"""
Comprehensive backend API test for Resell Corner application
Tests all endpoints: auth, suppliers, alerts, favorites, search, settings
"""

import requests
import sys
import json
import time
from datetime import datetime
from io import BytesIO

class ResellCornerAPITester:
    def __init__(self, base_url="https://app-quality-check-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, message="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: {message}")
        else:
            print(f"❌ {name}: {message}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "message": message,
            "response_data": response_data
        })

    def run_api_test(self, method, endpoint, expected_status, data=None, files=None, description=""):
        """Run a single API test"""
        url = f"{self.api_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                if files:
                    headers.pop('Content-Type', None)  # Let requests handle it
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    headers.pop('Content-Type', None)  # Let requests handle it
                    response = requests.post(url, headers={k:v for k,v in headers.items() if k != 'Content-Type'}, data=data, files=files, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            message = f"Status {response.status_code} (expected {expected_status})"
            
            if success:
                try:
                    response_data = response.json() if response.content else {}
                    return True, response_data, message
                except:
                    return True, {}, message
            else:
                try:
                    error_data = response.json() if response.content else {}
                    message += f" - {error_data.get('detail', '')}"
                except:
                    message += f" - {response.text[:100]}"
                return False, {}, message
                
        except Exception as e:
            return False, {}, f"Exception: {str(e)}"

    def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        success, response, message = self.run_api_test('GET', '/', 200)
        self.log_test("Root endpoint", success, message, response)
        
        # Test health endpoint
        success, response, message = self.run_api_test('GET', '/health', 200)
        self.log_test("Health check", success, message, response)

    def test_auth_flow(self):
        """Test complete authentication flow"""
        print("\n🔍 Testing Authentication Flow...")
        
        # Generate unique email for testing
        timestamp = datetime.now().strftime('%H%M%S')
        test_email = f"test_{timestamp}@resellcorner.com"
        test_password = "TestPass123!"
        test_name = f"Test User {timestamp}"
        
        # Test registration
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": test_name
        }
        success, response, message = self.run_api_test('POST', '/auth/register', 200, register_data)
        self.log_test("User registration", success, message, response)
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            print(f"   🔑 Token obtained and stored")
        
        # Test login with same credentials
        login_data = {
            "email": test_email,
            "password": test_password
        }
        success, response, message = self.run_api_test('POST', '/auth/login', 200, login_data)
        self.log_test("User login", success, message, response)
        
        # Test getting current user info
        success, response, message = self.run_api_test('GET', '/auth/me', 200)
        self.log_test("Get current user", success, message, response)
        
        # Test login with wrong credentials
        wrong_login = {
            "email": test_email,
            "password": "wrongpassword"
        }
        success, response, message = self.run_api_test('POST', '/auth/login', 401, wrong_login)
        self.log_test("Invalid login rejection", success, message)

    def test_suppliers_crud(self):
        """Test suppliers CRUD operations"""
        print("\n🔍 Testing Suppliers CRUD...")
        
        if not self.token:
            self.log_test("Suppliers CRUD", False, "No auth token available")
            return
        
        # Create supplier
        supplier_data = {
            "name": "Test Amazon Supplier",
            "url": "https://amazon.com",
            "logo_url": "https://amazon.com/favicon.ico",
            "category": "Electronics",
            "notes": "Test supplier for electronics"
        }
        success, response, message = self.run_api_test('POST', '/suppliers', 201, supplier_data)
        self.log_test("Create supplier", success, message, response)
        
        supplier_id = response.get('id') if success else None
        
        # Get all suppliers
        success, response, message = self.run_api_test('GET', '/suppliers', 200)
        self.log_test("Get all suppliers", success, message)
        
        if success:
            suppliers_count = len(response) if isinstance(response, list) else 0
            print(f"   📊 Found {suppliers_count} suppliers")
        
        if supplier_id:
            # Get specific supplier
            success, response, message = self.run_api_test('GET', f'/suppliers/{supplier_id}', 200)
            self.log_test("Get supplier by ID", success, message, response)
            
            # Update supplier
            update_data = {
                "name": "Updated Amazon Supplier",
                "url": "https://amazon.com",
                "category": "Electronics",
                "notes": "Updated test supplier"
            }
            success, response, message = self.run_api_test('PUT', f'/suppliers/{supplier_id}', 200, update_data)
            self.log_test("Update supplier", success, message, response)
            
            # Delete supplier
            success, response, message = self.run_api_test('DELETE', f'/suppliers/{supplier_id}', 200)
            self.log_test("Delete supplier", success, message)

    def test_alerts_management(self):
        """Test alerts management"""
        print("\n🔍 Testing Alerts Management...")
        
        if not self.token:
            self.log_test("Alerts management", False, "No auth token available")
            return
        
        # Create alert
        alert_data = {
            "product_name": "iPhone 15 Pro Max",
            "product_url": "https://apple.com/iphone-15-pro",
            "target_price": 1099.99,
            "current_price": 1299.99
        }
        success, response, message = self.run_api_test('POST', '/alerts', 201, alert_data)
        self.log_test("Create alert", success, message, response)
        
        alert_id = response.get('id') if success else None
        
        # Get all alerts
        success, response, message = self.run_api_test('GET', '/alerts', 200)
        self.log_test("Get all alerts", success, message)
        
        if success:
            alerts_count = len(response) if isinstance(response, list) else 0
            print(f"   📊 Found {alerts_count} alerts")
        
        if alert_id:
            # Toggle alert status
            success, response, message = self.run_api_test('PUT', f'/alerts/{alert_id}/toggle', 200)
            self.log_test("Toggle alert status", success, message, response)
            
            # Delete alert
            success, response, message = self.run_api_test('DELETE', f'/alerts/{alert_id}', 200)
            self.log_test("Delete alert", success, message)

    def test_favorites_management(self):
        """Test favorites management"""
        print("\n🔍 Testing Favorites Management...")
        
        if not self.token:
            self.log_test("Favorites management", False, "No auth token available")
            return
        
        # Create favorite
        favorite_data = {
            "product_name": "Sony WH-1000XM5 Headphones",
            "product_url": "https://sony.com/headphones",
            "image_url": "https://via.placeholder.com/300",
            "notes": "Great noise-canceling headphones",
            "search_query": "sony headphones"
        }
        success, response, message = self.run_api_test('POST', '/favorites', 201, favorite_data)
        self.log_test("Create favorite", success, message, response)
        
        favorite_id = response.get('id') if success else None
        
        # Get all favorites
        success, response, message = self.run_api_test('GET', '/favorites', 200)
        self.log_test("Get all favorites", success, message)
        
        if success:
            favorites_count = len(response) if isinstance(response, list) else 0
            print(f"   📊 Found {favorites_count} favorites")
        
        if favorite_id:
            # Delete favorite
            success, response, message = self.run_api_test('DELETE', f'/favorites/{favorite_id}', 200)
            self.log_test("Delete favorite", success, message)

    def test_search_functionality(self):
        """Test search functionality (text and image)"""
        print("\n🔍 Testing Search Functionality...")
        
        if not self.token:
            self.log_test("Search functionality", False, "No auth token available")
            return
        
        # Test text search
        search_data = {
            "query": "iPhone 15 Pro Max",
            "search_type": "text"
        }
        success, response, message = self.run_api_test('POST', '/search/text', 200, search_data)
        self.log_test("Text search", success, message, response)
        
        if success:
            comparisons_count = len(response.get('comparisons', []))
            print(f"   📊 Found {comparisons_count} price comparisons")
            if response.get('lowest_price'):
                print(f"   💰 Lowest price: {response.get('lowest_price'):.2f}€")
        
        # Test image search with a minimal test image
        try:
            # Create a simple 1x1 pixel PNG for testing
            test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
            
            files = {'file': ('test.png', BytesIO(test_image_data), 'image/png')}
            success, response, message = self.run_api_test('POST', '/search/image', 200, files=files)
            self.log_test("Image search", success, message, response)
            
            if success:
                detected_labels = response.get('detected_labels', [])
                print(f"   🏷️ Detected labels: {', '.join(detected_labels)}")
                
        except Exception as e:
            self.log_test("Image search", False, f"Exception: {str(e)}")
        
        # Test search history
        success, response, message = self.run_api_test('GET', '/history/searches', 200)
        self.log_test("Get search history", success, message)

    def test_settings_api_keys(self):
        """Test API keys settings"""
        print("\n🔍 Testing Settings & API Keys...")
        
        if not self.token:
            self.log_test("Settings API keys", False, "No auth token available")
            return
        
        # Get current API keys status
        success, response, message = self.run_api_test('GET', '/settings/api-keys', 200)
        self.log_test("Get API keys status", success, message, response)
        
        # Update API keys (with test values)
        keys_data = {
            "google_api_key": "test-google-key-123",
            "google_search_engine_id": "test-cx-456",
            "keepa_api_key": "test-keepa-789"
        }
        success, response, message = self.run_api_test('PUT', '/settings/api-keys', 200, keys_data)
        self.log_test("Update API keys", success, message, response)
        
        # Clear one API key
        clear_data = {"google_api_key": ""}
        success, response, message = self.run_api_test('PUT', '/settings/api-keys', 200, clear_data)
        self.log_test("Clear API key", success, message)

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n🔍 Testing Dashboard Stats...")
        
        if not self.token:
            self.log_test("Dashboard stats", False, "No auth token available")
            return
        
        success, response, message = self.run_api_test('GET', '/dashboard/stats', 200)
        self.log_test("Get dashboard stats", success, message, response)
        
        if success:
            stats = response
            print(f"   📊 Suppliers: {stats.get('suppliers_count', 0)}")
            print(f"   📊 Active alerts: {stats.get('active_alerts_count', 0)}")
            print(f"   📊 Favorites: {stats.get('favorites_count', 0)}")
            print(f"   📊 Total searches: {stats.get('total_searches', 0)}")

    def test_keepa_integration(self):
        """Test Keepa API integration (mock)"""
        print("\n🔍 Testing Keepa Integration...")
        
        if not self.token:
            self.log_test("Keepa integration", False, "No auth token available")
            return
        
        # Test with a sample ASIN
        test_asin = "B08N5WRWNW"  # Example ASIN
        success, response, message = self.run_api_test('GET', f'/keepa/product/{test_asin}', 200)
        self.log_test("Keepa product data", success, message, response)
        
        if success and response.get('mock_data'):
            print(f"   🎭 Using mock data for ASIN {test_asin}")

    def test_price_history(self):
        """Test price history"""
        print("\n🔍 Testing Price History...")
        
        if not self.token:
            self.log_test("Price history", False, "No auth token available")
            return
        
        test_product_id = "test-product-123"
        success, response, message = self.run_api_test('GET', f'/history/price/{test_product_id}', 200)
        self.log_test("Get price history", success, message, response)
        
        if success:
            history_count = len(response.get('history', []))
            print(f"   📈 Price history points: {history_count}")

    def run_all_tests(self):
        """Run all tests in sequence"""
        start_time = time.time()
        
        print("=" * 60)
        print("🚀 RESELL CORNER BACKEND API TESTING")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        
        # Run test suites
        self.test_health_endpoints()
        self.test_auth_flow()
        self.test_suppliers_crud()
        self.test_alerts_management()
        self.test_favorites_management()
        self.test_search_functionality()
        self.test_settings_api_keys()
        self.test_dashboard_stats()
        self.test_keepa_integration()
        self.test_price_history()
        
        # Results summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        # Failed tests details
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['name']}: {test['message']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = ResellCornerAPITester()
    
    # Run all tests
    all_passed = tester.run_all_tests()
    
    # Export results for further analysis
    results_file = "/app/test_reports/backend_api_results.json"
    try:
        import os
        os.makedirs("/app/test_reports", exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": tester.tests_run,
                "passed_tests": tester.tests_passed,
                "failed_tests": tester.tests_run - tester.tests_passed,
                "success_rate": tester.tests_passed / tester.tests_run * 100 if tester.tests_run > 0 else 0,
                "results": tester.test_results
            }, f, indent=2)
        print(f"\n📄 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save results file: {e}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())