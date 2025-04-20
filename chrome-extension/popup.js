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
    this.generateTab = document.getElementById("generateTab");
    this.savedTab = document.getElementById("savedTab");
    this.inputSection = document.getElementById("inputSection");
    this.messageDiv = document.getElementById("message");
    this.togglePasswordButton = document.getElementById("togglePassword");
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

    // Tab switching
    if (this.generateTab) {
      this.generateTab.addEventListener("click", () => this.showGenerateTab());
    }
    if (this.savedTab) {
      this.savedTab.addEventListener("click", () => this.showSavedTab());
    }

    // Add event delegation for recipe cards
    document.addEventListener("click", (event) => {
      const target = event.target;

      if (target.matches(".save-recipe-button")) {
        const recipeId = target.dataset.recipeId;
        this.saveRecipe(recipeId);
      }

      if (target.matches(".delete-recipe-button")) {
        const recipeId = target.dataset.recipeId;
        if (!recipeId) {
          console.error("No recipe ID found for delete button");
          this.showMessage(
            "Error: Could not identify recipe to delete",
            "error"
          );
          return;
        }
        this.deleteRecipe(recipeId);
      }
    });

    if (this.togglePasswordButton) {
      this.togglePasswordButton.addEventListener("click", () =>
        this.togglePasswordVisibility()
      );
    }
  }

  showGenerateTab() {
    this.generateTab.classList.add("active");
    this.savedTab.classList.remove("active");
    this.inputSection.style.display = "block";
    this.resultsDiv.style.display = "block";
    this.savedRecipesDiv.style.display = "none";
  }

  showSavedTab() {
    this.generateTab.classList.remove("active");
    this.savedTab.classList.add("active");
    this.inputSection.style.display = "none";
    this.resultsDiv.style.display = "none";
    this.savedRecipesDiv.style.display = "block";
    this.displaySavedRecipes();
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

    // Store the current recipes in memory
    this._currentRecipes = recipes;
    console.log("Stored current recipes:", this._currentRecipes);

    this.resultsDiv.innerHTML = `
      <div class="container">
        <h2>Generated Recipes</h2>
        ${recipes
          .map((recipe, index) => {
            if (!recipe) return "";

            const ingredients =
              recipe.required_ingredients || recipe.ingredients || [];
            const instructions = recipe.instructions || [];

            // Check if this recipe is already saved
            const isAlreadySaved = this.savedRecipes.some(
              (saved) =>
                saved.recipe.name === recipe.name &&
                JSON.stringify(saved.recipe.required_ingredients) ===
                  JSON.stringify(ingredients)
            );

            return `
            <div class="recipe-card">
              <h3>${recipe.name || "Unnamed Recipe"}</h3>
              ${recipe.description ? `<p>${recipe.description}</p>` : ""}
              <div class="recipe-details">
                <h4>Ingredients:</h4>
                <ul>
                  ${ingredients
                    .map(
                      (ing) =>
                        `<li>${ing.quantity} ${ing.unit} ${ing.name}</li>`
                    )
                    .join("")}
                </ul>
                <h4>Instructions:</h4>
                <ol>
                  ${instructions.map((step) => `<li>${step}</li>`).join("")}
                </ol>
                <button class="save-button save-recipe-button" 
                  data-recipe-id="${index}"
                  ${isAlreadySaved ? "disabled" : ""}
                  style="${
                    isAlreadySaved
                      ? "background-color: #ccc; cursor: not-allowed;"
                      : ""
                  }">
                  ${isAlreadySaved ? "Already Saved" : "Save Recipe"}
                </button>
              </div>
            </div>
          `;
          })
          .join("")}
      </div>
    `;
  }

  showMessage(message, type = "info") {
    if (!this.messageDiv) return;

    this.messageDiv.textContent = message;
    this.messageDiv.className = `message ${type}`;
    this.messageDiv.style.display = "block";

    // Hide message after 5 seconds if it's a success or info message
    if (type === "success" || type === "info") {
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
      console.log("Loaded saved recipes:", data);
      this.savedRecipes = data;
      this.displaySavedRecipes();
    } catch (error) {
      console.error("Error loading saved recipes:", error);
      this.savedRecipes = [];
      this.showMessage("Failed to load saved recipes", "error");
    }
  }

  async saveRecipe(recipeId) {
    try {
      console.log("Attempting to save recipe with ID:", recipeId);
      console.log("Current recipes:", this._currentRecipes);

      // Get the recipe data from the current results
      const recipes = this._currentRecipes;
      if (!recipes || !Array.isArray(recipes)) {
        throw new Error("No recipes available");
      }

      const recipeToSave = recipes[recipeId];
      console.log("Recipe to save:", recipeToSave);

      if (!recipeToSave) {
        throw new Error("Recipe not found");
      }

      // Check if recipe is already saved
      const isDuplicate = this.savedRecipes.some(
        (saved) =>
          saved.recipe.name === recipeToSave.name &&
          JSON.stringify(saved.recipe.required_ingredients) ===
            JSON.stringify(recipeToSave.required_ingredients)
      );

      if (isDuplicate) {
        this.showMessage(
          "This recipe is already in your saved recipes",
          "info"
        );
        return;
      }

      // Send the recipe ID along with the recipe data
      const response = await fetch(
        `${this.apiUrl}/api/save-recipe/${recipeId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(recipeToSave),
        }
      );

      const responseText = await response.text();
      console.log("Save recipe response:", responseText);

      let data;
      try {
        data = JSON.parse(responseText);
      } catch (e) {
        console.error("Failed to parse response:", e);
        throw new Error("Invalid response from server");
      }

      if (!response.ok) {
        throw new Error(data.detail || "Failed to save recipe");
      }

      await this.loadSavedRecipes(); // Reload the saved recipes from backend
      this.showMessage("Recipe saved successfully!", "success");
    } catch (error) {
      console.error("Save recipe error:", error);
      this.showMessage(`Error saving recipe: ${error.message}`, "error");
    }
  }

  async deleteRecipe(recipeId) {
    try {
      console.log("Attempting to delete recipe with ID:", recipeId);
      console.log("Current saved recipes:", this.savedRecipes);

      // Find the recipe in the saved recipes array
      const recipeIndex = parseInt(recipeId, 10);
      if (isNaN(recipeIndex)) {
        throw new Error("Invalid recipe ID");
      }

      console.log("Deleting recipe at index:", recipeIndex);

      const response = await fetch(
        `${this.apiUrl}/api/delete-recipe/${recipeIndex}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      const responseText = await response.text();
      console.log("Delete recipe response:", responseText);

      if (!response.ok) {
        let errorMessage;
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || "Failed to delete recipe";
        } catch (e) {
          errorMessage = "Failed to delete recipe";
        }
        throw new Error(errorMessage);
      }

      await this.loadSavedRecipes(); // Reload the saved recipes from backend
      this.showMessage("Recipe deleted successfully", "success");
    } catch (error) {
      console.error("Delete recipe error:", error);
      this.showMessage(`Error deleting recipe: ${error.message}`, "error");
    }
  }

  getCurrentRecipes() {
    // Store the current recipes in memory
    return this._currentRecipes || [];
  }

  displaySavedRecipes() {
    if (!this.savedRecipesDiv) return;

    if (!this.savedRecipes || this.savedRecipes.length === 0) {
      this.savedRecipesDiv.innerHTML = `
        <div class="container">
          <h2>Saved Recipes</h2>
          <p style="text-align: center; color: #666;">No saved recipes yet.</p>
        </div>
      `;
      return;
    }

    console.log("Displaying saved recipes:", this.savedRecipes);

    this.savedRecipesDiv.innerHTML = `
      <div class="container">
        <h2>Saved Recipes</h2>
        ${this.savedRecipes
          .map((saved, index) => {
            console.log("Processing recipe:", saved);
            return `
            <div class="recipe-card">
              <h3>${saved.recipe.name || "Unnamed Recipe"}</h3>
              ${
                saved.recipe.description
                  ? `<p>${saved.recipe.description}</p>`
                  : ""
              }
              <div class="recipe-details">
                <h4>Ingredients:</h4>
                <ul>
                  ${saved.recipe.required_ingredients
                    .map(
                      (ing) =>
                        `<li>${ing.quantity} ${ing.unit} ${ing.name}</li>`
                    )
                    .join("")}
                </ul>
                <h4>Instructions:</h4>
                <ol>
                  ${saved.recipe.instructions
                    .map((step) => `<li>${step}</li>`)
                    .join("")}
                </ol>
                <button class="save-button delete-recipe-button" data-recipe-id="${index}">
                  Delete Recipe
                </button>
              </div>
            </div>
          `;
          })
          .join("")}
      </div>
    `;
  }

  togglePasswordVisibility() {
    const type = this.apiKeyInput.type === "password" ? "text" : "password";
    this.apiKeyInput.type = type;
    this.togglePasswordButton.textContent =
      type === "password" ? "Show" : "Hide";
  }
}

// Initialize the app when the document is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.mealPlanner = new MealPlanner();
});
