class MealPlanner {
  constructor() {
    this.apiUrl = "http://127.0.0.1:8000"; // Backend API URL
    this.apiKey = "";
    this.initializeElements();
    this.attachEventListeners();
    this.loadStoredApiKey();
  }

  initializeElements() {
    this.apiKeyInput = document.getElementById("apiKey");
    this.startDateInput = document.getElementById("startDate");
    this.dietaryPrefsSelect = document.getElementById("dietaryPrefs");
    this.ingredientsTextarea = document.getElementById("ingredients");
    this.generateButton = document.getElementById("generatePlan");
    this.loadingSpinner = document.getElementById("loadingSpinner");
    this.mealPlanResults = document.getElementById("mealPlanResults");
    this.mealPlanContainer = document.getElementById("mealPlanContainer");
    this.shoppingList = document.getElementById("shoppingList");
  }

  attachEventListeners() {
    this.generateButton.addEventListener("click", () =>
      this.generateMealPlan()
    );
    this.apiKeyInput.addEventListener("change", () => this.saveApiKey());
  }

  async loadStoredApiKey() {
    const result = await chrome.storage.sync.get(["geminiApiKey"]);
    if (result.geminiApiKey) {
      this.apiKeyInput.value = result.geminiApiKey;
      this.apiKey = result.geminiApiKey;
    }
  }

  async saveApiKey() {
    this.apiKey = this.apiKeyInput.value;
    await chrome.storage.sync.set({ geminiApiKey: this.apiKey });
  }

  async generateMealPlan() {
    if (!this.validateInputs()) return;

    this.showLoading(true);

    try {
      const mealPlan = await this.callBackendAPI();
      this.displayMealPlan(mealPlan);
    } catch (error) {
      console.error("Detailed error:", error);
      alert(`Error generating meal plan: ${error.message}`);
    }

    this.showLoading(false);
  }

  validateInputs() {
    if (!this.apiKey) {
      alert("Please enter your Gemini API key");
      return false;
    }
    if (!this.startDateInput.value) {
      alert("Please select a start date");
      return false;
    }
    if (!this.ingredientsTextarea.value.trim()) {
      alert("Please enter some ingredients");
      return false;
    }
    return true;
  }

  async callBackendAPI() {
    try {
      // Format ingredients as an array of strings
      const ingredients = this.ingredientsTextarea.value
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.length > 0);

      console.log("Sending request with data:", {
        raw_ingredients: ingredients,
        dietary_preference: this.dietaryPrefsSelect.value,
        api_key: "HIDDEN",
      });

      const response = await fetch(`${this.apiUrl}/api/generate-meal-plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          raw_ingredients: ingredients,
          dietary_preference: this.dietaryPrefsSelect.value,
          api_key: this.apiKey,
        }),
      });

      const responseData = await response.json();
      console.log("Response:", responseData);

      if (!response.ok) {
        let errorMessage = `API Error: ${response.status}`;
        if (responseData.detail) {
          errorMessage += ` - ${responseData.detail}`;
        } else if (typeof responseData === "object") {
          errorMessage += ` - ${JSON.stringify(responseData)}`;
        }
        throw new Error(errorMessage);
      }

      return responseData;
    } catch (error) {
      console.error("Full error object:", error);
      if (error.message.includes("Failed to fetch")) {
        throw new Error(
          "Cannot connect to the backend server. Please make sure the server is running at " +
            this.apiUrl
        );
      }
      throw error;
    }
  }

  displayMealPlan(mealPlan) {
    const date = new Date(mealPlan.date).toLocaleDateString();

    this.mealPlanContainer.innerHTML = `
      <h3>${date}</h3>
      <div class="meals">
        ${this.createMealHTML("Breakfast", mealPlan.breakfast)}
        ${this.createMealHTML("Lunch", mealPlan.lunch)}
        ${this.createMealHTML("Dinner", mealPlan.dinner)}
      </div>
    `;

    this.displayShoppingList(mealPlan.shopping_list);
    this.mealPlanResults.classList.remove("hidden");
  }

  createMealHTML(mealType, meal) {
    return `
      <div class="meal">
        <h4>${mealType}: ${meal.recipe.name}</h4>
        <p class="description">${meal.recipe.description}</p>
        <div class="ingredients">
          <h5>Using:</h5>
          <ul>
            ${meal.used_ingredients
              .map((ing) => `<li>${ing.quantity} ${ing.unit} ${ing.name}</li>`)
              .join("")}
          </ul>
          ${
            meal.missing_ingredients.length
              ? `
            <h5>Missing:</h5>
            <ul class="missing">
              ${meal.missing_ingredients
                .map(
                  (ing) => `<li>${ing.quantity} ${ing.unit} ${ing.name}</li>`
                )
                .join("")}
            </ul>
          `
              : ""
          }
        </div>
        <div class="instructions">
          <h5>Instructions:</h5>
          <ol>
            ${meal.recipe.instructions
              .map((step) => `<li>${step}</li>`)
              .join("")}
          </ol>
        </div>
      </div>
    `;
  }

  displayShoppingList(shoppingList) {
    this.shoppingList.innerHTML = `
      <ul>
        ${shoppingList
          .map((item) => `<li>${item.quantity} ${item.unit} ${item.name}</li>`)
          .join("")}
      </ul>
    `;
  }

  showLoading(show) {
    this.loadingSpinner.classList.toggle("hidden", !show);
    this.generateButton.disabled = show;
  }
}

// Initialize the app when the document is loaded
document.addEventListener("DOMContentLoaded", () => {
  new MealPlanner();
});
