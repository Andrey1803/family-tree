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

/**
 * Рассчитывает возраст по дате рождения.
 * @param {string} birthDateStr - Дата рождения в формате "ДД.ММ.ГГГГ"
 * @param {string} deathDateStr - Дата смерти (опционально)
 * @param {boolean} isDeceased - Факт смерти
 * @returns {string} Возраст или "?"
 */
function calculateAge(birthDateStr, deathDateStr = "", isDeceased = false) {
    if (!birthDateStr) return "?";

    function parseDate(dateStr) {
        if (!dateStr) return null;
        const parts = dateStr.trim().split('.');
        if (parts.length !== 3) return null;
        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10) - 1;
        const year = parseInt(parts[2], 10);
        if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
        return new Date(year, month, day);
    }

    const birthDate = parseDate(birthDateStr);
    if (!birthDate) return "?";

    const endDate = isDeceased && deathDateStr ? parseDate(deathDateStr) : new Date();
    if (!endDate) return "?";

    let age = endDate.getFullYear() - birthDate.getFullYear();
    const birthMonthDay = birthDate.getMonth() * 100 + birthDate.getDate();
    const endMonthDay = endDate.getMonth() * 100 + endDate.getDate();

    if (endMonthDay < birthMonthDay) {
        age--;
    }

    return age >= 0 ? String(age) : "?";
}

/**
 * Преобразует дату в сортируемое значение.
 * @param {string} dateStr - Дата в формате "ДД.ММ.ГГГГ"
 * @returns {string} Строка в формате "ГГГГММДД" или "99999999" если дата невалидна
 */
function getSortableDate(dateStr) {
    if (!dateStr || typeof dateStr !== 'string' || dateStr.length !== 10) {
        return "99999999";
    }
    const parts = dateStr.split('.');
    if (parts.length !== 3) {
        return "99999999";
    }
    return `${parts[2]}${parts[1].padStart(2, '0')}${parts[0].padStart(2, '0')}`;
}

/**
 * Определяет знак зодиака по дате рождения.
 * @param {string} birthDateStr - Дата рождения в формате "ДД.ММ.ГГГГ"
 * @returns {string} Знак зодиака или пустая строка
 */
function getZodiacSign(birthDateStr) {
    if (!birthDateStr) return "";

    function parseDate(dateStr) {
        if (!dateStr) return null;
        const parts = dateStr.trim().split('.');
        if (parts.length !== 3) return null;
        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10);
        const year = parseInt(parts[2], 10);
        if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
        return { day, month, year };
    }

    const date = parseDate(birthDateStr);
    if (!date) return "";

    const day = date.day;
    const month = date.month;

    // Знаки зодиака
    if ((month === 12 && day >= 22) || (month === 1 && day <= 20)) return "♑ Козерог";
    if ((month === 1 && day >= 21) || (month === 2 && day <= 19)) return "♒ Водолей";
    if ((month === 2 && day >= 20) || (month === 3 && day <= 20)) return "♓ Рыбы";
    if ((month === 3 && day >= 21) || (month === 4 && day <= 20)) return "♈ Овен";
    if ((month === 4 && day >= 21) || (month === 5 && day <= 21)) return "♉ Телец";
    if ((month === 5 && day >= 22) || (month === 6 && day <= 21)) return "♊ Близнецы";
    if ((month === 6 && day >= 22) || (month === 7 && day <= 23)) return "♋ Рак";
    if ((month === 7 && day >= 24) || (month === 8 && day <= 23)) return "♌ Лев";
    if ((month === 8 && day >= 24) || (month === 9 && day <= 23)) return "♍ Дева";
    if ((month === 9 && day >= 24) || (month === 10 && day <= 23)) return "♎ Весы";
    if ((month === 10 && day >= 24) || (month === 11 && day <= 22)) return "♏ Скорпион";
    if ((month === 11 && day >= 23) || (month === 12 && day <= 21)) return "♐ Стрелец";

    return "";
}

async function loadTree() {
    console.log('[LOAD_TREE] Starting to load tree...');
    
    // Применяем палитру перед загрузкой
    loadPalette();
    
    // Сначала пробуем загрузить из backup в localStorage (для мобильных)
    const backup = localStorage.getItem('family_tree_backup');
    if (backup) {
        try {
            const backupData = JSON.parse(backup);
            if (backupData && backupData.persons && Object.keys(backupData.persons).length > 0) {
                console.log('[LOAD_TREE] Loaded from backup:', Object.keys(backupData.persons).length, 'persons');
                // Используем backup если сервер вернёт ошибку
                treeData = backupData;
            }
        } catch (e) {
            console.warn('[LOAD_TREE] Backup parse error:', e);
        }
    }
    
    const r = await fetch("/api/tree");
    console.log('[LOAD_TREE] Fetch response status:', r.status);
    if (r.status === 401) {
        console.log('[LOAD_TREE] 401 Unauthorized, redirecting to login');
        window.location.href = "/login";
        return;
    }
    if (!r.ok) {
        console.error('[LOAD_TREE] Response not ok:', r.status);
        // Если сервер не ответил, используем backup
        if (treeData && treeData.persons) {
            console.log('[LOAD_TREE] Using backup data');
            centerId = treeData.current_center || (Object.keys(treeData.persons)[0] || null);
            treeZoom = 0.5;
            treePanX = 0;
            treePanY = 0;
            render();
        }
        return;
    }
    treeData = await r.json();
    console.log('[LOAD_TREE] Loaded treeData:', treeData);
    console.log('[LOAD_TREE] Persons count:', Object.keys(treeData.persons || {}).length);
    console.log('[LOAD_TREE] Marriages:', treeData.marriages);
    console.log('[LOAD_TREE] Marriages type:', Array.isArray(treeData.marriages) ? 'array' : typeof treeData.marriages);
    if (Array.isArray(treeData.marriages)) {
        console.log('[LOAD_TREE] First marriage:', treeData.marriages[0]);
    }
    centerId = treeData.current_center || (Object.keys(treeData.persons)[0] || null);
    console.log('[LOAD_TREE] centerId:', centerId);

    // Сохраняем свежую версию в backup
    localStorage.setItem('family_tree_backup', JSON.stringify(treeData));

    // Сбрасываем зум и панорамирование при загрузке
    treeZoom = 0.5;  // Уменьшенный начальный зум
    treePanX = 0;
    treePanY = 0;

    render();

    // Центрируем дерево после рендеринга
    setTimeout(() => {
        const root = document.getElementById("tree-root");
        const wrap = root.querySelector(".tree-wrap");
        if (wrap) {
            const rootRect = root.getBoundingClientRect();
            const wrapRect = wrap.getBoundingClientRect();

            // Центрируем по центру экрана
            treePanX = (rootRect.width - wrapRect.width * treeZoom) / 2;
            treePanY = (rootRect.height - wrapRect.height * treeZoom) / 2;

            const panZoomWrapper = root.querySelector(".tree-pan-zoom");
            if (panZoomWrapper) {
                panZoomWrapper.style.transform = `translate(${treePanX}px,${treePanY}px)`;
            }
            console.log('[LOAD_TREE] Centered: panX=', treePanX, 'panY=', treePanY);
        }
    }, 100);
}

