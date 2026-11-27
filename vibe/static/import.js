const importForm = document.querySelector("#import-form");
const fileInput = document.querySelector("#score-file");
const selectedFile = document.querySelector("#selected-file");
const checkButton = document.querySelector("#check-button");
const uploadStep = document.querySelector("#upload-step");
const reviewStep = document.querySelector("#review-step");
const importStatus = document.querySelector("#import-status");
const importError = document.querySelector("#import-error");
const duplicateResult = document.querySelector("#duplicate-result");
const debugPanel = document.querySelector("#import-debug-panel");
const metadataForm = document.querySelector("#metadata-form");
const matchesStep = document.querySelector("#matches-step");
const rankedMatches = document.querySelector("#ranked-matches");
const duplicatePreviewDialog = document.querySelector("#duplicate-preview-dialog");
const saveButton = document.querySelector("#save-button");
const saveError = document.querySelector("#save-error");
const saveStatus = document.querySelector("#save-status");
let resourceId = null;
let detailUrl = null;
let metadataDefinitions = [];

loadMetadataDefinitions();

fetch("/api/session")
  .then((response) => response.json())
  .then((session) => {
    if (session.logged_in) {
      importForm.hidden = false;
      return;
    }
    document.querySelector("#import-login-required").hidden = false;
  })
  .catch(() => {
    document.querySelector("#import-login-required").hidden = false;
  });

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

fileInput.addEventListener("change", () => {
  selectedFile.textContent = fileInput.files.length ? fileInput.files[0].name : "No file selected";
});

importForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  importError.hidden = true;
  duplicateResult.hidden = true;
  importStatus.hidden = false;
  importStatus.setAttribute("aria-busy", "true");
  importStatus.textContent = "Checking file and first page…";
  checkButton.disabled = true;

  try {
    const response = await fetch(importForm.action, { method: "POST", body: new FormData(importForm) });
    const payload = await response.json();
    if (payload.status === "rejected" && payload.reason === "not_sheet_music") {
      showDebug(payload.debug);
      importError.textContent = payload.error || "This page does not appear to be sheet music.";
      importError.hidden = false;
      importStatus.hidden = true;
      return;
    }
    if (!response.ok) throw new Error(payload.error || "The score could not be checked.");
    showDebug(payload.debug);
    if (payload.status === "duplicate") {
      showDuplicate(payload);
      importStatus.hidden = true;
      return;
    }
    if (payload.status !== "created") throw new Error(payload.error || "The score could not be imported.");
    showReview(payload);
    importStatus.hidden = true;
  } catch (error) {
    importError.textContent = error instanceof Error ? error.message : "A network error interrupted the import.";
    importError.hidden = false;
    importStatus.hidden = true;
  } finally {
    importStatus.removeAttribute("aria-busy");
    checkButton.disabled = false;
  }
});

metadataForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!resourceId) return;
  const displayName = document.querySelector("#work-title").value.trim();
  const metadata = {};
  for (const input of metadataForm.querySelectorAll("[data-metadata-name]")) {
    metadata[input.dataset.metadataName] = input.value;
  }
  saveError.hidden = true;
  saveStatus.textContent = "Saving details…";
  saveButton.disabled = true;
  try {
    const response = await fetch(`/api/library/${resourceId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ DisplayName: displayName, metadata }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "The details could not be saved.");
    showMatchResults(payload);
  } catch (error) {
    saveError.textContent = error instanceof Error ? error.message : "A network error interrupted saving.";
    saveError.hidden = false;
    saveStatus.textContent = "";
  } finally {
    saveButton.disabled = false;
  }
});

function showDuplicate(payload) {
  uploadStep.querySelector("form").hidden = true;
  duplicateResult.hidden = false;
  document.querySelector("#duplicate-title").textContent = payload.duplicate.title;
  document.querySelector("#duplicate-reason").textContent = payload.match_type === "sha256"
    ? "This exact file is already in your library. No copy was stored."
    : "The first page has the same perceptual hash as an existing work. No copy was stored.";
  const link = document.querySelector("#duplicate-link");
  link.href = payload.duplicate.detail_url;
}

function showReview(payload) {
  resourceId = payload.upload.id;
  detailUrl = payload.upload.detail_url;
  document.querySelector("#wizard-step-1").classList.add("step-complete");
  document.querySelector("#wizard-step-1").removeAttribute("aria-current");
  document.querySelector("#wizard-step-2").setAttribute("aria-current", "step");
  uploadStep.hidden = true;
  reviewStep.hidden = false;
  document.querySelector("#review-original-name").textContent = payload.upload.OriginalName;
  document.querySelector("#work-title").value = payload.upload.title || "";
  document.querySelector("#recognized-text").textContent = payload.debug.ocr_text || "No OCR text was recognized.";
  const thumbnail = document.querySelector("#review-thumbnail");
  if (payload.upload.thumbnail_url) {
    thumbnail.src = `${payload.upload.thumbnail_url}/600`;
    thumbnail.hidden = false;
  }

  const inferred = payload.upload.metadata;
  const fields = metadataDefinitions.map((definition) => ({
    ...definition,
    value: inferred[definition.Name] ?? definition.value ?? "",
  }));
  const primary = [];
  const additional = [];
  for (const field of fields) {
    if (field.Core || field.value !== "") {
      primary.push(field);
    } else {
      additional.push(field);
    }
  }
  renderFields(document.querySelector("#primary-metadata"), primary);
  renderFields(document.querySelector("#additional-metadata"), additional);
}

function showMatchResults(payload) {
  document.querySelector("#wizard-step-2").classList.add("step-complete");
  document.querySelector("#wizard-step-2").removeAttribute("aria-current");
  document.querySelector("#wizard-step-3").setAttribute("aria-current", "step");
  reviewStep.hidden = true;
  matchesStep.hidden = false;
  rankedMatches.replaceChildren();
  const finishLink = document.querySelector("#finish-import-link");
  finishLink.href = payload.detail_url || detailUrl;
  const matches = payload.matches || [];
  const heading = document.querySelector("#match-heading");
  const instruction = document.querySelector("#match-instruction");
  const confirmation = document.querySelector("#match-confirmation");
  confirmation.hidden = true;

  if (!matches.length) {
    heading.textContent = "Import complete";
    instruction.textContent = "No visual matches were found. New uploads may require moderation to appear publically.";
    return;
  }

  heading.textContent = "Possible related works";
  instruction.textContent = "Are any of these the same work? Confirming a match does not merge or change either record in this PoC.";
  for (const match of matches) {
    const card = document.createElement("article");
    card.className = "match-card";
    const matchTitle = match.title || match.original_name || `Resource ${match.resource_id}`;
    const title = createWorkCard({
      title: matchTitle,
      OriginalName: match.original_name,
      detail_url: match.detail_url,
      thumbnail_url: match.preview_url,
    });
    const metrics = document.createElement("p");
    metrics.className = "match-metrics";
    const metricParts = [];
    if (match.hamming_distance !== null) metricParts.push(`visual distance ${match.hamming_distance}`);
    if (match.title_similarity !== null) metricParts.push(`title ${Math.round(match.title_similarity * 100)}%`);
    if (match.composer) metricParts.push(`composer ${match.composer}`);
    if (match.composer_similarity !== null) metricParts.push(`composer match ${Math.round(match.composer_similarity * 100)}%`);
    metrics.textContent = metricParts.join(" · ");
    const previewButton = document.createElement("button");
    previewButton.type = "button";
    previewButton.className = "match-preview-button secondary outline";
    previewButton.textContent = "Preview";
    previewButton.addEventListener("click", () => {
      document.querySelector("#duplicate-preview-title").textContent = matchTitle;
      const previewImage = document.querySelector("#duplicate-preview-image");
      previewImage.src = match.preview_url;
      duplicatePreviewDialog.showModal();
    });
    const decisions = document.createElement("div");
    decisions.className = "match-decisions";
    const sameButton = document.createElement("button");
    sameButton.type = "button";
    sameButton.textContent = "Same work";
    sameButton.addEventListener("click", () => {
      confirmation.textContent = `Marked as the same work as “${matchTitle}”. Both records remain separate for now.`;
      confirmation.hidden = false;
      sameButton.textContent = "Confirmed";
      sameButton.disabled = true;
      differentButton.disabled = true;
      card.dataset.decision = "same";
    });
    const differentButton = document.createElement("button");
    differentButton.type = "button";
    differentButton.className = "secondary outline";
    differentButton.textContent = "Different work";
    differentButton.addEventListener("click", () => {
      confirmation.textContent = `Marked “${matchTitle}” as a different work.`;
      confirmation.hidden = false;
      differentButton.textContent = "Marked different";
      differentButton.disabled = true;
      sameButton.disabled = true;
      card.dataset.decision = "different";
    });
    decisions.append(sameButton, differentButton);
    card.append(title, metrics, previewButton, decisions);
    rankedMatches.append(card);
  }
}

document.querySelector("#close-duplicate-preview").addEventListener("click", () => duplicatePreviewDialog.close());

function renderFields(container, fields) {
  container.replaceChildren();
  for (const field of fields) {
    const wrapper = document.createElement("div");
    wrapper.className = "metadata-field";
    const inputId = `metadata-${field.id}`;
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
      for (const optionValue of field.Options) {
        const option = document.createElement("option");
        option.value = String(optionValue);
        option.textContent = String(optionValue);
        input.append(option);
      }
      input.value = String(field.value ?? "");
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

function showDebug(debug = {}) {
  document.querySelector("#debug-file-hash").textContent = debug.file_hash || "Not calculated";
  document.querySelector("#debug-visual-hash").textContent = debug.visual_hash || "Not calculated";
  document.querySelector("#debug-ocr-text").textContent = debug.ocr_text || "OCR was not run or returned no text.";
  debugPanel.hidden = false;
}