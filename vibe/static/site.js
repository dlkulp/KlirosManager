const accountControls = document.querySelector("#account-controls");

function createWorkCard(work, metadataFields = []) {
  const link = document.createElement("a");
  link.className = "search-result-card";
  link.href = work.detail_url;
  if (work.thumbnail_url) {
    const image = document.createElement("img");
    image.src = work.thumbnail_url;
    image.srcset = work.thumbnail_srcset || "";
    image.sizes = "(max-width: 600px) 45vw, (max-width: 900px) 30vw, 300px";
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
  for (const fieldName of metadataFields) {
    const value = work.metadata?.[fieldName]?.trim();
    if (value) summary.push(`${fieldName}: ${value}`);
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

if (accountControls) {
  fetch("/api/session")
    .then((response) => response.json())
    .then(renderAccountControls)
    .catch(() => renderAccountControls({ logged_in: false }));
}

function renderAccountControls(session) {
  accountControls.replaceChildren();
  if (session.logged_in && session.user) {
    const profileLink = document.createElement("a");
    profileLink.className = "account-name";
    profileLink.href = "/profile";
    profileLink.textContent = session.user.Name;
    const logoutButton = document.createElement("button");
    logoutButton.className = "account-button";
    logoutButton.type = "button";
    logoutButton.textContent = "Log out";
    logoutButton.addEventListener("click", async () => {
      await fetch("/api/logout", { method: "POST" });
      window.location.reload();
    });
    accountControls.append(profileLink, logoutButton);
  } else {
    const loginButton = document.createElement("button");
    loginButton.className = "account-button";
    loginButton.type = "button";
    loginButton.textContent = "Log in (demo)";
    loginButton.addEventListener("click", async () => {
      const response = await fetch("/api/login", { method: "POST" });
      if (response.ok) window.location.reload();
    });
    accountControls.append(loginButton);
  }
}
