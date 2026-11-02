from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Address, User
from app.schemas import AddressIn, AddressOut
from app.security import get_current_user

router=APIRouter(tags=["Customer Resources"])

@router.get("/customers/{customer_id}/addresses",response_model=list[AddressOut])
def list_addresses(customer_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if user.id != customer_id and user.role.value != "ADMIN": raise HTTPException(403,"Not allowed")
    return db.query(Address).filter_by(user_id=customer_id).order_by(Address.created_at.desc()).all()

@router.post("/customers/{customer_id}/addresses",response_model=AddressOut,status_code=201)
def create_address(customer_id:int,data:AddressIn,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if user.id != customer_id and user.role.value != "ADMIN": raise HTTPException(403,"Not allowed")
    if not db.get(User,customer_id): raise HTTPException(404,"Customer not found")
    a=Address(user_id=customer_id,**data.model_dump()); db.add(a); db.commit(); db.refresh(a); return a
