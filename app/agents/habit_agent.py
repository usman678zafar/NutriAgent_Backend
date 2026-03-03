class HabitDetectionAgent:
    def detect_patterns(self, meal_history, daily_targets):
        """
        Analyzes meal history against targets to find recurring habits.
        """
        if not meal_history:
            return []

        recommendations = []
        
        # 1. Check for recurring protein deficit
        days_analyzed = len(set(m.timestamp.date() for m in meal_history))
        if days_analyzed >= 3:
            # Group meals by day and sum protein
            daily_protein = {}
            for meal in meal_history:
                day = meal.timestamp.date()
                daily_protein[day] = daily_protein.get(day, 0) + meal.protein
            
            protein_deficit_days = sum(1 for p in daily_protein.values() if p < (daily_targets.protein * 0.8))
            
            if protein_deficit_days >= 2:
                recommendations.append({
                    "type": "habit_warning",
                    "title": "Protein Consistency",
                    "text": "You've missed your protein target in 2 of the last 3 days. Consider adding high-protein snacks like Greek yogurt or jerky."
                })

        # 2. Check for meal skipping
        # (Simplified logic: check if certain meal types are missing across days)
        meal_types_logged = [m.meal_type.lower() for m in meal_history]
        if "breakfast" not in meal_types_logged and days_analyzed >= 3:
            recommendations.append({
                "type": "lifestyle_tip",
                "title": "Breakfast Pattern",
                "text": "It looks like you frequently skip breakfast. If you feel low energy in the afternoon, try a small protein-rich start to your day."
            })

        return recommendations
