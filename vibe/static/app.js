const form = document.querySelector("#upload-form");
const fileInput = document.querySelector("#score-file");
const selectedFile = document.querySelector("#selected-file");
const submitButton = document.querySelector("#submit-button");
const requestStatus = document.querySelector("#request-status");
const requestError = document.querySelector("#request-error");
const results = document.querySelector("#results");

fileInput.addEventListener("change", () => {
  selectedFile.textContent = fileInput.files.length ? fileInput.files[0].name : "No file selected";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  requestError.hidden = true;
  requestError.textContent = "";
  results.hidden = true;
  requestStatus.hidden = false;
  requestStatus.setAttribute("aria-busy", "true");
  requestStatus.textContent = "Uploading and analyzing score…";
  submitButton.disabled = true;

  try {
    const response = await fetch(form.action, { method: "POST", body: new FormData(form) });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "The upload could not be processed.");
    }
    renderResult(payload);
    requestStatus.textContent = payload.status === "success" ? "Analysis complete." : "Upload saved with processing warnings.";
  } catch (error) {
    requestError.textContent = error instanceof Error ? error.message : "A network error interrupted the upload.";
    requestError.hidden = false;
    requestStatus.textContent = "Upload failed.";
  } finally {
    requestStatus.removeAttribute("aria-busy");
    submitButton.disabled = false;
  }
});

function renderResult(payload) {
  const state = document.querySelector("#result-state");
  state.textContent = payload.status || "partial";
  state.dataset.state = payload.status || "partial";

  const uploadDetails = document.querySelector("#upload-details");
  uploadDetails.replaceChildren();
  addDefinition(uploadDetails, "Title", payload.upload?.title || "Untitled");
  addDefinition(uploadDetails, "Original name", payload.upload?.original_name || "Unknown");
  addDefinition(uploadDetails, "Stored name", payload.upload?.stored_name || "Unknown");
  addDefinition(uploadDetails, "Resource ID", payload.upload?.resource_id ?? "Not stored");
  addDefinition(uploadDetails, "pHash", payload.visual_hash || "Unavailable");
  const libraryLink = document.querySelector("#result-library-link");
  libraryLink.replaceChildren();
  if (payload.upload?.detail_url) {
    const link = document.createElement("a");
    link.href = payload.upload.detail_url;
    link.textContent = "View work details";
    libraryLink.append(link);
    libraryLink.hidden = false;
  } else {
    libraryLink.hidden = true;
  }

  const ocr = payload.ocr || {};
  document.querySelector("#ocr-status").textContent = ocr.message || (ocr.status === "success" ? "Text extracted" : "OCR unavailable");
  document.querySelector("#ocr-text").textContent = ocr.text || "No OCR text was returned.";

  const matches = payload.matches || [];
  document.querySelector("#match-summary").textContent = matches.length ? `${matches.length} possible match${matches.length === 1 ? "" : "es"}` : "No close matches found";
  const matchesList = document.querySelector("#matches-list");
  matchesList.replaceChildren();
  for (const match of matches) {
    const item = document.createElement("li");
    item.textContent = `${match.original_name || `Resource ${match.resource_id}`} · distance ${match.hamming_distance}`;
    matchesList.append(item);
  }

  const metadataList = document.querySelector("#metadata-list");
  metadataList.replaceChildren();
  const metadata = payload.inferred_metadata || {};
  const entries = Object.entries(metadata);
  if (!entries.length) addDefinition(metadataList, "Suggestions", "No metadata identified");
  for (const [name, value] of entries) addDefinition(metadataList, name, value ?? "");

  const processingErrors = document.querySelector("#processing-errors");
  processingErrors.replaceChildren();
  for (const message of payload.errors || []) {
    const item = document.createElement("li");
    item.textContent = message;
    processingErrors.append(item);
  }
  processingErrors.hidden = processingErrors.childElementCount === 0;
  results.hidden = false;
}

function addDefinition(list, label, value) {
  const term = document.createElement("dt");
  const description = document.createElement("dd");
  term.textContent = label;
  description.textContent = String(value);
  list.append(term, description);
}