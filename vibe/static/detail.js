const resourceId = Number(window.location.pathname.match(/\/library\/(\d+)/)?.[1]);
const detailStatus = document.querySelector("#detail-load-status");
const actionStatus = document.querySelector("#detail-action-status");
const favoriteButton = document.querySelector("#favorite-button");
const collectionDialog = document.querySelector("#collection-dialog");
const collectionStatus = document.querySelector("#collection-status");
const collectionChoices = document.querySelector("#collection-choices");
const newCollectionForm = document.querySelector("#new-collection-form");
const editMetadataButton = document.querySelector("#edit-metadata-button");
const metadataReadMode = document.querySelector("#metadata-read-mode");
const metadataGrid = document.querySelector("#metadata-grid");
const metadataEditForm = document.querySelector("#metadata-edit-form");
const metadataEditError = document.querySelector("#metadata-edit-error");
const metadataEditStatus = document.querySelector("#metadata-edit-status");
const deleteForm = document.querySelector("#delete-resource-form");
const reportDialog = document.querySelector("#report-dialog");
const reportForm = document.querySelector("#report-form");
const reportThanks = document.querySelector("#report-thanks");
let detail = null;
let metadataDefinitions = [];
let session = null;

loadMetadataDefinitions();
loadSession();
loadDetail();

async function loadMetadataDefinitions() {
  try {
    const response = await fetch("/api/site/metadata");
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Metadata definitions could not be loaded.");
    metadataDefinitions = payload.metadata_fields || [];
  } catch (error) {
    console.error("Failed to load metadata definitions:", error);
  }
}

async function loadSession() {
  try {
    const response = await fetch("/api/session");
    session = await response.json();
  } catch (error) {
    console.error("Failed to load session:", error);
    session = { logged_in: false };
  }
}

