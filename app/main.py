from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.db.database import get_db, engine
from app.models.models import Base, User, BodyMetrics, DailyTarget, Meal, WeeklyAdjustment
from app.models.schemas import (
    UserCreate, UserLogin, UserResponse, Token, MetricsCreate, 
    MetricsResponse, MealCreate, MealResponse, TargetResponse,
    MealEstimateRequest, MealScanRequest, MealScanResponse
)
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.agents.planner import PlannerAgent
import uuid
import datetime
from typing import Optional

app = FastAPI(title="NutriAgent AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

planner = PlannerAgent()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "NutriAgent API is up and running! 🥑", "status": "healthy"}

@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    import traceback
    try:
        result = await db.execute(select(User).where(User.email == user.email))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        db_user = User(
            name=user.name,
            email=user.email,
            password_hash=get_password_hash(user.password)
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        print(f"REGISTER ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalars().first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse)
async def get_me(db: AsyncSession = Depends(get_db), current_user_id: str = Depends(get_current_user)):
    result = await db.execute(select(User).where(User.id == uuid.UUID(current_user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Fetch latest metrics for onboarding status
    metrics_result = await db.execute(
        select(BodyMetrics)
        .where(BodyMetrics.user_id == user.id)
        .order_by(desc(BodyMetrics.recorded_at))
        .limit(1)
    )
    latest_metrics = metrics_result.scalars().first()
    
    # Enrichment for frontend
    if latest_metrics:
        user.weight = latest_metrics.weight
        user.height = latest_metrics.height
        user.age = latest_metrics.age
        user.gender = latest_metrics.gender
        user.activity_level = latest_metrics.activity_level
        user.goal = latest_metrics.goal
        
    return user

@app.post("/metrics", response_model=TargetResponse)
async def update_metrics(metrics: MetricsCreate, db: AsyncSession = Depends(get_db), current_user_id: str = Depends(get_current_user)):
    # Save metrics
    db_metrics = BodyMetrics(**metrics.dict(), user_id=current_user_id)
    db.add(db_metrics)
    
    # Run Planner Agent to calculate new targets
    targets = await planner.handle_metrics_update(current_user_id, metrics)
    
    db_target = DailyTarget(
        user_id=current_user_id,
        calories=targets["calories"],
        protein=targets["protein"],
        carbs=targets["carbs"],
        fats=targets["fats"]
    )
    db.add(db_target)
    
    await db.commit()
    await db.refresh(db_target)
    return db_target

@app.get("/targets/current", response_model=TargetResponse)
async def get_current_targets(db: AsyncSession = Depends(get_db), current_user_id: str = Depends(get_current_user)):
    result = await db.execute(
        select(DailyTarget)
        .where(DailyTarget.user_id == current_user_id)
        .order_by(desc(DailyTarget.date))
        .limit(1)
    )
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="No targets set yet")
    return target

@app.get("/metrics/current", response_model=MetricsResponse)
async def get_current_metrics(db: AsyncSession = Depends(get_db), current_user_id: str = Depends(get_current_user)):
    result = await db.execute(
        select(BodyMetrics)
        .where(BodyMetrics.user_id == current_user_id)
        .order_by(desc(BodyMetrics.recorded_at))
        .limit(1)
    )
    metrics = result.scalars().first()
    if not metrics:
        raise HTTPException(status_code=404, detail="No metrics recorded yet")
    return metrics

@app.get("/metrics/history")
async def get_metrics_history(db: AsyncSession = Depends(get_db), current_user_id: str = Depends(get_current_user)):
    result = await db.execute(
        select(BodyMetrics)
        .where(BodyMetrics.user_id == current_user_id)
        .order_by(BodyMetrics.recorded_at.asc())
        .limit(30)
    )
    return result.scalars().all()

@app.post("/meals", response_model=MealResponse)
async def log_meal(meal: MealCreate, db: AsyncSession = Depends(get_db), current_user_id: str = Depends(get_current_user)):
    meal_data = meal.dict()
    meal_data["meal_type"] = meal_data["meal_type"].lower()
    db_meal = Meal(**meal_data, user_id=current_user_id)
    db.add(db_meal)
    await db.commit()
    await db.refresh(db_meal)
    return db_meal

@app.get("/meals", response_model=list[MealResponse])
async def get_meals(date: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user_id: str = Depends(get_current_user)):
    if date:
        try:
            target_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = datetime.datetime.utcnow().date()
        
    start_of_day = datetime.datetime.combine(target_date, datetime.time.min)
    end_of_day = datetime.datetime.combine(target_date, datetime.time.max)
    
    result = await db.execute(
        select(Meal)
        .where(Meal.user_id == current_user_id, Meal.timestamp >= start_of_day, Meal.timestamp <= end_of_day)
    )
    return result.scalars().all()

@app.post("/progress/review")
async def review_progress(db: AsyncSession = Depends(get_db), current_user_id: str = Depends(get_current_user)):
    # Fetch weight history (last 10 entries)
    weights_result = await db.execute(
        select(BodyMetrics.weight)
        .where(BodyMetrics.user_id == current_user_id)
        .order_by(desc(BodyMetrics.recorded_at))
        .limit(10)
    )
    weight_history = weights_result.scalars().all()[::-1] # chronological
    
    # Fetch current targets
    targets_result = await db.execute(
        select(DailyTarget)
        .where(DailyTarget.user_id == current_user_id)
        .order_by(desc(DailyTarget.date))
        .limit(1)
    )
    current_targets = targets_result.scalars().first()
    
    # Fetch user goal
    metrics_result = await db.execute(
        select(BodyMetrics.goal)
        .where(BodyMetrics.user_id == current_user_id)
        .order_by(desc(BodyMetrics.recorded_at))
        .limit(1)
    )
    goal = metrics_result.scalars().first()
    
    if not current_targets or not goal:
         raise HTTPException(status_code=400, detail="Missing user data to review progress")

    adjustment = await planner.handle_review_progress(current_user_id, weight_history, current_targets, goal)
    
    if adjustment:
        # Save adjustment
        db_adj = WeeklyAdjustment(**adjustment)
        db.add(db_adj)
        
        # Update daily targets (simplified: keep macros same ratio)
        # In a real app, logic would be more complex
        scale = adjustment["new_calories"] / adjustment["previous_calories"]
        new_target = DailyTarget(
            user_id=current_user_id,
            calories=adjustment["new_calories"],
            protein=current_targets.protein * scale,
            carbs=current_targets.carbs * scale,
            fats=current_targets.fats * scale
        )
        db.add(new_target)
        await db.commit()
        return {"status": "adjusted", "details": adjustment}
    
    return {"status": "no_change", "reason": "Weight on track or insufficient data"}

@app.get("/meals/suggestions")
async def get_suggestions(db: AsyncSession = Depends(get_db), current_user_id: str = Depends(get_current_user)):
    result = await db.execute(
        select(DailyTarget)
        .where(DailyTarget.user_id == current_user_id)
        .order_by(desc(DailyTarget.date))
        .limit(1)
    )
    targets = result.scalars().first()
    if not targets:
        raise HTTPException(status_code=404, detail="Set your metrics first to get suggestions")
        
    suggestions = await planner.get_meal_suggestions(targets)
    return suggestions

@app.post("/meals/estimate", response_model=MealScanResponse)
async def estimate_meal(request: MealEstimateRequest, current_user_id: str = Depends(get_current_user)):
    # Delegate to AI Agent
    estimation = await planner.estimate_meal(request.food)
    return estimation

@app.post("/meals/scan", response_model=MealScanResponse)
async def scan_meal(request: MealScanRequest, current_user_id: str = Depends(get_current_user)):
    # Delegate to AI Agent with image
    result = await planner.scan_meal(request.image)
    if not result:
        raise HTTPException(status_code=500, detail="Image scan failed")
    return result

@app.get("/insights/habits")
async def get_habit_insights(db: AsyncSession = Depends(get_db), current_user_id: str = Depends(get_current_user)):
    # Fetch last 30 meals
    meals_result = await db.execute(
        select(Meal)
        .where(Meal.user_id == current_user_id)
        .order_by(desc(Meal.timestamp))
        .limit(30)
    )
    meal_history = meals_result.scalars().all()
    
    # Fetch current targets
    targets_result = await db.execute(
        select(DailyTarget)
        .where(DailyTarget.user_id == current_user_id)
        .order_by(desc(DailyTarget.date))
        .limit(1)
    )
    current_targets = targets_result.scalars().first()
    
    if not current_targets:
        return []
        
    insights = await planner.handle_habit_check(meal_history, current_targets)
    return insights
