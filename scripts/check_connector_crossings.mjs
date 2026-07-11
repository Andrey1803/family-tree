/**
 * Подсчёт пересечений линий родитель→дети (как в tree.js drawLines).
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import vm from "vm";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const CARD_H = 90;
const LEVEL_HEIGHT = 252;

function loadModule(relativePath) {
  const code = fs.readFileSync(path.join(root, relativePath), "utf8");
  const sandbox = { console, window: {}, Set, Map, Array, Object, String, Number, Math, Infinity, parseInt, parseFloat, isNaN, isFinite };
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  return sandbox;
}

const CONNECTOR_JUNCTION_EPS = 1.5;

function buildConnectorSegments(job, horizLineY) {
  const segs = [];
  const pcx = job.parentCenterX;
  const y0 = job.spouseLineY;
  const y1 = horizLineY;
  if (Math.abs(y1 - y0) > 1e-3) {
    segs.push({ kind: "v", x: pcx, yLo: Math.min(y0, y1), yHi: Math.max(y0, y1) });
  }
  const childXs = job.childrenCoords.map((t) => t.cx);
  const minX = Math.min(pcx, ...childXs);
  const maxX = Math.max(pcx, ...childXs);
  if (maxX - minX > 1e-3) {
    segs.push({ kind: "h", y: horizLineY, xLo: minX, xHi: maxX });
  }
  job.childrenCoords.forEach(({ cx, topY }) => {
    const yt = topY;
    const yh = horizLineY;
    if (Math.abs(yt - yh) > 1e-3) {
      segs.push({ kind: "v", x: cx, yLo: Math.min(yt, yh), yHi: Math.max(yt, yh) });
    }
  });
  return segs;
}

function connectorSegmentsCross(a, b) {
  const eps = CONNECTOR_JUNCTION_EPS;
  if (a.kind === "h" && b.kind === "v") {
    if (b.x <= a.xLo + eps || b.x >= a.xHi - eps) return false;
    if (a.y <= b.yLo + eps || a.y >= b.yHi - eps) return false;
    return true;
  }
  if (a.kind === "v" && b.kind === "h") return connectorSegmentsCross(b, a);
  if (a.kind === "h" && b.kind === "h") {
    if (Math.abs(a.y - b.y) > eps) return false;
    return !(a.xHi <= b.xLo + eps || b.xHi <= a.xLo + eps);
  }
  if (a.kind === "v" && b.kind === "v") {
    if (Math.abs(a.x - b.x) > eps) return false;
    return !(a.yHi <= b.yLo + eps || b.yHi <= a.yLo + eps);
  }
  return false;
}

function connectorSegmentsClash(segsA, segsB) {
  for (const sa of segsA) {
    for (const sb of segsB) {
      if (connectorSegmentsCross(sa, sb)) return true;
    }
  }
  return false;
}

function assignParentConnectorLanes(jobs) {
  if (!jobs.length) return [];
  const MIN_LANE_SEP = 12;
  const LANE_STEP = 3;
  const maxParentBottom = Math.max(...jobs.map((j) => j.parentY + CARD_H / 2));
  const minChildTop = Math.min(...jobs.map((j) => j.minTopY));
  let corridorTop = maxParentBottom + 4;
  let corridorBot = minChildTop - 4;
  const minCorridor = jobs.length * MIN_LANE_SEP + 14;
  if (corridorBot - corridorTop < minCorridor) {
    const deficit = minCorridor - (corridorBot - corridorTop);
    corridorTop -= deficit * 0.55;
    corridorBot += deficit * 0.45;
  }
  const sorted = [...jobs].sort((a, b) => a.maxSpanX - a.minSpanX - (b.maxSpanX - b.minSpanX));
  const placedSegs = [];
  sorted.forEach((job, idx) => {
    let placed = false;
    const fallbackY = corridorTop + ((idx + 1) / (jobs.length + 1)) * Math.max(8, corridorBot - corridorTop);
    for (let trialY = corridorTop + 4; trialY <= corridorBot - 4; trialY += LANE_STEP) {
      const segs = buildConnectorSegments(job, trialY);
      if (!connectorSegmentsClash(segs, placedSegs)) {
        job.horizLineY = trialY;
        placedSegs.push(...segs);
        placed = true;
        break;
      }
    }
    if (!placed) {
      job.horizLineY = Math.min(corridorBot - 2, Math.max(corridorTop + 2, fallbackY));
      placedSegs.push(...buildConnectorSegments(job, job.horizLineY));
    }
  });
  for (let pass = 0; pass < 12; pass++) {
    let changed = false;
    for (const job of sorted) {
      const otherSegs = [];
      jobs.forEach((j) => {
        if (j === job) return;
        otherSegs.push(...buildConnectorSegments(j, j.horizLineY));
      });
      const cur = buildConnectorSegments(job, job.horizLineY);
      if (!connectorSegmentsClash(cur, otherSegs)) continue;
      for (let trialY = corridorTop + 4; trialY <= corridorBot - 4; trialY += LANE_STEP) {
        const trial = buildConnectorSegments(job, trialY);
        if (!connectorSegmentsClash(trial, otherSegs)) {
          job.horizLineY = trialY;
          changed = true;
          break;
        }
      }
    }
    if (!changed) break;
  }
  const finalSegs = [];
  jobs.forEach((j) => finalSegs.push(...buildConnectorSegments(j, j.horizLineY)));
  return finalSegs;
}

function countCrossings(allSegs) {
  let n = 0;
  for (let i = 0; i < allSegs.length; i++) {
    for (let j = i + 1; j < allSegs.length; j++) {
      if (connectorSegmentsCross(allSegs[i], allSegs[j])) n++;
    }
  }
  return n;
}

function collectJobs(coords, persons, related) {
  const childTopOffset = CARD_H / 2;
  const snapRow = (y) => Math.round(y / LEVEL_HEIGHT) * LEVEL_HEIGHT;
  const parentSetToChildren = {};
  Object.keys(coords).forEach((pid) => {
    const p = persons[pid];
    if (!p?.parents) return;
    const dataParents = (p.parents || []).map(String).filter((prId) => persons[prId]).sort();
    if (!dataParents.length) return;
    const visibleParents = dataParents.filter((pid2) => coords[pid2] && related.has(pid2));
    if (!visibleParents.length) return;
    const key = dataParents.join("|");
    parentSetToChildren[key] = parentSetToChildren[key] || [];
    parentSetToChildren[key].push(pid);
  });

  const connectorJobsByBand = {};
  Object.entries(parentSetToChildren).forEach(([parentKey, childPids]) => {
    const first = persons[childPids[0]];
    const parentPids = (first.parents || []).filter((pid) => coords[pid]);
    if (!parentPids.length) return;
    let parentCenterX, parentY, spouseLineY;
    if (parentPids.length >= 2) {
      const p1 = coords[parentPids[0]], p2 = coords[parentPids[1]];
      parentCenterX = (p1.x + p2.x) / 2;
      parentY = p1.y;
      spouseLineY = p1.y;
    } else {
      parentCenterX = coords[parentPids[0]].x;
      parentY = coords[parentPids[0]].y;
      spouseLineY = parentY;
    }
    const childrenCoords = childPids
      .filter((cid) => coords[cid])
      .map((cid) => {
        const c = coords[cid];
        return { cx: c.x, cy: c.y, topY: c.y - childTopOffset };
      })
      .sort((a, b) => a.cx - b.cx);
    if (!childrenCoords.length) return;
    const childCentersX = childrenCoords.map((t) => t.cx);
    const bandKey = String(snapRow(childrenCoords[0].cy));
    if (!connectorJobsByBand[bandKey]) connectorJobsByBand[bandKey] = [];
    connectorJobsByBand[bandKey].push({
      parentCenterX,
      parentY,
      spouseLineY,
      childrenCoords,
      minTopY: Math.min(...childrenCoords.map((t) => t.topY)),
      minSpanX: Math.min(parentCenterX, ...childCentersX) - 2,
      maxSpanX: Math.max(parentCenterX, ...childCentersX) + 2,
    });
  });
  return connectorJobsByBand;
}

const jsonPath = path.join(root, "data", "family_tree_Андрей Емельянов.json");
const data = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
const persons = data.persons || {};
const marriages = data.marriages || [];
const centerId = process.argv[2] || "3";

const vp = loadModule("web/static/js/visible_persons.js");
const fl = loadModule("web/static/js/final_layout.js");
const related = vp.getVisiblePersons(centerId, persons, marriages, false, {
  gender: "Все", status: "Все", photos_only: false, childless: false,
});
const { coords } = fl.renderFinalLayout(centerId, persons, marriages, related);

const bands = collectJobs(coords, persons, related);
let totalCross = 0;
for (const [band, jobs] of Object.entries(bands)) {
  const segs = assignParentConnectorLanes(jobs);
  const crosses = countCrossings(segs);
  console.log(`band y=${band}: jobs=${jobs.length} segments=${segs.length} crossings=${crosses}`);
  totalCross += crosses;
}
console.log("TOTAL crossings:", totalCross);
