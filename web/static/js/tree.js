/**
 * Визуализация семейного дерева (web)
 * Совместимость с форматом данных desktop-версии
 * Расстояния — как в desktop: 100% карточки между братьями/сёстрами, 200% между двоюродными
 */

// Размеры карточки (как в desktop)
const CARD_W = 120;
const CARD_H = 90;
// Коэффициенты расстояний из desktop (app.py)
const SPOUSE_SPACING = 0.3;      // зазор между супругами: 30% от ширины карточки
const SIBLING_SPACING_FULL = 1.0;   // родные братья/сёстры: 100% от ширины карточки
const SIBLING_SPACING_COUSINS = 2.0; // двоюродные и далее: 200% от ширины карточки
// Вычисляемые расстояния (автоматическое соблюдение правил)
const SPOUSE_GAP = CARD_W * SPOUSE_SPACING;
const SIBLING_GAP = CARD_W * SIBLING_SPACING_FULL;
const COUSIN_GAP = CARD_W * SIBLING_SPACING_COUSINS;
const LEVEL_HEIGHT = CARD_H * 2.8;  // вертикальное расстояние между рядами (родители ↔ дети)
const PAD = 60;

let treeData = { persons: {}, marriages: [], current_center: null };
let centerId = null;
let treeZoom = 1;
let treePanX = 0;
let treePanY = 0;
let focusModeActive = false;
let activeFilters = { gender: "Все", status: "Все", photos_only: false, childless: false };
const ZOOM_MIN = 0.25;
const ZOOM_MAX = 3;

async function loadTree() {
    const r = await fetch("/api/tree");
    if (r.status === 401) {
        window.location.href = "/login";
        return;
    }
    if (!r.ok) return;
    treeData = await r.json();
    centerId = treeData.current_center || (Object.keys(treeData.persons)[0] || null);
    render();
}

function render() {
    const root = document.getElementById("tree-root");
    const emptyMsg = document.getElementById("empty-msg");
    root.innerHTML = "";

    const persons = treeData.persons || {};
    const ids = Object.keys(persons);
    if (ids.length === 0) {
        emptyMsg.style.display = "block";
        const btn = document.getElementById("btn-add-first");
        if (btn) btn.onclick = () => addFirstPerson();
        updateStatusBar();
        return;
    }
    emptyMsg.style.display = "none";

    const relatedRaw = new Set();
    function collect(pid, includeParents) {
        if (!pid || relatedRaw.has(pid)) return;
        relatedRaw.add(pid);
        const p = persons[pid];
        if (!p) return;
        if (includeParents) (p.parents || []).forEach(pr => collect(pr, true));
        (p.children || []).forEach(c => collect(c, true));
        (p.spouse_ids || []).forEach(s => collect(s, true));
    }
    if (centerId) collect(centerId, !focusModeActive);
    else ids.forEach(id => collect(id, true));

    const related = new Set();
    for (const pid of relatedRaw) {
        const p = persons[pid];
        if (!p) continue;
        if (activeFilters.gender !== "Все") {
            if (activeFilters.gender === "Только мужчины" && p.gender !== "Мужской") continue;
            if (activeFilters.gender === "Только женщины" && p.gender !== "Женский") continue;
        }
        if (activeFilters.status === "Только живые" && p.is_deceased) continue;
        if (activeFilters.photos_only && !((p.photo_path || p.photo || "").toString().trim())) continue;
        if (activeFilters.childless && (p.children || []).length > 0) continue;
        related.add(pid);
    }

    let rootId = centerId || ids[0];
    const visited = new Set();
    let queue = [rootId];
    while (queue.length) {
        const pid = queue.shift();
        if (visited.has(pid)) continue;
        visited.add(pid);
        const p = persons[pid];
        if (p && p.parents && p.parents.length) {
            rootId = p.parents[0];
            queue.push(rootId);
        }
    }

    const coords = {};
    const spouseStep = CARD_W + SPOUSE_GAP;

    function blockWidthOnly(p) {
        const spouses = (p.spouse_ids || []).filter(s => related.has(s) && persons[s]);
        if (!spouses.length) return CARD_W;
        return CARD_W + spouses.length * spouseStep;
    }

    function gapBetweenSiblings(cid1, cid2) {
        const p1 = persons[cid1], p2 = persons[cid2];
        if (!p1 || !p2) return COUSIN_GAP;
        const set1 = new Set((p1.parents || []).map(String));
        const set2 = new Set((p2.parents || []).map(String));
        if (set1.size !== set2.size) return COUSIN_GAP;
        const sameParents = [...set1].every(x => set2.has(x));
        return sameParents ? SIBLING_GAP : COUSIN_GAP;
    }

    function sortChildren(childrenIds) {
        return [...childrenIds].sort((a, b) => {
            const da = (persons[a]?.birth_date || "9999.99.99");
            const db = (persons[b]?.birth_date || "9999.99.99");
            if (da !== db) return da.localeCompare(db);
            return (String(a).match(/^\d+$/) ? parseInt(a, 10) : 0) - (String(b).match(/^\d+$/) ? parseInt(b, 10) : 0);
        });
    }
    function getSubtreeWidth(pid) {
        if (!pid || !persons[pid]) return CARD_W;
        const p = persons[pid];
        if (p.collapsed_branches) return blockWidthOnly(p);
        const kids = sortChildren((p.children || []).filter(c => related.has(c) && persons[c]));
        const bw = blockWidthOnly(p);
        if (kids.length === 0) return bw;
        const childWidths = kids.map(k => Math.max(getSubtreeWidth(k), blockWidthOnly(persons[k])));
        let total = childWidths.reduce((a, b) => a + b, 0);
        for (let i = 0; i < kids.length - 1; i++) total += gapBetweenSiblings(kids[i], kids[i + 1]);
        return Math.max(bw, total);
    }

    function layout(pid, x, y, w) {
        if (!pid || !persons[pid]) return null;
        const p = persons[pid];
        const spouses = (p.spouse_ids || []).filter(s => related.has(s) && persons[s]);
        const kids = p.collapsed_branches ? [] : sortChildren((p.children || []).filter(c => related.has(c) && persons[c]));

        const blockWidth = blockWidthOnly(p);
        const allocatedWidth = Math.max(w, blockWidth);
        const blockX = x + Math.max(0, (allocatedWidth - blockWidth) / 2);
        let dx = blockX;
        const block = [pid, ...spouses].sort((a, b) => {
            const ga = (persons[a] || {}).gender === "Мужской" ? 0 : 1;
            const gb = (persons[b] || {}).gender === "Мужской" ? 0 : 1;
            return ga - gb;
        });
        block.forEach(id => {
            coords[id] = { x: dx + CARD_W / 2, y: y + CARD_H / 2 };
            dx += spouseStep;
        });
        const parentCenterX = (coords[block[0]].x + coords[block[block.length - 1]].x) / 2;

        if (kids.length === 0) return { left: blockX, right: blockX + blockWidth, top: y, bottom: y + CARD_H };

        const childY = y + LEVEL_HEIGHT;
        const childWidths = kids.map(k => Math.max(getSubtreeWidth(k), blockWidthOnly(persons[k])));
        let totalChildW = childWidths.reduce((a, b) => a + b, 0);
        for (let i = 0; i < kids.length - 1; i++) totalChildW += gapBetweenSiblings(kids[i], kids[i + 1]);
        let childX = parentCenterX - totalChildW / 2;

        let left = blockX, right = blockX + blockWidth, bottom = childY + CARD_H;
        kids.forEach((kid, i) => {
            const cw = childWidths[i];
            const r = layout(kid, childX, childY, cw);
            if (r) {
                left = Math.min(left, r.left);
                right = Math.max(right, r.right);
                bottom = Math.max(bottom, r.bottom);
            }
            childX += cw + (i < kids.length - 1 ? gapBetweenSiblings(kids[i], kids[i + 1]) : 0);
        });
        return { left, right, top: y, bottom };
    }

    const bounds = layout(rootId, 0, 0, CARD_W * 3) || { left: 0, right: 400, top: 0, bottom: 300 };
    const offsetX = Math.max(0, -bounds.left) + PAD;
    const offsetY = Math.max(0, -bounds.top) + PAD;
    const totalW = bounds.right - bounds.left + PAD * 2;
    const totalH = bounds.bottom - bounds.top + PAD * 2;

    const panZoomWrapper = document.createElement("div");
    panZoomWrapper.className = "tree-pan-zoom";
    panZoomWrapper.style.cssText = `position:absolute; left:0; top:0; transform:translate(${treePanX}px,${treePanY}px);`;
    root.appendChild(panZoomWrapper);

    const zoomContainer = document.createElement("div");
    zoomContainer.className = "tree-zoom-container";
    zoomContainer.style.cssText = `position:relative; width:${totalW * treeZoom}px; height:${totalH * treeZoom}px;`;
    panZoomWrapper.appendChild(zoomContainer);

    const wrap = document.createElement("div");
    wrap.className = "tree-wrap";
    wrap.style.cssText = `position:relative; width:${totalW}px; height:${totalH}px; transform:scale(${treeZoom}); transform-origin:0 0;`;
    zoomContainer.appendChild(wrap);

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", totalW);
    svg.setAttribute("height", totalH);
    svg.style.cssText = "position:absolute; top:0; left:0; pointer-events:none;";
    wrap.appendChild(svg);

    // Линии родитель–ребёнок (ортогональные, как в desktop: вертикаль → горизонтальная планка → вертикали к детям)
    const parentSetToChildren = {};
    Object.keys(coords).forEach(pid => {
        const p = persons[pid];
        if (!p || !p.parents) return;
        const visibleParents = (p.parents || []).filter(pid2 => coords[pid2] && related.has(pid2));
        if (!visibleParents.length) return;
        const key = visibleParents.map(String).sort().join("|");
        parentSetToChildren[key] = parentSetToChildren[key] || [];
        parentSetToChildren[key].push(pid);
    });
    const childTopOffset = CARD_H / 2;
    Object.values(parentSetToChildren).forEach(childPids => {
        const first = persons[childPids[0]];
        if (!first || !first.parents) return;
        const parentPids = (first.parents || []).filter(pid => coords[pid]);
        if (!parentPids.length) return;
        let midX, midY;
        if (parentPids.length >= 2) {
            const p1 = coords[parentPids[0]], p2 = coords[parentPids[1]];
            midX = (p1.x + p2.x) / 2;
            midY = (p1.y + p2.y) / 2;
        } else {
            midX = coords[parentPids[0]].x;
            midY = coords[parentPids[0]].y;
        }
        const childrenCoords = childPids
            .filter(cid => coords[cid])
            .map(cid => {
                const c = coords[cid];
                return { cx: c.x, cy: c.y, topY: c.y - childTopOffset };
            })
            .sort((a, b) => a.cx - b.cx);
        if (!childrenCoords.length) return;
        const minTopY = Math.min(...childrenCoords.map(t => t.topY));
        const lineY = (midY + minTopY) / 2;
        const pts = [
            [midX + offsetX, midY + offsetY],
            [midX + offsetX, lineY + offsetY],
        ];
        childrenCoords.forEach(({ cx, topY }) => {
            pts.push([cx + offsetX, lineY + offsetY]);
            pts.push([cx + offsetX, topY + offsetY]);
            pts.push([cx + offsetX, lineY + offsetY]);
        });
        const path = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
        path.setAttribute("points", pts.map(p => p.join(",")).join(" "));
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", "#475569");
        path.setAttribute("stroke-width", 2);
        path.setAttribute("stroke-linecap", "round");
        path.setAttribute("stroke-linejoin", "round");
        svg.appendChild(path);
    });
    // Линии между супругами
    (treeData.marriages || []).forEach(([a, b]) => {
        const idA = String(a), idB = String(b);
        if (!coords[idA] || !coords[idB] || !related.has(idA) || !related.has(idB)) return;
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", coords[idA].x + offsetX);
        line.setAttribute("y1", coords[idA].y + offsetY);
        line.setAttribute("x2", coords[idB].x + offsetX);
        line.setAttribute("y2", coords[idB].y + offsetY);
        line.setAttribute("stroke", "#b45309");
        line.setAttribute("stroke-width", 2);
        line.setAttribute("stroke-dasharray", "4 4");
        svg.appendChild(line);
    });

    Object.entries(coords).forEach(([pid, pos]) => {
        const p = persons[pid];
        if (!p) return;
        const card = document.createElement("div");
        card.className = "tree-card";
        if ((p.gender || "") === "Мужской") card.classList.add("male");
        else card.classList.add("female");
        if (p.is_deceased) card.classList.add("deceased");
        if (pid === centerId) card.classList.add("center");

        let photoSrc = "";
        if (p.photo && typeof p.photo === "string" && p.photo.trim()) {
            const b = p.photo.trim();
            const mime = b.startsWith("iVBORw0K") ? "image/png" : "image/jpeg";
            photoSrc = `data:${mime};base64,${b}`;
        } else if (p.photo_path && typeof p.photo_path === "string" && p.photo_path.trim()) {
            photoSrc = `/api/photo/${encodeURIComponent(pid)}`;
        }

        const name = [p.name, p.patronymic, p.surname].filter(Boolean).join(" ");
        const dates = [p.birth_date, p.death_date].filter(Boolean).join(" — ");

        const photoHtml = photoSrc
            ? `<div class="card-photo"><img src="${photoSrc}" alt="" loading="lazy" onerror="this.parentElement.classList.add('no-photo')"><span class="photo-placeholder">📷</span></div>`
            : `<div class="card-photo no-photo"><span class="photo-placeholder">📷</span></div>`;

        card.innerHTML = photoHtml + `<div class="card-info"><div class="name">${escapeHtml(name)}</div><div class="dates">${escapeHtml(dates)}</div></div>`;

        card.style.left = (pos.x + offsetX - CARD_W / 2) + "px";
        card.style.top = (pos.y + offsetY - CARD_H / 2) + "px";

        card.onclick = (e) => {
            if (window._treeDidPan) return;
            if (card._longPressFired) return;
            setCenterAndSave(pid);
        };
        card.ondblclick = (e) => {
            e.preventDefault();
            if (window._treeDidPan) return;
            editPerson(pid);
        };
        card.addEventListener("contextmenu", (e) => {
            e.preventDefault();
            showContextMenu(pid, e.clientX, e.clientY, persons);
        });
        let longPressTimer;
        card.addEventListener("touchstart", (e) => {
            if (e.touches.length !== 1) return;
            card._longPressFired = false;
            const tx = e.touches[0].clientX, ty = e.touches[0].clientY;
            longPressTimer = setTimeout(() => {
                if (window._treeDidPan) return; // панорамирование — не показываем меню
                card._longPressFired = true;
                e.preventDefault();
                showContextMenu(pid, tx, ty, persons);
            }, 500);
        }, { passive: true });
        card.addEventListener("touchend", () => clearTimeout(longPressTimer));
        card.addEventListener("touchcancel", () => clearTimeout(longPressTimer));
        wrap.appendChild(card);
    });

    setupPan(wrap, panZoomWrapper);
    setupZoom(panZoomWrapper, zoomContainer, wrap, totalW, totalH);
    updateStatusBar();
}