function render() {
    const root = document.getElementById("tree-root");
    const emptyMsg = document.getElementById("empty-msg");
    root.innerHTML = "";

    const persons = treeData.persons || {};
    const ids = Object.keys(persons);
    
    console.log('[RENDER] persons count:', ids.length);
    console.log('[RENDER] centerId:', centerId);
    console.log('[RENDER] treeData:', treeData);
    
    if (ids.length === 0) {
        console.log('[RENDER] No persons, showing empty message');
        emptyMsg.style.display = "block";
        const btn = document.getElementById("btn-add-first");
        if (btn) btn.onclick = () => addFirstPerson();
        updateStatusBar();
        return;
    }
    console.log('[RENDER] Rendering tree with', ids.length, 'persons');
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
    
    // Добавляем супругов из marriages в relatedRaw
    console.log('[RENDER] Processing marriages for related:', treeData.marriages);
    (treeData.marriages || []).forEach(m => {
        let a, b;
        if (Array.isArray(m)) {
            [a, b] = m;
        } else if (m.persons && Array.isArray(m.persons)) {
            [a, b] = m.persons;
        } else {
            return;
        }
        // Добавляем обоих супругов, если они есть в persons
        if (persons[String(a)]) {
            relatedRaw.add(String(a));
            collect(String(a), !focusModeActive);
        }
        if (persons[String(b)]) {
            relatedRaw.add(String(b));
            collect(String(b), !focusModeActive);
        }
        console.log('[RENDER] Added spouses from marriage:', a, b);
    });

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

    // Сначала рисуем карточки
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
        
        // Двойной тап для мобильных (открытие редактирования)
        let lastTapTime = 0;
        let lastTapX = 0, lastTapY = 0;
        
        card.addEventListener("touchend", (e) => {
            const currentTime = Date.now();
            const touch = e.changedTouches[0];
            const tapX = touch.clientX;
            const tapY = touch.clientY;
            
            // Проверяем, что это второй тап за 300мс в той же области
            if (currentTime - lastTapTime < 300 && 
                Math.abs(tapX - lastTapX) < 30 && 
                Math.abs(tapY - lastTapY) < 30) {
                e.preventDefault();
                if (!window._treeDidPan) {
                    editPerson(pid);
                }
            }
            lastTapTime = currentTime;
            lastTapX = tapX;
            lastTapY = tapY;
        });
        card.ondblclick = (e) => {
            e.preventDefault();
            if (window._treeDidPan) return;
            editPerson(pid);
        };
        
        // Контекстное меню для десктопа (правая кнопка)
        card.addEventListener("contextmenu", (e) => {
            e.preventDefault();
            showContextMenu(pid, e.clientX, e.clientY, persons);
        });
        
        // Долгий тап для мобильных (1 секунда) - ОДИН ПАЛЕЦ
        let longPressTimer;
        let touchStartTime;
        let touchStartX = 0, touchStartY = 0;
        let hasMoved = false;
        
        card.addEventListener("touchstart", (e) => {
            console.log('[CARD] touchstart on', pid, 'touches:', e.touches.length);
            // Реагируем ТОЛЬКО на один палец
            if (e.touches.length !== 1) {
                clearTimeout(longPressTimer);
                return;
            }
            card._longPressFired = false;
            const tx = e.touches[0].clientX, ty = e.touches[0].clientY;
            touchStartX = tx;
            touchStartY = ty;
            touchStartTime = Date.now();
            hasMoved = false;
            
            console.log('[LONG_PRESS] Touch start at', tx, ty);
            
            longPressTimer = setTimeout(() => {
                const touchDuration = Date.now() - touchStartTime;
                // Проверяем, что палец не двигался и не было панорамирования
                if (hasMoved || window._treeDidPan || touchDuration < 900) {
                    console.log('[LONG_PRESS] Cancelled: moved=', hasMoved, 'pan=', window._treeDidPan, 'duration=', touchDuration);
                    return;
                }
                
                card._longPressFired = true;
                console.log('[LONG_PRESS] Triggered!');
                // Показываем меню с вибрацией (если поддерживается)
                if (navigator.vibrate) navigator.vibrate(50);
                showContextMenu(pid, tx, ty, persons);
            }, 1000); // 1 секунда для долгого тапа
        }, { passive: true });
        
        // Отслеживаем движение пальца - сбрасываем таймер если сдвинулся
        card.addEventListener("touchmove", (e) => {
            // Если пальцев больше одного - сбрасываем
            if (e.touches.length !== 1) {
                hasMoved = true;
                clearTimeout(longPressTimer);
                return;
            }
            
            const touch = e.touches[0];
            const moveDistance = Math.hypot(touch.clientX - touchStartX, touch.clientY - touchStartY);
            if (moveDistance > 10) { // Если палец сдвинулся больше чем на 10px
                hasMoved = true;
                clearTimeout(longPressTimer);
                console.log('[LONG_PRESS] Moved too far:', moveDistance);
            }
        }, { passive: true });

        card.addEventListener("touchend", (e) => {
            clearTimeout(longPressTimer);
            // Предотвращаем клик если был долгий тап
            if (card._longPressFired && e.cancelable) {
                e.preventDefault();
            }
        });
        
        card.addEventListener("touchcancel", () => {
            console.log('[LONG_PRESS] Cancelled');
            clearTimeout(longPressTimer);
        });
        wrap.appendChild(card);
    });

    // Закрытие контекстного меню при клике/тапе вне его области
    document.addEventListener('click', function closeMenuOnClick(e) {
        if (window._ctxMenu) {
            const menu = window._ctxMenu;
            const isClickInsideMenu = menu.contains(e.target);
            const isClickOnCard = e.target.closest('.tree-card');
            
            // Закрываем если клик не внутри меню и не на карточке
            if (!isClickInsideMenu && !isClickOnCard) {
                closeContextMenu();
            }
        }
    }, true); // Используем capture phase для надёжности
    
    // Закрытие меню при тапе вне его (для мобильных)
    document.addEventListener('touchend', function closeMenuOnTouch(e) {
        if (window._ctxMenu) {
            const menu = window._ctxMenu;
            const isTouchInsideMenu = menu.contains(e.target);
            const isTouchOnCard = e.target.closest('.tree-card');
            
            if (!isTouchInsideMenu && !isTouchOnCard) {
                closeContextMenu();
            }
        }
    }, true);

    // Рисуем линии ПОСЛЕ карточек (чтобы они были поверх)
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", totalW);
    svg.setAttribute("height", totalH);
    svg.style.cssText = "position:absolute; top:0; left:0; pointer-events:none;";
    wrap.appendChild(svg);

    // Отладка: проверяем marriages
    console.log('[DEBUG] Marriages count:', (treeData.marriages || []).length);
    console.log('[DEBUG] Marriages:', treeData.marriages);
    console.log('[DEBUG] Coords keys:', Object.keys(coords));
    console.log('[DEBUG] Related size:', related.size);

    // Линии родитель–ребёнок
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
    let marriageLinesDrawn = 0;
    (treeData.marriages || []).forEach(m => {
        let a, b;
        if (Array.isArray(m)) {
            [a, b] = m;
        } else if (m.persons && Array.isArray(m.persons)) {
            [a, b] = m.persons;
        } else {
            console.log('[MARRIAGE] Invalid format:', m);
            return;
        }

        const idA = String(a), idB = String(b);
        console.log('[MARRIAGE] Processing:', idA, idB);
        console.log('[MARRIAGE] Has coords:', !!coords[idA], !!coords[idB]);
        console.log('[MARRIAGE] In related:', related.has(idA), related.has(idB));
        
        if (!coords[idA] || !coords[idB]) {
            console.log('[MARRIAGE] Skipping - no coords');
            return;
        }
        if (!related.has(idA) || !related.has(idB)) {
            console.log('[MARRIAGE] Skipping - not in related');
            return;
        }

        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        const yCenter = coords[idA].y + offsetY;
        const xA = coords[idA].x + offsetX;
        const xB = coords[idB].x + offsetX;
        const xLeft = Math.min(xA, xB);
        const xRight = Math.max(xA, xB);
        const cardHalfWidth = CARD_W / 2;
        const xLeftEdge = xLeft + cardHalfWidth;
        const xRightEdge = xRight - cardHalfWidth;

        line.setAttribute("x1", xLeftEdge);
        line.setAttribute("y1", yCenter);
        line.setAttribute("x2", xRightEdge);
        line.setAttribute("y2", yCenter);
        line.setAttribute("stroke", "#b45309");
        line.setAttribute("stroke-width", 2);
        line.setAttribute("stroke-dasharray", "4 4");
        line.setAttribute("stroke-linecap", "round");
        svg.appendChild(line);
        marriageLinesDrawn++;
        console.log('[MARRIAGE] Line drawn:', idA, '->', idB);
    });
    console.log('[MARRIAGE] Total lines drawn:', marriageLinesDrawn);

    setupPan(wrap, panZoomWrapper);
    setupZoom(panZoomWrapper, zoomContainer, wrap, totalW, totalH);
    updateStatusBar();
}

