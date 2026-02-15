from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
import base64
import random
import pandas as pd
import io
from fastapi.responses import StreamingResponse
import xlsxwriter
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# ==================== PRODUCT CATEGORIES ====================

PRODUCT_CATEGORIES = {
    "Électronique": {
        "keywords": ["iphone", "samsung", "phone", "téléphone", "laptop", "ordinateur", "pc", "macbook",
                     "airpods", "écouteurs", "casque", "tablette", "ipad", "tv", "télévision", "monitor",
                     "écran", "camera", "gopro", "drone", "playstation", "ps5", "xbox", "nintendo", "switch",
                     "gpu", "processeur", "ram", "ssd", "carte graphique", "clavier", "souris", "imprimante",
                     "enceinte", "bluetooth", "smartwatch", "montre connectée", "apple watch", "pixel",
                     "galaxy", "huawei", "oneplus", "realme", "oppo", "xiaomi", "console", "gaming"],
        "amazon_price_range": (50, 1500),
    },
    "Mode": {
        "keywords": ["nike", "adidas", "chaussure", "sneaker", "vêtement", "robe", "pantalon", "jean",
                     "t-shirt", "chemise", "veste", "manteau", "sac", "lunettes", "montre", "bijou",
                     "bracelet", "collier", "air max", "jordan", "yeezy", "puma", "reebok", "new balance",
                     "converse", "vans", "pull", "sweat", "hoodie", "short", "jupe", "blouson", "boots"],
        "amazon_price_range": (15, 300),
    },
    "Maison": {
        "keywords": ["meuble", "canapé", "lit", "matelas", "lampe", "table", "chaise", "bureau",
                     "étagère", "rangement", "aspirateur", "robot", "cuisine", "cafetière", "mixer",
                     "four", "micro-ondes", "réfrigérateur", "lave-linge", "sèche-linge", "décoration",
                     "coussin", "rideau", "tapis", "vaisselle", "casserole", "poêle"],
        "amazon_price_range": (20, 800),
    },
    "Sport": {
        "keywords": ["vélo", "tapis de course", "haltère", "fitness", "yoga", "ballon", "raquette",
                     "tennis", "football", "basketball", "running", "natation", "ski", "randonnée",
                     "camping", "sac à dos", "gourde", "nutrition", "protéine", "musculation"],
        "amazon_price_range": (10, 500),
    },
    "Jouets": {
        "keywords": ["lego", "playmobil", "poupée", "figurine", "puzzle", "jeu de société", "nerf",
                     "peluche", "barbie", "hot wheels", "train", "voiture télécommandée", "robot jouet"],
        "amazon_price_range": (10, 150),
    },
    "Livres": {
        "keywords": ["livre", "roman", "manga", "bd", "bande dessinée", "ebook", "kindle",
                     "dictionnaire", "encyclopédie", "guide", "manuel"],
        "amazon_price_range": (5, 50),
    },
    "Beauté": {
        "keywords": ["parfum", "maquillage", "crème", "shampoing", "soin", "sérum", "mascara",
                     "rouge à lèvres", "fond de teint", "brosse", "sèche-cheveux", "rasoir",
                     "épilateur", "manucure"],
        "amazon_price_range": (5, 200),
    },
}

def detect_category(query: str) -> str:
    """Auto-detect product category from search query"""
    query_lower = query.lower()
    best_match = None
    best_score = 0
    
    for category, config in PRODUCT_CATEGORIES.items():
        score = 0
        for keyword in config["keywords"]:
            if keyword in query_lower:
                # Longer keyword matches are better
                score += len(keyword)
        if score > best_score:
            best_score = score
            best_match = category
    
    return best_match or "Général"

def generate_amazon_reference_price(query: str, category: str) -> dict:
    """Simulate Keepa Amazon price data for a product"""
    price_range = PRODUCT_CATEGORIES.get(category, {}).get("amazon_price_range", (30, 300))
    
    # Generate a base price that's somewhat consistent for the same query
    # Use hash of query to generate consistent-ish prices
    hash_val = sum(ord(c) for c in query)
    random.seed(hash_val)
    base_price = round(random.uniform(price_range[0], price_range[1]), 2)
    random.seed()  # Reset seed
    
    # Generate price history
    price_history = []
    for i in range(30):
        date = datetime.now(timezone.utc) - timedelta(days=30 - i)
        variation = random.uniform(0.85, 1.15)
        price = round(base_price * variation, 2)
        price_history.append({
            'date': date.isoformat(),
            'price': price
        })
    
    # Current Amazon price (slight variation from base)
    current_amazon_price = round(base_price * random.uniform(0.95, 1.05), 2)
    
    # Generate a fake but realistic ASIN
    asin_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    asin = "B0" + ''.join(random.choice(asin_chars) for _ in range(8))
    
    return {
        'asin': asin,
        'title': query,
        'current_price': current_amazon_price,
        'lowest_30d': min(p['price'] for p in price_history),
        'highest_30d': max(p['price'] for p in price_history),
        'average_30d': round(sum(p['price'] for p in price_history) / len(price_history), 2),
        'price_history': price_history,
        'currency': 'EUR',
        'category': category,
        'mock_data': True
    }

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'resell-corner-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer()

