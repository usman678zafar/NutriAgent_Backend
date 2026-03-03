from app.agents.nutrition_agent import NutritionAgent
from app.agents.meal_agent import MealAgent
from app.agents.progress_agent import ProgressAgent
from app.agents.habit_agent import HabitDetectionAgent

class PlannerAgent:
    def __init__(self):
        self.nutrition_agent = NutritionAgent()
        self.meal_agent = MealAgent()
        self.progress_agent = ProgressAgent()
        self.habit_agent = HabitDetectionAgent()

    async def handle_metrics_update(self, user_id, metrics):
        """
        Triggered when user updates weight, height, etc.
        """
        targets = self.nutrition_agent.calculate_targets(
            weight=metrics.weight,
            height=metrics.height,
            age=metrics.age,
            gender=metrics.gender,
            activity_level=metrics.activity_level,
            goal=metrics.goal
        )
        return targets

    async def handle_review_progress(self, user_id, weight_history, current_targets, goal):
        """
        Triggered manually or weekly.
        """
        new_calories, reason = self.progress_agent.analyze_progress(
            weight_history=weight_history,
            current_calories=current_targets.calories,
            goal=goal
        )
        
        if new_calories:
            # Re-calculate macros based on new calorie target
            # Keep same protein/fat ratios or re-run nutrition agent with a fixed cal target
            # For simplicity, we'll just adjust carbs for now in this flow
            # or we could scale everything.
            adjustment = {
                "user_id": user_id,
                "previous_calories": current_targets.calories,
                "new_calories": new_calories,
                "reason": reason
            }
            return adjustment
        
        return None

    async def get_meal_suggestions(self, targets):
        """
        Triggered when user requests a meal plan.
        """
        return self.meal_agent.generate_meal_plan(
            target_calories=targets.calories,
            target_protein=targets.protein,
            target_carbs=targets.carbs,
            target_fats=targets.fats
        )

    async def handle_habit_check(self, meal_history, daily_targets):
        """
        Triggered to detect eating patterns.
        """
        return self.habit_agent.detect_patterns(meal_history, daily_targets)

    async def estimate_meal(self, food_query: str):
        """
        Use AI to estimate macros for a specific food description.
        """
        return await self.meal_agent.estimate_nutrients(food_query)
