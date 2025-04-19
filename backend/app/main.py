from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from typing import List, Optional
import os
from dotenv import load_dotenv

from .models import UserPreferences, MealPlan, Ingredient, DietaryPreference
from .perception import PerceptionModule
from .memory import MemoryModule
from .decision_maker import DecisionMaker
from .action import ActionModule

# Load environment variables
load_dotenv()

app = FastAPI(title="Meal Planner API")

# Configure CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*"],  # Allow Chrome extensions
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
perception = PerceptionModule()
memory = MemoryModule()
decision_maker = DecisionMaker(memory)
action = ActionModule()

@app.post("/api/generate-meal-plan")
async def generate_meal_plan(
    raw_ingredients: List[str],
    dietary_preference: DietaryPreference = DietaryPreference.NONE,
    max_preparation_time: Optional[int] = None,
    excluded_ingredients: List[str] = []
) -> MealPlan:
    """Generate a daily meal plan based on available ingredients and preferences."""
    try:
        # Parse ingredients
        ingredients = perception.parse_ingredients(raw_ingredients)
        
        # Create user preferences
        preferences = UserPreferences(
            dietary_preference=dietary_preference,
            available_ingredients=ingredients,
            excluded_ingredients=excluded_ingredients,
            max_preparation_time=max_preparation_time
        )
        
        # Generate suitable recipes
        available_recipes = perception.generate_recipes(preferences)
        
        if not available_recipes:
            raise HTTPException(
                status_code=404,
                detail="No suitable recipes found for given preferences"
            )
        
        # Select meals
        breakfast, lunch, dinner = decision_maker.select_meals(
            available_recipes,
            preferences
        )
        
        # Create meal objects
        breakfast_meal = decision_maker.create_meal(breakfast, preferences.available_ingredients)
        lunch_meal = decision_maker.create_meal(lunch, preferences.available_ingredients)
        dinner_meal = decision_maker.create_meal(dinner, preferences.available_ingredients)
        
        # Generate meal plan
        meal_plan = action.generate_meal_plan(
            current_date=date.today(),
            breakfast=breakfast_meal,
            lunch=lunch_meal,
            dinner=dinner_meal
        )
        
        # Store in memory
        memory.store_meal_plan(meal_plan)
        
        return meal_plan
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 