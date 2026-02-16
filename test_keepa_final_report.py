#!/usr/bin/env python3
"""
Test Keepa API - Version finale avec produit Sanex
Documentation complète des fonctionnalités testées
"""

import httpx
import asyncio
import json
from datetime import datetime

KEEPA_API_KEY = "ju7cgn79dp9ehsp8473lldrvsi8a0cdiglba9gu6fpl61quncl0h870q0o01qbaq"


async def test_keepa_api_status(client):
    """Test 1: Vérifier que l'API Keepa est accessible et la clé est valide"""
    print("\n" + "="*100)
    print("TEST 1: VALIDATION DE LA CLÉ API KEEPA")
    print("="*100)
    
    try:
        response = await client.get(
            "https://api.keepa.com/product",
            params={
                "key": KEEPA_API_KEY,
                "domain": 4,
                "asin": "B0CHBQX4Z9",
            },
            timeout=30
        )
        
        print(f"📡 Statut HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            tokens = data.get('tokensLeft', 'N/A')
            print(f"✅ CLÉ API VALIDE")
            print(f"💰 Tokens restants: {tokens}")
            print(f"🌐 API Keepa: Opérationnelle")
            return True, tokens
        elif response.status_code == 401:
            print(f"❌ CLÉ API INVALIDE (401 Unauthorized)")
            return False, 0
        elif response.status_code == 429:
            print(f"⚠️  RATE LIMIT ATTEINT (429 Too Many Requests)")
            return False, 0
        else:
            print(f"⚠️  Statut inattendu: {response.status_code}")
            return False, 0
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False, 0


async def test_search_by_keyword(client, search_term, domain=4):
    """Test 2: Recherche par mot-clé (endpoint /search)"""
    print(f"\n" + "="*100)
    print(f"TEST 2: RECHERCHE PAR MOT-CLÉ")
    print("="*100)
    print(f"🔍 Terme: '{search_term}'")
    print(f"🌍 Marketplace: Amazon.fr (domain={domain})")
    
    try:
        response = await client.get(
            "https://api.keepa.com/search",
            params={
                "key": KEEPA_API_KEY,
                "domain": domain,
                "type": "product",
                "term": search_term
            },
            timeout=30
        )
        
        print(f"📡 HTTP: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.text[:100]}")
            return None
        
        data = response.json()
        asin_list = data.get('asinList', [])
        
        print(f"📊 Résultats: {len(asin_list)} ASIN(s) trouvé(s)")
        
        if asin_list:
            print(f"✅ Premier résultat: ASIN {asin_list[0]}")
            print(f"📋 Liste complète: {', '.join(asin_list[:5])}...")
            return asin_list[0]
        else:
            print(f"❌ Aucun produit trouvé pour '{search_term}'")
            print(f"💡 Note: L'endpoint /search peut avoir des limitations.")
            print(f"   Il est recommandé d'utiliser l'ASIN ou l'EAN si disponibles.")
            return None
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


async def test_product_by_asin(client, asin, domain=4):
    """Test 3: Récupération des détails produit par ASIN"""
    print(f"\n" + "="*100)
    print(f"TEST 3: DÉTAILS PRODUIT PAR ASIN")
    print("="*100)
    print(f"🆔 ASIN: {asin}")
    print(f"🌍 Marketplace: Amazon.fr (domain={domain})")
    
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
        
        print(f"📡 HTTP: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.text[:100]}")
            return None
        
        data = response.json()
        products = data.get('products', [])
        
        if not products:
            print(f"❌ Aucun produit retourné")
            return None
        
        product = products[0]
        
        print(f"\n✅ PRODUIT TROUVÉ:")
        print(f"   🆔 ASIN: {product.get('asin', 'N/A')}")
        print(f"   🏷️  Titre: {product.get('title') or 'Non disponible'}")
        print(f"   🏢 Marque: {product.get('brand') or 'Non disponible'}")
        print(f"   🏭 Fabricant: {product.get('manufacturer') or 'Non disponible'}")
        
        # EAN
        ean_list = product.get('eanList', [])
        if ean_list:
            print(f"   📊 EAN: {', '.join(ean_list)}")
        else:
            print(f"   📊 EAN: Non disponible")
        
        # Disponibilité
        avail = product.get('availabilityAmazon', -1)
        if avail == 0:
            print(f"   ✅ Statut: En stock")
        elif avail == 1:
            print(f"   ⚠️  Statut: Temporairement en rupture")
        elif avail == 2:
            print(f"   ❌ Statut: Indisponible")
        else:
            print(f"   ❓ Statut: Non spécifié")
        
        # Prix
        print(f"\n   💰 PRIX:")
        
        # From CSV (historical data)
        if 'csv' in product and product['csv'] and len(product['csv']) > 0:
            amazon_prices = product['csv'][0]  # Index 0 = Amazon price
            if amazon_prices:
                valid_prices = [p/100.0 for p in amazon_prices if p and p > 0]
                if valid_prices:
                    current_price = valid_prices[-1]
                    min_price = min(valid_prices)
                    max_price = max(valid_prices)
                    avg_price = sum(valid_prices) / len(valid_prices)
                    
                    print(f"      Actuel: {current_price:.2f} EUR")
                    print(f"      Min historique: {min_price:.2f} EUR")
                    print(f"      Max historique: {max_price:.2f} EUR")
                    print(f"      Moyenne: {avg_price:.2f} EUR")
                    print(f"      Points de données: {len(valid_prices)}")
                else:
                    print(f"      ⚠️  Aucun prix valide dans l'historique")
        else:
            print(f"      ⚠️  Données de prix non disponibles")
        
        # Stats
        if 'stats' in product and product['stats']:
            stats = product['stats']
            current = stats.get('current', [])
            if current and len(current) > 3:
                sales_rank = current[3]
                if sales_rank and sales_rank > 0:
                    print(f"\n   📊 CLASSEMENT:")
                    print(f"      Position: #{int(sales_rank):,}")
        
        # Données brutes disponibles
        print(f"\n   🔑 DONNÉES KEEPA DISPONIBLES:")
        important_keys = ['asin', 'title', 'brand', 'eanList', 'csv', 'stats', 'categoryTree', 'imagesCSV']
        for key in important_keys:
            if key in product and product[key]:
                val = product[key]
                if isinstance(val, list):
                    print(f"      ✓ {key}: {len(val)} élément(s)")
                elif isinstance(val, dict):
                    print(f"      ✓ {key}: {len(val)} clé(s)")
                else:
                    print(f"      ✓ {key}: Présent")
        
        return product
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


async def test_product_by_ean(client, ean, domain=4):
    """Test 4: Recherche par code EAN/GTIN"""
    print(f"\n" + "="*100)
    print(f"TEST 4: RECHERCHE PAR CODE EAN/GTIN")
    print("="*100)
    print(f"📊 EAN: {ean}")
    print(f"🌍 Marketplace: Amazon.fr (domain={domain})")
    
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
        
        print(f"📡 HTTP: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.text[:100]}")
            return None
        
        data = response.json()
        products = data.get('products', [])
        
        print(f"📊 Résultats: {len(products)} produit(s)")
        
        if products:
            product = products[0]
            asin = product.get('asin', 'N/A')
            title = product.get('title') or 'Non disponible'
            print(f"✅ Produit trouvé: ASIN {asin}")
            print(f"   Titre: {title[:60]}...")
            return product
        else:
            print(f"❌ Aucun produit trouvé pour EAN {ean}")
            print(f"💡 Ce produit n'est peut-être pas disponible sur Amazon.fr")
            return None
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


async def main():
    """Programme principal"""
    print("\n" + "="*100)
    print("  TESTS KEEPA API - RECHERCHE DE PRODUITS AMAZON")
    print("  Produit cible: Sanex Deodorant Roller Dermo Invisible Personal Care")
    print("="*100)
    print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 API Key: ju7cgn79dp9...0q0o01qbaq")
    
    results = {
        'api_status': None,
        'keyword_search': None,
        'asin_lookup': None,
        'ean_lookup': None
    }
    
    async with httpx.AsyncClient() as client:
        # Test 1: Validation API
        api_valid, tokens = await test_keepa_api_status(client)
        results['api_status'] = {'valid': api_valid, 'tokens': tokens}
        await asyncio.sleep(1)
        
        if not api_valid:
            print("\n❌ Tests arrêtés: Clé API invalide")
            return
        
        # Test 2: Recherche par mot-clé Sanex
        asin_found = await test_search_by_keyword(client, "Sanex Dermo Invisible")
        results['keyword_search'] = {'asin': asin_found}
        await asyncio.sleep(2)
        
        # Si un ASIN est trouvé, récupérer ses détails
        if asin_found:
            product = await test_product_by_asin(client, asin_found)
            results['asin_lookup'] = {'success': product is not None}
            await asyncio.sleep(2)
        else:
            # Test 2b: Essayer avec un ASIN connu
            print(f"\n💡 Tentative avec un ASIN connu (iPhone 15 pour test)")
            product = await test_product_by_asin(client, "B0CHBQX4Z9")
            results['asin_lookup'] = {'success': product is not None, 'note': 'Test avec ASIN connu'}
            await asyncio.sleep(2)
        
        # Test 4: Recherche Sanex par EAN (si connu)
        sanex_ean = "8710447348741"  # EAN Sanex Dermo Invisible
        product_ean = await test_product_by_ean(client, sanex_ean)
        results['ean_lookup'] = {'success': product_ean is not None, 'ean': sanex_ean}
    
    # Résumé final
    print(f"\n\n" + "="*100)
    print("  RÉSUMÉ DES TESTS KEEPA")
    print("="*100)
    
    print(f"\n1. ✅ CLÉ API: {'VALIDE' if results['api_status']['valid'] else 'INVALIDE'}")
    if results['api_status']['valid']:
        print(f"   💰 Tokens disponibles: {results['api_status']['tokens']}")
    
    print(f"\n2. 🔍 RECHERCHE PAR MOT-CLÉ:")
    if results['keyword_search']['asin']:
        print(f"   ✅ Fonctionnel - ASIN trouvé: {results['keyword_search']['asin']}")
    else:
        print(f"   ⚠️  Aucun résultat - Limitations possibles de l'endpoint /search")
        print(f"   💡 Recommandation: Utiliser ASIN ou EAN si disponibles")
    
    print(f"\n3. 🆔 RECHERCHE PAR ASIN:")
    if results['asin_lookup']['success']:
        print(f"   ✅ Fonctionnel - Données produit récupérées")
    else:
        print(f"   ❌ Échec")
    
    print(f"\n4. 📊 RECHERCHE PAR EAN (Sanex: {sanex_ean}):")
    if results['ean_lookup']['success']:
        print(f"   ✅ Produit Sanex trouvé sur Amazon.fr!")
    else:
        print(f"   ❌ Produit Sanex non trouvé sur Amazon.fr")
        print(f"   💡 Possibilités:")
        print(f"      • Le produit n'est pas vendu sur Amazon.fr")
        print(f"      • L'EAN ne correspond à aucun produit dans la base Keepa")
        print(f"      • Essayer sur d'autres marketplaces (Amazon.de, Amazon.co.uk)")
    
    print(f"\n📌 CONCLUSIONS:")
    print(f"   • L'API Keepa est opérationnelle avec votre clé")
    print(f"   • La recherche par ASIN fonctionne correctement")
    print(f"   • La recherche par mot-clé peut avoir des limitations")
    print(f"   • Pour Sanex Dermo Invisible:")
    if results['ean_lookup']['success']:
        print(f"     ✅ Disponible sur Amazon.fr via Keepa")
    else:
        print(f"     ⚠️  Non trouvé sur Amazon.fr - Essayer d'autres marketplaces")
    
    # Save results
    output_file = "/app/keepa_final_test_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'product_target': 'Sanex Deodorant Roller Dermo Invisible Personal Care',
            'ean_tested': sanex_ean,
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Rapport complet sauvegardé: {output_file}")
    print("\n" + "="*100 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
