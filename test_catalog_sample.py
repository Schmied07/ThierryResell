#!/usr/bin/env python3
"""
Additional test for catalog_sample.xlsx file as specified in review request
"""

import requests
import json

BACKEND_URL = "https://search-price-fix.preview.emergentagent.com/api"
TEST_EMAIL = "flextest@test.com"  
TEST_PASSWORD = "test123"

def get_auth_token():
    """Login and get auth token"""
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get("token")
    return None

def test_catalog_sample_preview():
    """Test catalog sample file preview as per review request"""
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with catalog_sample.xlsx
    sample_file_path = "/app/catalog_sample.xlsx"
    try:
        with open(sample_file_path, "rb") as f:
            files = {"file": (sample_file_path.split("/")[-1], f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            
            response = requests.post(
                f"{BACKEND_URL}/catalog/preview",
                files=files,
                headers=headers
            )
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = data.get("required_fields", [])
            optional_fields = data.get("optional_fields", [])
            columns = data.get("columns", [])
            
            print(f"✅ Catalog sample preview successful")
            print(f"   Columns found: {len(columns)}")
            print(f"   Required fields: {required_fields}")
            print(f"   Optional fields: {optional_fields}")
            
            # Verify required fields are ONLY GTIN and Price
            if required_fields == ['GTIN', 'Price']:
                print("✅ CRITICAL: Required fields correct - only GTIN and Price")
                return True
            else:
                print(f"❌ CRITICAL: Required fields incorrect! Expected ['GTIN', 'Price'], got {required_fields}")
                return False
        else:
            print(f"❌ Preview failed: {response.status_code} - {response.text}")
            return False
            
    except FileNotFoundError:
        print(f"❌ File not found: {sample_file_path}")
        return False
    except Exception as e:
        print(f"❌ Error testing catalog sample: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing catalog_sample.xlsx as per review request")
    print("=" * 50)
    
    result = test_catalog_sample_preview()
    
    if result:
        print("\n🎉 catalog_sample.xlsx test PASSED")
        print("✅ Confirms required_fields=['GTIN', 'Price'] (NOT 5 fields)")
    else:
        print("\n❌ catalog_sample.xlsx test FAILED")