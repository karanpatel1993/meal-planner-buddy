class MealPlanner {
  constructor() {
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
      const mealPlan = await this.callGeminiAPI();
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

  async callGeminiAPI() {
    const prompt = this.constructPrompt();

    try {
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${this.apiKey}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            contents: [
              {
                parts: [
                  {
                    text: prompt,
                  },
                ],
              },
            ],
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          `API Error: ${response.status} - ${JSON.stringify(errorData)}`
        );
      }

      const data = await response.json();
      return this.parseMealPlanResponse(data);
    } catch (error) {
      console.error("API call details:", error);
      throw error;
    }
  }

  constructPrompt() {
    const ingredients = this.ingredientsTextarea.value;
    const dietaryPrefs = this.dietaryPrefsSelect.value;
    const startDate = this.startDateInput.value;

    return `Generate a one-day Indian meal plan for ${startDate} with the following parameters:
    Available Ingredients: ${ingredients}
    Dietary Preferences: ${dietaryPrefs}
    
    Please provide authentic Indian cuisine for:
    1. Breakfast: Traditional Indian breakfast dishes (e.g., idli, dosa, poha, paratha)
    2. Lunch: Complete Indian thali with main dish, dal, rice/roti, and accompaniments
    3. Dinner: Balanced Indian dinner menu
    
    For each meal:
    - Provide authentic Indian recipe names (with English translations if needed)
    - List which ingredients from the provided list will be used
    - Highlight any missing ingredients needed for each recipe
    - Include brief cooking instructions
    
    Format the response as JSON with this structure:
    {
      "mealPlan": [
        {
          "date": "YYYY-MM-DD",
          "meals": {
            "breakfast": {
              "recipe": "Recipe name",
              "description": "Brief description",
              "usedIngredients": ["ingredient1", "ingredient2"],
              "missingIngredients": ["ingredient3", "ingredient4"],
              "instructions": "Brief cooking steps"
            },
            "lunch": {...},
            "dinner": {...}
          }
        }
      ],
      "shoppingList": ["ingredient1", "ingredient2"]
    }`;
  }

  parseMealPlanResponse(data) {
    try {
      console.log("Raw API response:", data);

      if (
        !data.candidates ||
        !data.candidates[0] ||
        !data.candidates[0].content
      ) {
        console.error("Unexpected API response structure:", data);
        throw new Error("Invalid API response structure");
      }

      let text = data.candidates[0].content.parts[0].text;

      // Clean up the response by removing markdown code blocks
      text = text
        .replace(/```json\n?/g, "")
        .replace(/```/g, "")
        .trim();
      console.log("Cleaned text to parse:", text);

      const parsedData = JSON.parse(text);
      console.log("Parsed data:", parsedData);

      // Validate the required structure
      if (!parsedData.mealPlan || !parsedData.shoppingList) {
        throw new Error("Response missing required fields");
      }

      return parsedData;
    } catch (error) {
      console.error("Parse error details:", error);
      throw new Error(`Failed to parse API response: ${error.message}`);
    }
  }

  displayMealPlan(mealPlan) {
    this.mealPlanContainer.innerHTML = "";

    mealPlan.mealPlan.forEach((day) => {
      const dayElement = this.createDayElement(day);
      this.mealPlanContainer.appendChild(dayElement);
    });

    this.displayShoppingList(mealPlan.shoppingList);
    this.mealPlanResults.classList.remove("hidden");
  }

  createDayElement(day) {
    const dayDiv = document.createElement("div");
    dayDiv.className = "day-plan";

    const date = new Date(day.date).toLocaleDateString();
    dayDiv.innerHTML = `
      <h3>${date}</h3>
      <div class="meals">
        ${this.createMealHTML("Breakfast", day.meals.breakfast)}
        ${this.createMealHTML("Lunch", day.meals.lunch)}
        ${this.createMealHTML("Dinner", day.meals.dinner)}
      </div>
    `;

    return dayDiv;
  }

  createMealHTML(mealType, meal) {
    return `
      <div class="meal">
        <h4>${mealType}: ${meal.recipe}</h4>
        <p class="description">${meal.description}</p>
        <p>Using: ${meal.usedIngredients.join(", ")}</p>
        ${
          meal.missingIngredients.length
            ? `<p class="missing-ingredient">Missing: ${meal.missingIngredients.join(
                ", "
              )}</p>`
            : ""
        }
        <div class="instructions">
          <h5>Cooking Instructions:</h5>
          <p>${meal.instructions}</p>
        </div>
      </div>
    `;
  }

  displayShoppingList(shoppingList) {
    this.shoppingList.innerHTML = `
      <ul>
        ${shoppingList.map((item) => `<li>${item}</li>`).join("")}
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