function updateStatusBar() {
    const centerEl = document.getElementById("status-center");
    const msgEl = document.getElementById("status-msg");
    if (!centerEl) return;
    const persons = treeData.persons || {};
    const p = centerId ? persons[centerId] : null;
    const name = p ? [p.name, p.patronymic, p.surname].filter(Boolean).join(" ") : "не выбран";
    centerEl.textContent = "Центр: " + name + (focusModeActive ? " 🔍" : "");
    if (msgEl) msgEl.textContent = focusModeActive ? "Режим фокуса: предки скрыты" : "";
}

function setupZoom(panZoomWrapper, zoomContainer, wrap, totalW, totalH) {
    const viewport = wrap.closest("#tree-root");
    if (!viewport) return;

    const applyZoom = (newZoom) => {
        treeZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, newZoom));
        zoomContainer.style.width = (totalW * treeZoom) + "px";
        zoomContainer.style.height = (totalH * treeZoom) + "px";
        wrap.style.transform = `scale(${treeZoom})`;
    };
    const applyPan = () => {
        panZoomWrapper.style.transform = `translate(${treePanX}px,${treePanY}px)`;
    };

    panZoomWrapper.addEventListener("wheel", (e) => {
        e.preventDefault();
        const rect = viewport.getBoundingClientRect();
        const cx = e.clientX - rect.left;
        const cy = e.clientY - rect.top;
        const factor = e.deltaY > 0 ? 0.9 : 1.1;
        const newZoom = treeZoom * factor;
        const oldZoom = treeZoom;
        applyZoom(newZoom);
        if (oldZoom !== treeZoom) {
            treePanX = cx - (cx - treePanX) * treeZoom / oldZoom;
            treePanY = cy - (cy - treePanY) * treeZoom / oldZoom;
            applyPan();
        }
    }, { passive: false });
    let pinchDist0, zoom0;
    panZoomWrapper.addEventListener("touchstart", (e) => {
        if (e.touches.length === 2) {
            pinchDist0 = Math.hypot(e.touches[1].clientX - e.touches[0].clientX, e.touches[1].clientY - e.touches[0].clientY);
            zoom0 = treeZoom;
        }
    }, { passive: true });
    panZoomWrapper.addEventListener("touchmove", (e) => {
        if (e.touches.length === 2 && pinchDist0) {
            e.preventDefault();
            const dist = Math.hypot(e.touches[1].clientX - e.touches[0].clientX, e.touches[1].clientY - e.touches[0].clientY);
            const factor = dist / pinchDist0;
            applyZoom(zoom0 * factor);
            applyPan();
        }
    }, { passive: false });
    panZoomWrapper.addEventListener("touchend", (e) => {
        if (e.touches.length < 2) pinchDist0 = null;
    });
}

