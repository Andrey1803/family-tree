/**
 * ЛОГИКА СБОРА ВИДИМЫХ ПЕРСОН (копия с desktop-версии)
 * 
 * Собирает:
 * - Всех предков (родители, дедушки/бабушки, и т.д.)
 * - Всех потомков (дети, внуки, и т.д.)
 * - Всех братьев/сестёр (через общих родителей)
 * - Всех супругов (в т.ч. второй/третий брак)
 * - Супругов братьев/сестёр
 */
function collectVisiblePersons(centerId, persons, marriages) {
    const visibleSet = new Set();
    const visited = new Set();
    
    if (!centerId) {
        // Если центр не задан — показываем ВСЕХ персон
        Object.keys(persons).forEach(id => visibleSet.add(id));
        return visibleSet;
    }
    
    // Нормализуем centerId к строке
    const centerIdStr = String(centerId);
    
    // Проверяем, существует ли центральная персона
    console.log('[VISIBLE] Looking for centerId:', centerIdStr, 'in persons:', !!persons[centerIdStr]);
    console.log('[VISIBLE] persons keys:', Object.keys(persons).slice(0, 5));
    
    if (!persons[centerIdStr]) {
        console.log('[VISIBLE] Center person NOT FOUND:', centerIdStr);
        // Если центр не найден — показываем всех
        Object.keys(persons).forEach(id => visibleSet.add(id));
        return visibleSet;
    }
    
    // BFS для сбора КРОВНЫХ родственников (предки, потомки, братья/сёстры)
    const queue = [centerIdStr];

    console.log('[VISIBLE] Starting BFS with:', centerIdStr);

    let iteration = 0;
    while (queue.length > 0) {
        iteration++;
        const currentPid = queue.shift();

        console.log('[VISIBLE] BFS iteration', iteration, ', processing:', currentPid, ', queue length:', queue.length);

        if (!persons[currentPid]) {
            console.log('[VISIBLE] Person NOT FOUND:', currentPid);
            continue;
        }

        if (visited.has(currentPid)) {
            console.log('[VISIBLE] Already visited:', currentPid);
            continue;
        }

        // Добавляем в кровные родственники
        visited.add(currentPid);
        visibleSet.add(currentPid);
        const person = persons[currentPid];

        console.log('[VISIBLE] Added blood relative:', currentPid, ', parents:', person.parents, ', children:', person.children);

        // Добавляем ТОЛЬКО кровных: родители, дети, братья/сёстры (СУПРУГИ НЕ ДОБАВЛЯЕМ!)
        if (person.parents) {
            person.parents.forEach(parentId => {
                const pStr = String(parentId);
                if (!visited.has(pStr)) {
                    queue.push(pStr);
                    console.log('[VISIBLE] Added parent to queue:', pStr);
                }
            });
        }

        if (person.children) {
            person.children.forEach(childId => {
                const cStr = String(childId);
                if (!visited.has(cStr)) {
                    queue.push(cStr);
                    console.log('[VISIBLE] Added child to queue:', cStr);
                }
            });
        }

        // Добавляем siblings (через родителей)
        if (person.parents) {
            person.parents.forEach(parentId => {
                const parent = persons[String(parentId)];
                if (parent && parent.children) {
                    parent.children.forEach(siblingId => {
                        const sk = String(siblingId);
                        if (sk !== currentPid && !visited.has(sk)) {
                            queue.push(sk);
                            console.log('[VISIBLE] Added sibling to queue:', sk);
                        }
                    });
                }
            });
        }
    }

    console.log('[VISIBLE] After blood relatives BFS:', visibleSet.size, 'persons');

    // === ДОБАВЛЯЕМ СУПРУГОВ ДЛЯ ВСЕХ КРОВНЫХ РОДСТВЕННИКОВ ===
    const spousesToAdd = new Set();
    visibleSet.forEach(pid => {
        const person = persons[pid];
        if (person && person.spouse_ids) {
            person.spouse_ids.forEach(spouseId => {
                const spouseStr = String(spouseId);
                if (!visibleSet.has(spouseStr)) {
                    spousesToAdd.add(spouseStr);
                    console.log('[VISIBLE] Will add spouse:', spouseStr, 'for:', pid);
                }
            });
        }
    });
    spousesToAdd.forEach(spouseStr => visibleSet.add(spouseStr));

    console.log('[VISIBLE] After adding spouses:', visibleSet.size, 'persons');

    return visibleSet;
}

