from typing import Optional


class NutritionAgent:
    """
    Calculates personalised calorie and macro targets using
    the Mifflin-St Jeor BMR formula and goal-based adjustments.
    """

    ACTIVITY_MULTIPLIERS = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }

    # Adjustment presets (kcal relative to TDEE)
    GOAL_ADJUSTMENTS = {
        "loss": -500,
        "gain": 500,
        "maintain": 0,
    }

    # Hard floors to keep targets physiologically safe
    MIN_CALORIES = {
        "male": 1500,
        "female": 1200,
    }

    def calculate_targets(
        self,
        weight: float,      # kg
        height: float,      # cm
        age: float,          # years
        gender: str,         # "male" | "female"
        activity_level: str, # key from ACTIVITY_MULTIPLIERS
        goal: str,           # "loss" | "gain" | "maintain"
        target_weight: Optional[float] = None,  # kg (unused yet, reserved)
    ) -> dict:
        """
        Returns a dict with keys: calories, protein, carbs, fats (all grams).

        Macro split logic:
        - Protein : 2.0 g/kg body-weight  (muscle preservation)
        - Fats    : 25 % of total calories (hormonal health floor)
        - Carbs   : Remainder (energy source)
        """
        # ── Input validation ──────────────────────────────────────────────
        if weight <= 0 or height <= 0 or age <= 0:
            raise ValueError("weight, height and age must be positive numbers")

        gender_key = gender.lower()
        if gender_key not in ("male", "female"):
            gender_key = "male"  # safe default

        activity_key = activity_level.lower()
        goal_key = goal.lower()

        # ── BMR (Mifflin-St Jeor) ─────────────────────────────────────────
        if gender_key == "male":
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        # ── TDEE ──────────────────────────────────────────────────────────
        multiplier = self.ACTIVITY_MULTIPLIERS.get(activity_key, 1.2)
        tdee = bmr * multiplier

        # ── Calorie target ────────────────────────────────────────────────
        adjustment = self.GOAL_ADJUSTMENTS.get(goal_key, 0)
        calories = tdee + adjustment

        # Enforce physiological floor
        floor = self.MIN_CALORIES.get(gender_key, 1200)
        calories = max(calories, floor)

        # ── Macros ────────────────────────────────────────────────────────
        # Protein: 2.0 g / kg
        protein_g = round(weight * 2.0)

        # Fats: 25 % of total target calories
        fat_g = round((calories * 0.25) / 9)

        # Carbs: fill remainder
        remaining_cals = calories - (protein_g * 4) - (fat_g * 9)
        carb_g = round(max(remaining_cals / 4, 0))

        return {
            "calories": round(calories),
            "protein":  protein_g,
            "carbs":    carb_g,
            "fats":     fat_g,
            # Metadata for the frontend to display to the user
            "bmr":  round(bmr),
            "tdee": round(tdee),
        }
