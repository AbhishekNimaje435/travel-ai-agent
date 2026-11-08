// ---------- Sidebar navigation: switch between pages ----------
const navButtons = document.querySelectorAll(".nav-item");
const pages = document.querySelectorAll(".page");

function showPage(pageName) {
  pages.forEach((page) => {
    page.hidden = page.dataset.page !== pageName;
  });
  navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.nav === pageName);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    showPage(button.dataset.nav);
  });
});

// ---------- Tabs (Flights, Hotels, Places, Itinerary) ----------
const tabButtons = document.querySelectorAll(".tab-button");

tabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const selectedTab = button.dataset.tab;

    tabButtons.forEach((other) => other.classList.remove("active"));
    button.classList.add("active");

    document.querySelectorAll(".tab-panel").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `panel-${selectedTab}`);
    });

    if (selectedTab === "hotels") {
      loadHotelCitiesOnce();
    }
    if (selectedTab === "places") {
      loadPlaceOptionsOnce();
    }
    if (selectedTab === "itinerary") {
      loadItineraryOptionsOnce();
    }
  });
});

// ---------- Default dates: today + 7 and today + 9 ----------
function formatDateForInput(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function setupDateInputs() {
  const startInput = document.getElementById("start-date");
  const endInput = document.getElementById("end-date");
  const today = new Date();

  const startDate = new Date(today);
  startDate.setDate(today.getDate() + 7);
  const endDate = new Date(today);
  endDate.setDate(today.getDate() + 9);

  startInput.min = formatDateForInput(today);
  endInput.min = formatDateForInput(today);
  startInput.value = formatDateForInput(startDate);
  endInput.value = formatDateForInput(endDate);
}

// ---------- Advanced preferences helpers ----------
function getCheckedValues(name) {
  return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map(
    (input) => input.value
  );
}

const starsInput = document.getElementById("minimum-stars");
const starsValue = document.getElementById("stars-value");
starsInput.addEventListener("input", () => {
  starsValue.textContent = starsInput.value;
});

// ---------- Search form: call the backend (Groq agent) ----------
const searchForm = document.getElementById("search-form");
const searchButton = document.getElementById("search-button");
const resultBox = document.getElementById("result-box");
const loadingBox = document.getElementById("loading");
const resultText = document.getElementById("result-text");
const saveTripButton = document.getElementById("save-trip-button");
const downloadJsonButton = document.getElementById("download-json-button");

let currentPlan = null;
let lastRequestBody = null;

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const sourceCity = document.getElementById("source-city").value.trim();
  const destinationCity = document.getElementById("destination-city").value.trim();
  const startDate = document.getElementById("start-date").value;
  const endDate = document.getElementById("end-date").value;

  if (!sourceCity || !destinationCity || !startDate || !endDate) {
    showToast("Please fill in all fields");
    return;
  }
  if (sourceCity.toLowerCase() === destinationCity.toLowerCase()) {
    showToast("From and To cities should be different");
    return;
  }
  if (endDate < startDate) {
    showToast("End date cannot be before the start date");
    return;
  }

  const requestBody = {
    source_city: sourceCity,
    destination_city: destinationCity,
    start_date: startDate,
    end_date: endDate,
    travellers: parseInt(document.getElementById("travellers").value, 10) || 1,
    flight_preference: document.getElementById("flight-preference").value,
    include_return_flight: document.getElementById("include-return").checked,
    minimum_stars: parseInt(starsInput.value, 10),
    maximum_hotel_price: parseInt(document.getElementById("max-hotel-price").value, 10),
    daily_local_expense: parseInt(document.getElementById("daily-expense").value, 10),
    total_budget: parseInt(document.getElementById("total-budget").value, 10),
    amenities: getCheckedValues("amenity"),
    interests: getCheckedValues("interest"),
    extra_requirements: document.getElementById("extra-requirements").value.trim(),
    model_name: "openai/gpt-oss-20b",
    temperature: 0.2,
    enabled_tools: [
      "search_flights",
      "search_hotels",
      "search_places",
      "get_weather_forecast",
      "estimate_trip_budget",
    ],
  };

  lastRequestBody = requestBody;
  showResultLoading();

  try {
    const response = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });

    const data = await response.json();

    if (!response.ok) {
      showResultError(data.detail || "Could not generate the trip plan.");
      return;
    }

    showResultText(data.plan);
  } catch (networkError) {
    showResultError("Could not connect to the server. Please try again in a moment.");
  } finally {
    searchButton.disabled = false;
    searchButton.textContent = "🔍 Plan my trip →";
  }
});

