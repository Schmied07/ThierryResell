#!/usr/bin/env python3
"""
Script de test pour l'API Keepa - Recherche de produits Amazon
Teste la recherche multi-domaine avec le produit Sanex
"""

import httpx
import asyncio
import json
from datetime import datetime

# Configuration
KEEPA_API_KEY = "ju7cgn79dp9ehsp8473lldrvsi8a0cdiglba9gu6fpl61quncl0h870q0o01qbaq"
PRODUCT_SEARCH_TERM = "Sanex Deodorant Roller Dermo Invisible Personal Care"

# Keepa domain IDs: 1=US, 2=UK, 3=DE, 4=FR, 5=JP, 6=CA, 7=CN, 8=IT, 9=ES, 10=IN, 11=MX
KEEPA_DOMAINS = [
    {'domain': 4, 'name': 'Amazon.fr', 'flag': '🇫🇷', 'currency': 'EUR'},
    {'domain': 3, 'name': 'Amazon.de', 'flag': '🇩🇪', 'currency': 'EUR'},
    {'domain': 2, 'name': 'Amazon.co.uk', 'flag': '🇬🇧', 'currency': 'GBP'},
    {'domain': 9, 'name': 'Amazon.es', 'flag': '🇪🇸', 'currency': 'EUR'},
    {'domain': 8, 'name': 'Amazon.it', 'flag': '🇮🇹', 'currency': 'EUR'},
    {'domain': 1, 'name': 'Amazon.com', 'flag': '🇺🇸', 'currency': 'USD'},
]


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)


def print_section(text):
    """Print formatted section"""
    print("\n" + "-"*80)
    print(f"  {text}")
    print("-"*80)


def extract_price_from_keepa(product_data):
    """Extract current price from Keepa product data"""
    try:
        # Method 1: stats.current
        if 'stats' in product_data and product_data['stats']:
            current_prices = product_data['stats'].get('current', [])
            if current_prices and len(current_prices) > 0:
                # Index 0 is Amazon price
                amazon_price = current_prices[0]
                if amazon_price is not None and amazon_price != -1 and amazon_price > 0:
                    return amazon_price / 100.0  # Keepa prices are in cents
        
        # Method 2: csv price history
        if 'csv' in product_data and product_data['csv']:
            csv_data = product_data['csv']
            # Index 0 is Amazon price history
            if len(csv_data) > 0 and csv_data[0]:
                price_history = csv_data[0]
                if len(price_history) >= 2:
                    # Last value in the array
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
        print(f"   ⚠️  Error extracting price: {e}")
        return None


async def search_keepa_by_keyword(client, search_term, domain_info):
    """Search Keepa by keyword on a specific domain"""
    domain_id = domain_info['domain']
    domain_name = domain_info['name']
    
    print(f"\n🔍 Recherche sur {domain_info['flag']} {domain_name} (domain={domain_id})...")
    print(f"   Terme de recherche: '{search_term}'")
    
    try:
        # Step 1: Search for ASINs
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
            print(f"   ❌ Erreur HTTP {search_response.status_code}")
            print(f"   Réponse: {search_response.text[:200]}")
            return None
        
        search_data = search_response.json()
        asin_list = search_data.get('asinList', [])
        
        if not asin_list or len(asin_list) == 0:
            print(f"   ❌ Aucun produit trouvé")
            return None
        
        print(f"   ✅ {len(asin_list)} ASIN(s) trouvé(s): {asin_list[:5]}")
        
        # Step 2: Get details for the first ASIN
        first_asin = asin_list[0]
        print(f"\n   📦 Récupération des détails pour ASIN: {first_asin}")
        
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
            print(f"   ❌ Erreur lors de la récupération des détails: HTTP {detail_response.status_code}")
            return None
        
        detail_data = detail_response.json()
        products = detail_data.get('products', [])
        
        if not products or len(products) == 0:
            print(f"   ❌ Aucun détail produit disponible")
            return None
        
        product = products[0]
        
        # Extract information
        title = product.get('title', 'N/A')
        asin = product.get('asin', 'N/A')
        price = extract_price_from_keepa(product)
        brand = product.get('brand', 'N/A')
        manufacturer = product.get('manufacturer', 'N/A')
        ean_list = product.get('eanList', [])
        image_url = product.get('imagesCSV', '').split(',')[0] if product.get('imagesCSV') else None
        
        # Print results
        print(f"\n   ✅ PRODUIT TROUVÉ:")
        print(f"      🏷️  Titre: {title[:80]}...")
        print(f"      🆔 ASIN: {asin}")
        print(f"      💰 Prix actuel: {price} {domain_info['currency']}" if price else "      💰 Prix: Non disponible")
        print(f"      🏢 Marque: {brand}")
        print(f"      🏭 Fabricant: {manufacturer}")
        print(f"      📊 EAN: {ean_list[0] if ean_list else 'N/A'}")
        
        # Check availability
        stats = product.get('stats', {})
        if stats:
            print(f"      📈 Stats disponibles: {', '.join(stats.keys())}")
        
        return {
            'domain': domain_name,
            'domain_id': domain_id,
            'flag': domain_info['flag'],
            'currency': domain_info['currency'],
            'asin': asin,
            'title': title,
            'price': price,
            'brand': brand,
            'manufacturer': manufacturer,
            'ean': ean_list[0] if ean_list else None,
            'image_url': image_url,
            'raw_data': product
        }
        
    except httpx.TimeoutException:
        print(f"   ⏱️  Timeout lors de la recherche sur {domain_name}")
        return None
    except Exception as e:
        print(f"   ❌ Erreur: {type(e).__name__}: {str(e)}")
        return None


