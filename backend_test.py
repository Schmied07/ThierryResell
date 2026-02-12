#!/usr/bin/env python3

import requests
import sys
import os
import json
from datetime import datetime
import random
import string
from io import BytesIO

class ResellCornerAPITester:
    def __init__(self, base_url="https://resell-pro-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
        if details:
            print(f"     Details: {details}")
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append({"test": test_name, "details": details})

    def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request with automatic token inclusion"""
        url = f"{self.api_url}/{endpoint}"
        headers = kwargs.get('headers', {})
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        kwargs['headers'] = headers
        kwargs.setdefault('timeout', 30)
        
        try:
            if method.upper() == 'GET':
                return requests.get(url, **kwargs)
            elif method.upper() == 'POST':
                return requests.post(url, **kwargs)
            elif method.upper() == 'PUT':
                return requests.put(url, **kwargs)
            elif method.upper() == 'DELETE':
                return requests.delete(url, **kwargs)
        except Exception as e:
            return None

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        response = self.make_request('GET', '')
        success = response and response.status_code == 200
        self.log_result("Root endpoint", success, 
                       f"Status: {response.status_code if response else 'No response'}")
        
        # Test health endpoint  
        response = self.make_request('GET', 'health')
        success = response and response.status_code == 200
        self.log_result("Health check", success,
                       f"Status: {response.status_code if response else 'No response'}")

    def test_user_registration(self):
        """Test user registration"""
        print("\n🔍 Testing User Registration...")
        
        # Generate random user data
        timestamp = str(int(datetime.now().timestamp()))
        test_email = f"test{timestamp}@example.com"
        test_password = "TestPassword123!"
        test_name = f"Test User {timestamp}"
        
        payload = {
            "email": test_email,
            "password": test_password,
            "name": test_name
        }
        
        response = self.make_request('POST', 'auth/register', json=payload)
        
        if response and response.status_code == 200:
            data = response.json()
            if 'token' in data and 'user' in data:
                self.token = data['token']
                self.user_id = data['user']['id']
                self.test_email = test_email
                self.test_password = test_password
                self.log_result("User registration", True, f"User ID: {self.user_id}")
                return True
            else:
                self.log_result("User registration", False, "Missing token or user in response")
        else:
            self.log_result("User registration", False, 
                           f"Status: {response.status_code if response else 'No response'}")
        return False

    def test_user_login(self):
        """Test user login"""
        print("\n🔍 Testing User Login...")
        
        if not hasattr(self, 'test_email'):
            self.log_result("User login", False, "No test user available")
            return False
        
        payload = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        response = self.make_request('POST', 'auth/login', json=payload)
        
        if response and response.status_code == 200:
            data = response.json()
            if 'token' in data:
                self.token = data['token']  # Update token
                self.log_result("User login", True, "Login successful")
                return True
            else:
                self.log_result("User login", False, "Missing token in response")
        else:
            self.log_result("User login", False,
                           f"Status: {response.status_code if response else 'No response'}")
        return False

    def test_auth_me(self):
        """Test get current user info"""
        print("\n🔍 Testing Auth Me...")
        
        if not self.token:
            self.log_result("Auth me", False, "No authentication token")
            return False
        
        response = self.make_request('GET', 'auth/me')
        
        success = response and response.status_code == 200
        if success:
            data = response.json()
            success = 'id' in data and 'email' in data and 'name' in data
        
        self.log_result("Get current user", success,
                       f"Status: {response.status_code if response else 'No response'}")
        return success

    def test_suppliers_crud(self):
        """Test supplier CRUD operations"""
        print("\n🔍 Testing Suppliers CRUD...")
        
        if not self.token:
            self.log_result("Suppliers CRUD", False, "No authentication token")
            return
        
        # Create supplier
        supplier_data = {
            "name": "Test Supplier",
            "url": "https://testsupplier.com",
            "logo_url": "https://testsupplier.com/logo.png",
            "category": "Electronics",
            "notes": "Test supplier for API testing"
        }
        
        response = self.make_request('POST', 'suppliers', json=supplier_data)
        
        if response and response.status_code == 200:
            supplier = response.json()
            supplier_id = supplier.get('id')
            self.log_result("Create supplier", True, f"Supplier ID: {supplier_id}")
            
            # Get suppliers list
            response = self.make_request('GET', 'suppliers')
            success = response and response.status_code == 200
            if success:
                suppliers = response.json()
                success = isinstance(suppliers, list) and len(suppliers) > 0
            self.log_result("Get suppliers list", success,
                           f"Found {len(suppliers) if success else 0} suppliers")
            
            # Get specific supplier
            if supplier_id:
                response = self.make_request('GET', f'suppliers/{supplier_id}')
                success = response and response.status_code == 200
                self.log_result("Get specific supplier", success)
                
                # Update supplier
                update_data = {"name": "Updated Test Supplier"}
                response = self.make_request('PUT', f'suppliers/{supplier_id}', json=update_data)
                success = response and response.status_code == 200
                self.log_result("Update supplier", success)
                
                # Delete supplier
                response = self.make_request('DELETE', f'suppliers/{supplier_id}')
                success = response and response.status_code == 200
                self.log_result("Delete supplier", success)
        else:
            self.log_result("Create supplier", False,
                           f"Status: {response.status_code if response else 'No response'}")

    def test_alerts_crud(self):
        """Test alerts CRUD operations"""
        print("\n🔍 Testing Alerts CRUD...")
        
        if not self.token:
            self.log_result("Alerts CRUD", False, "No authentication token")
            return
        
        # Create alert
        alert_data = {
            "product_name": "iPhone 15 Pro",
            "product_url": "https://apple.com/iphone",
            "target_price": 899.99,
            "current_price": 1199.99
        }
        
        response = self.make_request('POST', 'alerts', json=alert_data)
        
        if response and response.status_code == 200:
            alert = response.json()
            alert_id = alert.get('id')
            self.log_result("Create alert", True, f"Alert ID: {alert_id}")
            
            # Get alerts list
            response = self.make_request('GET', 'alerts')
            success = response and response.status_code == 200
            if success:
                alerts = response.json()
                success = isinstance(alerts, list) and len(alerts) > 0
            self.log_result("Get alerts list", success,
                           f"Found {len(alerts) if success else 0} alerts")
            
            # Toggle alert
            if alert_id:
                response = self.make_request('PUT', f'alerts/{alert_id}/toggle')
                success = response and response.status_code == 200
                self.log_result("Toggle alert", success)
                
                # Delete alert
                response = self.make_request('DELETE', f'alerts/{alert_id}')
                success = response and response.status_code == 200
                self.log_result("Delete alert", success)
        else:
            self.log_result("Create alert", False,
                           f"Status: {response.status_code if response else 'No response'}")

    def test_favorites_crud(self):
        """Test favorites CRUD operations"""
        print("\n🔍 Testing Favorites CRUD...")
        
        if not self.token:
            self.log_result("Favorites CRUD", False, "No authentication token")
            return
        
        # Create favorite
        favorite_data = {
            "product_name": "MacBook Pro 16",
            "product_url": "https://apple.com/macbook-pro",
            "image_url": "https://apple.com/macbook-pro.jpg",
            "notes": "Great laptop for development",
            "search_query": "macbook pro 16 inch"
        }
        
        response = self.make_request('POST', 'favorites', json=favorite_data)
        
        if response and response.status_code == 200:
            favorite = response.json()
            favorite_id = favorite.get('id')
            self.log_result("Create favorite", True, f"Favorite ID: {favorite_id}")
            
            # Get favorites list
            response = self.make_request('GET', 'favorites')
            success = response and response.status_code == 200
            if success:
                favorites = response.json()
                success = isinstance(favorites, list) and len(favorites) > 0
            self.log_result("Get favorites list", success,
                           f"Found {len(favorites) if success else 0} favorites")
            
            # Delete favorite
            if favorite_id:
                response = self.make_request('DELETE', f'favorites/{favorite_id}')
                success = response and response.status_code == 200
                self.log_result("Delete favorite", success)
        else:
            self.log_result("Create favorite", False,
                           f"Status: {response.status_code if response else 'No response'}")

    def test_search_functionality(self):
        """Test search functionality"""
        print("\n🔍 Testing Search Functionality...")
        
        if not self.token:
            self.log_result("Search functionality", False, "No authentication token")
            return
        
        # Test text search
        search_data = {
            "query": "iPhone 15",
            "search_type": "text"
        }
        
        response = self.make_request('POST', 'search/text', json=search_data)
        
        if response and response.status_code == 200:
            result = response.json()
            success = ('product_name' in result and 'comparisons' in result and 
                      isinstance(result['comparisons'], list))
            self.log_result("Text search", success, 
                           f"Found {len(result.get('comparisons', []))} comparisons")
        else:
            self.log_result("Text search", False,
                           f"Status: {response.status_code if response else 'No response'}")

        # Test image search with a simple image
        try:
            # Create a minimal test image (1x1 pixel PNG)
            test_image = BytesIO()
            # Simple 1x1 transparent PNG
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
            test_image.write(png_data)
            test_image.seek(0)
            
            files = {'file': ('test.png', test_image, 'image/png')}
            response = self.make_request('POST', 'search/image', files=files)
            
            if response and response.status_code == 200:
                result = response.json()
                success = ('product_name' in result and 'detected_labels' in result and 
                          isinstance(result.get('comparisons', []), list))
                self.log_result("Image search", success,
                               f"Detected: {len(result.get('detected_labels', []))} labels")
            else:
                self.log_result("Image search", False,
                               f"Status: {response.status_code if response else 'No response'}")
        except Exception as e:
            self.log_result("Image search", False, f"Error: {str(e)}")

    def test_api_keys_settings(self):
        """Test API keys settings"""
        print("\n🔍 Testing API Keys Settings...")
        
        if not self.token:
            self.log_result("API keys settings", False, "No authentication token")
            return
        
        # Get API keys status
        response = self.make_request('GET', 'settings/api-keys')
        
        if response and response.status_code == 200:
            status = response.json()
            success = ('google_api_key_set' in status and 
                      'google_search_engine_id_set' in status and 
                      'keepa_api_key_set' in status)
            self.log_result("Get API keys status", success)
            
            # Update API keys
            keys_data = {
                "google_api_key": "test-google-key",
                "google_search_engine_id": "test-search-engine-id",
                "keepa_api_key": "test-keepa-key"
            }
            
            response = self.make_request('PUT', 'settings/api-keys', json=keys_data)
            success = response and response.status_code == 200
            self.log_result("Update API keys", success)
            
            # Clear API keys
            clear_data = {
                "google_api_key": "",
                "google_search_engine_id": "",
                "keepa_api_key": ""
            }
            
            response = self.make_request('PUT', 'settings/api-keys', json=clear_data)
            success = response and response.status_code == 200
            self.log_result("Clear API keys", success)
            
        else:
            self.log_result("Get API keys status", False,
                           f"Status: {response.status_code if response else 'No response'}")

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n🔍 Testing Dashboard Stats...")
        
        if not self.token:
            self.log_result("Dashboard stats", False, "No authentication token")
            return
        
        response = self.make_request('GET', 'dashboard/stats')
        
        if response and response.status_code == 200:
            stats = response.json()
            required_keys = ['suppliers_count', 'active_alerts_count', 
                           'favorites_count', 'total_searches']
            success = all(key in stats for key in required_keys)
            self.log_result("Dashboard stats", success,
                           f"Stats: {json.dumps(stats, indent=2) if success else 'Missing keys'}")
        else:
            self.log_result("Dashboard stats", False,
                           f"Status: {response.status_code if response else 'No response'}")

    def test_search_history(self):
        """Test search history"""
        print("\n🔍 Testing Search History...")
        
        if not self.token:
            self.log_result("Search history", False, "No authentication token")
            return
        
        response = self.make_request('GET', 'history/searches')
        success = response and response.status_code == 200
        if success:
            history = response.json()
            success = isinstance(history, list)
        
        self.log_result("Get search history", success,
                       f"Found {len(history) if success else 0} entries")

    def run_all_tests(self):
        """Run all backend tests"""
        print("="*60)
        print("🚀 Starting Resell Corner Backend API Tests")
        print("="*60)
        
        # Test basic connectivity
        self.test_health_check()
        
        # Test authentication flow
        if self.test_user_registration():
            self.test_user_login()
            self.test_auth_me()
            
            # Test main features
            self.test_suppliers_crud()
            self.test_alerts_crud() 
            self.test_favorites_crud()
            self.test_search_functionality()
            self.test_api_keys_settings()
            self.test_dashboard_stats()
            self.test_search_history()
        else:
            print("❌ Authentication failed - skipping authenticated tests")
        
        # Final results
        print("="*60)
        print(f"📊 TEST RESULTS: {self.tests_passed}/{self.tests_run} passed")
        print("="*60)
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for fail in self.failed_tests:
                print(f"   • {fail['test']}: {fail['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = ResellCornerAPITester()
    
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())