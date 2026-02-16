#!/usr/bin/env python3
"""
Test Keepa - Recherche Sanex sur TOUS les marketplaces européens
"""

import httpx
import asyncio
import json

KEEPA_API_KEY = "ju7cgn79dp9ehsp8473lldrvsi8a0cdiglba9gu6fpl61quncl0h870q0o01qbaq"
SANEX_EAN = "8710447348741"

# Tous les marketplaces Amazon européens
EUROPEAN_MARKETPLACES = [
    {'domain': 4, 'name': 'Amazon.fr', 'flag': '🇫🇷', 'country': 'France'},
    {'domain': 3, 'name': 'Amazon.de', 'flag': '🇩🇪', 'country': 'Allemagne'},
    {'domain': 2, 'name': 'Amazon.co.uk', 'flag': '🇬🇧', 'country': 'Royaume-Uni'},
    {'domain': 9, 'name': 'Amazon.es', 'flag': '🇪🇸', 'country': 'Espagne'},
    {'domain': 8, 'name': 'Amazon.it', 'flag': '🇮🇹', 'country': 'Italie'},
    {'domain': 11, 'name': 'Amazon.nl', 'flag': '🇳🇱', 'country': 'Pays-Bas'},
    {'domain': 30, 'name': 'Amazon.se', 'flag': '🇸🇪', 'country': 'Suède'},
    {'domain': 27, 'name': 'Amazon.pl', 'flag': '🇵🇱', 'country': 'Pologne'},
    {'domain': 35, 'name': 'Amazon.be', 'flag': '🇧🇪', 'country': 'Belgique'},
]


async def search_sanex_on_marketplace(client, marketplace):
    """Recherche Sanex sur un marketplace spécifique"""
    domain_id = marketplace['domain']
    domain_name = marketplace['name']
    flag = marketplace['flag']
    country = marketplace['country']
    
    print(f"\n{flag} {domain_name} ({country})...", end=" ")
    
    try:
        # Recherche par EAN
        response = await client.get(
            "https://api.keepa.com/product",
            params={
                "key": KEEPA_API_KEY,
                "domain": domain_id,
                "code": SANEX_EAN,
                "stats": 1,
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return None
        
        data = response.json()
        products = data.get('products', [])
        
        if not products or len(products) == 0:
            print(f"❌ Non trouvé")
            return None
        
        product = products[0]
        asin = product.get('asin', 'N/A')
        title = product.get('title') or 'Sans titre'
        
        # Extraire le prix
        price = None
        if 'csv' in product and product['csv'] and len(product['csv']) > 0:
            amazon_prices = product['csv'][0]
            if amazon_prices:
                valid_prices = [p/100.0 for p in amazon_prices if p and p > 0]
                if valid_prices:
                    price = valid_prices[-1]
        
        print(f"✅ TROUVÉ!")
        print(f"   ASIN: {asin}")
        print(f"   Titre: {title[:60]}...")
        if price:
            print(f"   Prix: {price:.2f}")
        
        return {
            'marketplace': domain_name,
            'country': country,
            'flag': flag,
            'domain_id': domain_id,
            'asin': asin,
            'title': title,
            'price': price,
            'ean': SANEX_EAN
        }
        
    except httpx.TimeoutException:
        print(f"⏱️  Timeout")
        return None
    except Exception as e:
        print(f"❌ Erreur: {str(e)[:30]}")
        return None


async def main():
    """Recherche Sanex sur tous les marketplaces"""
    print("="*100)
    print("  RECHERCHE SANEX DERMO INVISIBLE SUR TOUS LES MARKETPLACES AMAZON EUROPÉENS")
    print("="*100)
    print(f"\n📦 Produit: Sanex Deodorant Roller Dermo Invisible Personal Care")
    print(f"📊 EAN: {SANEX_EAN}")
    print(f"🌍 Marketplaces testés: {len(EUROPEAN_MARKETPLACES)}")
    print(f"\n{'='*100}")
    print("RECHERCHE EN COURS...")
    print("="*100)
    
    results = []
    
    async with httpx.AsyncClient() as client:
        for marketplace in EUROPEAN_MARKETPLACES:
            result = await search_sanex_on_marketplace(client, marketplace)
            if result:
                results.append(result)
            await asyncio.sleep(2)  # Rate limiting
    
    # Résumé
    print(f"\n\n{'='*100}")
    print("  RÉSUMÉ DE LA RECHERCHE")
    print("="*100)
    
    if not results:
        print(f"\n❌ Produit Sanex Dermo Invisible NON TROUVÉ sur aucun marketplace Amazon européen")
        print(f"\n💡 Possibilités:")
        print(f"   • Le produit n'est pas vendu sur Amazon en Europe")
        print(f"   • L'EAN est incorrect ou a changé")
        print(f"   • Le produit a été retiré du catalogue Amazon")
        print(f"   • Il est disponible uniquement via des vendeurs tiers (non tracké par Keepa)")
    else:
        print(f"\n✅ Produit trouvé sur {len(results)} marketplace(s):\n")
        
        for r in results:
            print(f"{r['flag']} {r['marketplace']} ({r['country']})")
            print(f"   ASIN: {r['asin']}")
            print(f"   Titre: {r['title']}")
            if r['price']:
                print(f"   Prix: {r['price']:.2f}")
            print()
        
        # Comparaison des prix
        if len(results) > 1:
            prices = [(r['marketplace'], r['price']) for r in results if r['price']]
            if prices:
                print(f"💰 COMPARAISON DES PRIX:")
                for marketplace, price in sorted(prices, key=lambda x: x[1]):
                    print(f"   {marketplace}: {price:.2f}")
                
                cheapest = min(prices, key=lambda x: x[1])
                most_expensive = max(prices, key=lambda x: x[1])
                diff = most_expensive[1] - cheapest[1]
                
                print(f"\n   🏆 Moins cher: {cheapest[0]} à {cheapest[1]:.2f}")
                print(f"   📈 Plus cher: {most_expensive[0]} à {most_expensive[1]:.2f}")
                print(f"   💡 Différence: {diff:.2f} ({(diff/most_expensive[1]*100):.1f}%)")
    
    # Sauvegarder les résultats
    output = "/app/keepa_sanex_european_search.json"
    with open(output, 'w', encoding='utf-8') as f:
        json.dump({
            'product': 'Sanex Deodorant Roller Dermo Invisible Personal Care',
            'ean': SANEX_EAN,
            'marketplaces_tested': len(EUROPEAN_MARKETPLACES),
            'marketplaces_found': len(results),
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés: {output}")
    print("\n" + "="*100 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
