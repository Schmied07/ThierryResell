#!/usr/bin/env python3
"""
Script interactif Keepa - Test rapide de produits
Usage: python keepa_quick_test.py [ASIN ou EAN]
"""

import httpx
import asyncio
import sys

KEEPA_API_KEY = "ju7cgn79dp9ehsp8473lldrvsi8a0cdiglba9gu6fpl61quncl0h870q0o01qbaq"


def extract_price(product):
    """Extrait le prix actuel"""
    try:
        if 'csv' in product and product['csv'] and len(product['csv']) > 0:
            prices = [p/100.0 for p in product['csv'][0] if p and p > 0]
            return prices[-1] if prices else None
    except:
        pass
    return None


async def test_by_asin(asin, domain=4):
    """Test rapide par ASIN"""
    async with httpx.AsyncClient() as client:
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
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            products = data.get('products', [])
            
            return products[0] if products else None
        except:
            return None


async def test_by_ean(ean, domain=4):
    """Test rapide par EAN"""
    async with httpx.AsyncClient() as client:
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
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            products = data.get('products', [])
            
            return products[0] if products else None
        except:
            return None


async def main():
    """Main"""
    if len(sys.argv) < 2:
        print("Usage: python keepa_quick_test.py [ASIN ou EAN]")
        print("\nExemples:")
        print("  python keepa_quick_test.py B0CHBQX4Z9")
        print("  python keepa_quick_test.py 8710447348741")
        return
    
    identifier = sys.argv[1]
    
    print(f"\n🔍 Recherche Keepa: {identifier}")
    print("="*60)
    
    # Déterminer si c'est un ASIN ou EAN
    is_asin = len(identifier) == 10 and identifier[0] == 'B'
    
    if is_asin:
        print("📝 Type: ASIN")
        product = await test_by_asin(identifier)
    else:
        print("📝 Type: EAN/GTIN")
        product = await test_by_ean(identifier)
    
    if not product:
        print("❌ Produit non trouvé sur Amazon.fr")
        
        if not is_asin:
            print("\n🔄 Essai sur Amazon.de...")
            product = await test_by_ean(identifier, domain=3)
            if product:
                print("✅ Trouvé sur Amazon.de!")
            else:
                print("❌ Non trouvé sur Amazon.de non plus")
    
    if product:
        print("\n✅ PRODUIT TROUVÉ:")
        print(f"   ASIN: {product.get('asin', 'N/A')}")
        print(f"   Titre: {product.get('title') or 'Non disponible'}")
        print(f"   Marque: {product.get('brand') or 'Non disponible'}")
        
        ean_list = product.get('eanList', [])
        if ean_list:
            print(f"   EAN: {', '.join(ean_list)}")
        
        price = extract_price(product)
        if price:
            print(f"   Prix: {price:.2f} EUR")
        
        # Stats
        if 'csv' in product and product['csv'] and len(product['csv']) > 0:
            prices = [p/100.0 for p in product['csv'][0] if p and p > 0]
            if len(prices) > 1:
                print(f"\n📈 Historique:")
                print(f"   Min: {min(prices):.2f} EUR")
                print(f"   Max: {max(prices):.2f} EUR")
                print(f"   Moyenne: {sum(prices)/len(prices):.2f} EUR")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