function setupPan(wrap, panZoomWrapper) {
    let active = false, startX, startY, startPanX, startPanY;
    const viewport = wrap.closest("#tree-root");
    if (!viewport) return;

    const applyPan = () => {
        panZoomWrapper.style.transform = `translate(${treePanX}px,${treePanY}px)`;
    };

    const onMove = (e) => {
        if (!active) return;
        window._treeDidPan = true;
        treePanX = startPanX + e.clientX - startX;
        treePanY = startPanY + e.clientY - startY;
        applyPan();
    };
    const onUp = () => {
        active = false;
        viewport.style.cursor = "grab";
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
    };

    const startPan = (clientX, clientY) => {
        active = true;
        window._treeDidPan = false;
        startX = clientX;
        startY = clientY;
        startPanX = treePanX;
        startPanY = treePanY;
        viewport.style.cursor = "grabbing";
        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onUp);
    };
    const onTouchMove = (e) => {
        if (!active || !e.touches) return;
        e.preventDefault();
        const t = e.touches[0];
        window._treeDidPan = true;
        treePanX = startPanX + t.clientX - startX;
        treePanY = startPanY + t.clientY - startY;
        applyPan();
    };
    const stopTouchPan = () => {
        active = false;
        viewport.style.cursor = "grab";
        document.removeEventListener("touchmove", onTouchMove, { passive: false });
        document.removeEventListener("touchend", onTouchEnd);
        document.removeEventListener("touchcancel", onTouchEnd);
    };
    const onTouchEnd = stopTouchPan;
    viewport.style.cursor = "grab";
    viewport.addEventListener("mousedown", (e) => {
        if (e.button !== 0) return;
        startPan(e.clientX, e.clientY);
    });
    viewport.addEventListener("touchstart", (e) => {
        if (e.touches.length !== 1) return;
        e.preventDefault(); // важно для iOS: блокируем браузерный скролл, чтобы pan работал
        const t = e.touches[0];
        startX = t.clientX;
        startY = t.clientY;
        startPanX = treePanX;
        startPanY = treePanY;
        active = true;
        window._treeDidPan = false;
        document.addEventListener("touchmove", onTouchMove, { passive: false });
        document.addEventListener("touchend", onTouchEnd);
        document.addEventListener("touchcancel", onTouchEnd);
    }, { passive: false });
}

function setCenterAndSave(pid) {
            centerId = pid;
            treeData.current_center = pid;
    saveTree();
    render();
}

function saveTree() {
            fetch("/api/tree", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(treeData),
            });
}

function showContextMenu(pid, x, y, persons) {
    closeContextMenu(); // снимает предыдущее меню и его document listener
    const p = persons[pid];
    if (!p) return;

    const menu = document.createElement("div");
    menu.className = "tree-context-menu";
    menu.style.left = x + "px";
    menu.style.top = y + "px";

    const hasFather = (p.parents || []).some(prId => persons[prId]?.gender === "Мужской");
    const hasMother = (p.parents || []).some(prId => persons[prId]?.gender === "Женский");
    const subItems = [
        !hasFather && { label: "Отец...", action: () => addRelative(pid, "father") },
        !hasMother && { label: "Мать...", action: () => addRelative(pid, "mother") },
        { label: "Сын...", action: () => addRelative(pid, "son") },
        { label: "Дочь...", action: () => addRelative(pid, "daughter") },
        { label: "Брат...", action: () => addRelative(pid, "brother") },
        { label: "Сестра...", action: () => addRelative(pid, "sister") },
        { label: "Супруг(а)...", action: () => addRelative(pid, "spouse") },
    ].filter(Boolean);

    const items = [
        { label: "Просмотреть", action: () => viewPerson(pid) },
        { label: "Сделать центром", action: () => setCenterAndSave(pid) },
        { sep: true },
        { label: "Редактировать", action: () => editPerson(pid) },
        { label: "Удалить", action: () => deletePerson(pid) },
        { sep: true },
        { label: "Родственник", sub: subItems },
    ];

    items.forEach((it) => {
        if (it.sep) {
            const sep = document.createElement("div");
            sep.className = "cm-sep";
            menu.appendChild(sep);
            return;
        }
        if (it.sub) {
            const subWrap = document.createElement("div");
            subWrap.className = "cm-sub";
            const mainItem = document.createElement("div");
            mainItem.className = "cm-item";
            mainItem.textContent = it.label;
            subWrap.appendChild(mainItem);
            const submenu = document.createElement("div");
            submenu.className = "cm-submenu tree-context-menu";
            it.sub.forEach((s) => {
                const si = document.createElement("div");
                si.className = "cm-item";
                si.textContent = s.label;
                si.onclick = () => { s.action(); closeContextMenu(); };
                submenu.appendChild(si);
            });
            subWrap.appendChild(submenu);
            menu.appendChild(subWrap);
        } else {
            const item = document.createElement("div");
            item.className = "cm-item";
            item.textContent = it.label;
            item.onclick = () => { it.action(); closeContextMenu(); };
            menu.appendChild(item);
        }
    });

    document.body.appendChild(menu);
    window._ctxMenu = menu;

    const close = () => {
        closeContextMenu();
    };
    const removeListeners = () => {
        document.removeEventListener("click", close);
        document.removeEventListener("keydown", onEscape);
        if (_ctxMenuClickCleanup === removeListeners) _ctxMenuClickCleanup = null;
    };
    const onEscape = (e) => {
        if (e.key === "Escape") closeContextMenu();
    };
    _ctxMenuClickCleanup = removeListeners;
    setTimeout(() => {
        document.addEventListener("click", close);
        document.addEventListener("keydown", onEscape);
    }, 0);

    const rect = menu.getBoundingClientRect();
    if (rect.right > window.innerWidth) menu.style.left = (x - rect.width) + "px";
    if (rect.bottom > window.innerHeight) menu.style.top = (y - rect.height) + "px";
}

let _ctxMenuClickCleanup = null;

function closeContextMenu() {
    if (window._ctxMenu) {
        window._ctxMenu.remove();
        window._ctxMenu = null;
    }
    if (_ctxMenuClickCleanup) {
        _ctxMenuClickCleanup();
        _ctxMenuClickCleanup = null;
    }
}

function viewPerson(pid) {
    const persons = treeData.persons;
    const p = persons[pid];
    if (!p) return;
    const displayName = (q) => {
        const x = persons[q];
        return x ? [x.name, x.patronymic, x.surname].filter(Boolean).join(" ") : String(q);
    };
    let info = `Имя: ${p.name || "—"}\nФамилия: ${p.surname || "—"}\nОтчество: ${p.patronymic || "—"}\n`;
    info += `Дата рождения: ${p.birth_date || "—"}\nПол: ${p.gender || "—"}\n`;
    info += `Умер: ${p.is_deceased ? "Да" : "Нет"}\n`;
    if (p.is_deceased) info += `Дата смерти: ${p.death_date || "—"}\n`;
    info += `Девичья фамилия: ${p.maiden_name || "—"}\n`;
    info += `Родители: ${(p.parents || []).length}\nДети: ${(p.children || []).length}`;
    if ((p.spouse_ids || []).length) {
        info += `\nСупруг(а): ${(p.spouse_ids || []).map(s => displayName(s)).join(", ")}`;
    }
    alert(info);
}

