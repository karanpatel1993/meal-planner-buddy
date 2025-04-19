from typing import List
from datetime import date
from .models import Meal, MealPlan, Ingredient

class ActionModule:
    def generate_meal_plan(
        self,
        current_date: date,
        breakfast: Meal,
        lunch: Meal,
        dinner: Meal
    ) -> MealPlan:
        """Generate a complete meal plan for the day."""
        # Compile shopping list from all missing ingredients
        shopping_list = self._compile_shopping_list([breakfast, lunch, dinner])

        return MealPlan(
            date=current_date,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            shopping_list=shopping_list
        )

    def _compile_shopping_list(self, meals: List[Meal]) -> List[Ingredient]:
        """Compile a consolidated shopping list from all missing ingredients."""
        # Dictionary to store consolidated ingredients by name and unit
        consolidated: dict[tuple[str, str], Ingredient] = {}

        for meal in meals:
            for ingredient in meal.missing_ingredients:
                key = (ingredient.name, ingredient.unit)
                if key in consolidated:
                    # Add quantities for same ingredient and unit
                    consolidated[key].quantity += ingredient.quantity
                else:
                    # Create a new ingredient entry
                    consolidated[key] = Ingredient(
                        name=ingredient.name,
                        quantity=ingredient.quantity,
                        unit=ingredient.unit
                    )

        return list(consolidated.values())

    def format_meal_plan(self, meal_plan: MealPlan) -> str:
        """Format the meal plan as a human-readable string."""
        output = [
            f"Meal Plan for {meal_plan.date}",
            "\n=== Breakfast ===",
            f"Recipe: {meal_plan.breakfast.recipe.name}",
            f"Description: {meal_plan.breakfast.recipe.description}",
            "\nUsing:",
            *[f"- {ing}" for ing in meal_plan.breakfast.used_ingredients],
            "\nMissing:",
            *[f"- {ing}" for ing in meal_plan.breakfast.missing_ingredients],
            "\n=== Lunch ===",
            f"Recipe: {meal_plan.lunch.recipe.name}",
            f"Description: {meal_plan.lunch.recipe.description}",
            "\nUsing:",
            *[f"- {ing}" for ing in meal_plan.lunch.used_ingredients],
            "\nMissing:",
            *[f"- {ing}" for ing in meal_plan.lunch.missing_ingredients],
            "\n=== Dinner ===",
            f"Recipe: {meal_plan.dinner.recipe.name}",
            f"Description: {meal_plan.dinner.recipe.description}",
            "\nUsing:",
            *[f"- {ing}" for ing in meal_plan.dinner.used_ingredients],
            "\nMissing:",
            *[f"- {ing}" for ing in meal_plan.dinner.missing_ingredients],
            "\n=== Shopping List ===",
            *[f"- {ing}" for ing in meal_plan.shopping_list]
        ]
        
        return "\n".join(output) 