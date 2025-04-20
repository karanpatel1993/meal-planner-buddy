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

Return ONLY a JSON object in this exact format, with no additional text:
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
                    print("Raw API Response:", response_data)  # Debug log
                    
                    # Extract the generated text
                    generated_text = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                    print("Generated Text:", generated_text)  # Debug log
                    
                    # Clean up the text - remove any markdown and normalize whitespace
                    generated_text = generated_text.replace('```json\n', '').replace('\n```', '')
                    generated_text = generated_text.strip()
                    
                    # Parse the JSON response
                    try:
                        # First try direct parsing
                        recipes_data = json.loads(generated_text)
                    except json.JSONDecodeError as e:
                        print(f"Initial JSON parsing failed: {str(e)}")
                        try:
                            # Try cleaning the string more aggressively
                            import re
                            # Remove any non-JSON characters
                            cleaned_text = re.sub(r'[^\x20-\x7E]', '', generated_text)
                            recipes_data = json.loads(cleaned_text)
                        except json.JSONDecodeError as e:
                            print("Failed to parse JSON even after cleaning. Raw text:", generated_text)
                            raise Exception(f"Failed to parse recipe JSON: {str(e)}")
                    
                    if not isinstance(recipes_data, dict) or "recipes" not in recipes_data:
                        raise Exception("Invalid response format: missing 'recipes' key")
                    
                    if not recipes_data["recipes"]:
                        raise Exception("No recipes were generated")
                    
                    # Convert JSON to Recipe objects
                    recipes = []
                    for recipe_data in recipes_data["recipes"]:
                        try:
                            required_ingredients = [
                                Ingredient(**ing) for ing in recipe_data["required_ingredients"]
                            ]
                            
                            recipe = Recipe(
                                id=recipe_data["id"],
                                name=recipe_data["name"],
                                meal_type=recipe_data["meal_type"],
                                description=recipe_data["description"],
                                required_ingredients=required_ingredients,
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
            raise Exception(f"Network error while calling Gemini API: {str(e)}") 