function updateStatusBar() {
    const centerEl = document.getElementById("status-center");
    const msgEl = document.getElementById("status-msg");
    const statsEl = document.getElementById("status-stats");
    if (!centerEl) return;
    const persons = treeData.persons || {};
    const p = centerId ? persons[centerId] : null;
    const name = p ? [p.name, p.patronymic, p.surname].filter(Boolean).join(" ") : "не выбран";
    centerEl.textContent = "Центр: " + name + (focusModeActive ? " 🔍" : "");
    if (msgEl) msgEl.textContent = focusModeActive ? "Режим фокуса: предки скрыты" : "";
    
    // Обновляем краткую статистику
    if (statsEl) {
        const personsCount = Object.keys(persons).length;
        const marriagesCount = (treeData.marriages || []).length;
        statsEl.textContent = `📊 Персон: ${personsCount} | Браков: ${marriagesCount}`;
    }
}

function setupZoom(panZoomWrapper, zoomContainer, wrap, totalW, totalH) {
    const viewport = wrap.closest("#tree-root");
    if (!viewport) return;

    // Изначально transform-origin в 0 0
    wrap.style.transformOrigin = "0 0";

    const applyZoom = (newZoom, centerX, centerY) => {
        const oldZoom = treeZoom;
        const clampedZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, newZoom));
        
        // Если зум не изменился, всё равно обновляем панорамирование для точки
        if (clampedZoom === oldZoom) {
            // Даже если зум не изменился, точка должна остаться на месте
            if (centerX !== undefined && centerY !== undefined) {
                const contentX = (centerX - treePanX) / oldZoom;
                const contentY = (centerY - treePanY) / oldZoom;
                treePanX = centerX - contentX * oldZoom;
                treePanY = centerY - contentY * oldZoom;
                panZoomWrapper.style.transform = `translate(${treePanX}px,${treePanY}px)`;
            }
            return;
        }
        
        treeZoom = clampedZoom;

        zoomContainer.style.width = (totalW * treeZoom) + "px";
        zoomContainer.style.height = (totalH * treeZoom) + "px";
        wrap.style.transform = `scale(${treeZoom})`;

        // Корректируем панорамирование: точка (centerX, centerY) должна остаться на месте
        if (centerX !== undefined && centerY !== undefined) {
            // Координата точки в масштабируемом контенте до зума
            const contentX = (centerX - treePanX) / oldZoom;
            const contentY = (centerY - treePanY) / oldZoom;

            // После зума эта точка контента должна быть на (centerX, centerY)
            treePanX = centerX - contentX * treeZoom;
            treePanY = centerY - contentY * treeZoom;
        }

        panZoomWrapper.style.transform = `translate(${treePanX}px,${treePanY}px)`;
    };

    // Wheel zoom (desktop + touchpad)
    panZoomWrapper.addEventListener("wheel", (e) => {
        e.preventDefault();
        const rect = viewport.getBoundingClientRect();
        const cx = e.clientX - rect.left;
        const cy = e.clientY - rect.top;
        const factor = e.deltaY > 0 ? 0.9 : 1.1;
        applyZoom(treeZoom * factor, cx, cy);
    }, { passive: false });

    // Pinch zoom (mobile)
    let pinchDist0, zoom0, pinchCenterX, pinchCenterY;
    let pinchStartTime = 0;

    panZoomWrapper.addEventListener("touchstart", (e) => {
        console.log('[PINCH] touchstart, touches:', e.touches.length);
        if (e.touches.length === 2) {
            pinchStartTime = Date.now();
            pinchDist0 = Math.hypot(e.touches[1].clientX - e.touches[0].clientX, e.touches[1].clientY - e.touches[0].clientY);
            zoom0 = treeZoom;
            const rect = viewport.getBoundingClientRect();
            // Вычисляем центр между двумя пальцами относительно viewport
            pinchCenterX = (e.touches[0].clientX + e.touches[1].clientX) / 2 - rect.left;
            pinchCenterY = (e.touches[0].clientY + e.touches[1].clientY) / 2 - rect.top;
            console.log('[PINCH] Started dist:', pinchDist0, 'zoom:', zoom0);
        }
    }, { passive: true });

    panZoomWrapper.addEventListener("touchmove", (e) => {
        if (e.touches.length === 2 && pinchDist0) {
            e.preventDefault();
            const dist = Math.hypot(e.touches[1].clientX - e.touches[0].clientX, e.touches[1].clientY - e.touches[0].clientY);

            // Пересчитываем центр щипка для текущего кадра
            const rect = viewport.getBoundingClientRect();
            const currentCenterX = (e.touches[0].clientX + e.touches[1].clientX) / 2 - rect.left;
            const currentCenterY = (e.touches[0].clientY + e.touches[1].clientY) / 2 - rect.top;

            // Вычисляем новый зум
            const newZoom = zoom0 * (dist / pinchDist0);
            applyZoom(newZoom, currentCenterX, currentCenterY);

            // Обновляем pinchDist0 и zoom0 для следующего кадра (чтобы избежать накопления ошибки)
            pinchDist0 = dist;
            zoom0 = treeZoom; // Используем актуальный treeZoom после применения зума
        }
    }, { passive: false });

    panZoomWrapper.addEventListener("touchend", (e) => {
        // Сначала проверяем pinch — если был, не делаем double-tap
        const wasPinch = pinchDist0 !== null;
        
        // Очищаем pinch переменные
        if (e.touches.length < 2) {
            pinchDist0 = null;
            pinchCenterX = null;
            pinchCenterY = null;
            zoom0 = null;
        }
        
        // Double tap zoom (mobile) — только если не было pinch и pan
        if (!wasPinch && !window._treeDidPan) {
            const currentTime = new Date().getTime();
            const tapLength = currentTime - lastTap;
            if (tapLength < 500 && tapLength > 0 && e.changedTouches.length === 1) {
                e.preventDefault();
                const rect = viewport.getBoundingClientRect();
                const touch = e.changedTouches[0];
                const tx = touch.clientX - rect.left;
                const ty = touch.clientY - rect.top;

                // Увеличиваем или уменьшаем зум
                if (treeZoom > 1) {
                    applyZoom(1, tx, ty);
                } else {
                    applyZoom(2, tx, ty);
                }
            }
            lastTap = currentTime;
        }
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
        // Сбрасываем флаг через небольшую задержку, чтобы double-tap не сработал сразу после pan
        setTimeout(() => { window._treeDidPan = false; }, 100);
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
        // Если 2 пальца — это pinch, не панорамируем
        if (e.touches.length !== 1) {
            stopTouchPan();
            return;
        }
        // preventDefault только если действительно панорамируем
        if (active) e.preventDefault();
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
        // Сбрасываем флаг через небольшую задержку, чтобы double-tap не сработал сразу после pan
        setTimeout(() => { window._treeDidPan = false; }, 100);
    };
    const onTouchEnd = stopTouchPan;
    viewport.style.cursor = "grab";
    viewport.addEventListener("mousedown", (e) => {
        if (e.button !== 0) return;
        startPan(e.clientX, e.clientY);
    });
    viewport.addEventListener("touchstart", (e) => {
        // Начинаем pan только если 1 палец
        if (e.touches.length !== 1) return;
        // НЕ делаем preventDefault - позволяем событиям проходить к карточкам
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
    }, { passive: true });
}

function setCenterAndSave(pid) {
    centerId = pid;
    treeData.current_center = pid;
    saveTree();
    render();
}

async function saveTree() {
    // Сохраняем в localStorage сразу (для мобильных)
    if (treeData && treeData.persons) {
        localStorage.setItem('family_tree_backup', JSON.stringify(treeData));
    }
    
    // Отправляем на сервер
    try {
        await fetch("/api/tree", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(treeData),
        });
        console.log('[SAVE] Tree saved successfully at', new Date().toLocaleTimeString());
    } catch (e) {
        console.error('[SAVE] Error:', e);
    }
}

