from typing import List, Dict
from .models import Ingredient, Recipe, UserPreferences, DietaryPreference

class PerceptionModule:
    def __init__(self):
        # Mock recipe database - in a real implementation, this would be loaded from a database or API
        self.recipe_database: List[Recipe] = self._initialize_mock_recipes()

    def parse_ingredients(self, raw_ingredients: List[str]) -> List[Ingredient]:
        """Parse raw ingredient strings into Ingredient objects."""
        parsed_ingredients = []
        for raw_ing in raw_ingredients:
            # Simple parsing logic - in reality, would use more robust NLP
            parts = raw_ing.split()
            if len(parts) >= 3:
                quantity = float(parts[0])
                unit = parts[1]
                name = " ".join(parts[2:])
                parsed_ingredients.append(
                    Ingredient(name=name, quantity=quantity, unit=unit)
                )
        return parsed_ingredients

    def generate_recipes(self, preferences: UserPreferences) -> List[Recipe]:
        """Generate or retrieve recipes based on user preferences."""
        # In a real implementation, this would call an LLM or recipe API
        # For now, just filter mock recipes based on dietary preferences
        suitable_recipes = []
        for recipe in self.recipe_database:
            if preferences.dietary_preference in recipe.dietary_preferences:
                if (not preferences.max_preparation_time or 
                    recipe.preparation_time <= preferences.max_preparation_time):
                    suitable_recipes.append(recipe)
        return suitable_recipes

    def _initialize_mock_recipes(self) -> List[Recipe]:
        """Initialize a mock recipe database."""
        return [
            Recipe(
                id="1",
                name="Masala Dosa",
                meal_type="breakfast",
                description="Crispy rice and lentil crepe with potato filling",
                required_ingredients=[
                    Ingredient(name="rice", quantity=1, unit="cup"),
                    Ingredient(name="urad dal", quantity=0.5, unit="cup"),
                    Ingredient(name="potatoes", quantity=2, unit="pieces"),
                ],
                instructions=["Soak rice and dal", "Grind to paste", "Ferment", "Make dosa"],
                preparation_time=45,
                dietary_preferences=[DietaryPreference.VEGETARIAN, DietaryPreference.VEGAN]
            ),
            Recipe(
                id="2",
                name="Butter Chicken",
                meal_type="lunch",
                description="Creamy tomato-based curry with tender chicken",
                required_ingredients=[
                    Ingredient(name="chicken", quantity=500, unit="grams"),
                    Ingredient(name="tomatoes", quantity=4, unit="pieces"),
                    Ingredient(name="cream", quantity=200, unit="ml"),
                ],
                instructions=["Marinate chicken", "Make gravy", "Cook chicken"],
                preparation_time=60,
                dietary_preferences=[DietaryPreference.NONE]
            ),
            Recipe(
                id="3",
                name="Vegetable Biryani",
                meal_type="lunch",
                description="Fragrant rice dish with mixed vegetables and aromatic spices",
                required_ingredients=[
                    Ingredient(name="rice", quantity=2, unit="cups"),
                    Ingredient(name="mixed vegetables", quantity=500, unit="grams"),
                    Ingredient(name="onions", quantity=2, unit="pieces"),
                ],
                instructions=["Cook rice", "Prepare vegetables", "Layer and steam"],
                preparation_time=50,
                dietary_preferences=[DietaryPreference.VEGETARIAN, DietaryPreference.VEGAN]
            ),
            Recipe(
                id="4",
                name="Palak Paneer",
                meal_type="dinner",
                description="Cottage cheese cubes in creamy spinach gravy",
                required_ingredients=[
                    Ingredient(name="spinach", quantity=500, unit="grams"),
                    Ingredient(name="paneer", quantity=200, unit="grams"),
                    Ingredient(name="onions", quantity=2, unit="pieces"),
                ],
                instructions=["Blanch spinach", "Prepare gravy", "Cook paneer"],
                preparation_time=40,
                dietary_preferences=[DietaryPreference.VEGETARIAN]
            ),
            Recipe(
                id="5",
                name="Poha",
                meal_type="breakfast",
                description="Flattened rice with peanuts and spices",
                required_ingredients=[
                    Ingredient(name="poha", quantity=2, unit="cups"),
                    Ingredient(name="peanuts", quantity=0.5, unit="cup"),
                    Ingredient(name="onions", quantity=1, unit="piece"),
                ],
                instructions=["Soak poha", "Roast peanuts", "Cook with spices"],
                preparation_time=20,
                dietary_preferences=[DietaryPreference.VEGETARIAN, DietaryPreference.VEGAN]
            )
        ] 