function showResultLoading() {
  resultBox.hidden = false;
  loadingBox.hidden = false;
  resultText.innerHTML = "";
  resultText.classList.remove("error");
  saveTripButton.hidden = true;
  downloadJsonButton.hidden = true;
  currentPlan = null;
  searchButton.disabled = true;
  searchButton.textContent = "Planning...";
  resultBox.scrollIntoView({ behavior: "smooth", block: "start" });
}

function showResultText(planText) {
  loadingBox.hidden = true;
  const htmlFromMarkdown = marked.parse(planText);
  resultText.innerHTML = DOMPurify.sanitize(htmlFromMarkdown);

  // Remember the plan so "Save trip" can store it
  currentPlan = {
    source: document.getElementById("source-city").value.trim(),
    destination: document.getElementById("destination-city").value.trim(),
    startDate: document.getElementById("start-date").value,
    endDate: document.getElementById("end-date").value,
    planText: planText,
  };
  saveTripButton.hidden = false;
  saveTripButton.textContent = "💾 Save trip";
  saveTripButton.disabled = false;
  downloadJsonButton.hidden = false;
}

function showResultError(message) {
  loadingBox.hidden = true;
  resultText.textContent = message;
  resultText.classList.add("error");
}

// ---------- Save trip button ----------
saveTripButton.addEventListener("click", () => {
  if (!currentPlan) return;

  addTrip(
    {
      source: currentPlan.source,
      destination: currentPlan.destination,
      startDate: currentPlan.startDate,
      endDate: currentPlan.endDate,
    },
    currentPlan.planText
  );

  saveTripButton.disabled = true;
  saveTripButton.textContent = "✅ Saved";
  showToast("Trip saved to My Trips");
});

// ---------- Download JSON: calls /api/plan/json with the last form values ----------
downloadJsonButton.addEventListener("click", async () => {
  if (!lastRequestBody) return;

  const originalText = downloadJsonButton.textContent;
  downloadJsonButton.disabled = true;
  downloadJsonButton.textContent = "Preparing JSON...";

  try {
    const response = await fetch("/api/plan/json", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lastRequestBody),
    });
    const data = await response.json();

    if (!response.ok) {
      showToast(data.detail || "JSON could not be generated");
      return;
    }

    const jsonText = JSON.stringify(data.trip, null, 2);
    const blob = new Blob([jsonText], { type: "application/json" });
    const fileUrl = URL.createObjectURL(blob);

    const downloadLink = document.createElement("a");
    downloadLink.href = fileUrl;
    downloadLink.download = `trip_${lastRequestBody.source_city}_${lastRequestBody.destination_city}_${lastRequestBody.start_date}.json`;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    downloadLink.remove();
    URL.revokeObjectURL(fileUrl);

    showToast("JSON downloaded");
  } catch (error) {
    showToast("Could not connect to the server");
  } finally {
    downloadJsonButton.disabled = false;
    downloadJsonButton.textContent = originalText;
  }
});

// ---------- Hotels tab: loads from /api/hotels (no Groq call) ----------
const hotelCitySelect = document.getElementById("hotel-city");
const hotelStarsInput = document.getElementById("hotel-stars");
const hotelStarsValue = document.getElementById("hotel-stars-value");
const hotelMaxPriceInput = document.getElementById("hotel-max-price");
const hotelSortSelect = document.getElementById("hotel-sort");
const hotelGrid = document.getElementById("hotel-grid");
const hotelCount = document.getElementById("hotel-count");

