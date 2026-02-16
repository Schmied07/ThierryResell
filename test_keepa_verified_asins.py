#!/usr/bin/env python3
"""
Test Keepa avec ASINs validés Amazon.fr
"""

import httpx
import asyncio
import json

KEEPA_API_KEY = "ju7cgn79dp9ehsp8473lldrvsi8a0cdiglba9gu6fpl61quncl0h870q0o01qbaq"

# ASINs Amazon.fr validés
TEST_ASINS = [
    {'asin': 'B0CHBQX4Z9', 'name': 'Apple iPhone 15 (128 Go) - Noir'},
    {'asin': 'B0BSHF7WHW', 'name': 'Samsung Galaxy S23'},
    {'asin': 'B09G9FPHY6', 'name': 'Apple AirPods'},
]


async def test_asin_detailed(client, asin, name):
    """Test détaillé d'un ASIN"""
    print(f"\n{'='*80}")
    print(f"🔍 Test: {name}")
    print(f"🆔 ASIN: {asin}")
    print(f"{'='*80}")
    
    try:
        response = await client.get(
            "https://api.keepa.com/product",
            params={
                "key": KEEPA_API_KEY,
                "domain": 4,  # Amazon.fr
                "asin": asin,
                "stats": 1,
            },
            timeout=30
        )
        
        print(f"📡 HTTP: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.text}")
            return None
        
        data = response.json()
        products = data.get('products', [])
        
        if 'tokensLeft' in data:
            print(f"💰 Tokens: {data['tokensLeft']}")
        
        if not products:
            print(f"❌ Aucun produit")
            return None
        
        product = products[0]
        
        # Extraction sécurisée
        title = product.get('title', 'N/A')
        brand = product.get('brand', 'N/A')
        asin_ret = product.get('asin', 'N/A')
        
        print(f"\n✅ PRODUIT TROUVÉ:")
        print(f"   🏷️  {title}")
        print(f"   🏢 {brand}")
        print(f"   🆔 {asin_ret}")
        
        # Prix
        price = None
        if 'stats' in product and product.get('stats'):
            stats = product['stats']
            current = stats.get('current')
            if current and len(current) > 0:
                amazon_price = current[0]
                if amazon_price and amazon_price > 0:
                    price = amazon_price / 100.0
                    print(f"   💰 Prix: {price:.2f} EUR")
        
        # CSV price history
        if 'csv' in product and product.get('csv'):
            csv_data = product['csv']
            if len(csv_data) > 0 and csv_data[0]:
                prices = [p/100.0 for p in csv_data[0] if p and p > 0]
                if prices:
                    print(f"\n📈 Historique ({len(prices)} points):")
                    print(f"   Min: {min(prices):.2f} | Max: {max(prices):.2f} | Moy: {sum(prices)/len(prices):.2f} EUR")
        
        # EAN
        ean_list = product.get('eanList', [])
        if ean_list:
            print(f"   📊 EAN: {', '.join(ean_list[:2])}")
        
        # Image
        images = product.get('imagesCSV', '')
        if images:
            img_url = images.split(',')[0]
            print(f"   🖼️  Image disponible")
        
        # Sales rank
        if 'stats' in product and product.get('stats'):
            stats = product['stats']
            if 'current' in stats and len(stats['current']) > 3:
                sales_rank = stats['current'][3]
                if sales_rank and sales_rank > 0:
                    print(f"   📊 Classement: #{sales_rank}")
        
        # Affichage des clés disponibles
        print(f"\n🔑 Clés Keepa disponibles:")
        for key in sorted(product.keys()):
            val = product[key]
            if isinstance(val, (list, dict)):
                print(f"   • {key}: {type(val).__name__}({len(val)})")
            elif val:
                val_str = str(val)[:40]
                print(f"   • {key}: {val_str}...")
        
        return {
            'asin': asin_ret,
            'title': title,
            'brand': brand,
            'price': price
        }
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test"""
    print("="*80)
    print("  TEST KEEPA - ASINs Amazon.fr Validés")
    print("="*80)
    
    results = []
    
    async with httpx.AsyncClient() as client:
        for test in TEST_ASINS:
            result = await test_asin_detailed(client, test['asin'], test['name'])
            if result:
                results.append(result)
            await asyncio.sleep(2)
    
    print(f"\n{'='*80}")
    print(f"  RÉSUMÉ: {len(results)}/{len(TEST_ASINS)} réussis")
    print(f"{'='*80}\n")
    
    if results:
        for r in results:
            price_str = f"{r['price']:.2f} EUR" if r['price'] else "N/A"
            print(f"✅ {r['asin']}: {r['title'][:50]}... | {price_str}")


if __name__ == "__main__":
    asyncio.run(main())
