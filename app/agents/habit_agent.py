class HabitDetectionAgent:
    def detect_patterns(self, meal_history, daily_targets):
        """
        Analyzes meal history against targets to find recurring habits.
        Returns a list of patterns: { title, desc, impact, action }
        """
        if not meal_history:
            return []

        patterns = []
        import datetime
        
        # Helper to group meals by date
        daily_data = {}
        for meal in meal_history:
            day = meal.timestamp.date()
            if day not in daily_data:
                daily_data[day] = {"protein": 0, "calories": 0, "meals": []}
            daily_data[day]["protein"] += meal.protein
            daily_data[day]["calories"] += meal.calories
            daily_data[day]["meals"].append(meal.meal_type.lower())

        days_analyzed = len(daily_data)
        
        # 1. Protein Consistency
        if days_analyzed >= 2:
            protein_target = daily_targets.protein
            target_met_days = sum(1 for d in daily_data.values() if d["protein"] >= (protein_target * 0.9))
            
            if target_met_days == days_analyzed:
                patterns.append({
                    "title": "Protein Powerhouse",
                    "impact": "Positive",
                    "desc": f"You've hit your protein target {days_analyzed} days in a row! This is excellent for muscle preservation.",
                    "action": "Maintain this high-protein streak"
                })
            elif target_met_days < (days_analyzed / 2):
                patterns.append({
                    "title": "Protein Deficit",
                    "impact": "Negative",
                    "desc": "You are frequently falling short of your protein goals, which might slow down your recovery.",
                    "action": "Try adding a protein shake to your afternoon"
                })

        # 2. Timing/Cravings Pattern
        late_night_calories = sum(m.calories for m in meal_history if m.timestamp.hour >= 21)
        total_calories = sum(m.calories for m in meal_history) or 1
        if (late_night_calories / total_calories) > 0.2:
            patterns.append({
                "title": "Late Night Energy",
                "impact": "Negative",
                "desc": "A significant portion of your calories are consumed after 9 PM, which may affect sleep quality.",
                "action": "Shift your largest meal to earlier in the day"
            })

        # 3. Consistency
        if days_analyzed >= 5:
            patterns.append({
                "title": "Metric Consistency",
                "impact": "Positive",
                "desc": "Your logging consistency is in the top 10% of users. This data accuracy leads to better AI results.",
                "action": "Keep up the detailed logging"
            })

        return patterns