function showContextMenu(pid, x, y, persons) {
    closeContextMenu(); // снимает предыдущее меню и его document listener
    const p = persons[pid];
    if (!p) return;

    const menu = document.createElement("div");
    menu.className = "tree-context-menu";
    
    // Адаптивное позиционирование для мобильных
    const isMobile = window.innerWidth <= 480;
    const menuWidth = isMobile ? Math.min(200, window.innerWidth - 16) : 180;
    const menuHeight = 300; // примерная высота
    
    let left = x;
    let top = y;
    
    // На мобильных центрируем меню по горизонтали
    if (isMobile) {
        left = (window.innerWidth - menuWidth) / 2;
        top = Math.max(10, (window.innerHeight - menuHeight) / 2);
    } else {
        // На десктопе позиционируем рядом с кликом
        if (x + menuWidth > window.innerWidth) {
            left = x - menuWidth;
        }
        if (y + menuHeight > window.innerHeight) {
            top = y - menuHeight;
        }
    }
    
    menu.style.left = left + "px";
    menu.style.top = top + "px";

    const hasFather = (p.parents || []).some(prId => persons[prId]?.gender === "Мужской");
    const hasMother = (p.parents || []).some(prId => persons[prId]?.gender === "Женский");
    const subItems = [
        !hasFather && { label: "👨 Отец...", color: "#1e40af", action: () => addRelative(pid, "father") },
        !hasMother && { label: "👩 Мать...", color: "#dc2626", action: () => addRelative(pid, "mother") },
        { label: "👦 Сын...", color: "#1e40af", action: () => addRelative(pid, "son") },
        { label: "👧 Дочь...", color: "#dc2626", action: () => addRelative(pid, "daughter") },
        { label: "👤 Брат...", color: "#1e40af", action: () => addRelative(pid, "brother") },
        { label: "👤 Сестра...", color: "#dc2626", action: () => addRelative(pid, "sister") },
        { label: "💍 Супруг(а)...", action: () => addRelative(pid, "spouse") },
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
                if (s.color) {
                    si.style.color = s.color;
                    si.style.fontWeight = "500";
                }
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

    // Финальная проверка границ (для десктопа)
    if (!isMobile) {
        const rect = menu.getBoundingClientRect();
        if (rect.right > window.innerWidth) menu.style.left = (x - rect.width) + "px";
        if (rect.bottom > window.innerHeight) menu.style.top = (y - rect.height) + "px";
    }
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

    // Сохраняем состояние перед редактированием
    if (window.undoManager) window.undoManager.beforeEdit(treeData, pid);

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
                    <div id="ed-age-info" class="age-info" style="margin-top: 4px; font-size: 0.85rem; color: #64748b;"></div>
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
                    <div id="ed-spouses">${(p.spouse_ids || []).map((s, idx) => {
                        const marriageDate = p.spouse_dates && p.spouse_dates[idx] ? p.spouse_dates[idx] : '';
                        return `<div class="ed-family-item ed-spouse-row" data-spouse-id="${escapeHtml(String(s))}">
                            <span class="spouse-name">${escapeHtml(displayName(s))}</span>
                            <input type="text" class="spouse-date" placeholder="Дата брака (ДД.ММ.ГГГГ)" value="${escapeHtml(marriageDate)}" data-spouse="${escapeHtml(String(s))}">
                            <button type="button" class="btn-remove-spouse" data-spouse="${escapeHtml(String(s))}" title="Удалить связь">✕</button>
                        </div>`;
                    }).join("") || '<div class="muted">— Нет</div>'}</div>
                    <button type="button" class="btn-add-row" id="ed-add-spouse">+ Добавить супруга</button>
                    <h4>Дети</h4>
                    <div id="ed-children">${(p.children || []).sort((a, b) => {
                        const dateA = getSortableDate(persons[a]?.birth_date);
                        const dateB = getSortableDate(persons[b]?.birth_date);
                        if (dateA !== dateB) return dateA.localeCompare(dateB);
                        return String(a).localeCompare(String(b));
                    }).map(c => {
                        const child = persons[c];
                        const ageText = child?.birth_date ? ` (${calculateAge(child.birth_date, child.death_date, child.is_deceased)} л.)` : '';
                        return `<div class="ed-family-item ed-child-row">
                            <span class="child-name">${escapeHtml(displayName(c))}${ageText}</span>
                            <button type="button" class="btn-view-child" data-child="${escapeHtml(String(c))}" title="Просмотр">👁</button>
                            <button type="button" class="btn-edit-child" data-child="${escapeHtml(String(c))}" title="Редактировать">✏</button>
                        </div>`;
                    }).join("") || '<div class="muted">— Нет</div>'}</div>
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
                    <button type="button" class="cancel">О��мена</button>
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

    // Обработчики для кнопок детей
    ov.querySelectorAll(".btn-view-child").forEach(btn => {
        btn.onclick = () => {
            const childId = btn.dataset.child;
            ov.remove();
            editPerson(childId);
        };
    });

    ov.querySelectorAll(".btn-edit-child").forEach(btn => {
        btn.onclick = () => {
            const childId = btn.dataset.child;
            ov.remove();
            editPerson(childId);
        };
    });

    function updateAgeInfo() {
        const birthDateVal = (ov.querySelector("#ed-birth")?.value || "").trim();
        const isDeceased = ov.querySelector("#ed-deceased")?.checked || false;
        const deathDateVal = (ov.querySelector("#ed-death")?.value || "").trim();
        const ageInfoEl = ov.querySelector("#ed-age-info");

        if (!ageInfoEl) return;

        if (!birthDateVal) {
            ageInfoEl.textContent = "";
            return;
        }

        const age = calculateAge(birthDateVal, isDeceased ? deathDateVal : "", isDeceased);
        const zodiac = getZodiacSign(birthDateVal);

        if (age !== "?" || zodiac) {
            let infoText = "(";
            if (age !== "?") infoText += `${age} лет`;
            if (zodiac) infoText += `, ${zodiac}`;
            infoText += ")";
            ageInfoEl.textContent = infoText;
        } else {
            ageInfoEl.textContent = "";
        }
    }

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
        updateAgeInfo();
    };
    ov.querySelector("#ed-gender").onchange = () => {
        ov.querySelector("#ed-maiden-row").style.display = ov.querySelector("#ed-gender").value === "Женский" ? "flex" : "none";
    };

    // Обновление информации о возрасте и знаке зодиака
    ov.querySelector("#ed-birth").oninput = updateAgeInfo;
    ov.querySelector("#ed-death").oninput = updateAgeInfo;
    updateAgeInfo();  // Первоначальное обновление

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
        
        // Сохраняем даты браков
        const spouseDates = [];
        ov.querySelectorAll(".spouse-date").forEach(inp => {
            spouseDates.push(inp.value.trim());
        });
        if (spouseDates.length > 0) {
            p.spouse_dates = spouseDates;
        }
        
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
    
    // Сохраняем состояние перед удалением
    if (window.undoManager) window.undoManager.beforeDeletePerson(treeData, pid);
    
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
    // Сохраняем состояние перед добавлением
    if (window.undoManager) window.undoManager.beforeAddPerson(treeData);

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
    
    ov.querySelector(".save").onclick = async () => {
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
        
        // Ждём сохранения перед закрытием
        await saveTree();
        ov.remove();
        render();
    };
    document.body.appendChild(ov);
}

function addRelative(pid, relation) {
    const persons = treeData.persons;
    const p = persons[pid];
    if (!p) return;
    
    // Сохраняем состояние перед добавлением родственника
    if (window.undoManager) window.undoManager.beforeAddRelative(treeData);
    
    if ((relation === "brother" || relation === "sister") && (!p.parents || p.parents.length === 0)) {
        alert("Для добавления брата/сестры у персоны должны бы����ь родители.");
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
    if (!patronymic || !patronymic.trim()) return gender === "Мужской" ? "Неизвестный" : "��������������еизвестная";
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

/**
 * Менеджер резервных копий
 */
function showBackupManager() {
    fetch("/api/backup/list")
        .then(r => r.json())
        .then(data => {
            const backups = data.backups || [];
            const ov = document.createElement("div");
            ov.className = "tree-modal-overlay";
            ov.innerHTML = `
                <div class="tree-modal tree-backup-modal">
                    <h3>Резервные копии</h3>
                    <div class="backup-list" id="backup-list">
                        ${backups.length === 0 ? '<div class="muted">Нет резервных копий</div>' : ''}
                        ${backups.map(b => `
                            <div class="backup-item" data-filename="${escapeHtml(b.filename)}">
                                <div class="backup-info">
                                    <div class="backup-name">${escapeHtml(b.filename)}</div>
                                    <div class="backup-meta">${formatFileSize(b.size)} • ${formatDate(b.created_at)}</div>
                                </div>
                                <button type="button" class="btn-restore" data-filename="${escapeHtml(b.filename)}">Восстановить</button>
                            </div>
                        `).join('')}
                    </div>
                    <div class="tree-modal-btns">
                        <button type="button" class="cancel">Закрыть</button>
                        <button type="button" class="primary" id="btn-create-backup">Создать копию</button>
                    </div>
                </div>`;
            
            ov.querySelector(".cancel").onclick = () => ov.remove();
            ov.querySelector("#btn-create-backup").onclick = () => {
                ov.remove();
                fetch("/api/backup/create", { method: "POST" })
                    .then(r => r.blob())
                    .then(blob => {
                        const a = document.createElement("a");
                        a.href = URL.createObjectURL(blob);
                        a.download = `backup_${new Date().toISOString().slice(0,10)}.zip`;
                        a.click();
                    });
            };
            ov.querySelectorAll(".btn-restore").forEach(btn => {
                btn.onclick = () => {
                    if (!confirm("Восстановить из этой копии? Текущие данные будут заменены.")) return;
                    fetch("/api/backup/restore", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ filename: btn.dataset.filename }),
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.ok) {
                            alert("Дерево восстановлено!");
                            loadTree();
                            ov.remove();
                        } else {
                            alert("Ошибка: " + (data.error || "Неизвестная"));
                        }
                    });
                };
            });
            ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
            document.body.appendChild(ov);
        });
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' Б';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' КБ';
    return (bytes / (1024 * 1024)).toFixed(1) + ' МБ';
}

