# Indian Meal Planner

A Chrome extension with a Python backend for generating daily Indian meal plans based on available ingredients and dietary preferences.

## Architecture

The project uses a client-server architecture:

1. Backend: FastAPI service that handles meal planning logic
2. Frontend: Chrome extension that provides the user interface

## Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

The backend server will start at `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

### Features

- Modular Python backend with:
  - Input parsing and recipe generation
  - Memory management for avoiding meal repetition
  - Intelligent meal selection based on preferences
  - Shopping list generation
- RESTful API endpoints
- CORS support for Chrome extension
- Automatic API documentation with Swagger UI

## Frontend Setup

1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (toggle in top right)
4. Click "Load unpacked"
5. Select the `frontend` directory

### Features

- User-friendly interface for:
  - Inputting available ingredients
  - Setting dietary preferences
  - Specifying maximum preparation time
  - Excluding unwanted ingredients
- Real-time meal plan generation
- Detailed recipe display with:
  - Ingredients used/missing
  - Step-by-step instructions
  - Consolidated shopping list

## API Endpoints

### POST /api/generate-meal-plan

Generate a daily meal plan based on:

- List of available ingredients
- Dietary preferences
- Maximum preparation time
- Excluded ingredients

### GET /api/health

Health check endpoint for monitoring the service.

## Requirements

### Backend

- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic
- Python-dateutil
- Python-dotenv
- Google Generative AI (for future LLM integration)

### Frontend

- Google Chrome browser
- Internet connection to backend service

## Development

1. Start the backend server:

```bash
cd backend
uvicorn app.main:app --reload
```

2. Load the Chrome extension from the `frontend` directory.

3. The extension will connect to the local backend service at `http://localhost:8000`.

## Deployment

For production:

1. Deploy the backend to a cloud service (e.g., Heroku, AWS, GCP)
2. Update the `apiUrl` in `frontend/popup.js` to point to your deployed backend
3. Package and distribute the Chrome extension
