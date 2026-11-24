const recentWorks = document.querySelector("#recent-works");
const emptyState = document.querySelector("#home-empty-state");

fetch("/api/latest")
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
