#!/usr/bin/env python3
"""
Test Keepa FINAL - Extraction complète des données disponibles
"""

import httpx
import asyncio
import json

KEEPA_API_KEY = "ju7cgn79dp9ehsp8473lldrvsi8a0cdiglba9gu6fpl61quncl0h870q0o01qbaq"


def extract_all_prices(product):
    """Extraire tous les prix disponibles"""
    prices_info = {}
    
    # CSV price arrays (index meanings from Keepa documentation)
    csv_indices = {
        0: 'Amazon',
        1: 'Nouveau',
        2: 'Occasion',
        3: 'Sales Rank',
        4: 'Liste de prix',
        5: 'Collectible New',
        6: 'Refurbished',
        7: 'New FBM',
        8: 'Lightning Deal',
        9: 'Warehouse',
        10: 'New FBA',
        18: 'Buy Box'
    }
    
    if 'csv' in product and product['csv']:
        csv_data = product['csv']
        for idx, price_array in enumerate(csv_data):
            if price_array and len(price_array) > 0:
                # Get last valid price
                valid_prices = [p/100.0 for p in price_array if p and p > 0]
                if valid_prices:
                    price_type = csv_indices.get(idx, f'Index {idx}')
                    prices_info[price_type] = {
                        'current': valid_prices[-1],
                        'min': min(valid_prices),
                        'max': max(valid_prices),
                        'avg': sum(valid_prices) / len(valid_prices),
                        'data_points': len(valid_prices)
                    }
    
    return prices_info


