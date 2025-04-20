# Meal Planner Chrome Extension

A Chrome extension that helps you generate meal plans based on available ingredients using Google's Gemini AI. The extension suggests recipes that make the best use of your ingredients while respecting your dietary preferences.

## System Architecture

The meal planner is built on four core modules that work together to provide intelligent meal planning capabilities:

### 1. Perception Module (LLM)

- Powered by Google's Gemini AI
- Analyzes user inputs and ingredients
- Understands dietary preferences and constraints
- Generates creative and practical recipe suggestions
- Validates ingredient combinations and proportions
- Located in `backend/app/perception.py`

### 2. Memory Module

- Manages persistent storage of recipes
- Handles saving and retrieving favorite recipes
- Maintains user preferences and settings
- Prevents duplicate recipe suggestions
- Enables recipe history tracking
- Located in `backend/app/memory.py`

### 3. Decision-Making Module

- Evaluates recipe suitability based on:
  - Available ingredients
  - Dietary restrictions
  - Nutritional balance
  - Preparation complexity
- Prioritizes recipes based on ingredient utilization
- Ensures recipe variety and balance
- Located in `backend/app/decision.py`

### 4. Action Module

- Executes the recipe generation process
- Handles API interactions and requests
- Manages user interface updates
- Processes user actions (save/delete recipes)
- Coordinates between other modules
- Located in `backend/app/action.py`

## Features

- **AI-Powered Recipe Generation**: Uses Google's Gemini AI to create personalized recipes
- **Ingredient-Based Planning**: Generate recipes based on ingredients you have
- **Dietary Preferences**: Supports various dietary preferences:
  - Vegetarian
  - Vegan
  - Keto
  - Paleo
- **Recipe Management**:
  - Save favorite recipes
  - View saved recipes
  - Delete saved recipes
- **User-Friendly Interface**:
  - Clean, modern design
  - Tabbed interface for generating and viewing saved recipes
  - Clear error messages and loading states
- **Secure API Key Management**:
  - Secure storage of Gemini API key
  - Hidden API key display with show/hide toggle

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js and npm (for development)
- Google Chrome browser
- Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   - Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

The backend server will run at `http://127.0.0.1:8000`

### Chrome Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the `chrome-extension` directory
4. The extension icon should appear in your Chrome toolbar

## Usage

1. **First-Time Setup**:

   - Click the extension icon
   - Enter your Gemini API key in the settings
   - The API key will be securely saved for future use

2. **Generating Meal Plans**:

   - Enter your available ingredients (one per line)
   - Format: `quantity unit name` (e.g., "2 cups rice")
   - Select your dietary preference
   - Click "Generate Meal Plan"

3. **Managing Recipes**:
   - Click "Save Recipe" on any generated recipe to save it
   - Switch to the "Saved Recipes" tab to view saved recipes
   - Use the "Delete Recipe" button to remove saved recipes

## API Endpoints

The backend provides the following endpoints:

- `POST /api/generate-meal-plan`: Generate recipes based on ingredients
- `GET /api/saved-recipes`: Get all saved recipes
- `POST /api/save-recipe/{recipe_id}`: Save a recipe
- `DELETE /api/delete-recipe/{recipe_id}`: Delete a saved recipe

## Error Handling

The extension includes comprehensive error handling for:

- Backend server connection issues
- Invalid API keys
- Missing or invalid ingredients
- Recipe saving/deletion errors
- API rate limiting

## Development

### Project Structure

```
meal-planner-buddy/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── perception.py
│   └── requirements.txt
└── chrome-extension/
    ├── manifest.json
    ├── popup.html
    ├── popup.js
    └── icons/
```

### Backend Development

The backend is built with:

- **FastAPI**: Modern web framework for building APIs

  - High performance and automatic API documentation
  - Built-in support for async operations
  - OpenAPI (Swagger) integration

- **Pydantic**: Data validation using Python type annotations

  - Robust request/response model validation
  - Automatic JSON schema generation
  - Models:
    - `MealPlanRequest`: Validates ingredient inputs and preferences
    - `Recipe`: Ensures consistent recipe structure
    - `Ingredient`: Validates ingredient quantities and units
    - `UserPreferences`: Handles dietary preferences and API settings
  - Type safety and automatic data conversion
  - Integration with FastAPI for request/response validation

- **Google's Gemini AI**: Advanced language model for recipe generation
  - Creative recipe suggestions
  - Natural language understanding
  - Context-aware responses

### Frontend Development

The Chrome extension is built with:

- Vanilla JavaScript
- Chrome Extension APIs
- Modern CSS with CSS Variables

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for powering the recipe generation
- FastAPI for the backend framework
- Chrome Extensions API for making the frontend possible
