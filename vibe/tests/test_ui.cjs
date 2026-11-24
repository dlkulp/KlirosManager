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
      { title: "Work", OriginalName: "score.pdf", detail_url: "/library/1" },
    ] }) };
  });
  ui.load("home.js");
  await new Promise(setImmediate);
  assert.deepEqual(calls, ["/api/latest"]);
  assert.equal(ui.recent.children.length, 1);
  assert.equal(ui.recent.children[0].children[1].textContent, "Work");
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