async function loadDetail() {
  try {
    const response = await fetch(`/api/library/${resourceId}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "The score could not be loaded.");
    detail = payload;
    renderDetail(payload);
  } catch (error) {
    detailStatus.textContent = error instanceof Error ? error.message : "The score could not be loaded.";
    detailStatus.hidden = false;
  }
}

function renderDetail(payload) {
  const resource = payload.resource;
  document.title = `${resource.title} | Kliros Manager`;
  document.querySelector("#detail-title").textContent = resource.title;
  document.querySelector("#detail-original").textContent = payload.original_name || "";
  document.querySelector("#download-original").href = payload.download_url;
  document.querySelector("#download-count-value").textContent = String(resource.DownloadCount || 0);
  document.querySelector("#download-count").hidden = !resource.DownloadCount;
  
  const initials = document.querySelector("#uploader-initials");
  initials.textContent = payload.uploader_initials;
  const uploaderName = document.querySelector("#uploader-name");
  if (Number.isInteger(payload.uploader.UserID)) {
    const link = document.createElement("a");
    link.href = `/profile/${payload.uploader.UserID}`;
    link.textContent = payload.uploader.Name;
    uploaderName.replaceChildren(link);
  } else {
    uploaderName.textContent = payload.uploader.Name;
  }
  const joined = document.querySelector("#uploader-joined");
  joined.dateTime = payload.uploader.JoinedAt || "";
  joined.textContent = `Joined ${payload.uploader.JoinedAt || "date unavailable"}`;
  renderMetadata(payload);
  renderOriginal(payload);
  renderOcr(payload.ocr?.text || "");
  renderActions(payload);
  detailStatus.hidden = true;
}

function renderMetadata(payload) {
  const summary = document.querySelector("#metadata-summary");
  summary.replaceChildren();
  const metadata = payload.metadata || {};
  
  // Render summary (non-empty values only)
  for (const [name, value] of Object.entries(metadata)) {
    if (value === null || value === undefined || String(value).trim() === "") continue;
    const row = document.createElement("div");
    const label = document.createElement("dt");
    label.textContent = name;
    const valueEl = document.createElement("dd");
    valueEl.textContent = typeof value === "string" ? value : JSON.stringify(value);
    row.append(label, valueEl);
    summary.append(row);
  }
  document.querySelector("#metadata-summary-empty").hidden = summary.children.length > 0;

  // Render detailed grid (all values)
  metadataGrid.replaceChildren();
  for (const [name, value] of Object.entries(metadata)) {
    const label = document.createElement("dt");
    label.textContent = name;
    const detailValue = document.createElement("dd");
    detailValue.textContent = typeof value === "string" ? value : JSON.stringify(value);
    metadataGrid.append(label, detailValue);
  }
  document.querySelector("#metadata-empty").hidden = metadataGrid.children.length > 0;
  document.querySelector("#detail-work-title").value = resourceTitle(payload.resource);
  metadataEditForm.dataset.endpoint = `/api/library/${payload.resource.id}`;
  if (session?.logged_in) {
    editMetadataButton.hidden = false;
    // Convert metadata object to array of {Name, value} for renderMetadataFields
    const metadataArray = Object.entries(metadata).map(([name, value]) => ({
      Name: name,
      value: typeof value === "string" ? value : JSON.stringify(value),
    }));
    renderMetadataFields(metadataArray);
  }
}

function resourceTitle(resource) {
  return resource.title || resource.DisplayName || "";
}

function renderOriginal(payload) {
  const viewer = document.querySelector("#original-score");
  viewer.replaceChildren();
  
  // Determine if the file is a PDF based on the file extension
  const fileName = payload.original_name || "";
  const isPdf = fileName.toLowerCase().endsWith(".pdf");
  
  if (isPdf) {
    const frame = document.createElement("iframe");
    frame.src = `${payload.file_url}#view=FitH`;
    frame.title = `${payload.resource.title} PDF`;
    viewer.append(frame);
  } else {
    const image = document.createElement("img");
    image.src = payload.file_url;
    image.alt = `${payload.resource.title} full-size score`;
    viewer.append(image);
  }
}

function renderOcr(text) {
  if (!text) return;
  document.querySelector("#recognized-text").textContent = text;
  document.querySelector("#recognized-details").hidden = false;
}

function renderActions(payload) {
  favoriteButton.dataset.endpoint = `/api/library/${payload.resource.id}/favorite`;
  updateFavoriteButton(payload.is_favorite);
  collectionDialog.dataset.endpoint = `/api/library/${payload.resource.id}/collections`;
  if (session?.logged_in) {
    deleteForm.hidden = false;
    fillCollections(payload.user_collections || [], payload.resource_collection_ids || []);
  } else {
    document.querySelector("#collection-login-prompt").hidden = false;
    document.querySelector("#collection-status").hidden = true;
    document.querySelector("#new-collection-details").hidden = true;
  }
}

function updateFavoriteButton(isFavorite) {
  favoriteButton.setAttribute("aria-pressed", String(isFavorite));
  favoriteButton.textContent = isFavorite ? "★" : "☆";
  favoriteButton.setAttribute("aria-label", isFavorite ? "Remove from favorites" : "Add to favorites");
}

function fillCollections(collections, resourceCollectionIds) {
  const selectedIds = new Set(resourceCollectionIds);
  collectionChoices.replaceChildren();
  if (!collections.length) {
    const empty = document.createElement("p");
    empty.id = "empty-collections";
    empty.className = "muted-copy collection-empty";
    empty.textContent = "No collections yet. Create one to save this score.";
    collectionChoices.append(empty);
    return;
  }
  for (const collection of collections) {
    collectionChoices.append(createCollectionRow(collection, selectedIds.has(collection.id)));
  }
}

function createCollectionRow(collection, isSaved) {
  const row = document.createElement("label");
  row.className = "collection-choice";
  row.dataset.collectionRow = collection.id;
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = isSaved;
  checkbox.dataset.collectionId = collection.id;
  checkbox.addEventListener("change", () => updateCollection(checkbox));
  const mark = document.createElement("span");
  mark.className = "collection-choice-mark";
  mark.setAttribute("aria-hidden", "true");
  mark.textContent = "▤";
  const copy = document.createElement("span");
  copy.className = "collection-choice-copy";
  const name = document.createElement("strong");
  name.textContent = collection.Name;
  const visibility = document.createElement("small");
  visibility.textContent = collection.Public ? "Public" : "Private";
  copy.append(name, visibility);
  const state = document.createElement("span");
  state.className = "collection-choice-state";
  state.textContent = isSaved ? "Saved" : "Save";
  row.append(checkbox, mark, copy, state);
  return row;
}

favoriteButton.addEventListener("click", async () => {
  try {
    const response = await fetch(favoriteButton.dataset.endpoint, { method: "POST" });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "The favorite could not be updated.");
    updateFavoriteButton(result.is_favorite);
    actionStatus.textContent = result.is_favorite ? "Added to favorites." : "Removed from favorites.";
  } catch (error) {
    actionStatus.textContent = error instanceof Error ? error.message : "Could not update favorite.";
  }
});

document.querySelector("#open-collection-dialog").addEventListener("click", () => collectionDialog.showModal());
document.querySelector("#close-collection-dialog").addEventListener("click", () => collectionDialog.close());
newCollectionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await createAndSaveCollection(newCollectionForm.elements.name.value.trim());
});

document.querySelector("#open-report-dialog").addEventListener("click", () => {
  reportForm.hidden = false;
  reportThanks.hidden = true;
  reportDialog.showModal();
});
document.querySelector("#close-report-dialog").addEventListener("click", () => reportDialog.close());
document.querySelector("#cancel-report").addEventListener("click", () => reportDialog.close());
reportForm.addEventListener("submit", (event) => {
  event.preventDefault();
  reportForm.hidden = true;
  reportThanks.hidden = false;
  reportForm.reset();
});

