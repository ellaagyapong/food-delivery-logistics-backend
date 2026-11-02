from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import auth, restaurants, products, cart, orders, payments, delivery, resources

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Food Delivery & Logistics Platform API", version="1.0.0",
              description="JWT-authenticated multi-entity food delivery backend. See README for setup and API workflow.")
origins = [x.strip() for x in __import__("app.config", fromlist=["settings"]).settings.cors_origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for router in (auth.router, restaurants.router, products.router, cart.router, orders.router, payments.router, delivery.router, resources.router):
    app.include_router(router)

@app.get("/health", tags=["System"])
def health():
    return {"status":"ok"}
