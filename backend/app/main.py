from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from datetime import date
from typing import List, Optional
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

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
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize modules
perception = PerceptionModule()
memory = MemoryModule()
decision_maker = DecisionMaker(memory)
action = ActionModule()

@app.get("/")
async def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": jsonable_encoder(exc.errors())
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc.detail),
            "status_code": exc.status_code
        }
    )

# Request model for meal plan generation
class MealPlanRequest(BaseModel):
    raw_ingredients: List[str] = Field(
        ..., 
        min_items=1, 
        description="List of ingredients with quantities",
        example=["2 cups rice", "500 grams chicken", "4 pieces tomatoes"]
    )
    dietary_preference: DietaryPreference = Field(
        default=DietaryPreference.NONE,
        description="Dietary preference"
    )
    api_key: str = Field(
        ..., 
        min_length=1, 
        description="Gemini API key"
    )

    class Config:
        schema_extra = {
            "example": {
                "raw_ingredients": [
                    "2 cups rice",
                    "500 grams chicken",
                    "4 pieces tomatoes"
                ],
                "dietary_preference": "NONE",
                "api_key": "your-api-key-here"
            }
        }

@app.post("/api/generate-meal-plan")
async def generate_meal_plan(request: MealPlanRequest) -> MealPlan:
    """Generate a daily meal plan based on available ingredients and preferences."""
    try:
        # Validate ingredients format
        if not all(isinstance(ing, str) for ing in request.raw_ingredients):
            raise HTTPException(
                status_code=422,
                detail="All ingredients must be strings"
            )

        # Parse ingredients
        try:
            ingredients = perception.parse_ingredients(request.raw_ingredients)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse ingredients: {str(e)}"
            )
        
        # Create user preferences
        preferences = UserPreferences(
            dietary_preference=request.dietary_preference,
            available_ingredients=ingredients,
            excluded_ingredients=[],
            max_preparation_time=None
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 