/**
 * ПРОВЕРКА: ЯВЛЯЕТСЯ ЛИ ПЕРСОНА ПРЕДКОМ (копия _is_ancestor из desktop)
 */
function isAncestor(persons, ancestorId, descendantId) {
    const visited = new Set();
    const queue = [descendantId];
    
    while (queue.length > 0) {
        const currentId = queue.shift();
        const key = String(currentId);
        
        if (visited.has(key)) {
            continue;
        }
        
        visited.add(key);
        
        if (key === String(ancestorId)) {
            return true;
        }
        
        const person = persons[key];
        if (person && person.parents) {
            person.parents.forEach(parentId => {
                queue.push(parentId);
            });
        }
    }
    
    return false;
}

/**
 * ПРИМЕНЕНИЕ СВОРАЧИВАНИЯ ВЕТВЕЙ (копия с desktop)
 */
function applyCollapse(visibleSet, persons) {
    const afterCollapse = new Set();
    
    visibleSet.forEach(pid => {
        const person = persons[pid];
        if (!person) {
            return;
        }
        
        let isHidden = false;
        if (person.parents) {
            for (const parentId of person.parents) {
                const parent = persons[String(parentId)];
                if (parent && parent.collapsed_branches) {
                    isHidden = true;
                    break;
                }
            }
        }
        
        if (!isHidden) {
            afterCollapse.add(pid);
        }
    });
    
    return afterCollapse;
}

/**
 * ПРИМЕНЕНИЕ РЕЖИМА ФОКУСА (копия с desktop)
 */
function applyFocusMode(afterCollapse, persons, centerId, focusModeActive) {
    if (!focusModeActive || !centerId) {
        return afterCollapse;
    }
    
    const afterFocus = new Set();
    
    afterCollapse.forEach(pid => {
        // Показываем центральную персону и НЕ предков
        if (pid === String(centerId) || !isAncestor(persons, pid, centerId)) {
            afterFocus.add(pid);
        }
    });
    
    return afterFocus;
}

/**
 * ПРИМЕНЕНИЕ ВНЕШНИХ ФИЛЬТРОВ (копия с desktop)
 */
function applyFilters(afterFocus, persons, activeFilters) {
    const filteredVisible = new Set();
    
    afterFocus.forEach(pid => {
        const person = persons[pid];
        if (!person) {
            return;
        }
        
        // Фильтр "Только с фото"
        if (activeFilters.photos_only) {
            const hasPhoto = person.photo_path || person.photo;
            if (!hasPhoto || !String(hasPhoto).trim()) {
                return;
            }
        }
        
        // Фильтр "Только бездетные"
        if (activeFilters.childless) {
            if (person.children && person.children.length > 0) {
                return;
            }
        }
        
        // Фильтр по полу
        if (activeFilters.gender !== "Все") {
            if (activeFilters.gender === "Только мужчины" && person.gender !== "Мужской") {
                return;
            }
            if (activeFilters.gender === "Только женщины" && person.gender !== "Женский") {
                return;
            }
        }
        
        // Фильтр по статусу
        if (activeFilters.status === "Только живые" && person.is_deceased) {
            return;
        }
        
        filteredVisible.add(pid);
    });
    
    return filteredVisible;
}

/**
 * ГЛАВНАЯ ФУНКЦИЯ СБОРА ВИДИМЫХ ПЕРСОН (полная копия desktop-версии)
 */
function getVisiblePersons(centerId, persons, marriages, focusModeActive, activeFilters) {
    console.log('[VISIBLE] Starting collection, centerId:', centerId);
    
    // 1. Собираем всех связанных персон
    const visibleSet = collectVisiblePersons(centerId, persons, marriages);
    console.log('[VISIBLE] After collectVisiblePersons:', visibleSet.size, 'persons');
    
    // 2. Применяем сворачивание ветвей
    const afterCollapse = applyCollapse(visibleSet, persons);
    console.log('[VISIBLE] After collapse:', afterCollapse.size, 'persons');
    
    // 3. Применяем режим фокуса
    const afterFocus = applyFocusMode(afterCollapse, persons, centerId, focusModeActive);
    console.log('[VISIBLE] After focus:', afterFocus.size, 'persons');
    
    // 4. Применяем внешние фильтры
    const filteredVisible = applyFilters(afterFocus, persons, activeFilters);
    console.log('[VISIBLE] After filters:', filteredVisible.size, 'persons');
    
    return filteredVisible;
}
