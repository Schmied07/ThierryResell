# 🚀 Nouvelles Fonctionnalités Avancées

## 🔮 Prévisions de Profitabilité (30/60/90 jours)

### Description
Analyse prédictive basée sur l'historique des prix Amazon (via Keepa) pour estimer les profits futurs.

### Fonctionnement
- **Algorithme**: Régression linéaire sur l'historique Keepa
- **Prévisions**: Prix Amazon et profits estimés à 30, 60 et 90 jours
- **Confiance**: Niveau de fiabilité (Haute/Moyenne/Faible) basé sur la volatilité et les données disponibles
- **Recommandations**:
  - ✅ **Acheter maintenant**: Profit en hausse attendu
  - ⏳ **Attendre**: Profit stable, surveiller
  - ⚠️ **Risqué**: Profit en baisse ou volatilité élevée

### Affichage Frontend
- Badge de recommandation d'action
- 3 cartes de prévision (30/60/90j) avec:
  - Prix Amazon prévu
  - Profit prévu
  - Changement en %
- Évaluation du risque de volatilité
- Indicateur de tendance

### Backend
- Fonction: `predict_price_profitability()`
- Endpoint: `POST /api/catalog/compare/{product_id}`
- Champ retourné: `profitability_predictions`

---

## 🌍 Arbitrage Multi-Marchés Amazon

### Description
Comparaison des prix et marges sur 4 marchés Amazon européens pour identifier les opportunités d'arbitrage international.

### Marchés Analysés
- 🇫🇷 **France** (Amazon.fr) - EUR
- 🇬🇧 **Royaume-Uni** (Amazon.co.uk) - GBP → EUR (taux: 1.17)
- 🇩🇪 **Allemagne** (Amazon.de) - EUR
- 🇪🇸 **Espagne** (Amazon.es) - EUR

### Fonctionnement
- **API Keepa**: Appels par domaine pour chaque marché
- **Conversion devises**: GBP automatiquement converti en EUR
- **Calcul marges**: Prix vente - Prix achat - Frais Amazon (15% par marché)
- **Opportunités**: Identification du meilleur marché d'achat (prix le plus bas) et de vente (marge la plus élevée)

### Affichage Frontend
- **Carte Best Sell** 💰: Marché avec la marge la plus élevée
- **Carte Best Buy** 🛒: Marché avec le prix le plus bas
- **Badge Arbitrage**: Profit supplémentaire potentiel via arbitrage
- **Tableau comparatif**: Prix, conversion EUR, marge pour chaque marché

### Backend
- Fonction: `analyze_multi_market_arbitrage()`
- Endpoint: `POST /api/catalog/compare/{product_id}`
- Champ retourné: `multi_market_arbitrage`

---

## 📊 Données MOCK

Les deux fonctionnalités utilisent des **données simulées** (MOCK) si aucune clé API Keepa n'est configurée, permettant de tester l'interface sans frais.

Pour utiliser les **vraies données**:
1. Allez dans **Paramètres** → **Clés API**
2. Configurez votre **clé API Keepa**
3. Les prévisions et l'arbitrage utiliseront les données réelles

---

## 🎯 Cas d'Usage

### Prévisions de Profitabilité
**Scénario**: Vous hésitez à acheter un produit maintenant.
- ✅ **Recommandation "Acheter maintenant"** → Le profit devrait augmenter, achetez !
- ⏳ **Recommandation "Attendre"** → Le profit est stable, surveillez
- ⚠️ **Recommandation "Risque"** → Forte volatilité ou baisse attendue, attendez

### Arbitrage Multi-Marchés
**Scénario**: Vous voulez maximiser votre marge.
- 💰 Identifiez le **meilleur marché de vente** (ex: Allemagne avec +15€ de marge)
- 🛒 Trouvez le **meilleur marché d'achat** (ex: Royaume-Uni avec prix le plus bas)
- 🌟 **Opportunité d'arbitrage**: Achetez en UK, vendez en DE = profit supplémentaire !

---

## 🔧 Configuration Technique

### Prérequis Backend
- Python 3.9+
- Bibliothèques: `httpx`, `pandas`, `numpy` (implicite via pandas)

### Prérequis Frontend
- React 18+
- Lucide React pour les icônes

### API Keepa
- **Endpoint Product**: `https://api.keepa.com/product`
- **Paramètres**:
  - `key`: Votre clé API Keepa
  - `domain`: 1 (FR), 2 (UK), 3 (DE), 4 (ES)
  - `code`: GTIN/EAN du produit
  - `stats`: 1 (inclure statistiques et prix actuels)

---

## 📈 Améliorations Futures

### Prévisions
- [ ] Modèle ML avancé (Prophet, LSTM)
- [ ] Analyse saisonnalité
- [ ] Alertes automatiques quand recommandation change

### Arbitrage
- [ ] Ajouter plus de marchés (IT, NL, etc.)
- [ ] Inclure frais de douane/TVA
- [ ] Calculer frais logistiques FBA internationaux
- [ ] Alertes opportunités arbitrage en temps réel

---

## 📚 Ressources

- [Documentation Keepa API](https://keepa.com/#!api)
- [Amazon FBA Fees](https://sell.amazon.fr/pricing)
- [Régression linéaire - Wikipedia](https://fr.wikipedia.org/wiki/R%C3%A9gression_lin%C3%A9aire)

---

**Créé avec ❤️ pour optimiser vos marges de revente Amazon !**