function editPerson(pid) {
    const persons = treeData.persons;
    const p = persons[pid];
    if (!p) return;

    const displayName = (q) => {
        const x = persons[q];
        return x ? [x.name, x.patronymic, x.surname].filter(Boolean).join(" ") : String(q);
    };
    const motherId = (p.parents || []).find(pr => persons[pr]?.gender === "Женский");
    const fatherId = (p.parents || []).find(pr => persons[pr]?.gender !== "Женский");
    const motherText = motherId ? displayName(motherId) : "— Нет";
    const fatherText = fatherId ? displayName(fatherId) : "— Нет";

    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay tree-edit-overlay";
    ov.innerHTML = `
        <div class="tree-edit-modal">
            <h3>Личная страница: ${escapeHtml(displayName(pid))}</h3>
            <div class="tree-edit-tabs">
                <button type="button" class="tab-btn active" data-tab="main">Основное</button>
                <button type="button" class="tab-btn" data-tab="family">Семья</button>
                <button type="button" class="tab-btn" data-tab="history">История</button>
                <button type="button" class="tab-btn" data-tab="photos">Фотоальбом</button>
                <button type="button" class="tab-btn" data-tab="links">Ссылки</button>
                <button type="button" class="tab-btn" data-tab="extra">Дополнительно</button>
            </div>
            <div class="tree-edit-content">
                <div class="tab-pane active" id="tab-main">
                    <label>Имя *</label>
                    <input type="text" id="ed-name" value="${escapeHtml(p.name || "")}">
                    <label>Фамилия *</label>
                    <input type="text" id="ed-surname" value="${escapeHtml(p.surname || "")}">
                    <label>Отчество</label>
                    <input type="text" id="ed-patronymic" value="${escapeHtml(p.patronymic || "")}">
                    <label>Дата рождения (ДД.ММ.ГГГГ)</label>
                    <input type="text" id="ed-birth" value="${escapeHtml(p.birth_date || "")}" placeholder="ДД.ММ.ГГГГ">
                    <label>Место рождения</label>
                    <input type="text" id="ed-birth-place" value="${escapeHtml(p.birth_place || "")}">
                    <label>Пол</label>
                    <select id="ed-gender">
                        <option value="Мужской" ${(p.gender || "") === "Мужской" ? "selected" : ""}>Мужской</option>
                        <option value="Женский" ${(p.gender || "") === "Женский" ? "selected" : ""}>Женский</option>
                    </select>
                    <label><input type="checkbox" id="ed-deceased" ${p.is_deceased ? "checked" : ""}> Умер(ла)</label>
                    <div id="ed-death-row" class="row-inline" style="${p.is_deceased ? "" : "display:none"}">
                        <label>Дата смерти</label>
                        <input type="text" id="ed-death" value="${escapeHtml(p.death_date || "")}" placeholder="ДД.ММ.ГГГГ">
                    </div>
                    <div id="ed-maiden-row" class="row-inline" style="${(p.gender || "") === "Женский" ? "" : "display:none"}">
                        <label>Девичья фамилия</label>
                        <input type="text" id="ed-maiden" value="${escapeHtml(p.maiden_name || "")}">
                    </div>
                    <label>Главное фото</label>
                    <div class="ed-photo-row">
                        <input type="text" id="ed-photo" value="${escapeHtml(p.photo_path || "")}" placeholder="Путь или base64">
                        <label class="btn-browse">Обзор...
                            <input type="file" id="ed-photo-file" accept="image/*" style="display:none">
                        </label>
                        <button type="button" class="btn-remove-photo" id="ed-photo-clear" title="Удалить фото">Удалить</button>
                    </div>
                    <div id="ed-photo-preview" class="ed-photo-preview"></div>
                </div>
                <div class="tab-pane" id="tab-family">
                    <h4>Родители</h4>
                    <div class="ed-family-row">
                        <span class="ed-family-label">Мать:</span>
                        ${motherId ? `<span>${escapeHtml(motherText)}</span>` : '<button type="button" class="btn-add-parent" data-role="mother">Добавить из существующих</button>'}
                    </div>
                    <div class="ed-family-row">
                        <span class="ed-family-label">Отец:</span>
                        ${fatherId ? `<span>${escapeHtml(fatherText)}</span>` : '<button type="button" class="btn-add-parent" data-role="father">Добавить из существующих</button>'}
                    </div>
                    <h4>Супруг(и) / Партнёры</h4>
                    <div id="ed-spouses">${(p.spouse_ids || []).map(s => `<div class="ed-family-item ed-spouse-row"><span>${escapeHtml(displayName(s))}</span><button type="button" class="btn-remove-spouse" data-spouse="${escapeHtml(String(s))}" title="Удалить связь">✕</button></div>`).join("") || '<div class="muted">— Нет</div>'}</div>
                    <button type="button" class="btn-add-row" id="ed-add-spouse">+ Добавить супруга</button>
                    <h4>Дети</h4>
                    <div id="ed-children">${(p.children || []).sort((a,b)=>(persons[a]?.birth_date||"9999").localeCompare(persons[b]?.birth_date||"9999")).map(c => `<div class="ed-family-item">${escapeHtml(displayName(c))}</div>`).join("") || '<div class="muted">— Нет</div>'}</div>
                </div>
                <div class="tab-pane" id="tab-history">
                    <label>Биография, история жизни</label>
                    <textarea id="ed-bio" rows="6">${escapeHtml(p.biography || "")}</textarea>
                    <h4>Захоронение (если умер(ла))</h4>
                    <label>Место захоронения</label>
                    <input type="text" id="ed-burial-place" value="${escapeHtml(p.burial_place || "")}">
                    <label>Дата / год захоронения</label>
                    <input type="text" id="ed-burial-date" value="${escapeHtml(p.burial_date || "")}">
                </div>
                <div class="tab-pane" id="tab-photos">
                    <h4>Дополнительные фото</h4>
                    <div id="ed-album-list"></div>
                    <button type="button" class="btn-add-row" id="ed-album-add">+ Добавить фото</button>
                </div>
                <div class="tab-pane" id="tab-links">
                    <h4>Ссылки на информацию</h4>
                    <div id="ed-links-list"></div>
                    <button type="button" class="btn-add-row" id="ed-links-add">+ Добавить ссылку</button>
                </div>
                <div class="tab-pane" id="tab-extra">
                    <label>Профессия / род занятий</label>
                    <input type="text" id="ed-occupation" value="${escapeHtml(p.occupation || "")}">
                    <label>Образование</label>
                    <input type="text" id="ed-education" value="${escapeHtml(p.education || "")}">
                    <label>Адрес (проживания / исторический)</label>
                    <input type="text" id="ed-address" value="${escapeHtml(p.address || "")}">
                    <label>Заметки</label>
                    <textarea id="ed-notes" rows="4">${escapeHtml(p.notes || "")}</textarea>
                </div>
            </div>
            <div class="tree-modal-btns">
                <button type="button" class="cancel">Отмена</button>
                <button type="button" class="primary save">Сохранить</button>
            </div>
        </div>`;

    const album = (p.photo_album || []).slice();
    const links = (p.links || []).length ? (p.links || []).map(l => ({ title: l.title || "", url: l.url || "" })) : [{ title: "", url: "" }];

    function renderAlbum() {
        const el = ov.querySelector("#ed-album-list");
        el.innerHTML = album.map((path, i) => {
            const hasPreview = (path || "").trim().startsWith("data:image/");
            return `
            <div class="ed-row ed-album-row" data-idx="${i}">
                ${hasPreview ? `<img src="${path}" alt="" class="ed-album-thumb" onerror="this.style.display='none'">` : '<span class="ed-album-no-thumb">Нет превью</span>'}
                <input type="text" class="ed-album-path" value="${escapeHtml(path)}" placeholder="Путь или base64">
                <label class="btn-browse">Обзор
                    <input type="file" class="ed-album-file" data-idx="${i}" accept="image/*" style="display:none">
                </label>
                <button type="button" class="btn-remove" data-idx="${i}">✕</button>
            </div>`;
        }).join("");
        el.querySelectorAll(".btn-remove").forEach(btn => {
            btn.onclick = () => { album.splice(+btn.dataset.idx, 1); renderAlbum(); };
        });
        el.querySelectorAll(".ed-album-path").forEach((inp, i) => {
            inp.oninput = () => { album[i] = inp.value; };
        });
        el.querySelectorAll(".ed-album-file").forEach(inp => {
            inp.onchange = (e) => {
                const file = e.target.files?.[0];
                if (!file || !file.type.startsWith("image/")) return;
                const idx = +inp.dataset.idx;
                const r = new FileReader();
                r.onload = () => { album[idx] = r.result; renderAlbum(); };
                r.readAsDataURL(file);
                e.target.value = "";
            };
        });
    }
    function renderLinks() {
        const el = ov.querySelector("#ed-links-list");
        el.innerHTML = links.map((l, i) => `
            <div class="ed-row ed-links-row" data-idx="${i}">
                <input type="text" class="ed-link-title" placeholder="Название" value="${escapeHtml(l.title)}">
                <input type="text" class="ed-link-url" placeholder="URL" value="${escapeHtml(l.url)}">
                <button type="button" class="btn-open-link" data-idx="${i}" title="Открыть">Открыть</button>
                <button type="button" class="btn-remove" data-idx="${i}">✕</button>
            </div>`).join("");
        el.querySelectorAll(".btn-remove").forEach(btn => {
            btn.onclick = () => { links.splice(+btn.dataset.idx, 1); if (!links.length) links.push({title:"",url:""}); renderLinks(); };
        });
        el.querySelectorAll(".btn-open-link").forEach(btn => {
            btn.onclick = () => {
                const u = (links[+btn.dataset.idx]?.url || "").trim();
                if (u) window.open(u, "_blank");
            };
        });
        el.querySelectorAll(".ed-link-title").forEach((inp, i) => { inp.oninput = () => links[i].title = inp.value; });
        el.querySelectorAll(".ed-link-url").forEach((inp, i) => { inp.oninput = () => links[i].url = inp.value; });
    }
    renderAlbum();
    renderLinks();

    ov.querySelector("#ed-album-add").onclick = () => { album.push(""); renderAlbum(); };
    ov.querySelector("#ed-links-add").onclick = () => { links.push({ title: "", url: "" }); renderLinks(); };

    ov.querySelectorAll(".btn-remove-spouse").forEach(btn => {
        btn.onclick = () => {
            const sid = btn.dataset.spouse;
            const spouse = persons[sid];
            const pName = displayName(pid);
            const sName = spouse ? displayName(sid) : sid;
            if (!confirm(`Удалить связь между «${pName}» и «${sName}»?`)) return;
            p.spouse_ids = (p.spouse_ids || []).filter(s => String(s) !== String(sid));
            if (spouse) {
                spouse.spouse_ids = (spouse.spouse_ids || []).filter(s => String(s) !== String(pid));
            }
            treeData.marriages = (treeData.marriages || []).filter(([a, b]) => !(String(a) === String(pid) && String(b) === String(sid)) && !(String(a) === String(sid) && String(b) === String(pid)));
            saveTree();
            ov.remove();
            render();
            editPerson(pid);
        };
    });

    ov.querySelector("#ed-add-spouse")?.addEventListener("click", () => {
        const needGender = (p.gender || "") === "Мужской" ? "Женский" : "Мужской";
        const candidates = Object.entries(persons).filter(([id, x]) =>
            id !== pid && String(id) !== String(pid) &&
            (x.gender || "") === needGender &&
            !(p.spouse_ids || []).some(s => String(s) === String(id))
        );
        if (!candidates.length) { alert("Нет подходящих персон для добавления в качестве супруга(и)."); return; }
        const pickOv = document.createElement("div");
        pickOv.className = "tree-modal-overlay";
        pickOv.innerHTML = `
            <div class="tree-modal tree-pick-modal">
                <h3>Выберите супруга(у)</h3>
                <div class="pick-list" id="pick-spouse-list"></div>
                <div class="tree-modal-btns">
                    <button type="button" class="cancel">Отмена</button>
                </div>
            </div>`;
        const listEl = pickOv.querySelector("#pick-spouse-list");
        candidates.forEach(([id, x]) => {
            const div = document.createElement("div");
            div.className = "pick-item";
            div.textContent = [x.name, x.patronymic, x.surname].filter(Boolean).join(" ");
            div.onclick = () => {
                p.spouse_ids = p.spouse_ids || [];
                if (!p.spouse_ids.some(s => String(s) === String(id))) p.spouse_ids.push(id);
                const spouse = persons[id];
                if (spouse) {
                    spouse.spouse_ids = spouse.spouse_ids || [];
                    if (!spouse.spouse_ids.some(s => String(s) === String(pid))) spouse.spouse_ids.push(pid);
                }
                const pair = [String(pid), String(id)].sort();
                if (!treeData.marriages.some(([a,b]) => String(a)===pair[0] && String(b)===pair[1])) {
                    treeData.marriages = treeData.marriages || [];
                    treeData.marriages.push(pair);
                }
                saveTree();
                pickOv.remove();
                ov.remove();
                render();
                editPerson(pid);
            };
            listEl.appendChild(div);
        });
        pickOv.onclick = (e) => { if (e.target === pickOv) pickOv.remove(); };
        pickOv.querySelector(".cancel").onclick = () => pickOv.remove();
        document.body.appendChild(pickOv);
    });

    ov.querySelectorAll(".btn-add-parent").forEach(btn => {
        btn.onclick = () => {
            const isMother = btn.dataset.role === "mother";
            const needGender = isMother ? "Женский" : "Мужской";
            const candidates = Object.entries(persons).filter(([id, x]) =>
                id !== pid && String(id) !== String(pid) && (x.gender || "") === needGender
            );
            if (!candidates.length) { alert("Нет подходящих персон для добавления в качестве " + (isMother ? "матери" : "отца") + "."); return; }
            const pickOv = document.createElement("div");
            pickOv.className = "tree-modal-overlay";
            pickOv.innerHTML = `
                <div class="tree-modal tree-pick-modal">
                    <h3>Выберите ${isMother ? "мать" : "отца"}</h3>
                    <div class="pick-list" id="pick-parent-list"></div>
                    <div class="tree-modal-btns">
                        <button type="button" class="cancel">Отмена</button>
                    </div>
                </div>`;
            const listEl = pickOv.querySelector("#pick-parent-list");
            candidates.forEach(([id, x]) => {
                const div = document.createElement("div");
                div.className = "pick-item";
                div.textContent = [x.name, x.patronymic, x.surname].filter(Boolean).join(" ");
                div.onclick = () => {
                    p.parents = p.parents || [];
                    if (!p.parents.some(pr => String(pr) === String(id))) {
                        p.parents.push(id);
                        const parent = persons[id];
                        if (parent) {
                            parent.children = parent.children || [];
                            if (!parent.children.some(c => String(c) === String(pid))) parent.children.push(pid);
                        }
                        saveTree();
                        pickOv.remove();
                        ov.remove();
                        render();
                        editPerson(pid);
                    }
                };
                listEl.appendChild(div);
            });
            pickOv.onclick = (e) => { if (e.target === pickOv) pickOv.remove(); };
            pickOv.querySelector(".cancel").onclick = () => pickOv.remove();
            document.body.appendChild(pickOv);
        };
    });

    function updatePhotoPreview() {
        const val = (ov.querySelector("#ed-photo")?.value || "").trim();
        const prev = ov.querySelector("#ed-photo-preview");
        if (!prev) return;
        prev.innerHTML = "";
        if (val.startsWith("data:image/")) {
            const img = document.createElement("img");
            img.src = val;
            img.alt = "Превью";
            img.className = "ed-photo-thumb";
            prev.appendChild(img);
        }
    }
    ov.querySelector("#ed-photo").oninput = updatePhotoPreview;
    updatePhotoPreview();
    ov.querySelector("#ed-photo-file").onchange = (e) => {
        const file = e.target.files?.[0];
        if (!file || !file.type.startsWith("image/")) return;
        const r = new FileReader();
        r.onload = () => { ov.querySelector("#ed-photo").value = r.result; updatePhotoPreview(); };
        r.readAsDataURL(file);
        e.target.value = "";
    };
    ov.querySelector("#ed-photo-clear").onclick = () => {
        if ((p.photo_path || "").trim() && !confirm("Удалить фото этой персоны?")) return;
        ov.querySelector("#ed-photo").value = "";
        updatePhotoPreview();
    };
    ov.querySelector("#ed-deceased").onchange = () => {
        ov.querySelector("#ed-death-row").style.display = ov.querySelector("#ed-deceased").checked ? "flex" : "none";
    };
    ov.querySelector("#ed-gender").onchange = () => {
        ov.querySelector("#ed-maiden-row").style.display = ov.querySelector("#ed-gender").value === "Женский" ? "flex" : "none";
    };

    ov.querySelectorAll(".tab-btn").forEach(btn => {
        btn.onclick = () => {
            ov.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            ov.querySelectorAll(".tab-pane").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            ov.querySelector("#tab-" + btn.dataset.tab).classList.add("active");
        };
    });

    ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
    ov.querySelector(".tree-edit-modal").onclick = (e) => e.stopPropagation();
    ov.querySelector(".cancel").onclick = () => ov.remove();
    ov.querySelector(".save").onclick = () => {
        const name = ov.querySelector("#ed-name").value.trim();
        const surname = ov.querySelector("#ed-surname").value.trim();
        if (!name) { alert("Имя обязательно."); return; }
        if (!surname) { alert("Фамилия обязательна."); return; }
        const birthDate = ov.querySelector("#ed-birth").value.trim();
        const deathDate = ov.querySelector("#ed-death").value.trim();
        const isDeceased = !!ov.querySelector("#ed-deceased").checked;
        if (birthDate && !validateDate(birthDate)) { alert("Неверный формат даты рождения (ДД.ММ.ГГГГ)"); return; }
        if (isDeceased && deathDate && !validateDate(deathDate)) { alert("Неверный формат даты смерти (ДД.ММ.ГГГГ)"); return; }
        p.name = name;
        p.surname = surname;
        p.patronymic = ov.querySelector("#ed-patronymic").value.trim() || "";
        p.birth_date = ov.querySelector("#ed-birth").value.trim() || "";
        p.birth_place = ov.querySelector("#ed-birth-place").value.trim() || "";
        p.gender = ov.querySelector("#ed-gender").value;
        p.is_deceased = isDeceased;
        p.death_date = isDeceased ? deathDate || "" : "";
        p.maiden_name = p.gender === "Женский" ? ov.querySelector("#ed-maiden").value.trim() || "" : "";
        p.photo_path = ov.querySelector("#ed-photo").value.trim() || "";
        p.biography = ov.querySelector("#ed-bio").value.trim() || "";
        p.burial_place = ov.querySelector("#ed-burial-place").value.trim() || "";
        p.burial_date = ov.querySelector("#ed-burial-date").value.trim() || "";
        p.photo_album = album.filter(x => x.trim());
        p.links = links.filter(l => (l.url || "").trim()).map(l => ({ title: (l.title || "").trim(), url: (l.url || "").trim() }));
        p.occupation = ov.querySelector("#ed-occupation").value.trim() || "";
        p.education = ov.querySelector("#ed-education").value.trim() || "";
        p.address = ov.querySelector("#ed-address").value.trim() || "";
        p.notes = ov.querySelector("#ed-notes").value.trim() || "";
        saveTree();
        ov.remove();
        render();
        const savedName = [p.name, p.patronymic, p.surname].filter(Boolean).join(" ");
        alert(`Данные персоны «${savedName}» сохранены.`);
    };
    document.body.appendChild(ov);
}

