/**
 * ФИНАЛЬНАЯ ВЕРСИЯ ОТРИСОВКИ v3
 * Размещение по уровням с учётом семейных групп
 * 
 * ПРАВИЛА СКРЫТИЯ ПРЕДКОВ:
 * 1. Скрываем предков по женской линии (если персона женская - её предков не показываем)
 * 2. ИСКЛЮЧЕНИЕ: если выбрана персона женского пола - показываем ЕЁ предков
 * 3. Если у выбранной персоны (женской) есть супруг - скрываем предков супруга
 */

function renderFinalLayout(centerId, persons, marriages, related) {
    const coords = {};
    const CARD_W = 120;
    const CARD_H = 90;
    const SPOUSE_GAP = 36;
    const SIBLING_GAP = 120;
    const FAMILY_GROUP_GAP = 56;  // зазор между семьями на одном уровне (пара шире одной карточки)
    const LEVEL_HEIGHT = 252;
    const PAD = 60;

    function rangesOverlap(l1, r1, l2, r2) {
        return l1 < r2 && l2 < r1;
    }

    /** Центры карточек детей (без супругов) — равномерно под серединой брака родителей */
    function bloodChildCenterXs(midX, childIds) {
        const n = childIds.length;
        if (n === 0) return [];
        if (n === 1) return [midX];
        const step = CARD_W + SIBLING_GAP;
        const span = (n - 1) * step;
        const start = midX - span / 2;
        return childIds.map((_, i) => start + i * step);
    }

    function marriageMidFromKey(parentKey, rowY) {
        const ids = parentKey.split('|').filter(id => {
            const c = coords[id];
            if (!c) return false;
            if (rowY == null) return true;
            return snapLayoutRowY(c.y) === rowY;
        });
        if (!ids.length) return 0;
        return ids.reduce((s, id) => s + coords[id].x, 0) / ids.length;
    }

    function snapLayoutRowY(y) {
        return Math.round(y / LEVEL_HEIGHT) * LEVEL_HEIGHT;
    }

    function normalizeMarriedCoupleSpacingOnRow(py) {
        const CENTER_DIST = CARD_W + SPOUSE_GAP;
        const onRow = Object.keys(coords).filter(id => snapLayoutRowY(coords[id].y) === py);
        const assigned = new Set();
        for (const pid of onRow) {
            if (assigned.has(pid)) continue;
            const cset = new Set([pid]);
            let grow = true;
            while (grow) {
                grow = false;
                for (const q of [...cset]) {
                    for (const sidRaw of marriageMap.get(q) || []) {
                        const sid = String(sidRaw);
                        if (!onRow.includes(sid) || cset.has(sid)) continue;
                        if (snapLayoutRowY(coords[sid].y) === py) {
                            cset.add(sid);
                            grow = true;
                        }
                    }
                }
            }
            cset.forEach(id => assigned.add(id));
            if (cset.size !== 2) continue;
            const [pLeft, pRight] = [...cset].sort((a, b) => coords[a].x - coords[b].x);
            const mid = (coords[pLeft].x + coords[pRight].x) / 2;
            coords[pLeft].x = mid - CENTER_DIST / 2;
            coords[pRight].x = mid + CENTER_DIST / 2;
        }
    }

    function shiftParentMarriageUnitOnKey(parentKey, rowY, dx) {
        if (Math.abs(dx) < 0.25) return;
        const seeds = parentKey.split('|').filter(
            id => coords[id] && snapLayoutRowY(coords[id].y) === rowY
        );
        const unit = new Set(seeds);
        let grow = true;
        while (grow) {
            grow = false;
            for (const q of [...unit]) {
                for (const sidRaw of marriageMap.get(q) || []) {
                    const sid = String(sidRaw);
                    if (!coords[sid] || unit.has(sid)) continue;
                    if (snapLayoutRowY(coords[sid].y) !== rowY) continue;
                    unit.add(sid);
                    grow = true;
                }
            }
        }
        unit.forEach(id => {
            coords[id].x += dx;
        });
    }

    /** Старт группы: по центру родителей, при пересечении — минимальный сдвиг вправо */
    function resolveGroupStartX(idealLeft, groupWidth, occupied) {
        let start = idealLeft;
        let guard = 0;
        while (guard++ < 200) {
            let hit = false;
            for (const r of occupied) {
                if (rangesOverlap(start, start + groupWidth, r.left, r.right)) {
                    start = r.right + FAMILY_GROUP_GAP;
                    hit = true;
                    break;
                }
            }
            if (!hit) break;
        }
        return start;
    }

    function registerOccupied(left, width, occupied) {
        if (width <= 0) return;
        occupied.push({ left, right: left + width });
        occupied.sort((a, b) => a.left - b.left);
    }

    // === ПРОВЕРКА: centerId и related валидны ===
    if (!centerId || !persons[centerId]) {
        console.log('[FINAL] Invalid centerId or person not found:', centerId);
        return { coords: {}, bounds: {left:0,right:400,top:0,bottom:300}, totalW:400, totalH:300, offsetX:60, offsetY:60 };
    }

    // === ПРОВЕРКА: related - это Set ===
    if (!(related instanceof Set)) {
        console.warn('[FINAL] related is not a Set! Creating empty Set.');
        related = new Set();
    }

    console.log('[FINAL] Starting layout for center:', centerId, 'related:', related.size);

    // === ПОСТРОЕНИЕ MARRIAGE MAP (как в visible_persons.js) ===
    const marriageMap = new Map();  // pid -> [spouse_ids]
    if (Array.isArray(marriages)) {
        marriages.forEach(marriage => {
            let p1, p2;
            if (Array.isArray(marriage) && marriage.length >= 2) {
                p1 = String(marriage[0]);
                p2 = String(marriage[1]);
            } else if (marriage && marriage.persons && marriage.persons.length >= 2) {
                p1 = String(marriage.persons[0]);
                p2 = String(marriage.persons[1]);
            } else {
                return;
            }
            if (!marriageMap.has(p1)) marriageMap.set(p1, []);
            if (!marriageMap.has(p2)) marriageMap.set(p2, []);
            marriageMap.get(p1).push(p2);
            marriageMap.get(p2).push(p1);
        });
    }
    console.log('[FINAL] Marriage map built:', marriageMap.size, 'persons with spouses');

    // === ОПРЕДЕЛЯЕМ ЦЕНТРАЛЬНУЮ ПЕРСОНУ И ЕЁ СУПРУГА ===
    const centerPerson = persons[centerId];
    const isCenterFemale = centerPerson && centerPerson.gender === 'Женский';

    // Находим супруга центральной персоны через marriageMap
    let centerSpouseId = null;
    if (centerPerson) {
        const centerSpouses = marriageMap.get(centerId) || [];
        if (centerSpouses.length > 0) {
            centerSpouseId = centerSpouses[0];
        }
    }

    console.log('[FINAL] Center:', centerId, 'isFemale:', isCenterFemale, 'spouseId:', centerSpouseId);

    // === 1. РАЗМЕЩЕНИЕ ПО УРОВНЯМ ===
    const levels = new Map();
    const visited = new Set();

    // Начинаем с центра
    const queue = [[centerId, 0]];

    while (queue.length > 0) {
        const [pid, level] = queue.shift();
        const pidStr = String(pid);

        if (visited.has(pidStr)) continue;
        visited.add(pidStr);

        if (!levels.has(level)) levels.set(level, []);
        // === ПРОВЕРКА: не добавлен ли уже на этот уровень ===
        if (!levels.get(level).includes(pidStr)) {
            levels.get(level).push(pidStr);
        }

        const person = persons[pidStr];
        if (!person) continue;

        // === ПРОВЕРКА: СКРЫВАТЬ ЛИ ПРЕДКОВ ЭТОЙ ПЕРСОНЫ? ===
        const isFemale = person.gender === 'Женский';
        const isCenter = pidStr === String(centerId);
        const isCenterSpouse = pidStr === String(centerSpouseId);

        // По умолчанию показываем предков
        let shouldHideParents = false;

        // Правило 1: Скрываем предков по женской линии (если персона женская - её предков не показываем)
        if (isFemale && !isCenter) {
            shouldHideParents = true;
            console.log('[FINAL] Hiding parents of female:', pidStr, person.name);
        }

        // Правило 2: ИСКЛЮЧЕНИЕ - если центр женский, показываем ЕЁ предков
        // (уже учтено выше через !isCenter)

        // Правило 3: Если персона - супруг центральной женской персоны, скрываем ЕГО предков
        if (isCenterSpouse && isCenterFemale) {
            shouldHideParents = true;
            console.log('[FINAL] Hiding parents of center spouse:', pidStr, person.name);
        }

        // Родители - уровень -1
        if (!shouldHideParents && person.parents) {
            person.parents.forEach(prId => {
                if (related.has(String(prId)) && !visited.has(String(prId))) {
                    queue.push([prId, level - 1]);
                }
            });
        }

        // Дети - уровень +1 (всегда показываем)
        if (person.children) {
            person.children.forEach(chId => {
                if (related.has(String(chId)) && !visited.has(String(chId))) {
                    queue.push([chId, level + 1]);
                }
            });
        }

        // Супруги - тот же уровень (всегда показываем)
        // ИСПОЛЬЗУЕМ marriageMap вместо spouse_ids
        const spouses = marriageMap.get(pidStr) || [];
        spouses.forEach(spId => {
            if (related.has(String(spId)) && !visited.has(String(spId))) {
                queue.push([spId, level]);
            }
        });
    }
    
    // === 1.5. ДОБАВЛЯЕМ ОСТАЛЬНЫХ (не попали в BFS, но есть в related) ===
    // Не добавляем предков по женской линии — иначе ломается компактность дерева.
    const remaining = Array.from(related).filter(pid => {
        if (visited.has(pid) || !persons[pid]) return false;
        const person = persons[pid];
        if (person.children) {
            for (const childId of person.children) {
                const child = persons[childId];
                if (child && child.gender === 'Женский' && String(childId) !== String(centerId)) {
                    return false;
                }
            }
        }
        if (isCenterFemale && centerSpouseId && person.children) {
            for (const childId of person.children) {
                if (String(childId) === String(centerSpouseId)) return false;
            }
        }
        return true;
    });
    console.log('[FINAL] Remaining persons:', remaining.length);

    if (remaining.length > 0) {
        if (!levels.has(0)) levels.set(0, []);
        remaining.forEach(pid => {
            const key = String(pid);
            if (!levels.get(0).includes(key)) levels.get(0).push(key);
        });
    }
    
    console.log('[FINAL] Levels before sorting:', Object.fromEntries([...levels].map(([k,v]) => [k, v])));
    console.log('[FINAL] Levels:', Object.fromEntries([...levels].map(([k,v]) => [k, v.length])));

    // === 2. РАЗМЕЩЕНИЕ ВНУТРИ КАЖДОГО УРОВНЯ ===
    // Стратегия: размещаем группы детей под их родителями
    // ВАЖНО: Обрабатываем уровни ПО ПОРЯДКУ (сначала родители, потом дети)
    const sortedLevels = Array.from(levels.entries()).sort((a, b) => a[0] - b[0]);
    
    console.log('[FINAL] Sorted levels order:', sortedLevels.map(([l, p]) => `L${l}:${p.length}`));
    
    // === ПРОВЕРКА ПЕРЕД РАЗМЕЩЕНИЕМ: какие персоны на каких уровнях ===
    sortedLevels.forEach(([level, pids]) => {
        pids.forEach(pid => {
            const person = persons[pid];
            if (person && person.parents) {
                const parentNames = person.parents.map(prId => persons[prId]?.name || prId).join(', ');
                console.log(`[FINAL] PRE-CHECK: Level ${level}: ${pid}(${person.name}) has parents: [${parentNames}]`);
            }
        });
    });

    // === ШАГ 0: Сначала размещаем всех "сирот" и тех, у кого нет видимых родителей ===
    // Это освободит место для детей с видимыми родителями
    const orphansByLevel = new Map();
    
    for (const [level, pids] of sortedLevels) {
        const yPos = level * LEVEL_HEIGHT;
        const levelOrphans = [];
        
        for (const pid of pids) {
            const person = persons[pid];
            if (!person) continue;
            
            // Проверяем, есть ли видимые родители
            const hasVisibleParents = person.parents && person.parents.some(prId => {
                const pr = persons[prId];
                return pr && related.has(String(prId));
            });
            
            if (!hasVisibleParents) {
                levelOrphans.push(pid);
            }
        }
        
        orphansByLevel.set(level, levelOrphans);
    }
    
    console.log('[FINAL] Orphans by level (preliminary):', Object.fromEntries([...orphansByLevel].map(([k,v]) => [k, v.length])));

    // === РАЗМЕЩЕНИЕ: Сначала семьи с родителями, потом сироты ===
    for (const [level, pids] of sortedLevels) {
        const yPos = level * LEVEL_HEIGHT;
        const placed = new Set();

        function multiCardBlockWidth(nCards) {
            if (nCards <= 0) return 0;
            return nCards * CARD_W + (nCards - 1) * SPOUSE_GAP;
        }

        function widthForChildBlock(childId, spousesArr) {
            const sp = spousesArr || [];
            return multiCardBlockWidth(1 + sp.length);
        }

        /** Порядок карточек в блоке ребёнок+супруги (совпадает с бывшей логикой в placeChildWithSpousesAt). */
        function spouseRowOrder(childId, spousesArr) {
            const sp = spousesArr || [];
            if (sp.length === 1) {
                const ch = persons[childId];
                const s0 = persons[sp[0]];
                const cM = ch?.gender === 'Мужской';
                const sM = s0?.gender === 'Мужской';
                if (cM && !sM) return [childId, sp[0]];
                if (!cM && sM) return [sp[0], childId];
                return [childId, sp[0]];
            }
            if (sp.length > 1) return [childId, ...sp];
            return [childId];
        }

        /** Середина брака: центр между карточками двух родителей (линия супругов). */
        function centersOneChildPackAtMid(midMarriageX, childId, spousesArr) {
            const order = spouseRowOrder(childId, spousesArr);
            const k = order.indexOf(childId);
            if (k < 0) {
                return {
                    order: [childId],
                    centers: [midMarriageX],
                };
            }
            const centers = new Array(order.length);
            centers[k] = midMarriageX;
            for (let j = k - 1; j >= 0; j--) {
                centers[j] = centers[j + 1] - CARD_W - SPOUSE_GAP;
            }
            for (let j = k + 1; j < order.length; j++) {
                centers[j] = centers[j - 1] + CARD_W + SPOUSE_GAP;
            }
            return { order, centers };
        }

        function boundsFromFamilyCenters(order, centers) {
            const half = CARD_W / 2;
            const left = Math.min(...centers) - half;
            const right = Math.max(...centers) + half;
            return { left, right, width: right - left };
        }

        function oneChildPackBoundsAtMid(midMarriageX, childId, spousesArr) {
            const { order, centers } = centersOneChildPackAtMid(midMarriageX, childId, spousesArr);
            return { order, centers, ...boundsFromFamilyCenters(order, centers) };
        }

        /** Разместить блок: центр карточки ребёнка = midMarriageX. */
        function placeOneChildAnchoredMidMarriage(midMarriageX, childId, spousesArr) {
            const { order, centers } = centersOneChildPackAtMid(midMarriageX, childId, spousesArr);
            const geom = boundsFromFamilyCenters(order, centers);
            order.forEach((pid, i) => {
                coords[pid] = { x: centers[i], y: yPos };
                placed.add(pid);
            });
            return { width: geom.width, geom };
        }

        /** Центр bbox всего ряда детей+супругов при старте слева от 0 (согласовано с reAnchor). */
        function childrenRowBBoxMidFromLeft(children, childSpouses) {
            let leftEdge = 0;
            let minL = Infinity;
            let maxR = -Infinity;
            children.forEach((cid, idx) => {
                const sp = childSpouses.get(cid) || [];
                const order = spouseRowOrder(cid, sp);
                order.forEach((pid, i) => {
                    const cleft = leftEdge + i * (CARD_W + SPOUSE_GAP);
                    minL = Math.min(minL, cleft);
                    maxR = Math.max(maxR, cleft + CARD_W);
                });
                leftEdge += widthForChildBlock(cid, sp);
                if (idx < children.length - 1) leftEdge += SIBLING_GAP;
            });
            return {
                bboxMidFromRowLeft: Number.isFinite(minL) ? (minL + maxR) / 2 : 0,
                totalRowWidth: leftEdge,
            };
        }

        /** Карточки подряд от левого края блока.rebёнок центрируют под браком только через placeOneChildAnchoredMidMarriage. */
        function placeChildWithSpousesAt(xLeft, childId, spousesArr) {
            const order = spouseRowOrder(childId, spousesArr);
            let px = xLeft;
            for (let i = 0; i < order.length; i++) {
                const pid = order[i];
                coords[pid] = { x: px + CARD_W / 2, y: yPos };
                placed.add(pid);
                px += CARD_W + (i < order.length - 1 ? SPOUSE_GAP : 0);
            }
            return multiCardBlockWidth(order.length);
        }

        console.log(`[FINAL] === Placing level ${level} (yPos=${yPos}) with ${pids.length} persons ===`);
        console.log('[FINAL] Persons on this level:', pids.map(pid => `${pid}(${persons[pid]?.name || '?'})`).join(', '));

        // === ШАГ 0: Находим ВСЕ супружеские пары на этом уровне ===
        const spouseMap = new Map(); // pid -> spouseId
        pids.forEach(pid => {
            const person = persons[pid];
            if (!person) return;

            // ИСПОЛЬЗУЕМ marriageMap вместо spouse_ids
            const spouses = marriageMap.get(pid) || [];
            spouses.forEach(spId => {
                const spouse = persons[spId];
                if (spouse && pids.includes(spId)) {
                    spouseMap.set(pid, spId);
                    spouseMap.set(spId, pid);
                }
            });
        });

        const spousePairsCount = new Set([...spouseMap.keys()].map(k => Math.min(k, spouseMap.get(k)))).size;
        console.log(`[FINAL] Found ${spousePairsCount} spouse pairs on level ${level}`);

        // === ШАГ 1: Находим ВСЕ группы (и с родителями, и сироты) ===
        const familyGroups = new Map();
        const orphanSet = new Set(); // Будет заполнена динамически

        console.log(`[FINAL] Level ${level}: ${pids.length} persons to place`);

        // Сначала группируем детей с родителями
        pids.forEach(pid => {
            if (placed.has(pid)) return;

            const person = persons[pid];
            if (!person) return;

            // Ищем видимых родителей с координатами
            let parentKey = null;
            let parentIds = [];

            if (person.parents) {
                parentIds = person.parents.filter(prId => {
                    const pr = persons[prId];
                    const isVisible = related.has(String(prId));
                    const hasCoords = coords[prId] !== undefined;
                    const onCorrectLevel = hasCoords && coords[prId].y === (level - 1) * LEVEL_HEIGHT;
                    
                    // Родитель должен быть видим И размещён на уровне выше
                    return isVisible && onCorrectLevel;
                }).map(String);

                // === ВАЖНО: Если хотя бы ОДИН родитель размещён — добавляем в группу ===
                if (parentIds.length > 0) {
                    parentKey = parentIds.sort().join('|');
                }
            }

            // Если НЕТ ни одного размещённого родителя — это сирота
            if (!parentKey) {
                orphanSet.add(pid);
                return;
            }

            if (!familyGroups.has(parentKey)) {
                familyGroups.set(parentKey, {
                    parentIds,
                    children: [],
                    childSpouses: new Map()
                });
            }

            familyGroups.get(parentKey).children.push(pid);
        });

        console.log(`[FINAL] Grouped: ${familyGroups.size} family groups, ${orphanSet.size} orphans`);
        
        // Лог для отладки: кто в какой группе
        familyGroups.forEach((group, key) => {
            console.log(`[FINAL] Group [${key}]: ${group.children.length} children: ${group.children.map(c => `${c}(${persons[c]?.name})`).join(', ')}`);
        });
        console.log(`[FINAL] Orphans: ${[...orphanSet].map(id => `${id}(${persons[id]?.name})`).join(', ')}`);
        
        // === ШАГ 2: Находим супругов для детей ===
        familyGroups.forEach((group) => {
            group.children.forEach(childId => {
                const person = persons[childId];
                if (!person) return;

                // ИСПОЛЬЗУЕМ marriageMap вместо spouse_ids
                const allSpouses = marriageMap.get(childId) || [];
                const spousesOnThisLevel = allSpouses.filter(spId => {
                    const sp = persons[spId];
                    return sp && pids.includes(spId) && !group.children.includes(spId);
                });

                if (spousesOnThisLevel.length > 0) {
                    group.childSpouses.set(childId, spousesOnThisLevel);
                    // Помечаем супругов как размещённых ВМЕСТЕ с ребёнком
                    spousesOnThisLevel.forEach(spId => {
                        placed.add(spId);
                        // Если супруг был в сиротах — убираем его оттуда
                        if (orphanSet.has(spId)) {
                            console.log(`[FINAL] Removing spouse ${spId} from orphans`);
                            orphanSet.delete(spId);
                        }
                    });
                }
            });
        });
        
        console.log(`[FINAL] After spouse check: ${orphanSet.size} orphans: ${[...orphanSet].map(id => `${id}(${persons[id]?.name})`).join(', ')}`);

        // === ШАГ 3: Сортируем группы ===
        const sortedGroups = Array.from(familyGroups.entries()).sort(([keyA, grpA], [keyB, grpB]) => {
            const parentsA = grpA.parentIds.map(id => coords[id]?.x || 0);
            const parentsB = grpB.parentIds.map(id => coords[id]?.x || 0);
            const centerA = parentsA.length ? parentsA.reduce((s, v) => s + v, 0) / parentsA.length : 0;
            const centerB = parentsB.length ? parentsB.reduce((s, v) => s + v, 0) / parentsB.length : 0;
            return centerA - centerB;
        });

        console.log(`[FINAL] sortedGroups: ${sortedGroups.length} groups: ${sortedGroups.map(([k, g]) => `[${k}]:${g.children.length}`).join(', ')}`);

        // === ШАГ 4: Размещаем группы (без наложения на одном уровне) ===
        const levelOccupied = [];
        let currentX = 0;

        sortedGroups.forEach(([parentKey, group]) => {
            const { children, childSpouses } = group;
            const allParentIds = parentKey.split('|').filter(id => coords[id]);
            const hasPlacedParents = allParentIds.length > 0;

            children.sort((a, b) => {
                const da = persons[a]?.birth_date || '9999.99.99';
                const db = persons[b]?.birth_date || '9999.99.99';
                return da.localeCompare(db);
            });

            if (!hasPlacedParents) {
                console.log(`[FINAL] Group [${parentKey}]: parents not placed, adding ${children.length} children to orphans`);
                children.forEach(childId => {
                    orphanSet.add(childId);
                    const allSpouses = marriageMap.get(childId) || [];
                    allSpouses.forEach(spId => {
                        if (pids.includes(spId)) orphanSet.add(spId);
                    });
                });
                return;
            }

            const parentCenterX = marriageMidFromKey(parentKey, yPos - LEVEL_HEIGHT);

            if (children.length === 1) {
                const childId = children[0];
                const spouses = childSpouses.get(childId) || [];
                const preview = oneChildPackBoundsAtMid(parentCenterX, childId, spouses);
                const resolvedLeft = resolveGroupStartX(preview.left, preview.width, levelOccupied);
                const shiftedMid = parentCenterX + (resolvedLeft - preview.left);
                if (Math.abs(resolvedLeft - preview.left) > 1) {
                    console.log(`[FINAL] Group [${parentKey}] single-child anchor shifted by ${(resolvedLeft - preview.left).toFixed(0)}px (overlap)`);
                }
                const placedPack = placeOneChildAnchoredMidMarriage(shiftedMid, childId, spouses);
                registerOccupied(placedPack.geom.left, placedPack.width, levelOccupied);
                currentX = Math.max(currentX, placedPack.geom.right + SIBLING_GAP);
                console.log(`[FINAL] Group under parents [${parentKey}]: 1 child anchored mid-marriage center=${parentCenterX.toFixed(1)}`);
                return;
            }

            const centerXs = bloodChildCenterXs(parentCenterX, children);
            let minL = Infinity;
            let maxR = -Infinity;
            children.forEach((childId, i) => {
                const preview = oneChildPackBoundsAtMid(centerXs[i], childId, childSpouses.get(childId) || []);
                minL = Math.min(minL, preview.left);
                maxR = Math.max(maxR, preview.right);
            });
            const groupWidth = maxR - minL;
            const resolvedLeft = resolveGroupStartX(minL, groupWidth, levelOccupied);
            const dx = resolvedLeft - minL;
            if (Math.abs(dx) > 1) {
                console.log(`[FINAL] Group [${parentKey}] shifted by ${dx.toFixed(0)}px (overlap)`);
            }
            console.log(
                `[FINAL] Group under parents [${parentKey}]: ${children.length} children, marriageMid=${parentCenterX.toFixed(1)}, startX=${resolvedLeft.toFixed(1)}`
            );

            children.forEach((childId, i) => {
                placeOneChildAnchoredMidMarriage(centerXs[i] + dx, childId, childSpouses.get(childId) || []);
            });

            shiftParentMarriageUnitOnKey(parentKey, yPos - LEVEL_HEIGHT, dx);
            registerOccupied(resolvedLeft, groupWidth, levelOccupied);
            currentX = Math.max(currentX, maxR + dx + SIBLING_GAP);
        });

        // === ШАГ 5: Размещаем сирот СПРАВА ===
        const remainingOrphans = pids.filter(pid => !placed.has(pid));
        
        console.log(`[FINAL] Placing ${remainingOrphans.length} orphans on level ${level}`);
        
        // Проверяем, есть ли супруги среди сирот
        const orphansWithSpouses = [];
        const singleOrphans = [];
        const processedInPair = new Set();

        remainingOrphans.forEach(pid => {
            if (processedInPair.has(pid)) return;

            const person = persons[pid];
            if (!person) return;

            // Ищем супруга среди ещё не размещённых
            // ИСПОЛЬЗУЕМ marriageMap вместо spouse_ids
            const allSpouses = marriageMap.get(pid) || [];
            const spouseInOrphans = allSpouses.find(spId =>
                remainingOrphans.includes(spId) && !processedInPair.has(spId)
            );

            if (spouseInOrphans) {
                orphansWithSpouses.push([pid, spouseInOrphans]);
                processedInPair.add(pid);
                processedInPair.add(spouseInOrphans);
            } else {
                singleOrphans.push(pid);
            }
        });
        
        // Размещаем пары сирот (без наложения на семьи)
        orphansWithSpouses.forEach(([pid1, pid2]) => {
            const p1 = persons[pid1];
            const p1IsMale = p1?.gender === 'Мужской';
            const mainId = p1IsMale ? pid1 : pid2;
            const spouseId = p1IsMale ? pid2 : pid1;
            const pairW = 2 * CARD_W + SPOUSE_GAP;
            const start = resolveGroupStartX(currentX, pairW, levelOccupied);

            coords[mainId] = { x: start + CARD_W / 2, y: yPos };
            coords[spouseId] = { x: start + CARD_W + SPOUSE_GAP + CARD_W / 2, y: yPos };
            placed.add(mainId);
            placed.add(spouseId);
            registerOccupied(start, pairW, levelOccupied);
            currentX = start + pairW + SIBLING_GAP;
            console.log(`[FINAL] Orphan spouse pair: ${mainId} + ${spouseId} at x=${start}`);
        });

        singleOrphans.forEach(pid => {
            const start = resolveGroupStartX(currentX, CARD_W, levelOccupied);
            placed.add(pid);
            coords[pid] = { x: start + CARD_W / 2, y: yPos };
            registerOccupied(start, CARD_W, levelOccupied);
            currentX = start + CARD_W + SIBLING_GAP;
            console.log(`[FINAL] Orphan ${pid}(${persons[pid]?.name}) at x=${start}`);
        });

        console.log(`[FINAL] Level ${level} placed: ${placed.size} persons`);
        normalizeMarriedCoupleSpacingOnRow(yPos);
    }

    console.log('[FINAL] Placed persons:', Object.keys(coords).length);

    /** Один логический ряд = уровень (избегаем двойной обработки при чуть разных y) */
    function layoutRowKeys() {
        return [...new Set(Object.keys(coords).map(id => snapLayoutRowY(coords[id].y)))].sort((a, b) => a - b);
    }

    // === POST: фиксируем расстояние между супругами (между центрами = CARD_W + SPOUSE_GAP, как «одна карточка + зазор») ===
    function normalizeMarriedCoupleSpacing() {
        const CENTER_DIST = CARD_W + SPOUSE_GAP; // два соседних блока парного ряда, без искусственного разъезда

        function gatherUnitsOnRow(py) {
            const onRow = Object.keys(coords).filter(
                id => snapLayoutRowY(coords[id].y) === py
            );
            const assigned = new Set();
            const units = [];
            for (const pid of onRow) {
                if (assigned.has(pid)) continue;
                const cset = new Set([pid]);
                let grow = true;
                while (grow) {
                    grow = false;
                    for (const q of [...cset]) {
                        for (const sidRaw of marriageMap.get(q) || []) {
                            const sid = String(sidRaw);
                            if (!onRow.includes(sid) || cset.has(sid)) continue;
                            if (snapLayoutRowY(coords[sid].y) === py) {
                                cset.add(sid);
                                grow = true;
                            }
                        }
                    }
                }
                cset.forEach(id => assigned.add(id));
                units.push({ ids: [...cset].sort(), y: py });
            }
            return units;
        }

        let n = 0;
        layoutRowKeys().forEach(py => {
            gatherUnitsOnRow(py).forEach(unit => {
                if (unit.ids.length !== 2) return;
                const [pLeft, pRight] = [...unit.ids].sort(
                    (a, b) => coords[a].x - coords[b].x
                );
                const mid = (coords[pLeft].x + coords[pRight].x) / 2;
                coords[pLeft].x = mid - CENTER_DIST / 2;
                coords[pRight].x = mid + CENTER_DIST / 2;
                n++;
            });
        });
        if (n) {
            console.log('[FINAL] Normalized', n, 'married pairs → fixed center distance', CENTER_DIST, 'px');
        }
    }

    // === POST: зазор между соседними блоками на ряду (пара супругов = один блок, иначе карточки липнут) ===
    function separateMarriedClustersOnEachRow() {
        const CARD_EDGE_PAD = 10;
        const MIN_UNIT_GAP = Math.max(FAMILY_GROUP_GAP + 32, CARD_W - 4);

        for (let iter = 0; iter < 28; iter++) {
            let any = false;
            layoutRowKeys().forEach(yRow => {
                const ids = Object.keys(coords).filter(id => snapLayoutRowY(coords[id].y) === yRow);
                if (ids.length < 2) return;
                ids.sort((a, b) => coords[a].x - coords[b].x);

                const clusters = [];
                const inCluster = new Set();
                for (const id of ids) {
                    if (inCluster.has(id)) continue;
                    const cset = new Set([id]);
                    let grow = true;
                    while (grow) {
                        grow = false;
                        for (const pid of [...cset]) {
                            for (const sidRaw of marriageMap.get(pid) || []) {
                                const sid = String(sidRaw);
                                if (!ids.includes(sid) || cset.has(sid)) continue;
                                if (snapLayoutRowY(coords[sid].y) === snapLayoutRowY(coords[pid].y)) {
                                    cset.add(sid);
                                    grow = true;
                                }
                            }
                        }
                    }
                    cset.forEach(p => inCluster.add(p));
                    let lo = Infinity;
                    let hi = -Infinity;
                    cset.forEach(p => {
                        lo = Math.min(lo, coords[p].x - CARD_W / 2 - CARD_EDGE_PAD);
                        hi = Math.max(hi, coords[p].x + CARD_W / 2 + CARD_EDGE_PAD);
                    });
                    clusters.push({ cset, lo, hi });
                }
                clusters.sort((u, v) => u.lo - v.lo);

                let trail = -Infinity;
                clusters.forEach(cl => {
                    if (cl.lo < trail + MIN_UNIT_GAP) {
                        const dx = trail + MIN_UNIT_GAP - cl.lo;
                        cl.cset.forEach(pid => {
                            if (coords[pid]) coords[pid].x += dx;
                        });
                        any = true;
                        cl.lo += dx;
                        cl.hi += dx;
                    }
                    trail = Math.max(trail, cl.hi);
                });
            });
            if (!any) break;
        }
        console.log('[FINAL] Married-cluster row separation applied');
    }

    // === POST: заново ставим ряд детей под актуальной серединой брака ===
    function reAnchorChildrenUnderPlacedParents() {
        function dataParentKey(pid) {
            return (persons[pid].parents || [])
                .map(String)
                .filter(pr => persons[pr])
                .sort()
                .join('|');
        }

        function spouseRowOrderLocal(childId, sp) {
            const arr = sp || [];
            if (arr.length === 1) {
                const ch = persons[childId];
                const s0 = persons[arr[0]];
                const cM = ch?.gender === 'Мужской';
                const sM = s0?.gender === 'Мужской';
                if (cM && !sM) return [childId, arr[0]];
                if (!cM && sM) return [arr[0], childId];
                return [childId, arr[0]];
            }
            if (arr.length > 1) return [childId, ...arr];
            return [childId];
        }

        function multiNw(nCards) {
            if (nCards <= 0) return 0;
            return nCards * CARD_W + (nCards - 1) * SPOUSE_GAP;
        }

        /** Центр bbox всего ряда «ребёнок+супруги» при старте слева от 0 — лучше для линий, чем среднее по центрам детей. */
        function childrenRowBBoxMidFromLeftLocal(children, childSpouses) {
            let leftEdge = 0;
            let minL = Infinity;
            let maxR = -Infinity;
            children.forEach((cid, idx) => {
                const spp = childSpouses.get(cid) || [];
                const order = spouseRowOrderLocal(cid, spp);
                order.forEach((pid, i) => {
                    const cleft = leftEdge + i * (CARD_W + SPOUSE_GAP);
                    minL = Math.min(minL, cleft);
                    maxR = Math.max(maxR, cleft + CARD_W);
                });
                leftEdge += multiNw(1 + spp.length);
                if (idx < children.length - 1) leftEdge += SIBLING_GAP;
            });
            const bboxMidFromRowLeft = Number.isFinite(minL) ? (minL + maxR) / 2 : 0;
            return { bboxMidFromRowLeft, totalRowWidth: leftEdge };
        }

        function writeChildBlockFromLeft(xLeft, yRow, childId, spArr) {
            const order = spouseRowOrderLocal(childId, spArr || []);
            let px = xLeft;
            for (let i = 0; i < order.length; i++) {
                const pid = order[i];
                if (!coords[pid]) continue;
                coords[pid].x = px + CARD_W / 2;
                coords[pid].y = yRow;
                px += CARD_W + (i < order.length - 1 ? SPOUSE_GAP : 0);
            }
            return multiNw(order.length);
        }

        function writeOneChildAnchoredMid(midX, yRow, childId, spArr) {
            const order = spouseRowOrderLocal(childId, spArr || []);
            const k = order.indexOf(childId);
            if (k < 0) {
                if (coords[childId]) {
                    coords[childId].x = midX;
                    coords[childId].y = yRow;
                }
                return;
            }
            const centers = new Array(order.length);
            centers[k] = midX;
            for (let j = k - 1; j >= 0; j--) {
                centers[j] = centers[j + 1] - CARD_W - SPOUSE_GAP;
            }
            for (let j = k + 1; j < order.length; j++) {
                centers[j] = centers[j - 1] + CARD_W + SPOUSE_GAP;
            }
            order.forEach((pid, i) => {
                if (coords[pid]) {
                    coords[pid].x = centers[i];
                    coords[pid].y = yRow;
                }
            });
        }

        function spousesNextToChildOnRow(childId) {
            const cy = coords[childId] ? coords[childId].y : null;
            if (cy == null) return [];
            const rowSnap = snapLayoutRowY(cy);
            return (marriageMap.get(childId) || []).map(String).filter(sid => {
                if (!related.has(sid) || !coords[sid]) return false;
                return snapLayoutRowY(coords[sid].y) === rowSnap;
            });
        }

        /** Геометрия блока «ребёнок по mid» без записи в coords */
        function geomOneFamilyAnchoredMid(midX, childId, spArr) {
            const order = spouseRowOrderLocal(childId, spArr || []);
            const k = order.indexOf(childId);
            if (k < 0) {
                return { left: midX - CARD_W / 2, width: CARD_W };
            }
            const centers = new Array(order.length);
            centers[k] = midX;
            for (let j = k - 1; j >= 0; j--) {
                centers[j] = centers[j + 1] - CARD_W - SPOUSE_GAP;
            }
            for (let j = k + 1; j < order.length; j++) {
                centers[j] = centers[j - 1] + CARD_W + SPOUSE_GAP;
            }
            const lo = Math.min(...centers) - CARD_W / 2;
            const hi = Math.max(...centers) + CARD_W / 2;
            return { left: lo, width: hi - lo };
        }

        function resolvePackLeft(idealLeft, groupWidth, occupied, gap) {
            let start = idealLeft;
            let guard = 0;
            while (guard++ < 320) {
                let hit = false;
                for (const r of occupied) {
                    if (rangesOverlap(start, start + groupWidth, r.left, r.right)) {
                        start = r.right + gap;
                        hit = true;
                        break;
                    }
                }
                if (!hit) break;
            }
            return start;
        }

        function packStartValid(s, groupWidth, occupied, gap) {
            if (groupWidth <= 0) return true;
            for (const r of occupied) {
                if (!(s >= r.right + gap || s + groupWidth <= r.left)) return false;
            }
            return true;
        }

        /** Старт блока: из допустимых позиций выбираем ближайшую к idealLeft (не только сдвиг вправо). */
        function resolvePackNearest(idealLeft, groupWidth, occupied, gap) {
            if (groupWidth <= 0) return idealLeft;
            const cands = new Set([idealLeft]);
            for (const r of occupied) {
                cands.add(r.right + gap);
                cands.add(r.left - gap - groupWidth);
            }
            let best = resolvePackLeft(idealLeft, groupWidth, occupied, gap);
            let bestAbs = Math.abs(best - idealLeft);
            for (const s of cands) {
                if (!packStartValid(s, groupWidth, occupied, gap)) continue;
                const d = Math.abs(s - idealLeft);
                if (d < bestAbs - 1e-6 || (Math.abs(d - bestAbs) < 1e-6 && s < best)) {
                    bestAbs = d;
                    best = s;
                }
            }
            return best;
        }

        let groups = 0;
        const PACK_GAP = Math.max(FAMILY_GROUP_GAP + 12, SIBLING_GAP + 28);

        layoutRowKeys().forEach(py => {
            const cry = py + LEVEL_HEIGHT;

            /** Все ключи родителей -> дети на ряду cry */
            const byKey = new Map();
            Object.keys(coords).forEach(cid => {
                if (!related.has(cid) || !coords[cid] || !persons[cid]) return;
                if (snapLayoutRowY(coords[cid].y) !== cry) return;
                const pk = dataParentKey(cid);
                if (!pk) return;
                const prs = pk.split('|').filter(Boolean);
                const onGenAbove = prs.some(
                    pr => coords[pr] && snapLayoutRowY(coords[pr].y) === py
                );
                if (!onGenAbove) return;
                if (!byKey.has(pk)) byKey.set(pk, []);
                byKey.get(pk).push(cid);
            });

            const rowGroups = [];
            byKey.forEach((childList, pk) => {
                childList.sort((a, b) => {
                    const da = persons[a]?.birth_date || '9999.99.99';
                    const db = persons[b]?.birth_date || '9999.99.99';
                    if (da !== db) return da.localeCompare(db);
                    return String(a).localeCompare(String(b));
                });

                const prIds = pk.split('|').filter(Boolean);
                const placedOnRowAbove = prIds.filter(
                    pr => coords[pr] && snapLayoutRowY(coords[pr].y) === py
                );
                if (placedOnRowAbove.length === 0) return;

                let midX;
                if (placedOnRowAbove.length >= 2) {
                    midX =
                        placedOnRowAbove.reduce((s, pr) => s + coords[pr].x, 0) /
                        placedOnRowAbove.length;
                } else {
                    midX = coords[placedOnRowAbove[0]].x;
                }

                const csMap = new Map();
                childList.forEach(cid => csMap.set(cid, spousesNextToChildOnRow(cid)));
                rowGroups.push({ pk, childList, midX, csMap });
            });

            rowGroups.sort((a, b) => a.midX - b.midX);
            const rowOccupied = [];

            rowGroups.forEach(g => {
                if (g.childList.length === 1) {
                    const cid = g.childList[0];
                    const sp = g.csMap.get(cid) || [];
                    const geom0 = geomOneFamilyAnchoredMid(g.midX, cid, sp);
                    let resolvedLeft = geom0.left;
                    if (!packStartValid(resolvedLeft, geom0.width, rowOccupied, PACK_GAP)) {
                        resolvedLeft = resolvePackNearest(
                            geom0.left,
                            geom0.width,
                            rowOccupied,
                            PACK_GAP
                        );
                    }
                    const dMid = resolvedLeft - geom0.left;
                    writeOneChildAnchoredMid(g.midX + dMid, cry, cid, sp);
                    registerOccupied(resolvedLeft, geom0.width, rowOccupied);
                } else {
                    const centerXs = bloodChildCenterXs(g.midX, g.childList);
                    let minL = Infinity;
                    let maxR = -Infinity;
                    g.childList.forEach((cid, i) => {
                        const geom = geomOneFamilyAnchoredMid(centerXs[i], cid, g.csMap.get(cid) || []);
                        minL = Math.min(minL, geom.left);
                        maxR = Math.max(maxR, geom.left + geom.width);
                    });
                    const groupWidth = maxR - minL;
                    let resolvedLeft = minL;
                    if (!packStartValid(resolvedLeft, groupWidth, rowOccupied, PACK_GAP)) {
                        resolvedLeft = resolvePackNearest(
                            minL,
                            groupWidth,
                            rowOccupied,
                            PACK_GAP
                        );
                    }
                    const dx = resolvedLeft - minL;
                    g.childList.forEach((cid, i) => {
                        writeOneChildAnchoredMid(centerXs[i] + dx, cry, cid, g.csMap.get(cid) || []);
                    });
                    shiftParentMarriageUnitOnKey(g.pk, py, dx);
                    registerOccupied(resolvedLeft, groupWidth, rowOccupied);
                }
                groups++;
            });
        });

        /**
         * После pack дети часто смещены относительно середины брака родителей:
         * вертикаль тогда «приземляется» на край горизонтали. Сдвигаем целый кластер
         * (ребёнок + супруги на том же ряду) к midX, насколько позволяют зазоры PACK_GAP.
         */
        function collectGroupNodeIds(childList, csMap) {
            const ids = new Set();
            childList.forEach(cid => {
                if (coords[cid]) ids.add(cid);
                (csMap.get(cid) || []).forEach(sid => {
                    if (coords[sid]) ids.add(sid);
                });
            });
            return ids;
        }

        function horizExtentsForCluster(childList, csMap, rowSnapY) {
            let lo = Infinity;
            let hi = -Infinity;
            childList.forEach(cid => {
                const order = spouseRowOrderLocal(cid, csMap.get(cid) || []);
                order.forEach(pid => {
                    const c = coords[pid];
                    if (!c || snapLayoutRowY(c.y) !== rowSnapY) return;
                    lo = Math.min(lo, c.x - CARD_W / 2);
                    hi = Math.max(hi, c.x + CARD_W / 2);
                });
            });
            if (!Number.isFinite(lo)) return null;
            return { lo, hi, width: hi - lo };
        }

        for (let rpass = 0; rpass < 14; rpass++) {
            let movedRelax = false;
            layoutRowKeys().forEach(pyRelax => {
                const cryRelax = pyRelax + LEVEL_HEIGHT;

                const byKeyRelax = new Map();
                Object.keys(coords).forEach(cid => {
                    if (!related.has(cid) || !coords[cid] || !persons[cid]) return;
                    if (snapLayoutRowY(coords[cid].y) !== cryRelax) return;
                    const pk = dataParentKey(cid);
                    if (!pk) return;
                    const prs = pk.split('|').filter(Boolean);
                    const onGenAbove = prs.some(
                        pr => coords[pr] && snapLayoutRowY(coords[pr].y) === pyRelax
                    );
                    if (!onGenAbove) return;
                    if (!byKeyRelax.has(pk)) byKeyRelax.set(pk, []);
                    byKeyRelax.get(pk).push(cid);
                });

                const rg = [];
                byKeyRelax.forEach((childList, pk) => {
                    childList.sort((a, b) => {
                        const da = persons[a]?.birth_date || '9999.99.99';
                        const db = persons[b]?.birth_date || '9999.99.99';
                        if (da !== db) return da.localeCompare(db);
                        return String(a).localeCompare(String(b));
                    });
                    const prIds = pk.split('|').filter(Boolean);
                    const placedOnRowAbove = prIds.filter(
                        pr => coords[pr] && snapLayoutRowY(coords[pr].y) === pyRelax
                    );
                    if (placedOnRowAbove.length === 0) return;
                    let midXR;
                    if (placedOnRowAbove.length >= 2) {
                        midXR =
                            placedOnRowAbove.reduce((s, pr) => s + coords[pr].x, 0) /
                            placedOnRowAbove.length;
                    } else {
                        midXR = coords[placedOnRowAbove[0]].x;
                    }
                    const csMapR = new Map();
                    childList.forEach(cid => csMapR.set(cid, spousesNextToChildOnRow(cid)));
                    rg.push({ pk, childList, midX: midXR, csMap: csMapR });
                });

                rg.forEach(entry => {
                    const ex = horizExtentsForCluster(entry.childList, entry.csMap, cryRelax);
                    entry._extent = ex;
                });

                rg.sort(
                    (a, b) =>
                        (a._extent?.lo ?? Infinity) - (b._extent?.lo ?? Infinity)
                );

                let prevHi = -Infinity;
                rg.forEach((entry, idx) => {
                    const ext = entry._extent;
                    if (!ext) return;
                    let lo = ext.lo;
                    let hi = ext.hi;
                    const clusterMid = (lo + hi) / 2;
                    let deltaIdeal = entry.midX - clusterMid;

                    const next = rg[idx + 1];
                    const nextLo = next && next._extent ? next._extent.lo : Infinity;

                    const deltaMin = prevHi + PACK_GAP - lo;
                    const deltaMax = Number.isFinite(nextLo) ? nextLo - PACK_GAP - hi : Infinity;
                    let delta = deltaIdeal;
                    if (delta < deltaMin) delta = deltaMin;
                    if (delta > deltaMax) delta = deltaMax;

                    if (Math.abs(delta) > 0.25) {
                        const toMove = collectGroupNodeIds(entry.childList, entry.csMap);
                        toMove.forEach(pid => {
                            if (coords[pid]) coords[pid].x += delta;
                        });
                        movedRelax = true;
                        lo += delta;
                        hi += delta;
                    }
                    prevHi = Math.max(prevHi, hi);
                });
            });
            if (!movedRelax) break;
        }

        if (groups) {
            console.log(
                '[FINAL] Re-anchored children under parents (row pack, gap≥',
                PACK_GAP,
                '):',
                groups,
                'groups (+ relax toward marriage mid)'
            );
        }
    }
    reAnchorChildrenUnderPlacedParents();
    normalizeMarriedCoupleSpacing();
    separateMarriedClustersOnEachRow();
    reAnchorChildrenUnderPlacedParents();
    normalizeMarriedCoupleSpacing();
    separateMarriedClustersOnEachRow();

    // === ПРОВЕРКА ПОСЛЕ РАЗМЕЩЕНИЯ: где кто оказался ===
    console.log('[FINAL] === FINAL COORDINATES CHECK ===');
    Object.entries(coords).forEach(([pid, pos]) => {
        const person = persons[pid];
        if (person && person.parents) {
            const parentCoords = person.parents.map(prId => {
                const pr = coords[prId];
                return pr ? `${pr.x.toFixed(0)},${pr.y.toFixed(0)}` : 'NOT_PLACED';
            }).join(' | ');
            const parentNames = person.parents.map(prId => persons[prId]?.name || prId).join(', ');
            console.log(`[FINAL] ${pid}(${person.name}) at [${pos.x.toFixed(0)},${pos.y.toFixed(0)}] | Parents: [${parentNames}] at [${parentCoords}]`);
        }
    });
    
    // === 3. ГРАНИЦЫ ===
    // === ПРОВЕРКА: если координаты пустые, возвращаем значения по умолчанию ===
    if (Object.keys(coords).length === 0) {
        console.log('[FINAL] No coords placed, using default bounds');
        return { coords: {}, bounds: {left:0,right:400,top:0,bottom:300}, totalW:400, totalH:300, offsetX:60, offsetY:60 };
    }

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    Object.values(coords).forEach(pos => {
        minX = Math.min(minX, pos.x - CARD_W/2);
        minY = Math.min(minY, pos.y - CARD_H/2);
        maxX = Math.max(maxX, pos.x + CARD_W/2);
        maxY = Math.max(maxY, pos.y + CARD_H/2);
    });
    
    const bounds = { left: minX, top: minY, right: maxX, bottom: maxY };
    const offsetX = Math.max(0, -minX) + PAD;
    const offsetY = Math.max(0, -minY) + PAD;
    const totalW = maxX - minX + PAD * 2;
    const totalH = maxY - minY + PAD * 2;
    
    return { coords, bounds, totalW, totalH, offsetX, offsetY };
}

window.renderFinalLayout = renderFinalLayout;
