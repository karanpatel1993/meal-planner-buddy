from datetime import date
from typing import List

from models import UserPreferences, DietaryPreference, Ingredient
from perception import PerceptionModule
from memory import MemoryModule
from decision_maker import DecisionMaker
from action import ActionModule

def main():
    # Initialize all modules
    perception = PerceptionModule()
    memory = MemoryModule()
    decision_maker = DecisionMaker(memory)
    action = ActionModule()

    # Example user input
    raw_ingredients = [
        "500 grams rice",
        "250 grams chicken",
        "5 pieces tomatoes",
        "2 cups milk",
        "500 grams potatoes"
    ]

    # Parse user preferences
    ingredients = perception.parse_ingredients(raw_ingredients)
    preferences = UserPreferences(
        dietary_preference=DietaryPreference.NONE,
        available_ingredients=ingredients,
        max_preparation_time=60  # 60 minutes
    )

    # Generate suitable recipes
    available_recipes = perception.generate_recipes(preferences)

    # Select the best meals for today
    breakfast, lunch, dinner = decision_maker.select_meals(
        available_recipes,
        preferences
    )

    # Create meal objects with used/missing ingredients
    breakfast_meal = decision_maker.create_meal(breakfast, preferences.available_ingredients)
    lunch_meal = decision_maker.create_meal(lunch, preferences.available_ingredients)
    dinner_meal = decision_maker.create_meal(dinner, preferences.available_ingredients)

    # Generate the final meal plan
    meal_plan = action.generate_meal_plan(
        current_date=date.today(),
        breakfast=breakfast_meal,
        lunch=lunch_meal,
        dinner=dinner_meal
    )

    # Store the meal plan in memory
    memory.store_meal_plan(meal_plan)

    # Format and print the meal plan
    print(action.format_meal_plan(meal_plan))

if __name__ == "__main__":
    main() 