function deletePerson(pid) {
    if (!confirm("Удалить эту персону из дерева?")) return;
    const persons = treeData.persons;
    const p = persons[pid];
    if (!p) return;
    const toRemove = new Set([pid]);
    (p.parents || []).forEach(pid2 => {
        const par = persons[pid2];
        if (par) par.children = (par.children || []).filter(c => c !== pid && String(c) !== pid);
    });
    (p.children || []).forEach(cid => {
        const ch = persons[cid];
        if (ch) ch.parents = (ch.parents || []).filter(pr => pr !== pid && String(pr) !== pid);
    });
    (p.spouse_ids || []).forEach(sid => {
        const sp = persons[sid];
        if (sp) sp.spouse_ids = (sp.spouse_ids || []).filter(s => s !== pid && String(s) !== pid);
    });
    delete persons[pid];
    treeData.marriages = (treeData.marriages || []).filter(([a, b]) => a !== pid && b !== pid && String(a) !== pid && String(b) !== pid);
    if (centerId === pid || String(centerId) === pid) {
        centerId = Object.keys(persons)[0] || null;
        treeData.current_center = centerId;
    }
    saveTree();
    render();
}

function addFirstPerson() {
    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay";
    ov.innerHTML = `
        <div class="tree-modal">
            <h3>Добавить первую персону</h3>
            <label>Имя</label>
            <input type="text" id="fp-name" placeholder="Имя">
            <label>Отчество</label>
            <input type="text" id="fp-patronymic" placeholder="Отчество">
            <label>Фамилия</label>
            <input type="text" id="fp-surname" placeholder="Фамилия">
            <label>Дата рождения (ДД.ММ.ГГГГ)</label>
            <input type="text" id="fp-birth" placeholder="ДД.ММ.ГГГГ">
            <label>Дата смерти (ДД.ММ.ГГГГ)</label>
            <input type="text" id="fp-death" placeholder="ДД.ММ.ГГГГ">
            <label>Пол</label>
            <select id="fp-gender">
                <option value="Мужской">Мужской</option>
                <option value="Женский">Женский</option>
            </select>
            <label><input type="checkbox" id="fp-deceased"> Умер(ла)</label>
            <div class="tree-modal-btns">
                <button type="button" class="cancel">Отмена</button>
                <button type="button" class="primary save">Добавить</button>
            </div>
        </div>`;
    ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
    ov.querySelector(".cancel").onclick = () => ov.remove();
    ov.querySelector(".save").onclick = () => {
        const name = ov.querySelector("#fp-name").value.trim();
        const surname = ov.querySelector("#fp-surname").value.trim();
        if (!name) { alert("Введите имя."); return; }
        if (!surname) { alert("Введите фамилию."); return; }
        const numIds = Object.keys(treeData.persons).map(k => parseInt(k, 10)).filter(n => !isNaN(n));
        const newId = numIds.length ? String(Math.max(...numIds) + 1) : "1";
        const np = {
            name, surname,
            patronymic: ov.querySelector("#fp-patronymic").value.trim() || "",
            birth_date: ov.querySelector("#fp-birth").value.trim() || "",
            death_date: ov.querySelector("#fp-death").value.trim() || "",
            gender: ov.querySelector("#fp-gender").value,
            is_deceased: !!ov.querySelector("#fp-deceased").checked,
            parents: [], children: [], spouse_ids: [],
        };
        treeData.persons[newId] = np;
        centerId = newId;
        treeData.current_center = newId;
        saveTree();
        ov.remove();
        render();
    };
    document.body.appendChild(ov);
}