let hotelCitiesLoaded = false;

async function loadHotelCitiesOnce() {
  if (hotelCitiesLoaded) return;
  try {
    const response = await fetch("/api/cities");
    const data = await response.json();
    hotelCitySelect.innerHTML = data.cities
      .map((city) => `<option value="${city}">${city}</option>`)
      .join("");
    hotelCitiesLoaded = true;
    loadHotels();
  } catch (error) {
    showToast("Could not load cities");
  }
}

async function loadHotels() {
  const city = hotelCitySelect.value;
  if (!city) return;

  const params = new URLSearchParams({
    city: city,
    min_stars: hotelStarsInput.value,
    max_price: hotelMaxPriceInput.value || "20000",
    sort_by: hotelSortSelect.value,
  });

  try {
    const response = await fetch(`/api/hotels?${params.toString()}`);
    const data = await response.json();
    renderHotels(data.hotels);
    hotelCount.textContent = `${data.count} hotel(s) found in ${city}`;
  } catch (error) {
    hotelGrid.innerHTML = `<div class="hotel-empty">Could not load hotels.</div>`;
  }
}

function renderHotels(hotels) {
  if (hotels.length === 0) {
    hotelGrid.innerHTML = `<div class="hotel-empty">No hotels match this filter. Try more stars or a higher price.</div>`;
    return;
  }

  hotelGrid.innerHTML = hotels
    .map(
      (hotel, index) => `
      <div class="hotel-card" style="animation-delay: ${index * 0.08}s">
        ${favoriteButtonHtml("hotel", hotel)}
        <div class="hotel-card-header">
          <div class="hotel-name">${hotel.name}</div>
          <div class="hotel-stars">${"★".repeat(hotel.stars)}</div>
        </div>
        <div class="hotel-price">₹${hotel.price_per_night.toLocaleString("en-IN")} <small>/ night</small></div>
        <div class="hotel-amenities">
          ${hotel.amenities.map((amenity) => `<span class="amenity-tag">${amenity}</span>`).join("")}
        </div>
      </div>`
    )
    .join("");
}

hotelCitySelect.addEventListener("change", loadHotels);
hotelSortSelect.addEventListener("change", loadHotels);
hotelMaxPriceInput.addEventListener("change", loadHotels);
hotelStarsInput.addEventListener("input", () => {
  hotelStarsValue.textContent = hotelStarsInput.value;
});
hotelStarsInput.addEventListener("change", loadHotels);

// ---------- Places tab: loads from /api/places (no Groq call) ----------
const placeCitySelect = document.getElementById("place-city");
const placeTypeSelect = document.getElementById("place-type");
const placeRatingInput = document.getElementById("place-rating");
const placeRatingValue = document.getElementById("place-rating-value");
const placeSortSelect = document.getElementById("place-sort");
const placeGrid = document.getElementById("place-grid");
const placeCount = document.getElementById("place-count");

let placeOptionsLoaded = false;

async function loadPlaceOptionsOnce() {
  if (placeOptionsLoaded) return;
  try {
    const response = await fetch("/api/place-options");
    const data = await response.json();

    placeCitySelect.innerHTML = data.cities
      .map((city) => `<option value="${city}">${city}</option>`)
      .join("");

    placeTypeSelect.innerHTML =
      `<option value="all" selected>All types</option>` +
      data.types
        .map((type) => `<option value="${type}">${type.charAt(0).toUpperCase() + type.slice(1)}</option>`)
        .join("");

    placeOptionsLoaded = true;
    loadPlaces();
  } catch (error) {
    showToast("Could not load place options");
  }
}

