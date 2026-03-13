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
    
    // BFS для сбора всех связанных персон
    const queue = [centerId];
    visited.add(String(centerId));
    
    while (queue.length > 0) {
        const currentPid = queue.shift();
        const key = String(currentPid);
        
        if (!persons[key] || visited.has(key)) {
            continue;
        }
        
        visited.add(key);
        visibleSet.add(key);
        const person = persons[key];
        
        // Добавляем всех связанных в очередь
        if (person.parents) {
            person.parents.forEach(parentId => {
                if (!visited.has(String(parentId))) {
                    queue.push(parentId);
                }
            });
        }
        
        if (person.children) {
            person.children.forEach(childId => {
                if (!visited.has(String(childId))) {
                    queue.push(childId);
                }
            });
        }
        
        if (person.spouse_ids) {
            person.spouse_ids.forEach(spouseId => {
                if (!visited.has(String(spouseId))) {
                    queue.push(spouseId);
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
                        if (sk !== key && !visited.has(sk)) {
                            queue.push(siblingId);
                        }
                    });
                }
            });
        }
    }
    
    // === ДОБАВЛЯЕМ ВСЕХ СУПРУГОВ ИЗ marriages ===
    (marriages || []).forEach(m => {
        let a, b;
        if (Array.isArray(m)) {
            [a, b] = m;
        } else if (m.persons && Array.isArray(m.persons)) {
            [a, b] = m.persons;
        } else {
            return;
        }
        
        const aStr = String(a);
        const bStr = String(b);
        
        if (visibleSet.has(aStr) && !visibleSet.has(bStr)) {
            visibleSet.add(bStr);
            console.log('[MARRIAGE_FIX] Добавлен супруг', bStr, 'в visibleSet');
        }
        if (visibleSet.has(bStr) && !visibleSet.has(aStr)) {
            visibleSet.add(aStr);
            console.log('[MARRIAGE_FIX] Добавлен супруг', aStr, 'в visibleSet');
        }
    });
    
    // === ДОБАВЛЯЕМ СУПРУГОВ ДЛЯ ВСЕХ ВИДИМЫХ ПЕРСОН ===
    const additionalSpouses = new Set();
    visibleSet.forEach(pid => {
        const person = persons[pid];
        if (person && person.spouse_ids) {
            person.spouse_ids.forEach(spouseId => {
                const spouseStr = String(spouseId);
                if (!visibleSet.has(spouseStr)) {
                    additionalSpouses.add(spouseStr);
                }
            });
        }
    });
    
    additionalSpouses.forEach(spouseId => {
        visibleSet.add(spouseId);
        console.log('[SPOUSE_FIX] Добавлен супруг', spouseId);
    });
    
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
