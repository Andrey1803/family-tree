/**
 * ЛОГИКА СБОРА ВИДИМЫХ ПЕРСОН
 * Показываем всех кровных родственников (общий предок) и их супругов
 */
function collectVisiblePersons(centerId, persons, marriages) {
    const visibleSet = new Set();
    const centerIdStr = String(centerId);

    // === 1. Находим всех предков центральной персоны ===
    const ancestors = new Set();
    
    function addAncestors(pid) {
        const person = persons[String(pid)];
        if (!person || !person.parents) return;
        
        for (const parentId of person.parents) {
            const parentStr = String(parentId);
            if (!ancestors.has(parentStr)) {
                ancestors.add(parentStr);
                addAncestors(parentStr);  // Рекурсивно добавляем предков родителя
            }
        }
    }
    
    // Добавляем саму центральную персону как "предка" для себя
    ancestors.add(centerIdStr);
    addAncestors(centerIdStr);
    
    console.log('[VISIBLE] Ancestors found:', ancestors.size, Array.from(ancestors).map(id => persons[id]?.name || id).join(', '));
    
    // === 2. Находим всех потомков каждого предка (это и есть все кровные родственники) ===
    const bloodRelatives = new Set();
    
    function addDescendants(pid) {
        const person = persons[String(pid)];
        if (!person) return;
        
        // Добавляем саму персону
        if (!bloodRelatives.has(String(pid))) {
            bloodRelatives.add(String(pid));
        }
        
        // Добавляем детей и их потомков
        if (person.children) {
            for (const childId of person.children) {
                const childStr = String(childId);
                if (!bloodRelatives.has(childStr)) {
                    addDescendants(childStr);  // Рекурсивно добавляем потомков ребёнка
                }
            }
        }
    }
    
    // Для каждого предка находим всех его потомков
    ancestors.forEach(ancestorId => {
        addDescendants(ancestorId);
    });
    
    console.log('[VISIBLE] Blood relatives (including center):', bloodRelatives.size, Array.from(bloodRelatives).slice(0, 20).map(id => persons[id]?.name || id).join(', '));
    
    // === 3. Добавляем всех кровных родственников в visibleSet ===
    bloodRelatives.forEach(pid => {
        visibleSet.add(pid);
    });
    
    // === 4. Добавляем супругов кровных родственников (рекурсивно) ===
    const marriageMap = new Map();  // pid -> [spouse_ids]

    function addMarriagePair(p1, p2) {
        const a = String(p1);
        const b = String(p2);
        if (!marriageMap.has(a)) marriageMap.set(a, []);
        if (!marriageMap.has(b)) marriageMap.set(b, []);
        if (!marriageMap.get(a).includes(b)) marriageMap.get(a).push(b);
        if (!marriageMap.get(b).includes(a)) marriageMap.get(b).push(a);
    }

    if (Array.isArray(marriages)) {
        marriages.forEach(marriage => {
            if (Array.isArray(marriage) && marriage.length >= 2) {
                addMarriagePair(marriage[0], marriage[1]);
            } else if (marriage && marriage.persons && marriage.persons.length >= 2) {
                addMarriagePair(marriage.persons[0], marriage.persons[1]);
            }
        });
    }

    // Добавляем супругов для каждого кровного родственника (рекурсивно)
    const addedSpouses = new Set();
    
    function addSpousesRecursively(pid) {
        const spouses = marriageMap.get(pid) || [];
        spouses.forEach(spouseId => {
            if (!addedSpouses.has(spouseId)) {
                addedSpouses.add(spouseId);
                visibleSet.add(String(spouseId));
                // Рекурсивно добавляем супругов супруга
                addSpousesRecursively(spouseId);
            }
        });
    }

    bloodRelatives.forEach(pid => {
        addSpousesRecursively(pid);
    });

    console.log('[VISIBLE] Added', addedSpouses.size, 'spouses recursively');
    console.log('[VISIBLE] Blood relatives:', bloodRelatives.size, ', Total visible (with spouses):', visibleSet.size, 'persons');
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
function applyCollapse(visibleSet, persons, centerId) {
    const afterCollapse = new Set();

    visibleSet.forEach(pid => {
        const person = persons[pid];
        if (!person) {
            return;
        }

        // === ИСПРАВЛЕНИЕ: Центр никогда не скрывается ===
        if (String(pid) === String(centerId)) {
            afterCollapse.add(pid);
            return;
        }

        // === ИСПРАВЛЕНИЕ: Если у персоны есть дети - не скрываем ===
        if (person.children && person.children.length > 0) {
            afterCollapse.add(pid);
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

    // === ПРОВЕРКА: centerId валиден ===
    if (!centerId || !persons || !persons[centerId]) {
        console.warn('[VISIBLE] Invalid centerId or persons data. Returning empty Set.');
        return new Set();
    }

    // 1. Собираем всех связанных персон
    const visibleSet = collectVisiblePersons(centerId, persons, marriages);
    console.log('[VISIBLE] After collectVisiblePersons:', visibleSet.size, 'persons');

    // 2. Применяем сворачивание ветвей
    const afterCollapse = applyCollapse(visibleSet, persons, centerId);
    console.log('[VISIBLE] After collapse:', afterCollapse.size, 'persons');

    // 3. Применяем режим фокуса
    const afterFocus = applyFocusMode(afterCollapse, persons, centerId, focusModeActive);
    console.log('[VISIBLE] After focus:', afterFocus.size, 'persons');

    // 4. Применяем внешние фильтры
    const filteredVisible = applyFilters(afterFocus, persons, activeFilters);
    console.log('[VISIBLE] After filters:', filteredVisible.size, 'persons');

    return filteredVisible;
}
