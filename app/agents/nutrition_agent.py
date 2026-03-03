class NutritionAgent:
    def __init__(self):
        self.activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }

    def calculate_targets(self, weight, height, age, gender, activity_level, goal):
        # BMR Calculation (Mifflin-St Jeor)
        if gender.lower() == "male":
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        # TDEE Calculation
        multiplier = self.activity_multipliers.get(activity_level, 1.2)
        tdee = bmr * multiplier

        # Adjust for goal
        if goal == "loss":
            calories = tdee - 500
        elif goal == "gain":
            calories = tdee + 500
        else:
            calories = tdee

        # Macro Calculation (Weight-based approach)
        # Protein: 2.0g per kg
        protein_grams = weight * 2.0
        protein_cals = protein_grams * 4

        # Fats: 0.9g per kg
        fat_grams = weight * 0.9
        fat_cals = fat_grams * 9

        # Carbs: Remainder
        carb_cals = calories - (protein_cals + fat_cals)
        carb_grams = max(carb_cals / 4, 0)

        return {
            "calories": round(calories),
            "protein": round(protein_grams),
            "carbs": round(carb_grams),
            "fats": round(fat_grams)
        }