async def test_keepa_search():
    """Test Keepa search across multiple domains"""
    print_header("TEST KEEPA API - RECHERCHE DE PRODUITS AMAZON")
    print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 API Key: {KEEPA_API_KEY[:20]}...{KEEPA_API_KEY[-10:]}")
    print(f"🔍 Produit recherché: {PRODUCT_SEARCH_TERM}")
    
    results = []
    
    async with httpx.AsyncClient() as client:
        # Test sur tous les domaines
        for domain_info in KEEPA_DOMAINS:
            result = await search_keepa_by_keyword(client, PRODUCT_SEARCH_TERM, domain_info)
            if result:
                results.append(result)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
    
    # Summary
    print_header("RÉSUMÉ DES RÉSULTATS")
    
    if not results:
        print("\n❌ Aucun produit trouvé sur aucun marketplace Amazon")
        return
    
    print(f"\n✅ Produit trouvé sur {len(results)} marketplace(s):\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['flag']} {result['domain']} - ASIN: {result['asin']}")
        if result['price']:
            print(f"   💰 Prix: {result['price']:.2f} {result['currency']}")
        else:
            print(f"   💰 Prix: Non disponible")
        print(f"   🏷️  {result['title'][:70]}...")
        print()
    
    # Prix comparison
    if len(results) > 1:
        print_section("COMPARAISON DES PRIX")
        available_prices = [(r['domain'], r['price'], r['currency']) for r in results if r['price']]
        
        if available_prices:
            print("\nPrix par marketplace:")
            for domain, price, currency in available_prices:
                print(f"   {domain}: {price:.2f} {currency}")
            
            # Find best price (simplified, assumes EUR for most)
            euro_prices = [(d, p) for d, p, c in available_prices if c == 'EUR']
            if euro_prices:
                best = min(euro_prices, key=lambda x: x[1])
                worst = max(euro_prices, key=lambda x: x[1])
                print(f"\n   🏆 Meilleur prix: {best[0]} - {best[1]:.2f} EUR")
                print(f"   📈 Prix le plus élevé: {worst[0]} - {worst[1]:.2f} EUR")
                if best[1] < worst[1]:
                    diff = worst[1] - best[1]
                    percent = (diff / worst[1]) * 100
                    print(f"   💡 Économie potentielle: {diff:.2f} EUR ({percent:.1f}%)")
    
    # Save results to file
    output_file = "/app/keepa_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'search_term': PRODUCT_SEARCH_TERM,
            'results': [{k: v for k, v in r.items() if k != 'raw_data'} for r in results],
            'total_found': len(results)
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés dans: {output_file}")
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(test_keepa_search())
