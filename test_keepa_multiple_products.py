#!/usr/bin/env python3
"""
Script de test pour l'API Keepa - Test avec plusieurs produits
"""

import httpx
import asyncio
import json
from datetime import datetime

# Configuration
KEEPA_API_KEY = "ju7cgn79dp9ehsp8473lldrvsi8a0cdiglba9gu6fpl61quncl0h870q0o01qbaq"

# Produits à tester (du plus spécifique au plus général)
TEST_PRODUCTS = [
    "Sanex Dermo Invisible",
    "Sanex deodorant",
    "iPhone 15 Pro",
    "Nivea Creme",
    "Nutella 750g"
]

# Keepa domain IDs
KEEPA_DOMAINS = [
    {'domain': 4, 'name': 'Amazon.fr', 'flag': '🇫🇷', 'currency': 'EUR'},
    {'domain': 3, 'name': 'Amazon.de', 'flag': '🇩🇪', 'currency': 'EUR'},
    {'domain': 2, 'name': 'Amazon.co.uk', 'flag': '🇬🇧', 'currency': 'GBP'},
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


async def quick_search_product(client, search_term, domain_info):
    """Quick search for a product"""
    domain_id = domain_info['domain']
    
    try:
        # Search for ASINs
        search_response = await client.get(
            "https://api.keepa.com/search",
            params={
                "key": KEEPA_API_KEY,
                "domain": domain_id,
                "type": "product",
                "term": search_term
            },
            timeout=30
        )
        
        if search_response.status_code != 200:
            return None
        
        search_data = search_response.json()
        asin_list = search_data.get('asinList', [])
        
        if not asin_list or len(asin_list) == 0:
            return None
        
        # Get details for first ASIN
        first_asin = asin_list[0]
        
        detail_response = await client.get(
            "https://api.keepa.com/product",
            params={
                "key": KEEPA_API_KEY,
                "domain": domain_id,
                "asin": first_asin,
                "stats": 1,
            },
            timeout=30
        )
        
        if detail_response.status_code != 200:
            return None
        
        detail_data = detail_response.json()
        products = detail_data.get('products', [])
        
        if not products:
            return None
        
        product = products[0]
        title = product.get('title', 'N/A')
        asin = product.get('asin', 'N/A')
        price = extract_price_from_keepa(product)
        
        return {
            'search_term': search_term,
            'domain': domain_info['name'],
            'flag': domain_info['flag'],
            'asin': asin,
            'title': title,
            'price': price,
            'currency': domain_info['currency'],
            'total_asins_found': len(asin_list)
        }
        
    except Exception as e:
        return None


async def test_multiple_products():
    """Test multiple products"""
    print("="*80)
    print("  TEST KEEPA API - RECHERCHE MULTI-PRODUITS")
    print("="*80)
    print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 API Key configurée: ✅")
    print(f"🔍 Nombre de produits à tester: {len(TEST_PRODUCTS)}")
    print(f"🌍 Marketplaces testés: {len(KEEPA_DOMAINS)}")
    
    all_results = []
    
    async with httpx.AsyncClient() as client:
        for product_term in TEST_PRODUCTS:
            print(f"\n{'='*80}")
            print(f"🔍 Recherche: '{product_term}'")
            print(f"{'='*80}")
            
            product_found = False
            
            for domain_info in KEEPA_DOMAINS:
                print(f"   {domain_info['flag']} {domain_info['name']}...", end=" ")
                
                result = await quick_search_product(client, product_term, domain_info)
                
                if result:
                    product_found = True
                    all_results.append(result)
                    print(f"✅ Trouvé!")
                    print(f"      🆔 ASIN: {result['asin']}")
                    print(f"      🏷️  {result['title'][:60]}...")
                    if result['price']:
                        print(f"      💰 {result['price']:.2f} {result['currency']}")
                    print(f"      📊 {result['total_asins_found']} résultat(s) total")
                else:
                    print("❌ Non trouvé")
                
                await asyncio.sleep(1)  # Rate limiting
            
            if not product_found:
                print(f"\n   ⚠️  '{product_term}' introuvable sur tous les marketplaces testés")
    
    # Summary
    print("\n" + "="*80)
    print("  RÉSUMÉ GLOBAL")
    print("="*80)
    print(f"\n✅ Total de produits trouvés: {len(all_results)}")
    
    if all_results:
        # Group by search term
        by_product = {}
        for r in all_results:
            term = r['search_term']
            if term not in by_product:
                by_product[term] = []
            by_product[term].append(r)
        
        print(f"\n📊 Résultats par produit:")
        for term, results in by_product.items():
            print(f"\n   '{term}': {len(results)} marketplace(s)")
            for r in results:
                price_str = f"{r['price']:.2f} {r['currency']}" if r['price'] else "Prix indisponible"
                print(f"      {r['flag']} {r['domain']}: {price_str}")
    
    # Test API status
    print("\n" + "="*80)
    print("  VÉRIFICATION API KEEPA")
    print("="*80)
    
    async with httpx.AsyncClient() as client:
        try:
            # Test with a well-known ASIN (iPhone)
            test_response = await client.get(
                "https://api.keepa.com/product",
                params={
                    "key": KEEPA_API_KEY,
                    "domain": 4,
                    "asin": "B0CHX1W1XY",  # iPhone 15 Pro example ASIN
                },
                timeout=30
            )
            
            if test_response.status_code == 200:
                print("\n✅ Clé API Keepa: VALIDE")
                data = test_response.json()
                print(f"✅ Réponse API: OK")
                print(f"✅ Format de données: OK")
                
                # Check tokens remaining
                if 'tokensLeft' in data:
                    print(f"💰 Tokens restants: {data['tokensLeft']}")
                    
            elif test_response.status_code == 401:
                print("\n❌ Clé API Keepa: INVALIDE (401 Unauthorized)")
            elif test_response.status_code == 429:
                print("\n⚠️  Clé API Keepa: RATE LIMIT ATTEINT (429)")
            else:
                print(f"\n⚠️  Statut API: HTTP {test_response.status_code}")
                
        except Exception as e:
            print(f"\n❌ Erreur lors du test API: {e}")
    
    # Save results
    output_file = "/app/keepa_multiple_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'products_tested': TEST_PRODUCTS,
            'results': all_results,
            'total_found': len(all_results)
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés: {output_file}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_multiple_products())
