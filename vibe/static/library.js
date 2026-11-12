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
