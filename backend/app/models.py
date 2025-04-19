from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date


class DietaryPreference(str, Enum):
    NONE = "none"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    KETO = "keto"
    PALEO = "paleo"


class Ingredient(BaseModel):
    name: str
    quantity: float
    unit: str
    
    def __str__(self) -> str:
        return f"{self.quantity} {self.unit} {self.name}"


class Recipe(BaseModel):
    id: str
    name: str
    meal_type: str  # breakfast, lunch, or dinner
    description: str
    required_ingredients: List[Ingredient]
    instructions: List[str]
    preparation_time: int  # in minutes
    dietary_preferences: List[DietaryPreference]
    cuisine_type: str = "Indian"  # Default to Indian cuisine


class Meal(BaseModel):
    recipe: Recipe
    used_ingredients: List[Ingredient]
    missing_ingredients: List[Ingredient]


class MealPlan(BaseModel):
    date: date
    breakfast: Meal
    lunch: Meal
    dinner: Meal
    shopping_list: List[Ingredient]


class UserPreferences(BaseModel):
    dietary_preference: DietaryPreference = DietaryPreference.NONE
    available_ingredients: List[Ingredient]
    excluded_ingredients: List[str] = Field(default_factory=list)
    max_preparation_time: Optional[int] = None  # in minutes 