function formatDate(iso) {
    try {
        const d = new Date(iso);
        return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch { return iso; }
}

/**
 * Временная шкала (улучшенная версия)
 * Аналогично desktop-версии: горизонтальные полосы, зум, перетаскивание, события
 */
function openTimeline() {
    const persons = treeData.persons || {};
    const events = [];
    const personsWithDates = [];
    
    // Фильтруем персоны с датами рождения
    for (const [pid, p] of Object.entries(persons)) {
        if (p.birth_date) {
            const birthYear = parseYear(p.birth_date);
            const deathYear = p.is_deceased && p.death_date ? parseYear(p.death_date) : null;
            personsWithDates.push({
                id: pid,
                ...p,
                birthYear,
                deathYear,
                age: deathYear && birthYear ? deathYear - birthYear : null,
            });
        }
    }
    
    if (personsWithDates.length === 0) {
        alert("Нет персон с датами рождения");
        return;
    }
    
    // Диапазон лет
    const allYears = personsWithDates.flatMap(p => [p.birthYear, p.deathYear].filter(Boolean));
    const minYear = Math.min(...allYears) - 5;
    const maxYear = Math.max(...allYears) + 5;
    
    // Сортировка по году рождения
    personsWithDates.sort((a, b) => a.birthYear - b.birthYear);
    
    // Создаем модальное окно
    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay timeline-overlay";
    ov.innerHTML = `
        <div class="tree-timeline-full">
            <div class="timeline-header">
                <h3>📅 Временная шкала жизней</h3>
                <div class="timeline-toolbar">
                    <div class="toolbar-group">
                        <label>Масштаб:</label>
                        <select id="timeline-scale">
                            <option value="0.5">5 лет/см</option>
                            <option value="1" selected>2 года/см</option>
                            <option value="2">1 год/см</option>
                            <option value="5">0.5 года/см</option>
                        </select>
                    </div>
                    <div class="toolbar-group">
                        <label>Фильтр:</label>
                        <select id="timeline-filter">
                            <option value="all">Все персоны</option>
                            <option value="male">Мужчины</option>
                            <option value="female">Женщины</option>
                            <option value="with_photos">Только с фото</option>
                        </select>
                    </div>
                    <div class="toolbar-group">
                        <button type="button" class="btn-zoom-in" title="Увеличить">🔍+</button>
                        <button type="button" class="btn-zoom-out" title="Уменьшить">🔍-</button>
                        <button type="button" class="btn-refresh" title="Обновить">🔄</button>
                    </div>
                </div>
                <div class="timeline-legend">
                    <span>👶 Рождение</span>
                    <span>💍 Брак</span>
                    <span>📌 Событие</span>
                    <span class="legend-hint">| Двойной клик — переход к персоне | Колесо — зум | Перетаскивание — панорамирование</span>
                </div>
            </div>
            <div class="timeline-canvas-container" id="timeline-canvas">
                <svg class="timeline-svg" id="timeline-svg"></svg>
            </div>
            <div class="timeline-footer">
                <span id="timeline-status">Персон: ${personsWithDates.length} | Диапазон: ${minYear}—${maxYear}</span>
                <button type="button" class="btn-close">Закрыть</button>
            </div>
        </div>`;
    
    // Переменные состояния
    let timelineZoom = 1;
    let timelinePanX = 0;
    let timelinePanY = 0;
    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;
    const pixelsPerYearBase = 20;
    
    const svg = ov.querySelector("#timeline-svg");
    const container = ov.querySelector("#timeline-canvas");
    const scaleSelect = ov.querySelector("#timeline-scale");
    const filterSelect = ov.querySelector("#timeline-filter");
    
    // Функция отрисовки
    function drawTimeline() {
        const scaleMultiplier = parseFloat(scaleSelect.value);
        const filterType = filterSelect.value;
        const pixelsPerYear = pixelsPerYearBase * timelineZoom * scaleMultiplier;
        
        // Применяем фильтр
        let filtered = [...personsWithDates];
        if (filterType === "male") filtered = filtered.filter(p => p.gender === "Мужской");
        else if (filterType === "female") filtered = filtered.filter(p => p.gender === "Женский");
        else if (filterType === "with_photos") filtered = filtered.filter(p => p.photo || p.photo_path);
        
        if (filtered.length === 0) {
            svg.innerHTML = '<text x="500" y="200" font-size="14" fill="#64748b">Нет персон по выбранному фильтру</text>';
            return;
        }
        
        const rowHeight = 40;
        const yOffset = 80;
        const totalWidth = (maxYear - minYear) * pixelsPerYear + 200;
        const totalHeight = yOffset + filtered.length * rowHeight + 100;
        
        svg.setAttribute("width", totalWidth);
        svg.setAttribute("height", totalHeight);
        svg.setAttribute("viewBox", `${-timelinePanX} ${-timelinePanY} ${container.clientWidth} ${container.clientHeight}`);
        
        let content = '';
        
        // Шкала лет
        content += `<g class="year-scale">`;
        for (let year = minYear; year <= maxYear; year++) {
            const x = (year - minYear) * pixelsPerYear;
            const isDecade = year % 10 === 0;
            const isFiveYear = year % 5 === 0;
            
            if (isDecade) {
                content += `<line x1="${x}" y1="40" x2="${x}" y2="55" stroke="#64748b" stroke-width="1"/>`;
                content += `<text x="${x+3}" y="70" font-size="9" fill="#1e293b">${year}</text>`;
            } else if (isFiveYear) {
                content += `<line x1="${x}" y1="40" x2="${x}" y2="50" stroke="#94a3b8" stroke-width="1"/>`;
            } else {
                content += `<line x1="${x}" y1="45" x2="${x}" y2="55" stroke="#cbd5e1" stroke-width="1"/>`;
            }
        }
        content += `<line x1="0" y1="55" x2="${totalWidth}" y2="55" stroke="#64748b" stroke-width="1"/>`;
        content += `</g>`;
        
        // Полосы жизней
        filtered.forEach((p, i) => {
            const y = yOffset + i * rowHeight;
            const xStart = (p.birthYear - minYear) * pixelsPerYear;
            const lifeYears = p.deathYear ? p.deathYear - p.birthYear : (new Date().getFullYear() - p.birthYear);
            const width = Math.max(50, lifeYears * pixelsPerYear);
            const color = p.gender === "Мужской" ? "#60a5fa" : "#f472b6";
            
            // Полоса
            content += `<g class="person-bar" data-pid="${p.id}" data-x="${xStart}" data-y="${y}" data-width="${width}">`;
            content += `<rect x="${xStart}" y="${y}" width="${width}" height="${rowHeight - 4}" fill="${color}" stroke="#1e293b" stroke-width="1" rx="4" class="person-life"/>`;
            
            // Имя
            let nameText = `${p.surname || ''} ${p.name || ''}`.trim();
            const maxNameWidth = width - 40;
            while (nameText.length > 3 && nameText.length * 7 > maxNameWidth) {
                nameText = nameText.slice(0, -1);
            }
            if (nameText.length < `${p.surname || ''} ${p.name || ''}`.trim().length) {
                nameText = nameText.slice(0, -3) + '...';
            }
            content += `<text x="${xStart + 5}" y="${y + (rowHeight - 4) / 2 + 3}" font-size="8" font-weight="bold" fill="#ffffff">${escapeHtml(nameText)}</text>`;
            
            // Даты и возраст
            if (width > 80) {
                const ageText = p.age ? ` (${p.age} лет)` : '';
                const deathDisplay = p.deathYear || (p.is_deceased ? 'н.д.' : new Date().getFullYear());
                content += `<text x="${xStart + width - 5}" y="${y + (rowHeight - 4) / 2 + 3}" font-size="7" fill="#ffffff" text-anchor="end">${p.birthYear}—${deathDisplay}${ageText}</text>`;
            }
            
            // События (рождение детей)
            if (p.children && p.children.length > 0) {
                p.children.forEach((childId, idx) => {
                    const child = persons[childId];
                    if (child && child.birth_date) {
                        const childYear = parseYear(child.birth_date);
                        const eventX = (childYear - minYear) * pixelsPerYear;
                        content += `<text x="${eventX - 5}" y="${y + rowHeight / 2 + 3}" font-size="10" class="event-icon">👶</text>`;
                    }
                });
            }
            
            // Двойной клик для перехода
            content += `</g>`;
        });
        
        svg.innerHTML = content;
        
        // Обработчики для полос
        svg.querySelectorAll(".person-bar").forEach(bar => {
            bar.style.cursor = "pointer";
            bar.addEventListener("dblclick", (e) => {
                const pid = bar.dataset.pid;
                if (pid) {
                    ov.remove();
                    centerId = pid;
                    treeData.current_center = pid;
                    saveTree();
                    render();
                }
            });
        });
        
        // Обновляем статус
        ov.querySelector("#timeline-status").textContent = `Персон: ${filtered.length} | Диапазон: ${minYear}—${maxYear} | Масштаб: ${(timelineZoom * parseFloat(scaleSelect.value)).toFixed(1)}x`;
    }
    
    // Перетаскивание
    container.addEventListener("mousedown", (e) => {
        isDragging = true;
        dragStartX = e.clientX - timelinePanX;
        dragStartY = e.clientY - timelinePanY;
        container.style.cursor = "grabbing";
    });

    container.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        e.preventDefault();
        timelinePanX = e.clientX - dragStartX;
        timelinePanY = e.clientY - dragStartY;
        drawTimeline();
    });
    
    container.addEventListener("mouseup", () => {
        isDragging = false;
        container.style.cursor = "grab";
    });
    
    container.addEventListener("mouseleave", () => {
        isDragging = false;
        container.style.cursor = "grab";
    });
    
    // Зум колесом
    container.addEventListener("wheel", (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        timelineZoom = Math.max(0.5, Math.min(5, timelineZoom * delta));
        drawTimeline();
    }, { passive: false });
    
    // Кнопки зума
    ov.querySelector(".btn-zoom-in").onclick = () => {
        timelineZoom = Math.min(5, timelineZoom * 1.2);
        drawTimeline();
    };
    ov.querySelector(".btn-zoom-out").onclick = () => {
        timelineZoom = Math.max(0.5, timelineZoom / 1.2);
        drawTimeline();
    };
    
    // Изменение масштаба и фильтра
    scaleSelect.onchange = drawTimeline;
    filterSelect.onchange = drawTimeline;
    
    // Обновление
    ov.querySelector(".btn-refresh").onclick = () => {
        loadTree();
        setTimeout(() => {
            alert("Данные обновлены");
        }, 500);
    };
    
    // Закрытие
    ov.querySelector(".btn-close").onclick = () => ov.remove();
    ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
    
    document.body.appendChild(ov);
    
    // Инициализация
    container.style.cursor = "grab";
    drawTimeline();
}

