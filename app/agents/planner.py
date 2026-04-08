import traceback
from app.agents.nutrition_agent import NutritionAgent
from app.agents.meal_agent import MealAgent
from app.agents.progress_agent import ProgressAgent
from app.agents.habit_agent import HabitDetectionAgent
from app.agents.coach_agent import CoachAgent


class PlannerAgent:
    """
    Central orchestrator.  All public methods are wrapped with consistent
    error handling so individual agent failures do not crash the API.
    """

    def __init__(self):
        self.nutrition_agent = NutritionAgent()
        self.meal_agent      = MealAgent()
        self.progress_agent  = ProgressAgent()
        self.habit_agent     = HabitDetectionAgent()
        self.coach_agent     = CoachAgent()

    # ── Metrics / Targets ──────────────────────────────────────────────────

    async def handle_metrics_update(self, user_id: str, metrics):
        """
        Triggered when user updates weight, height, etc.
        Returns a calorie/macro target dict or raises ValueError with a
        user-friendly message on invalid inputs.
        """
        try:
            targets = self.nutrition_agent.calculate_targets(
                weight=metrics.weight,
                height=metrics.height,
                age=metrics.age,
                gender=metrics.gender,
                activity_level=metrics.activity_level,
                goal=metrics.goal,
                target_weight=getattr(metrics, "target_weight", None),
            )
            return targets
        except ValueError as e:
            raise ValueError(f"Invalid metrics: {e}") from e
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Failed to calculate targets: {e}") from e

    # ── Progress Review ────────────────────────────────────────────────────

    async def handle_review_progress(self, user_id: str, weight_history: list,
                                     current_targets, goal: str):
        """
        Analyses weight history and returns an adjustment dict or None.
        """
        try:
            new_calories, reason = self.progress_agent.analyze_progress(
                weight_history=weight_history,
                current_calories=current_targets.calories,
                goal=goal,
            )
            if new_calories:
                # Floor: never recommend dangerously low calories
                new_calories = max(new_calories, 1200)
                return {
                    "user_id":           user_id,
                    "previous_calories": current_targets.calories,
                    "new_calories":      new_calories,
                    "reason":            reason,
                }
            return None
        except Exception as e:
            traceback.print_exc()
            print(f"Progress review failed: {e}")
            return None   # non-fatal; just skip adjustment

    # ── Meal Suggestions ───────────────────────────────────────────────────

    async def get_meal_suggestions(self, targets):
        """
        Returns a list of meal suggestions matching the user's macro targets.
        """
        try:
            return self.meal_agent.generate_meal_plan(
                target_calories=targets.calories,
                target_protein=targets.protein,
                target_carbs=targets.carbs,
                target_fats=targets.fats,
            )
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Meal suggestion generation failed: {e}") from e

    # ── Habit Analysis ─────────────────────────────────────────────────────

    async def handle_habit_check(self, meal_history: list, daily_targets):
        """
        Analyses eating patterns. Returns [] on failure so the UI still loads.
        """
        try:
            return self.habit_agent.detect_patterns(meal_history, daily_targets)
        except Exception as e:
            traceback.print_exc()
            print(f"Habit detection failed: {e}")
            return []

    # ── Food Estimation ────────────────────────────────────────────────────

    async def estimate_meal(self, food_query: str):
        """
        Use AI to estimate macros for a specific food description.
        Raises ValueError for bad input, RuntimeError for AI failures.
        """
        try:
            return await self.meal_agent.estimate_nutrients(food_query)
        except ValueError:
            raise   # pass validation errors straight through to the API
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Meal estimation failed: {e}") from e

    # ── Image Scan ─────────────────────────────────────────────────────────

    async def scan_meal(self, base64_image: str):
        """
        Use AI Vision to scan meal from an image.
        """
        try:
            return await self.meal_agent.scan_food_image(base64_image)
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Image scan failed: {e}") from e

    # ── Coach Chat ─────────────────────────────────────────────────────────

    async def chat_with_coach(self, message: str, history: list,
                               user_context: dict, today_stats: dict,
                               targets: dict = None):
        """
        Speak to the AI Coach.
        Returns a fallback tuple on failure instead of crashing.
        """
        try:
            return await self.coach_agent.chat(
                message, history, user_context, today_stats, targets or {}
            )
        except Exception as e:
            traceback.print_exc()
            print(f"Coach agent failed: {e}")
            return (
                "I'm having trouble processing that right now. "
                "Please try again in a moment! 🙏",
                None,
            )
