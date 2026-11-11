const queryInput = document.querySelector("#search-query");
const metadataFilters = document.querySelector("#metadata-filters");
const resultsContainer = document.querySelector("#search-results");
const resultsCount = document.querySelector("#search-count");
let searchableFieldNames = [];
const pageSizeSelect = document.querySelector("#page-size");
const sortSelect = document.querySelector("#sort-order");
const pagination = document.querySelector("#search-pagination");
const filterValues = new Map();
let currentPage = 1;
let pageSize = Number(pageSizeSelect.value);
let sortOrder = sortSelect.value;
let lastSubmittedQuery = "";
let activeRequest = null;
let requestSequence = 0;
let facetsRendered = false;

function valuesFromMetadata(value) {
  if (value === null || value === undefined || value === "") return [];
  if (Array.isArray(value)) return value.flatMap(valuesFromMetadata);
  if (typeof value === "object") {
    if (Object.hasOwn(value, "value")) return valuesFromMetadata(value.value);
    return Object.values(value).flatMap(valuesFromMetadata);
  }
  return [String(value).trim()].filter(Boolean);
}

function fieldValues(work, fieldName) {
  return valuesFromMetadata((work.MetaData || {})[fieldName]);
}

function renderFilters(facets) {
  metadataFilters.replaceChildren();
  for (const [fieldName, choices] of Object.entries(facets)) {
    if (!choices.length) continue;

    const wrapper = document.createElement("label");
    wrapper.className = "metadata-filter";
    const label = document.createElement("span");
    label.textContent = fieldName;
    const select = document.createElement("select");
    select.dataset.metadataName = fieldName;
    const anyOption = document.createElement("option");
    anyOption.value = "";
    anyOption.textContent = `Any ${fieldName}`;
    select.append(anyOption);
    for (const value of choices) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.append(option);
    }
    select.addEventListener("change", () => {
      if (select.value) filterValues.set(fieldName, select.value);
      else filterValues.delete(fieldName);
      currentPage = 1;
      runSearch();
    });
    wrapper.append(label, select);
    metadataFilters.append(wrapper);
  }
  searchableFieldNames = Object.keys(facets);
}

async function runSearch() {
  activeRequest?.abort();
  activeRequest = new AbortController();
  const sequence = ++requestSequence;
  const params = new URLSearchParams({
    q: queryInput.value.trim(),
    page: String(currentPage),
    page_size: String(pageSize),
    sort: sortOrder,
    filters: JSON.stringify(Object.fromEntries(filterValues)),
  });
  resultsCount.textContent = "Searching...";
  try {
    const response = await fetch(`/api/search?${params}`, { signal: activeRequest.signal });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Search failed.");
    if (sequence !== requestSequence) return;
    if (!facetsRendered) {
      renderFilters(payload.facets || {});
      facetsRendered = true;
    }
    renderResults(payload);
    lastSubmittedQuery = queryInput.value;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") return;
    if (sequence !== requestSequence) return;
    resultsCount.textContent = error instanceof Error ? error.message : "Search failed.";
    resultsContainer.replaceChildren();
    pagination.replaceChildren();
  }
}

function renderResults(payload) {
  currentPage = payload.page;
  const pageWorks = payload.results || [];
  const firstResult = payload.total ? ((currentPage - 1) * pageSize) + 1 : 0;
  const lastResult = Math.min(currentPage * pageSize, payload.total);
  resultsCount.textContent = `Showing ${firstResult}-${lastResult} of ${payload.total} results`;
  resultsContainer.replaceChildren();
  if (pageWorks.length) {
    for (const work of pageWorks) resultsContainer.append(renderWork(work));
  } else {
    const empty = document.createElement("p");
    empty.className = "search-empty";
    empty.textContent = "No scores match these search criteria.";
    resultsContainer.append(empty);
  }
  renderPagination(payload.page_count || 0);
}

function renderWork(work) {
  const link = document.createElement("a");
  link.className = "search-result-card";
  link.href = work.detail_url;
  if (work.thumbnail_url) {
    const image = document.createElement("img");
    image.src = work.thumbnail_url;
    if (work.thumbnail_srcset) image.srcset = work.thumbnail_srcset;
    if (work.thumbnail_sizes) image.sizes = work.thumbnail_sizes;
    image.alt = "";
    image.loading = "lazy";
    image.width = 232;
    image.height = 300;
    link.append(image);
  } else {
    const placeholder = document.createElement("span");
    placeholder.className = "search-result-placeholder";
    placeholder.setAttribute("aria-hidden", "true");
    placeholder.textContent = "♫";
    link.append(placeholder);
  }
  const title = document.createElement("strong");
  title.className = "search-result-title";
  title.textContent = work.title || work.OriginalName || "Untitled";
  link.append(title);
  const summary = [];
  for (const fieldName of searchableFieldNames) {
    const value = fieldValues(work, fieldName);
    if (value.length) summary.push(`${fieldName}: ${value.join(", ")}`);
    if (summary.length === 2) break;
  }
  if (summary.length) {
    const metadata = document.createElement("span");
    metadata.className = "search-result-metadata";
    metadata.textContent = summary.join(" · ");
    link.append(metadata);
  }
  const originalName = document.createElement("span");
  originalName.className = "search-result-original";
  originalName.textContent = work.OriginalName || "";
  link.append(originalName);
  return link;
}

function renderPagination(pageCount) {
  pagination.replaceChildren();
  if (pageCount <= 1) return;
  addPageButton("Previous", currentPage - 1, currentPage === 1, false);
  const pages = new Set([1, pageCount]);
  for (let page = Math.max(1, currentPage - 2); page <= Math.min(pageCount, currentPage + 2); page += 1) pages.add(page);
  let previousPage = 0;
  for (const page of [...pages].sort((left, right) => left - right)) {
    if (previousPage && page - previousPage > 1) {
      const ellipsis = document.createElement("span");
      ellipsis.textContent = "...";
      ellipsis.setAttribute("aria-hidden", "true");
      pagination.append(ellipsis);
    }
    addPageButton(String(page), page, false, page === currentPage);
    previousPage = page;
  }
  addPageButton("Next", currentPage + 1, currentPage === pageCount, false);
}

function addPageButton(label, page, disabled, current) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.disabled = disabled;
  if (current) button.setAttribute("aria-current", "page");
  button.addEventListener("click", () => {
    currentPage = page;
    runSearch();
    document.querySelector("#search-results-heading").scrollIntoView({ block: "start", behavior: "smooth" });
  });
  pagination.append(button);
}

queryInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  event.preventDefault();
  currentPage = 1;
  runSearch();
});
queryInput.addEventListener("blur", () => {
  if (queryInput.value === lastSubmittedQuery) return;
  currentPage = 1;
  runSearch();
});
pageSizeSelect.addEventListener("change", () => {
  pageSize = Number(pageSizeSelect.value);
  currentPage = 1;
  runSearch();
});
sortSelect.addEventListener("change", () => {
  sortOrder = sortSelect.value;
  currentPage = 1;
  runSearch();
});
document.querySelector("#clear-search-filters").addEventListener("click", () => {
  queryInput.value = "";
  lastSubmittedQuery = "";
  filterValues.clear();
  for (const select of metadataFilters.querySelectorAll("select")) select.value = "";
  currentPage = 1;
  runSearch();
});

runSearch();
