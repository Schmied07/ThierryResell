#!/usr/bin/env python3
"""
Backend Test Script - DataForSEO Google Shopping Integration
Tests the new DataForSEO endpoints and authentication flow
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://price-id-import.preview.emergentagent.com/api"
TEST_USER = {
    "email": "dataforseo_test@test.com", 
    "password": "test123",
    "name": "DFSTest"
}

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def make_request(self, method: str, endpoint: str, data=None, headers=None):
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}{endpoint}"
        if headers is None:
            headers = {}
        
        if self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
            
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                headers['Content-Type'] = 'application/json'
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                headers['Content-Type'] = 'application/json'
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def test_auth_registration(self):
        """Test user registration"""
        try:
            response = self.make_request('POST', '/auth/register', TEST_USER)
            
            if response and response.status_code in [200, 201]:
                data = response.json()
                if 'token' in data:
                    self.jwt_token = data['token']
                    self.log_result("User Registration", True, f"User registered successfully, JWT received")
                    return True
                else:
                    self.log_result("User Registration", False, "No JWT token in response")
                    return False
            elif response and response.status_code == 400:
                # User might already exist, try login instead
                return self.test_auth_login()
            else:
                status = response.status_code if response else "No response"
                self.log_result("User Registration", False, f"Registration failed with status {status}")
                return False
                
        except Exception as e:
            self.log_result("User Registration", False, f"Exception: {str(e)}")
            return False

    def test_auth_login(self):
        """Test user login as fallback"""
        try:
            login_data = {"email": TEST_USER["email"], "password": TEST_USER["password"]}
            response = self.make_request('POST', '/auth/login', login_data)
            
            if response and response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    self.jwt_token = data['token']
                    self.log_result("User Login (fallback)", True, "Login successful, JWT received")
                    return True
                else:
                    self.log_result("User Login (fallback)", False, "No JWT token in login response")
                    return False
            else:
                status = response.status_code if response else "No response"
                self.log_result("User Login (fallback)", False, f"Login failed with status {status}")
                return False
                
        except Exception as e:
            self.log_result("User Login (fallback)", False, f"Exception: {str(e)}")
            return False

    def test_get_api_keys_initial(self):
        """Test GET /api/settings/api-keys - check initial state"""
        try:
            response = self.make_request('GET', '/settings/api-keys')
            
            if response and response.status_code == 200:
                data = response.json()
                
                # Check for all required fields
                required_fields = [
                    'google_api_key_set', 'google_search_engine_id_set', 'keepa_api_key_set',
                    'dataforseo_login_set', 'dataforseo_password_set', 'use_google_shopping'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("GET /api/settings/api-keys - Initial State", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Check initial values - should all be false initially
                if (data['dataforseo_login_set'] == False and 
                    data['dataforseo_password_set'] == False and 
                    data['use_google_shopping'] == False):
                    self.log_result("GET /api/settings/api-keys - Initial State", True, 
                                  f"All DataForSEO fields are false initially as expected: {data}")
                    return True
                else:
                    self.log_result("GET /api/settings/api-keys - Initial State", False, 
                                  f"Unexpected initial values: {data}")
                    return False
                    
            else:
                status = response.status_code if response else "No response"
                self.log_result("GET /api/settings/api-keys - Initial State", False, 
                              f"Request failed with status {status}")
                return False
                
        except Exception as e:
            self.log_result("GET /api/settings/api-keys - Initial State", False, f"Exception: {str(e)}")
            return False

    def test_save_dataforseo_credentials(self):
        """Test PUT /api/settings/api-keys - Save DataForSEO credentials"""
        try:
            credentials = {
                "dataforseo_login": "test_login",
                "dataforseo_password": "test_pass"
            }
            
            response = self.make_request('PUT', '/settings/api-keys', credentials)
            
            if response and response.status_code == 200:
                data = response.json()
                
                if (data.get('dataforseo_login_set') == True and 
                    data.get('dataforseo_password_set') == True):
                    self.log_result("PUT /api/settings/api-keys - Save DataForSEO credentials", True, 
                                  f"DataForSEO credentials saved: login_set={data['dataforseo_login_set']}, password_set={data['dataforseo_password_set']}")
                    return True
                else:
                    self.log_result("PUT /api/settings/api-keys - Save DataForSEO credentials", False, 
                                  f"DataForSEO flags not set correctly: {data}")
                    return False
                    
            else:
                status = response.status_code if response else "No response"
                self.log_result("PUT /api/settings/api-keys - Save DataForSEO credentials", False, 
                              f"Request failed with status {status}")
                return False
                
        except Exception as e:
            self.log_result("PUT /api/settings/api-keys - Save DataForSEO credentials", False, f"Exception: {str(e)}")
            return False

    def test_toggle_google_search_mode_to_shopping(self):
        """Test PUT /api/settings/google-search-mode - Toggle to Google Shopping"""
        try:
            response = self.make_request('PUT', '/settings/google-search-mode')
            
            if response and response.status_code == 200:
                data = response.json()
                
                if (data.get('use_google_shopping') == True and 
                    data.get('mode') == 'google_shopping'):
                    self.log_result("PUT /api/settings/google-search-mode - Toggle to Shopping", True, 
                                  f"Successfully toggled to Google Shopping: {data}")
                    return True
                else:
                    self.log_result("PUT /api/settings/google-search-mode - Toggle to Shopping", False, 
                                  f"Toggle failed: {data}")
                    return False
                    
            else:
                status = response.status_code if response else "No response"
                self.log_result("PUT /api/settings/google-search-mode - Toggle to Shopping", False, 
                              f"Request failed with status {status}")
                return False
                
        except Exception as e:
            self.log_result("PUT /api/settings/google-search-mode - Toggle to Shopping", False, f"Exception: {str(e)}")
            return False

    def test_toggle_google_search_mode_to_search(self):
        """Test PUT /api/settings/google-search-mode - Toggle back to Google Search"""
        try:
            response = self.make_request('PUT', '/settings/google-search-mode')
            
            if response and response.status_code == 200:
                data = response.json()
                
                if (data.get('use_google_shopping') == False and 
                    data.get('mode') == 'google_search'):
                    self.log_result("PUT /api/settings/google-search-mode - Toggle to Search", True, 
                                  f"Successfully toggled back to Google Search: {data}")
                    return True
                else:
                    self.log_result("PUT /api/settings/google-search-mode - Toggle to Search", False, 
                                  f"Toggle failed: {data}")
                    return False
                    
            else:
                status = response.status_code if response else "No response"
                self.log_result("PUT /api/settings/google-search-mode - Toggle to Search", False, 
                              f"Request failed with status {status}")
                return False
                
        except Exception as e:
            self.log_result("PUT /api/settings/google-search-mode - Toggle to Search", False, f"Exception: {str(e)}")
            return False

    def test_verify_toggle_persistence(self):
        """Test that toggle state persists by checking GET /api/settings/api-keys"""
        try:
            response = self.make_request('GET', '/settings/api-keys')
            
            if response and response.status_code == 200:
                data = response.json()
                
                # Should be false after previous toggle back to search
                if data.get('use_google_shopping') == False:
                    self.log_result("Verify Toggle Persistence", True, 
                                  f"Toggle state persisted correctly: use_google_shopping={data['use_google_shopping']}")
                    return True
                else:
                    self.log_result("Verify Toggle Persistence", False, 
                                  f"Toggle state not persisted: {data}")
                    return False
                    
            else:
                status = response.status_code if response else "No response"
                self.log_result("Verify Toggle Persistence", False, 
                              f"Request failed with status {status}")
                return False
                
        except Exception as e:
            self.log_result("Verify Toggle Persistence", False, f"Exception: {str(e)}")
            return False

    def test_toggle_to_shopping_and_verify(self):
        """Test toggling to shopping mode and verifying persistence"""
        try:
            # Toggle to shopping
            response = self.make_request('PUT', '/settings/google-search-mode')
            
            if response and response.status_code == 200:
                data = response.json()
                
                if data.get('use_google_shopping') != True:
                    self.log_result("Toggle to Shopping and Verify", False, 
                                  f"Failed to toggle to shopping: {data}")
                    return False
                
                # Verify persistence with GET request
                get_response = self.make_request('GET', '/settings/api-keys')
                
                if get_response and get_response.status_code == 200:
                    get_data = get_response.json()
                    
                    if get_data.get('use_google_shopping') == True:
                        self.log_result("Toggle to Shopping and Verify", True, 
                                      f"Toggle to shopping persisted correctly: use_google_shopping={get_data['use_google_shopping']}")
                        return True
                    else:
                        self.log_result("Toggle to Shopping and Verify", False, 
                                      f"Toggle to shopping not persisted: {get_data}")
                        return False
                else:
                    self.log_result("Toggle to Shopping and Verify", False, 
                                  "Failed to verify persistence with GET request")
                    return False
                    
            else:
                status = response.status_code if response else "No response"
                self.log_result("Toggle to Shopping and Verify", False, 
                              f"Toggle request failed with status {status}")
                return False
                
        except Exception as e:
            self.log_result("Toggle to Shopping and Verify", False, f"Exception: {str(e)}")
            return False

    def test_clear_dataforseo_keys(self):
        """Test PUT /api/settings/api-keys - Clear DataForSEO credentials"""
        try:
            clear_data = {
                "dataforseo_login": ""
            }
            
            response = self.make_request('PUT', '/settings/api-keys', clear_data)
            
            if response and response.status_code == 200:
                data = response.json()
                
                if data.get('dataforseo_login_set') == False:
                    self.log_result("PUT /api/settings/api-keys - Clear DataForSEO keys", True, 
                                  f"DataForSEO login cleared successfully: login_set={data['dataforseo_login_set']}")
                    return True
                else:
                    self.log_result("PUT /api/settings/api-keys - Clear DataForSEO keys", False, 
                                  f"DataForSEO login not cleared: {data}")
                    return False
                    
            else:
                status = response.status_code if response else "No response"
                self.log_result("PUT /api/settings/api-keys - Clear DataForSEO keys", False, 
                              f"Request failed with status {status}")
                return False
                
        except Exception as e:
            self.log_result("PUT /api/settings/api-keys - Clear DataForSEO keys", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all DataForSEO integration tests"""
        print("=" * 80)
        print("BACKEND TESTING - DataForSEO Google Shopping Integration")
        print("=" * 80)
        
        test_methods = [
            self.test_auth_registration,
            self.test_get_api_keys_initial,
            self.test_save_dataforseo_credentials,
            self.test_toggle_google_search_mode_to_shopping,
            self.test_toggle_google_search_mode_to_search,
            self.test_verify_toggle_persistence,
            self.test_toggle_to_shopping_and_verify,
            self.test_clear_dataforseo_keys
        ]
        
        passed = 0
        total = len(test_methods)
        
        for test_method in test_methods:
            success = test_method()
            if success:
                passed += 1
            print()  # Add spacing between tests
            
        print("=" * 80)
        print(f"TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - DataForSEO integration working correctly!")
            return True
        else:
            print("❌ SOME TESTS FAILED - Check the details above")
            return False

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)