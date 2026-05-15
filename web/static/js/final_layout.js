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
    const LEVEL_HEIGHT = 252;
    const PAD = 60;

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
            if (Array.isArray(marriage) && marriage.length >= 2) {
                const p1 = String(marriage[0]);
                const p2 = String(marriage[1]);
                if (!marriageMap.has(p1)) marriageMap.set(p1, []);
                if (!marriageMap.has(p2)) marriageMap.set(p2, []);
                marriageMap.get(p1).push(p2);
                marriageMap.get(p2).push(p1);
            }
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
    
    // === 1.5. ДОБАВЛЯЕМ ОСТАЛЬНЫХ ===
    // Добавляем только тех, кто не был добавлен и не является предком по женской линии
    const remaining = Array.from(related).filter(pid => {
        if (!visited.has(pid) && persons[pid]) {
            const person = persons[pid];
            const isFemale = person.gender === 'Женский';

            // Проверяем, является ли эта персона предком по женской линии
            if (person.children) {
                for (const childId of person.children) {
                    const child = persons[childId];
                    if (child && child.gender === 'Женский' && String(childId) !== String(centerId)) {
                        // Эта персона - родитель женской персоны (не центр)
                        // Скрываем по правилу 1
                        console.log('[FINAL] Skipping ancestor of female:', pid, '→', childId);
                        return false;
                    }
                }
            }

            // Проверяем, является ли эта персона предком супруга центральной женской персоны
            if (isCenterFemale && centerSpouseId && person.children) {
                for (const childId of person.children) {
                    if (String(childId) === String(centerSpouseId)) {
                        // Эта персона - родитель супруга центральной женской персоны
                        // Скрываем по правилу 3
                        console.log('[FINAL] Skipping ancestor of center spouse:', pid, '→', centerSpouseId);
                        return false;
                    }
                }
            }

            return true;
        }
        return false;
    });
    console.log('[FINAL] Remaining persons:', remaining.length);

    if (remaining.length > 0) {
        // Размещаем их на уровне 0 справа от остальных
        if (!levels.has(0)) levels.set(0, []);
        remaining.forEach(pid => {
            // === ПРОВЕРКА: не добавлен ли уже на этот уровень ===
            if (!levels.get(0).includes(pid)) {
                levels.get(0).push(pid);
            }
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
            // === ИСПРАВЛЕНИЕ: Защита от пустых массивов ===
            const minX_A = parentsA.length > 0 ? Math.min(...parentsA) : 0;
            const minX_B = parentsB.length > 0 ? Math.min(...parentsB) : 0;
            return minX_A - minX_B;
        });

        console.log(`[FINAL] sortedGroups: ${sortedGroups.length} groups: ${sortedGroups.map(([k, g]) => `[${k}]:${g.children.length}`).join(', ')}`);

        // === ШАГ 4: Размещаем группы СЛЕВА (семьи с родителями) ===
        let currentX = 0;  // Начинаем с 0 для каждого уровня

        sortedGroups.forEach(([parentKey, group]) => {
            const { parentIds, children, childSpouses } = group;

            // Сортируем детей по дате рождения
            children.sort((a, b) => {
                const da = persons[a]?.birth_date || '9999.99.99';
                const db = persons[b]?.birth_date || '9999.99.99';
                return da.localeCompare(db);
            });

            // === Вычисляем X для размещения ===
            let groupStartX;
            const hasPlacedParents = parentIds.every(id => coords[id] !== undefined);

            if (parentIds.length === 2 && hasPlacedParents) {
                const p1 = coords[parentIds[0]];
                const p2 = coords[parentIds[1]];
                // === ПРОВЕРКА: координаты родителей существуют ===
                if (!p1 || !p2) {
                    console.log('[FINAL] Parents coords missing, adding to orphans');
                    children.forEach(childId => orphanSet.add(childId));
                    return;
                }
                const parentCenterX = (p1.x + p2.x) / 2;

                let totalWidth = 0;
                children.forEach((childId, idx) => {
                    const spouses = childSpouses.get(childId) || [];
                    // Супруги всегда рядом: считаем как 1 блок
                    totalWidth += CARD_W + spouses.length * (CARD_W + SPOUSE_GAP);
                    if (idx < children.length - 1) {
                        totalWidth += SIBLING_GAP;
                    }
                });

                // === ИСПРАВЛЕНИЕ: Для одного ребёнка центрируем точно под родителями ===
                if (children.length === 1) {
                    const childId = children[0];
                    const spouses = childSpouses.get(childId) || [];
                    
                    if (spouses.length === 0) {
                        // Один ребёнок без супруга — центр карточки = центр родителей
                        groupStartX = parentCenterX - CARD_W / 2;
                    } else {
                        // Один ребёнок с супругом — центр пары = центр родителей
                        const pairWidth = 2 * CARD_W + SPOUSE_GAP;
                        groupStartX = parentCenterX - pairWidth / 2;
                    }
                } else {
                    // Несколько детей — обычное центрирование
                    groupStartX = parentCenterX - totalWidth / 2;
                }

                // === ВАЖНО: Если группа наезжает на предыдущую — сдвигаем вправо ===
                if (currentX > 0 && groupStartX < currentX) {
                    console.log(`[FINAL] Group [${parentKey}] overlaps! Moving from ${groupStartX.toFixed(0)} to ${currentX.toFixed(0)}`);
                    groupStartX = currentX;
                }

                console.log(`[FINAL] Group under parents [${parentKey}]: ${children.length} children, center=${parentCenterX.toFixed(1)}, startX=${groupStartX.toFixed(1)}`);
                
                // === Размещаем детей и супругов РЯДОМ ===
                let x = groupStartX;

                children.forEach(childId => {
                    const spouses = childSpouses.get(childId) || [];
                    const child = persons[childId];
                    const childIsMale = child?.gender === 'Мужской';

                    let mainPersonId = childId;
                    let spouseId = null;

                    if (spouses.length === 1) {
                        const spouse = persons[spouses[0]];
                        const spouseIsMale = spouse?.gender === 'Мужской';

                        if (childIsMale && !spouseIsMale) {
                            mainPersonId = childId;
                            spouseId = spouses[0];
                        } else if (!childIsMale && spouseIsMale) {
                            mainPersonId = spouses[0];
                            spouseId = childId;
                        }
                    }

                    // Размещаем главную персону (слева)
                    coords[mainPersonId] = { x: x + CARD_W / 2, y: yPos };
                    placed.add(mainPersonId);

                    // Размещаем супруга (справа) если есть
                    if (spouseId) {
                        coords[spouseId] = { x: x + CARD_W + SPOUSE_GAP + CARD_W / 2, y: yPos };
                        placed.add(spouseId);
                    }
                    
                    // ВАЖНО: Помечаем ВСЕХ детей и супругов как размещённых
                    placed.add(childId);
                    spouses.forEach(spId => placed.add(spId));

                    const blockWidth = CARD_W + spouses.length * (CARD_W + SPOUSE_GAP);
                    x += blockWidth + SIBLING_GAP;
                });

                currentX = Math.max(currentX, x);
            } else if (parentIds.length === 1 && hasPlacedParents) {
                const p = coords[parentIds[0]];
                // === ПРОВЕРКА: координаты родителя существуют ===
                if (!p) {
                    console.log('[FINAL] Parent coords missing, adding to orphans');
                    children.forEach(childId => orphanSet.add(childId));
                    return;
                }

                let groupTotalWidth = 0;
                children.forEach((childId, idx) => {
                    const spouses = childSpouses.get(childId) || [];
                    groupTotalWidth += CARD_W + spouses.length * (CARD_W + SPOUSE_GAP);
                    if (idx < children.length - 1) {
                        groupTotalWidth += SIBLING_GAP;
                    }
                });

                // === ИСПРАВЛЕНИЕ: Для одного ребёнка центрируем точно под родителем ===
                if (children.length === 1) {
                    const childId = children[0];
                    const spouses = childSpouses.get(childId) || [];
                    
                    if (spouses.length === 0) {
                        // Один ребёнок без супруга — центр карточки = центр родителя
                        groupStartX = p.x - CARD_W / 2;
                    } else {
                        // Один ребёнок с супругом — центр пары = центр родителя
                        const pairWidth = 2 * CARD_W + SPOUSE_GAP;
                        groupStartX = p.x - pairWidth / 2;
                    }
                } else {
                    // Несколько детей — обычное центрирование
                    groupStartX = p.x - groupTotalWidth / 2;
                }

                // === ВАЖНО: Если группа наезжает на предыдущую — сдвигаем вправо ===
                if (currentX > 0 && groupStartX < currentX) {
                    console.log(`[FINAL] Group [${parentKey}] overlaps! Moving from ${groupStartX.toFixed(0)} to ${currentX.toFixed(0)}`);
                    groupStartX = currentX;
                }

                console.log(`[FINAL] Group under single parent [${parentKey}]: ${children.length} children, parentX=${p.x.toFixed(1)}, groupWidth=${groupTotalWidth.toFixed(1)}, startX=${groupStartX.toFixed(1)}`);
                
                // === Размещаем детей и супругов РЯДОМ ===
                let x = groupStartX;

                children.forEach(childId => {
                    const spouses = childSpouses.get(childId) || [];
                    const child = persons[childId];
                    const childIsMale = child?.gender === 'Мужской';

                    let mainPersonId = childId;
                    let spouseId = null;

                    if (spouses.length === 1) {
                        const spouse = persons[spouses[0]];
                        const spouseIsMale = spouse?.gender === 'Мужской';

                        if (childIsMale && !spouseIsMale) {
                            mainPersonId = childId;
                            spouseId = spouses[0];
                        } else if (!childIsMale && spouseIsMale) {
                            mainPersonId = spouses[0];
                            spouseId = childId;
                        }
                    }

                    // Размещаем главную персону (слева)
                    coords[mainPersonId] = { x: x + CARD_W / 2, y: yPos };
                    placed.add(mainPersonId);

                    // Размещаем супруга (справа) если есть
                    if (spouseId) {
                        coords[spouseId] = { x: x + CARD_W + SPOUSE_GAP + CARD_W / 2, y: yPos };
                        placed.add(spouseId);
                    }
                    
                    // ВАЖНО: Помечаем ВСЕХ детей и супругов как размещённых
                    placed.add(childId);
                    spouses.forEach(spId => placed.add(spId));

                    const blockWidth = CARD_W + spouses.length * (CARD_W + SPOUSE_GAP);
                    x += blockWidth + SIBLING_GAP;
                });

                currentX = Math.max(currentX, x);
            } else {
                // Родители не размещены — добавляем детей в сироты для ШАГА 5
                console.log(`[FINAL] Group [${parentKey}]: parents not placed (${parentIds.length}), adding ${children.length} children to orphans`);
                children.forEach(childId => {
                    orphanSet.add(childId);
                    // ИСПОЛЬЗУЕМ marriageMap вместо spouse_ids
                    const allSpouses = marriageMap.get(childId) || [];
                    allSpouses.forEach(spId => {
                        if (pids.includes(spId)) {
                            orphanSet.add(spId);
                        }
                    });
                });
                // НЕ помечаем детей как placed - они будут размещены в ШАГЕ 5
            }
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
        
        // Размещаем пары сирот
        orphansWithSpouses.forEach(([pid1, pid2]) => {
            const p1 = persons[pid1];
            const p1IsMale = p1?.gender === 'Мужской';
            
            const mainId = p1IsMale ? pid1 : pid2;
            const spouseId = p1IsMale ? pid2 : pid1;
            
            coords[mainId] = { x: currentX + CARD_W / 2, y: yPos };
            coords[spouseId] = { x: currentX + CARD_W + SPOUSE_GAP + CARD_W / 2, y: yPos };
            placed.add(mainId);
            placed.add(spouseId);
            
            console.log(`[FINAL] Orphan spouse pair: ${mainId}(${persons[mainId]?.name}) + ${spouseId}(${persons[spouseId]?.name}) at [${currentX + CARD_W/2},${yPos}]`);
            currentX += 2 * CARD_W + SPOUSE_GAP + SIBLING_GAP;
        });
        
        // Размещаем одиноких сирот
        singleOrphans.forEach(pid => {
            placed.add(pid);
            coords[pid] = { x: currentX + CARD_W / 2, y: yPos };
            currentX += CARD_W + SIBLING_GAP;
            console.log(`[FINAL] Orphan ${pid}(${persons[pid]?.name}) at [${currentX - CARD_W/2},${yPos}]`);
        });

        console.log(`[FINAL] Level ${level} placed: ${placed.size} persons`);
    }

    console.log('[FINAL] Placed persons:', Object.keys(coords).length);
    
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
