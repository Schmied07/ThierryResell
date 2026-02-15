import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def check():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    # Find Elmex products
    products = await db.catalog_products.find(
        {'name': {'$regex': 'Elmex.*Junior', '$options': 'i'}},
        {'name': 1, 'gtin': 1, 'brand': 1, 'supplier_price_eur': 1, 'amazon_price_eur': 1, '_id': 0}
    ).to_list(5)
    print("=== Elmex Junior products ===")
    for p in products:
        print(p)
    
    # Check total products
    total = await db.catalog_products.count_documents({})
    print(f'\nTotal products in catalog: {total}')
    
    # Check users with keepa key
    users = await db.users.find({}, {'email': 1, 'api_keys': 1, '_id': 0}).to_list(10)
    print("\n=== Users ===")
    for u in users:
        keys = u.get('api_keys', {})
        keepa = keys.get('keepa_api_key', '')
        google = keys.get('google_api_key', '')
        print(f"User: {u.get('email')} - Keepa: {'SET (' + keepa[:10] + '...)' if keepa else 'NOT SET'} - Google: {'SET' if google else 'NOT SET'}")

asyncio.run(check())
