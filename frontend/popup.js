class MealPlanner {
  constructor() {
    this.apiUrl = "http://localhost:8000"; // Update this with your deployed API URL
    this.initializeElements();
    this.attachEventListeners();
  }

  initializeElements() {
    this.startDateInput = document.getElementById("startDate");
    this.dietaryPrefsSelect = document.getElementById("dietaryPrefs");
    this.ingredientsTextarea = document.getElementById("ingredients");
    this.excludedIngredientsTextarea = document.getElementById(
      "excludedIngredients"
    );
    this.maxPrepTimeInput = document.getElementById("maxPrepTime");
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
    const response = await fetch(`${this.apiUrl}/api/generate-meal-plan`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        raw_ingredients: this.ingredientsTextarea.value
          .split("\n")
          .filter((line) => line.trim()),
        dietary_preference: this.dietaryPrefsSelect.value,
        max_preparation_time: this.maxPrepTimeInput.value
          ? parseInt(this.maxPrepTimeInput.value)
          : null,
        excluded_ingredients: this.excludedIngredientsTextarea.value
          .split("\n")
          .filter((line) => line.trim()),
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`API Error: ${response.status} - ${errorData.detail}`);
    }

    return await response.json();
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
