from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, ProductVariant, Category, Restaurant, Role, User
from app.schemas import ProductIn, ProductOut, CategoryIn, CategoryOut, VariantIn, VariantOut
from app.security import get_current_user

router=APIRouter(tags=["Products & Categories"])

@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(data:ProductIn, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    r=db.get(Restaurant,data.restaurant_id); c=db.get(Category,data.category_id)
    if not r or not c: raise HTTPException(404,"Restaurant or category not found")
    if c.menu.restaurant_id != r.id: raise HTTPException(400,"Category must belong to a menu for the selected restaurant")
    if user.role not in (Role.ADMIN,Role.RESTAURANT_OWNER) or (user.role != Role.ADMIN and r.owner_id != user.id): raise HTTPException(403,"Not allowed to create products for this restaurant")
    obj=Product(**data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.get("/products", response_model=list[ProductOut])
def list_products(search:str|None=None, category_id:int|None=None, restaurant_id:int|None=None, min_price:float|None=Query(None,ge=0), max_price:float|None=Query(None,ge=0), available:bool|None=None, page:int=Query(1,ge=1), limit:int=Query(20,ge=1,le=100), sort_by:str="created_at", order:str="desc", db:Session=Depends(get_db)):
    q=db.query(Product)
    if search: q=q.filter(Product.name.ilike(f"%{search}%"))
    if category_id: q=q.filter(Product.category_id==category_id)
    if restaurant_id: q=q.filter(Product.restaurant_id==restaurant_id)
    if min_price is not None: q=q.filter(Product.price>=min_price)
    if max_price is not None: q=q.filter(Product.price<=max_price)
    if available is not None: q=q.filter(Product.is_available==available)
    col=getattr(Product,sort_by,Product.created_at); q=q.order_by(col.asc() if order.lower()=="asc" else col.desc())
    return q.offset((page-1)*limit).limit(limit).all()

@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id:int, db:Session=Depends(get_db)):
    p=db.get(Product,product_id)
    if not p: raise HTTPException(404,"Product not found")
    return p

@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(data:CategoryIn, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    menu=db.get(__import__("app.models",fromlist=["Menu"]).Menu,data.menu_id)
    if not menu: raise HTTPException(404,"Menu not found")
    if user.role not in (Role.ADMIN,Role.RESTAURANT_OWNER) or (user.role != Role.ADMIN and menu.restaurant.owner_id != user.id): raise HTTPException(403,"Not allowed")
    c=Category(**data.model_dump()); db.add(c); db.commit(); db.refresh(c); return c

@router.get("/categories", response_model=list[CategoryOut])
def list_categories(menu_id:int|None=None, db:Session=Depends(get_db)):
    q=db.query(Category)
    if menu_id: q=q.filter(Category.menu_id==menu_id)
    return q.order_by(Category.name).all()

@router.post("/product-variants", response_model=VariantOut, status_code=201)
def create_variant(data:VariantIn, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    p=db.get(Product,data.product_id)
    if not p: raise HTTPException(404,"Product not found")
    if user.role not in (Role.ADMIN,Role.RESTAURANT_OWNER) or (user.role != Role.ADMIN and p.category.menu.restaurant.owner_id != user.id): raise HTTPException(403,"Not allowed")
    v=ProductVariant(**data.model_dump()); db.add(v); db.commit(); db.refresh(v); return v

@router.get("/product-variants", response_model=list[VariantOut])
def list_variants(product_id:int|None=None, db:Session=Depends(get_db)):
    q=db.query(ProductVariant)
    if product_id: q=q.filter(ProductVariant.product_id==product_id)
    return q.all()
