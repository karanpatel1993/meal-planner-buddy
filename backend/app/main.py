from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from datetime import date
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import logging
import traceback

from .models import UserPreferences, MealPlan, Ingredient, DietaryPreference, Recipe
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        content={"detail": str(exc.detail)}
    )

# Request model for meal plan generation
class MealPlanRequest(BaseModel):
    raw_ingredients: List[str] = Field(
        ...,  # This makes the field required
        description="List of ingredients in the format 'quantity unit name'",
        example=["2 cups rice", "1 lb chicken breast"]
    )
    dietary_preference: str = Field(
        ...,
        description="Dietary preference for meal planning",
        example="vegetarian"
    )
    api_key: str = Field(
        ...,
        description="Gemini API key for recipe generation"
    )

@app.post("/api/generate-meal-plan")
async def generate_meal_plan(request: MealPlanRequest):
    """Generate a meal plan based on available ingredients and preferences."""
    logger.info("Received meal plan generation request")
    logger.info(f"Ingredients: {request.raw_ingredients}")
    logger.info(f"Dietary preference: {request.dietary_preference}")
    
    try:
        # Validate ingredients format
        parsed_ingredients = []
        for ingredient in request.raw_ingredients:
            parts = ingredient.split()
            if len(parts) < 2:  # Need at least quantity and name
                logger.warning(f"Invalid ingredient format: {ingredient}")
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid ingredient format: '{ingredient}'. Expected format: 'quantity unit name' (e.g., '2 cups rice') or 'quantity name' (e.g., '2 carrots')"
                )
            try:
                quantity = float(parts[0])
            except ValueError:
                logger.warning(f"Invalid quantity in ingredient: {ingredient}")
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid quantity in ingredient: '{ingredient}'. Quantity must be a number."
                )

            # If only 2 parts (quantity and name), insert "piece" as the unit
            if len(parts) == 2:
                parts = [parts[0], "piece", parts[1]]
        
        logger.info("Creating UserPreferences object")
        # Create UserPreferences object
        preferences = UserPreferences(
            dietary_preference=request.dietary_preference,
            available_ingredients=perception.parse_ingredients(request.raw_ingredients),
            api_key=request.api_key
        )
        
        # Generate meal plan using the perception module
        try:
            logger.info("Calling perception module to generate recipes")
            recipes = await perception.generate_recipes(preferences)
            
            if not recipes:
                logger.warning("No recipes generated")
                raise HTTPException(
                    status_code=404,
                    detail="No suitable recipes found for the given ingredients and preferences"
                )
            
            logger.info(f"Successfully generated {len(recipes)} recipes")
            return {"recipes": recipes}
            
        except Exception as recipe_error:
            error_trace = traceback.format_exc()
            logger.error(f"Recipe generation error: {str(recipe_error)}\n{error_trace}")
            
            if "API request failed" in str(recipe_error):
                raise HTTPException(
                    status_code=400,
                    detail=f"Gemini API error: {str(recipe_error)}"
                )
            elif "Failed to parse recipe JSON" in str(recipe_error):
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse recipe data: {str(recipe_error)}"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error generating recipes: {str(recipe_error)}"
                )
            
    except HTTPException:
        # Re-raise HTTP exceptions as they already have proper error details
        raise
    except ValueError as e:
        error_trace = traceback.format_exc()
        logger.error(f"Validation error: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Unexpected error: {str(e)}\n{error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/api/save-recipe/{recipe_id}")
async def save_recipe(recipe_id: str):
    """Save a recipe to memory."""
    try:
        # Find the recipe in the last generated batch
        recipes = await perception.get_last_generated_recipes()
        
        # Convert recipe_id to integer for array indexing
        try:
            recipe_index = int(recipe_id)
            if recipe_index < 0 or recipe_index >= len(recipes):
                raise ValueError("Invalid recipe index")
            recipe = recipes[recipe_index]
        except ValueError:
            # If recipe_id is not a valid index, try matching by ID
            recipe = next((r for r in recipes if r.id == recipe_id), None)
            if not recipe:
                raise HTTPException(status_code=404, detail="Recipe not found")

        # Try to save the recipe
        if memory.save_recipe(recipe):
            return {"message": "Recipe saved successfully"}
        else:
            raise HTTPException(status_code=400, detail="Recipe already saved")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save recipe: {str(e)}")

@app.get("/api/saved-recipes")
async def get_saved_recipes() -> List[Dict[str, Any]]:
    """Get all saved recipes."""
    try:
        return memory.get_saved_recipes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve saved recipes: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 