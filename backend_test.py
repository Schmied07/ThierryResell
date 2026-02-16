#!/usr/bin/env python3
"""
Backend Testing - Keepa Multi-Domain Search Fix
Testing the new multi-domain Keepa search functionality that searches across
FR(4)→DE(3)→IT(8)→ES(9)→UK(2)→US(1) instead of just Amazon.fr
"""

import requests
import json
import sys
import uuid

# Configuration
BASE_URL = "https://metal-box-finder.preview.emergentagent.com/api"
TEST_EMAIL = f"keepatest_{uuid.uuid4().hex[:8]}@test.com"
TEST_PASSWORD = "TestPassword123!"
TEST_NAME = "Keepa Test User"

# Global auth token
auth_token = None

def make_request(method, endpoint, data=None, files=None, headers=None, json_data=None):
    """Make HTTP request with optional authentication"""
    url = f"{BASE_URL}{endpoint}"
    
    # Prepare headers
    request_headers = headers or {}
    if auth_token:
        request_headers['Authorization'] = f"Bearer {auth_token}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=request_headers, timeout=30)
        elif method.upper() == 'POST':
            if files:
                response = requests.post(url, data=data, files=files, headers=request_headers, timeout=30)
            elif json_data:
                request_headers['Content-Type'] = 'application/json'
                response = requests.post(url, json=json_data, headers=request_headers, timeout=30)
            else:
                response = requests.post(url, data=data, headers=request_headers, timeout=30)
        elif method.upper() == 'PUT':
            if json_data:
                request_headers['Content-Type'] = 'application/json'
                response = requests.put(url, json=json_data, headers=request_headers, timeout=30)
            else:
                response = requests.put(url, data=data, headers=request_headers, timeout=30)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=request_headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed for {method} {endpoint}: {e}")
        return None

def test_health_check():
    """Test 1: Health check endpoint"""
    print("\n🔍 Test 1: Health Check")
    print("-" * 40)
    
    response = make_request('GET', '/health')
    
    if not response:
        print("❌ FAILED: No response from health endpoint")
        return False
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: Health check returned: {data}")
        return True
    else:
        print(f"❌ FAILED: Health check returned {response.status_code}: {response.text}")
        return False

def test_authentication():
    """Test 2: User registration and authentication"""
    print("\n🔍 Test 2: User Authentication")
    print("-" * 40)
    
    global auth_token
    
    # Register new user
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "name": TEST_NAME
    }
    
    response = make_request('POST', '/auth/register', json_data=register_data)
    
    if not response:
        print("❌ FAILED: No response from register endpoint")
        return False
    
    if response.status_code in [200, 201]:
        data = response.json()
        auth_token = data.get('token') or data.get('access_token')
        if auth_token:
            print(f"✅ SUCCESS: User registered successfully")
            print(f"   Email: {TEST_EMAIL}")
            print(f"   Token received: {auth_token[:20]}...")
            return True
        else:
            print("❌ FAILED: No access token in register response")
            return False
    elif response.status_code == 400 and "email already exists" in response.text.lower():
        # User already exists, try to login
        print("ℹ️  User already exists, attempting login...")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        login_response = make_request('POST', '/auth/login', json_data=login_data)
        
        if login_response and login_response.status_code == 200:
            data = login_response.json()
            auth_token = data.get('token') or data.get('access_token')
            if auth_token:
                print(f"✅ SUCCESS: User logged in successfully")
                return True
        
        print("❌ FAILED: Could not login existing user")
        return False
    else:
        print(f"❌ FAILED: Registration returned {response.status_code}: {response.text}")
        return False

def test_api_keys_setup():
    """Test 3: API Keys setup for testing"""
    print("\n🔍 Test 3: API Keys Setup")
    print("-" * 40)
    
    # First check current API keys status
    response = make_request('GET', '/settings/api-keys')
    
    if not response or response.status_code != 200:
        print("❌ FAILED: Could not fetch API keys status")
        return False
    
    data = response.json()
    print(f"✅ Current API keys status: {data}")
    
    # Set a test Keepa API key (will be used for mock testing)
    test_keys = {
        "keepa_api_key": "test_keepa_key_123_for_mock_testing"
    }
    
    response = make_request('PUT', '/settings/api-keys', json_data=test_keys)
    
    if response and response.status_code == 200:
        print("✅ SUCCESS: Test Keepa API key set for mock testing")
        return True
    else:
        print(f"❌ FAILED: Could not set API keys: {response.status_code if response else 'No response'}")
        return False

