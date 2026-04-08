from typing import Tuple, Optional


class ProgressAgent:
    """
    Analyses weight-trend data and recommends calorie adjustments
    to keep the user moving toward their goal.

    Algorithms used
    ───────────────
    • Linear regression over the supplied history to obtain a reliable
      rate-of-change even with noisy daily weigh-ins.
    • Plateau detection: < 0.15 kg / week change for 2+ consecutive "weeks"
      of data (requires >= 14 data points for full analysis).
    • Over-shoot detection: change rate beyond the healthy range triggers a
      gentler approach recommendation.
    """

    # Healthy weekly change thresholds (kg)
    PLATEAU_THRESHOLD_KG   = 0.15   # below this → plateau
    MAX_SAFE_LOSS_PER_WEEK = 0.9    # above this → too aggressive
    MAX_SAFE_GAIN_PER_WEEK = 0.6

    # Calorie step sizes
    ADJUSTMENT_SMALL = 100   # gentle nudge
    ADJUSTMENT_MED   = 200   # standard step
    ADJUSTMENT_LARGE = 300   # break a stubborn plateau

    def analyze_progress(
        self,
        weight_history: list,
        current_calories: float,
        goal: str,
    ) -> Tuple[Optional[float], str]:
        """
        Returns (new_calories | None, reason_string).
        Returns (None, reason) when no calorie change is warranted.
        """
        n = len(weight_history)
        if n < 3:
            return None, "Not enough data yet (need at least 3 weigh-ins)."

        # ── Linear regression for trend rate ──────────────────────────────
        indices = list(range(n))
        x_mean = sum(indices) / n
        y_mean = sum(weight_history) / n

        numerator   = sum((indices[i] - x_mean) * (weight_history[i] - y_mean) for i in range(n))
        denominator = sum((indices[i] - x_mean) ** 2 for i in range(n)) or 1
        slope_per_day = numerator / denominator          # kg / day
        weekly_rate   = slope_per_day * 7                # kg / week

        # ── Plateau detection ──────────────────────────────────────────────
        is_plateau = abs(weekly_rate) < self.PLATEAU_THRESHOLD_KG

        # ── Goal-specific logic ────────────────────────────────────────────
        if goal == "loss":
            if is_plateau:
                step = self.ADJUSTMENT_LARGE if n >= 14 else self.ADJUSTMENT_MED
                return (
                    current_calories - step,
                    f"📉 Plateau detected (trend: {weekly_rate:+.2f} kg/wk). "
                    f"Reducing target by {step} kcal to restart progress."
                )
            if weekly_rate < -self.MAX_SAFE_LOSS_PER_WEEK:
                return (
                    current_calories + self.ADJUSTMENT_MED,
                    f"⚠️ Losing too fast ({weekly_rate:.2f} kg/wk). "
                    f"Adding {self.ADJUSTMENT_MED} kcal to protect muscle."
                )
            return None, (
                f"✅ Solid progress ({weekly_rate:.2f} kg/wk). "
                "No calorie change needed — keep going!"
            )

        if goal == "gain":
            if is_plateau:
                step = self.ADJUSTMENT_LARGE if n >= 14 else self.ADJUSTMENT_MED
                return (
                    current_calories + step,
                    f"📈 Plateau detected (trend: {weekly_rate:+.2f} kg/wk). "
                    f"Adding {step} kcal to restart muscle gain."
                )
            if weekly_rate > self.MAX_SAFE_GAIN_PER_WEEK:
                return (
                    current_calories - self.ADJUSTMENT_SMALL,
                    f"⚠️ Gaining too fast ({weekly_rate:.2f} kg/wk). "
                    f"Reducing by {self.ADJUSTMENT_SMALL} kcal to minimise fat gain."
                )
            return None, (
                f"✅ Solid gain pace ({weekly_rate:+.2f} kg/wk). "
                "No adjustment needed."
            )

        # Maintain
        if abs(weekly_rate) > 0.3:
            direction = "down" if weekly_rate < 0 else "up"
            step = self.ADJUSTMENT_SMALL
            new_cal = current_calories + (step if weekly_rate < 0 else -step)
            return (
                new_cal,
                f"Weight drifting {direction} ({weekly_rate:+.2f} kg/wk). "
                f"Adjusting by {step} kcal to hold steady."
            )

        return None, f"✅ Weight stable ({weekly_rate:+.2f} kg/wk). No adjustment needed."
