from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Cart, CartItem, Product, ProductVariant, Order, OrderItem, OrderStatusHistory, Delivery, OrderStatus, DeliveryStatus, Role, User, Address
from app.schemas import OrderCreate, OrderOut, OrderStatusPatch, HistoryOut
from app.security import get_current_user

router=APIRouter(prefix="/orders",tags=["Orders"])
TRANSITIONS={
 OrderStatus.PENDING:{OrderStatus.CONFIRMED,OrderStatus.CANCELLED},
 OrderStatus.CONFIRMED:{OrderStatus.PREPARING,OrderStatus.CANCELLED},
 OrderStatus.PREPARING:{OrderStatus.READY_FOR_PICKUP,OrderStatus.CANCELLED},
 OrderStatus.READY_FOR_PICKUP:{OrderStatus.OUT_FOR_DELIVERY},
 OrderStatus.OUT_FOR_DELIVERY:{OrderStatus.DELIVERED},
 OrderStatus.DELIVERED:set(), OrderStatus.CANCELLED:set()
}

@router.post("",response_model=OrderOut,status_code=201)
def create_order(data:OrderCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    try:
        cart=db.query(Cart).options(joinedload(Cart.items).joinedload(CartItem.product),joinedload(Cart.items).joinedload(CartItem.variant)).filter(Cart.user_id==user.id).first()
        if not cart or not cart.items: raise HTTPException(400,"Cart is empty")
        if data.address_id:
            a=db.get(Address,data.address_id)
            if not a or a.user_id != user.id: raise HTTPException(400,"Address does not belong to current user")
        order=Order(customer_id=user.id,address_id=data.address_id,notes=data.notes,status=OrderStatus.PENDING,total=0)
        db.add(order); db.flush()
        total=0
        for ci in list(cart.items):
            p=ci.product
            if not p or not p.is_available: raise HTTPException(400,f"Product {ci.product_id} is unavailable")
            price=p.price
            if ci.variant:
                if ci.variant.product_id != p.id: raise HTTPException(400,"Invalid product variant")
                price += ci.variant.price_delta
            if price < 0: raise HTTPException(400,"Invalid item price")
            db.add(OrderItem(order_id=order.id,product_id=p.id,product_name=p.name,unit_price=price,quantity=ci.quantity))
            total += price*ci.quantity
        order.total=round(total,2)
        db.add(OrderStatusHistory(order_id=order.id,old_status="NONE",new_status=OrderStatus.PENDING.value,changed_by_id=user.id,note="Order created"))
        db.add(Delivery(order_id=order.id,status=DeliveryStatus.ASSIGNED))
        for ci in list(cart.items): db.delete(ci)
        db.commit(); db.refresh(order)
        return order
    except Exception:
        db.rollback()
        raise

@router.get("",response_model=list[OrderOut])
def list_orders(customer_id:int|None=None,status:OrderStatus|None=None,start_date:str|None=None,end_date:str|None=None,page:int=Query(1,ge=1),limit:int=Query(20,ge=1,le=100),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    q=db.query(Order)
    if user.role==Role.CUSTOMER: q=q.filter(Order.customer_id==user.id)
    elif customer_id: q=q.filter(Order.customer_id==customer_id)
    if status: q=q.filter(Order.status==status)
    if start_date: q=q.filter(Order.created_at>=start_date)
    if end_date: q=q.filter(Order.created_at<=end_date)
    return q.order_by(Order.created_at.desc()).offset((page-1)*limit).limit(limit).all()

@router.get("/{order_id}",response_model=OrderOut)
def get_order(order_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    o=db.get(Order,order_id)
    if not o: raise HTTPException(404,"Order not found")
    if user.role==Role.CUSTOMER and o.customer_id != user.id: raise HTTPException(403,"Not your order")
    return o

@router.patch("/{order_id}/status",response_model=OrderOut)
def update_order_status(order_id:int,data:OrderStatusPatch,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    o=db.get(Order,order_id)
    if not o: raise HTTPException(404,"Order not found")
    if user.role==Role.CUSTOMER: raise HTTPException(403,"Customers cannot update order status")
    if data.status not in TRANSITIONS[o.status]: raise HTTPException(400,f"Invalid transition: {o.status.value} -> {data.status.value}")
    old=o.status; o.status=data.status
    db.add(OrderStatusHistory(order_id=o.id,old_status=old.value,new_status=data.status.value,changed_by_id=user.id,note=data.note))
    db.commit(); db.refresh(o); return o

@router.get("/{order_id}/status-history",response_model=list[HistoryOut])
def order_history(order_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    o=db.get(Order,order_id)
    if not o: raise HTTPException(404,"Order not found")
    if user.role==Role.CUSTOMER and o.customer_id != user.id: raise HTTPException(403,"Not your order")
    return db.query(OrderStatusHistory).filter_by(order_id=order_id).order_by(OrderStatusHistory.created_at).all()
