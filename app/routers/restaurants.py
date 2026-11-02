from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Restaurant, RestaurantBranch, Menu, Role, User
from app.schemas import RestaurantIn, RestaurantOut, BranchIn, BranchOut, MenuIn, MenuOut
from app.security import get_current_user, require_roles

router = APIRouter(tags=["Restaurants & Menus"])

@router.post("/restaurants", response_model=RestaurantOut, status_code=201)
def create_restaurant(data: RestaurantIn, db: Session=Depends(get_db), user: User=Depends(require_roles(Role.ADMIN, Role.RESTAURANT_OWNER))):
    obj=Restaurant(owner_id=user.id, **data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.get("/restaurants", response_model=list[RestaurantOut])
def list_restaurants(search: str|None=None, location: str|None=None, active: bool|None=None, page: int=Query(1, ge=1), limit: int=Query(20, ge=1, le=100), sort_by: str="created_at", order: str="desc", db: Session=Depends(get_db)):
    q=db.query(Restaurant)
    if search: q=q.filter(Restaurant.name.ilike(f"%{search}%"))
    if location: q=q.filter(Restaurant.location.ilike(f"%{location}%"))
    if active is not None: q=q.filter(Restaurant.is_active == active)
    column=getattr(Restaurant, sort_by, Restaurant.created_at)
    q=q.order_by(column.asc() if order.lower()=="asc" else column.desc())
    return q.offset((page-1)*limit).limit(limit).all()

@router.get("/restaurants/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(restaurant_id:int, db:Session=Depends(get_db)):
    obj=db.get(Restaurant, restaurant_id)
    if not obj: raise HTTPException(404,"Restaurant not found")
    return obj

@router.post("/restaurants/{restaurant_id}/branches", response_model=BranchOut, status_code=201)
def create_branch(restaurant_id:int, data:BranchIn, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    r=db.get(Restaurant,restaurant_id)
    if not r: raise HTTPException(404,"Restaurant not found")
    if user.role != Role.ADMIN and r.owner_id != user.id: raise HTTPException(403,"Only the restaurant owner or admin can add branches")
    obj=RestaurantBranch(restaurant_id=restaurant_id,**data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.post("/menus", response_model=MenuOut, status_code=201)
def create_menu(data:MenuIn, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    r=db.get(Restaurant,data.restaurant_id)
    if not r: raise HTTPException(404,"Restaurant not found")
    if user.role not in (Role.ADMIN,Role.RESTAURANT_OWNER) or (user.role != Role.ADMIN and r.owner_id != user.id): raise HTTPException(403,"Not allowed")
    obj=Menu(**data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.get("/menus/{menu_id}", response_model=MenuOut)
def get_menu(menu_id:int, db:Session=Depends(get_db)):
    obj=db.get(Menu,menu_id)
    if not obj: raise HTTPException(404,"Menu not found")
    return obj


def test_customer_cannot_create_restaurant(client):
    # Register and log in as a customer
    client.post(
        "/auth/register",
        json={
            "full_name": "Test Customer",
            "email": "restaurant_customer@example.com",
            "password": "SecurePass123"
        }
    )

    login = client.post(
        "/auth/login",
        data={
            "username": "restaurant_customer@example.com",
            "password": "SecurePass123"
        }
    )
    assert login.status_code == 200, login.text

    token = login.json()["access_token"]

    # Try to create a restaurant as a customer
    response = client.post(
        "/restaurants",
        json={
            "name": "Unauthorized Restaurant",
            "description": "Test restaurant",
            "location": "Kumasi"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403, response.text


def test_restaurant_list_is_public(client):
    response = client.get("/restaurants")

    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)