async def test_product_complete(client, asin, domain=4):
    """Test complet d'un produit"""
    print(f"\n{'='*100}")
    print(f"🆔 ASIN: {asin} | 🌍 Amazon.fr (domain={domain})")
    print(f"{'='*100}")
    
    try:
        response = await client.get(
            "https://api.keepa.com/product",
            params={
                "key": KEEPA_API_KEY,
                "domain": domain,
                "asin": asin,
                "stats": 1,
                "history": 1,
                "offers": 1,
                "rating": 1
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}: {response.text[:100]}")
            return None
        
        data = response.json()
        print(f"💰 Tokens restants: {data.get('tokensLeft', 'N/A')}")
        
        products = data.get('products', [])
        if not products:
            print("❌ Aucun produit")
            return None
        
        product = products[0]
        
        # Informations de base
        print(f"\n📦 INFORMATIONS DE BASE:")
        print(f"   ASIN: {product.get('asin', 'N/A')}")
        print(f"   Titre: {product.get('title', 'N/A')}")
        print(f"   Marque: {product.get('brand', 'N/A')}")
        print(f"   Fabricant: {product.get('manufacturer', 'N/A')}")
        print(f"   Type: {product.get('productType', 'N/A')}")
        
        # EAN/UPC
        ean_list = product.get('eanList', [])
        upc_list = product.get('upcList', [])
        if ean_list:
            print(f"   EAN: {', '.join(ean_list)}")
        if upc_list:
            print(f"   UPC: {', '.join(upc_list)}")
        
        # Categories
        cat_tree = product.get('categoryTree', [])
        if cat_tree:
            cat_names = [c.get('name', '') for c in cat_tree if c.get('name')]
            if cat_names:
                print(f"   Catégories: {' > '.join(cat_names[:3])}")
        
        # Images
        images = product.get('imagesCSV', '')
        if images:
            img_list = images.split(',')
            print(f"   Images: {len(img_list)} disponible(s)")
            if img_list[0]:
                print(f"   URL: https://images-na.ssl-images-amazon.com/images/I/{img_list[0]}")
        
        # Dates
        tracking_since = product.get('trackingSince', -1)
        if tracking_since > 0:
            print(f"   Suivi depuis: Keepa minute {tracking_since}")
        
        # Prix détaillés
        print(f"\n💰 PRIX ET HISTORIQUE:")
        prices = extract_all_prices(product)
        
        if prices:
            for price_type, price_data in prices.items():
                if price_type in ['Amazon', 'Nouveau', 'Buy Box']:
                    print(f"\n   📊 {price_type}:")
                    print(f"      Actuel: {price_data['current']:.2f} EUR")
                    print(f"      Min: {price_data['min']:.2f} | Max: {price_data['max']:.2f} | Moy: {price_data['avg']:.2f}")
                    print(f"      Points de données: {price_data['data_points']}")
        else:
            print("   ⚠️  Aucune donnée de prix disponible")
        
        # Stats
        if 'stats' in product and product['stats']:
            stats = product['stats']
            print(f"\n📈 STATISTIQUES KEEPA:")
            
            # Current prices from stats
            current = stats.get('current', [])
            if current and len(current) > 0:
                if current[0] and current[0] > 0:
                    print(f"   Prix Amazon (stats): {current[0]/100:.2f} EUR")
                if len(current) > 3 and current[3] and current[3] > 0:
                    print(f"   Classement ventes: #{current[3]}")
            
            # Sales rank
            avg_rank = stats.get('avg', [])
            if avg_rank and len(avg_rank) > 3 and avg_rank[3]:
                ranks = avg_rank[3]
                if len(ranks) > 0:
                    print(f"   Classement moyen 30j: #{ranks[0]}")
                if len(ranks) > 1:
                    print(f"   Classement moyen 90j: #{ranks[1]}")
            
            # Other stats
            print(f"   Statistiques disponibles: {len(stats)} types")
        
        # Availability
        avail = product.get('availabilityAmazon', -1)
        if avail == 0:
            print(f"\n✅ Disponibilité: En stock")
        elif avail == 1:
            print(f"\n⚠️  Disponibilité: Temporairement en rupture")
        elif avail == 2:
            print(f"\n❌ Disponibilité: Indisponible")
        
        # Offres
        offers = product.get('offers', [])
        if offers:
            print(f"\n🏪 OFFRES:")
            print(f"   Nombre d'offres: {len(offers)}")
            for i, offer in enumerate(offers[:3]):
                print(f"   Offre #{i+1}: {offer}")
        
        # Rating
        rating = product.get('rating', {})
        if rating:
            print(f"\n⭐ ÉVALUATIONS:")
            for key, val in rating.items():
                print(f"   {key}: {val}")
        
        # Résumé JSON
        result = {
            'asin': product.get('asin'),
            'title': product.get('title'),
            'brand': product.get('brand'),
            'ean': ean_list[0] if ean_list else None,
            'prices': prices,
            'tracking_since': tracking_since,
            'available': avail
        }
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Tests principaux"""
    print("="*100)
    print("  TEST KEEPA API - EXTRACTION COMPLÈTE DES DONNÉES")
    print("="*100)
    print("\n🔑 API Key: Configurée")
    print("🎯 Objectif: Extraire toutes les données disponibles pour chaque produit\n")
    
    # Produits à tester
    test_products = [
        'B0CHBQX4Z9',  # iPhone 15
        'B0BSHF7WHW',  # Samsung Galaxy S23
        'B09G9FPHY6',  # AirPods
        'B08L5VN58M',  # Echo Dot
    ]
    
    results = []
    
    async with httpx.AsyncClient() as client:
        for asin in test_products:
            result = await test_product_complete(client, asin)
            if result:
                results.append(result)
            await asyncio.sleep(2)  # Rate limiting
    
    # Résumé
    print(f"\n{'='*100}")
    print(f"  RÉSUMÉ FINAL")
    print(f"{'='*100}")
    print(f"\n✅ Produits testés avec succès: {len(results)}/{len(test_products)}\n")
    
    if results:
        for r in results:
            title = r['title'] if r['title'] else '(Sans titre)'
            brand = r['brand'] if r['brand'] else 'N/A'
            num_prices = len(r['prices'])
            print(f"🆔 {r['asin']}")
            print(f"   Marque: {brand} | Titre: {title[:50]}")
            print(f"   Prix disponibles: {num_prices} type(s)")
            if r['prices']:
                for ptype, pdata in list(r['prices'].items())[:2]:
                    print(f"      • {ptype}: {pdata['current']:.2f} EUR")
            print()
    
    # Save results
    output = "/app/keepa_complete_test_results.json"
    with open(output, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': asyncio.get_event_loop().time(),
            'results': results,
            'success_count': len(results),
            'total_tests': len(test_products)
        }, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Résultats complets sauvegardés: {output}")
    print("\n✅ TESTS KEEPA TERMINÉS\n")
    print("="*100 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
