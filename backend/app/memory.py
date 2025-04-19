from typing import List, Dict, Set
from datetime import date, timedelta
from .models import Recipe, MealPlan

class MemoryModule:
    def __init__(self):
        # In-memory storage of past meal plans
        # In a real implementation, this would be persisted to disk or database
        self.meal_plans: Dict[date, MealPlan] = {}
        # Set of recipe IDs used in the last week to avoid repetition
        self.recent_recipe_ids: Set[str] = set()

    def store_meal_plan(self, meal_plan: MealPlan):
        """Store a new meal plan and update recent recipes."""
        self.meal_plans[meal_plan.date] = meal_plan
        
        # Add recipe IDs to recent set
        self.recent_recipe_ids.add(meal_plan.breakfast.recipe.id)
        self.recent_recipe_ids.add(meal_plan.lunch.recipe.id)
        self.recent_recipe_ids.add(meal_plan.dinner.recipe.id)
        
        # Remove recipes older than 7 days
        self._cleanup_old_recipes()

    def is_recipe_recently_used(self, recipe: Recipe) -> bool:
        """Check if a recipe has been used recently."""
        return recipe.id in self.recent_recipe_ids

    def get_past_meal_plan(self, target_date: date) -> MealPlan:
        """Retrieve a meal plan for a specific date."""
        return self.meal_plans.get(target_date)

    def _cleanup_old_recipes(self):
        """Remove recipes that are older than 7 days from recent_recipe_ids."""
        cutoff_date = date.today() - timedelta(days=7)
        old_recipe_ids = set()
        
        # Find recipes from meal plans older than 7 days
        for plan_date, meal_plan in self.meal_plans.items():
            if plan_date < cutoff_date:
                old_recipe_ids.add(meal_plan.breakfast.recipe.id)
                old_recipe_ids.add(meal_plan.lunch.recipe.id)
                old_recipe_ids.add(meal_plan.dinner.recipe.id)
        
        # Remove old recipe IDs from recent set
        self.recent_recipe_ids -= old_recipe_ids 