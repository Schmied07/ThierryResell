#!/usr/bin/env python3
"""
Script de test Keepa - Recherche par EAN/GTIN et ASIN
"""

import httpx
import asyncio
import json
from datetime import datetime

KEEPA_API_KEY = "ju7cgn79dp9ehsp8473lldrvsi8a0cdiglba9gu6fpl61quncl0h870q0o01qbaq"

# Tests avec différents types d'identifiants
TEST_CASES = [
    {
        'name': 'Sanex Dermo Invisible (EAN trouvé sur Amazon.fr)',
        'ean': '8710447348741',  # EAN Sanex Dermo Invisible
        'domain': 4,
        'domain_name': 'Amazon.fr'
    },
    {
        'name': 'Nutella 750g (EAN)',
        'ean': '8000500217566',  # EAN Nutella 750g
        'domain': 4,
        'domain_name': 'Amazon.fr'
    },
    {
        'name': 'Nivea Creme (EAN)',
        'ean': '4005808891771',  # EAN Nivea Creme
        'domain': 4,
        'domain_name': 'Amazon.fr'
    },
    {
        'name': 'iPhone 15 Pro (ASIN Amazon.fr)',
        'asin': 'B0CHX1W1XY',
        'domain': 4,
        'domain_name': 'Amazon.fr'
    },
]


def extract_price_from_keepa(product_data):
    """Extract current price from Keepa product data"""
    try:
        # Method 1: stats.current
        if 'stats' in product_data and product_data['stats']:
            current_prices = product_data['stats'].get('current', [])
            if current_prices and len(current_prices) > 0:
                amazon_price = current_prices[0]
                if amazon_price is not None and amazon_price != -1 and amazon_price > 0:
                    return amazon_price / 100.0
        
        # Method 2: csv price history
        if 'csv' in product_data and product_data['csv']:
            csv_data = product_data['csv']
            if len(csv_data) > 0 and csv_data[0]:
                price_history = csv_data[0]
                if len(price_history) >= 2:
                    last_price = price_history[-1]
                    if last_price is not None and last_price != -1 and last_price > 0:
                        return last_price / 100.0
        
        # Method 3: buyBoxPrice
        if 'buyBoxPrice' in product_data:
            buybox = product_data['buyBoxPrice']
            if buybox is not None and buybox != -1 and buybox > 0:
                return buybox / 100.0
        
        return None
    except Exception as e:
        return None


def get_price_history_stats(product_data):
    """Extract price history statistics"""
    try:
        if 'csv' in product_data and product_data['csv']:
            csv_data = product_data['csv']
            if len(csv_data) > 0 and csv_data[0]:
                price_history = csv_data[0]
                # Filter valid prices
                valid_prices = [p/100.0 for p in price_history if p is not None and p != -1 and p > 0]
                
                if valid_prices:
                    return {
                        'min': min(valid_prices),
                        'max': max(valid_prices),
                        'avg': sum(valid_prices) / len(valid_prices),
                        'count': len(valid_prices)
                    }
        return None
    except:
        return None


async def test_by_ean(client, ean, domain, domain_name):
    """Test Keepa product lookup by EAN/GTIN"""
    print(f"\n{'='*80}")
    print(f"🔍 Recherche par EAN: {ean}")
    print(f"🌍 Marketplace: {domain_name} (domain={domain})")
    print(f"{'='*80}")
    
    try:
        response = await client.get(
            "https://api.keepa.com/product",
            params={
                "key": KEEPA_API_KEY,
                "domain": domain,
                "code": ean,
                "stats": 1,
            },
            timeout=30
        )
        
        print(f"📡 Statut HTTP: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.text[:200]}")
            return None
        
        data = response.json()
        print(f"✅ Réponse reçue")
        
        # Check tokens
        if 'tokensLeft' in data:
            print(f"💰 Tokens restants: {data['tokensLeft']}")
        
        products = data.get('products', [])
        
        if not products or len(products) == 0:
            print(f"❌ Aucun produit trouvé pour cet EAN")
            return None
        
        product = products[0]
        
        # Extract information
        asin = product.get('asin', 'N/A')
        title = product.get('title', 'N/A')
        brand = product.get('brand', 'N/A')
        manufacturer = product.get('manufacturer', 'N/A')
        ean_list = product.get('eanList', [])
        category = product.get('categoryTree', [])
        
        price = extract_price_from_keepa(product)
        price_stats = get_price_history_stats(product)
        
        # Display results
        print(f"\n✅ PRODUIT TROUVÉ!")
        print(f"\n📦 Informations produit:")
        print(f"   🆔 ASIN: {asin}")
        print(f"   🏷️  Titre: {title[:80]}")
        if len(title) > 80:
            print(f"           {title[80:][:80]}")
        print(f"   🏢 Marque: {brand}")
        print(f"   🏭 Fabricant: {manufacturer}")
        print(f"   📊 EAN: {', '.join(ean_list[:3]) if ean_list else 'N/A'}")
        if category:
            print(f"   📁 Catégorie: {' > '.join([c.get('name', '') for c in category[:3]])}")
        
        print(f"\n💰 Prix:")
        if price:
            print(f"   💵 Prix actuel: {price:.2f} EUR")
        else:
            print(f"   ⚠️  Prix actuel: Non disponible")
        
        if price_stats:
            print(f"\n📈 Historique des prix:")
            print(f"   📉 Min: {price_stats['min']:.2f} EUR")
            print(f"   📈 Max: {price_stats['max']:.2f} EUR")
            print(f"   📊 Moyenne: {price_stats['avg']:.2f} EUR")
            print(f"   🔢 Points de données: {price_stats['count']}")
        
        # Additional stats
        if 'stats' in product and product['stats']:
            stats = product['stats']
            print(f"\n📊 Statistiques Keepa disponibles:")
            for key, value in stats.items():
                if isinstance(value, (list, dict)):
                    print(f"   • {key}: {type(value).__name__} avec {len(value)} élément(s)")
                else:
                    print(f"   • {key}: {value}")
        
        return {
            'asin': asin,
            'title': title,
            'brand': brand,
            'price': price,
            'ean': ean,
            'domain': domain_name,
            'price_stats': price_stats
        }
        
    except httpx.TimeoutException:
        print(f"⏱️  Timeout")
        return None
    except Exception as e:
        print(f"❌ Erreur: {type(e).__name__}: {str(e)}")
        return None