def test_compare_endpoint_structure():
    """Test 4: Compare endpoint structure - verify amazon_source_domain field"""
    print("\n🔍 Test 4: Compare Endpoint Structure")
    print("-" * 40)
    
    # First, let's create a test product by importing a simple catalog
    print("Creating test catalog product...")
    
    # Create minimal Excel content in memory
    test_data = """EAN,Name,Price
8718951388574,Test Product German,5.99
3014260033279,Test Product French,3.50"""
    
    # Create a simple CSV file content for testing
    files = {
        'file': ('test_catalog.csv', test_data, 'text/csv')
    }
    
    form_data = {
        'column_mapping': json.dumps({
            'GTIN': 'EAN',
            'Name': 'Name', 
            'Price': 'Price'
        })
    }
    
    # Import catalog
    import_response = make_request('POST', '/catalog/import', data=form_data, files=files)
    
    if not import_response or import_response.status_code != 200:
        print(f"❌ FAILED: Could not import test catalog: {import_response.status_code if import_response else 'No response'}")
        return False
    
    import_result = import_response.json()
    print(f"✅ Test catalog imported: {import_result.get('imported_count', 0)} products")
    
    # Get first product ID
    products_response = make_request('GET', '/catalog/products')
    if not products_response or products_response.status_code != 200:
        print("❌ FAILED: Could not fetch catalog products")
        return False
    
    products_data = products_response.json()
    if not products_data.get('products') or len(products_data['products']) == 0:
        print("❌ FAILED: No products found in catalog")
        return False
    
    test_product = products_data['products'][0]
    product_id = test_product['id']
    print(f"✅ Using test product: {test_product['name']} (ID: {product_id})")
    
    # Now test the compare endpoint
    compare_response = make_request('POST', f'/catalog/compare/{product_id}')
    
    if not compare_response:
        print("❌ FAILED: No response from compare endpoint")
        return False
    
    if compare_response.status_code == 200:
        compare_data = compare_response.json()
        
        # Check for amazon_source_domain field
        if 'amazon_source_domain' in compare_data:
            amazon_source = compare_data['amazon_source_domain']
            print(f"✅ SUCCESS: amazon_source_domain field present: {amazon_source}")
            
            # Verify the response structure
            required_fields = ['product_id', 'product_name', 'gtin', 'amazon_source_domain', 'supplier_price_eur', 'amazon_price_eur']
            missing_fields = [field for field in required_fields if field not in compare_data]
            
            if missing_fields:
                print(f"⚠️  WARNING: Missing fields in response: {missing_fields}")
            else:
                print("✅ All required fields present in compare response")
            
            # Check if it's mock data or real data
            is_mock = compare_data.get('is_mock_data', True)
            if is_mock:
                print(f"ℹ️  Using MOCK data (no real Keepa API key configured)")
                print(f"   Mock amazon_source_domain: {amazon_source}")
            else:
                print(f"ℹ️  Using REAL Keepa API data")
                print(f"   Real amazon_source_domain: {amazon_source}")
            
            return True
        else:
            print("❌ FAILED: amazon_source_domain field missing from response")
            print(f"   Available fields: {list(compare_data.keys())}")
            return False
    else:
        print(f"❌ FAILED: Compare endpoint returned {compare_response.status_code}: {compare_response.text}")
        return False

def test_text_search_endpoint():
    """Test 5: Text search endpoint with multi-domain support"""
    print("\n🔍 Test 5: Text Search Endpoint")
    print("-" * 40)
    
    test_queries = [
        "Gebäckdosen Kindermotiv",  # German product that should be found on Amazon.de
        "test product",             # Generic search
        "iPhone 15"                 # Common product
    ]
    
    for query in test_queries:
        print(f"\nTesting search query: '{query}'")
        
        search_data = {"query": query}
        response = make_request('POST', '/search/text', json_data=search_data)
        
        if not response:
            print(f"❌ FAILED: No response for query '{query}'")
            continue
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if keepa_data exists and has source_domain
            keepa_data = data.get('keepa_data', {})
            if keepa_data and 'source_domain' in keepa_data:
                source_domain = keepa_data['source_domain']
                print(f"✅ SUCCESS: Found source_domain: {source_domain}")
                
                mock_data = keepa_data.get('mock_data', True)
                if mock_data:
                    print(f"   (Using mock data - no real API key)")
                else:
                    print(f"   (Using real Keepa API data)")
            else:
                print(f"⚠️  WARNING: No keepa_data.source_domain in response for '{query}'")
            
            print(f"   Response structure: {list(data.keys())}")
        else:
            print(f"❌ FAILED: Text search returned {response.status_code}: {response.text}")

