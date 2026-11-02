from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models import Role, OrderStatus, DeliveryStatus, PaymentStatus

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(ORMModel):
    id: int
    full_name: str
    email: EmailStr
    role: Role
    is_active: bool

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RestaurantIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = ""
    location: str = Field(min_length=2, max_length=255)

class RestaurantOut(ORMModel):
    id: int
    owner_id: int
    name: str
    description: str
    location: str
    is_active: bool

class ProductIn(BaseModel):
    restaurant_id: int
    category_id: int
    name: str = Field(min_length=2, max_length=160)
    description: str = ""
    price: float = Field(gt=0)
    is_available: bool = True

class ProductOut(ORMModel):
    id: int
    restaurant_id: int
    category_id: int
    name: str
    description: str
    price: float
    is_available: bool

class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=100)
    variant_id: int | None = None

class CartItemPatch(BaseModel):
    quantity: int = Field(ge=1, le=100)

class CartItemOut(ORMModel):
    id: int
    product_id: int
    variant_id: int | None
    quantity: int

class CartOut(BaseModel):
    id: int
    user_id: int
    items: list[CartItemOut]

class OrderCreate(BaseModel):
    address_id: int | None = None
    notes: str = ""

class OrderStatusPatch(BaseModel):
    status: OrderStatus
    note: str = ""

class OrderItemOut(ORMModel):
    id: int
    product_id: int
    product_name: str
    unit_price: float
    quantity: int

class OrderOut(ORMModel):
    id: int
    customer_id: int
    address_id: int | None
    status: OrderStatus
    total: float
    notes: str
    created_at: datetime
    items: list[OrderItemOut]

class PaymentCreate(BaseModel):
    order_id: int
    provider_reference: str = ""

class PaymentOut(ORMModel):
    id: int
    order_id: int
    amount: float
    status: PaymentStatus
    provider_reference: str

class DriverCreate(BaseModel):
    user_id: int
    vehicle_type: str = "Motorcycle"

class DriverOut(ORMModel):
    id: int
    user_id: int
    vehicle_type: str
    is_available: bool

class DriverAssign(BaseModel):
    driver_id: int

class DeliveryStatusPatch(BaseModel):
    status: DeliveryStatus
    note: str = ""

class DeliveryOut(ORMModel):
    id: int
    order_id: int
    driver_id: int | None
    status: DeliveryStatus
    pickup_notes: str
    delivery_notes: str

class AddressIn(BaseModel):
    label: str = "Home"
    address_line: str
    city: str
    region: str = ""
    latitude: float | None = None
    longitude: float | None = None

class AddressOut(ORMModel):
    id: int
    user_id: int
    label: str
    address_line: str
    city: str
    region: str
    latitude: float | None
    longitude: float | None

class CategoryIn(BaseModel):
    menu_id: int
    name: str

class CategoryOut(ORMModel):
    id: int
    menu_id: int
    name: str

class MenuIn(BaseModel):
    restaurant_id: int
    name: str

class MenuOut(ORMModel):
    id: int
    restaurant_id: int
    name: str
    is_active: bool

class BranchIn(BaseModel):
    name: str
    address: str

class BranchOut(ORMModel):
    id: int
    restaurant_id: int
    name: str
    address: str
    is_active: bool

class VariantIn(BaseModel):
    product_id: int
    name: str
    price_delta: float = 0

class VariantOut(ORMModel):
    id: int
    product_id: int
    name: str
    price_delta: float

class RefundIn(BaseModel):
    payment_id: int
    amount: float = Field(gt=0)
    reason: str = Field(min_length=3)

class RefundOut(ORMModel):
    id: int
    payment_id: int
    amount: float
    reason: str

class HistoryOut(ORMModel):
    id: int
    old_status: str
    new_status: str
    changed_by_id: int
    note: str
    created_at: datetime
