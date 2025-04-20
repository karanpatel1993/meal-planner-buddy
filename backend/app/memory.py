from typing import List, Dict, Set, Any
from datetime import date, timedelta, datetime
from .models import Recipe, MealPlan

class MemoryModule:
    def __init__(self):
        # In-memory storage of past meal plans
        # In a real implementation, this would be persisted to disk or database
        self.meal_plans: Dict[date, MealPlan] = {}
        # Set of recipe IDs used in the last week to avoid repetition
        self.recent_recipe_ids: Set[str] = set()
        self.saved_recipes: Dict[str, Dict[str, Any]] = {}  # key: recipe_id, value: {recipe: Recipe, saved_at: datetime}

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

    def save_recipe(self, recipe: Recipe) -> bool:
        """Save a recipe with current timestamp. Return True if saved, False if already exists."""
        if recipe.id in self.saved_recipes:
            return False
        
        self.saved_recipes[recipe.id] = {
            "recipe": recipe,
            "saved_at": datetime.now()
        }
        return True

    def get_saved_recipes(self) -> List[Dict[str, Any]]:
        """Get all saved recipes with their timestamps."""
        return [
            {
                "recipe": {
                    "id": saved["recipe"].id,
                    "name": saved["recipe"].name,
                    "meal_type": saved["recipe"].meal_type,
                    "description": saved["recipe"].description,
                    "required_ingredients": [
                        {
                            "name": ing.name,
                            "quantity": ing.quantity,
                            "unit": ing.unit
                        } for ing in saved["recipe"].required_ingredients
                    ],
                    "instructions": saved["recipe"].instructions,
                    "preparation_time": saved["recipe"].preparation_time,
                    "dietary_preferences": [pref.value for pref in saved["recipe"].dietary_preferences]
                },
                "saved_at": saved["saved_at"].isoformat()
            }
            for saved in self.saved_recipes.values()
        ]

    def is_recipe_saved(self, recipe_id: str) -> bool:
        """Check if a recipe is already saved."""
        return recipe_id in self.saved_recipes

    def get_recipe_names(self) -> List[str]:
        """Get names of all saved recipes to avoid duplicates."""
        return [saved["recipe"].name for saved in self.saved_recipes.values()] 