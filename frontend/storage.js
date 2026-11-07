// ---------- Storage: favorites and saved trips (browser localStorage, no backend, no Groq) ----------
const FAVORITES_STORAGE_KEY = "travel_planner_favorites_v1";
const TRIPS_STORAGE_KEY = "travel_planner_trips_v1";

// Items currently shown on screen, so a heart click knows what to save
const renderedFavoriteItems = new Map();

// ---------- Generic helpers ----------
function readStorageList(key) {
  try {
    const savedItems = JSON.parse(localStorage.getItem(key));
    return Array.isArray(savedItems) ? savedItems : [];
  } catch (error) {
    return [];
  }
}

function writeStorageList(key, items) {
  localStorage.setItem(key, JSON.stringify(items));
}

// ---------- Favorites ----------
function loadFavorites() {
  return readStorageList(FAVORITES_STORAGE_KEY);
}

function saveFavorites(favorites) {
  writeStorageList(FAVORITES_STORAGE_KEY, favorites);
}

function makeFavoriteId(kind, item) {
  const itemKey = kind === "hotel" ? item.hotel_id : item.place_id;
  return `${kind}:${itemKey}`;
}

function isFavorite(favoriteId) {
  return loadFavorites().some((favorite) => favorite.id === favoriteId);
}

// Returns the heart button HTML for a hotel or place card
function favoriteButtonHtml(kind, item) {
  const favoriteId = makeFavoriteId(kind, item);
  renderedFavoriteItems.set(favoriteId, { kind, item });

  const saved = isFavorite(favoriteId);
  const activeClass = saved ? " on" : "";
  const symbol = saved ? "♥" : "♡";
  return `<button type="button" class="fav-button${activeClass}" data-fav-id="${favoriteId}" aria-label="Save to favorites">${symbol}</button>`;
}

// Adds or removes the item. Returns true if saved now, false if removed, null if unknown.
function toggleFavorite(favoriteId) {
  const entry = renderedFavoriteItems.get(favoriteId);
  if (!entry) return null;

  let favorites = loadFavorites();
  const alreadySaved = favorites.some((favorite) => favorite.id === favoriteId);

  if (alreadySaved) {
    favorites = favorites.filter((favorite) => favorite.id !== favoriteId);
  } else {
    favorites.push({
      id: favoriteId,
      kind: entry.kind,
      item: entry.item,
      saved_at: new Date().toISOString(),
    });
  }

  saveFavorites(favorites);
  return !alreadySaved;
}

function favoriteCardHtml(favorite, index) {
  const item = favorite.item;
  const removeButton = favoriteButtonHtml(favorite.kind, item);
  const delay = `style="animation-delay: ${index * 0.08}s"`;

  if (favorite.kind === "hotel") {
    return `
      <div class="hotel-card" ${delay}>
        ${removeButton}
        <div class="hotel-card-header">
          <div class="hotel-name">${item.name}</div>
          <div class="hotel-stars">${"★".repeat(item.stars)}</div>
        </div>
        <div class="hotel-price">₹${item.price_per_night.toLocaleString("en-IN")} <small>/ night</small></div>
        <div class="hotel-amenities">
          ${item.amenities.map((amenity) => `<span class="amenity-tag">${amenity}</span>`).join("")}
        </div>
        <div class="hotel-count">${item.city}</div>
      </div>`;
  }

  return `
    <div class="place-card" ${delay}>
      ${removeButton}
      <div class="place-name">${item.name}</div>
      <span class="place-type-tag">${item.type}</span>
      <div class="place-rating">⭐ ${item.rating.toFixed(1)} <small>/ 5 · ${item.city}</small></div>
    </div>`;
}

function renderFavoritesPage() {
  const container = document.getElementById("favorites-list");
  if (!container) return;

  const favorites = loadFavorites();
  if (favorites.length === 0) {
    container.innerHTML = `<div class="hotel-empty">No favorites yet. Tap ♡ on a hotel or place.</div>`;
    return;
  }

  container.innerHTML = favorites
    .map((favorite, index) => {
      renderedFavoriteItems.set(favorite.id, { kind: favorite.kind, item: favorite.item });
      return favoriteCardHtml(favorite, index);
    })
    .join("");
}

// ---------- Trips (saved Groq plans) ----------
function loadTrips() {
  return readStorageList(TRIPS_STORAGE_KEY);
}

function saveTrips(trips) {
  writeStorageList(TRIPS_STORAGE_KEY, trips);
}

// Saves a plan text with its trip details. Returns the saved trip.
function addTrip(tripDetails, planText) {
  const trips = loadTrips();
  const newTrip = {
    id: `trip-${Date.now()}`,
    title: `${tripDetails.source} → ${tripDetails.destination}`,
    dates: `${tripDetails.startDate} to ${tripDetails.endDate}`,
    planText: planText,
    saved_at: new Date().toISOString(),
  };
  trips.unshift(newTrip);
  saveTrips(trips);
  return newTrip;
}

function deleteTrip(tripId) {
  saveTrips(loadTrips().filter((trip) => trip.id !== tripId));
}

function renderTripsPage() {
  const container = document.getElementById("trips-list");
  if (!container) return;

  const trips = loadTrips();
  if (trips.length === 0) {
    container.innerHTML = `<div class="hotel-empty">No trips saved yet. After planning a trip, tap "Save trip".</div>`;
    return;
  }

  container.innerHTML = trips
    .map(
      (trip, index) => `
      <div class="trip-card" style="animation-delay: ${index * 0.08}s">
        <div class="trip-card-header">
          <div>
            <div class="trip-title">${trip.title}</div>
            <div class="trip-dates">${trip.dates}</div>
          </div>
          <button type="button" class="trip-delete" data-trip-id="${trip.id}" aria-label="Delete trip">🗑️</button>
        </div>
        <details class="trip-details">
          <summary>Click to view the plan</summary>
          <div class="trip-plan-text">${escapeHtml(trip.planText)}</div>
        </details>
      </div>`
    )
    .join("");
}

// Escapes plain text so saved plans cannot inject HTML
function escapeHtml(text) {
  const element = document.createElement("div");
  element.textContent = text;
  return element.innerHTML;
}

// ---------- Event handling ----------
document.addEventListener("click", (event) => {
  // Heart button on hotel and place cards, and on the favorites page
  const favoriteButton = event.target.closest(".fav-button");
  if (favoriteButton) {
    const favoriteId = favoriteButton.dataset.favId;
    const nowSaved = toggleFavorite(favoriteId);
    if (nowSaved === null) return;

    showToast(nowSaved ? "Saved to favorites" : "Removed from favorites");
    renderFavoritesPage();

    document.querySelectorAll(`.fav-button[data-fav-id="${favoriteId}"]`).forEach((heart) => {
      heart.classList.toggle("on", nowSaved);
      heart.textContent = nowSaved ? "♥" : "♡";
    });
    return;
  }

  // Delete button on a saved trip
  const deleteButton = event.target.closest(".trip-delete");
  if (deleteButton) {
    deleteTrip(deleteButton.dataset.tripId);
    showToast("Trip deleted");
    renderTripsPage();
  }
});

// Refresh the Favorites and My Trips pages each time they are opened
document.querySelectorAll('.nav-item[data-nav="favorites"]').forEach((navButton) => {
  navButton.addEventListener("click", renderFavoritesPage);
});
document.querySelectorAll('.nav-item[data-nav="trips"]').forEach((navButton) => {
  navButton.addEventListener("click", renderTripsPage);
});