def test_multi_domain_mock_behavior():
    """Test 6: Verify multi-domain mock behavior works correctly"""
    print("\n🔍 Test 6: Multi-Domain Mock Behavior")
    print("-" * 40)
    
    # Test with different product GTINs to see if mock data simulates different domains
    test_gtins = [
        "8718951388574",  # Should simulate finding on a specific domain
        "3014260033279",  # Should simulate finding on another domain
        "1234567890123"   # Non-existent GTIN for testing
    ]
    
    # Get products from catalog
    products_response = make_request('GET', '/catalog/products')
    if not products_response or products_response.status_code != 200:
        print("❌ FAILED: Could not fetch catalog products")
        return False
    
    products_data = products_response.json()
    products = products_data.get('products', [])
    
    if not products:
        print("❌ FAILED: No products in catalog for testing")
        return False
    
    success_count = 0
    total_tests = len(products[:3])  # Test first 3 products
    
    for product in products[:3]:
        product_id = product['id']
        gtin = product['gtin']
        name = product['name']
        
        print(f"\nTesting product: {name} (GTIN: {gtin})")
        
        response = make_request('POST', f'/catalog/compare/{product_id}')
        
        if response and response.status_code == 200:
            data = response.json()
            amazon_source = data.get('amazon_source_domain', 'Not found')
            is_mock = data.get('is_mock_data', True)
            
            print(f"✅ amazon_source_domain: {amazon_source}")
            print(f"   Mock data: {is_mock}")
            print(f"   Amazon price: €{data.get('amazon_price_eur', 0)}")
            
            success_count += 1
        else:
            print(f"❌ FAILED: Compare failed for {name}")
    
    print(f"\n📊 Multi-domain mock test results: {success_count}/{total_tests} successful")
    return success_count == total_tests

def test_api_response_fields():
    """Test 7: Comprehensive API response field validation"""
    print("\n🔍 Test 7: API Response Fields Validation")
    print("-" * 40)
    
    # Get a product to compare
    products_response = make_request('GET', '/catalog/products')
    if not products_response or products_response.status_code != 200:
        print("❌ FAILED: Could not fetch products")
        return False
    
    products_data = products_response.json()
    products = products_data.get('products', [])
    
    if not products:
        print("❌ FAILED: No products available")
        return False
    
    test_product = products[0]
    product_id = test_product['id']
    
    # Compare the product
    response = make_request('POST', f'/catalog/compare/{product_id}')
    
    if not response or response.status_code != 200:
        print(f"❌ FAILED: Compare request failed")
        return False
    
    data = response.json()
    
    # Expected fields in the response
    expected_fields = {
        'product_id': str,
        'product_name': str,
        'gtin': str,
        'amazon_source_domain': str,  # NEW FIELD - this is what we're testing
        'supplier_price_eur': (int, float),
        'amazon_price_eur': (int, float),
        'is_mock_data': bool
    }
    
    print("Validating response fields:")
    
    all_valid = True
    for field, expected_type in expected_fields.items():
        if field in data:
            value = data[field]
            if isinstance(value, expected_type):
                print(f"✅ {field}: {value} (type: {type(value).__name__})")
            else:
                print(f"❌ {field}: {value} (expected type: {expected_type}, got: {type(value)})")
                all_valid = False
        else:
            print(f"❌ {field}: MISSING")
            all_valid = False
    
    # Special validation for amazon_source_domain
    amazon_source = data.get('amazon_source_domain')
    if amazon_source:
        expected_domains = ['Amazon.fr', 'Amazon.de', 'Amazon.it', 'Amazon.es', 'Amazon.co.uk', 'Amazon.com', 'Mock']
        if any(domain in amazon_source for domain in expected_domains):
            print(f"✅ amazon_source_domain contains valid domain: {amazon_source}")
        else:
            print(f"⚠️  amazon_source_domain has unexpected value: {amazon_source}")
    
    print(f"\n📊 Field validation: {'✅ ALL VALID' if all_valid else '❌ SOME ISSUES'}")
    return all_valid

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 KEEPA MULTI-DOMAIN SEARCH FIX TESTING")
    print("=" * 60)
    print(f"Backend URL: {BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")
    
    # Run all tests
    tests = [
        ("Health Check", test_health_check),
        ("Authentication", test_authentication),
        ("API Keys Setup", test_api_keys_setup),
        ("Compare Endpoint Structure", test_compare_endpoint_structure),
        ("Text Search Endpoint", test_text_search_endpoint),
        ("Multi-Domain Mock Behavior", test_multi_domain_mock_behavior),
        ("API Response Fields", test_api_response_fields)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Keepa multi-domain search fix is working correctly.")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)