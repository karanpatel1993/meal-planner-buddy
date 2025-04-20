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

    def clean_json_text(self, text: str) -> str:
        """Clean up JSON text to handle common formatting issues."""
        # Remove any markdown code block indicators
        text = text.replace('```json', '').replace('```', '').strip()
        
        # Remove any text before the first { or [ and after the last } or ]
        start_idx = min(text.find('{') if text.find('{') != -1 else len(text),
                       text.find('[') if text.find('[') != -1 else len(text))
        end_idx = max(text.rfind('}') + 1 if text.rfind('}') != -1 else 0,
                     text.rfind(']') + 1 if text.rfind(']') != -1 else 0)
        
        if start_idx == len(text) or end_idx == 0:
            raise ValueError("No valid JSON structure found")
            
        text = text[start_idx:end_idx]
        
        # Fix trailing commas in objects and arrays
        text = text.replace(',}', '}')
        text = text.replace(',]', ']')
        
        # Fix multiple trailing commas
        while ',,' in text:
            text = text.replace(',,', ',')
        
        # Remove trailing commas after property values
        import re
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Fix missing quotes around property names
        text = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)
        
        return text

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
        
        prompt = f"""You are an expert chef and meal planner. Your task is to create recipes using the available ingredients while following dietary preferences.

Input Ingredients:
{ingredients_text}

Dietary Preference: {preferences.dietary_preference.value if preferences.dietary_preference else 'None'}

Follow these steps carefully:

1. INGREDIENT ANALYSIS
- Parse and validate each ingredient line
- Format: Check if each line follows "quantity unit ingredient_name"
- List any ingredients that don't match the format
- Tag ingredients by category (protein, carb, vegetable, etc.)

2. DIETARY VALIDATION
- Check if ingredients align with {preferences.dietary_preference.value if preferences.dietary_preference else 'None'} requirements
- List any ingredients that violate dietary restrictions
- Suggest alternatives if needed

3. RECIPE IDEATION
- Consider common cuisine combinations
- Match protein-carb-vegetable ratios
- Ensure recipes are practical and achievable
- Tag each recipe by cuisine type and complexity

4. RECIPE GENERATION
Return ONLY a JSON array of recipes in this exact format, with NO additional text:
[
  {{
    "name": "Recipe Name",
    "cuisine_type": "Type of Cuisine",
    "complexity": "Easy/Medium/Hard",
    "description": "Brief description",
    "required_ingredients": [
      {{
        "quantity": "numeric amount",
        "unit": "measurement unit",
        "name": "ingredient name"
      }}
    ],
    "instructions": [
      "Step 1...",
      "Step 2..."
    ],
    "nutrition_check": {{
      "balanced": true,
      "concerns": []
    }}
  }}
]

5. SELF-VERIFICATION
For each recipe:
- Verify all required ingredients are available
- Check instruction completeness
- Validate dietary compliance
- Assess nutritional balance

6. ERROR HANDLING
If you encounter any issues:
- For missing crucial ingredients: Suggest alternatives
- For dietary conflicts: Explain the issue and propose modifications
- For complex recipes: Offer simpler variations
- For uncertain steps: Mark them as "requires verification"

7. FINAL OUTPUT
- Generate 2-3 recipes that best utilize the ingredients
- Each recipe must follow the exact JSON format above
- Include any warnings or suggestions as "notes" in the description

Remember to:
- Think step-by-step through each recipe
- Prioritize ingredients provided
- Consider cooking time and complexity
- Maintain dietary restrictions strictly
- Verify each step's feasibility

IMPORTANT: Return ONLY the JSON array with no additional text, markdown formatting, or explanation. Do not include any trailing commas in the JSON."""

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
                    print("Raw generated text:", generated_text)  # Debug log
                    
                    try:
                        # Clean and parse the JSON
                        cleaned_text = self.clean_json_text(generated_text)
                        print("Cleaned JSON text:", cleaned_text)  # Debug log
                        
                        recipes_data = json.loads(cleaned_text)
                        print("Parsed JSON:", recipes_data)  # Debug log
                        
                        # Convert to list if single recipe
                        if isinstance(recipes_data, dict):
                            recipes_data = [recipes_data]
                        
                        # Convert JSON to Recipe objects
                        recipes = []
                        for recipe_data in recipes_data:
                            try:
                                # Create Recipe object
                                recipe = Recipe(
                                    id=str(recipe_data.get("id", "")),
                                    name=recipe_data["name"],
                                    meal_type=recipe_data.get("meal_type", "main"),  # Default to main
                                    description=recipe_data.get("description", ""),
                                    required_ingredients=[
                                        Ingredient(
                                            name=ing["name"],
                                            quantity=float(ing["quantity"]) if isinstance(ing["quantity"], (int, float)) else float(ing["quantity"].split()[0]),
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
                                print(f"Error details: {str(e)}")
                                continue  # Skip this recipe and try the next one
                        
                        if not recipes:
                            raise Exception("No valid recipes could be created")
                        
                        # Store the generated recipes
                        self.last_generated_recipes = recipes
                        return recipes
                        
                    except json.JSONDecodeError as e:
                        print("JSON Parse Error. Position:", e.pos)
                        print("Line:", e.lineno, "Column:", e.colno)
                        print("Error message:", e.msg)
                        print("Text around error:", generated_text[max(0, e.pos-50):min(len(generated_text), e.pos+50)])
                        raise Exception(f"Failed to parse recipe JSON: {str(e)}")
                    
        except Exception as e:
            self.last_generated_recipes = []  # Clear on error
            raise Exception(f"Failed to generate recipes: {str(e)}") 