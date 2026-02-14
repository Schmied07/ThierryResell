#!/usr/bin/env python3

import requests
import json
import sys
import os
from typing import Dict, Any, Optional

# Backend URL from frontend .env
BACKEND_URL = "https://app-quality-check-2.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        self.token = None
        self.user_id = None
        self.test_results = {}
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results[test_name] = {"success": success, "details": details}
        
    def make_request(self, method: str, endpoint: str, data: Any = None, files: Dict = None) -> Dict[str, Any]:
        """Make HTTP request and return parsed response"""
        url = f"{BACKEND_URL}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=30)
            elif method.upper() == 'POST':
                if files:
                    # Remove content-type header for file uploads
                    headers = {k: v for k, v in self.session.headers.items() if k.lower() != 'content-type'}
                    response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
                else:
                    response = self.session.post(url, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=30)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            # Try to parse JSON response
            try:
                result = response.json()
            except:
                result = {"text": response.text, "status_code": response.status_code}
                
            result["status_code"] = response.status_code
            result["success"] = 200 <= response.status_code < 300
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False, "status_code": 0}
    
    def set_auth_token(self, token: str):
        """Set authorization token for subsequent requests"""
        self.token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
    
    def test_health_check(self):
        """Test GET /api/health"""
        response = self.make_request('GET', '/health')
        
        if response.get("success") and response.get("status") == "healthy":
            self.log_test("Health Check", True, "API is healthy")
        else:
            self.log_test("Health Check", False, f"Response: {response}")
    
    def test_user_registration(self):
        """Test POST /api/auth/register"""
        user_data = {
            "email": "john.doe@example.com",
            "password": "securepassword123",
            "name": "John Doe"
        }
        
        response = self.make_request('POST', '/auth/register', user_data)
        
        if response.get("success") and "token" in response and "user" in response:
            self.log_test("User Registration", True, f"User created with ID: {response['user']['id']}")
            return response["token"], response["user"]["id"]
        else:
            self.log_test("User Registration", False, f"Response: {response}")
            return None, None
    
    def test_user_login(self):
        """Test POST /api/auth/login"""
        login_data = {
            "email": "john.doe@example.com",
            "password": "securepassword123"
        }
        
        response = self.make_request('POST', '/auth/login', login_data)
        
        if response.get("success") and "token" in response:
            self.log_test("User Login", True, f"Login successful")
            return response["token"]
        else:
            self.log_test("User Login", False, f"Response: {response}")
            return None
    
    def test_get_current_user(self):
        """Test GET /api/auth/me"""
        response = self.make_request('GET', '/auth/me')
        
        if response.get("success") and "id" in response and "email" in response:
            self.log_test("Get Current User", True, f"User info retrieved: {response['name']}")
        else:
            self.log_test("Get Current User", False, f"Response: {response}")
    
    def test_api_keys_management(self):
        """Test GET and PUT /api/settings/api-keys"""
        # Test GET
        response = self.make_request('GET', '/settings/api-keys')
        
        if response.get("success"):
            self.log_test("Get API Keys", True, "API keys status retrieved")
            
            # Test PUT - update API keys
            api_keys_data = {
                "google_api_key": "test-google-key-123",
                "google_search_engine_id": "test-engine-id",
                "keepa_api_key": "test-keepa-key-456"
            }
            
            update_response = self.make_request('PUT', '/settings/api-keys', api_keys_data)
            
            if update_response.get("success"):
                self.log_test("Update API Keys", True, "API keys updated successfully")
            else:
                self.log_test("Update API Keys", False, f"Response: {update_response}")
        else:
            self.log_test("Get API Keys", False, f"Response: {response}")
    
    def test_suppliers_crud(self):
        """Test Suppliers CRUD operations"""
        # Create supplier
        supplier_data = {
            "name": "Tech Warehouse",
            "url": "https://techwarehouse.com",
            "logo_url": "https://techwarehouse.com/logo.png",
            "category": "Electronics",
            "notes": "Good prices on tech items"
        }
        
        create_response = self.make_request('POST', '/suppliers', supplier_data)
        
        if create_response.get("success") and "id" in create_response:
            supplier_id = create_response["id"]
            self.log_test("Create Supplier", True, f"Supplier created with ID: {supplier_id}")
            
            # Test GET all suppliers
            get_all_response = self.make_request('GET', '/suppliers')
            if get_all_response.get("success") and isinstance(get_all_response.get("response", get_all_response), list):
                self.log_test("Get All Suppliers", True, f"Retrieved {len(get_all_response.get('response', get_all_response))} suppliers")
            else:
                self.log_test("Get All Suppliers", False, f"Response: {get_all_response}")
            
            # Test GET single supplier
            get_one_response = self.make_request('GET', f'/suppliers/{supplier_id}')
            if get_one_response.get("success") and get_one_response.get("id") == supplier_id:
                self.log_test("Get Single Supplier", True, f"Retrieved supplier: {get_one_response['name']}")
            else:
                self.log_test("Get Single Supplier", False, f"Response: {get_one_response}")
            
            # Test PUT - update supplier
            update_data = {
                "name": "Updated Tech Warehouse",
                "url": "https://techwarehouse.com",
                "category": "Electronics & Gadgets"
            }
            
            update_response = self.make_request('PUT', f'/suppliers/{supplier_id}', update_data)
            if update_response.get("success"):
                self.log_test("Update Supplier", True, f"Supplier updated")
            else:
                self.log_test("Update Supplier", False, f"Response: {update_response}")
            
            # Test DELETE supplier
            delete_response = self.make_request('DELETE', f'/suppliers/{supplier_id}')
            if delete_response.get("success"):
                self.log_test("Delete Supplier", True, "Supplier deleted successfully")
            else:
                self.log_test("Delete Supplier", False, f"Response: {delete_response}")
        else:
            self.log_test("Create Supplier", False, f"Response: {create_response}")
    
    def test_alerts_crud(self):
        """Test Alerts CRUD operations"""
        # Create alert
        alert_data = {
            "product_name": "iPhone 15 Pro",
            "product_url": "https://example.com/iphone15pro",
            "target_price": 999.99,
            "current_price": 1199.99
        }
        
        create_response = self.make_request('POST', '/alerts', alert_data)
        
        if create_response.get("success") and "id" in create_response:
            alert_id = create_response["id"]
            self.log_test("Create Alert", True, f"Alert created with ID: {alert_id}")
            
            # Test GET all alerts
            get_all_response = self.make_request('GET', '/alerts')
            if get_all_response.get("success") and isinstance(get_all_response.get("response", get_all_response), list):
                self.log_test("Get All Alerts", True, f"Retrieved {len(get_all_response.get('response', get_all_response))} alerts")
            else:
                self.log_test("Get All Alerts", False, f"Response: {get_all_response}")
            
            # Test toggle alert
            toggle_response = self.make_request('PUT', f'/alerts/{alert_id}/toggle')
            if toggle_response.get("success") and "is_active" in toggle_response:
                self.log_test("Toggle Alert", True, f"Alert toggled to: {toggle_response['is_active']}")
            else:
                self.log_test("Toggle Alert", False, f"Response: {toggle_response}")
            
            # Test DELETE alert
            delete_response = self.make_request('DELETE', f'/alerts/{alert_id}')
            if delete_response.get("success"):
                self.log_test("Delete Alert", True, "Alert deleted successfully")
            else:
                self.log_test("Delete Alert", False, f"Response: {delete_response}")
        else:
            self.log_test("Create Alert", False, f"Response: {create_response}")
    
    def test_favorites_crud(self):
        """Test Favorites CRUD operations"""
        # Create favorite
        favorite_data = {
            "product_name": "MacBook Pro M3",
            "product_url": "https://example.com/macbook-pro-m3",
            "image_url": "https://example.com/images/macbook.jpg",
            "notes": "Great laptop for development",
            "search_query": "MacBook Pro M3 2024"
        }
        
        create_response = self.make_request('POST', '/favorites', favorite_data)
        
        if create_response.get("success") and "id" in create_response:
            favorite_id = create_response["id"]
            self.log_test("Create Favorite", True, f"Favorite created with ID: {favorite_id}")
            
            # Test GET all favorites
            get_all_response = self.make_request('GET', '/favorites')
            if get_all_response.get("success") and isinstance(get_all_response.get("response", get_all_response), list):
                self.log_test("Get All Favorites", True, f"Retrieved {len(get_all_response.get('response', get_all_response))} favorites")
            else:
                self.log_test("Get All Favorites", False, f"Response: {get_all_response}")
            
            # Test DELETE favorite
            delete_response = self.make_request('DELETE', f'/favorites/{favorite_id}')
            if delete_response.get("success"):
                self.log_test("Delete Favorite", True, "Favorite deleted successfully")
            else:
                self.log_test("Delete Favorite", False, f"Response: {delete_response}")
        else:
            self.log_test("Create Favorite", False, f"Response: {create_response}")
    
    def test_text_search(self):
        """Test POST /api/search/text"""
        search_data = {
            "query": "iPhone 15",
            "search_type": "text"
        }
        
        response = self.make_request('POST', '/search/text', search_data)
        
        if response.get("success") and "product_name" in response and "comparisons" in response:
            self.log_test("Text Search", True, f"Search returned {len(response['comparisons'])} price comparisons")
        else:
            self.log_test("Text Search", False, f"Response: {response}")
    
    def test_dashboard_stats(self):
        """Test GET /api/dashboard/stats"""
        response = self.make_request('GET', '/dashboard/stats')
        
        if (response.get("success") and 
            "suppliers_count" in response and 
            "active_alerts_count" in response and
            "favorites_count" in response):
            self.log_test("Dashboard Stats", True, f"Retrieved dashboard stats")
        else:
            self.log_test("Dashboard Stats", False, f"Response: {response}")
    
    def test_search_history(self):
        """Test GET /api/history/searches"""
        response = self.make_request('GET', '/history/searches')
        
        if response.get("success") and isinstance(response.get("response", response), list):
            self.log_test("Search History", True, f"Retrieved {len(response.get('response', response))} search history items")
        else:
            self.log_test("Search History", False, f"Response: {response}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"🚀 Starting Resell Corner Backend API Tests")
        print(f"📡 Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test health check first
        self.test_health_check()
        
        # Test user registration and login
        token, user_id = self.test_user_registration()
        if not token:
            # Try login with existing user
            token = self.test_user_login()
        
        if token:
            self.set_auth_token(token)
            self.user_id = user_id
            
            # Test authenticated endpoints
            self.test_get_current_user()
            self.test_api_keys_management()
            self.test_suppliers_crud()
            self.test_alerts_crud()
            self.test_favorites_crud()
            self.test_text_search()
            self.test_dashboard_stats()
            self.test_search_history()
        else:
            print("❌ Unable to authenticate - skipping authenticated endpoint tests")
        
        # Print summary
        print("=" * 60)
        print("📊 TEST SUMMARY:")
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        
        if failed_tests > 0:
            print("\n🚨 FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result["success"]:
                    print(f"   ❌ {test_name}: {result['details']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)