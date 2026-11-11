const profileMessage = document.querySelector("#profile-message");
const profileContent = document.querySelector("#profile-content");
const uploadList = document.querySelector("#profile-upload-list");
const collectionsContainer = document.querySelector("#profile-collections");

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

function renderProfile(profile) {
  profileContent.hidden = false;
  document.querySelector("#profile-initials").textContent = profile.initials;
  document.querySelector("#profile-name").textContent = profile.user.Name;
  document.querySelector("#profile-email").textContent = profile.user.Email;
  const joined = document.querySelector("#profile-joined");
  joined.dateTime = profile.user.JoinedAt || "";
  joined.textContent = `Joined ${profile.user.JoinedAt || "date unavailable"}`;
  document.querySelector("#profile-upload-count").textContent = profile.uploads.length;
  document.querySelector("#profile-collection-count").textContent = profile.collections.length;
  if (!profile.uploads.length) document.querySelector("#profile-no-uploads").hidden = false;
  if (!profile.collections.length) document.querySelector("#profile-no-collections").hidden = false;
  for (const upload of profile.uploads) uploadList.append(renderUpload(upload));
  for (const collection of profile.collections) collectionsContainer.append(renderCollection(collection));
}

function renderUpload(work) {
  const item = document.createElement("li");
  if (work.thumbnail_url) {
    const image = document.createElement("img");
    image.src = work.thumbnail_url;
    image.srcset = work.thumbnail_srcset || "";
    image.sizes = "48px";
    image.alt = "";
    image.width = 48;
    image.height = 62;
    item.append(image);
  } else {
    const placeholder = document.createElement("span");
    placeholder.className = "profile-upload-placeholder";
    placeholder.setAttribute("aria-hidden", "true");
    placeholder.textContent = "♫";
    item.append(placeholder);
  }
  const copy = document.createElement("div");
  copy.className = "profile-item-copy";
  const link = document.createElement("a");
  link.href = work.detail_url;
  link.textContent = work.title || work.OriginalName || "Untitled";
  const original = document.createElement("span");
  original.textContent = work.OriginalName || "";
  copy.append(link, original);
  item.append(copy);
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
    itemList.className = "collection-item-list";
    for (const work of collection.items) {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = work.detail_url;
      link.textContent = work.title || work.OriginalName || "Untitled";
      const removeForm = document.createElement("form");
      const removeButton = document.createElement("button");
      removeButton.className = "text-danger";
      removeButton.type = "button";
      removeButton.textContent = "Remove";
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
  const response = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    profileMessage.textContent = payload.error || "The profile change could not be saved.";
    profileMessage.hidden = false;
    return;
  }
  window.location.reload();
}