function parseYear(dateStr) {
    if (!dateStr) return null;
    const parts = dateStr.split(".");
    if (parts.length === 3) {
        return parseInt(parts[2], 10);
    }
    return null;
}

/**
 * Статистика дерева
 */
function showStats() {
    fetch("/api/stats")
        .then(r => r.json())
        .then(stats => {
            const ov = document.createElement("div");
            ov.className = "tree-modal-overlay";
            ov.innerHTML = `
                <div class="tree-modal tree-stats-modal">
                    <h3>📊 Статистика дерева</h3>
                    <div class="stats-grid">
                        <div class="stat-item"><span class="stat-label">Всего персон:</span><span class="stat-value">${stats.total_persons}</span></div>
                        <div class="stat-item"><span class="stat-label">Мужчин:</span><span class="stat-value">${stats.male_count}</span></div>
                        <div class="stat-item"><span class="stat-label">Женщин:</span><span class="stat-value">${stats.female_count}</span></div>
                        <div class="stat-item"><span class="stat-label">Живых:</span><span class="stat-value">${stats.living_count}</span></div>
                        <div class="stat-item"><span class="stat-label">Умерших:</span><span class="stat-value">${stats.deceased_count}</span></div>
                        <div class="stat-item"><span class="stat-label">Браков:</span><span class="stat-value">${stats.marriages_count}</span></div>
                        <div class="stat-item"><span class="stat-label">Поколений:</span><span class="stat-value">${stats.max_generations}</span></div>
                        ${stats.average_age ? `<div class="stat-item"><span class="stat-label">Средний возраст:</span><span class="stat-value">${stats.average_age} лет</span></div>` : ''}
                    </div>
                    ${stats.top_birth_places && stats.top_birth_places.length > 0 ? `
                        <h4>Места рождения</h4>
                        <ul class="places-list">
                            ${stats.top_birth_places.map(([place, count]) => `<li>${escapeHtml(place)}: ${count}</li>`).join('')}
                        </ul>
                    ` : ''}
                    <div class="tree-modal-btns">
                        <button type="button" class="cancel">Закрыть</button>
                    </div>
                </div>`;
            
            ov.querySelector(".cancel").onclick = () => ov.remove();
            ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
            document.body.appendChild(ov);
        });
}

/**
 * Проверка обновлений
 */
function checkUpdates() {
    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay";
    ov.innerHTML = `
        <div class="tree-modal tree-updates-modal">
            <h3>🔄 Проверка обновлений</h3>
            <div class="updates-content">
                <p>Проверка...</p>
            </div>
            <div class="tree-modal-btns">
                <button type="button" class="cancel">Закрыть</button>
            </div>
        </div>`;
    
    ov.querySelector(".cancel").onclick = () => ov.remove();
    ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
    document.body.appendChild(ov);
    
    fetch("/api/version/check")
        .then(r => r.json())
        .then(data => {
            const content = ov.querySelector(".updates-content");
            if (data.has_update) {
                content.innerHTML = `
                    <p class="update-available">✅ Доступна новая версия: <strong>${data.latest_version}</strong></p>
                    <p>Ваша версия: ${data.current_version}</p>
                    ${data.release_notes ? `<div class="release-notes"><h4>Что нового:</h4><pre>${escapeHtml(data.release_notes)}</pre></div>` : ''}
                    <button type="button" class="primary" onclick="window.open('${data.download_url}', '_blank')">Скачать</button>
                `;
            } else {
                content.innerHTML = `<p class="up-to-date">✅ Установлена последняя версия: ${data.current_version}</p>`;
            }
        })
        .catch(err => {
            ov.querySelector(".updates-content").innerHTML = `<p class="error">Ошибка проверки: ${err.message}</p>`;
        });
}

/**
 * О программе
 */
function showAbout() {
    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay";
    ov.innerHTML = `
        <div class="tree-modal tree-about-modal">
            <h3>ℹ️ О программе</h3>
            <div class="about-content">
                <h4>Семейное древо</h4>
                <p>Веб-версия приложения для построения и редактирования семейного генеалогического дерева.</p>
                <p><strong>Версия:</strong> 1.3.0 (Web)</p>
                <p><strong>Технологии:</strong> Flask, JavaScript, CSS</p>
                <hr>
                <p>Приложение позволяет:</p>
                <ul>
                    <li>Создавать и редактировать персоны</li>
                    <li>Добавлять родственников (родители, дети, супруги)</li>
                    <li>Визуализировать дерево с линиями связей</li>
                    <li>Экспортировать данные в CSV и PDF</li>
                    <li>Создавать резервные копии</li>
                    <li>Отменять и повторять действия</li>
                    <li>Настраивать цвета интерфейса</li>
                </ul>
                <hr>
                <p>GitHub: <a href="https://github.com/Andrey1803/family-tree" target="_blank">Andrey1803/family-tree</a></p>
            </div>
            <div class="tree-modal-btns">
                <button type="button" class="cancel">Закрыть</button>
            </div>
        </div>`;
    
    ov.querySelector(".cancel").onclick = () => ov.remove();
    ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
    document.body.appendChild(ov);
}

