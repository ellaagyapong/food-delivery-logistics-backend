from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, Payment, PaymentStatus, Refund, Role, User
from app.schemas import PaymentCreate, PaymentOut, RefundIn, RefundOut
from app.security import get_current_user

router=APIRouter(tags=["Payments & Refunds"])

@router.post("/payments",response_model=PaymentOut,status_code=201)
def create_payment(data:PaymentCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    o=db.get(Order,data.order_id)
    if not o: raise HTTPException(404,"Order not found")
    if user.role==Role.CUSTOMER and o.customer_id != user.id: raise HTTPException(403,"Not your order")
    if o.payment: raise HTTPException(409,"Payment already exists for this order")
    p=Payment(order_id=o.id,amount=o.total,status=PaymentStatus.PENDING,provider_reference=data.provider_reference)
    db.add(p); db.commit(); db.refresh(p); return p

@router.get("/payments/{payment_id}",response_model=PaymentOut)
def get_payment(payment_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    p=db.get(Payment,payment_id)
    if not p: raise HTTPException(404,"Payment not found")
    if user.role==Role.CUSTOMER and p.order.customer_id != user.id: raise HTTPException(403,"Not your payment")
    return p

@router.post("/refunds",response_model=RefundOut,status_code=201)
def create_refund(data:RefundIn,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if user.role not in (Role.ADMIN,Role.RESTAURANT_OWNER): raise HTTPException(403,"Only admins or restaurant owners can record refunds")
    p=db.get(Payment,data.payment_id)
    if not p: raise HTTPException(404,"Payment not found")
    already=sum(x.amount for x in p.refunds)
    if data.amount + already > p.amount: raise HTTPException(400,"Refund exceeds payment amount")
    r=Refund(**data.model_dump()); db.add(r)
    if data.amount+already >= p.amount: p.status=PaymentStatus.REFUNDED
    db.commit(); db.refresh(r); return r

@router.get("/refunds/{refund_id}",response_model=RefundOut)
def get_refund(refund_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    r=db.get(Refund,refund_id)
    if not r: raise HTTPException(404,"Refund not found")
    if user.role==Role.CUSTOMER and r.payment.order.customer_id != user.id: raise HTTPException(403,"Not your refund")
    return r
