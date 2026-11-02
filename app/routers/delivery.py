from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Delivery, Driver, User, Role, DeliveryStatus, DeliveryStatusHistory, OrderStatus, Order
from app.schemas import DriverCreate, DriverOut, DriverAssign, DeliveryStatusPatch, DeliveryOut, HistoryOut
from app.security import get_current_user

router=APIRouter(tags=["Delivery"])

@router.post("/drivers",response_model=DriverOut,status_code=201)
def create_driver(data:DriverCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if user.role != Role.ADMIN: raise HTTPException(403,"Only admins can create driver profiles")
    target=db.get(User,data.user_id)
    if not target: raise HTTPException(404,"User not found")
    if target.role != Role.DRIVER: raise HTTPException(400,"User must have DRIVER role")
    if db.query(Driver).filter_by(user_id=target.id).first(): raise HTTPException(409,"Driver profile already exists")
    d=Driver(**data.model_dump()); db.add(d); db.commit(); db.refresh(d); return d

@router.get("/drivers",response_model=list[DriverOut])
def list_drivers(available:bool|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    q=db.query(Driver)
    if available is not None: q=q.filter(Driver.is_available==available)
    return q.all()

@router.post("/deliveries/{delivery_id}/assign-driver",response_model=DeliveryOut)
def assign_driver(delivery_id:int,data:DriverAssign,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if user.role not in (Role.ADMIN,Role.STAFF,Role.RESTAURANT_OWNER): raise HTTPException(403,"Not allowed to assign drivers")
    d=db.get(Delivery,delivery_id); driver=db.get(Driver,data.driver_id)
    if not d or not driver: raise HTTPException(404,"Delivery or driver not found")
    if not driver.is_available: raise HTTPException(409,"Driver is not available")
    if d.status in (DeliveryStatus.DELIVERED,DeliveryStatus.FAILED): raise HTTPException(400,"Delivery is already closed")
    if d.driver_id and d.driver_id != driver.id:
        previous=db.get(Driver,d.driver_id)
        if previous: previous.is_available=True
    d.driver_id=driver.id; driver.is_available=False; d.status=DeliveryStatus.ASSIGNED
    db.add(DeliveryStatusHistory(delivery_id=d.id,old_status="UNASSIGNED",new_status=DeliveryStatus.ASSIGNED.value,changed_by_id=user.id,note="Driver assigned"))
    db.commit(); db.refresh(d); return d

@router.patch("/deliveries/{delivery_id}/status",response_model=DeliveryOut)
def update_delivery_status(delivery_id:int,data:DeliveryStatusPatch,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    d=db.get(Delivery,delivery_id)
    if not d: raise HTTPException(404,"Delivery not found")
    if user.role not in (Role.ADMIN,Role.STAFF,Role.DRIVER): raise HTTPException(403,"Not allowed")
    if user.role==Role.DRIVER and (not d.driver or d.driver.user_id != user.id): raise HTTPException(403,"This delivery is assigned to another driver")
    allowed={
      DeliveryStatus.ASSIGNED:{DeliveryStatus.PICKED_UP,DeliveryStatus.FAILED},
      DeliveryStatus.PICKED_UP:{DeliveryStatus.IN_TRANSIT,DeliveryStatus.FAILED},
      DeliveryStatus.IN_TRANSIT:{DeliveryStatus.DELIVERED,DeliveryStatus.FAILED},
      DeliveryStatus.DELIVERED:set(), DeliveryStatus.FAILED:set()
    }
    if data.status not in allowed[d.status]: raise HTTPException(400,f"Invalid delivery transition: {d.status.value} -> {data.status.value}")
    old=d.status; d.status=data.status
    if data.status==DeliveryStatus.DELIVERED:
        d.order.status=OrderStatus.DELIVERED
        if d.driver: d.driver.is_available=True
    if data.status==DeliveryStatus.FAILED and d.driver: d.driver.is_available=True
    db.add(DeliveryStatusHistory(delivery_id=d.id,old_status=old.value,new_status=data.status.value,changed_by_id=user.id,note=data.note))
    db.commit(); db.refresh(d); return d

@router.get("/deliveries",response_model=list[DeliveryOut])
def list_deliveries(status:DeliveryStatus|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    q=db.query(Delivery)
    if status: q=q.filter(Delivery.status==status)
    if user.role==Role.DRIVER:
        driver=db.query(Driver).filter_by(user_id=user.id).first()
        if not driver: return []
        q=q.filter(Delivery.driver_id==driver.id)
    elif user.role==Role.CUSTOMER:
        q=q.join(Order).filter(Order.customer_id==user.id)
    return q.order_by(Delivery.created_at.desc()).all()

@router.get("/deliveries/{delivery_id}",response_model=DeliveryOut)
def get_delivery(delivery_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    d=db.get(Delivery,delivery_id)
    if not d: raise HTTPException(404,"Delivery not found")
    if user.role==Role.CUSTOMER and d.order.customer_id != user.id: raise HTTPException(403,"Not your delivery")
    if user.role==Role.DRIVER and (not d.driver or d.driver.user_id != user.id): raise HTTPException(403,"Not assigned to you")
    return d

@router.get("/deliveries/{delivery_id}/status-history",response_model=list[HistoryOut])
def delivery_history(delivery_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    d=db.get(Delivery,delivery_id)
    if not d: raise HTTPException(404,"Delivery not found")
    if user.role==Role.CUSTOMER and d.order.customer_id != user.id: raise HTTPException(403,"Not your delivery")
    return db.query(DeliveryStatusHistory).filter_by(delivery_id=delivery_id).order_by(DeliveryStatusHistory.created_at).all()