app = FastAPI(title="Resell Corner API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=2)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

class ApiKeysUpdate(BaseModel):
    google_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    keepa_api_key: Optional[str] = None

class ApiKeysResponse(BaseModel):
    google_api_key_set: bool
    google_search_engine_id_set: bool
    keepa_api_key_set: bool

class SupplierCreate(BaseModel):
    name: str
    url: str
    logo_url: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None

class SupplierResponse(BaseModel):
    id: str
    user_id: str
    name: str
    url: str
    logo_url: Optional[str]
    category: Optional[str]
    notes: Optional[str]
    created_at: datetime

class ProductSearchRequest(BaseModel):
    query: str
    search_type: str = "text"
    category: Optional[str] = None  # Optional category filter

class AlertCreate(BaseModel):
    product_name: str
    product_url: Optional[str] = None
    target_price: float
    current_price: Optional[float] = None
    supplier_id: Optional[str] = None

class AlertResponse(BaseModel):
    id: str
    user_id: str
    product_name: str
    product_url: Optional[str]
    target_price: float
    current_price: Optional[float]
    supplier_id: Optional[str]
    is_active: bool
    triggered: bool
    created_at: datetime

class FavoriteCreate(BaseModel):
    product_name: str
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None
    search_query: Optional[str] = None

class FavoriteResponse(BaseModel):
    id: str
    user_id: str
    product_name: str
    product_url: Optional[str]
    image_url: Optional[str]
    notes: Optional[str]
    search_query: Optional[str]
    created_at: datetime

class PriceComparisonResult(BaseModel):
    supplier: str
    supplier_url: str
    price: float
    currency: str = "EUR"
    availability: str = "In Stock"
    shipping: Optional[float] = None
    total_price: float
    profit_margin: Optional[float] = None
    is_user_supplier: bool = False
    supplier_category: Optional[str] = None

class SearchResult(BaseModel):
    product_name: str
    image_url: Optional[str]
    detected_labels: List[str] = []
    comparisons: List[PriceComparisonResult] = []
    lowest_price: Optional[float] = None
    highest_price: Optional[float] = None
    average_price: Optional[float] = None
    category: Optional[str] = None
    amazon_reference_price: Optional[float] = None
    keepa_data: Optional[Dict[str, Any]] = None

# ==================== AMAZON FEES ====================

# Amazon referral fee percentage (standard ~15% TTC)
AMAZON_FEE_PERCENTAGE = 0.15

def calculate_amazon_fees(amazon_price: float) -> float:
    """Calculate Amazon referral fees (15% TTC)"""
    return round(amazon_price * AMAZON_FEE_PERCENTAGE, 2)

def calculate_margin(selling_price: float, buying_price: float, fees: float) -> dict:
    """Calculate net margin after Amazon fees"""
    margin_eur = round(selling_price - buying_price - fees, 2)
    margin_percentage = round((margin_eur / selling_price) * 100, 2) if selling_price > 0 else 0
    return {
        'margin_eur': margin_eur,
        'margin_percentage': margin_percentage
    }

# ==================== CATALOG MODELS ====================

class CatalogProduct(BaseModel):
    id: str
    user_id: str
    gtin: str
    name: str
    category: str
    brand: str
    supplier_price_gbp: float
    supplier_price_eur: float
    inventory: str
    number_of_offers: int
    product_link: Optional[str] = None
    # Price data
    amazon_price_eur: Optional[float] = None  # Prix de vente Amazon (via Keepa)
    google_lowest_price_eur: Optional[float] = None  # Prix le plus bas en ligne (via Google)
    # Comparison results
    cheapest_source: Optional[str] = None  # "supplier" or "google"
    cheapest_buy_price_eur: Optional[float] = None  # min(supplier, google)
    amazon_fees_eur: Optional[float] = None  # Frais Amazon (15% TTC)
    # Margins
    amazon_margin_eur: Optional[float] = None  # Marge nette = amazon - achat - frais
    amazon_margin_percentage: Optional[float] = None  # % marge nette
    supplier_margin_eur: Optional[float] = None  # Marge si achat fournisseur
    supplier_margin_percentage: Optional[float] = None
    google_margin_eur: Optional[float] = None  # Marge si achat Google
    google_margin_percentage: Optional[float] = None
    google_vs_amazon_diff_eur: Optional[float] = None  # Diff prix Google vs Amazon
    supplier_vs_google_diff_eur: Optional[float] = None  # Diff prix Fournisseur vs Google
    # Legacy (keep for backwards compat)
    google_price_eur: Optional[float] = None
    best_price_eur: Optional[float] = None
    margin_eur: Optional[float] = None
    margin_percentage: Optional[float] = None
    last_compared_at: Optional[datetime] = None
    created_at: datetime

class CatalogStats(BaseModel):
    total_products: int
    compared_products: int
    total_potential_margin: float
    avg_margin_percentage: float
    best_opportunity_margin: float

# ==================== CURRENCY CONVERSION ====================

# Fixed GBP to EUR rate (you can make this dynamic with an API later)
GBP_TO_EUR_RATE = 1.17  # 1 GBP = 1.17 EUR (approximate)

def convert_gbp_to_eur(price_gbp: float) -> float:
    """Convert GBP to EUR"""
    return round(price_gbp * GBP_TO_EUR_RATE, 2)

async def get_exchange_rate() -> float:
    """Get current GBP to EUR exchange rate from API (fallback to fixed rate)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.exchangerate-api.com/v4/latest/GBP",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data['rates'].get('EUR', GBP_TO_EUR_RATE)
    except Exception as e:
        logger.warning(f"Exchange rate API error, using fixed rate: {e}")
    return GBP_TO_EUR_RATE

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({'id': payload['user_id']}, {'_id': 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user = {
        'id': user_id,
        'email': user_data.email,
        'name': user_data.name,
        'password_hash': hash_password(user_data.password),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'api_keys': {}
    }
    await db.users.insert_one(user)
    
    token = create_token(user_id, user_data.email)
    return {'token': token, 'user': {'id': user_id, 'email': user_data.email, 'name': user_data.name}}

@api_router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await db.users.find_one({'email': credentials.email}, {'_id': 0})
    if not user or not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'], user['email'])
    return {'token': token, 'user': {'id': user['id'], 'email': user['email'], 'name': user['name']}}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user['id'],
        email=user['email'],
        name=user['name'],
        created_at=datetime.fromisoformat(user['created_at']) if isinstance(user['created_at'], str) else user['created_at']
    )

# ==================== API KEYS ROUTES ====================

@api_router.get("/settings/api-keys", response_model=ApiKeysResponse)
async def get_api_keys(user: dict = Depends(get_current_user)):
    api_keys = user.get('api_keys', {})
    return ApiKeysResponse(
        google_api_key_set=bool(api_keys.get('google_api_key')),
        google_search_engine_id_set=bool(api_keys.get('google_search_engine_id')),
        keepa_api_key_set=bool(api_keys.get('keepa_api_key'))
    )

@api_router.put("/settings/api-keys", response_model=ApiKeysResponse)
async def update_api_keys(keys: ApiKeysUpdate, user: dict = Depends(get_current_user)):
    update_data = {}
    if keys.google_api_key is not None:
        update_data['api_keys.google_api_key'] = keys.google_api_key if keys.google_api_key else None
    if keys.google_search_engine_id is not None:
        update_data['api_keys.google_search_engine_id'] = keys.google_search_engine_id if keys.google_search_engine_id else None
    if keys.keepa_api_key is not None:
        update_data['api_keys.keepa_api_key'] = keys.keepa_api_key if keys.keepa_api_key else None
    
    if update_data:
        await db.users.update_one({'id': user['id']}, {'$set': update_data})
    
    updated_user = await db.users.find_one({'id': user['id']}, {'_id': 0})
    api_keys = updated_user.get('api_keys', {})
    return ApiKeysResponse(
        google_api_key_set=bool(api_keys.get('google_api_key')),
        google_search_engine_id_set=bool(api_keys.get('google_search_engine_id')),
        keepa_api_key_set=bool(api_keys.get('keepa_api_key'))
    )

# ==================== SUPPLIERS ROUTES ====================

@api_router.post("/suppliers", response_model=SupplierResponse)
async def create_supplier(supplier: SupplierCreate, user: dict = Depends(get_current_user)):
    supplier_id = str(uuid.uuid4())
    supplier_doc = {
        'id': supplier_id,
        'user_id': user['id'],
        'name': supplier.name,
        'url': supplier.url,
        'logo_url': supplier.logo_url,
        'category': supplier.category,
        'notes': supplier.notes,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.suppliers.insert_one(supplier_doc)
    return SupplierResponse(**{**supplier_doc, 'created_at': datetime.fromisoformat(supplier_doc['created_at'])})

@api_router.get("/suppliers", response_model=List[SupplierResponse])
async def get_suppliers(user: dict = Depends(get_current_user)):
    suppliers = await db.suppliers.find({'user_id': user['id']}, {'_id': 0}).to_list(1000)
    return [SupplierResponse(**{**s, 'created_at': datetime.fromisoformat(s['created_at']) if isinstance(s['created_at'], str) else s['created_at']}) for s in suppliers]

@api_router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str, user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({'id': supplier_id, 'user_id': user['id']}, {'_id': 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SupplierResponse(**{**supplier, 'created_at': datetime.fromisoformat(supplier['created_at']) if isinstance(supplier['created_at'], str) else supplier['created_at']})

@api_router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: str, supplier: SupplierCreate, user: dict = Depends(get_current_user)):
    existing = await db.suppliers.find_one({'id': supplier_id, 'user_id': user['id']})
    if not existing:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    update_data = supplier.model_dump(exclude_unset=True)
    await db.suppliers.update_one({'id': supplier_id}, {'$set': update_data})
    
    updated = await db.suppliers.find_one({'id': supplier_id}, {'_id': 0})
    return SupplierResponse(**{**updated, 'created_at': datetime.fromisoformat(updated['created_at']) if isinstance(updated['created_at'], str) else updated['created_at']})

@api_router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, user: dict = Depends(get_current_user)):
    result = await db.suppliers.delete_one({'id': supplier_id, 'user_id': user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier deleted"}

# ==================== ALERTS ROUTES ====================

@api_router.post("/alerts", response_model=AlertResponse)
async def create_alert(alert: AlertCreate, user: dict = Depends(get_current_user)):
    alert_id = str(uuid.uuid4())
    alert_doc = {
        'id': alert_id,
        'user_id': user['id'],
        'product_name': alert.product_name,
        'product_url': alert.product_url,
        'target_price': alert.target_price,
        'current_price': alert.current_price,
        'supplier_id': alert.supplier_id,
        'is_active': True,
        'triggered': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.alerts.insert_one(alert_doc)
    return AlertResponse(**{**alert_doc, 'created_at': datetime.fromisoformat(alert_doc['created_at'])})

@api_router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(user: dict = Depends(get_current_user)):
    alerts = await db.alerts.find({'user_id': user['id']}, {'_id': 0}).to_list(1000)
    return [AlertResponse(**{**a, 'created_at': datetime.fromisoformat(a['created_at']) if isinstance(a['created_at'], str) else a['created_at']}) for a in alerts]

@api_router.put("/alerts/{alert_id}/toggle")
async def toggle_alert(alert_id: str, user: dict = Depends(get_current_user)):
    alert = await db.alerts.find_one({'id': alert_id, 'user_id': user['id']})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    new_status = not alert['is_active']
    await db.alerts.update_one({'id': alert_id}, {'$set': {'is_active': new_status}})
    return {"is_active": new_status}

@api_router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str, user: dict = Depends(get_current_user)):
    result = await db.alerts.delete_one({'id': alert_id, 'user_id': user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted"}

# ==================== FAVORITES ROUTES ====================

@api_router.post("/favorites", response_model=FavoriteResponse)
async def create_favorite(favorite: FavoriteCreate, user: dict = Depends(get_current_user)):
    favorite_id = str(uuid.uuid4())
    favorite_doc = {
        'id': favorite_id,
        'user_id': user['id'],
        'product_name': favorite.product_name,
        'product_url': favorite.product_url,
        'image_url': favorite.image_url,
        'notes': favorite.notes,
        'search_query': favorite.search_query,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.favorites.insert_one(favorite_doc)
    return FavoriteResponse(**{**favorite_doc, 'created_at': datetime.fromisoformat(favorite_doc['created_at'])})

@api_router.get("/favorites", response_model=List[FavoriteResponse])
async def get_favorites(user: dict = Depends(get_current_user)):
    favorites = await db.favorites.find({'user_id': user['id']}, {'_id': 0}).to_list(1000)
    return [FavoriteResponse(**{**f, 'created_at': datetime.fromisoformat(f['created_at']) if isinstance(f['created_at'], str) else f['created_at']}) for f in favorites]

@api_router.delete("/favorites/{favorite_id}")
async def delete_favorite(favorite_id: str, user: dict = Depends(get_current_user)):
    result = await db.favorites.delete_one({'id': favorite_id, 'user_id': user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"message": "Favorite deleted"}

# ==================== SEARCH ROUTES ====================

def generate_mock_comparisons(product_name: str, suppliers: List[dict], category: str = None, amazon_price: float = None) -> List[PriceComparisonResult]:
    """Generate mock price comparisons for demo purposes with intelligent category matching"""
    comparisons = []
    
    # Filter suppliers by category if specified
    if category and category != "Général":
        # Matching suppliers (same category)
        matching_suppliers = [s for s in suppliers if s.get('category', '').lower() == category.lower()]
        # Also include suppliers with no category
        no_category_suppliers = [s for s in suppliers if not s.get('category')]
        relevant_suppliers = matching_suppliers + no_category_suppliers
    else:
        relevant_suppliers = suppliers
    
    # Default suppliers if user has none or no match
    default_suppliers = [
        {"name": "Amazon", "url": "https://amazon.fr", "is_default": True},
        {"name": "Cdiscount", "url": "https://cdiscount.com", "is_default": True},
        {"name": "Fnac", "url": "https://fnac.com", "is_default": True},
        {"name": "Rakuten", "url": "https://fr.rakuten.com", "is_default": True},
    ]
    
    # Use amazon_price as reference for generating realistic prices
    base_price = amazon_price if amazon_price else random.uniform(30, 300)
    
    # Add user's relevant suppliers
    for supplier in relevant_suppliers[:5]:
        # User suppliers typically offer better prices (wholesale/sourcing)
        variation = random.uniform(0.45, 0.85)  # 15-55% cheaper than Amazon
        price = round(base_price * variation, 2)
        shipping = round(random.uniform(0, 10), 2) if random.random() > 0.4 else 0
        total = round(price + shipping, 2)
        
        # Calculate profit margin based on Amazon price
        if amazon_price:
            margin = round(((amazon_price - total) / amazon_price) * 100, 1)
        else:
            margin = round(random.uniform(5, 45), 1)
        
        comparisons.append(PriceComparisonResult(
            supplier=supplier.get('name', ''),
            supplier_url=supplier.get('url', ''),
            price=price,
            currency="EUR",
            availability=random.choice(["In Stock", "In Stock", "In Stock", "Low Stock"]),
            shipping=shipping,
            total_price=total,
            profit_margin=margin,
            is_user_supplier=True,
            supplier_category=supplier.get('category', '')
        ))
    
    # Add default marketplace suppliers for comparison
    for supplier in default_suppliers[:4]:
        # Marketplaces are typically closer to Amazon price
        variation = random.uniform(0.88, 1.12)
        price = round(base_price * variation, 2)
        shipping = round(random.uniform(0, 8), 2) if random.random() > 0.5 else 0
        total = round(price + shipping, 2)
        
        # Calculate profit margin based on Amazon price
        if amazon_price:
            margin = round(((amazon_price - total) / amazon_price) * 100, 1)
        else:
            margin = round(random.uniform(-5, 15), 1)
        
        comparisons.append(PriceComparisonResult(
            supplier=supplier.get('name', ''),
            supplier_url=supplier.get('url', ''),
            price=price,
            currency="EUR",
            availability=random.choice(["In Stock", "In Stock", "In Stock", "Low Stock", "Pre-order"]),
            shipping=shipping,
            total_price=total,
            profit_margin=margin,
            is_user_supplier=False,
            supplier_category=None
        ))
    
    return sorted(comparisons, key=lambda x: x.total_price)

# ==================== CATEGORIES ROUTES ====================

@api_router.get("/categories")
async def get_categories(user: dict = Depends(get_current_user)):
    """Get available product categories"""
    # Get unique categories from user's suppliers
    suppliers = await db.suppliers.find({'user_id': user['id']}, {'_id': 0, 'category': 1}).to_list(1000)
    supplier_categories = list(set(s.get('category', '') for s in suppliers if s.get('category')))
    
    # All available categories
    all_categories = list(PRODUCT_CATEGORIES.keys())
    
    return {
        "all_categories": all_categories,
        "supplier_categories": supplier_categories,
        "category_details": {
            cat: {"keyword_count": len(config["keywords"])}
            for cat, config in PRODUCT_CATEGORIES.items()
        }
    }

@api_router.post("/search/text", response_model=SearchResult)
async def search_by_text(request: ProductSearchRequest, user: dict = Depends(get_current_user)):
    """Search products by text query with category filtering and Keepa profit margin"""
    api_keys = user.get('api_keys', {})
    google_key = api_keys.get('google_api_key')
    search_engine_id = api_keys.get('google_search_engine_id')
    keepa_key = api_keys.get('keepa_api_key')
    
    # Auto-detect category if not provided
    category = request.category if request.category else detect_category(request.query)
    
    # Get user's suppliers
    suppliers = await db.suppliers.find({'user_id': user['id']}, {'_id': 0}).to_list(100)
    
    # Get Amazon reference price from Keepa (real or mock)
    keepa_data = None
    amazon_price = None
    
    if keepa_key:
        # Try real Keepa API - use /search for text-based product search
        try:
            async with httpx.AsyncClient() as http_client:
                # Search for product on Keepa by keyword
                response = await http_client.get(
                    "https://api.keepa.com/search",
                    params={
                        "key": keepa_key,
                        "domain": 4,  # Amazon.fr
                        "type": "product",
                        "term": request.query
                    },
                    timeout=30
                )
                logger.info(f"Keepa search response status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    asin_list = data.get('asinList', [])
                    
                    # The search endpoint returns ASINs, then query for product details
                    if asin_list and len(asin_list) > 0:
                        # Get product details for the first ASIN
                        detail_response = await http_client.get(
                            "https://api.keepa.com/product",
                            params={
                                "key": keepa_key,
                                "domain": 4,
                                "asin": asin_list[0],
                                "stats": 1,
                            },
                            timeout=30
                        )
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            if detail_data.get('products') and len(detail_data['products']) > 0:
                                product_data = detail_data['products'][0]
                                stats = product_data.get('stats', {})
                                current_prices = stats.get('current', [])
                                
                                # Try Amazon price (index 0), then 3rd party new (index 1)
                                if current_prices and len(current_prices) > 0:
                                    if current_prices[0] is not None and current_prices[0] > 0:
                                        amazon_price = current_prices[0] / 100.0
                                    elif len(current_prices) > 1 and current_prices[1] is not None and current_prices[1] > 0:
                                        amazon_price = current_prices[1] / 100.0
                                
                                # Fallback: try csv price history
                                if amazon_price is None:
                                    csv_data = product_data.get('csv', [])
                                    for csv_idx in [0, 1]:  # Amazon, then 3rd party
                                        if csv_data and len(csv_data) > csv_idx and csv_data[csv_idx]:
                                            prices_array = csv_data[csv_idx]
                                            for i in range(len(prices_array) - 1, 0, -2):
                                                if prices_array[i] is not None and prices_array[i] > 0:
                                                    amazon_price = prices_array[i] / 100.0
                                                    break
                                        if amazon_price is not None:
                                            break
                                
                                # Fallback: buyBoxPrice
                                if amazon_price is None:
                                    buy_box = stats.get('buyBoxPrice', -1)
                                    if buy_box is not None and buy_box > 0:
                                        amazon_price = buy_box / 100.0
                                
                                keepa_data = {
                                    'asin': product_data.get('asin', ''),
                                    'title': product_data.get('title', request.query),
                                    'current_price': amazon_price,
                                    'mock_data': False
                                }
                                logger.info(f"Keepa found product: {product_data.get('title', 'N/A')} - Price: €{amazon_price}")
                    
                    # If search returned products directly (older API format)
                    if not keepa_data and data.get('products'):
                        product_data = data['products'][0]
                        stats = product_data.get('stats', {})
                        current_prices = stats.get('current', [])
                        if current_prices and len(current_prices) > 0 and current_prices[0] is not None and current_prices[0] > 0:
                            amazon_price = current_prices[0] / 100.0
                        keepa_data = {
                            'asin': product_data.get('asin', ''),
                            'title': product_data.get('title', request.query),
                            'current_price': amazon_price,
                            'mock_data': False
                        }
        except Exception as e:
            logger.warning(f"Keepa API error: {e}")
    
    # If no real Keepa data, generate mock Amazon reference price
    if not keepa_data:
        keepa_data = generate_amazon_reference_price(request.query, category)
        amazon_price = keepa_data['current_price']
    
    # If Google API keys are configured, use real search
    if google_key and search_engine_id:
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": google_key,
                        "cx": search_engine_id,
                        "q": request.query,
                        "searchType": "image" if request.search_type == "image" else None,
                        "num": 5
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    # Process real search results...
                    pass
        except Exception as e:
            logger.warning(f"Google Search API error: {e}")
    
    # Generate comparisons with category filtering and Amazon-based margins
    comparisons = generate_mock_comparisons(request.query, suppliers, category, amazon_price)
    prices = [c.total_price for c in comparisons]
    
    # Count matching user suppliers
    matching_suppliers = [c for c in comparisons if c.is_user_supplier]
    
    # Save to search history
    history_doc = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'query': request.query,
        'search_type': 'text',
        'category': category,
        'results_count': len(comparisons),
        'lowest_price': min(prices) if prices else None,
        'amazon_price': amazon_price,
        'matching_suppliers_count': len(matching_suppliers),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.search_history.insert_one(history_doc)
    
    return SearchResult(
        product_name=request.query,
        image_url=f"https://via.placeholder.com/300x300?text={request.query.replace(' ', '+')}",
        detected_labels=[request.query, category, "product"],
        comparisons=comparisons,
        lowest_price=min(prices) if prices else None,
        highest_price=max(prices) if prices else None,
        average_price=round(sum(prices) / len(prices), 2) if prices else None,
        category=category,
        amazon_reference_price=amazon_price,
        keepa_data=keepa_data
    )

@api_router.post("/search/image", response_model=SearchResult)
async def search_by_image(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Search products by image upload"""
    api_keys = user.get('api_keys', {})
    google_key = api_keys.get('google_api_key')
    
    # Read image content
    content = await file.read()
    image_base64 = base64.b64encode(content).decode('utf-8')
    
    detected_labels = ["Product", "Item", "Object"]
    product_name = "Detected Product"
    
    # If Google Vision API key is configured, use real detection
    if google_key:
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    f"https://vision.googleapis.com/v1/images:annotate?key={google_key}",
                    json={
                        "requests": [{
                            "image": {"content": image_base64},
                            "features": [
                                {"type": "LABEL_DETECTION", "maxResults": 10},
                                {"type": "WEB_DETECTION", "maxResults": 5},
                                {"type": "OBJECT_LOCALIZATION", "maxResults": 5}
                            ]
                        }]
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    responses = data.get('responses', [{}])[0]
                    
                    # Extract labels
                    labels = responses.get('labelAnnotations', [])
                    detected_labels = [lbl.get('description', '') for lbl in labels[:5]]
                    
                    # Extract web entities for product name
                    web_detection = responses.get('webDetection', {})
                    web_entities = web_detection.get('webEntities', [])
                    if web_entities:
                        product_name = web_entities[0].get('description', 'Detected Product')
        except Exception as e:
            logger.warning(f"Google Vision API error: {e}")
    
    # Auto-detect category
    category = detect_category(product_name)
    
    # Get user's suppliers
    suppliers = await db.suppliers.find({'user_id': user['id']}, {'_id': 0}).to_list(100)
    
    # Get Amazon reference price
    keepa_data = generate_amazon_reference_price(product_name, category)
    amazon_price = keepa_data['current_price']
    
    # Generate comparisons with category filtering and Amazon-based margins
    comparisons = generate_mock_comparisons(product_name, suppliers, category, amazon_price)
    prices = [c.total_price for c in comparisons]
    
    # Save to search history
    history_doc = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'query': product_name,
        'search_type': 'image',
        'category': category,
        'results_count': len(comparisons),
        'lowest_price': min(prices) if prices else None,
        'amazon_price': amazon_price,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.search_history.insert_one(history_doc)
    
    return SearchResult(
        product_name=product_name,
        image_url=f"data:image/{file.content_type.split('/')[-1]};base64,{image_base64[:100]}...",
        detected_labels=detected_labels,
        comparisons=comparisons,
        lowest_price=min(prices) if prices else None,
        highest_price=max(prices) if prices else None,
        average_price=round(sum(prices) / len(prices), 2) if prices else None,
        category=category,
        amazon_reference_price=amazon_price,
        keepa_data=keepa_data
    )

# ==================== PRICE HISTORY ROUTES ====================

@api_router.get("/history/searches")
async def get_search_history(user: dict = Depends(get_current_user), limit: int = 50):
    """Get user's search history"""
    history = await db.search_history.find(
        {'user_id': user['id']}, 
        {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    return history

@api_router.get("/history/price/{product_id}")
async def get_price_history(product_id: str, user: dict = Depends(get_current_user)):
    """Get price history for a product (mock data for demo)"""
    # Generate mock price history
    history = []
    base_price = random.uniform(50, 150)
    
    for i in range(30):
        date = datetime.now(timezone.utc) - timedelta(days=30-i)
        variation = random.uniform(0.9, 1.1)
        price = round(base_price * variation, 2)
        history.append({
            'date': date.isoformat(),
            'price': price,
            'supplier': random.choice(['Amazon', 'eBay', 'AliExpress'])
        })
    
    return {'product_id': product_id, 'history': history}

# ==================== KEEPA INTEGRATION ====================

@api_router.get("/keepa/product/{asin}")
async def get_keepa_product(asin: str, user: dict = Depends(get_current_user)):
    """Get product data from Keepa API"""
    api_keys = user.get('api_keys', {})
    keepa_key = api_keys.get('keepa_api_key')
    
    if not keepa_key:
        # Return mock data if no API key
        return {
            'asin': asin,
            'title': f'Product {asin}',
            'current_price': round(random.uniform(20, 200), 2),
            'price_history': [
                {'date': (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(), 'price': round(random.uniform(20, 200), 2)}
                for i in range(30)
            ],
            'mock_data': True
        }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.keepa.com/product",
                params={
                    "key": keepa_key,
                    "domain": 1,  # Amazon.com
                    "asin": asin,
                    "history": 1
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Keepa API error")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Keepa API timeout")
    except Exception as e:
        logger.error(f"Keepa API error: {e}")
        raise HTTPException(status_code=500, detail="Keepa API error")

# ==================== CATALOG ENDPOINTS ====================

@api_router.post("/catalog/import")
async def import_catalog(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Import product catalog from Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    try:
        # Read Excel file
        contents = await file.read()
        
        # Try different header row positions to find the correct structure
        df = None
        for header_row in range(20):  # Try up to 20 rows for header detection
            try:
                temp_df = pd.read_excel(io.BytesIO(contents), header=header_row)
                # Check if this looks like the right header row
                col_str = ' '.join(str(col) for col in temp_df.columns)
                if len(temp_df.columns) > 3 and ('GTIN' in col_str or 'EAN' in col_str):
                    df = temp_df
                    break
                # Check if any of the first few rows contain the headers
                for row_idx in range(min(5, len(temp_df))):
                    row_vals = temp_df.iloc[row_idx]
                    row_str = ' '.join(str(v) for v in row_vals.values if pd.notna(v))
                    if 'GTIN' in row_str or 'EAN' in row_str:
                        # Use this row as headers
                        new_columns = [str(val) if pd.notna(val) else f'Unnamed_{i}' for i, val in enumerate(row_vals.values)]
                        df = temp_df.iloc[row_idx + 1:].copy()
                        df.columns = new_columns
                        break
                if df is not None:
                    break
            except Exception:
                continue
        
        if df is None:
            raise HTTPException(status_code=400, detail="Impossible de trouver les colonnes GTIN/EAN dans le fichier. Vérifiez que le fichier contient bien des colonnes GTIN, Name, Category, Brand et un prix.")
        
        # Clean up column names and find required columns
        df.columns = [str(col).strip() for col in df.columns]
        
        # Map possible column variations
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'gtin' in col_lower or 'ean' in col_lower or 'barcode' in col_lower:
                column_mapping['GTIN'] = col
            elif 'name' in col_lower and 'brand' not in col_lower and 'file' not in col_lower:
                column_mapping['Name'] = col
            elif 'category' in col_lower or 'catégorie' in col_lower:
                column_mapping['Category'] = col
            elif 'brand' in col_lower or 'marque' in col_lower:
                column_mapping['Brand'] = col
            elif 'Price' not in column_mapping and ('price' in col_lower or 'prix' in col_lower or 'lowest' in col_lower or '£' in col or '€' in col):
                column_mapping['Price'] = col
        
        # Validate required columns exist
        required_fields = ['GTIN', 'Name', 'Category', 'Brand', 'Price']
        missing_fields = [field for field in required_fields if field not in column_mapping]
        if missing_fields:
            available_cols = list(df.columns)
            raise HTTPException(
                status_code=400,
                detail=f"Colonnes manquantes : {', '.join(missing_fields)}. Colonnes disponibles : {', '.join(available_cols)}"
            )
        
        # Get exchange rate
        exchange_rate = await get_exchange_rate()
        
        # Process products
        products = []
        imported_count = 0
        skipped_count = 0
        
        for _, row in df.iterrows():
            try:
                gtin = str(row[column_mapping['GTIN']])
                
                # Skip rows with invalid GTIN
                if pd.isna(row[column_mapping['GTIN']]) or gtin == 'nan' or len(gtin) < 8:
                    skipped_count += 1
                    continue
                
                # Check if product already exists for this user
                existing = await db.catalog_products.find_one({
                    'user_id': user['id'],
                    'gtin': gtin
                })
                
                if existing:
                    skipped_count += 1
                    continue
                
                raw_price = row[column_mapping['Price']]
                if pd.isna(raw_price) or str(raw_price).strip() == '':
                    skipped_count += 1
                    continue
                try:
                    price_gbp = float(raw_price)
                except (ValueError, TypeError):
                    skipped_count += 1
                    continue
                if price_gbp <= 0:
                    skipped_count += 1
                    continue
                price_eur = round(price_gbp * exchange_rate, 2)
                
                # Get additional fields with defaults
                inventory = str(row.get(column_mapping.get('Inventory', 'Lowest Priced Offer Inventory'), 'Unknown'))
                if pd.isna(inventory) or inventory == 'nan':
                    inventory = 'Unknown'
                
                num_offers = row.get(column_mapping.get('Offers', 'Number of Offers'), 0)
                if pd.isna(num_offers):
                    num_offers = 0
                else:
                    num_offers = int(num_offers)
                
                product_link = row.get(column_mapping.get('Link', 'Product Link'), '')
                if pd.isna(product_link):
                    product_link = None
                else:
                    product_link = str(product_link)
                
                product = {
                    'id': str(uuid.uuid4()),
                    'user_id': user['id'],
                    'gtin': gtin,
                    'name': str(row[column_mapping['Name']]),
                    'category': str(row[column_mapping['Category']]),
                    'brand': str(row[column_mapping['Brand']]),
                    'supplier_price_gbp': price_gbp,
                    'supplier_price_eur': price_eur,
                    'inventory': inventory,
                    'number_of_offers': num_offers,
                    'product_link': product_link,
                    'amazon_price_eur': None,
                    'google_price_eur': None,
                    'best_price_eur': None,
                    'margin_eur': None,
                    'margin_percentage': None,
                    'last_compared_at': None,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                products.append(product)
                imported_count += 1
                
            except Exception as e:
                logger.warning(f"Error processing row: {e}")
                skipped_count += 1
                continue
        
        # Bulk insert products
        if products:
            await db.catalog_products.insert_many(products)
        
        return {
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'total': len(df),
            'exchange_rate': exchange_rate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Catalog import error: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import : {str(e)}")

@api_router.get("/catalog/products")
async def get_catalog_products(
    user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    min_margin: Optional[float] = None,
    search: Optional[str] = None,
    compared_only: bool = False
):
    """Get catalog products with filters"""
    query = {'user_id': user['id']}
    
    if brand:
        query['brand'] = brand
    if category:
        query['category'] = category
    if min_margin is not None:
        query['margin_percentage'] = {'$gte': min_margin}
    if compared_only:
        query['last_compared_at'] = {'$ne': None}
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'gtin': {'$regex': search, '$options': 'i'}}
        ]
    
    total = await db.catalog_products.count_documents(query)
    products = await db.catalog_products.find(
        query,
        {'_id': 0}
    ).sort('created_at', -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        'products': products,
        'total': total,
        'skip': skip,
        'limit': limit
    }

@api_router.get("/catalog/stats")
async def get_catalog_stats(user: dict = Depends(get_current_user)):
    """Get catalog statistics"""
    total_products = await db.catalog_products.count_documents({'user_id': user['id']})
    compared_products = await db.catalog_products.count_documents({
        'user_id': user['id'],
        'last_compared_at': {'$ne': None}
    })
    
    # Calculate margins using new fields
    products_with_margin = await db.catalog_products.find({
        'user_id': user['id'],
        'amazon_margin_eur': {'$ne': None}
    }, {'_id': 0, 'amazon_margin_eur': 1, 'amazon_margin_percentage': 1, 
        'supplier_margin_eur': 1, 'supplier_margin_percentage': 1,
        'margin_eur': 1, 'margin_percentage': 1}).to_list(None)
    
    total_margin = sum(p.get('amazon_margin_eur', p.get('margin_eur', 0)) for p in products_with_margin)
    margins_pct = [p.get('amazon_margin_percentage', p.get('margin_percentage', 0)) for p in products_with_margin]
    avg_margin_percentage = sum(margins_pct) / len(margins_pct) if margins_pct else 0
    best_margin = max((p.get('amazon_margin_eur', p.get('margin_eur', 0)) for p in products_with_margin), default=0)
    
    # Count profitable products
    profitable_products = sum(1 for p in products_with_margin if p.get('amazon_margin_eur', p.get('margin_eur', 0)) > 0)
    
    # Get brands and categories
    brands = await db.catalog_products.distinct('brand', {'user_id': user['id']})
    categories = await db.catalog_products.distinct('category', {'user_id': user['id']})
    
    return {
        'total_products': total_products,
        'compared_products': compared_products,
        'profitable_products': profitable_products,
        'total_potential_margin': round(total_margin, 2),
        'avg_margin_percentage': round(avg_margin_percentage, 2),
        'best_opportunity_margin': round(best_margin, 2),
        'amazon_fee_percentage': AMAZON_FEE_PERCENTAGE * 100,
        'brands': sorted(brands),
        'categories': sorted(categories)
    }

def generate_mock_catalog_prices(product: dict) -> dict:
    """Generate realistic mock prices for catalog comparison when no API keys are set.
    
    Logic:
    - Amazon price: typically 2x-3.5x the supplier price (retail markup)
    - Google lowest price: somewhere between supplier and Amazon (varies)
    """
    supplier_price = product['supplier_price_eur']
    
    # Use product GTIN hash for consistent pricing
    hash_val = sum(ord(c) for c in str(product.get('gtin', '')))
    random.seed(hash_val)
    
    # Amazon price: 1.8x to 3.5x supplier price (retail markup)
    amazon_multiplier = random.uniform(1.8, 3.5)
    amazon_price = round(supplier_price * amazon_multiplier, 2)
    
    # Google lowest price: between 0.7x and 1.1x Amazon price
    # Sometimes cheaper, sometimes similar to Amazon
    google_multiplier = random.uniform(0.70, 1.10)
    google_lowest_price = round(amazon_price * google_multiplier, 2)
    
    random.seed()  # Reset seed
    
    return {
        'amazon_price': amazon_price,
        'google_lowest_price': google_lowest_price,
        'is_mock': True
    }


def extract_price_from_text(text: str) -> Optional[float]:
    """Extract price from text string (supports €, EUR formats)"""
    # Match patterns like: 29,99€, 29.99€, €29.99, 29,99 EUR, etc.
    patterns = [
        r'(\d+[.,]\d{2})\s*€',
        r'€\s*(\d+[.,]\d{2})',
        r'(\d+[.,]\d{2})\s*EUR',
        r'EUR\s*(\d+[.,]\d{2})',
        r'(\d+[.,]\d{2})\s*eur',
    ]
    
    prices = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                price = float(match.replace(',', '.'))
                if 0.01 < price < 100000:  # Sanity check
                    prices.append(price)
            except ValueError:
                continue
    
    return min(prices) if prices else None


@api_router.post("/catalog/compare/{product_id}")
async def compare_catalog_product(
    product_id: str,
    user: dict = Depends(get_current_user)
):
    """Compare a single catalog product: Keepa (Amazon) + Google (lowest price online).
    
    Calculates:
    - Amazon price (selling price via Keepa)
    - Google lowest price (cheapest online)
    - Cheapest source between supplier and Google
    - Amazon margin = Amazon price - buy price - Amazon fees (15% TTC)
    """
    product = await db.catalog_products.find_one({
        'id': product_id,
        'user_id': user['id']
    }, {'_id': 0})
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get API keys
    user_doc = await db.users.find_one({'id': user['id']}, {'_id': 0})
    api_keys = user_doc.get('api_keys', {})
    keepa_key = api_keys.get('keepa_api_key')
    google_key = api_keys.get('google_api_key')
    google_cx = api_keys.get('google_search_engine_id')
    
    supplier_price = product['supplier_price_eur']
    amazon_price = None
    google_lowest_price = None
    is_mock_data = False
    
    # ==================== KEEPA API (Amazon price) ====================
    if keepa_key:
        try:
            async with httpx.AsyncClient() as http_client:
                # Step 1: Try /product endpoint with code parameter for EAN/GTIN lookup
                response = await http_client.get(
                    "https://api.keepa.com/product",
                    params={
                        "key": keepa_key,
                        "domain": 4,  # Amazon.fr
                        "code": product['gtin'],
                        "stats": 1,  # Include stats with current prices
                    },
                    timeout=30
                )
                logger.info(f"Keepa API response status for {product['gtin']}: {response.status_code}")
                
                keepa_product = None
                if response.status_code == 200:
                    data = response.json()
                    products_found = data.get('products', [])
                    if products_found and len(products_found) > 0:
                        keepa_product = products_found[0]
                        logger.info(f"Keepa found ASIN via GTIN: {keepa_product.get('asin', 'N/A')} for {product['name']}")
                    else:
                        logger.info(f"Keepa: no products found for EAN {product['gtin']}, trying search by name...")
                
                # Step 2: If no product found by GTIN, try search by product name
                if keepa_product is None:
                    search_term = f"{product['brand']} {product['name']}"
                    logger.info(f"Keepa: searching by name: {search_term}")
                    
                    search_response = await http_client.get(
                        "https://api.keepa.com/search",
                        params={
                            "key": keepa_key,
                            "domain": 4,  # Amazon.fr
                            "type": "product",
                            "term": search_term
                        },
                        timeout=30
                    )
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        asin_list = search_data.get('asinList', [])
                        
                        if asin_list and len(asin_list) > 0:
                            # Get product details for the first ASIN found
                            detail_response = await http_client.get(
                                "https://api.keepa.com/product",
                                params={
                                    "key": keepa_key,
                                    "domain": 4,
                                    "asin": asin_list[0],
                                    "stats": 1,
                                },
                                timeout=30
                            )
                            if detail_response.status_code == 200:
                                detail_data = detail_response.json()
                                if detail_data.get('products') and len(detail_data['products']) > 0:
                                    keepa_product = detail_data['products'][0]
                                    logger.info(f"Keepa found ASIN via name search: {keepa_product.get('asin', 'N/A')} for {product['name']}")
                        else:
                            logger.info(f"Keepa: no products found by name search for {search_term}")
                    else:
                        logger.warning(f"Keepa search API HTTP {search_response.status_code}: {search_response.text[:200]}")
                
                # Step 3: Extract price from found product
                if keepa_product:
                    # Method 1: Try stats.current array
                    # Index 0 = Amazon price, Index 1 = New 3rd party, Index 2 = Used
                    # Keepa prices are in cents, -1 means no data
                    stats = keepa_product.get('stats', {})
                    current_prices = stats.get('current', [])
                    
                    if current_prices and len(current_prices) > 0:
                        # Try Amazon price first (index 0)
                        if current_prices[0] is not None and current_prices[0] > 0:
                            amazon_price = current_prices[0] / 100.0
                        # Fallback to 3rd party new price (index 1)
                        elif len(current_prices) > 1 and current_prices[1] is not None and current_prices[1] > 0:
                            amazon_price = current_prices[1] / 100.0
                    
                    # Method 2: If stats.current didn't work, try csv price history
                    # csv[0] = Amazon price history, csv[1] = New 3rd party history
                    if amazon_price is None:
                        csv_data = keepa_product.get('csv', [])
                        # Try Amazon csv (index 0) - get last valid price
                        if csv_data and len(csv_data) > 0 and csv_data[0]:
                            prices_array = csv_data[0]
                            # csv arrays are [timestamp, price, timestamp, price, ...]
                            # Walk backwards to find the last valid price
                            for i in range(len(prices_array) - 1, 0, -2):
                                if prices_array[i] is not None and prices_array[i] > 0:
                                    amazon_price = prices_array[i] / 100.0
                                    break
                        # Try New 3rd party csv (index 1) if Amazon csv didn't work
                        if amazon_price is None and csv_data and len(csv_data) > 1 and csv_data[1]:
                            prices_array = csv_data[1]
                            for i in range(len(prices_array) - 1, 0, -2):
                                if prices_array[i] is not None and prices_array[i] > 0:
                                    amazon_price = prices_array[i] / 100.0
                                    break
                    
                    # Method 3: Try buyBoxPrice from stats
                    if amazon_price is None:
                        buy_box = stats.get('buyBoxPrice', -1)
                        if buy_box is not None and buy_box > 0:
                            amazon_price = buy_box / 100.0
                    
                    logger.info(f"Keepa final Amazon price for {product['name']}: €{amazon_price}")
                else:
                    logger.info(f"Keepa: no products found for {product['name']} (neither by GTIN nor by name)")
                    
        except Exception as e:
            logger.warning(f"Keepa API error for {product['gtin']}: {e}")
    
    # ==================== GOOGLE CUSTOM SEARCH (lowest price online) ====================
    if google_key and google_cx:
        try:
            search_query = f"{product['brand']} {product['name']} prix"
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": google_key,
                        "cx": google_cx,
                        "q": search_query,
                        "num": 10
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    found_prices = []
                    
                    for item in items:
                        # Try to extract price from snippet
                        snippet = item.get('snippet', '')
                        title = item.get('title', '')
                        
                        # Check pagemap for structured pricing data
                        pagemap = item.get('pagemap', {})
                        offers = pagemap.get('offer', [])
                        for offer in offers:
                            price_str = offer.get('price', '')
                            try:
                                price = float(price_str.replace(',', '.'))
                                if 0.01 < price < 100000:
                                    found_prices.append(price)
                            except (ValueError, AttributeError):
                                pass
                        
                        # Try product structured data
                        products_data = pagemap.get('product', [])
                        for prod in products_data:
                            price_str = prod.get('price', '')
                            try:
                                price = float(price_str.replace(',', '.'))
                                if 0.01 < price < 100000:
                                    found_prices.append(price)
                            except (ValueError, AttributeError):
                                pass
                        
                        # Extract from snippet text
                        snippet_price = extract_price_from_text(snippet)
                        if snippet_price:
                            found_prices.append(snippet_price)
                        
                        title_price = extract_price_from_text(title)
                        if title_price:
                            found_prices.append(title_price)
                    
                    if found_prices:
                        google_lowest_price = min(found_prices)
                        logger.info(f"Google lowest price for {product['name']}: €{google_lowest_price} (from {len(found_prices)} prices found)")
        except Exception as e:
            logger.warning(f"Google API error for {product['name']}: {e}")
    
    # ==================== MOCK DATA FALLBACK ====================
    has_api_keys = bool(keepa_key) or bool(google_key and google_cx)
    
    if amazon_price is None and google_lowest_price is None and not has_api_keys:
        # No API keys configured at all → use mock data for demo
        mock_prices = generate_mock_catalog_prices(product)
        amazon_price = mock_prices['amazon_price']
        google_lowest_price = mock_prices['google_lowest_price']
        is_mock_data = True
        logger.info(f"Using mock prices for {product['name']} (no API keys): Amazon=€{amazon_price}, Google=€{google_lowest_price}")
    elif amazon_price is None and google_lowest_price is None and has_api_keys:
        # API keys configured but no prices found → product not found on APIs
        is_mock_data = False
        logger.info(f"No prices found via APIs for {product['name']} (GTIN: {product['gtin']})")
    else:
        is_mock_data = False
    
    # ==================== CALCULATE COMPARISONS ====================
    
    # Amazon fees (15% TTC) - only if amazon price is available
    amazon_fees = calculate_amazon_fees(amazon_price) if amazon_price else None
    
    # Cheapest source between supplier and Google
    if google_lowest_price is not None and google_lowest_price <= supplier_price:
        cheapest_source = "google"
        cheapest_buy_price = google_lowest_price
    else:
        cheapest_source = "supplier"
        cheapest_buy_price = supplier_price
    
    # Margin if buying from SUPPLIER and selling on Amazon
    supplier_margin = calculate_margin(amazon_price, supplier_price, amazon_fees) if amazon_price else {'margin_eur': None, 'margin_percentage': None}
    
    # Margin if buying from GOOGLE and selling on Amazon
    google_margin = calculate_margin(amazon_price, google_lowest_price, amazon_fees) if (amazon_price and google_lowest_price) else {'margin_eur': None, 'margin_percentage': None}
    
    # Best margin (from cheapest source)
    best_margin = calculate_margin(amazon_price, cheapest_buy_price, amazon_fees) if amazon_price else {'margin_eur': None, 'margin_percentage': None}
    
    # Price differences
    google_vs_amazon_diff = round(google_lowest_price - amazon_price, 2) if (google_lowest_price and amazon_price) else None
    supplier_vs_google_diff = round(supplier_price - google_lowest_price, 2) if google_lowest_price else None
    
    # Update product in database with all comparison data
    update_data = {
        'amazon_price_eur': amazon_price,
        'google_lowest_price_eur': google_lowest_price,
        'cheapest_source': cheapest_source,
        'cheapest_buy_price_eur': cheapest_buy_price,
        'amazon_fees_eur': amazon_fees,
        'amazon_margin_eur': best_margin['margin_eur'],
        'amazon_margin_percentage': best_margin['margin_percentage'],
        'supplier_margin_eur': supplier_margin['margin_eur'],
        'supplier_margin_percentage': supplier_margin['margin_percentage'],
        'google_margin_eur': google_margin['margin_eur'],
        'google_margin_percentage': google_margin['margin_percentage'],
        'google_vs_amazon_diff_eur': google_vs_amazon_diff,
        'supplier_vs_google_diff_eur': supplier_vs_google_diff,
        # Legacy fields
        'google_price_eur': google_lowest_price,
        'best_price_eur': cheapest_buy_price,
        'margin_eur': best_margin['margin_eur'],
        'margin_percentage': best_margin['margin_percentage'],
        'last_compared_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.catalog_products.update_one(
        {'id': product_id},
        {'$set': update_data}
    )
    
    return {
        'product_id': product_id,
        'product_name': product['name'],
        'gtin': product['gtin'],
        'brand': product['brand'],
        'is_mock_data': is_mock_data,
        # Prices
        'supplier_price_eur': supplier_price,
        'amazon_price_eur': amazon_price,
        'google_lowest_price_eur': google_lowest_price,
        # Comparison
        'cheapest_source': cheapest_source,
        'cheapest_buy_price_eur': cheapest_buy_price,
        'amazon_fees_eur': amazon_fees,
        'amazon_fee_percentage': AMAZON_FEE_PERCENTAGE * 100,
        # Margins
        'supplier_margin_eur': supplier_margin['margin_eur'],
        'supplier_margin_percentage': supplier_margin['margin_percentage'],
        'google_margin_eur': google_margin['margin_eur'],
        'google_margin_percentage': google_margin['margin_percentage'],
        'best_margin_eur': best_margin['margin_eur'],
        'best_margin_percentage': best_margin['margin_percentage'],
        # Differences
        'google_vs_amazon_diff_eur': google_vs_amazon_diff,
        'supplier_vs_google_diff_eur': supplier_vs_google_diff,
        'compared_at': datetime.now(timezone.utc).isoformat()
    }

@api_router.post("/catalog/compare-batch")
async def compare_batch(
    product_ids: List[str],
    user: dict = Depends(get_current_user)
):
    """Compare multiple products in batch"""
    results = []
    errors = []
    
    for product_id in product_ids:
        try:
            result = await compare_catalog_product(product_id, user)
            results.append(result)
        except Exception as e:
            errors.append({'product_id': product_id, 'error': str(e)})
    
    return {
        'success': len(results),
        'failed': len(errors),
        'results': results,
        'errors': errors
    }

@api_router.post("/catalog/compare-all")
async def compare_all_products(
    user: dict = Depends(get_current_user)
):
    """Compare ALL products in the catalog for the current user"""
    # Fetch all product IDs for this user
    all_products = await db.catalog_products.find(
        {'user_id': user['id']},
        {'id': 1, '_id': 0}
    ).to_list(10000)
    
    if not all_products:
        raise HTTPException(status_code=404, detail="Aucun produit dans le catalogue")
    
    product_ids = [p['id'] for p in all_products]
    total = len(product_ids)
    
    results = []
    errors = []
    
    for product_id in product_ids:
        try:
            result = await compare_catalog_product(product_id, user)
            results.append(result)
        except Exception as e:
            errors.append({'product_id': product_id, 'error': str(e)})
    
    return {
        'total': total,
        'success': len(results),
        'failed': len(errors),
        'results': results,
        'errors': errors
    }

@api_router.get("/catalog/opportunities")
async def get_opportunities(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    min_margin_percentage: float = 0
):
    """Get best reselling opportunities sorted by Amazon margin"""
    # Try new field first, fallback to legacy
    products = await db.catalog_products.find({
        'user_id': user['id'],
        '$or': [
            {'amazon_margin_percentage': {'$gte': min_margin_percentage}},
            {'margin_percentage': {'$gte': min_margin_percentage}}
        ],
        '$and': [
            {'$or': [
                {'amazon_margin_eur': {'$ne': None}},
                {'margin_eur': {'$ne': None}}
            ]}
        ]
    }, {'_id': 0}).sort('amazon_margin_eur', -1).limit(limit).to_list(limit)
    
    return {
        'opportunities': products,
        'total': len(products),
        'amazon_fee_percentage': AMAZON_FEE_PERCENTAGE * 100
    }

@api_router.delete("/catalog/products/{product_id}")
async def delete_catalog_product(
    product_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a catalog product"""
    result = await db.catalog_products.delete_one({
        'id': product_id,
        'user_id': user['id']
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {'success': True, 'message': 'Product deleted'}

@api_router.delete("/catalog/products")
async def delete_all_catalog_products(user: dict = Depends(get_current_user)):
    """Delete all catalog products for the current user"""
    result = await db.catalog_products.delete_many({'user_id': user['id']})
    return {'success': True, 'deleted': result.deleted_count}

@api_router.get("/catalog/export")
async def export_catalog(
    user: dict = Depends(get_current_user),
    compared_only: bool = False
):
    """Export catalog to Excel file"""
    query = {'user_id': user['id']}
    if compared_only:
        query['last_compared_at'] = {'$ne': None}
    
    products = await db.catalog_products.find(query, {'_id': 0}).to_list(None)
    
    if not products:
        raise HTTPException(status_code=404, detail="No products to export")
    
    # Create Excel file in memory
    output = io.BytesIO()
    df = pd.DataFrame(products)
    
    # Reorder and rename columns for better readability
    column_order = [
        'gtin', 'name', 'brand', 'category',
        'supplier_price_gbp', 'supplier_price_eur',
        'amazon_price_eur', 'google_lowest_price_eur',
        'cheapest_source', 'cheapest_buy_price_eur',
        'amazon_fees_eur',
        'amazon_margin_eur', 'amazon_margin_percentage',
        'supplier_margin_eur', 'supplier_margin_percentage',
        'google_margin_eur', 'google_margin_percentage',
        'google_vs_amazon_diff_eur', 'supplier_vs_google_diff_eur',
        'inventory', 'number_of_offers', 'product_link',
        'last_compared_at', 'created_at'
    ]
    
    df = df[[col for col in column_order if col in df.columns]]
    
    # Rename columns to French
    column_names = {
        'gtin': 'Code EAN',
        'name': 'Nom du produit',
        'brand': 'Marque',
        'category': 'Catégorie',
        'supplier_price_gbp': 'Prix fournisseur (£)',
        'supplier_price_eur': 'Prix fournisseur (€)',
        'amazon_price_eur': 'Prix Amazon (€)',
        'google_lowest_price_eur': 'Prix Google le + bas (€)',
        'cheapest_source': 'Source la - chère',
        'cheapest_buy_price_eur': "Prix d'achat le + bas (€)",
        'amazon_fees_eur': 'Frais Amazon 15% (€)',
        'amazon_margin_eur': 'Marge nette Amazon (€)',
        'amazon_margin_percentage': 'Marge nette Amazon (%)',
        'supplier_margin_eur': 'Marge via fournisseur (€)',
        'supplier_margin_percentage': 'Marge via fournisseur (%)',
        'google_margin_eur': 'Marge via Google (€)',
        'google_margin_percentage': 'Marge via Google (%)',
        'google_vs_amazon_diff_eur': 'Diff Google vs Amazon (€)',
        'supplier_vs_google_diff_eur': 'Diff Fournisseur vs Google (€)',
        'inventory': 'Stock',
        'number_of_offers': "Nombre d'offres",
        'product_link': 'Lien produit',
        'last_compared_at': 'Dernière comparaison',
        'created_at': 'Date création'
    }
    
    df = df.rename(columns={k: v for k, v in column_names.items() if k in df.columns})
    
    df.to_excel(output, index=False, engine='xlsxwriter')
    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="catalogue_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    }
    
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )

# ==================== DASHBOARD STATS ====================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    suppliers_count = await db.suppliers.count_documents({'user_id': user['id']})
    alerts_count = await db.alerts.count_documents({'user_id': user['id'], 'is_active': True})
    favorites_count = await db.favorites.count_documents({'user_id': user['id']})
    searches_count = await db.search_history.count_documents({'user_id': user['id']})
    
    # Get recent searches
    recent_searches = await db.search_history.find(
        {'user_id': user['id']},
        {'_id': 0}
    ).sort('created_at', -1).limit(5).to_list(5)
    
    return {
        'suppliers_count': suppliers_count,
        'active_alerts_count': alerts_count,
        'favorites_count': favorites_count,
        'total_searches': searches_count,
        'recent_searches': recent_searches
    }

# ==================== ROOT & HEALTH ====================

@api_router.get("/")
async def root():
    return {"message": "Resell Corner API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
