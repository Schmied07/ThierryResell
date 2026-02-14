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

def generate_mock_comparisons(product_name: str, suppliers: List[dict]) -> List[PriceComparisonResult]:
    """Generate mock price comparisons for demo purposes"""
    base_price = random.uniform(20, 200)
    comparisons = []
    
    # Default suppliers if user has none
    default_suppliers = [
        {"name": "Amazon", "url": "https://amazon.com"},
        {"name": "eBay", "url": "https://ebay.com"},
        {"name": "AliExpress", "url": "https://aliexpress.com"},
        {"name": "Alibaba", "url": "https://alibaba.com"},
    ]
    
    all_suppliers = suppliers if suppliers else default_suppliers
    
    for supplier in all_suppliers[:5]:
        variation = random.uniform(0.7, 1.3)
        price = round(base_price * variation, 2)
        shipping = round(random.uniform(0, 15), 2) if random.random() > 0.3 else 0
        total = round(price + shipping, 2)
        
        comparisons.append(PriceComparisonResult(
            supplier=supplier.get('name', supplier.get('name')),
            supplier_url=supplier.get('url', ''),
            price=price,
            currency="EUR",
            availability=random.choice(["In Stock", "In Stock", "In Stock", "Low Stock", "Pre-order"]),
            shipping=shipping,
            total_price=total,
            profit_margin=round(random.uniform(-10, 40), 1)
        ))
    
    return sorted(comparisons, key=lambda x: x.total_price)

@api_router.post("/search/text", response_model=SearchResult)
async def search_by_text(request: ProductSearchRequest, user: dict = Depends(get_current_user)):
    """Search products by text query"""
    api_keys = user.get('api_keys', {})
    google_key = api_keys.get('google_api_key')
    search_engine_id = api_keys.get('google_search_engine_id')
    
    # Get user's suppliers
    suppliers = await db.suppliers.find({'user_id': user['id']}, {'_id': 0}).to_list(100)
    
    # If Google API keys are configured, use real search
    if google_key and search_engine_id:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
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
    
    # Generate mock results for demo
    comparisons = generate_mock_comparisons(request.query, suppliers)
    prices = [c.total_price for c in comparisons]
    
    # Save to search history
    history_doc = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'query': request.query,
        'search_type': 'text',
        'results_count': len(comparisons),
        'lowest_price': min(prices) if prices else None,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.search_history.insert_one(history_doc)
    
    return SearchResult(
        product_name=request.query,
        image_url=f"https://via.placeholder.com/300x300?text={request.query.replace(' ', '+')}",
        detected_labels=[request.query, "product", "item"],
        comparisons=comparisons,
        lowest_price=min(prices) if prices else None,
        highest_price=max(prices) if prices else None,
        average_price=round(sum(prices) / len(prices), 2) if prices else None
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
            async with httpx.AsyncClient() as client:
                response = await client.post(
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
                    detected_labels = [l.get('description', '') for l in labels[:5]]
                    
                    # Extract web entities for product name
                    web_detection = responses.get('webDetection', {})
                    web_entities = web_detection.get('webEntities', [])
                    if web_entities:
                        product_name = web_entities[0].get('description', 'Detected Product')
        except Exception as e:
            logger.warning(f"Google Vision API error: {e}")
    
    # Get user's suppliers
    suppliers = await db.suppliers.find({'user_id': user['id']}, {'_id': 0}).to_list(100)
    
    # Generate mock comparisons
    comparisons = generate_mock_comparisons(product_name, suppliers)
    prices = [c.total_price for c in comparisons]
    
    # Save to search history
    history_doc = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'query': product_name,
        'search_type': 'image',
        'results_count': len(comparisons),
        'lowest_price': min(prices) if prices else None,
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
        average_price=round(sum(prices) / len(prices), 2) if prices else None
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
                f"https://api.keepa.com/product",
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