editMetadataButton.addEventListener("click", () => {
  metadataReadMode.hidden = true;
  metadataEditForm.hidden = false;
  editMetadataButton.hidden = true;
  document.querySelector("#detail-work-title").focus();
});
document.querySelector("#cancel-metadata-button").addEventListener("click", () => {
  metadataEditForm.hidden = true;
  metadataReadMode.hidden = false;
  editMetadataButton.hidden = false;
  metadataEditError.hidden = true;
  metadataEditStatus.textContent = "";
});
metadataEditForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const metadata = {};
  for (const input of metadataEditForm.querySelectorAll("[data-metadata-name]")) metadata[input.dataset.metadataName] = input.value;
  metadataEditError.hidden = true;
  metadataEditStatus.textContent = "Saving metadata…";
  try {
    const response = await fetch(metadataEditForm.dataset.endpoint, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        DisplayName: document.querySelector("#detail-work-title").value.trim(),
        metadata,
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "The metadata could not be saved.");
    window.location.reload();
  } catch (error) {
    metadataEditError.textContent = error instanceof Error ? error.message : "A network error interrupted saving.";
    metadataEditError.hidden = false;
    metadataEditStatus.textContent = "";
  }
});

deleteForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!window.confirm("Delete this work and its local files? This cannot be undone.")) return;
  const response = await fetch(`/api/library/${detail.resource.id}`, { method: "DELETE" });
  if (response.ok) window.location.assign("/");
});

if (editMetadataButton && metadataReadMode && metadataEditForm) {
  editMetadataButton.addEventListener("click", () => {
    // Convert metadata object to array of {Name, value} for renderMetadataFields
    const metadata = detail.metadata || {};
    const metadataArray = Object.entries(metadata).map(([name, value]) => ({
      Name: name,
      value: typeof value === "string" ? value : JSON.stringify(value),
    }));
    renderMetadataFields(metadataArray);
  });
}

function renderMetadataFields(fields) {
  const valueMap = {};
  for (const field of fields) {
    valueMap[field.Name] = field.value;
  }
  
  const mergedFields = metadataDefinitions.map((definition) => ({
    ...definition,
    value: valueMap[definition.Name] ?? definition.value ?? "",
  }));
  
  const primary = [];
  const additional = [];
  for (const field of mergedFields) {
    if (field.Core || field.value !== "") primary.push(field);
    else additional.push(field);
  }
  renderFields(document.querySelector("#detail-primary-metadata"), primary);
  renderFields(document.querySelector("#detail-additional-metadata"), additional);
}

function renderFields(container, fields) {
  container.replaceChildren();
  for (const field of fields) {
    const wrapper = document.createElement("div");
    wrapper.className = "metadata-field";
    const inputId = `detail-metadata-${field.id}`;
    const label = document.createElement("label");
    label.htmlFor = inputId;
    label.textContent = field.Name;
    let input;
    if (Array.isArray(field.Options) && field.Options.length) {
      input = document.createElement("select");
      const empty = document.createElement("option");
      empty.value = "";
      empty.textContent = "Select…";
      input.append(empty);
      for (const value of field.Options) {
        const option = document.createElement("option");
        option.value = String(value);
        option.textContent = String(value);
        input.append(option);
      }
      const currentValue = String(field.value ?? "");
      if (currentValue && !field.Options.some((value) => String(value) === currentValue)) {
        const existing = document.createElement("option");
        existing.value = currentValue;
        existing.textContent = currentValue;
        input.append(existing);
      }
      input.value = currentValue;
    } else {
      input = document.createElement("input");
      input.type = field.Type === "date" ? "date" : field.Type === "number" ? "number" : "text";
      input.value = String(field.value ?? "");
    }
    input.id = inputId;
    input.dataset.metadataName = field.Name;
    input.required = Boolean(field.Required);
    wrapper.append(label, input);
    container.append(wrapper);
  }
}

async function updateCollection(checkbox) {
  const saved = checkbox.checked;
  const row = checkbox.closest("[data-collection-row]");
  const state = row.querySelector(".collection-choice-state");
  checkbox.disabled = true;
  if (collectionStatus) collectionStatus.textContent = saved ? "Saving to collection…" : "Removing from collection…";
  try {
    const response = await fetch(`/api/library/${detail.resource.id}/collections`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ collection_id: Number(checkbox.dataset.collectionId), action: saved ? "add" : "remove" }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not update the collection.");
    state.textContent = saved ? "Saved" : "Save";
    if (collectionStatus) collectionStatus.textContent = saved ? `Saved to ${result.collection}.` : `Removed from ${result.collection}.`;
  } catch (error) {
    checkbox.checked = !saved;
    collectionStatus.textContent = error instanceof Error ? error.message : "Could not update collection.";
  } finally {
    checkbox.disabled = false;
  }
}

async function createAndSaveCollection(name) {
  if (!name) return;
  const button = newCollectionForm.querySelector("button[type='submit']");
  button.disabled = true;
  try {
    const response = await fetch(`/api/library/${detail.resource.id}/collections`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_collection_name: name }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not create collection.");
    collectionChoices.append(createCollectionRow({ id: result.collection_id, Name: result.collection, Public: result.is_public }, true));
    document.querySelector("#empty-collections")?.remove();
    newCollectionForm.reset();
    newCollectionForm.closest("details").open = false;
    collectionStatus.textContent = `Saved to ${result.collection}.`;
  } catch (error) {
    collectionStatus.textContent = error instanceof Error ? error.message : "Could not create collection.";
  } finally {
    button.disabled = false;
  }
}