function addRelative(pid, relation) {
    const persons = treeData.persons;
    const p = persons[pid];
    if (!p) return;
    if ((relation === "brother" || relation === "sister") && (!p.parents || p.parents.length === 0)) {
        alert("Для добавления брата/сестры у персоны должны быть родители.");
        return;
    }
    const labels = { father: "Отец", mother: "Мать", son: "Сын", daughter: "Дочь", brother: "Брат", sister: "Сестра", spouse: "Супруг(а)" };
    const newGender = ["son", "brother", "father"].includes(relation) ? "Мужской" : "Женский";

    let autoName = "", autoPatronymic = "", autoSurname = "";
    const fathersOfPerson = (p.parents || []).map(pr => persons[pr]).filter(x => x && x.gender === "Мужской");
    const fatherOfPerson = fathersOfPerson[0];
    const fatherForChild = p.gender === "Мужской" ? p : (p.spouse_ids || []).map(s => persons[s]).find(x => x && x.gender === "Мужской");

    if (relation === "father") {
        autoName = (p.patronymic && p.patronymic.trim()) ? generateNameFromPatronymic(p.patronymic, "Мужской") : "";
        autoSurname = getCurrentSurname(p) || p.surname || "";
    } else if (relation === "mother") {
        autoSurname = getCurrentSurname(p) || p.surname || "";
    } else if (relation === "son" || relation === "daughter") {
        autoSurname = getCurrentSurname(p) || p.surname || "";
        autoPatronymic = (fatherForChild && fatherForChild.name) ? generatePatronymic(fatherForChild.name, newGender) : "";
    } else if (relation === "brother" || relation === "sister") {
        autoSurname = p.surname || "";
        autoPatronymic = (fatherOfPerson && fatherOfPerson.name) ? generatePatronymic(fatherOfPerson.name, newGender) : "";
    }
    if (relation === "spouse") autoSurname = "";

    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay";
    ov.innerHTML = `
        <div class="tree-modal">
            <h3>Добавить ${labels[relation] || "родственника"}</h3>
            <label>Имя</label>
            <input type="text" id="ar-name" value="${escapeHtml(autoName)}" placeholder="Имя">
            <label>Отчество</label>
            <input type="text" id="ar-patronymic" value="${escapeHtml(autoPatronymic)}" placeholder="Отчество">
            <label>Фамилия</label>
            <input type="text" id="ar-surname" value="${escapeHtml(autoSurname)}" placeholder="Фамилия">
            <label>Дата рождения (ДД.ММ.ГГГГ)</label>
            <input type="text" id="ar-birth" placeholder="ДД.ММ.ГГГГ">
            <label>Пол</label>
            <select id="ar-gender">
                <option value="Мужской" ${newGender === "Мужской" ? "selected" : ""}>Мужской</option>
                <option value="Женский" ${newGender === "Женский" ? "selected" : ""}>Женский</option>
            </select>
            <div class="tree-modal-btns">
                <button type="button" class="cancel">Отмена</button>
                <button type="button" class="primary save">Добавить</button>
            </div>
        </div>`;
    ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
    ov.querySelector(".cancel").onclick = () => ov.remove();
    ov.querySelector(".save").onclick = () => {
        const name = ov.querySelector("#ar-name").value.trim();
        const surname = ov.querySelector("#ar-surname").value.trim();
        if (!name) { alert("Введите имя."); return; }
        if (!surname) { alert("Введите фамилию."); return; }
        const numIds = Object.keys(treeData.persons).map(k => parseInt(k, 10)).filter(n => !isNaN(n));
        const newId = numIds.length ? String(Math.max(...numIds) + 1) : "1";
        const np = {
            name, surname,
            patronymic: ov.querySelector("#ar-patronymic").value.trim() || "",
            birth_date: ov.querySelector("#ar-birth").value.trim() || "",
            gender: ov.querySelector("#ar-gender").value,
            is_deceased: false, death_date: "", maiden_name: "",
            parents: [], children: [], spouse_ids: [],
        };
        treeData.persons[newId] = np;

        const pidStr = String(pid);
        if (relation === "father" || relation === "mother") {
            np.children = [pidStr];
            const par = treeData.persons[pidStr];
            if (par) par.parents = [...(par.parents || []), newId];
        } else if (relation === "son" || relation === "daughter") {
            np.parents = [pidStr];
            const par = treeData.persons[pidStr];
            if (par) par.children = [...(par.children || []), newId];
            const spouseIds = (p.spouse_ids || []).map(String);
            spouseIds.forEach(sid => {
                np.parents.push(sid);
                const sp = treeData.persons[sid];
                if (sp) sp.children = [...(sp.children || []), newId];
            });
        } else if (relation === "brother" || relation === "sister") {
            const parIds = (p.parents || []).map(String);
            np.parents = [...parIds];
            parIds.forEach(pr => {
                const par = treeData.persons[pr];
                if (par) par.children = [...(par.children || []), newId];
            });
        } else if (relation === "spouse") {
            np.spouse_ids = [pidStr];
            p.spouse_ids = [...(p.spouse_ids || []), newId];
            const pair = [pidStr, newId].sort();
            treeData.marriages = [...(treeData.marriages || []), pair];
        }
        saveTree();
        ov.remove();
        centerId = pid;
        treeData.current_center = pid;
        render();
    };
    document.body.appendChild(ov);
}

function generatePatronymic(fatherName, childGender) {
    if (!fatherName || !fatherName.trim()) return "";
    const clean = fatherName.trim().split(/\s+/)[0];
    if (!clean) return "";
    const lower = clean.toLowerCase();
    const SPECIAL = {
        николай: "Николаевич", сергей: "Сергеевич", владимир: "Владимирович", александр: "Александрович",
        михаил: "Михайлович", дмитрий: "Дмитриевич", андрей: "Андреевич", константин: "Константинович",
        пётр: "Петрович", петр: "Петрович", иван: "Иванович", юрий: "Юрьевич", фёдор: "Фёдорович",
        федор: "Федорович", геннадий: "Геннадиевич", никита: "Никитич", илья: "Ильич"
    };
    if (SPECIAL[lower]) {
        const s = SPECIAL[lower];
        return childGender === "Женский" ? s.replace(/ович$/, "овна").replace(/евич$/, "евна").replace(/ич$/, "ична") : s;
    }
    const RULES = [["ий","евич","евна"],["ей","евич","евна"],["ый","ович","овна"],["ай","аевич","аевна"],
        ["ой","ович","овна"],["я","евич","евна"],["а","ович","овна"],["ь","евич","евна"],["г","оглы","кызы"],
        ["к","ович","овна"],["м","ович","овна"],["н","ович","овна"],["р","ович","овна"],["с","ович","овна"],
        ["т","ович","овна"],["в","ович","овна"],["й","евич","евна"]];
    for (const [end, maleS, femaleS] of RULES) {
        if (lower.endsWith(end)) {
            const stem = clean.slice(0, -end.length);
            if (!stem) continue;
            const suf = childGender === "Женский" ? femaleS : maleS;
            return (stem + suf).replace(/^./, c => c.toUpperCase());
        }
    }
    const last = lower.slice(-1);
    let suf = last === "ы" ? "евич" : last === "а" ? "ович" : last === "й" ? "евич" : "ович";
    if (childGender === "Женский") suf = suf.replace("ович","овна").replace("евич","евна");
    return (clean + suf).replace(/^./, c => c.toUpperCase());
}

function generateNameFromPatronymic(patronymic, gender) {
    if (!patronymic || !patronymic.trim()) return gender === "Мужской" ? "Неизвестный" : "Неизвестная";
    const pat = patronymic.trim().toLowerCase();
    const REVERSE = { никитич: "Никита", ильич: "Илья" };
    if (REVERSE[pat]) return REVERSE[pat];
    const RULES = [["ьевич","ий"],["ьевна","ий"],["евич","й"],["евна","й"],["ович",""],["овна",""],["оглы","г"],["кызы","г"]];
    for (const [suff, base] of RULES) {
        if (pat.endsWith(suff)) {
            const stem = patronymic.trim().slice(0, -suff.length);
            if (!stem) continue;
            return (stem + base).replace(/^./, c => c.toUpperCase());
        }
    }
    return gender === "Мужской" ? "Неизвестный" : "Неизвестная";
}

function getCurrentSurname(person) {
    return (person.gender === "Женский" && person.maiden_name) ? (person.maiden_name || person.surname) : (person.surname || "");
}

function validateDate(s) {
    if (!s || !s.trim()) return true;
    const p = s.trim().split(".");
    if (p.length !== 3) return false;
    try {
        const [d, m, y] = p.map(x => parseInt(x, 10));
        if (isNaN(d) || isNaN(m) || isNaN(y)) return false;
        if (String(y).length !== 4) return false;
        if (m < 1 || m > 12) return false;
        if (d < 1 || d > 31) return false;
        return true;
    } catch (_) { return false; }
}