async function loadPlaces() {
  const city = placeCitySelect.value;
  if (!city) return;

  const params = new URLSearchParams({
    city: city,
    place_type: placeTypeSelect.value || "all",
    min_rating: placeRatingInput.value,
    sort_by: placeSortSelect.value,
  });

  try {
    const response = await fetch(`/api/places?${params.toString()}`);
    const data = await response.json();
    renderPlaces(data.places);
    placeCount.textContent = `${data.count} place(s) found in ${city}`;
  } catch (error) {
    placeGrid.innerHTML = `<div class="hotel-empty">Could not load places.</div>`;
  }
}

function renderPlaces(places) {
  if (places.length === 0) {
    placeGrid.innerHTML = `<div class="hotel-empty">No places match this filter. Try a different type or rating.</div>`;
    return;
  }

  placeGrid.innerHTML = places
    .map(
      (place, index) => `
      <div class="place-card" style="animation-delay: ${index * 0.08}s">
        ${favoriteButtonHtml("place", place)}
        <div class="place-name">${place.name}</div>
        <span class="place-type-tag">${place.type}</span>
        <div class="place-rating">⭐ ${place.rating.toFixed(1)} <small>/ 5</small></div>
      </div>`
    )
    .join("");
}

placeCitySelect.addEventListener("change", loadPlaces);
placeTypeSelect.addEventListener("change", loadPlaces);
placeSortSelect.addEventListener("change", loadPlaces);
placeRatingInput.addEventListener("input", () => {
  placeRatingValue.textContent = placeRatingInput.value;
});
placeRatingInput.addEventListener("change", loadPlaces);

// ---------- Itinerary tab: local planner (no Groq call) ----------
const itinCitySelect = document.getElementById("itin-city");
const itinDaysInput = document.getElementById("itin-days");
const itinDaysValue = document.getElementById("itin-days-value");
const itinPerDaySelect = document.getElementById("itin-per-day");
const itinRatingInput = document.getElementById("itin-rating");
const itinRatingValue = document.getElementById("itin-rating-value");
const itinInterestsBox = document.getElementById("itin-interests");
const itinStarsSelect = document.getElementById("itin-stars");
const itinHotelPriceInput = document.getElementById("itin-hotel-price");
const itinFlightInput = document.getElementById("itin-flight");
const itinDailyInput = document.getElementById("itin-daily");
const itinBuildButton = document.getElementById("itin-build");
const itinMessage = document.getElementById("itin-message");
const itinResult = document.getElementById("itin-result");

let itineraryOptionsLoaded = false;

async function loadItineraryOptionsOnce() {
  if (itineraryOptionsLoaded) return;
  try {
    const [citiesResponse, placeOptionsResponse] = await Promise.all([
      fetch("/api/cities"),
      fetch("/api/place-options"),
    ]);
    const citiesData = await citiesResponse.json();
    const placeOptions = await placeOptionsResponse.json();

    itinCitySelect.innerHTML = citiesData.cities
      .map((city) => `<option value="${city}">${city}</option>`)
      .join("");

    itinInterestsBox.innerHTML = placeOptions.types
      .map(
        (type) =>
          `<label class="chip"><input type="checkbox" name="itin-interest" value="${type}"> ${
            type.charAt(0).toUpperCase() + type.slice(1)
          }</label>`
      )
      .join("");

    itineraryOptionsLoaded = true;
  } catch (error) {
    showToast("Could not load itinerary options");
  }
}

async function buildItinerary() {
  const city = itinCitySelect.value;
  if (!city) {
    showToast("Please choose a city first");
    return;
  }

  const interests = Array.from(
    document.querySelectorAll('input[name="itin-interest"]:checked')
  ).map((input) => input.value);

  const params = new URLSearchParams({
    city: city,
    days: itinDaysInput.value,
    interests: interests.join(","),
    min_rating: itinRatingInput.value,
    places_per_day: itinPerDaySelect.value,
    hotel_stars: itinStarsSelect.value,
    max_hotel_price: itinHotelPriceInput.value || "7000",
    flight_price: itinFlightInput.value || "0",
    daily_local_expense: itinDailyInput.value || "1500",
  });

  itinBuildButton.disabled = true;
  itinBuildButton.textContent = "Building...";
  itinResult.innerHTML = `<div class="hotel-empty">Building your itinerary...</div>`;

  try {
    const response = await fetch(`/api/itinerary?${params.toString()}`);
    const data = await response.json();

    if (!response.ok) {
      itinResult.innerHTML = `<div class="hotel-empty">Could not build the itinerary. Please check the inputs.</div>`;
      return;
    }

    renderItinerary(data);
  } catch (error) {
    itinResult.innerHTML = `<div class="hotel-empty">Could not connect to the server.</div>`;
  } finally {
    itinBuildButton.disabled = false;
    itinBuildButton.textContent = "🗺️ Build itinerary";
  }
}

