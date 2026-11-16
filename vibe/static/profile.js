const profileMessage = document.querySelector("#profile-message");
const profileContent = document.querySelector("#profile-content");
const uploadList = document.querySelector("#profile-upload-list");
const collectionsContainer = document.querySelector("#profile-collections");
const favoritesContainer = document.querySelector("#profile-favorites");

fetch("/api/profile")
  .then(async (response) => {
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Log in to view your profile.");
    return payload;
  })
  .then(renderProfile)
  .catch((error) => {
    profileMessage.textContent = error instanceof Error ? error.message : "Could not load your profile.";
    profileMessage.hidden = false;
  });

document.querySelector("#profile-name-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await sendProfileAction("/api/profile", "PATCH", {
    name: document.querySelector("#profile-name-input").value.trim(),
  });
});

function renderProfile(profile) {
  profileContent.hidden = false;
  document.querySelector("#profile-initials").textContent = profile.initials;
  document.querySelector("#profile-name").textContent = profile.user.Name;
  document.querySelector("#profile-name-input").value = profile.user.Name;
  document.querySelector("#profile-email").textContent = profile.user.Email;
  const joined = document.querySelector("#profile-joined");
  joined.dateTime = profile.user.JoinedAt || "";
  joined.textContent = `Joined ${profile.user.JoinedAt || "date unavailable"}`;
  document.querySelector("#profile-upload-count").textContent = profile.uploads.length;
  document.querySelector("#profile-collection-count").textContent = profile.collections.length;
  const favorites = profile.favorites || [];
  document.querySelector("#profile-favorite-count").textContent = favorites.length;
  document.querySelector("#profile-no-favorites").hidden = favorites.length > 0;
  if (!profile.uploads.length) document.querySelector("#profile-no-uploads").hidden = false;
  if (!profile.collections.length) document.querySelector("#profile-no-collections").hidden = false;
  for (const upload of profile.uploads) uploadList.append(renderUpload(upload));
  for (const work of favorites) {
    const item = renderUpload(work);
    const removeButton = document.createElement("button");
    removeButton.className = "score-remove-button";
    removeButton.type = "button";
    removeButton.textContent = "★";
    removeButton.title = "Unfavorite";
    removeButton.setAttribute("aria-label", `Unfavorite ${work.title || work.OriginalName || "score"}`);
    removeButton.addEventListener("click", async () => {
      removeButton.disabled = true;
      try {
        await sendProfileAction(`/api/library/${work.id}/favorite`, "DELETE");
      } finally {
        removeButton.disabled = false;
      }
    });
    item.append(removeButton);
    favoritesContainer.append(item);
  }
  for (const collection of profile.collections) collectionsContainer.append(renderCollection(collection));
}

function renderUpload(work) {
  const item = document.createElement("li");
  item.append(createWorkCard(work));
  return item;
}

function renderCollection(collection) {
  const article = document.createElement("article");
  article.className = "profile-collection";
  const heading = document.createElement("header");
  heading.className = "profile-collection-heading";
  const summary = document.createElement("div");
  const title = document.createElement("h3");
  title.textContent = collection.Name;
  const count = document.createElement("span");
  count.textContent = `${collection.items.length} items`;
  summary.append(title, count);
  const deleteForm = document.createElement("form");
  const deleteButton = document.createElement("button");
  deleteButton.className = "text-danger";
  deleteButton.type = "button";
  deleteButton.textContent = "Delete collection";
  deleteButton.addEventListener("click", async () => {
    if (!window.confirm("Delete this collection and remove all of its items?")) return;
    await sendProfileAction(`/api/profile/collections/${collection.id}`, "DELETE");
  });
  deleteForm.append(deleteButton);
  heading.append(summary, deleteForm);
  article.append(heading);

  const renameDetails = document.createElement("details");
  renameDetails.className = "collection-rename";
  const renameSummary = document.createElement("summary");
  renameSummary.textContent = "Rename";
  const renameForm = document.createElement("form");
  const label = document.createElement("label");
  label.htmlFor = `collection-name-${collection.id}`;
  label.textContent = "Collection name";
  const controls = document.createElement("div");
  controls.className = "collection-rename-controls";
  const input = document.createElement("input");
  input.id = label.htmlFor;
  input.value = collection.Name;
  input.maxLength = 255;
  input.required = true;
  const saveButton = document.createElement("button");
  saveButton.type = "submit";
  saveButton.textContent = "Save name";
  controls.append(input, saveButton);
  renameForm.append(label, controls);
  renameForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await sendProfileAction(`/api/profile/collections/${collection.id}`, "PATCH", { name: input.value.trim() });
  });
  renameDetails.append(renameSummary, renameForm);
  article.append(renameDetails);

  if (collection.items.length) {
    const itemList = document.createElement("ul");
    itemList.className = "score-list search-result-grid";
    for (const work of collection.items) {
      const item = document.createElement("li");
      const link = createWorkCard(work);
      const removeForm = document.createElement("form");
      const removeButton = document.createElement("button");
      removeButton.className = "score-remove-button";
      removeButton.type = "button";
      removeButton.textContent = "×";
      removeButton.title = "Remove from collection";
      removeButton.setAttribute("aria-label", `Remove ${work.title || work.OriginalName || "score"} from collection`);
      removeButton.addEventListener("click", async () => {
        if (!window.confirm("Remove this score from the collection?")) return;
        await sendProfileAction(`/api/profile/collections/${collection.id}/items/${work.id}`, "DELETE");
      });
      removeForm.append(removeButton);
      item.append(link, removeForm);
      itemList.append(item);
    }
    article.append(itemList);
  } else {
    const empty = document.createElement("p");
    empty.className = "empty-state collection-empty";
    empty.textContent = "This collection is empty.";
    article.append(empty);
  }
  return article;
}

async function sendProfileAction(url, method, body) {
  try {
    const response = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || "The profile change could not be saved.");
    }
    window.location.reload();
  } catch (error) {
    profileMessage.textContent = error instanceof Error ? error.message : "The profile change could not be saved.";
    profileMessage.hidden = false;
  }
}
