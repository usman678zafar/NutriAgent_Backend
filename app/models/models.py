from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    metrics = relationship("BodyMetrics", back_populates="user")
    meals = relationship("Meal", back_populates="user")
    targets = relationship("DailyTarget", back_populates="user")
    adjustments = relationship("WeeklyAdjustment", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")

class BodyMetrics(Base):
    __tablename__ = "body_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    age = Column(Float, nullable=False)
    gender = Column(String, nullable=False) # male, female
    activity_level = Column(String, nullable=False) # sedentary, light, moderate, active, very_active
    goal = Column(String, nullable=False) # loss, gain, maintain
    target_weight = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="metrics")

class DailyTarget(Base):
    __tablename__ = "daily_targets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="targets")

class Meal(Base):
    __tablename__ = "meals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    meal_type = Column(String, nullable=False) # breakfast, lunch, dinner, snack
    food_name = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    volume = Column(Float, nullable=True, default=0)
    source = Column(String, nullable=False, default="manual")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="meals")

class WeeklyAdjustment(Base):
    __tablename__ = "weekly_adjustments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    previous_calories = Column(Float, nullable=False)
    new_calories = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="adjustments")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="chat_history")