function escapeHtml(s) {
    if (!s) return "";
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}

const PALETTE_DEFAULTS = {
    "CANVAS_BG": "#f5f0e8",
    "MALE_COLOR": "#1e40af",
    "FEMALE_COLOR": "#9d174d",
    "DECEASED_COLOR": "#64748b",
    "CENTER_COLOR": "#b45309",
    "CARD_HOVER_BORDER": "#eab308",
    "MARRIAGE_LINE_COLOR": "#b45309",
    "PARENT_LINE_COLOR": "#475569",
    "CARD_BORDER_COLOR": "#1e293b",
};
const PALETTE_LABELS = {
    "CANVAS_BG": "Фон холста",
    "MALE_COLOR": "Карточка: мужчина",
    "FEMALE_COLOR": "Карточка: женщина",
    "DECEASED_COLOR": "Карточка: умерший",
    "CENTER_COLOR": "Карточка: центр дерева",
    "CARD_HOVER_BORDER": "Подсветка при наведении",
    "MARRIAGE_LINE_COLOR": "Линия: супруги",
    "PARENT_LINE_COLOR": "Линия: родители–дети",
    "CARD_BORDER_COLOR": "Рамка карточки",
};
const PALETTE_CSS_MAP = {
    CANVAS_BG: "--bg",
    MALE_COLOR: "--card-male",
    FEMALE_COLOR: "--card-female",
    DECEASED_COLOR: "--card-deceased",
    CENTER_COLOR: "--card-center",
    CARD_HOVER_BORDER: "--card-hover",
    MARRIAGE_LINE_COLOR: "--line-marriage",
    PARENT_LINE_COLOR: "--line-parent",
    CARD_BORDER_COLOR: "--border",
};

function loadPalette() {
    try {
        const s = localStorage.getItem("tree_palette");
        if (!s) return;
        const data = JSON.parse(s);
        const root = document.documentElement;
        for (const [key, cssVar] of Object.entries(PALETTE_CSS_MAP)) {
            if (data[key]) root.style.setProperty(cssVar, data[key]);
        }
    } catch (_) {}
}

function savePalette(data) {
    try {
        localStorage.setItem("tree_palette", JSON.stringify(data));
    } catch (_) {}
}

function applyPaletteToCss(data) {
    const root = document.documentElement;
    for (const [key, cssVar] of Object.entries(PALETTE_CSS_MAP)) {
        if (data[key]) root.style.setProperty(cssVar, data[key]);
    }
}

function rgbToHex(rgbStr) {
    const m = rgbStr.match(/rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/);
    if (!m) return null;
    const r = ("0" + parseInt(m[1], 10).toString(16)).slice(-2);
    const g = ("0" + parseInt(m[2], 10).toString(16)).slice(-2);
    const b = ("0" + parseInt(m[3], 10).toString(16)).slice(-2);
    return "#" + r + g + b;
}

function openColorPaletteDialog() {
    const current = {};
    for (const k of Object.keys(PALETTE_DEFAULTS)) {
        const cssVar = PALETTE_CSS_MAP[k];
        let v = cssVar ? getComputedStyle(document.documentElement).getPropertyValue(cssVar).trim() : "";
        if (v && v.startsWith("rgb")) v = rgbToHex(v) || v;
        if (!v || !/^#[0-9a-fA-F]{6}$/.test(v)) v = PALETTE_DEFAULTS[k];
        current[k] = v;
    }

    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay";
    ov.innerHTML = `
        <div class="tree-modal tree-palette-modal">
            <h3>Цвет интерфейса</h3>
            <div class="palette-list" id="palette-list"></div>
            <div class="tree-modal-btns">
                <button type="button" class="cancel">По умолчанию</button>
                <button type="button" class="primary save">Применить</button>
            </div>
        </div>`;
    const list = ov.querySelector("#palette-list");

    function renderRows() {
        list.innerHTML = "";
        for (const key of Object.keys(PALETTE_DEFAULTS)) {
            const row = document.createElement("div");
            row.className = "palette-row";
            const label = document.createElement("span");
            label.className = "palette-label";
            label.textContent = PALETTE_LABELS[key] || key;
            const swatch = document.createElement("div");
            swatch.className = "palette-swatch";
            swatch.style.backgroundColor = current[key];
            const inp = document.createElement("input");
            inp.type = "color";
            inp.value = current[key];
            inp.style.opacity = "0";
            inp.style.position = "absolute";
            inp.style.width = "44px";
            inp.style.height = "24px";
            inp.style.cursor = "pointer";
            inp.oninput = () => {
                current[key] = inp.value;
                swatch.style.backgroundColor = inp.value;
            };
            row.appendChild(label);
            const swatchWrap = document.createElement("div");
            swatchWrap.className = "palette-swatch-wrap";
            swatchWrap.appendChild(swatch);
            swatchWrap.appendChild(inp);
            swatchWrap.onclick = () => inp.click();
            row.appendChild(swatchWrap);
            list.appendChild(row);
        }
    }
    renderRows();

    ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
    ov.querySelector(".tree-modal").onclick = (e) => e.stopPropagation();
    ov.querySelector(".cancel").onclick = () => {
        Object.assign(current, PALETTE_DEFAULTS);
        renderRows();
    };
    ov.querySelector(".save").onclick = () => {
        applyPaletteToCss(current);
        savePalette(current);
        ov.remove();
        render();
    };
    document.body.appendChild(ov);
}

function setupMenubar() {
    document.querySelectorAll(".tree-menubar .menu-dropdown").forEach(dd => {
        dd.onclick = (e) => e.stopPropagation();
    });
    document.querySelectorAll(".tree-menubar [data-action]").forEach(btn => {
        btn.onclick = () => {
            const act = btn.dataset.action;
            if (act === "new") {
                if (!confirm("Создать новое дерево? Текущие данные будут утрачены.")) return;
                treeData = { persons: {}, marriages: [], current_center: null };
                centerId = null;
                saveTree();
                render();
            } else if (act === "save") {
                saveTree();
                alert("Данные сохранены.");
            } else if (act === "export-csv") {
                exportToCsv();
            } else if (act === "import-csv") {
                document.getElementById("import-csv-input")?.click();
            } else if (act === "refresh") {
                loadTree();
            } else if (act === "zoom-reset") {
                treeZoom = 1;
                treePanX = 0;
                treePanY = 0;
                render();
            } else if (act === "collapse-all") {
                Object.values(treeData.persons || {}).forEach(p => { p.collapsed_branches = true; });
                saveTree();
                render();
            } else if (act === "expand-all") {
                Object.values(treeData.persons || {}).forEach(p => { p.collapsed_branches = false; });
                saveTree();
                render();
            } else if (act === "focus-mode") {
                focusModeActive = !focusModeActive;
                render();
            } else if (act === "filters") {
                openFiltersDialog();
            } else if (act === "color-palette") {
                openColorPaletteDialog();
            } else if (act === "search") {
                openSearchDialog();
            }
            document.querySelectorAll(".menu-item.open").forEach(m => m.classList.remove("open"));
        };
    });

    const csvInput = document.getElementById("import-csv-input");
    if (csvInput) {
        csvInput.onchange = (e) => {
            const file = e.target.files?.[0];
            e.target.value = "";
            if (!file) return;
            const r = new FileReader();
            r.onload = () => {
                try {
                    const data = parseCsvImport(r.result);
                    if (data) {
                        treeData.persons = { ...(treeData.persons || {}), ...data.persons };
                        const marMap = new Map();
                        (treeData.marriages || []).forEach(m => marMap.set([String(m[0]), String(m[1])].sort().join("|"), m));
                        (data.marriages || []).forEach(m => {
                            const k = [String(m[0]), String(m[1])].sort().join("|");
                            if (!marMap.has(k)) marMap.set(k, [String(m[0]), String(m[1])]);
                        });
                        treeData.marriages = [...marMap.values()];
                        saveTree();
                        render();
                        alert("Импорт завершён.");
                    }
                } catch (err) {
                    alert("Ошибка импорта: " + err.message);
                }
            };
            r.readAsText(file, "utf-8");
        };
    }

    document.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "f") {
            e.preventDefault();
            openSearchDialog();
        }
    });
    document.querySelectorAll(".tree-menubar .menu-label").forEach(lbl => {
        lbl.onclick = (e) => {
            e.stopPropagation();
            document.querySelectorAll(".menu-item.open").forEach(m => m.classList.remove("open"));
            lbl.closest(".menu-item").classList.toggle("open");
        };
    });
    document.addEventListener("click", () => {
        document.querySelectorAll(".menu-item.open").forEach(m => m.classList.remove("open"));
    });
}

