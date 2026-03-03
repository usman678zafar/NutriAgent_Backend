import datetime

class ProgressAgent:
    def analyze_progress(self, weight_history, current_calories, goal):
        """
        weight_history: list of weights in the last 7+ days
        current_calories: current calorie target
        goal: 'loss', 'gain', 'maintain'
        """
        if len(weight_history) < 7:
            return None, "Not enough data to analyze (need 7 days)"

        last_7_days = weight_history[-7:]
        weight_change = last_7_days[-1] - last_7_days[0]
        
        # Simple plateau detection: change less than 0.2kg in a week
        is_plateau = abs(weight_change) < 0.2
        
        if is_plateau:
            new_calories = current_calories
            reason = "Plateau detected. "
            
            if goal == "loss":
                new_calories -= 150
                reason += "Reducing calories by 150 to break plateau."
            elif goal == "gain":
                new_calories += 150
                reason += "Increasing calories by 150 to break plateau."
            else:
                reason = "Weight stable. No adjustment needed for 'maintain' goal."
                return None, reason
                
            return new_calories, reason
            
        return None, "Progress on track. No adjustment needed."
