const libraryGrid = document.querySelector("#library-grid");
const libraryEmptyState = document.querySelector("#library-empty-state");

fetch("/api/library")
  .then((response) => {
    if (!response.ok) throw new Error("Could not load the library.");
    return response.json();
  })
  .then(({ works }) => {
    if (!works.length) {
      libraryEmptyState.hidden = false;
      return;
    }
    for (const work of works) libraryGrid.append(createWorkCard(work));
  })
  .catch(() => {
    libraryEmptyState.hidden = false;
    libraryEmptyState.textContent = "The library could not be loaded.";
  });

function createWorkCard(work) {
  const link = document.createElement("a");
  link.className = "work-card";
  link.href = work.detail_url;
  if (work.thumbnail_url) {
    const image = document.createElement("img");
    image.className = "work-thumbnail";
    image.src = work.thumbnail_url;
    image.srcset = work.thumbnail_srcset || "";
    image.sizes = "(max-width: 600px) 50vw, (max-width: 900px) 30vw, 220px";
    image.alt = "";
    image.width = 232;
    image.height = 300;
    image.loading = "lazy";
    link.append(image);
  } else {
    const placeholder = document.createElement("span");
    placeholder.className = "work-thumbnail thumbnail-placeholder";
    placeholder.setAttribute("aria-hidden", "true");
    placeholder.textContent = "♫";
    link.append(placeholder);
  }
  const title = document.createElement("span");
  title.className = "work-title";
  title.textContent = work.title || work.OriginalName || "Untitled";
  const originalName = document.createElement("span");
  originalName.className = "work-subtitle";
  originalName.textContent = work.OriginalName || "";
  link.append(title, originalName);
  return link;
}
