from typing import List, Tuple
from .models import Recipe, Ingredient, Meal, UserPreferences

class DecisionMaker:
    def __init__(self, memory_module):
        self.memory = memory_module

    def select_meals(
        self,
        available_recipes: List[Recipe],
        user_preferences: UserPreferences
    ) -> Tuple[Recipe, Recipe, Recipe]:
        """Select the best combination of breakfast, lunch, and dinner recipes."""
        breakfast_options = [r for r in available_recipes if r.meal_type == "breakfast"]
        lunch_options = [r for r in available_recipes if r.meal_type == "lunch"]
        dinner_options = [r for r in available_recipes if r.meal_type == "dinner"]

        # Score and sort recipes based on ingredient availability and preferences
        breakfast = self._select_best_recipe(breakfast_options, user_preferences)
        lunch = self._select_best_recipe(lunch_options, user_preferences)
        dinner = self._select_best_recipe(dinner_options, user_preferences)

        return breakfast, lunch, dinner

    def create_meal(self, recipe: Recipe, available_ingredients: List[Ingredient]) -> Meal:
        """Create a Meal object by matching recipe requirements with available ingredients."""
        used_ingredients = []
        missing_ingredients = []

        # Match required ingredients with available ones
        for required_ing in recipe.required_ingredients:
            found = False
            for available_ing in available_ingredients:
                if (required_ing.name == available_ing.name and 
                    required_ing.unit == available_ing.unit and
                    required_ing.quantity <= available_ing.quantity):
                    used_ingredients.append(required_ing)
                    found = True
                    break
            if not found:
                missing_ingredients.append(required_ing)

        return Meal(
            recipe=recipe,
            used_ingredients=used_ingredients,
            missing_ingredients=missing_ingredients
        )

    def _select_best_recipe(
        self,
        recipes: List[Recipe],
        preferences: UserPreferences
    ) -> Recipe:
        """Score and select the best recipe based on various factors."""
        best_score = float('-inf')
        best_recipe = None

        for recipe in recipes:
            # Skip recently used recipes
            if self.memory.is_recipe_recently_used(recipe):
                continue

            score = self._calculate_recipe_score(recipe, preferences)
            if score > best_score:
                best_score = score
                best_recipe = recipe

        # If no recipe found (all were recently used), pick the first available one
        if best_recipe is None and recipes:
            best_recipe = recipes[0]

        return best_recipe

    def _calculate_recipe_score(self, recipe: Recipe, preferences: UserPreferences) -> float:
        """Calculate a score for a recipe based on various factors."""
        score = 0.0

        # Check ingredient availability
        available_ingredients = set(ing.name for ing in preferences.available_ingredients)
        required_ingredients = set(ing.name for ing in recipe.required_ingredients)
        
        # Calculate percentage of available ingredients
        if required_ingredients:
            availability_score = len(available_ingredients & required_ingredients) / len(required_ingredients)
            score += availability_score * 5  # Weight of 5 for ingredient availability

        # Check preparation time
        if preferences.max_preparation_time:
            if recipe.preparation_time <= preferences.max_preparation_time:
                score += 2
            else:
                score -= 1

        # Check dietary preferences
        if preferences.dietary_preference in recipe.dietary_preferences:
            score += 3

        # Check excluded ingredients
        if any(excluded in required_ingredients for excluded in preferences.excluded_ingredients):
            score -= 10

        return score 