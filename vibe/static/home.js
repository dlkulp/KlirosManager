const recentWorks = document.querySelector("#recent-works");
const emptyState = document.querySelector("#home-empty-state");

fetch("/api/home")
  .then((response) => {
    if (!response.ok) throw new Error("Could not load recent works.");
    return response.json();
  })
  .then(({ recent_works: works }) => {
    if (!works.length) {
      emptyState.hidden = false;
      return;
    }
    for (const work of works) recentWorks.append(createWorkCard(work));
  })
  .catch(() => {
    emptyState.hidden = false;
    emptyState.textContent = "Recent works could not be loaded.";
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
    image.sizes = "(max-width: 600px) 112px, 128px";
    image.alt = "";
    image.width = 232;
    image.height = 300;
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
