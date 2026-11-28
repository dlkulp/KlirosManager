const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function element() {
  return {
    children: [],
    append(child) { this.children.push(child); },
    setAttribute() {},
  };
}

function interactiveElement() {
  return {
    children: [],
    dataset: {},
    handlers: {},
    classList: { add() {} },
    addEventListener(type, handler) { this.handlers[type] = handler; },
    append(...children) { this.children.push(...children); },
    replaceChildren(...children) { this.children = children; },
    setAttribute() {},
    removeAttribute() {},
    showModal() { this.open = true; },
    close() { this.open = false; },
    reset() { this.wasReset = true; },
  };
}

function setup(fetch) {
  const recent = element();
  const empty = { hidden: true };
  const document = {
    querySelector(selector) {
      return { "#recent-works": recent, "#home-empty-state": empty }[selector] || null;
    },
    createElement: element,
  };
  const context = vm.createContext({ document, fetch });
  const load = (name) => vm.runInContext(
    fs.readFileSync(path.join(__dirname, "..", "static", name), "utf8"), context
  );
  load("site.js");
  return { context, load, recent, empty };
}

test("home loads recent works from the latest API", async () => {
  const calls = [];
  const ui = setup(async (url) => {
    calls.push(url);
    return { ok: true, json: async () => ({ recent_works: [
      {
        title: "Work", OriginalName: "score.pdf", detail_url: "/library/1",
        metadata: { Composer: "A Composer", Tone: "2" },
      },
    ] }) };
  });
  ui.load("home.js");
  await new Promise(setImmediate);
  assert.deepEqual(calls, ["/api/latest"]);
  assert.equal(ui.recent.children.length, 1);
  assert.equal(ui.recent.children[0].children[1].textContent, "Work");
  assert.equal(
    ui.recent.children[0].children.find((child) => child.className === "search-result-metadata").textContent,
    "Composer: A Composer · Tone: 2"
  );
  assert.equal(ui.empty.hidden, true);
});

test("search cards display the formatted metadata map", () => {
  const ui = setup();
  const card = vm.runInContext(`createWorkCard({
    title: "Work", OriginalName: "score.pdf", detail_url: "/library/1",
    metadata: { Service: "Vespers", Language: "English", Composer: "Composer" }
  }, ["Service", "Language", "Composer"])`, ui.context);
  const summary = card.children.find((child) => child.className === "search-result-metadata");
  assert.equal(summary.textContent, "Service: Vespers · Language: English");
});

test("profile cards use metadata by default, skip blanks, and limit the summary", () => {
  const ui = setup();
  const card = vm.runInContext(`createWorkCard({
    title: "Work", OriginalName: "score.pdf", detail_url: "/library/1",
    metadata: { Composer: " ", Tone: "", Service: "Vespers", Language: "English", Tradition: "Chant" }
  })`, ui.context);
  const summary = card.children.find((child) => child.className === "search-result-metadata");
  assert.equal(summary.textContent, "Service: Vespers · Language: English");
});

test("cards with absent or empty metadata omit the summary", () => {
  const ui = setup();
  for (const metadata of [undefined, {}]) {
    ui.context.work = { title: "Work", detail_url: "/library/1", metadata };
    const card = vm.runInContext("createWorkCard(work)", ui.context);
    assert.equal(card.children.some((child) => child.className === "search-result-metadata"), false);
  }
});

test("import review uses the created resource and saves its metadata", async () => {
  const elements = new Map();
  const document = {
    querySelector(selector) {
      if (!elements.has(selector)) elements.set(selector, interactiveElement());
      return elements.get(selector);
    },
    createElement: interactiveElement,
  };
  const importForm = document.querySelector("#import-form");
  importForm.action = "/api/library/import/check";
  const metadataForm = document.querySelector("#metadata-form");
  metadataForm.querySelectorAll = () => [
    ...document.querySelector("#primary-metadata").children,
    ...document.querySelector("#additional-metadata").children,
  ].flatMap((wrapper) => wrapper.children.filter((child) => child.dataset.metadataName));

  const saved = [];
  const fetch = async (url, options) => {
    if (url === "/api/session") return { ok: true, json: async () => ({ logged_in: true }) };
    if (url === "/api/site/metadata") return { ok: true, json: async () => ({
      metadata_fields: [{ id: 1, Name: "Tone Set", Type: "text", Core: true }],
    }) };
    if (url === "/api/library/import/check") return { ok: true, json: async () => ({
      status: "created",
      upload: {
        id: 17,
        OriginalName: "hymn.pdf",
        title: "Evening Hymn",
        metadata: { "Tone Set": "Byzantine" },
        thumbnail_url: "/api/library/17/thumbnail",
        detail_url: "/library/17",
      },
      debug: { ocr_text: "Evening Hymn" },
      matches: [],
      errors: [],
    }) };
    if (url === "/api/library/17") {
      saved.push({ url, options });
      return { ok: true, json: async () => ({ detail_url: "/library/17", matches: [] }) };
    }
    throw new Error(`Unexpected request: ${url}`);
  };
  const context = vm.createContext({ document, fetch, FormData: class FormData {} });
  vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "static", "import.js"), "utf8"), context);
  await new Promise(setImmediate);

  await importForm.handlers.submit({ preventDefault() {} });
  assert.equal(document.querySelector("#review-original-name").textContent, "hymn.pdf");
  assert.equal(document.querySelector("#work-title").value, "Evening Hymn");
  assert.equal(document.querySelector("#recognized-text").textContent, "Evening Hymn");
  assert.equal(document.querySelector("#review-thumbnail").src, "/api/library/17/thumbnail/600");
  assert.equal(metadataForm.querySelectorAll()[0].value, "Byzantine");

  await metadataForm.handlers.submit({ preventDefault() {} });
  assert.equal(saved.length, 1);
  assert.equal(saved[0].options.method, "PATCH");
  assert.deepEqual(JSON.parse(saved[0].options.body), {
    DisplayName: "Evening Hymn",
    metadata: { "Tone Set": "Byzantine" },
  });
  assert.equal(document.querySelector("#finish-import-link").href, "/library/17");
});