function exportToCsv() {
    const fields = ["id", "name", "surname", "patronymic", "birth_date", "birth_place", "gender",
        "is_deceased", "death_date", "maiden_name", "photo_path", "parents", "children", "spouse_ids",
        "biography", "burial_place", "burial_date", "photo_album", "link_titles", "link_urls",
        "occupation", "education", "address", "notes"];
    const escapeCsv = (v) => {
        const s = String(v == null ? "" : v);
        if (/[;"\n,]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
        return s;
    };
    const rows = [];
    for (const [pid, p] of Object.entries(treeData.persons || {})) {
        const links = p.links || [];
        const linkTitles = links.map(l => l.title || "").join("|");
        const linkUrls = links.map(l => l.url || "").join("|");
        const photoAlbum = (p.photo_album || []).join("|");
        rows.push([
            pid, p.name || "", p.surname || "", p.patronymic || "", p.birth_date || "", p.birth_place || "",
            p.gender || "", p.is_deceased || false, p.death_date || "", p.maiden_name || "", p.photo_path || "",
            (p.parents || []).join(","), (p.children || []).join(","), (p.spouse_ids || []).join(","),
            (p.biography || "").replace(/\n/g, " "), p.burial_place || "", p.burial_date || "",
            photoAlbum, linkTitles, linkUrls,
            p.occupation || "", p.education || "", p.address || "", p.notes || ""
        ].map(escapeCsv).join(";"));
    }
    const csv = fields.join(";") + "\n" + rows.join("\n");
    const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "family_tree.csv";
    a.click();
    URL.revokeObjectURL(a.href);
}

function parseCsvImport(text) {
    const lines = text.split(/\r?\n/).filter(l => l.trim());
    if (!lines.length) return null;
    const headers = lines[0].split(";").map(h => h.replace(/^"|"$/g, ""));
    const persons = {};
    const marriages = new Set();
    for (let i = 1; i < lines.length; i++) {
        const vals = [];
        let cur = "", inQ = false;
        for (let j = 0; j < lines[i].length; j++) {
            const c = lines[i][j];
            if (c === '"') { inQ = !inQ; continue; }
            if (!inQ && c === ";") { vals.push(cur); cur = ""; continue; }
            cur += c;
        }
        vals.push(cur);
        const row = {};
        headers.forEach((h, idx) => { row[h] = vals[idx] || ""; });
        const pid = String(row.id || "").trim();
        if (!pid) continue;
        const parents = (row.parents || "").split(",").map(p => p.trim()).filter(Boolean);
        const children = (row.children || "").split(",").map(c => c.trim()).filter(Boolean);
        const spouseIds = (row.spouse_ids || "").split(",").map(s => s.trim()).filter(Boolean);
        const linkTitles = (row.link_titles || "").split("|");
        const linkUrls = (row.link_urls || "").split("|");
        const links = linkUrls.map((u, i) => ({ title: (linkTitles[i] || "").trim(), url: (u || "").trim() })).filter(l => l.url);
        const photoAlbum = (row.photo_album || "").split("|").map(p => p.trim()).filter(Boolean);
        persons[pid] = {
            name: (row.name || "").trim(), surname: (row.surname || "").trim(), patronymic: (row.patronymic || "").trim(),
            birth_date: (row.birth_date || "").trim(), birth_place: (row.birth_place || "").trim(),
            gender: (row.gender || "").trim() || "Мужской", is_deceased: /true|1|yes/i.test((row.is_deceased || "").trim()),
            death_date: (row.death_date || "").trim(), maiden_name: (row.maiden_name || "").trim(),
            photo_path: (row.photo_path || "").trim(), biography: (row.biography || "").replace(/  +/g, " ").trim(),
            burial_place: (row.burial_place || "").trim(), burial_date: (row.burial_date || "").trim(),
            photo_album: photoAlbum, links: links,
            occupation: (row.occupation || "").trim(), education: (row.education || "").trim(),
            address: (row.address || "").trim(), notes: (row.notes || "").trim(),
            parents: parents, children: children, spouse_ids: spouseIds,
        };
        spouseIds.forEach(sid => {
            if (sid && sid !== pid) marriages.add(JSON.stringify([pid, sid].sort()));
        });
    }
    return { persons, marriages: [...marriages].map(s => JSON.parse(s)) };
}

function openFiltersDialog() {
    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay";
    ov.innerHTML = `
        <div class="tree-modal tree-filters-modal">
            <h3>Фильтры</h3>
            <label>Пол</label>
            <select id="filter-gender">
                <option value="Все" ${activeFilters.gender === "Все" ? "selected" : ""}>Все</option>
                <option value="Только мужчины" ${activeFilters.gender === "Только мужчины" ? "selected" : ""}>Только мужчины</option>
                <option value="Только женщины" ${activeFilters.gender === "Только женщины" ? "selected" : ""}>Только женщины</option>
            </select>
            <label>Статус</label>
            <select id="filter-status">
                <option value="Все" ${activeFilters.status === "Все" ? "selected" : ""}>Все</option>
                <option value="Только живые" ${activeFilters.status === "Только живые" ? "selected" : ""}>Только живые</option>
            </select>
            <label><input type="checkbox" id="filter-photos" ${activeFilters.photos_only ? "checked" : ""}> Только с фото</label>
            <label><input type="checkbox" id="filter-childless" ${activeFilters.childless ? "checked" : ""}> Только бездетные</label>
            <div class="tree-modal-btns">
                <button type="button" class="cancel">Отмена</button>
                <button type="button" class="primary" id="filter-apply">Применить</button>
            </div>
        </div>`;
    ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
    ov.querySelector(".cancel").onclick = () => ov.remove();
    ov.querySelector("#filter-apply").onclick = () => {
        activeFilters.gender = ov.querySelector("#filter-gender").value;
        activeFilters.status = ov.querySelector("#filter-status").value;
        activeFilters.photos_only = !!ov.querySelector("#filter-photos").checked;
        activeFilters.childless = !!ov.querySelector("#filter-childless").checked;
        ov.remove();
        render();
    };
    ov.querySelector(".tree-modal").onclick = (e) => e.stopPropagation();
    document.body.appendChild(ov);
}

function openSearchDialog() {
    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay";
    ov.innerHTML = `
        <div class="tree-modal tree-search-modal">
            <h3>Найти</h3>
            <label>Поиск по имени, фамилии, отчеству, датам</label>
            <input type="text" id="search-query" placeholder="Введите текст...">
            <div id="search-results" class="search-results"></div>
            <div class="tree-modal-btns">
                <button type="button" class="cancel">Закрыть</button>
            </div>
        </div>`;
    const qInp = ov.querySelector("#search-query");
    const resultsEl = ov.querySelector("#search-results");

    const doSearch = () => {
        const q = (qInp.value || "").trim().toLowerCase();
        resultsEl.innerHTML = "";
        if (!q) return;
        const persons = treeData.persons || {};
        const found = [];
        for (const [pid, p] of Object.entries(persons)) {
            const text = [p.name, p.patronymic, p.surname, p.birth_date, p.death_date].filter(Boolean).join(" ").toLowerCase();
            if (text.includes(q)) found.push({ pid, p });
        }
        if (found.length === 0) {
            resultsEl.innerHTML = '<div class="muted">Ничего не найдено</div>';
        } else {
            found.forEach(({ pid, p }) => {
                const div = document.createElement("div");
                div.className = "search-result-item";
                div.textContent = [p.name, p.patronymic, p.surname].filter(Boolean).join(" ");
                div.onclick = () => {
                    centerId = pid;
                    treeData.current_center = pid;
                    saveTree();
                    ov.remove();
                    render();
                };
                resultsEl.appendChild(div);
            });
        }
    };
    qInp.oninput = doSearch;
    qInp.onkeydown = (e) => { if (e.key === "Enter") doSearch(); };

    ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
    ov.querySelector(".cancel").onclick = () => ov.remove();
    ov.querySelector(".tree-modal").onclick = (e) => e.stopPropagation();
    document.body.appendChild(ov);
    qInp.focus();
}

function setupDesktopAppButtons() {
    const btnExe = document.getElementById("btn-download-exe");
    const btnInstall = document.getElementById("btn-pwa-install");
    const btnOpen = document.getElementById("btn-pwa-open");
    const hint = document.getElementById("desktop-app-hint");
    if (!btnInstall || !btnOpen) return;

    const isWindows = /Win|Windows/i.test(navigator.userAgent) || /Windows/i.test(navigator.platform);
    const isStandalone = () =>
        window.matchMedia("(display-mode: standalone)").matches ||
        window.navigator.standalone === true;
    const isDesktopAppInstalled = () => localStorage.getItem("desktop-app-installed") === "1";

    function updateButtons() {
        const hide = (el) => { if (el) el.style.display = "none"; };
        const show = (el, d) => { if (el) el.style.display = d || "inline-block"; };
        if (isStandalone()) {
            hide(btnExe); hide(btnInstall); hide(btnOpen); hide(hint);
            return;
        }
        if (!isWindows) {
            hide(btnExe); hide(btnInstall); hide(btnOpen); hide(hint);
            return;
        }
        if (isDesktopAppInstalled()) {
            hide(btnExe); hide(btnInstall);
            show(btnOpen);
            hide(hint);
        } else {
            show(btnExe);
            show(btnInstall);
            hide(btnOpen);
            if (hint) {
                hint.style.display = "inline";
                hint.textContent = "Уже установлено?";
            }
        }
    }

    updateButtons();

    btnInstall.onclick = () => {
        // ?v= — обход кэша браузера, всегда скачивать свежий exe
        window.location.href = window.location.origin + "/download/desktop?v=" + Date.now();
    };

    btnOpen.onclick = () => {
        const url = window.location.origin + "/";
        const protocolUrl = "derevo://open?url=" + encodeURIComponent(url);
        // Создаём ссылку и кликаем — так браузеры надёжнее обрабатывают кастомные протоколы
        const a = document.createElement("a");
        a.href = protocolUrl;
        a.style.display = "none";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };

    if (hint) {
        hint.onclick = () => {
            localStorage.setItem("desktop-app-installed", "1");
            updateButtons();
        };
    }
}

if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {});
}

loadPalette();
loadTree();
setupMenubar();
setupDesktopAppButtons();