async def test_by_asin(client, asin, domain, domain_name):
    """Test Keepa product lookup by ASIN"""
    print(f"\n{'='*80}")
    print(f"🔍 Recherche par ASIN: {asin}")
    print(f"🌍 Marketplace: {domain_name} (domain={domain})")
    print(f"{'='*80}")
    
    try:
        response = await client.get(
            "https://api.keepa.com/product",
            params={
                "key": KEEPA_API_KEY,
                "domain": domain,
                "asin": asin,
                "stats": 1,
            },
            timeout=30
        )
        
        print(f"📡 Statut HTTP: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.text[:200]}")
            return None
        
        data = response.json()
        print(f"✅ Réponse reçue")
        
        if 'tokensLeft' in data:
            print(f"💰 Tokens restants: {data['tokensLeft']}")
        
        products = data.get('products', [])
        
        if not products:
            print(f"❌ Aucun produit trouvé")
            return None
        
        product = products[0]
        
        # Extract information
        title = product.get('title', 'N/A')
        brand = product.get('brand', 'N/A')
        price = extract_price_from_keepa(product)
        price_stats = get_price_history_stats(product)
        
        print(f"\n✅ PRODUIT TROUVÉ!")
        print(f"\n📦 Informations:")
        print(f"   🏷️  {title[:80]}")
        print(f"   🏢 Marque: {brand}")
        
        if price:
            print(f"   💵 Prix actuel: {price:.2f} EUR")
        
        if price_stats:
            print(f"\n📈 Historique:")
            print(f"   Min: {price_stats['min']:.2f} | Max: {price_stats['max']:.2f} | Moy: {price_stats['avg']:.2f} EUR")
        
        return {
            'asin': asin,
            'title': title,
            'brand': brand,
            'price': price,
            'domain': domain_name,
            'price_stats': price_stats
        }
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return None


async def run_tests():
    """Run all tests"""
    print("="*80)
    print("  TEST KEEPA API - RECHERCHE PAR EAN/ASIN")
    print("="*80)
    print(f"\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🧪 Nombre de tests: {len(TEST_CASES)}")
    
    results = []
    
    async with httpx.AsyncClient() as client:
        for test_case in TEST_CASES:
            if 'ean' in test_case:
                result = await test_by_ean(
                    client, 
                    test_case['ean'], 
                    test_case['domain'],
                    test_case['domain_name']
                )
            elif 'asin' in test_case:
                result = await test_by_asin(
                    client,
                    test_case['asin'],
                    test_case['domain'],
                    test_case['domain_name']
                )
            else:
                result = None
            
            if result:
                result['test_name'] = test_case['name']
                results.append(result)
            
            await asyncio.sleep(2)  # Rate limiting
    
    # Summary
    print(f"\n{'='*80}")
    print("  RÉSUMÉ DES TESTS")
    print(f"{'='*80}")
    print(f"\n✅ Tests réussis: {len(results)}/{len(TEST_CASES)}")
    
    if results:
        print(f"\n📊 Produits trouvés:\n")
        for i, r in enumerate(results, 1):
            price_str = f"{r['price']:.2f} EUR" if r['price'] else "Prix indisponible"
            print(f"{i}. {r['test_name']}")
            print(f"   ASIN: {r['asin']} | {price_str}")
    
    # Save
    output = "/app/keepa_ean_asin_test_results.json"
    with open(output, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'tests': TEST_CASES,
            'results': results,
            'success_count': len(results),
            'total_tests': len(TEST_CASES)
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats: {output}\n")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
