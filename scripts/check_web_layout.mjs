/**
 * Headless проверка final_layout.js на JSON из data/
 * node scripts/check_web_layout.mjs [path-to-json]
 */
import fs from "fs";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";
import vm from "vm";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");

function findDefaultJson() {
  const dir = path.join(root, "data");
  const files = fs
    .readdirSync(dir)
    .filter(
      (f) =>
        f.startsWith("family_tree_") &&
        f.endsWith(".json") &&
        !/admin|import|fixed|test|backup|broken|before/i.test(f),
    );
  if (!files.length) throw new Error("No family_tree_*.json in data/");
  return path.join(dir, files[0]);
}

function loadModule(relativePath) {
  const code = fs.readFileSync(path.join(root, relativePath), "utf8");
  const sandbox = { console, window: {}, Set, Map, Array, Object, String, Number, Math, Infinity, parseInt, parseFloat, isNaN, isFinite };
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  return sandbox;
}

const jsonPath = process.argv[2] ? path.resolve(process.argv[2]) : findDefaultJson();
const data = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
const persons = data.persons || {};
const marriages = data.marriages || [];
let centerId = String(data.current_center || data.center_id || Object.keys(persons)[0]);

const vp = loadModule("web/static/js/visible_persons.js");
const fl = loadModule("web/static/js/final_layout.js");
const getVisiblePersons = vp.getVisiblePersons || vp.window?.getVisiblePersons;
const renderFinalLayout = fl.renderFinalLayout || fl.window?.renderFinalLayout;
if (typeof getVisiblePersons !== "function" || typeof renderFinalLayout !== "function") {
  throw new Error("Could not load getVisiblePersons or renderFinalLayout");
}

const related = getVisiblePersons(centerId, persons, marriages, false, {
  gender: "Все",
  status: "Все",
  photos_only: false,
  childless: false,
});

const { coords } = renderFinalLayout(centerId, persons, marriages, related);
const CARD_W = 120;
const CARD_H = 90;

const missing = Object.keys(persons).filter((id) => related.has(id) && !coords[id]);
const overlaps = [];
const entries = Object.entries(coords);
for (let i = 0; i < entries.length; i++) {
  for (let j = i + 1; j < entries.length; j++) {
    const [, a] = entries[i];
    const [, b] = entries[j];
    const dx = Math.abs(a.x - b.x);
    const dy = Math.abs(a.y - b.y);
    if (dx < CARD_W - 4 && dy < CARD_H - 4) {
      overlaps.push([entries[i][0], entries[j][0], dx, dy]);
    }
  }
}

let hierarchyBad = 0;
for (const [pid, pos] of Object.entries(coords)) {
  const p = persons[pid];
  for (const pr of p?.parents || []) {
    const pp = coords[pr];
    if (pp && pp.y >= pos.y) hierarchyBad++;
  }
}

let spouseBad = 0;
for (const m of marriages) {
  const ids = m.persons || m;
  if (!ids || ids.length < 2) continue;
  const a = coords[String(ids[0])];
  const b = coords[String(ids[1])];
  if (a && b && Math.abs(a.y - b.y) > 30) spouseBad++;
}

const xs = Object.values(coords).map((c) => c.x);
const ys = Object.values(coords).map((c) => c.y);
const width = xs.length ? Math.max(...xs) - Math.min(...xs) : 0;

console.log("=".repeat(60));
console.log("WEB LAYOUT CHECK");
console.log("=".repeat(60));
console.log("JSON:", jsonPath);
console.log("center:", centerId);
console.log("persons:", Object.keys(persons).length);
console.log("visible:", related.size);
console.log("placed:", Object.keys(coords).length);
console.log("missing (visible, no coord):", missing.length);
console.log("overlaps:", overlaps.length);
console.log("hierarchy violations:", hierarchyBad);
console.log("spouse Y mismatch:", spouseBad);
console.log("width px:", Math.round(width), width > 5000 ? "WIDE" : "ok");

if (overlaps.length) {
  console.log("\nFirst overlaps:");
  overlaps.slice(0, 8).forEach(([a, b, dx, dy]) => {
    const na = `${persons[a]?.name || ""} ${persons[a]?.surname || ""}`.trim();
    const nb = `${persons[b]?.name || ""} ${persons[b]?.surname || ""}`.trim();
    console.log(`  ${a}(${na}) ↔ ${b}(${nb}) dx=${dx.toFixed(0)} dy=${dy.toFixed(0)}`);
  });
}

if (missing.length) {
  console.log("\nMissing placement:");
  missing.slice(0, 8).forEach((id) => {
    const p = persons[id];
    console.log(`  ${id}: ${p?.name} ${p?.surname}`);
  });
}

process.exit(overlaps.length || missing.length || hierarchyBad ? 1 : 0);