/**
 * О разработчике
 */
function showAboutDeveloper() {
    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay";
    ov.innerHTML = `
        <div class="tree-modal tree-about-modal">
            <h3>👨‍💻 О разработчике</h3>
            <div class="about-content">
                <h4>Емельянов Андрей Николаевич</h4>
                <p><strong>Разработчик приложения «Семейное древо»</strong></p>
                <hr>
                <p><strong>📞 Телефон:</strong> <a href="tel:+375291472108">+375 29 147-21-08</a></p>
                <p><strong>📧 Email:</strong> <a href="mailto:familyroots010326@gmail.com">familyroots010326@gmail.com</a></p>
                <hr>
                <p>Приложение создано для удобного построения и визуализации семейных генеалогических деревьев с возможностью экспорта, резервного копирования и работы в веб-интерфейсе.</p>
            </div>
            <div class="tree-modal-btns">
                <button type="button" class="cancel">Закрыть</button>
            </div>
        </div>`;

    ov.querySelector(".cancel").onclick = () => ov.remove();
    ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
    document.body.appendChild(ov);
}

function setupMenubar() {
    document.querySelectorAll(".tree-menubar [data-action]").forEach(btn => {
        btn.onclick = () => {
            const act = btn.dataset.action;
            if (act === "new") {
                if (!confirm("Создать новое дерево? Текущие данные будут утрачены.")) return;
                if (window.undoManager) window.undoManager.clear();
                treeData = { persons: {}, marriages: [], current_center: null };
                centerId = null;
                saveTree();
                render();
            } else if (act === "save") {
                saveTree();
                alert("Данные сохранены.");
            } else if (act === "undo") {
                if (window.undoManager && window.undoManager.canUndo()) {
                    window.undoManager.undo(treeData);
                    render();
                    saveTree();
                    updateUndoRedoMenu();
                }
            } else if (act === "redo") {
                if (window.undoManager && window.undoManager.canRedo()) {
                    window.undoManager.redo(treeData);
                    render();
                    saveTree();
                    updateUndoRedoMenu();
                }
            } else if (act === "export-csv") {
                exportToCsv();
            } else if (act === "export-pdf") {
                window.open("/api/export/pdf", "_blank");
            } else if (act === "import-csv") {
                document.getElementById("import-csv-input")?.click();
            } else if (act === "backup-create") {
                fetch("/api/backup/create", { method: "POST" })
                    .then(r => {
                        if (!r.ok) throw new Error("Ошибка создания копии");
                        return r.blob();
                    })
                    .then(blob => {
                        const a = document.createElement("a");
                        a.href = URL.createObjectURL(blob);
                        a.download = `backup_${new Date().toISOString().slice(0,10)}.zip`;
                        a.click();
                        URL.revokeObjectURL(a.href);
                        alert("Резервная копия создана и загружена.");
                    })
                    .catch(err => alert("Ошибка: " + err.message));
            } else if (act === "backup-list") {
                showBackupManager();
            } else if (act === "refresh") {
loadTree();
            } else if (act === "zoom-reset") {
                treeZoom = 1;
                treePanX = 0;
                treePanY = 0;
                render();
            } else if (act === "collapse-all") {
                if (window.undoManager) window.undoManager.saveState(treeData);
                Object.values(treeData.persons || {}).forEach(p => { p.collapsed_branches = true; });
                saveTree();
                render();
            } else if (act === "expand-all") {
                if (window.undoManager) window.undoManager.saveState(treeData);
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
            } else if (act === "timeline") {
                openTimeline();
            } else if (act === "search") {
                openSearchDialog();
            } else if (act === "stats") {
                showStats();
            } else if (act === "check-updates") {
                checkUpdates();
            } else if (act === "about-dev") {
                showAboutDeveloper();
            } else if (act === "about") {
                showAbout();
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
    console.log('[FILTERS] Opening filters dialog, treeData:', treeData);
    console.log('[FILTERS] Persons count:', Object.keys(treeData.persons || {}).length);
    
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
        console.log('[FILTERS] Applied filters:', activeFilters);
        ov.remove();
        render();
    };
    ov.querySelector(".tree-modal").onclick = (e) => e.stopPropagation();
    document.body.appendChild(ov);
}

function openSearchDialog() {
    console.log('[SEARCH] Opening search dialog, treeData:', treeData);
    console.log('[SEARCH] Persons count:', Object.keys(treeData.persons || {}).length);
    
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
        console.log('[SEARCH] Query:', q, 'Persons:', Object.keys(persons).length);
        const found = [];
        for (const [pid, p] of Object.entries(persons)) {
            const text = [p.name, p.patronymic, p.surname, p.birth_date, p.death_date].filter(Boolean).join(" ").toLowerCase();
            if (text.includes(q)) found.push({ pid, p });
        }
        console.log('[SEARCH] Found:', found.length);
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
    const btnOpen = document.getElementById("btn-pwa-open");
    const hint = document.getElementById("desktop-app-hint");
    if (!btnExe || !btnOpen) return;

    const isWindows = /Win|Windows/i.test(navigator.userAgent) || /Windows/i.test(navigator.platform);
    const isStandalone = () =>
        window.matchMedia("(display-mode: standalone)").matches ||
        window.navigator.standalone === true;
    const isDesktopAppInstalled = () => localStorage.getItem("desktop-app-installed") === "1";

    function updateButtons() {
        const hide = (el) => { if (el) el.style.display = "none"; };
        const show = (el, d) => { if (el) el.style.display = d || "inline-block"; };
        if (isStandalone()) {
            hide(btnExe); hide(btnOpen); hide(hint);
            return;
        }
        if (!isWindows) {
            hide(btnExe); hide(btnOpen); hide(hint);
            return;
        }
        if (isDesktopAppInstalled()) {
            hide(btnExe);
            show(btnOpen);
            hide(hint);
        } else {
            show(btnExe);
            hide(btnOpen);
            if (hint) {
                hint.style.display = "inline";
                hint.textContent = "Уже установлено?";
            }
        }
    }

    updateButtons();

    btnOpen.onclick = () => {
        const url = window.location.origin + "/";
        const protocolUrl = "derevo://open?url=" + encodeURIComponent(url);
        // Создаём ссылку и кликаем — так браузеры надёжнее обрабатывают кастомные проток��лы
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

function setupAdminButton() {
    const btnAdmin = document.getElementById("btn-admin");
    if (!btnAdmin) return;

    // Показываем кнопку для администраторов
    // Супер-админ "admin" перенаправляется на /admin сразу, поэтому кнопка ему не нужна
    // Другие админы (например, "Андрей Емельянов") видят кнопку
    const username = "{{ username }}";
    if (username === "admin") {
        // Админу кнопка не нужна - он уже в админ-панели
        btnAdmin.style.display = "none";
    } else {
        // Для других пользователей с is_admin показываем кнопку
        const isAdmin = document.body.dataset.isAdmin === "true";
        if (isAdmin) {
            btnAdmin.style.display = "inline-block";
        }
    }
}

if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {});
}

// Инициализация менеджера отмены/повтора
window.undoManager = new UndoManager(50);

// Палитра применяется в loadTree()

// ПРОВЕРЯЕМ admin_view ПЕРЕД загрузкой дерева!
const urlParamsCheck = new URLSearchParams(window.location.search);
const isAdminViewCheck = urlParamsCheck.get('admin_view') === '1';

if (isAdminViewCheck) {
    // Для админ-просмотра НЕ загружаем дерево сразу - загрузим через checkAdminView
    console.log('[INIT] Admin view detected, skipping initial loadTree()');
    // Инициализируем пустое дерево
    treeData = { persons: {}, marriages: [], current_center: null };
    centerId = null;
} else {
    // Обычный режим - загружаем дерево пользователя
    console.log('[INIT] Normal view, loading tree');
    loadTree();
}

setupMenubar();
setupDesktopAppButtons();
setupUndoRedo();
setupAdminButton();

// Проверка режима просмотра из админ-панели (после инициализации)
if (isAdminViewCheck) {
    checkAdminView();
}

// Проверка первого запуска
checkFirstRun();

async function checkAdminView() {
    // Проверяем, открыли ли дерево из адм��н-панели
    const urlParams = new URLSearchParams(window.location.search);
    console.log('[ADMIN_VIEW] URL params:', Object.fromEntries(urlParams));
    console.log('[ADMIN_VIEW] Tree owner:', urlParams.get('tree_owner'));
    
    // Пробуем получить данные из localStorage (быстрый путь)
    const adminTreeData = localStorage.getItem('adminTreeData');
    console.log('[ADMIN_VIEW] adminTreeData from localStorage:', adminTreeData ? 'found' : 'not found');
    
    if (adminTreeData) {
        try {
            const treeDataFromStorage = JSON.parse(adminTreeData);
            console.log('[ADMIN_VIEW] Parsed treeData from localStorage:', treeDataFromStorage);
            console.log('[ADMIN_VIEW] Persons count:', Object.keys(treeDataFromStorage.persons || {}).length);
            
            // Загружаем данные из localStorage
            treeData = treeDataFromStorage;
            centerId = treeData.current_center;
            
            finalizeAdminView(treeDataFromStorage);
            return;
        } catch (e) {
            console.error('[ADMIN_VIEW] Error parsing localStorage:', e);
        }
    }
    
    // Если localStorage пуст, пробуем загрузить с сервера
    console.log('[ADMIN_VIEW] Trying to load from sync server...');
    try {
        // Передаём tree_owner в запросе!
        const treeOwner = urlParams.get('tree_owner');
        const response = await fetch('/api/tree?tree_owner=' + encodeURIComponent(treeOwner));
        if (response.ok) {
            const serverData = await response.json();
            console.log('[ADMIN_VIEW] Loaded from /api/tree:', serverData);
            console.log('[ADMIN_VIEW] Persons count from server:', Object.keys(serverData.persons || {}).length);
            
            treeData = {
                persons: serverData.persons || {},
                marriages: serverData.marriages || [],
                current_center: serverData.current_center
            };
            centerId = treeData.current_center || Object.keys(treeData.persons)[0];
            
            finalizeAdminView(treeData);
        } else {
            console.error('[ADMIN_VIEW] Failed to load from /api/tree:', response.status);
            alert('Не удалось загрузить данные дерева. Вернитесь в админ-панель и попробуйте снова.');
        }
    } catch (e) {
        console.error('[ADMIN_VIEW] Error loading from server:', e);
        alert('Ошибка загрузки дерева: ' + e.message);
    }
}

function finalizeAdminView(treeDataFromStorage) {
    // Показываем информацию о владельце
    const header = document.querySelector('.tree-header h1');
    if (header && treeDataFromStorage.treeOwner) {
        header.textContent = `🌳 ${treeDataFromStorage.treeName} (владелец: ${treeDataFromStorage.treeOwner})`;
    }
    
    // Нормализуем браки (п��еобразуем из {persons: [a,b]} в [a,b])
    if (treeData.marriages && treeData.marriages.length) {
        treeData.marriages = treeData.marriages.map(m => {
            if (Array.isArray(m)) return m;
            if (m.persons && Array.isArray(m.persons)) return m.persons;
            return [];
        }).filter(m => m.length === 2);
    }
    
    // Перерисовываем дерево
    console.log('[ADMIN_VIEW] Calling render()...');
    render();
    
    // Показываем кнопку "Назад в админ-панель"
    showBackToAdminButton();
    
    // Очищаем localStorage
    localStorage.removeItem('adminTreeData');
    localStorage.removeItem('adminTreeRef');
}

function showBackToAdminButton() {
    // Добавляем кнопку "Назад в админ-панель"
    const headerRight = document.querySelector('.tree-header-right');
    if (headerRight) {
        const backBtn = document.createElement('a');
        backBtn.href = '/admin';
        backBtn.textContent = '← Назад в админ-панель';
        backBtn.className = 'btn-back-admin';
        backBtn.style.cssText = 'background: #64748b; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; margin-right: 10px;';
        headerRight.insertBefore(backBtn, headerRight.firstChild);
    }
}

function checkFirstRun() {
    // Показываем приветственный диалог, если дерево пусто
    setTimeout(() => {
        const persons = treeData.persons || {};
        if (Object.keys(persons).length === 0) {
            showWelcomeDialog();
        }
    }, 500);
}

function showWelcomeDialog() {
    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay";
    ov.innerHTML = `
        <div class="tree-modal tree-welcome-modal">
            <h3>�� Добро пожаловать!</h3>
            <p>Ваше дерево пусто. Давайте создадим первую запись!</p>
            <p>Заполните свои данные — это будет ваша карточка в дереве.</p>
            <hr>
            <label>Имя *</label>
            <input type="text" id="welcome-name" placeholder="Имя">
            <label>Фамилия *</label>
            <input type="text" id="welcome-surname" placeholder="Фамилия">
            <label>Отчество</label>
            <input type="text" id="welcome-patronymic" placeholder="Отчество">
            <label>Дата рождения (ДД.ММ.ГГГГ)</label>
            <input type="text" id="welcome-birth" placeholder="ДД.ММ.ГГГГ">
            <label>Место рождения</label>
            <input type="text" id="welcome-birth-place" value="Минск, Б���ларусь">
            <label>Пол</label>
            <select id="welcome-gender">
                <option value="Мужской">Мужской</option>
                <option value="Женский">Женский</option>
            </select>
            <hr>
            <p class="small">* — обязательные поля</p>
            <div class="tree-modal-btns">
                <button type="button" class="cancel" id="welcome-skip">Пропустить</button>
                <button type="button" class="primary" id="welcome-create">Создать</button>
            </div>
        </div>`;
    
    ov.querySelector("#welcome-skip").onclick = () => ov.remove();
    ov.querySelector("#welcome-create").onclick = () => {
        const name = ov.querySelector("#welcome-name").value.trim();
        const surname = ov.querySelector("#welcome-surname").value.trim();
        if (!name) { alert("Введите имя."); return; }
        if (!surname) { alert("Введите фамилию."); return; }
        
        fetch("/welcome/complete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: name,
                surname: surname,
                patronymic: ov.querySelector("#welcome-patronymic").value.trim(),
                birth_date: ov.querySelector("#welcome-birth").value.trim(),
                birth_place: ov.querySelector("#welcome-birth-place").value.trim(),
                gender: ov.querySelector("#welcome-gender").value,
            }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                ov.remove();
                loadTree();
                alert(`Добро пожаловать, ${name}! Ваша персона создана.`);
            } else {
                alert("Ошибка: " + (data.error || "Неизвестная"));
            }
        });
    };
    
    ov.onclick = (e) => { if (e.target === ov) ov.remove(); };
    document.body.appendChild(ov);
    ov.querySelector("#welcome-name").focus();
}

