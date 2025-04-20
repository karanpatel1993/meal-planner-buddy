from typing import List, Dict, Any
import json
import aiohttp
import asyncio
from .models import Ingredient, Recipe, UserPreferences, DietaryPreference
import os
import certifi
import ssl

class PerceptionModule:
    def __init__(self):
        self.recipe_database: List[Recipe] = []
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.headers = {
            "Content-Type": "application/json"
        }
        # Create SSL context with certifi certificates
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

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

    async def generate_recipes(self, preferences: UserPreferences) -> List[Recipe]:
        """Generate recipes using Gemini API based on user preferences."""
        # Create prompt for recipe generation
        ingredients_text = "\n".join([f"{ing.quantity} {ing.unit} {ing.name}" for ing in preferences.available_ingredients])
        
        prompt = f"""Generate 6 Indian recipes (2 breakfast, 2 lunch, 2 dinner) using these ingredients:
{ingredients_text}

Dietary preference: {preferences.dietary_preference.value}

Return ONLY a JSON object in this exact format:
{{
    "recipes": [
        {{
            "id": "1",
            "name": "Recipe Name",
            "meal_type": "breakfast|lunch|dinner",
            "description": "Brief description",
            "available_ingredients": [
                {{
                    "name": "ingredient name",
                    "quantity": 1.0,  # Use decimal numbers or whole numbers, not fractions
                    "unit": "unit"    # Use "piece" for countable items without units
                }}
            ],
            "additional_ingredients": [
                {{
                    "name": "ingredient name",
                    "quantity": 1.0,  # Use decimal numbers or whole numbers, not fractions
                    "unit": "unit"    # Use "piece" for countable items without units
                }}
            ],
            "instructions": ["step 1", "step 2"],
            "preparation_time": 30
        }}
    ]
}}"""

        try:
            # Prepare the request data
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 8192,
                }
            }

            # Add API key to URL
            api_url = f"{self.base_url}?key={preferences.api_key}"

            # Make the API request with SSL context
            timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    api_url,
                    headers=self.headers,
                    json=data,
                    ssl=self.ssl_context
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API request failed with status {response.status}: {error_text}")
                    
                    response_data = await response.json()
                    
                    # Extract the generated text
                    generated_text = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                    print("Generated text:", generated_text)  # Debug log
                    
                    # Clean up the text - remove markdown code block indicators and whitespace
                    generated_text = generated_text.replace('```json', '').replace('```', '').strip()
                    
                    # Parse the JSON response
                    try:
                        recipes_data = json.loads(generated_text)
                    except json.JSONDecodeError as e:
                        print("Failed to parse JSON. Raw text:", generated_text)
                        raise Exception(f"Failed to parse recipe JSON: {str(e)}")
                    
                    if not isinstance(recipes_data, dict) or "recipes" not in recipes_data:
                        raise Exception("Invalid response format: missing 'recipes' key")
                    
                    if not recipes_data["recipes"]:
                        raise Exception("No recipes were generated")
                    
                    # Convert JSON to Recipe objects
                    recipes = []
                    for recipe_data in recipes_data["recipes"]:
                        try:
                            # Combine available and additional ingredients
                            all_ingredients = []
                            if "available_ingredients" in recipe_data:
                                all_ingredients.extend(recipe_data["available_ingredients"])
                            if "additional_ingredients" in recipe_data:
                                all_ingredients.extend(recipe_data["additional_ingredients"])
                            
                            # Create Recipe object
                            recipe = Recipe(
                                id=recipe_data["id"],
                                name=recipe_data["name"],
                                meal_type=recipe_data["meal_type"],
                                description=recipe_data["description"],
                                required_ingredients=[
                                    Ingredient(
                                        name=ing["name"],
                                        quantity=float(eval(str(ing["quantity"]))) if isinstance(ing["quantity"], str) else float(ing["quantity"]),
                                        unit=ing["unit"] if ing["unit"] else "piece"  # Default to "piece" if unit is empty
                                    ) for ing in all_ingredients
                                ],
                                instructions=recipe_data["instructions"],
                                preparation_time=recipe_data["preparation_time"],
                                dietary_preferences=[preferences.dietary_preference]
                            )
                            recipes.append(recipe)
                        except Exception as e:
                            print(f"Error processing recipe: {recipe_data}")
                            raise Exception(f"Failed to process recipe: {str(e)}")
                    
                    if not recipes:
                        raise Exception("Failed to create any valid recipes")
                    
                    return recipes
                    
        except Exception as e:
            raise Exception(f"Failed to generate recipes: {str(e)}") 