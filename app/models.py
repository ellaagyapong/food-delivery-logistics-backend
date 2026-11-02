from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum

class Role(str, enum.Enum):
    ADMIN="ADMIN"
    RESTAURANT_OWNER="RESTAURANT_OWNER"
    STAFF="STAFF"
    CUSTOMER="CUSTOMER"
    DRIVER="DRIVER"

class OrderStatus(str, enum.Enum):
    PENDING="PENDING"
    CONFIRMED="CONFIRMED"
    PREPARING="PREPARING"
    READY_FOR_PICKUP="READY_FOR_PICKUP"
    OUT_FOR_DELIVERY="OUT_FOR_DELIVERY"
    DELIVERED="DELIVERED"
    CANCELLED="CANCELLED"

class DeliveryStatus(str, enum.Enum):
    ASSIGNED="ASSIGNED"
    PICKED_UP="PICKED_UP"
    IN_TRANSIT="IN_TRANSIT"
    DELIVERED="DELIVERED"
    FAILED="FAILED"

class PaymentStatus(str, enum.Enum):
    PENDING="PENDING"
    PAID="PAID"
    FAILED="FAILED"
    REFUNDED="REFUNDED"

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(TimestampMixin, Base):
    __tablename__="users"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.CUSTOMER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    profile: Mapped["CustomerProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    addresses: Mapped[list["Address"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Address(TimestampMixin, Base):
    __tablename__="addresses"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(60), default="Home")
    address_line: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100))
    region: Mapped[str] = mapped_column(String(100), default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    user: Mapped["User"] = relationship(back_populates="addresses")

class CustomerProfile(TimestampMixin, Base):
    __tablename__="customer_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    phone: Mapped[str] = mapped_column(String(30), default="")
    user: Mapped["User"] = relationship(back_populates="profile")

class Restaurant(TimestampMixin, Base):
    __tablename__="restaurants"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(255), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    branches: Mapped[list["RestaurantBranch"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    staff: Mapped[list["RestaurantStaff"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    menus: Mapped[list["Menu"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")

class RestaurantBranch(TimestampMixin, Base):
    __tablename__="restaurant_branches"
    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    restaurant: Mapped["Restaurant"] = relationship(back_populates="branches")

class RestaurantStaff(TimestampMixin, Base):
    __tablename__="restaurant_staff"
    __table_args__=(UniqueConstraint("restaurant_id","user_id", name="uq_restaurant_staff"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    job_title: Mapped[str] = mapped_column(String(80), default="Staff")
    restaurant: Mapped["Restaurant"] = relationship(back_populates="staff")
    user: Mapped["User"] = relationship()

class Menu(TimestampMixin, Base):
    __tablename__="menus"
    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    restaurant: Mapped["Restaurant"] = relationship(back_populates="menus")
    categories: Mapped[list["Category"]] = relationship(back_populates="menu", cascade="all, delete-orphan")

class Category(TimestampMixin, Base):
    __tablename__="categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120), index=True)
    menu: Mapped["Menu"] = relationship(back_populates="categories")
    products: Mapped[list["Product"]] = relationship(back_populates="category", cascade="all, delete-orphan")

class Product(TimestampMixin, Base):
    __tablename__="products"
    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[float] = mapped_column(Float)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    category: Mapped["Category"] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")

class ProductVariant(TimestampMixin, Base):
    __tablename__="product_variants"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    price_delta: Mapped[float] = mapped_column(Float, default=0)
    product: Mapped["Product"] = relationship(back_populates="variants")

class Cart(TimestampMixin, Base):
    __tablename__="carts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")

class CartItem(TimestampMixin, Base):
    __tablename__="cart_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
    variant: Mapped["ProductVariant | None"] = relationship()

class Order(TimestampMixin, Base):
    __tablename__="orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    address_id: Mapped[int | None] = mapped_column(ForeignKey("addresses.id"), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    total: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    history: Mapped[list["OrderStatusHistory"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payment: Mapped["Payment | None"] = relationship(back_populates="order", uselist=False, cascade="all, delete-orphan")
    delivery: Mapped["Delivery | None"] = relationship(back_populates="order", uselist=False, cascade="all, delete-orphan")

class OrderItem(TimestampMixin, Base):
    __tablename__="order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(160))
    unit_price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[int] = mapped_column(Integer)
    order: Mapped["Order"] = relationship(back_populates="items")

class OrderStatusHistory(TimestampMixin, Base):
    __tablename__="order_status_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    old_status: Mapped[str] = mapped_column(String(40))
    new_status: Mapped[str] = mapped_column(String(40))
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str] = mapped_column(Text, default="")
    order: Mapped["Order"] = relationship(back_populates="history")

class Payment(TimestampMixin, Base):
    __tablename__="payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True)
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    provider_reference: Mapped[str] = mapped_column(String(160), default="")
    order: Mapped["Order"] = relationship(back_populates="payment")
    refunds: Mapped[list["Refund"]] = relationship(back_populates="payment", cascade="all, delete-orphan")

class Refund(TimestampMixin, Base):
    __tablename__="refunds"
    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"))
    amount: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    payment: Mapped["Payment"] = relationship(back_populates="refunds")

class Driver(TimestampMixin, Base):
    __tablename__="drivers"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    vehicle_type: Mapped[str] = mapped_column(String(80), default="Motorcycle")
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    user: Mapped["User"] = relationship()

class Delivery(TimestampMixin, Base):
    __tablename__="deliveries"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"), nullable=True)
    status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus), default=DeliveryStatus.ASSIGNED)
    pickup_notes: Mapped[str] = mapped_column(Text, default="")
    delivery_notes: Mapped[str] = mapped_column(Text, default="")
    order: Mapped["Order"] = relationship(back_populates="delivery")
    driver: Mapped["Driver | None"] = relationship()
    history: Mapped[list["DeliveryStatusHistory"]] = relationship(back_populates="delivery", cascade="all, delete-orphan")

class DeliveryStatusHistory(TimestampMixin, Base):
    __tablename__="delivery_status_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    delivery_id: Mapped[int] = mapped_column(ForeignKey("deliveries.id", ondelete="CASCADE"))
    old_status: Mapped[str] = mapped_column(String(40))
    new_status: Mapped[str] = mapped_column(String(40))
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str] = mapped_column(Text, default="")
    delivery: Mapped["Delivery"] = relationship(back_populates="history")
