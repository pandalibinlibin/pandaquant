import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy import Index


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)

    strategies: List["Strategy"] = Relationship(back_populates="creator")
    factors: List["Factor"] = Relationship(back_populates="creator")
    backtests: List["Backtest"] = Relationship(back_populates="creator")
    signals: List["Signal"] = Relationship(back_populates="creator")


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


class Strategy(SQLModel, table=True):
    __tablename__ = "strategies"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    strategy_type: str = Field(max_length=50)
    status: str = Field(default="draft", max_length=20)
    config: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: UUID = Field(foreign_key="user.id")

    creator: Optional["User"] = Relationship(back_populates="strategies")
    backtests: List["Backtest"] = Relationship(back_populates="strategy")
    signals: List["Signal"] = Relationship(back_populates="strategy")


class Factor(SQLModel, table=True):
    __tablename__ = "factors"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    factor_type: str = Field(max_length=50)
    formula: str = Field(max_length=1000)
    parameters: Optional[str] = Field(default=None)
    status: str = Field(default="active", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: UUID = Field(foreign_key="user.id")

    creator: Optional["User"] = Relationship(back_populates="factors")


class Backtest(SQLModel, table=True):
    __tablename__ = "backtests"

    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    name: str = Field(max_length=100, index=True)
    strategy_id: UUID = Field(foreign_key="strategies.id")
    start_date: datetime = Field(index=True)
    end_date: datetime = Field(index=True)
    initial_capital: float = Field(default=1000000.0)
    status: str = Field(default="pending", max_length=20)
    results: Optional[str] = Field(default=None)
    performance_metrics: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: UUID = Field(foreign_key="user.id")

    strategy: Optional["Strategy"] = Relationship(back_populates="backtests")
    creator: Optional["User"] = Relationship(back_populates="backtests")


class Signal(SQLModel, table=True):
    __tablename__ = "signals"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    strategy_id: UUID = Field(foreign_key="strategies.id")
    symbol: str = Field(max_length=20, index=True)
    signal_type: str = Field(max_length=20, index=True)
    signal_strength: float = Field(default=0.0)
    price: Optional[float] = Field(default=None)
    quantity: Optional[int] = Field(default=None)
    message: Optional[str] = Field(default=None, max_length=500)
    status: str = Field(default="pending", max_length=20)
    push_status: str = Field(default="not_pushed", max_length=20, index=True)
    push_channels: Optional[str] = Field(default=None, max_length=200)
    push_time: Optional[datetime] = Field(default=None)
    push_error: Optional[str] = Field(default=None, max_length=500)
    sent_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: UUID = Field(foreign_key="user.id")

    strategy: Optional["Strategy"] = Relationship(back_populates="signals")
    creator: Optional["User"] = Relationship(back_populates="signals")


class BacktestResult(SQLModel, table=True):
    """Backtest result model for storing backtest performance metrics"""

    __tablename__ = "backtest_result"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    strategy_name: str = Field(max_length=100)
    symbol: str = Field(max_length=20)
    start_date: str = Field(max_length=20)
    end_date: str = Field(max_length=20)
    initial_capital: float
    final_value: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    result_data: str = Field(default="{}")
    created_by: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
