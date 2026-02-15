import asyncio
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json

async def test_keepa():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    # Get the user with keepa key
    user = await db.users.find_one({'email': 'talomthibaut@gmail.com'}, {'_id': 0})
    keepa_key = user['api_keys']['keepa_api_key']
    
    # Test with Elmex Junior Toothpaste GTIN
    gtin = '8718951652248'
    print(f"Testing Keepa /product endpoint with code={gtin}")
    print(f"Keepa key: {keepa_key[:10]}...")
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            "https://api.keepa.com/product",
            params={
                "key": keepa_key,
                "domain": 4,  # Amazon.fr
                "code": gtin,
                "stats": 1,
            },
            timeout=30
        )
        print(f"\nHTTP Status: {response.status_code}")
        data = response.json()
        
        # Check tokens remaining
        print(f"Tokens left: {data.get('tokensLeft', 'N/A')}")
        print(f"Tokens consumed: {data.get('tokensConsumed', 'N/A')}")
        
        products = data.get('products', [])
        print(f"Products found: {len(products)}")
        
        if products:
            p = products[0]
            print(f"\n=== Product Details ===")
            print(f"ASIN: {p.get('asin', 'N/A')}")
            print(f"Title: {p.get('title', 'N/A')}")
            print(f"Brand: {p.get('brand', 'N/A')}")
            
            stats = p.get('stats', {})
            current = stats.get('current', [])
            print(f"\nStats.current (first 5): {current[:5] if current else 'EMPTY'}")
            
            # Check csv data
            csv_data = p.get('csv', [])
            print(f"CSV arrays count: {len(csv_data) if csv_data else 0}")
            
            # Try to get price from different sources
            amazon_price = None
            
            # Method 1: stats.current
            if current and len(current) > 0:
                print(f"\nCurrent[0] (Amazon): {current[0]}")
                if len(current) > 1:
                    print(f"Current[1] (3rd party): {current[1]}")
                if current[0] is not None and current[0] > 0:
                    amazon_price = current[0] / 100.0
                    print(f"  → Amazon price: €{amazon_price}")
                elif len(current) > 1 and current[1] is not None and current[1] > 0:
                    amazon_price = current[1] / 100.0
                    print(f"  → 3rd party price: €{amazon_price}")
            
            # Method 2: csv
            if amazon_price is None and csv_data:
                for idx in [0, 1]:
                    if len(csv_data) > idx and csv_data[idx]:
                        arr = csv_data[idx]
                        # Get last valid price
                        for i in range(len(arr) - 1, 0, -2):
                            if arr[i] is not None and arr[i] > 0:
                                amazon_price = arr[i] / 100.0
                                print(f"\n  → CSV[{idx}] last price: €{amazon_price}")
                                break
                    if amazon_price:
                        break
            
            # Method 3: buyBoxPrice
            if amazon_price is None:
                buy_box = stats.get('buyBoxPrice', -1)
                if buy_box and buy_box > 0:
                    amazon_price = buy_box / 100.0
                    print(f"\n  → BuyBox price: €{amazon_price}")
            
            print(f"\n=== FINAL PRICE: €{amazon_price} ===")
        else:
            print("\nNo products found!")
            print(f"Full response keys: {list(data.keys())}")

asyncio.run(test_keepa())
