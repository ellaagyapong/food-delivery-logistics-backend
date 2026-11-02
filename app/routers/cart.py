from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cart, CartItem, Product, ProductVariant, User
from app.schemas import CartItemIn, CartItemPatch, CartOut, CartItemOut
from app.security import get_current_user

router=APIRouter(prefix="/cart",tags=["Cart"])

def get_cart(db,user):
    cart=db.query(Cart).filter(Cart.user_id==user.id).first()
    if not cart:
        cart=Cart(user_id=user.id); db.add(cart); db.commit(); db.refresh(cart)
    return cart

@router.post("/items",response_model=CartItemOut,status_code=201)
def add_item(data:CartItemIn,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    cart=get_cart(db,user); p=db.get(Product,data.product_id)
    if not p or not p.is_available: raise HTTPException(404,"Available product not found")
    if data.variant_id:
        v=db.get(ProductVariant,data.variant_id)
        if not v or v.product_id != p.id: raise HTTPException(400,"Variant does not belong to product")
    item=db.query(CartItem).filter(CartItem.cart_id==cart.id,CartItem.product_id==p.id,CartItem.variant_id==data.variant_id).first()
    if item: item.quantity += data.quantity
    else: item=CartItem(cart_id=cart.id,**data.model_dump()); db.add(item)
    db.commit(); db.refresh(item); return item

@router.get("",response_model=CartOut)
def get_current_cart(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    c=get_cart(db,user)
    return {"id":c.id,"user_id":c.user_id,"items":c.items}

@router.patch("/items/{item_id}",response_model=CartItemOut)
def update_item(item_id:int,data:CartItemPatch,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    c=get_cart(db,user); item=db.get(CartItem,item_id)
    if not item or item.cart_id != c.id: raise HTTPException(404,"Cart item not found")
    item.quantity=data.quantity; db.commit(); db.refresh(item); return item

@router.delete("/items/{item_id}",status_code=204)
def delete_item(item_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    c=get_cart(db,user); item=db.get(CartItem,item_id)
    if not item or item.cart_id != c.id: raise HTTPException(404,"Cart item not found")
    db.delete(item); db.commit(); return None
