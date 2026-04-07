from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[float] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class MetricsBase(BaseModel):
    weight: float
    height: float
    age: float
    gender: str
    activity_level: str
    goal: str

class MetricsCreate(MetricsBase):
    pass

class MetricsResponse(MetricsBase):
    id: UUID
    recorded_at: datetime
    class Config:
        from_attributes = True

class MealBase(BaseModel):
    meal_type: str
    food_name: str
    calories: float
    protein: float
    carbs: float
    fats: float
    source: Optional[str] = "manual"

class MealCreate(MealBase):
    pass

class MealResponse(MealBase):
    id: UUID
    timestamp: datetime
    class Config:
        from_attributes = True

class TargetResponse(BaseModel):
    calories: float
    protein: float
    carbs: float
    fats: float
    date: datetime
    class Config:
        from_attributes = True

class AdjustmentResponse(BaseModel):
    previous_calories: float
    new_calories: float
    reason: str
    created_at: datetime
    class Config:
        from_attributes = True

class MealEstimateRequest(BaseModel):
    food: str

class MealScanRequest(BaseModel):
    image: str # Base64 encoded image

class MealScanResponse(BaseModel):
    food_name: str
    calories: float
    protein: float
    carbs: float
    fats: float
    description: Optional[str] = None
