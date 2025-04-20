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
        self.last_generated_recipes: List[Recipe] = []
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.headers = {
            "Content-Type": "application/json"
        }
        # Create SSL context with certifi certificates
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.memory = None  # Will be set by main.py

    def set_memory(self, memory_module):
        """Set the memory module for checking saved recipes."""
        self.memory = memory_module

    def parse_ingredients(self, raw_ingredients: List[str]) -> List[Ingredient]:
        """Parse raw ingredient strings into Ingredient objects."""
        parsed_ingredients = []
        for raw_ing in raw_ingredients:
            parts = raw_ing.split()
            try:
                if len(parts) >= 3:
                    # Format: "quantity unit name"
                    quantity = float(parts[0])
                    unit = parts[1]
                    name = " ".join(parts[2:])
                else:
                    # Format: "quantity name"
                    quantity = float(parts[0])
                    unit = "piece"  # Default unit for countable items
                    name = " ".join(parts[1:])
                
                parsed_ingredients.append(
                    Ingredient(name=name, quantity=quantity, unit=unit)
                )
            except (ValueError, IndexError) as e:
                raise ValueError(f"Failed to parse ingredient '{raw_ing}': {str(e)}")
            
        return parsed_ingredients

    async def get_last_generated_recipes(self) -> List[Recipe]:
        """Get the list of recipes from the last generation."""
        return self.last_generated_recipes

    async def generate_recipes(self, preferences: UserPreferences) -> List[Recipe]:
        """Generate recipes using Gemini API based on user preferences."""
        # Create prompt for recipe generation
        ingredients_text = "\n".join([f"{ing.quantity} {ing.unit} {ing.name}" for ing in preferences.available_ingredients])
        
        # Get saved recipe names to avoid duplicates
        saved_recipe_names = []
        if self.memory:
            try:
                saved_recipes = self.memory.get_saved_recipes()
                saved_recipe_names = [recipe["recipe"]["name"].lower() for recipe in saved_recipes]
            except Exception as e:
                print(f"Warning: Could not get saved recipes: {e}")
        
        prompt = f"""Generate 6 unique Indian recipes (2 breakfast, 2 lunch, 2 dinner) using these ingredients:
{ingredients_text}

Dietary preference: {preferences.dietary_preference.value}

{f'Please avoid these already saved recipes: {", ".join(saved_recipe_names)}' if saved_recipe_names else ''}

Return ONLY a JSON object in this exact format, with NO trailing commas:
{{
    "recipes": [
        {{
            "id": "1",
            "name": "Recipe Name",
            "meal_type": "breakfast|lunch|dinner",
            "description": "Brief description",
            "required_ingredients": [
                {{
                    "name": "ingredient name",
                    "quantity": 1.0,
                    "unit": "unit"
                }}
            ],
            "instructions": ["step 1", "step 2"],
            "preparation_time": 30
        }}
    ]
}}

Important:
1. Do not include any text before or after the JSON
2. Do not use trailing commas in arrays or objects
3. Use only double quotes for strings
4. Use decimal numbers for quantities (1.0, 2.5, etc.)
5. Keep the JSON structure exactly as shown
6. Generate completely different recipes from the saved ones listed above"""

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
                    "maxOutputTokens": 8192
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
                    
                    # Clean up the text - remove markdown code block indicators, whitespace, and any text before/after JSON
                    generated_text = generated_text.replace('```json', '').replace('```', '').strip()
                    
                    # Try to find the JSON object boundaries
                    start_idx = generated_text.find('{')
                    end_idx = generated_text.rfind('}') + 1
                    if start_idx == -1 or end_idx == 0:
                        raise Exception("No valid JSON object found in response")
                    
                    generated_text = generated_text[start_idx:end_idx]
                    
                    # Remove any trailing commas before ] or }
                    generated_text = generated_text.replace(',]', ']').replace(',}', '}')
                    
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
                            # Create Recipe object
                            recipe = Recipe(
                                id=str(recipe_data.get("id", "")),
                                name=recipe_data["name"],
                                meal_type=recipe_data["meal_type"],
                                description=recipe_data.get("description", ""),
                                required_ingredients=[
                                    Ingredient(
                                        name=ing["name"],
                                        quantity=float(ing["quantity"]),
                                        unit=ing.get("unit", "piece")
                                    ) for ing in recipe_data.get("required_ingredients", [])
                                ],
                                instructions=recipe_data.get("instructions", []),
                                preparation_time=int(recipe_data.get("preparation_time", 30)),
                                dietary_preferences=[preferences.dietary_preference]
                            )
                            recipes.append(recipe)
                        except Exception as e:
                            print(f"Error processing recipe: {recipe_data}")
                            raise Exception(f"Failed to process recipe: {str(e)}")
                    
                    if not recipes:
                        raise Exception("Failed to create any valid recipes")
                    
                    # Store the generated recipes
                    self.last_generated_recipes = recipes
                    
                    return recipes
                    
        except Exception as e:
            self.last_generated_recipes = []  # Clear on error
            raise Exception(f"Failed to generate recipes: {str(e)}") 