async function setupDetailReporting(reportFetch) {
  const elements = new Map();
  const document = {
    querySelector(selector) {
      if (!elements.has(selector)) elements.set(selector, interactiveElement());
      return elements.get(selector);
    },
    createElement: interactiveElement,
  };
  const fetch = async (url, options) => {
    if (url === "/api/session") return { ok: true, json: async () => ({ logged_in: false }) };
    if (url === "/api/site/metadata") return { ok: true, json: async () => ({ metadata_fields: [] }) };
    if (url === "/api/library/17") return { ok: true, json: async () => ({
      resource: { id: 17, title: "Score", UserID: 1 },
      original_name: "score.png", download_url: "/api/library/17/download",
      file_url: "/api/library/17/file", metadata: {}, uploader_initials: "LA",
      uploader: { Name: "Local Admin", JoinedAt: "" }, is_favorite: false,
    }) };
    return reportFetch(url, options);
  };
  const context = vm.createContext({
    document, fetch, window: { location: { pathname: "/library/17" } },
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "static", "detail.js"), "utf8"), context);
  await new Promise(setImmediate);
  return document;
}

test("anonymous score reporting loads reason codes and confirms only a stored report", async () => {
  const calls = [];
  const ui = await setupDetailReporting(async (url, options) => {
    calls.push({ url, options });
    if (url === "/api/flag-report-reasons") return { ok: true, json: async () => ({
      reasons: [{ Code: "copyright", DisplayMessage: "Copyright concern" }],
    }) };
    if (url === "/api/library/17/flags") return { ok: true, json: async () => ({ flag_report_id: 1 }) };
    throw new Error(`Unexpected request: ${url}`);
  });
  await ui.querySelector("#open-report-dialog").handlers.click();
  const reason = ui.querySelector("#report-reason");
  assert.equal(reason.children[1].value, "copyright");
  assert.equal(reason.children[1].textContent, "Copyright concern");
  reason.value = "copyright";
  ui.querySelector("#report-details").value = "Rights concern";
  await ui.querySelector("#report-form").handlers.submit({ preventDefault() {} });
  assert.equal(calls[1].url, "/api/library/17/flags");
  assert.equal(calls[1].options.method, "POST");
  assert.deepEqual(JSON.parse(calls[1].options.body), { reason: "copyright", notes: "Rights concern" });
  assert.equal(ui.querySelector("#report-thanks").hidden, false);
  assert.equal(ui.querySelector("#report-form").hidden, true);
  assert.equal(ui.querySelector("#report-form").wasReset, true);
});

test("failed reporting preserves the draft and does not show success", async () => {
  const ui = await setupDetailReporting(async (url) => {
    if (url === "/api/flag-report-reasons") return { ok: true, json: async () => ({
      reasons: [{ Code: "other", DisplayMessage: "Other" }],
    }) };
    return { ok: false, json: async () => ({ error: "Report could not be saved." }) };
  });
  await ui.querySelector("#open-report-dialog").handlers.click();
  ui.querySelector("#report-reason").value = "other";
  ui.querySelector("#report-details").value = "Keep my draft";
  await ui.querySelector("#report-form").handlers.submit({ preventDefault() {} });
  assert.equal(ui.querySelector("#report-thanks").hidden, true);
  assert.equal(ui.querySelector("#report-form").hidden, false);
  assert.equal(ui.querySelector("#report-form").wasReset, undefined);
  assert.equal(ui.querySelector("#report-details").value, "Keep my draft");
  assert.equal(ui.querySelector("#report-error").textContent, "Report could not be saved.");
  assert.equal(ui.querySelector("#report-submit").disabled, false);
});

test("failed reason loading disables submission and can be retried", async () => {
  let attempts = 0;
  const ui = await setupDetailReporting(async () => {
    attempts += 1;
    return attempts === 1
      ? { ok: false, json: async () => ({ error: "Reasons unavailable." }) }
      : { ok: true, json: async () => ({ reasons: [{ Code: "other", DisplayMessage: "Other" }] }) };
  });
  await ui.querySelector("#open-report-dialog").handlers.click();
  assert.equal(ui.querySelector("#report-submit").disabled, true);
  assert.equal(ui.querySelector("#report-error").textContent, "Reasons unavailable.");
  await ui.querySelector("#open-report-dialog").handlers.click();
  assert.equal(attempts, 2);
  assert.equal(ui.querySelector("#report-submit").disabled, false);
});
