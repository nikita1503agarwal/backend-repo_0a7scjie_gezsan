import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from database import create_document, get_documents, db

app = FastAPI(title="Meer Shoes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Meer Shoes backend is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from Meer Shoes API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# -------------------------------------------------
# Products Endpoints for "Meer Shoes" (Nike shoes)
# -------------------------------------------------

NIKE_SEED = [
    {
        "title": "Nike Air Max 270",
        "description": "Breathable mesh upper with a large Air unit for all‑day comfort.",
        "price": 149.99,
        "category": "Sneakers",
        "brand": "Nike",
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=1600&q=80&auto=format&fit=crop"
        ],
        "colors": ["Black", "White", "Volt"],
        "rating": {"average": 4.7, "count": 324}
    },
    {
        "title": "Nike Air Force 1 '07",
        "description": "The classic AF1—legendary style with crisp leather and durable cushioning.",
        "price": 109.99,
        "category": "Lifestyle",
        "brand": "Nike",
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1543508282-6319a3e2621f?w=1600&q=80&auto=format&fit=crop"
        ],
        "colors": ["White", "Black"],
        "rating": {"average": 4.8, "count": 512}
    },
    {
        "title": "Nike Pegasus 40",
        "description": "Daily trainer built for smooth transitions and dependable cushioning.",
        "price": 129.99,
        "category": "Running",
        "brand": "Nike",
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=1600&q=80&auto=format&fit=crop"
        ],
        "colors": ["Blue", "Grey"],
        "rating": {"average": 4.6, "count": 210}
    }
]

COLLECTION = "product"  # based on Product schema class name lowercased

@app.post("/api/products/seed")
def seed_products():
    """Seed a few Nike shoes if they don't exist yet."""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    created = 0
    for item in NIKE_SEED:
        existing = list(db[COLLECTION].find({"title": item["title"]}).limit(1))
        if not existing:
            create_document(COLLECTION, item)
            created += 1
    return {"message": "Seed complete", "created": created}

@app.get("/api/products")
def list_products(brand: Optional[str] = None, q: Optional[str] = None):
    """List products. Filter by brand or search query in title/description."""
    filter_q = {}
    if brand:
        filter_q["brand"] = brand
    if q:
        # simple contains search
        filter_q["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    docs = get_documents(COLLECTION, filter_q)
    # Convert ObjectId to string
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return {"items": docs}

@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    from bson import ObjectId
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        doc = db[COLLECTION].find_one({"_id": ObjectId(product_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Product not found")
        doc["id"] = str(doc.pop("_id"))
        return doc
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