// === АВТОСОХРАНЕНИЕ ПРИ ЗАКРЫТИИ СТРАНИЦЫ (важно для мобильных) ===
let saveTimeout = null;

// Сохраняем дерево при закрытии/обновлении страницы
window.addEventListener('beforeunload', (e) => {
    // Сохраняем в localStorage для быстрого восстановления
    if (treeData && treeData.persons) {
        localStorage.setItem('family_tree_backup', JSON.stringify(treeData));
        console.log('[AUTO-SAVE] Saved to localStorage at', new Date().toLocaleTimeString());
    }
});

// Сохранение при уходе в фон (mobile)
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
        // Пользователь свернул браузер или перешёл на другую вкладку
        if (treeData && treeData.persons) {
            localStorage.setItem('family_tree_backup', JSON.stringify(treeData));
            console.log('[AUTO-SAVE] Saved on visibilitychange at', new Date().toLocaleTimeString());
        }
    }
});

// Периодическое автосохранение каждые 30 секунд
setInterval(() => {
    if (treeData && treeData.persons && Object.keys(treeData.persons).length > 0) {
        localStorage.setItem('family_tree_backup', JSON.stringify(treeData));
        console.log('[AUTO-SAVE] Periodic save at', new Date().toLocaleTimeString());
    }
}, 30000);