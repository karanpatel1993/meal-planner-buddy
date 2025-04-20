class MealPlanner {
  constructor() {
    this.apiUrl = "http://127.0.0.1:8000"; // Backend API URL
    this.apiKey = "";
    this.savedRecipes = [];
    this.initializeElements();
    this.loadStoredApiKey().then(() => {
      this.attachEventListeners();
      this.loadSavedRecipes();
    });
  }

  initializeElements() {
    this.apiKeyInput = document.getElementById("apiKey");
    this.dietaryPrefsSelect = document.getElementById("dietaryPreference");
    this.ingredientsTextarea = document.getElementById("ingredients");
    this.generateButton = document.getElementById("generateButton");
    this.resultsDiv = document.getElementById("results");
    this.savedRecipesDiv = document.getElementById("savedRecipes");
    this.viewSavedButton = document.getElementById("viewSavedButton");
    this.messageDiv = document.getElementById("message");
  }

  attachEventListeners() {
    if (this.generateButton) {
      this.generateButton.addEventListener("click", () =>
        this.generateMealPlan()
      );
    }
    if (this.apiKeyInput) {
      this.apiKeyInput.addEventListener("change", () => this.saveApiKey());
    }
    if (this.viewSavedButton) {
      this.viewSavedButton.addEventListener("click", () =>
        this.toggleSavedRecipes()
      );
    }

    // Add event delegation for recipe cards
    document.addEventListener("click", (event) => {
      const target = event.target;

      // Handle save recipe button clicks
      if (target.matches(".save-recipe-button")) {
        const recipeId = target.dataset.recipeId;
        this.saveRecipe(recipeId);
      }

      // Handle delete recipe button clicks
      if (target.matches(".delete-recipe-button")) {
        const recipeIndex = target.dataset.recipeIndex;
        this.deleteRecipe(recipeIndex);
      }
    });
  }

  async loadStoredApiKey() {
    try {
      const result = await chrome.storage.sync.get(["geminiApiKey"]);
      if (result.geminiApiKey) {
        this.apiKey = result.geminiApiKey;
        if (this.apiKeyInput) {
          this.apiKeyInput.value = this.apiKey;
        }
      }
    } catch (error) {
      console.error("Error loading API key:", error);
    }
  }

  async saveApiKey() {
    try {
      this.apiKey = this.apiKeyInput.value.trim();
      await chrome.storage.sync.set({ geminiApiKey: this.apiKey });
      this.showMessage("API key saved successfully", "success");
    } catch (error) {
      console.error("Error saving API key:", error);
      this.showMessage("Failed to save API key", "error");
    }
  }

  async generateMealPlan() {
    if (!this.validateInputs()) return;

    this.showMessage("Generating meal plan...", "info");
    this.generateButton.disabled = true;

    try {
      const response = await this.callBackendAPI();
      console.log("Response from backend:", response);

      if (response && response.recipes && Array.isArray(response.recipes)) {
        this.displayRecipes(response.recipes);
        this.showMessage("Meal plan generated successfully!", "success");
      } else {
        console.error("Invalid response format:", response);
        this.showMessage(
          "Error: Received invalid response from server",
          "error"
        );
      }
    } catch (error) {
      console.error("Error generating meal plan:", error);
      this.showMessage(`Error: ${error.message}`, "error");
    } finally {
      this.generateButton.disabled = false;
    }
  }

  validateInputs() {
    if (!this.apiKey) {
      this.showMessage("Please enter your Gemini API key", "error");
      return false;
    }
    if (!this.ingredientsTextarea.value.trim()) {
      this.showMessage("Please enter some ingredients", "error");
      return false;
    }
    return true;
  }

  async callBackendAPI() {
    const ingredients = this.ingredientsTextarea.value
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);

    const dietaryPreference = this.dietaryPrefsSelect.value;
    const apiKey = this.apiKey;

    const requestData = {
      raw_ingredients: ingredients,
      dietary_preference: dietaryPreference,
      api_key: apiKey,
    };

    console.log("Sending request with data:", {
      ...requestData,
      api_key: "[HIDDEN]", // Hide API key in logs
      raw_ingredients: ingredients,
      dietary_preference: dietaryPreference,
    });

    try {
      console.log(
        "Making request to:",
        `${this.apiUrl}/api/generate-meal-plan`
      );

      const response = await fetch(`${this.apiUrl}/api/generate-meal-plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(requestData),
      });

      console.log("Response status:", response.status, response.statusText);
      console.log(
        "Response headers:",
        Object.fromEntries([...response.headers])
      );

      const responseText = await response.text();
      console.log("Raw response:", responseText);

      let responseData;
      try {
        responseData = JSON.parse(responseText);
        console.log("Parsed response data:", responseData);
      } catch (e) {
        console.error("Failed to parse response as JSON:", responseText);
        throw new Error(
          `Server returned invalid JSON response: ${responseText.substring(
            0,
            100
          )}...`
        );
      }

      if (!response.ok) {
        let errorMessage = "API Error";

        if (response.status === 422) {
          // Handle validation errors
          if (responseData.detail) {
            if (Array.isArray(responseData.detail)) {
              // Handle Pydantic validation errors
              errorMessage = `Validation Error: ${responseData.detail
                .map((err) => `${err.loc.join(".")} - ${err.msg}`)
                .join("; ")}`;
            } else {
              errorMessage = `Validation Error: ${responseData.detail}`;
            }
          }
        } else if (responseData.detail) {
          // Handle other errors with detail
          errorMessage = responseData.detail;
        } else if (responseData.message) {
          // Some APIs use 'message' instead of 'detail'
          errorMessage = responseData.message;
        } else if (responseData.error) {
          // Handle error field
          errorMessage = responseData.error;
        } else {
          // Fallback error message with status text
          errorMessage = `Server returned ${response.status} (${response.statusText})`;
        }

        console.error("API Error:", {
          status: response.status,
          statusText: response.statusText,
          data: responseData,
          error: errorMessage,
        });

        throw new Error(errorMessage);
      }

      if (!responseData || !responseData.recipes) {
        console.error("Invalid response format:", responseData);
        throw new Error("Server returned an invalid response format");
      }

      return responseData;
    } catch (error) {
      console.error("API call error details:", {
        message: error.message,
        stack: error.stack,
        name: error.name,
      });

      if (error.message.includes("Failed to fetch")) {
        throw new Error(
          "Cannot connect to the backend server. Please make sure the server is running at http://127.0.0.1:8000"
        );
      }

      // If it's already a handled error, rethrow it
      if (
        error.message.includes("Server returned") ||
        error.message.includes("Validation Error") ||
        error.message.includes("API Error")
      ) {
        throw error;
      }

      // For unhandled errors, provide a generic message but log the details
      throw new Error(
        "An error occurred while communicating with the server. Check the console for details."
      );
    }
  }

  displayRecipes(recipes) {
    if (!this.resultsDiv) return;

    if (!recipes || !Array.isArray(recipes)) {
      console.error("Invalid recipes data:", recipes);
      this.showMessage(
        "Error: Received invalid recipe data from server",
        "error"
      );
      return;
    }

    this.resultsDiv.innerHTML = `
      <h2>Generated Recipes</h2>
      ${recipes
        .map((recipe, index) => {
          if (!recipe) return "";

          const ingredients =
            recipe.required_ingredients || recipe.ingredients || [];
          const instructions = recipe.instructions || [];

          return `
          <div class="recipe-card">
            <h3>${recipe.name || "Unnamed Recipe"}</h3>
            ${recipe.description ? `<p>${recipe.description}</p>` : ""}
            <h4>Ingredients:</h4>
            <ul>
              ${ingredients
                .map((ing) => {
                  if (!ing) return "";
                  return `<li>${ing.quantity} ${ing.unit} ${ing.name}</li>`;
                })
                .join("")}
            </ul>
            <h4>Instructions:</h4>
            <ol>
              ${instructions
                .map((step) => {
                  if (!step) return "";
                  return `<li>${step}</li>`;
                })
                .join("")}
            </ol>
            <button class="save-button save-recipe-button" data-recipe-id="${index}">
              Save Recipe
            </button>
          </div>
        `;
        })
        .join("")}
    `;
  }

  showMessage(message, type = "info") {
    if (!this.messageDiv) return;

    this.messageDiv.textContent = message;
    this.messageDiv.className = `message ${type}`;
    this.messageDiv.style.display = "block";

    // Hide message after 5 seconds if it's a success message
    if (type === "success") {
      setTimeout(() => {
        this.messageDiv.style.display = "none";
      }, 5000);
    }
  }

  async loadSavedRecipes() {
    try {
      const response = await fetch(`${this.apiUrl}/api/saved-recipes`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      this.savedRecipes = data;
    } catch (error) {
      console.error("Error loading saved recipes:", error);
      this.savedRecipes = [];
    }
  }

  async saveRecipe(recipeId) {
    try {
      const response = await fetch(
        `${this.apiUrl}/api/save-recipe/${recipeId}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to save recipe");
      }

      await this.loadSavedRecipes();
      this.showMessage("Recipe saved successfully!", "success");
    } catch (error) {
      this.showMessage(`Error saving recipe: ${error.message}`, "error");
    }
  }

  toggleSavedRecipes() {
    const inputSection = document.getElementById("inputSection");
    const results = document.getElementById("results");
    const savedRecipes = document.getElementById("savedRecipes");
    const viewSavedButton = document.getElementById("viewSavedButton");

    if (savedRecipes.style.display === "none") {
      inputSection.style.display = "none";
      results.style.display = "none";
      savedRecipes.style.display = "block";
      viewSavedButton.textContent = "Back to Generator";
      this.displaySavedRecipes();
    } else {
      inputSection.style.display = "block";
      results.style.display = "block";
      savedRecipes.style.display = "none";
      viewSavedButton.textContent = "View Saved Recipes";
    }
  }

  displaySavedRecipes() {
    const savedRecipesDiv = document.getElementById("savedRecipes");
    savedRecipesDiv.innerHTML = "<h2>Saved Recipes</h2>";

    if (this.savedRecipes.length === 0) {
      savedRecipesDiv.innerHTML += "<p>No saved recipes yet.</p>";
      return;
    }

    this.savedRecipes.forEach((recipe, index) => {
      const recipeCard = document.createElement("div");
      recipeCard.className = "recipe-card";
      recipeCard.innerHTML = `
        <h3>${recipe.recipe.name || "Unnamed Recipe"}</h3>
        <p><strong>Ingredients:</strong></p>
        <p>${recipe.recipe.ingredients}</p>
        <p><strong>Instructions:</strong></p>
        <p>${recipe.recipe.instructions}</p>
        <button class="save-button delete-recipe-button" data-recipe-index="${index}">Delete</button>
      `;
      savedRecipesDiv.appendChild(recipeCard);
    });
  }

  deleteRecipe(index) {
    this.savedRecipes.splice(index, 1);
    this.saveMealToStorage();
    this.displaySavedRecipes();
    this.showMessage("Recipe deleted successfully", "success");
  }

  saveMealToStorage() {
    localStorage.setItem("savedRecipes", JSON.stringify(this.savedRecipes));
  }
}

// Initialize the app when the document is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.mealPlanner = new MealPlanner();
});
