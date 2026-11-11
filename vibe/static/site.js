const accountControls = document.querySelector("#account-controls");

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