function renderItinerary(data) {
  itinMessage.textContent = data.messages.join(" ");

  const dayCards = data.days
    .map((day, index) => {
      const placeItems = day.places.length
        ? day.places
            .map(
              (place) => `
                <li>
                  <span>${place.name} <small>(${place.type})</small></span>
                  <span class="itin-place-rating">⭐ ${place.rating.toFixed(1)}</span>
                </li>`
            )
            .join("")
        : `<li><span>No places left for this day</span></li>`;

      return `
        <div class="itin-day" style="animation-delay: ${index * 0.1}s">
          <div class="itin-day-title">Day ${day.day}</div>
          <ul class="itin-place-list">${placeItems}</ul>
        </div>`;
    })
    .join("");

  const hotelCard = data.hotel
    ? `<div class="itin-card">
         <h3>🏨 Hotel</h3>
         <p><strong>${data.hotel.name}</strong> · ${"★".repeat(data.hotel.stars)}</p>
         <p>₹${data.hotel.price_per_night.toLocaleString("en-IN")} / night</p>
       </div>`
    : `<div class="itin-card"><h3>🏨 Hotel</h3><p>No matching hotel found.</p></div>`;

  const budgetCard = data.budget
    ? `<div class="itin-card">
         <h3>💰 Budget</h3>
         <div class="itin-budget-row"><span>Flight</span><span>₹${Math.round(data.budget.flight_cost).toLocaleString("en-IN")}</span></div>
         <div class="itin-budget-row"><span>Hotel</span><span>₹${Math.round(data.budget.hotel_cost).toLocaleString("en-IN")}</span></div>
         <div class="itin-budget-row"><span>Local expenses</span><span>₹${Math.round(data.budget.local_expense_cost).toLocaleString("en-IN")}</span></div>
         <div class="itin-budget-row total"><span>Total</span><span>₹${Math.round(data.budget.total_cost).toLocaleString("en-IN")}</span></div>
       </div>`
    : `<div class="itin-card"><h3>💰 Budget</h3><p>Budget will appear once a hotel is found.</p></div>`;

  itinResult.innerHTML = `${dayCards}<div class="itin-summary-grid">${hotelCard}${budgetCard}</div>`;
}

itinBuildButton.addEventListener("click", buildItinerary);

itinDaysInput.addEventListener("input", () => {
  itinDaysValue.textContent = itinDaysInput.value;
});
itinRatingInput.addEventListener("input", () => {
  itinRatingValue.textContent = itinRatingInput.value;
});

// ---------- Home page: buttons and destination cards ----------
document.querySelectorAll("[data-go]").forEach((element) => {
  element.addEventListener("click", () => {
    showPage(element.dataset.go);
    if (element.dataset.tabTarget) {
      document.querySelector(`.tab-button[data-tab="${element.dataset.tabTarget}"]`).click();
    }
  });
});

document.querySelectorAll(".destination-card").forEach((card) => {
  card.addEventListener("click", () => {
    document.getElementById("destination-city").value = card.dataset.city;
    showPage("plan");
    showToast(`${card.dataset.city} selected. Choose dates and click Plan my trip.`);
  });
});

// ---------- Toast ----------
function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 2400);
}

// ---------- Start ----------
setupDateInputs();