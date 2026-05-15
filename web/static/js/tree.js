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
let treeLoaded = false;  // Флаг: дерево загружено

// === РЕЖИМ ОТРИСОВКИ ===
// По умолчанию classic (синхронизирован с desktop-версией)
let renderMode = localStorage.getItem('family_tree_render_mode') || 'classic'; // 'generations' | 'classic'
const RENDER_MODE_KEY = 'family_tree_render_mode';

/**
 * Сохраняет режим отрисовки в localStorage
 */
function setRenderMode(mode) {
    renderMode = mode;
    localStorage.setItem(RENDER_MODE_KEY, mode);
    console.log('[RENDER_MODE] Set to:', mode);
    render();
}

/**
 * Переключает режим отрисовки
 */
function toggleRenderMode() {
    const newMode = renderMode === 'generations' ? 'classic' : 'generations';
    setRenderMode(newMode);
    return newMode;
}

/**
 * Возвращает текущий режим отрисовки
 */
function getRenderMode() {
    return renderMode;
}

// === АВТОСОХРАНЕНИЕ ===
let autoSaveTimer = null;
let lastSavedState = null;
const AUTO_SAVE_INTERVAL = 5 * 60 * 1000; // 5 минут

// === БЭКАПЫ ===
const MAX_BACKUPS = 10;
const BACKUP_KEY = 'family_tree_backups';

/**
 * Проверяет, есть ли несохранённые изменения
 */
function hasUnsavedChanges() {
    const current = JSON.stringify(treeData);
    return current !== lastSavedState;
}

/**
 * Создаёт резервную копию текущего состояния
 */
function createBackup() {
    try {
        const backups = JSON.parse(localStorage.getItem(BACKUP_KEY) || '[]');
        
        // Добавляем новый бэкап
        const backup = {
            timestamp: Date.now(),
            date: new Date().toLocaleString('ru-RU'),
            data: JSON.parse(JSON.stringify(treeData)),
            personsCount: Object.keys(treeData.persons || {}).length,
            size: JSON.stringify(treeData).length
        };
        
        backups.push(backup);
        
        // Удаляем старые бэкапы если больше MAX_BACKUPS
        while (backups.length > MAX_BACKUPS) {
            backups.shift();
        }
        
        // Проверяем размер перед сохранением
        const backupsStr = JSON.stringify(backups);
        const estimatedSize = backupsStr.length;
        
        // localStorage имеет лимит ~5MB, оставляем запас
        if (estimatedSize > 4 * 1024 * 1024) {
            console.warn('[BACKUP] Skipping - estimated size', estimatedSize, 'exceeds limit');
            
            // Удаляем самый старый бэкап и пробуем снова
            if (backups.length > 1) {
                backups.shift();
                const newSize = JSON.stringify(backups).length;
                if (newSize > 4 * 1024 * 1024) {
                    console.warn('[BACKUP] Still too large, clearing old backups');
                    backups.splice(0, Math.floor(backups.length / 2));
                }
            }
        }
        
        localStorage.setItem(BACKUP_KEY, JSON.stringify(backups));
        console.log('[BACKUP] Created backup #' + backups.length);
        
        return true;
    } catch (e) {
        if (e.name === 'QuotaExceededError') {
            console.error('[BACKUP] Quota exceeded! Clearing old backups...');
            
            // Очищаем старые бэкапы
            const backups = JSON.parse(localStorage.getItem(BACKUP_KEY) || '[]');
            if (backups.length > 0) {
                // Оставляем только последний
                const lastBackup = backups[backups.length - 1];
                localStorage.setItem(BACKUP_KEY, JSON.stringify([lastBackup]));
                console.log('[BACKUP] Cleared old backups, kept only last one');
            }
            
            // Пробуем сохранить ещё раз
            try {
                const backup = {
                    timestamp: Date.now(),
                    date: new Date().toLocaleString('ru-RU'),
                    data: JSON.parse(JSON.stringify(treeData)),
                    personsCount: Object.keys(treeData.persons || {}).length,
                    size: JSON.stringify(treeData).length
                };
                localStorage.setItem(BACKUP_KEY, JSON.stringify([backup]));
                console.log('[BACKUP] Saved single backup after cleanup');
                return true;
            } catch (e2) {
                console.error('[BACKUP] Still cannot save:', e2);
                showStatusMessage('⚠️ Превышена квота хранилища');
                return false;
            }
        }
        
        console.error('[BACKUP] Error:', e);
        return false;
    }
}

/**
 * Показывает диалог управления бэкапами
 */
function showBackupManager() {
    const backups = JSON.parse(localStorage.getItem(BACKUP_KEY) || '[]');
    
    const overlay = document.createElement('div');
    overlay.className = 'tree-modal-overlay';
    overlay.innerHTML = `
        <div class="tree-modal" style="max-width: 800px; max-height: 80vh; overflow-y: auto;">
            <h3>📦 Резервные копии</h3>
            <p style="color: #64748b; font-size: 14px; margin-bottom: 16px;">
                Хранится последних ${backups.length} из ${MAX_BACKUPS} бэкапов
            </p>
            ${backups.length === 0 ? `
                <p style="text-align: center; color: #94a3b8; padding: 40px;">
                    Нет сохранённых бэкапов
                </p>
            ` : `
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    ${backups.map((b, i) => `
                        <div style="
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                            padding: 12px 16px;
                            background: ${i === backups.length - 1 ? '#f0fdf4' : '#f8fafc'};
                            border: 1px solid ${i === backups.length - 1 ? '#22c55e' : '#e2e8f0'};
                            border-radius: 8px;
                        ">
                            <div style="flex: 1;">
                                <div style="font-weight: 600; color: #1e293b;">
                                    ${i === backups.length - 1 ? '✅ ' : '📦 '} ${b.date}
                                </div>
                                <div style="font-size: 13px; color: #64748b;">
                                    Персон: ${b.personsCount} | Размер: ${(b.size / 1024).toFixed(1)} KB
                                </div>
                            </div>
                            <div style="display: flex; gap: 8px;">
                                <button onclick="restoreBackup(${i})" class="btn-primary" style="padding: 6px 12px;">
                                    Восстановить
                                </button>
                                <button onclick="downloadBackup(${i})" class="btn-secondary" style="padding: 6px 12px;">
                                    Скачать
                                </button>
                                <button onclick="deleteBackup(${i})" class="btn-danger" style="padding: 6px 12px;">
                                    Удалить
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `}
            <div style="margin-top: 20px; display: flex; gap: 12px; justify-content: flex-end;">
                <button onclick="this.closest('.tree-modal-overlay').remove()" class="btn-secondary">
                    Закрыть
                </button>
                ${backups.length > 0 ? `
                    <button onclick="clearAllBackups()" class="btn-danger">
                        Удалить все
                    </button>
                ` : ''}
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    overlay.querySelector('.tree-modal-overlay').onclick = (e) => {
        if (e.target === overlay) overlay.remove();
    };
}

/**
 * Восстанавливает бэкап по индексу
 */
function restoreBackup(index) {
    const backups = JSON.parse(localStorage.getItem(BACKUP_KEY) || '[]');
    if (index < 0 || index >= backups.length) return;
    
    if (!confirm(`Восстановить дерево из бэкапа ${backups[index].date}?\\n\\nТекущие данные будут заменены.`)) {
        return;
    }
    
    treeData = JSON.parse(JSON.stringify(backups[index].data));
    treeData._username = localStorage.getItem('family_tree_username') || 'unknown';
    
    saveTree();
    render();
    
    alert('✅ Дерево восстановлено!');
    document.querySelectorAll('.tree-modal-overlay').forEach(el => el.remove());
}

/**
 * Скачивает бэкап как JSON файл
 */
function downloadBackup(index) {
    const backups = JSON.parse(localStorage.getItem(BACKUP_KEY) || '[]');
    if (index < 0 || index >= backups.length) return;
    
    const backup = backups[index];
    const dataStr = JSON.stringify(backup.data, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `family_tree_backup_${new Date(backup.timestamp).toISOString().slice(0,10)}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
}

/**
 * Удаляет бэкап по индексу
 */
function deleteBackup(index) {
    const backups = JSON.parse(localStorage.getItem(BACKUP_KEY) || '[]');
    if (index < 0 || index >= backups.length) return;
    
    if (!confirm(`Удалить бэкап ${backups[index].date}?`)) return;
    
    backups.splice(index, 1);
    localStorage.setItem(BACKUP_KEY, JSON.stringify(backups));
    
    showBackupManager();
}

/**
 * Удаляет все бэкапы
 */
function clearAllBackups() {
    if (!confirm('Удалить ВСЕ резервные копии?')) return;
    
    localStorage.removeItem(BACKUP_KEY);
    showBackupManager();
}

/**
 * Запускает автосохранение
 */
function startAutoSave() {
    if (autoSaveTimer) clearInterval(autoSaveTimer);
    
    autoSaveTimer = setInterval(() => {
        if (hasUnsavedChanges()) {
            console.log('[AUTO_SAVE] Saving...');
            saveTree();
            showStatusMessage('Автосохранение выполнено');
        }
    }, AUTO_SAVE_INTERVAL);
    
    console.log('[AUTO_SAVE] Started (5 min interval)');
}

/**
 * Показывает сообщение в статус-баре
 */
function showStatusMessage(msg) {
    const statusEl = document.getElementById('status-msg');
    if (statusEl) {
        statusEl.textContent = msg;
        setTimeout(() => { statusEl.textContent = ''; }, 3000);
    }
}

/**
 * Настраивает горячие клавиши
 */
function setupHotkeys() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+S — Сохранить
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            saveTree(true);
            showStatusMessage('✅ Сохранено');
        }
        
        // Ctrl+Z — Отменить
        if (e.ctrlKey && e.key === 'z') {
            e.preventDefault();
            if (window.undoManager && window.undoManager.undo()) {
                showStatusMessage('Отменено');
            }
        }
        
        // Ctrl+Y — Повторить
        if (e.ctrlKey && e.key === 'y') {
            e.preventDefault();
            if (window.undoManager && window.undoManager.redo()) {
                showStatusMessage('Повторено');
            }
        }
        
        // Ctrl+F — Режим фокуса
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            toggleFocusMode();
            showStatusMessage(`Фокус: ${focusModeActive ? 'вкл' : 'выкл'}`);
        }
        
        // Ctrl+T — Временная шкала
        if (e.ctrlKey && e.key === 't') {
            e.preventDefault();
            openTimeline();
        }
        
        // Delete — Удалить персону (если выбрана)
        if (e.key === 'Delete' && !e.ctrlKey && !e.altKey) {
            const selectedCard = document.querySelector('.tree-card.selected');
            if (selectedCard) {
                const pid = selectedCard.getAttribute('data-pid');
                if (pid) deletePerson(pid);
            }
        }
    });
    
    console.log('[HOTKEYS] Setup complete: Ctrl+S, Z, Y, F, T, Delete');
}

/**
 * Переключает режим фокуса (показывает только предков/потомков)
 */
function toggleFocusMode() {
    focusModeActive = !focusModeActive;
    render();
}

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

    // === БЕЗОПАСНОСТЬ: Проверяем, что localStorage принадлежит текущему пользователю ===
    const currentUsername = localStorage.getItem('family_tree_username') || '';
    console.log('[LOAD_TREE] Current username from storage:', currentUsername);

    // Загружаем backup из localStorage (локальная версия)
    let backup = localStorage.getItem('family_tree_backup');
    let localData = null;

    // Если backup есть, проверяем, что он принадлежит текущему пользователю
    if (backup) {
        try {
            const parsed = JSON.parse(backup);
            const backupUsername = parsed._username || '';

            // Если пользователь сменился — НЕ используем старый backup!
            if (backupUsername && backupUsername !== currentUsername) {
                console.log('[LOAD_TREE] SECURITY: Backup belongs to different user!', backupUsername, '!=', currentUsername);
                console.log('[LOAD_TREE] Clearing old backup');
                localStorage.removeItem('family_tree_backup');
                localStorage.removeItem('family_tree_username');
                backup = null;
                localData = null;
            } else if (parsed.persons && Object.keys(parsed.persons).length > 0) {
                localData = parsed;
                console.log('[LOAD_TREE] Local backup:', Object.keys(localData.persons).length, 'persons');
            }
        } catch (e) {
            console.warn('[LOAD_TREE] Backup parse error:', e);
            localData = null;
        }
    }

    // Загружаем данные с сервера
    const r = await fetch("/api/tree");
    console.log('[LOAD_TREE] Fetch response status:', r.status);
    if (r.status === 401) {
        console.log('[LOAD_TREE] 401 Unauthorized, redirecting to login');
        window.location.href = "/login";
        return;
    }
    if (!r.ok) {
        console.error('[LOAD_TREE] Response not ok:', r.status);
        // Если сервер не ответил, используем локальные данные
        if (normalizedLocalData) {
            console.log('[LOAD_TREE] Using local data (server error)');
            treeData = normalizedLocalData;
            centerId = treeData.current_center || (Object.keys(treeData.persons)[0] || null);
            treeZoom = 0.5;
            treePanX = 0;
            treePanY = 0;
            render();
        }
        return;
    }

    const serverData = await r.json();
    
    // === ОТЛАДКА: покажем, что пришёл с сервера ===
    console.log('[LOAD_TREE] Raw serverData marriages:', serverData.marriages);
    console.log('[LOAD_TREE] Raw serverData marriages type:', Array.isArray(serverData.marriages) ? 'Array' : typeof serverData.marriages);
    
    // === НОРМАЛИЗАЦИЯ ДАННЫХ ===
    // Преобразуем все ID в строки для консистентности
    const normalizePerson = (p) => {
        if (!p) return p;
        return {
            ...p,
            id: String(p.id),
            parents: (p.parents || []).map(String),
            children: (p.children || []).map(String),
            spouse_ids: (p.spouse_ids || []).map(String),
        };
    };
    
    const normalizeMarriage = (m) => {
        if (Array.isArray(m)) {
            return m.map(String);
        } else if (m && m.persons && Array.isArray(m.persons)) {
            return { persons: m.persons.map(String) };
        }
        return m;
    };
    
    // Нормализуем данные с сервера
    const normalizedServerData = {
        persons: {},
        marriages: (serverData.marriages || []).map(normalizeMarriage),
        current_center: serverData.current_center,
    };
    Object.entries(serverData.persons || {}).forEach(([id, p]) => {
        normalizedServerData.persons[String(id)] = normalizePerson(p);
    });
    
    // Нормализуем локальные данные
    let normalizedLocalData = null;
    if (localData) {
        normalizedLocalData = {
            persons: {},
            marriages: (localData.marriages || []).map(normalizeMarriage),
            current_center: localData.current_center,
        };
        Object.entries(localData.persons || {}).forEach(([id, p]) => {
            normalizedLocalData.persons[String(id)] = normalizePerson(p);
        });
    }
    
    const serverPersonsCount = Object.keys(normalizedServerData.persons || {}).length;
    const localPersonsCount = normalizedLocalData ? Object.keys(normalizedLocalData.persons || {}).length : 0;

    console.log('[LOAD_TREE] Server:', serverPersonsCount, 'persons, Local:', localPersonsCount, 'persons');

    // === БЕЗОПАСНОСТЬ: Сохраняем имя пользователя в localStorage ===
    // Получаем имя текущего пользователя (из login.html или session)
    const username = localStorage.getItem('family_tree_username') || currentUsername;
    if (!username) {
        // Пытаемся получить username из страницы (если есть)
        const usernameMeta = document.querySelector('meta[name="username"]');
        if (usernameMeta) {
            localStorage.setItem('family_tree_username', usernameMeta.content);
        }
    }

    // === ЛОГИКА СИНХРОНИЗАЦИИ ===

    // 1. Если сервер пустой, а локально есть данные - НЕ перезаписываем локальные!
    if (serverPersonsCount === 0 && localPersonsCount > 0) {
        console.log('[SYNC] Server empty, KEEPING local data (DO NOT OVERWRITE)');
        treeData = normalizedLocalData;
        // Сохраняем обратно в localStorage чтобы не потерять
        treeData._username = username;
        localStorage.setItem('family_tree_backup', JSON.stringify(treeData));
    }
    // 2. Если локально пусто, а сервер вернул данные - используем сервер
    else if (serverPersonsCount > 0 && localPersonsCount === 0) {
        console.log('[SYNC] Local empty, using server data');
        treeData = normalizedServerData;
        // Сохраняем в localStorage
        treeData._username = username;
        localStorage.setItem('family_tree_backup', JSON.stringify(treeData));
    }
    // 3. Если есть и там и там - БЕРЁМ БОЛЬШЕЕ из двух
    else if (serverPersonsCount > 0 && localPersonsCount > 0) {
        console.log('[SYNC] Both have data, using LARGER dataset...');

        // Выбираем где больше персон
        if (localPersonsCount > serverPersonsCount) {
            console.log('[SYNC] Local has more persons, using local data');
            treeData = normalizedLocalData;
        } else {
            console.log('[SYNC] Server has more/equal persons, using server data');
            treeData = normalizedServerData;
        }

        // Сохраняем выбранное в localStorage
        treeData._username = username;
        localStorage.setItem('family_tree_backup', JSON.stringify(treeData));
    }
    // 4. Если оба пустые - оставляем как есть
    else {
        console.log('[SYNC] Both empty');
        treeData = {persons: {}, marriages: [], current_center: null};
        treeData._username = username;
    }

    // === СИНХРОНИЗАЦИЯ spouse_ids И marriages (как в desktop models.py) ===
    // Восстанавливаем spouse_ids из marriages
    console.log('[SYNC] Synchronizing spouse_ids with marriages...');
    const marriages = treeData.marriages || [];
    
    // Очищаем spouse_ids у всех персон
    Object.values(treeData.persons).forEach(p => {
        if (p) p.spouse_ids = [];
    });
    
    // Восстанавливаем spouse_ids из marriages
    let restoredCount = 0;
    marriages.forEach(m => {
        let a, b;
        if (Array.isArray(m)) {
            [a, b] = m;
        } else if (m.persons && Array.isArray(m.persons)) {
            [a, b] = m.persons;
        } else {
            return;
        }
        
        const idA = String(a), idB = String(b);
        const pA = treeData.persons[idA];
        const pB = treeData.persons[idB];
        
        if (pA && pB) {
            if (!pA.spouse_ids.includes(idB)) pA.spouse_ids.push(idB);
            if (!pB.spouse_ids.includes(idA)) pB.spouse_ids.push(idA);
            restoredCount++;
        }
    });
    
    console.log('[SYNC] Restored', restoredCount, 'spouse relationships from marriages');
    
    // === ИСПРАВЛЕНИЕ: восстанавливаем marriages из spouse_ids, если marriages пуст ===
    if (marriages.length === 0 && Object.keys(treeData.persons).length > 0) {
        console.log('[SYNC] Marriages empty, restoring from spouse_ids...');
        const marriageSet = new Set();
        
        Object.entries(treeData.persons).forEach(([id, p]) => {
            if (p && p.spouse_ids) {
                p.spouse_ids.forEach(spouseId => {
                    const pair = [id, spouseId].sort();
                    marriageSet.add(pair.join('|'));
                });
            }
        });
        
        treeData.marriages = Array.from(marriageSet).map(pairStr => {
            const [a, b] = pairStr.split('|');
            return [a, b];
        });
        
        console.log('[SYNC] Restored', treeData.marriages.length, 'marriages from spouse_ids');
    }
    // === КОНЕЦ СИНХРОНИЗАЦИИ ===

    // Сохраняем объединённые данные в backup
    treeData._username = username;
    localStorage.setItem('family_tree_backup', JSON.stringify(treeData));

    centerId = treeData.current_center || (Object.keys(treeData.persons)[0] || null);
    console.log('[LOAD_TREE] centerId:', centerId, 'total persons:', Object.keys(treeData.persons).length);

    // ✅ Устанавливаем флаг загрузки
    treeLoaded = true;

    // Сбрасываем зум и панорамирование при загрузке
    treeZoom = 0.5;
    treePanX = 0;
    treePanY = 0;

    render();

    // ✅ ПРОВЕРКА ПЕРВОГО ЗАПУСКА (после загрузки!)
    checkFirstRun();

    // Центрируем дерево после рендеринга (БЕЗ сохранения!)
    setTimeout(() => {
        if (centerId && treeData._coords && treeData._coords[centerId]) {
            // Используем координаты из render()
            const pos = treeData._coords[centerId];
            if (pos && pos.x !== undefined && pos.y !== undefined) {
                treePanX = -pos.x * treeZoom + window.innerWidth / 2;
                treePanY = -pos.y * treeZoom + window.innerHeight / 2;
                render();
            }
        }
    }, 100);
}

// Принудительная перезагрузка дерева с сервера (после удаления)
async function loadTreeFromServer() {
    console.log('[LOAD_TREE_FROM_SERVER] Reloading tree from server...');
    try {
        const r = await fetch("/api/tree");
        if (r.ok) {
            const serverData = await r.json();
            treeData = serverData;
            centerId = treeData.current_center || (Object.keys(treeData.persons)[0] || null);
            
            // Сбрасываем зум и панорамирование
            treeZoom = 0.5;
            treePanX = 0;
            treePanY = 0;
            
            console.log('[LOAD_TREE_FROM_SERVER] Loaded', Object.keys(treeData.persons).length, 'persons');
            render();
            return true;
        }
    } catch (e) {
        console.error('[LOAD_TREE_FROM_SERVER] Error:', e);
    }
    return false;
}

function render() {
    const root = document.getElementById("tree-root");
    const emptyMsg = document.getElementById("empty-msg");
    root.innerHTML = "";

    const persons = treeData.persons || {};
    const ids = Object.keys(persons);

    console.log('[RENDER] persons count:', ids.length, 'treeLoaded:', treeLoaded);

    // === ПРОВЕРКА: Дерево загружено? ===
    // Если treeLoaded=false, ждём загрузки (не показываем empty-msg)
    if (!treeLoaded && ids.length === 0) {
        console.log('[RENDER] Tree not loaded yet, waiting...');
        return;  // Просто выходим, не показывая empty-msg
    }
    
    // Если persons пустой, но treeLoaded=true - показываем пустое сообщение
    if (ids.length === 0) {
        console.log('[RENDER] No persons, showing empty message');
        emptyMsg.style.display = "block";
        const btn = document.getElementById("btn-add-first");
        if (btn) btn.onclick = (e) => {
            e.stopPropagation();
            closeContextMenu();
            addFirstPerson();
        };
        updateStatusBar();
        return;
    }
    
    console.log('[RENDER] Rendering tree with', ids.length, 'persons');
    emptyMsg.style.display = "none";

    // === ИСПОЛЬЗУЕМ ФУНКЦИЮ ИЗ visible_persons.js (полная копия desktop-версии) ===
    const relatedRaw = getVisiblePersons(centerId, persons, treeData.marriages, focusModeActive, activeFilters);
    console.log('[RENDER] Visible persons:', relatedRaw.size);
    console.log('[RENDER] Render mode:', renderMode);

    // Применяем фильтры к visible persons
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

    // === ВЫБИРАЕМ АЛГОРИТМ ОТРИСОВКИ ===
    // ФИНАЛЬНАЯ ВЕРСИЯ: простое размещение по поколениям
    let layoutResult;

    console.log('[RENDER] Using FINAL layout...');
    layoutResult = renderFinalLayout(centerId, persons, treeData.marriages, related);
    
    const { coords, bounds, totalW, totalH, offsetX, offsetY } = layoutResult;

    // ✅ Сохраняем координаты и bounds для setCenterAndSave
    treeData._coords = coords;
    treeData._bounds = bounds;

    // Создаём структуру для дерева
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

    // Вешаем события
    setupPan(wrap, panZoomWrapper);
    setupZoom(panZoomWrapper, zoomContainer, wrap, totalW, totalH);

    // Рассчитываем степень родства для всех персон
    const kinship = calculateKinship();

    // Сначала рисуем карточки
    Object.entries(coords).forEach(([pid, pos]) => {
        const p = persons[pid];
        if (!p) return;
        const card = document.createElement("div");
        card.className = "tree-card";
        card.setAttribute("data-pid", pid);  // ✅ Добавляем data-pid для поиска
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
        const kinshipText = kinship[pid] || "";

        const photoHtml = photoSrc
            ? `<div class="card-photo" onclick="event.stopPropagation(); openPhotoModal('${pid}', '${escapeHtml(name)}')" title="Нажмите чтобы загрузить фото"><img src="${photoSrc}" alt="" loading="lazy" onerror="this.parentElement.classList.add('no-photo')"><span class="photo-placeholder">📷</span></div>`
            : `<div class="card-photo no-photo" onclick="event.stopPropagation(); openPhotoModal('${pid}', '${escapeHtml(name)}')" title="Нажмите чтобы добавить фото"><span class="photo-placeholder">📷</span></div>`;

        card.innerHTML = photoHtml + `<div class="card-info">
            <div class="name">${escapeHtml(name)}</div>
            <div class="dates">${escapeHtml(dates)}</div>
            ${kinshipText ? `<div class="kinship">${escapeHtml(kinshipText)}</div>` : ''}
        </div>`;

        card.style.left = (pos.x + offsetX - CARD_W / 2) + "px";
        card.style.top = (pos.y + offsetY - CARD_H / 2) + "px";

        // Клик по карточке — разное поведение для десктопа и мобильного
        card.onclick = (e) => {
            if (window._treeDidPan) return;
            if (card._longPressFired) return;
            
            // На мобильном — контекстное меню
            if (window.innerWidth <= 480) {
                const rect = card.getBoundingClientRect();
                showContextMenu(pid, rect.left + rect.width / 2, rect.top + rect.height / 2, persons);
            } 
            // На десктопе — сделать центром
            else {
                setCenterAndSave(pid);
            }
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
        
        // Обработка touchstart
        const handleTouchStart = (e) => {
            console.log('[CARD] touchstart on', pid, 'touches:', e.touches.length, 'target:', e.target.className);
            // Реагируем ТОЛЬКО на один палец
            if (e.touches.length !== 1) {
                console.log('[LONG_PRESS] Cancelled: touches=', e.touches.length);
                clearTimeout(longPressTimer);
                return;
            }
            card._longPressFired = false;
            const tx = e.touches[0].clientX, ty = e.touches[0].clientY;
            touchStartX = tx;
            touchStartY = ty;
            touchStartTime = Date.now();
            hasMoved = false;
            
            console.log('[LONG_PRESS] Touch start at', tx, ty, 'time:', touchStartTime);
            
            longPressTimer = setTimeout(() => {
                const touchDuration = Date.now() - touchStartTime;
                console.log('[LONG_PRESS] Timer fired: duration=', touchDuration, 'moved=', hasMoved, 'pan=', window._treeDidPan);
                
                // Проверяем, что палец не двигался и не было панорамирования
                if (hasMoved || window._treeDidPan || touchDuration < 900) {
                    console.log('[LONG_PRESS] Cancelled: moved=', hasMoved, 'pan=', window._treeDidPan, 'duration=', touchDuration);
                    return;
                }
                
                card._longPressFired = true;
                console.log('[LONG_PRESS] Triggered! Showing menu for', pid);
                // Показываем меню с вибрацией (если поддерживается)
                if (navigator.vibrate) navigator.vibrate(50);
                showContextMenu(pid, tx, ty, persons);
            }, 1000); // 1 секунда для долгого тапа
        };
        
        // Обработка touchmove
        const handleTouchMove = (e) => {
            // Если пальцев больше одного - сбрасываем
            if (e.touches.length !== 1) {
                hasMoved = true;
                clearTimeout(longPressTimer);
                console.log('[LONG_PRESS] Cancelled: multi-touch');
                return;
            }
            
            const touch = e.touches[0];
            const moveDistance = Math.hypot(touch.clientX - touchStartX, touch.clientY - touchStartY);
            if (moveDistance > 10) { // Если палец сдвинулся больше чем на 10px
                hasMoved = true;
                clearTimeout(longPressTimer);
                console.log('[LONG_PRESS] Cancelled: moved', moveDistance.toFixed(1), 'px');
            }
        };
        
        // Обработка touchend
        const handleTouchEnd = (e) => {
            console.log('[CARD] touchend on', pid);
            clearTimeout(longPressTimer);
            // Предотвращаем клик если был долгий тап
            if (card._longPressFired && e.cancelable) {
                e.preventDefault();
            }
        };
        
        // Обработка touchcancel
        const handleTouchCancel = () => {
            console.log('[CARD] touchcancel on', pid);
            clearTimeout(longPressTimer);
        };
        
        // Вешаем события с разными вариантами для совместимости
        card.addEventListener("touchstart", handleTouchStart, { passive: true });
        card.addEventListener("touchmove", handleTouchMove, { passive: true });
        card.addEventListener("touchend", handleTouchEnd);
        card.addEventListener("touchcancel", handleTouchCancel);
        
        // Для старых браузеров пробуем также pointer events
        if (window.PointerEvent) {
            let pointerDownTime = 0;
            let pointerDownX = 0, pointerDownY = 0;
            
            card.addEventListener("pointerdown", (e) => {
                if (e.pointerType !== 'touch') return;
                pointerDownTime = Date.now();
                pointerDownX = e.clientX;
                pointerDownY = e.clientY;
                console.log('[POINTER] pointerdown at', pointerDownX, pointerDownY);
            });
            
            card.addEventListener("pointerup", (e) => {
                if (e.pointerType !== 'touch') return;
                const duration = Date.now() - pointerDownTime;
                const moveDistance = Math.hypot(e.clientX - pointerDownX, e.clientY - pointerDownY);
                console.log('[POINTER] pointerup duration=', duration, 'move=', moveDistance);
                
                // Долгое нажатие без движения
                if (duration > 900 && moveDistance < 10 && !card._longPressFired) {
                    console.log('[POINTER] Long press detected!');
                    if (navigator.vibrate) navigator.vibrate(50);
                    showContextMenu(pid, pointerDownX, pointerDownY, persons);
                }
            });
        }
        
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
    svg.style.cssText = "position:absolute; top:0; left:0; pointer-events:none; z-index:100 !important;";
    svg.setAttribute("class", "tree-lines");
    wrap.appendChild(svg);

    // Отладка: проверяем marriages и связи

    // Отладка: проверяем связи родителей для каждой персоны
    Object.keys(coords).forEach(pid => {
        const p = persons[pid];
        if (p && p.parents) {
            console.log(`  ${pid} (${p.name}) parents:`, p.parents);
        }
    });

    // === 1. СНАЧАЛА ЛИНИИ СУПРУГОВ (чтобы линии родителей соединялись с ними) ===
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

        // Проверяем, что обе персоны имеют координаты (значит они отрисованы)
        if (!coords[idA] || !coords[idB]) {
            console.log('[MARRIAGE] Skipping - no coords for', idA, idB);
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

        // === ИСПОЛЬЗУЕМ ЦВЕТ ИЗ ПАЛИТРЫ (как в desktop) ===
        const marriageLineColor = getComputedStyle(document.documentElement)
            .getPropertyValue('--line-marriage').trim() || '#b45309';

        line.setAttribute("x1", xLeftEdge);
        line.setAttribute("y1", yCenter);
        line.setAttribute("x2", xRightEdge);
        line.setAttribute("y2", yCenter);
        line.setAttribute("stroke", marriageLineColor);
        line.setAttribute("stroke-width", 2);
        line.setAttribute("stroke-dasharray", "4 4");
        line.setAttribute("stroke-linecap", "round");
        svg.appendChild(line);
        marriageLinesDrawn++;
    });
    console.log('[MARRIAGE] Total marriage lines drawn:', marriageLinesDrawn);

    // === 2. ЛИНИИ РОДИТЕЛЕЙ (рисуются поверх линий супругов) ===
    const parentSetToChildren = {};
    Object.keys(coords).forEach(pid => {
        const p = persons[pid];
        if (!p || !p.parents) return;
        // Фильтруем только ВИДИМЫХ родителей (у которых есть coords)
        const visibleParents = (p.parents || []).filter(pid2 => coords[pid2] && related.has(pid2));
        if (!visibleParents.length) {
            console.log(`[DEBUG] ${pid} (${p.name}) has no visible parents, skipping line`);
            return;
        }
        const key = visibleParents.map(String).sort().join("|");
        parentSetToChildren[key] = parentSetToChildren[key] || [];
        parentSetToChildren[key].push(pid);
    });
    
    Object.entries(parentSetToChildren).forEach(([key, children]) => {
        console.log(`  Parents [${key}] → Children:`, children);
    });
    
    const childTopOffset = CARD_H / 2;

    Object.entries(parentSetToChildren).forEach(([parentKey, childPids]) => {
        const first = persons[childPids[0]];
        if (!first || !first.parents) return;
        
        // Получаем родителей ПЕРВОГО ребёнка (они должны быть одинаковыми для всех в группе)
        let parentPids = (first.parents || []).filter(pid => coords[pid]);
        if (!parentPids.length) return;

        // === ПРОВЕРКА: У всех детей в группе должны быть те же родители ===
        // Если нет — разделяем на подгруппы по родителям
        const childrenByParents = {};
        childPids.forEach(cid => {
            const child = persons[cid];
            const childParents = (child.parents || [])
                .filter(pid => coords[pid] && related.has(pid))
                .map(String)
                .sort()
                .join('|');
            
            if (!childrenByParents[childParents]) {
                childrenByParents[childParents] = [];
            }
            childrenByParents[childParents].push(cid);
        });

        // Обрабатываем каждую подгруппу отдельно
        Object.values(childrenByParents).forEach(subGroupChildPids => {
            const subFirst = persons[subGroupChildPids[0]];
            parentPids = (subFirst.parents || []).filter(pid => coords[pid]);
            if (!parentPids.length) return;

            console.log(`[DEBUG] Drawing parent line for parents:`, parentPids, 'children:', subGroupChildPids);

            // === НАХОДИМ СЕРЕДИНУ МЕЖДУ РОДИТЕЛЯМИ ===
            let parentCenterX, parentY, spouseLineY;
            if (parentPids.length >= 2) {
                const p1 = coords[parentPids[0]], p2 = coords[parentPids[1]];
                parentCenterX = (p1.x + p2.x) / 2;  // СЕРЕДИНА между родителями по X
                parentY = p1.y;  // Оба на одном уровне Y

                // === ЛИНИЯ СУПРУГОВ (между ними) ===
                const p1RightEdge = p1.x + CARD_W / 2;
                const p2LeftEdge = p2.x - CARD_W / 2;
                const spouseLineMidX = (p1RightEdge + p2LeftEdge) / 2;
                spouseLineY = p1.y;  // На том же уровне что и супруги

                console.log(`[DEBUG] Two parents: p1=(${p1.x},${p1.y}), p2=(${p2.x},${p2.y}), center=${parentCenterX}`);
            } else {
                parentCenterX = coords[parentPids[0]].x;
                parentY = coords[parentPids[0]].y;
                spouseLineY = parentY;
                console.log(`[DEBUG] Single parent: (${parentCenterX},${parentY})`);
            }

            const childrenCoords = subGroupChildPids
                .filter(cid => coords[cid])
                .map(cid => {
                    const c = coords[cid];
                    return { cx: c.x, cy: c.y, topY: c.y - childTopOffset };
                })
                .sort((a, b) => a.cx - b.cx);
            if (!childrenCoords.length) return;
            const minTopY = Math.min(...childrenCoords.map(t => t.topY));

            // Горизонтальная линия НА УРОВНЕ детей (над ними)
            const horizLineY = (parentY + CARD_H/2 + minTopY) / 2;  // Посередине между родителями и детьми

            console.log(`[DEBUG] horizLineY=${horizLineY}, parentY=${parentY}, minTopY=${minTopY}`);

            // === ОТРИСОВКА ЛИНИЙ РОДИТЕЛЕЙ ===
            const parentLineColor = getComputedStyle(document.documentElement)
                .getPropertyValue('--line-parent').trim() || '#475569';

            // Вертикальная линия ОТ ЛИНИИ СУПРУГОВ (не от нижнего края!)
            // spouseLineY — это Y-координата линии между супругами (на уровне центра карточек)
            const midVertLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
            midVertLine.setAttribute("x1", (parentCenterX + offsetX));
            midVertLine.setAttribute("y1", (spouseLineY + offsetY));  // ✅ ОТ линии супругов
            midVertLine.setAttribute("x2", (parentCenterX + offsetX));
            midVertLine.setAttribute("y2", (horizLineY + offsetY));
            midVertLine.setAttribute("stroke", parentLineColor);
            midVertLine.setAttribute("stroke-width", 2);
            midVertLine.setAttribute("stroke-linecap", "round");
            svg.appendChild(midVertLine);

            // Горизонтальная линия над всеми детьми
            const minX = childrenCoords[0].cx;
            const maxX = childrenCoords[childrenCoords.length - 1].cx;
            const horizLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
            horizLine.setAttribute("x1", (minX + offsetX));
            horizLine.setAttribute("y1", (horizLineY + offsetY));
            horizLine.setAttribute("x2", (maxX + offsetX));
            horizLine.setAttribute("y2", (horizLineY + offsetY));
            horizLine.setAttribute("stroke", parentLineColor);
            horizLine.setAttribute("stroke-width", 2);
            horizLine.setAttribute("stroke-linecap", "round");
            svg.appendChild(horizLine);

            // Вертикальные линии к каждому ребёнку
            childrenCoords.forEach(({ cx, topY }) => {
                const childLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
                childLine.setAttribute("x1", (cx + offsetX));
                childLine.setAttribute("y1", (horizLineY + offsetY));
                childLine.setAttribute("x2", (cx + offsetX));
                childLine.setAttribute("y2", (topY + offsetY));
                childLine.setAttribute("stroke", parentLineColor);
                childLine.setAttribute("stroke-width", 2);
                childLine.setAttribute("stroke-linecap", "round");
                svg.appendChild(childLine);
            });
        }); // Конец обработки подгруппы
    }); // Конец обработки группы

    updateStatusBar();
}

/**
 * КЛАССИЧЕСКИЙ АЛГОРИТМ ОТРИСОВКИ (синхронизирован с desktop-версией)
 * Использует ДВУХПРОХОДНЫЙ алгоритм как в desktop (Дерево/app.py:calculate_layout)
 * 
 * Проход 1: Размещение от centerId вниз (дети, внуки)
 * Проход 2: Доразмещение родителей выше и супругов рядом
 */
function runClassicLayout(centerId, persons, marriages, related) {
    const coords = {};
    const spouseStep = CARD_W + SPOUSE_GAP;

    // === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
    
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

    // === ПРОХОД 1: РАЗМЕЩЕНИЕ ОТ CENTERId ВНИЗ ===
    // Используем множество для отслеживания УЖЕ размещённых персон
    const placed = new Set();
    
    function placeSubtree(pid, placeX, yPos, allocatedWidth) {
        if (!pid || !persons[pid]) {
            return { left: placeX, right: placeX + CARD_W };
        }
        const p = persons[pid];

        // Если уже размещён — НЕ ТРОГАЕМ, возвращаем его текущие границы
        if (placed.has(pid)) {
            return { left: coords[pid].x - CARD_W/2, right: coords[pid].x + CARD_W/2, top: coords[pid].y - CARD_H/2, bottom: coords[pid].y + CARD_H/2 };
        }

        const spouses = (p.spouse_ids || []).filter(s => related.has(s) && persons[s]);
        const blockWidth = blockWidthOnly(p);
        const actualWidth = Math.max(allocatedWidth, blockWidth);
        const blockX = placeX + (actualWidth - blockWidth) / 2;

        // === ПОЗИЦИОНИРОВАНИЕ ПЕРСОНЫ И СУПРУГОВ ===
        // Сортируем: муж слева, жена справа
        const allInBlock = [pid, ...spouses].sort((a, b) => {
            const ga = (persons[a] || {}).gender === "Мужской" ? 0 : 1;
            const gb = (persons[b] || {}).gender === "Мужской" ? 0 : 1;
            return ga - gb;
        });

        let dx = blockX;
        allInBlock.forEach(id => {
            if (!placed.has(id)) {
                coords[id] = { x: dx + CARD_W / 2, y: yPos + CARD_H / 2 };
                placed.add(id);
            }
            dx += spouseStep;
        });

        // === ПОЗИЦИОНИРОВАНИЕ РОДИТЕЛЕЙ (выше) ===
        // Размещаем родителей выше текущей персоны
        const visibleParents = (p.parents || []).filter(pr => related.has(pr) && persons[pr]);
        if (visibleParents.length > 0) {
            const parentY = yPos - LEVEL_HEIGHT;
            const parentWidths = visibleParents.map(pr => Math.max(getSubtreeWidth(pr), blockWidthOnly(persons[pr])));
            let totalParentW = parentWidths.reduce((a, b) => a + b, 0);
            for (let i = 0; i < visibleParents.length - 1; i++) {
                totalParentW += gapBetweenSiblings(visibleParents[i], visibleParents[i + 1]);
            }

            // Центрируем родителей относительно текущего блока
            const parentCenterX = blockX + blockWidth / 2;
            let parentX = parentCenterX - totalParentW / 2;

            visibleParents.forEach((pr, i) => {
                // Если родитель ещё не размещён — размещаем
                if (!placed.has(pr)) {
                    const pw = parentWidths[i];
                    placeSubtree(pr, parentX, parentY, pw);
                }
                // Сдвигаем parentX для следующего родителя
                parentX += parentWidths[i];
                if (i < visibleParents.length - 1) {
                    parentX += gapBetweenSiblings(visibleParents[i], visibleParents[i + 1]);
                }
            });
        }

        // === ПОЗИЦИОНИРОВАНИЕ СУПРУГОВ (рядом) ===
        // Супруги должны быть размещены ВМЕСТЕ с основной персоной в одном блоке
        spouses.forEach((spouseId, idx) => {
            if (!placed.has(spouseId)) {
                // Размещаем супруга справа от последнего в блоке
                const spouseX = blockX + (idx + 1) * spouseStep;
                coords[spouseId] = {
                    x: spouseX + CARD_W / 2,
                    y: yPos + CARD_H / 2
                };
                placed.add(spouseId);
            }
        });

        // === ПОЗИЦИОНИРОВАНИЕ ДЕТЕЙ (ниже) ===
        const kids = p.collapsed_branches ? [] : sortChildren((p.children || []).filter(c => related.has(c) && persons[c]));
        
        if (kids.length === 0) {
            return { left: blockX, right: blockX + blockWidth, top: yPos, bottom: yPos + CARD_H };
        }

        const childY = yPos + LEVEL_HEIGHT;
        
        // Вычисляем центр между родителями для центрирования детей
        let parentCenterX = blockX + blockWidth / 2;
        if (visibleParents.length > 0) {
            const parentKeys = visibleParents.filter(pr => coords[pr]);
            if (parentKeys.length > 0) {
                const sumX = parentKeys.reduce((sum, pr) => sum + coords[pr].x, 0);
                parentCenterX = sumX / parentKeys.length;
            }
        }

        const childWidths = kids.map(k => Math.max(getSubtreeWidth(k), blockWidthOnly(persons[k])));
        let totalChildW = childWidths.reduce((a, b) => a + b, 0);
        for (let i = 0; i < kids.length - 1; i++) {
            totalChildW += gapBetweenSiblings(kids[i], kids[i + 1]);
        }

        let left = blockX, right = blockX + blockWidth, bottom = childY + CARD_H;

        if (kids.length === 1) {
            // Один ребёнок — центрируем под родителями
            const cw = childWidths[0];
            const childBw = blockWidthOnly(persons[kids[0]]);
            const childResult = placeSubtree(kids[0], parentCenterX - childBw / 2, childY, childBw);
            
            // Сдвигаем ребёнка если нужно для точного центрирования
            if (kids[0] in coords) {
                const childX = coords[kids[0]].x;
                const delta = parentCenterX - childX;
                if (Math.abs(delta) > 0.01) {
                    coords[kids[0]].x += delta;
                    // Сдвигаем также супругов ребёнка
                    const childSpouses = (persons[kids[0]].spouse_ids || []).filter(s => related.has(s) && persons[s] && coords[s]);
                    childSpouses.forEach(s => {
                        coords[s].x += delta;
                    });
                }
            }
            
            left = Math.min(left, childResult.left);
            right = Math.max(right, childResult.right);
            bottom = Math.max(bottom, childResult.bottom);
        } else {
            // Несколько детей — симметрично относительно центра
            let childX = parentCenterX - totalChildW / 2;
            kids.forEach((kid, i) => {
                const cw = childWidths[i];
                const r = placeSubtree(kid, childX, childY, cw);
                if (r) {
                    left = Math.min(left, r.left);
                    right = Math.max(right, r.right);
                    bottom = Math.max(bottom, r.bottom);
                }
                childX += cw;
                if (i < kids.length - 1) {
                    childX += gapBetweenSiblings(kids[i], kids[i + 1]);
                }
            });
        }

        return { left, right, top: yPos, bottom };
    }

    // === ИНИЦИАЛИЗАЦИЯ: НАЧИНАЕМ ОТ CENTERId ===
    const rootKey = centerId && persons[centerId] && related.has(centerId) ? centerId : (Array.from(related)[0] || Object.keys(persons)[0]);

    // === ПРЕДВАРИТЕЛЬНОЕ РАЗМЕЩЕНИЕ КОРНЕВЫХ ПРЕДКОВ ===
    // Находим корневых предков НО ТОЛЬКО тех кто в related
    // related уже отфильтрован visible_persons.js (только один родитель)
    const rootAncestors = [];
    for (const pid of related) {
        const p = persons[pid];
        if (p && (!p.parents || p.parents.length === 0)) {
            rootAncestors.push(pid);
        }
    }
    console.log('[CLASSIC] Root ancestors (no parents):', rootAncestors);
    console.log('[CLASSIC] related size:', related.size, 'persons:', Array.from(related));

    // === ИЗМЕНЕНИЕ: Не размещаем корневых предков в ряд! ===
    // Вместо этого начинаем от rootKey и позволяем алгоритму естественно разместить всех
    // Корневые предки будут размещены как родители своих детей

    if (!rootKey || !persons[rootKey]) {
        // Если нет корневой персоны — размещаем всех подряд
        let offsetX = 0;
        for (const pid of related) {
            if (persons[pid] && !coords[pid]) {
                coords[pid] = { x: offsetX + CARD_W / 2, y: CARD_H / 2 };
                offsetX += CARD_W + SIBLING_GAP;
            }
        }
    } else {
        // === ПРОХОД 1: Размещаем от корня вниз (если не размещён) ===
        if (!coords[rootKey]) {
            const canvasWidth = Math.max(800, getSubtreeWidth(rootKey));
            placeSubtree(rootKey, 0, 50, canvasWidth);
        }
    }

    // === ПРОХОД 1.5: ДОРАЗМЕЩЕНИЕ РОДИТЕЛЕЙ ===
    // Проверяем ВСЕ персоны и размещаем их родителей если они ещё не размещены
    // Также проверяем супругов - размещаем ИХ родителей тоже
    let parentsPlaced = 0;
    
    for (const pid of related) {
        const p = persons[pid];
        if (!p) continue;
        
        // Получаем список персон для проверки (сама персона + супруги)
        const personsToCheck = [pid];
        if (p.spouse_ids) {
            p.spouse_ids.forEach(sid => {
                if (related.has(sid) && persons[sid]) {
                    personsToCheck.push(sid);
                }
            });
        }
        
        // Для каждой персоны проверяем родителей
        for (const checkPid of personsToCheck) {
            const checkP = persons[checkPid];
            if (!checkP || !checkP.parents) continue;
            
            // Если у этой персоны ещё нет координат - пропускаем (будет размещена позже)
            if (!coords[checkPid]) continue;
            
            const unplacedParents = (checkP.parents || [])
                .filter(pr => related.has(pr) && persons[pr] && !coords[pr]);
            
            if (unplacedParents.length > 0) {
                console.log('[CLASSIC] Placing unplaced parents for', checkPid, ':', unplacedParents);
                parentsPlaced++;
                
                const parentY = coords[checkPid].y - LEVEL_HEIGHT;
                const parentWidths = unplacedParents.map(pr => Math.max(getSubtreeWidth(pr), blockWidthOnly(persons[pr])));
                let totalParentW = parentWidths.reduce((a, b) => a + b, 0);
                for (let i = 0; i < unplacedParents.length - 1; i++) {
                    totalParentW += gapBetweenSiblings(unplacedParents[i], unplacedParents[i + 1]);
                }
                let parentX = coords[checkPid].x - totalParentW / 2;
                unplacedParents.forEach((pr, i) => {
                    if (!coords[pr]) {
                        const pw = parentWidths[i];
                        placeSubtree(pr, parentX, parentY, pw);
                    }
                    parentX += parentWidths[i];
                    if (i < unplacedParents.length - 1) {
                        parentX += gapBetweenSiblings(unplacedParents[i], unplacedParents[i + 1]);
                    }
                });
            }
        }
    }
    
    console.log('[CLASSIC] Total parents placed in pass 1.5:', parentsPlaced);

    // === ПРОХОД 2: ДОРАЗМЕЩЕНИЕ СУПРУГОВ ===
    // Добавляем супругов которые не были размещены
    let added = 0;
    let iterations = 0;
    const maxIterations = related.size * 2;
    
    do {
        added = 0;
        iterations++;
        
        // Через marriages
        (marriages || []).forEach(m => {
            let a, b;
            if (Array.isArray(m)) {
                [a, b] = m;
            } else if (m.persons && Array.isArray(m.persons)) {
                [a, b] = m.persons;
            }
            const aStr = String(a), bStr = String(b);
            
            if (related.has(aStr) && related.has(bStr) && persons[aStr] && persons[bStr]) {
                // Если один размещён, а другой нет
                if (coords[aStr] && !coords[bStr]) {
                    coords[bStr] = { x: coords[aStr].x + spouseStep, y: coords[aStr].y };
                    added++;
                } else if (coords[bStr] && !coords[aStr]) {
                    coords[aStr] = { x: coords[bStr].x - spouseStep, y: coords[bStr].y };
                    added++;
                }
            }
        });
        
        // Через spouse_ids
        for (const pid of related) {
            if (coords[pid] || !persons[pid]) continue;
            const p = persons[pid];
            
            for (const spouseId of (p.spouse_ids || [])) {
                const sStr = String(spouseId);
                if (related.has(sStr) && persons[sStr] && coords[sStr] && !coords[pid]) {
                    coords[pid] = { x: coords[sStr].x + spouseStep, y: coords[sStr].y };
                    added++;
                    break;
                }
            }
        }
    } while (added > 0 && iterations < maxIterations);

    // === ПРОХОД 3: ДОРАЗМЕЩЕНИЕ ОСТАВШИХСЯ ===
    let layoutOffsetX = 0;
    let layoutOffsetY = 0;
    
    for (const pid of related) {
        if (!coords[pid] && persons[pid]) {
            console.log('[CLASSIC] Disconnected person, placing at offset:', pid);
            coords[pid] = { x: layoutOffsetX + CARD_W / 2, y: layoutOffsetY + CARD_H / 2 };
            layoutOffsetX += CARD_W * 2;
        }
    }

    // === ВЫЧИСЛЕНИЕ ГРАНИЦ ===
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;
    
    for (const pid in coords) {
        if (related.has(pid)) {
            const pos = coords[pid];
            minX = Math.min(minX, pos.x - CARD_W / 2);
            minY = Math.min(minY, pos.y - CARD_H / 2);
            maxX = Math.max(maxX, pos.x + CARD_W / 2);
            maxY = Math.max(maxY, pos.y + CARD_H / 2);
        }
    }
    
    if (!isFinite(minX)) minX = 0;
    if (!isFinite(minY)) minY = 0;
    if (!isFinite(maxX)) maxX = CARD_W * 3;
    if (!isFinite(maxY)) maxY = CARD_H * 3;

    const bounds = { left: minX, top: minY, right: maxX, bottom: maxY };
    const offsetX = Math.max(0, -bounds.left) + PAD;
    const offsetY = Math.max(0, -bounds.top) + PAD;
    const totalW = bounds.right - bounds.left + PAD * 2;
    const totalH = bounds.bottom - bounds.top + PAD * 2;

    console.log('[CLASSIC] Layout complete:', Object.keys(coords).length, 'persons,', 'bounds:', bounds);

    return { coords, bounds, totalW, totalH, offsetX, offsetY };
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

    const applyZoom = (newZoom, mouseX, mouseY) => {
        const oldZoom = treeZoom;
        const clampedZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, newZoom));

        // Если зум не изменился — ничего не делаем
        if (clampedZoom === oldZoom) {
            return;
        }

        // Зум в точку курсора: корректируем panX/panY так, чтобы точка под мышью осталась на месте
        const scaleChange = clampedZoom / oldZoom;
        treePanX = mouseX - (mouseX - treePanX) * scaleChange;
        treePanY = mouseY - (mouseY - treePanY) * scaleChange;

        treeZoom = clampedZoom;

        // Убираем transition чтобы зум был мгновенным без плавного смещения
        panZoomWrapper.style.transition = 'none';

        zoomContainer.style.width = (totalW * treeZoom) + "px";
        zoomContainer.style.height = (totalH * treeZoom) + "px";
        wrap.style.transform = `scale(${treeZoom})`;

        // Смещаем холст с учётом нового зума
        panZoomWrapper.style.transform = `translate(${treePanX}px,${treePanY}px)`;
    };

    // Wheel zoom (desktop + touchpad) - НА ВСЮ ОБЛАСТЬ ОКНА!
    // Используем capture: true чтобы перехватывать события даже над карточками
    viewport.addEventListener("wheel", (e) => {
        e.preventDefault();
        const rect = viewport.getBoundingClientRect();
        // Координаты мыши относительно viewport (экрана)
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        const factor = e.deltaY > 0 ? 0.9 : 1.1;
        applyZoom(treeZoom * factor, mouseX, mouseY);
    }, { passive: false, capture: true });

    // Pinch zoom (mobile) - вешаем на panZoomWrapper (работает и на пустом поле)
    let pinchDist0, zoom0, pinchCenterX, pinchCenterY;
    let pinchStartTime = 0;

    // Важно: используем capture phase чтобы перехватить события до карточек
    panZoomWrapper.addEventListener("touchstart", (e) => {
        console.log('[PINCH] touchstart on wrapper, touches:', e.touches.length, 'target:', e.target.className);
        if (e.touches.length === 2) {
            e.preventDefault(); // Блокируем скролл
            pinchStartTime = Date.now();
            pinchDist0 = Math.hypot(e.touches[1].clientX - e.touches[0].clientX, e.touches[1].clientY - e.touches[0].clientY);
            zoom0 = treeZoom;
            const rect = viewport.getBoundingClientRect();
            // Вычисляем центр между двумя пальцами относительно viewport
            pinchCenterX = (e.touches[0].clientX + e.touches[1].clientX) / 2 - rect.left;
            pinchCenterY = (e.touches[0].clientY + e.touches[1].clientY) / 2 - rect.top;
            console.log('[PINCH] Started dist:', pinchDist0.toFixed(1), 'zoom:', zoom0.toFixed(2));
        }
    }, { passive: false, capture: true });

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
    }, { passive: false, capture: true });

    panZoomWrapper.addEventListener("touchend", (e) => {
        if (e.touches.length < 2) {
            // Сбрасываем pinch переменные
            pinchDist0 = null;
            console.log('[PINCH] Ended');
        }
    }, { passive: true, capture: true });

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
    console.log('[PAN] setupPan called, viewport found:', !!viewport, 'wrap:', wrap.className);
    if (!viewport) {
        console.error('[PAN] viewport not found! Cannot setup pan.');
        return;
    }

    const applyPan = () => {
        panZoomWrapper.style.transform = `translate(${treePanX}px,${treePanY}px)`;
    };
    
    // Убираем transition во время перетаскивания
    const disableTransition = () => {
        panZoomWrapper.style.transition = 'none';
    };
    
    // Включаем transition для анимации
    const enableTransition = () => {
        panZoomWrapper.style.transition = 'transform 0.6s ease-in-out';
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
        enableTransition(); // Возвращаем transition для анимации
    };

    const startPan = (clientX, clientY) => {
        active = true;
        window._treeDidPan = false;
        startX = clientX;
        startY = clientY;
        startPanX = treePanX;
        startPanY = treePanY;
        viewport.style.cursor = "grabbing";
        disableTransition(); // Убираем transition для мгновенной реакции
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
        enableTransition(); // Возвращаем transition для анимации
    };
    const onTouchEnd = stopTouchPan;
    viewport.style.cursor = "grab";
    viewport.addEventListener("mousedown", (e) => {
        if (e.button !== 0) return;
        startPan(e.clientX, e.clientY);
    });
    viewport.addEventListener("touchstart", (e) => {
        console.log('[PAN] viewport touchstart, touches:', e.touches.length, 'target:', e.target.className);
        // Начинаем pan только если 1 палец
        if (e.touches.length !== 1) {
            console.log('[PAN] Ignored: touches=', e.touches.length);
            return;
        }
        // НЕ делаем preventDefault - позволяем событиям проходить к карточкам и зуму
        const t = e.touches[0];
        startX = t.clientX;
        startY = t.clientY;
        startPanX = treePanX;
        startPanY = treePanY;
        active = true;
        window._treeDidPan = false;
        console.log('[PAN] Started at', startX, startY);
        document.addEventListener("touchmove", onTouchMove, { passive: false });
        document.addEventListener("touchend", onTouchEnd);
        document.addEventListener("touchcancel", onTouchEnd);
    }, { passive: true });
}

function setCenterAndSave(pid) {
    console.log('[SET_CENTER] Called with pid:', pid);
    console.log('[SET_CENTER] Person:', treeData.persons[pid]);

    // === ЗАПОМИНАЕМ ЭКРАННЫЕ КООРДИНАТЫ ПЕРСОНЫ ДО ПЕРЕРИСОВКИ ===
    const oldCoords = treeData._coords || {};
    const oldPos = oldCoords[pid];
    const oldBounds = treeData._bounds || { left: 0, right: 0, top: 0, bottom: 0 };
    const oldOffsetX = Math.max(0, -oldBounds.left) + 60;
    const oldOffsetY = Math.max(0, -oldBounds.top) + 60;
    const zoomBefore = treeZoom;
    
    // Экранная позиция персоны ДО перерисовки (если персона видима)
    let screenXBefore = null, screenYBefore = null;
    if (oldPos && oldPos.x !== undefined) {
        screenXBefore = (oldPos.x + oldOffsetX) * zoomBefore + treePanX;
        screenYBefore = (oldPos.y + oldOffsetY) * zoomBefore + treePanY;
    }
    console.log('[SET_CENTER] screenBefore:', screenXBefore, screenYBefore);

    // === УСТАНАВЛИВАЕМ НОВЫЙ ЦЕНТР ===
    centerId = pid;
    treeData.current_center = pid;

    // Сохраняем на сервер
    saveTree();

    // Перерисовываем дерево с новым центром
    render();

    console.log('[SET_CENTER] Tree re-rendered, visible persons:', treeData._coords ? Object.keys(treeData._coords).length : 0);

    // === ВЫЧИСЛЯЕМ НОВЫЕ КООРДИНАТЫ ===
    const persons = treeData.persons;
    const p = persons[pid];
    const coords = treeData._coords || {};
    const pos = coords[pid];
    
    if (!p || !pos || pos.x === undefined) {
        console.log('[SET_CENTER] Person not found in coords');
        return;
    }

    const bounds = treeData._bounds || { left: 0, right: 0, top: 0, bottom: 0 };
    const offsetX = Math.max(0, -bounds.left) + 60;
    const offsetY = Math.max(0, -bounds.top) + 60;

    // Если у нас есть экранные координаты ДО, корректируем pan чтобы персона осталась на месте
    if (screenXBefore !== null) {
        // Новая экранная позиция с текущим pan (от render())
        const newScreenX = (pos.x + offsetX) * zoomBefore + treePanX;
        const newScreenY = (pos.y + offsetY) * zoomBefore + treePanY;
        
        // Разница между старой и новой экранной позицией
        const deltaX = screenXBefore - newScreenX;
        const deltaY = screenYBefore - newScreenY;
        
        // Корректируем pan чтобы персона осталась на том же месте экрана
        treePanX += deltaX;
        treePanY += deltaY;
        
        console.log('[SET_CENTER] delta:', deltaX, deltaY, 'adjusted pan:', treePanX, treePanY);
        
        // Применяем корректировку сразу (без анимации)
        const panZoomWrapper = document.querySelector('.tree-pan-zoom');
        if (panZoomWrapper) {
            panZoomWrapper.style.transition = 'none';
            panZoomWrapper.style.transform = `translate(${treePanX}px, ${treePanY}px)`;
        }
    }

    // === ТЕПЕРЬ ВЫЧИСЛЯЕМ ЦЕЛЕВЫЕ КООРДИНАТЫ ДЛЯ ЦЕНТРИРОВАНИЯ ===
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Целевые координаты: центр экрана минус координаты персоны с учётом зума
    const targetPanX = (viewportWidth / 2) - (pos.x + offsetX) * zoomBefore;
    const targetPanY = (viewportHeight / 2) - (pos.y + offsetY) * zoomBefore;

    console.log('[SET_CENTER] panAfter:', treePanX, treePanY, 'targetPan:', targetPanX, targetPanY);

    // На десктопе — плавная анимация перемещения в центр
    if (window.innerWidth > 480) {
        // Анимация будет в следующем кадре (от ТЕКУЩИХ координат к целевым)
        requestAnimationFrame(() => animateToCenterTarget(pid, treePanX, treePanY, targetPanX, targetPanY));
    } else {
        // На мобильном — сразу центрируем без анимации
        treePanX = targetPanX;
        treePanY = targetPanY;
        const panZoomWrapper = document.querySelector('.tree-pan-zoom');
        if (panZoomWrapper) {
            panZoomWrapper.style.transition = 'none';
            panZoomWrapper.style.transform = `translate(${treePanX}px, ${treePanY}px)`;
        }
    }
}

/**
 * Анимация перемещения к центральной персоне
 * @param {string} pid - ID персоны
 * @param {number} startX - Начальная X координата панорамирования
 * @param {number} startY - Начальная Y координата панорамирования
 * @param {number} targetX - Целевая X координата
 * @param {number} targetY - Целевая Y координата
 */
function animateToCenterTarget(pid, startX, startY, targetX, targetY) {
    console.log('[ANIMATE_CENTER] Starting animation for pid:', pid);
    console.log('[ANIMATE_CENTER] ======');
    console.log('[ANIMATE_CENTER] start:', startX, startY);
    console.log('[ANIMATE_CENTER] target:', targetX, targetY);

    // Проверяем, нужно ли вообще перемещать
    const dx = Math.abs(targetX - startX);
    const dy = Math.abs(targetY - startY);
    if (dx < 1 && dy < 1) {
        console.log('[ANIMATE_CENTER] Already centered, skipping animation');
        return;
    }

    // Анимация с ускорением и замедлением (ease-in-out)
    const duration = 600; // мс
    const startTime = performance.now();

    console.log('[ANIMATE_CENTER] Starting animation, duration:', duration, 'ms');

    function easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easedProgress = easeInOutCubic(progress);

        treePanX = startX + (targetX - startX) * easedProgress;
        treePanY = startY + (targetY - startY) * easedProgress;

        const panZoomWrapper = document.querySelector('.tree-pan-zoom');
        if (panZoomWrapper) {
            // Убираем transition для плавной анимации
            panZoomWrapper.style.transition = 'none';
            panZoomWrapper.style.transform = `translate(${treePanX}px, ${treePanY}px)`;
        }

        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            console.log('[ANIMATE_CENTER] Animation complete!');
            console.log('[ANIMATE_CENTER] Final treePanX:', treePanX, 'treePanY:', treePanY);
        }
    }

    requestAnimationFrame(animate);
}

/**
 * Рассчитывает степень родства для каждой персоны относительно centerId
 * Использует улучшенный алгоритм на основе desktop-версии
 * @returns {Object} Объект { pid: "степень родства" }
 */
function calculateKinship() {
    const persons = treeData.persons || {};
    const center = persons[centerId];
    const kinship = {};

    if (!center) return kinship;

    // Центральная персона
    kinship[centerId] = "Это вы";

    // BFS для расчёта родства через предков
    const visited = new Set();
    const queue = [[centerId, 0, null]]; // [pid, generation, relation]
    visited.add(String(centerId));

    while (queue.length > 0) {
        const [pid, gen, relation] = queue.shift();
        const p = persons[pid];
        if (!p) continue;

        // Если ещё не установлено родство
        if (!kinship[pid] || pid === centerId) continue;

        // Добавляем родственников в очередь
        // Родители (-1 поколение)
        if (p.parents) {
            for (const parentId of p.parents) {
                const pidStr = String(parentId);
                if (!visited.has(pidStr) && persons[parentId]) {
                    visited.add(pidStr);
                    queue.push([parentId, gen - 1, 'ancestor']);
                }
            }
        }

        // Дети (+1 поколение)
        if (p.children) {
            for (const childId of p.children) {
                const pidStr = String(childId);
                if (!visited.has(pidStr) && persons[childId]) {
                    visited.add(pidStr);
                    queue.push([childId, gen + 1, 'descendant']);
                }
            }
        }

        // Супруги (то же поколение)
        if (p.spouse_ids) {
            for (const spouseId of p.spouse_ids) {
                const pidStr = String(spouseId);
                if (!visited.has(pidStr) && persons[spouseId]) {
                    visited.add(pidStr);
                    queue.push([spouseId, gen, 'spouse']);
                }
            }
        }
    }

    // Второй проход — расчёт конкретного родства
    for (const pid of Object.keys(persons)) {
        if (pid === centerId) continue;
        
        const rel = getKinshipTerm(persons, centerId, pid);
        if (rel) {
            kinship[pid] = rel;
        }
    }

    return kinship;
}

/**
 * Определяет термин родства для персоны
 */
function getKinshipTerm(persons, centerId, personId) {
    const center = persons[centerId];
    const person = persons[personId];
    
    if (!center || !person) return null;

    // === 1. ПРЯМЫЕ СВЯЗИ ===
    
    // Родители
    if (center.parents && center.parents.includes(personId)) {
        return person.gender === "Мужской" ? "Отец" : "Мать";
    }
    
    // Дети
    if (person.parents && person.parents.includes(centerId)) {
        return person.gender === "Мужской" ? "Сын" : "Дочь";
    }
    
    // Супруги
    if ((center.spouse_ids && center.spouse_ids.includes(personId)) ||
        (person.spouse_ids && person.spouse_ids.includes(centerId))) {
        return person.gender === "Мужской" ? "Супруг" : "Супруга";
    }

    // === 2. ПРЕДКИ (деды, прадеды) ===
    const centerAncestors = getAncestors(persons, centerId);
    const personAncestors = getAncestors(persons, personId);
    
    // Проверяем, является ли person предком center
    if (centerAncestors[personId]) {
        const level = centerAncestors[personId];
        if (level === 1) return person.gender === "Мужской" ? "Отец" : "Мать";
        if (level === 2) return person.gender === "Мужской" ? "Дед" : "Бабушка";
        if (level === 3) return person.gender === "Мужской" ? "Прадед" : "Прабабушка";
        return person.gender === "Мужской" ? `Дед ${level}-го колена` : `Бабушка ${level}-го колена`;
    }

    // === 3. ПОТОМКИ (внуки, правнуки) ===
    const centerDescendants = getDescendants(persons, centerId);
    if (centerDescendants[personId]) {
        const level = centerDescendants[personId];
        if (level === 1) return person.gender === "Мужской" ? "Сын" : "Дочь";
        if (level === 2) return person.gender === "Мужской" ? "Внук" : "Внучка";
        if (level === 3) return person.gender === "Мужской" ? "Правнук" : "Правнучка";
        return person.gender === "Мужской" ? `Внук ${level}-го колена` : `Внучка ${level}-го колена`;
    }

    // === 4. КРОВНОЕ РОДСТВО (через общих предков) ===
    const commonAncestors = Object.keys(centerAncestors).filter(a => personAncestors[a]);
    
    if (commonAncestors.length > 0) {
        // Находим ближайшего общего предка
        let bestAncestor = null;
        let minDistance = Infinity;
        
        for (const ancestor of commonAncestors) {
            const distance = centerAncestors[ancestor] + personAncestors[ancestor];
            if (distance < minDistance) {
                minDistance = distance;
                bestAncestor = ancestor;
            }
        }
        
        if (bestAncestor) {
            const cLevel = centerAncestors[bestAncestor];
            const pLevel = personAncestors[bestAncestor];
            
            return getByLevels(person.gender, pLevel, cLevel);
        }
    }

    // === 5. СВОЙСТВЕННИКИ ===
    // Через супруга center
    if (center.spouse_ids) {
        for (const spouseId of center.spouse_ids) {
            if (spouseId === personId) continue;
            const spouse = persons[spouseId];
            if (!spouse) continue;
            
            // Родители супруга
            if (spouse.parents && spouse.parents.includes(personId)) {
                return person.gender === "Мужской" ? "Тесть" : "Теща";
            }
            
            // Братья/сёстры супруга
            for (const spouseParentId of spouse.parents || []) {
                const spouseParent = persons[spouseParentId];
                if (spouseParent && spouseParent.children && 
                    Array.from(spouseParent.children).some(c => String(c) === String(personId) && String(c) !== String(spouseId))) {
                    return person.gender === "Мужской" ? "Шурин" : "Золовка";
                }
            }
        }
    }

    return "Родственник";
}

/**
 * Возвращает предков с уровнями: {id: level}
 */
function getAncestors(persons, personId) {
    const ancestors = {};
    const queue = [[personId, 0]];
    const visited = new Set([String(personId)]);

    while (queue.length > 0) {
        const [currentId, level] = queue.shift();
        const current = persons[currentId];
        if (!current || !current.parents) continue;

        for (const parentId of current.parents) {
            const pidStr = String(parentId);
            if (!visited.has(pidStr) && persons[parentId]) {
                visited.add(pidStr);
                ancestors[parentId] = level + 1;
                queue.push([parentId, level + 1]);
            }
        }
    }

    return ancestors;
}

/**
 * Возвращает потомков с уровнями: {id: level}
 */
function getDescendants(persons, personId) {
    const descendants = {};
    const queue = [[personId, 0]];
    const visited = new Set([String(personId)]);

    while (queue.length > 0) {
        const [currentId, level] = queue.shift();
        const current = persons[currentId];
        if (!current || !current.children) continue;

        for (const childId of current.children) {
            const cidStr = String(childId);
            if (!visited.has(cidStr) && persons[childId]) {
                visited.add(cidStr);
                descendants[childId] = level + 1;
                queue.push([childId, level + 1]);
            }
        }
    }

    return descendants;
}

/**
 * Определяет родство по уровням до общего предка
 */
function getByLevels(gender, personLevel, centerLevel) {
    const diff = Math.abs(personLevel - centerLevel);

    // Один уровень = братья/сёстры
    if (personLevel === centerLevel) {
        if (personLevel === 1) {
            return gender === "Мужской" ? "Брат" : "Сестра";
        } else if (personLevel === 2) {
            return gender === "Мужской" ? "Двоюродный брат" : "Двоюродная сестра";
        } else if (personLevel === 3) {
            return gender === "Мужской" ? "Троюродный брат" : "Троюродная сестра";
        }
        return gender === "Мужской" ? `Двоюродный брат ${personLevel - 1}-го колена` : `Двоюродная сестра ${personLevel - 1}-го колена`;
    }

    // Разница 1 поколение
    if (diff === 1) {
        if (personLevel < centerLevel) {
            // person старше
            if (personLevel === 1 && centerLevel === 2) {
                return gender === "Мужской" ? "Дядя" : "Тётя";
            }
            if (personLevel === 1) {
                return gender === "Мужской" ? "Двоюродный дядя" : "Двоюродная тётя";
            }
            if (personLevel === 2 && centerLevel === 3) {
                return gender === "Мужской" ? "Двоюродный дядя" : "Двоюродная тётя";
            }
            return gender === "Мужской" ? "Дед" : "Бабушка";
        } else {
            // person младше
            if (centerLevel === 1 && personLevel === 2) {
                return gender === "Мужской" ? "Племянник" : "Племянница";
            }
            if (centerLevel === 2 && personLevel === 3) {
                return gender === "Мужской" ? "Двоюродный племянник" : "Двоюродная племянница";
            }
            return gender === "Мужской" ? "Племянник" : "Племянница";
        }
    }

    // Разница 2+ поколения
    if (personLevel < centerLevel) {
        // person старше
        if (personLevel === 1 && centerLevel === 2) {
            return gender === "Мужской" ? "Дед" : "Бабушка";
        }
        if (personLevel === 1) {
            return gender === "Мужской" ? "Двоюродный дед" : "Двоюродная бабушка";
        }
        return gender === "Мужской" ? "Прадед" : "Прабабушка";
    } else {
        // person младше
        if (centerLevel === 1 && personLevel === 2) {
            return gender === "Мужской" ? "Внук" : "Внучка";
        }
        if (centerLevel === 1) {
            return gender === "Мужской" ? "Правнук" : "Правнучка";
        }
        if (centerLevel === 2 && personLevel === 3) {
            return gender === "Мужской" ? "Внук" : "Внучка";
        }
        return gender === "Мужской" ? "Правнук" : "Правнучка";
    }
}

// === МОДАЛЬНОЕ ОКНО ДЛЯ РОДСТВЕННИКОВ (МОБИЛЬНЫЙ) ===
function showRelativesModal(pid, relatives) {
    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay";
    ov.innerHTML = `
        <div class="tree-modal" style="max-width: 90vw; width: 90vw;">
            <h3>Добавить родственника</h3>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                ${relatives.map(r => `
                    <button type="button" class="relatives-btn" style="
                        padding: 12px 16px;
                        text-align: left;
                        font-size: 16px;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        background: #fff;
                        cursor: pointer;
                        color: ${r.color || '#1e293b'};
                        font-weight: ${r.color ? '600' : '400'};
                    ">
                        ${r.label}
                    </button>
                `).join('')}
            </div>
            <div class="tree-modal-btns">
                <button type="button" class="cancel" style="width: 100%;">Отмена</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(ov);
    
    // Обработчики кнопок
    ov.querySelectorAll(".relatives-btn").forEach((btn, idx) => {
        btn.onclick = () => {
            relatives[idx].action();
            ov.remove();
        };
    });
    
    // Закрытие по клику вне окна
    ov.onclick = (e) => {
        if (e.target === ov) ov.remove();
    };
    
    // Кнопка отмены
    ov.querySelector(".cancel").onclick = () => ov.remove();
}

async function saveTree(showNotification = false) {
    // Создаём бэкап только если прошло 5 минут с последнего ИЛИ это первое сохранение
    const lastBackupTime = parseInt(localStorage.getItem('last_backup_time') || '0');
    const now = Date.now();
    const shouldCreateBackup = (now - lastBackupTime) > 5 * 60 * 1000; // 5 минут
    
    if (shouldCreateBackup) {
        createBackup();
        localStorage.setItem('last_backup_time', now.toString());
    }
    
    // Сохраняем в localStorage сразу (для мобильных)
    if (treeData && treeData.persons) {
        // Сохраняем с username для идентификации
        const backupData = {...treeData, _username: localStorage.getItem('family_tree_username') || 'unknown'};
        localStorage.setItem('family_tree_backup', JSON.stringify(backupData));
        // Сохраняем состояние для автосохранения
        lastSavedState = JSON.stringify(treeData);
    }

    // Проверяем, есть ли что сохранять
    const personsCount = treeData && treeData.persons ? Object.keys(treeData.persons).length : 0;
    if (personsCount === 0) {
        console.log('[SAVE] Skipping - tree is empty');
        return;
    }

    console.log('[SAVE] Saving tree with', personsCount, 'persons');
    console.log('[SAVE] treeData:', JSON.parse(JSON.stringify(treeData)));

    // Отправляем на сервер с повторной попыткой
    const maxRetries = 3;
    let serverSaved = false;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            console.log('[SAVE] Attempt', attempt, 'at', new Date().toLocaleTimeString());
            
            // DEBUG: Показываем полную информацию
            const fullUrl = window.location.origin + '/api/tree';
            console.log('[SAVE] URL:', fullUrl);
            console.log('[SAVE] Session check:', document.cookie ? 'Cookies present' : 'No cookies');
            console.log('[SAVE] Tree data size:', JSON.stringify(treeData).length, 'bytes');

            const response = await fetch(fullUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(treeData),
                credentials: "include"
            });
            
            console.log('[SAVE] Response status:', response.status);

            if (response.ok) {
                const result = await response.json();
                console.log('[SAVE] Server response:', result);

                if (result.ok) {
                    console.log('[SAVE] ✅ Success at', new Date().toLocaleTimeString());
                    serverSaved = true;
                    // Обновляем treeData из ответа сервера если есть
                    if (result.tree) {
                        treeData = result.tree;
                    }
                } else {
                    console.error('[SAVE] ❌ Server returned error:', result);
                }

                // Показываем уведомление только если сервер сохранил
                if (showNotification || window.innerWidth <= 480) {
                    const msg = document.createElement('div');
                    msg.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#27ae60;color:white;padding:12px 24px;border-radius:8px;z-index:10000;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-size:16px;font-weight:bold;';
                    msg.textContent = serverSaved ? '✅ Дерево сохранено на сервере!' : '⚠️ Сохранено локально';
                    document.body.appendChild(msg);
                    setTimeout(() => msg.remove(), 4000);
                }
                return true;  // Успех
            } else if (response.status === 401) {
                console.error('[SAVE] ❌ Unauthorized - session expired');
                alert('Сессия истекла. Пожалуйста, войдите снова.');
                window.location.href = '/login';
                return false;
            } else {
                console.error('[SAVE] ❌ Server error:', response.status, 'attempt', attempt);
            }
        } catch (e) {
            console.error('[SAVE] ❌ Network error:', e, 'attempt', attempt);
            if (attempt < maxRetries) {
                await new Promise(resolve => setTimeout(resolve, 1000));  // Ждём 1 секунду
            }
        }
    }

    console.error('[SAVE] ❌ Failed after', maxRetries, 'attempts');

    // Данные УЖЕ сохранены в localStorage (см. выше), показываем предупреждение
    console.warn('[SAVE] ⚠️ Saved locally only (server unavailable)');

    // Показываем уведомление
    const msg = document.createElement('div');
    msg.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#f39c12;color:white;padding:12px 24px;border-radius:8px;z-index:10000;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-size:16px;font-weight:bold;';
    msg.textContent = '⚠️ Сохранено локально (сервер недоступен)';
    document.body.appendChild(msg);
    setTimeout(() => msg.remove(), 5000);
    
    // Возвращаем false чтобы вызвать перезагрузку
    return false;
}

// === ИСПРАВЛЕНИЕ СКРОЛЛА НА МОБИЛЬНОМ ===
// Добавляем обработчик для принудительной прокрутки в модальных окнах
document.addEventListener('DOMContentLoaded', function() {
    // Разрешаем скролл в модальных окнах на мобильном
    document.addEventListener('touchmove', function(e) {
        // Если скролл внутри модального окна — разрешаем
        if (e.target.closest('.tree-modal-overlay') || e.target.closest('.tree-edit-overlay')) {
            e.stopPropagation();
        }
    }, {passive: true});
});

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
        // === СВЁРНУТЬ/РАЗВЕРНУТЬ ВЕТКУ ===
        p.children && p.children.length > 0 && {
            label: p.collapsed_branches ? "🔓 Развернуть ветку" : "🔒 Свернуть ветку",
            action: () => {
                if (window.undoManager) window.undoManager.saveState(treeData);
                p.collapsed_branches = !p.collapsed_branches;
                saveTree();
                render();
            }
        },
        { sep: true },
        // === /СВЁРНУТЬ/РАЗВЕРНУТЬ ВЕТКУ ===
        { label: "Родственник", sub: subItems },
    ].filter(Boolean);

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
            mainItem.style.cursor = 'pointer';

            // Обработка для мобильного (touch) и десктопа (click)
            const toggleSubmenu = (e) => {
                if (e) e.stopPropagation();
                
                // На мобильном — открываем модальное окно вместо подменю
                if (window.innerWidth <= 480) {
                    e.preventDefault();
                    closeContextMenu();  // Закрываем контекстное меню
                    showRelativesModal(pid, subItems);  // Открываем модальное окно
                    return;
                }
                
                // На десктопе — переключаем подменю
                subWrap.classList.toggle('is-open');
                console.log('[CONTEXT_MENU] submenu toggle:', subWrap.classList.contains('is-open'));
            };

            // Для мобильного - touchstart (срабатывает раньше click)
            mainItem.addEventListener('touchstart', toggleSubmenu, {passive: false});
            // Для десктопа - click
            mainItem.addEventListener('click', toggleSubmenu, {passive: true});

            subWrap.appendChild(mainItem);
            const submenu = document.createElement("div");
            submenu.className = "cm-submenu tree-context-menu";
            console.log('[CONTEXT_MENU] Creating submenu for', it.label, 'with', it.sub.length, 'items');
            it.sub.forEach((s) => {
                const si = document.createElement("div");
                si.className = "cm-item";
                si.textContent = s.label;
                if (s.color) {
                    si.style.color = s.color;
                    si.style.fontWeight = "500";
                }
                // Обработка клика для мобильных и десктопа
                const handleItemClick = (e) => {
                    if (e) e.stopPropagation();
                    console.log('[CONTEXT_MENU] item click:', s.label);
                    closeContextMenu();
                    s.action();
                };
                si.addEventListener('touchstart', handleItemClick, {passive: true});
                si.addEventListener('click', handleItemClick, {passive: true});
                submenu.appendChild(si);
            });
            subWrap.appendChild(submenu);
            menu.appendChild(subWrap);
        } else {
            const item = document.createElement("div");
            item.className = "cm-item";
            item.textContent = it.label;
            item.style.cursor = 'pointer';
            
            // Обработка для мобильных и десктопа
            const handleItemClick = (e) => {
                if (e) e.stopPropagation();
                it.action();
                closeContextMenu();
            };
            item.addEventListener('touchstart', handleItemClick, {passive: true});
            item.addEventListener('click', handleItemClick, {passive: true});
            menu.appendChild(item);
        }
    });

    document.body.appendChild(menu);
    window._ctxMenu = menu;

    const close = (e) => {
        // НЕ закрываем меню если клик был по меню или по модальному окну
        if (e && e.target) {
            if (e.target.closest('.tree-context-menu')) return;
            if (e.target.closest('.tree-modal')) return;
            if (e.target.closest('.tree-modal-overlay')) return;
        }
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

async function editPerson(pid) {
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
                        <button type="button" class="btn-browse" id="ed-photo-browse-btn">Обзор...</button>
                        <input type="file" id="ed-photo-file" accept="image/*" style="display:none">
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
                            <button type="button" class="btn-remove-spouse" data-spouse="${escapeHtml(String(s))}" title="Удалить с��я������ь">✕</button>
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
                ${hasPreview ? `<img src="${path}" alt="" class="ed-album-thumb" onerror="this.style.display='none'">` : '<span class="ed-album-no-thumb">Нет превь����</span>'}
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
                <input type="text" class="ed-link-title" placeholder="Назва����ие" value="${escapeHtml(l.title)}">
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
    
    // Обработчик кнопки "Обзор"
    ov.querySelector("#ed-photo-browse-btn").onclick = () => {
        ov.querySelector("#ed-photo-file").click();
    };
    
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

    ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
    ov.querySelector(".tree-edit-modal").onclick = (e) => e.stopPropagation();
    ov.querySelector(".cancel").onclick = () => ov.remove();
    
    // Обработчик кнопки "Сохранить"
    ov.querySelector(".save").onclick = () => {
        console.log('[EDIT_PERSON] Save button clicked');
        
        const name = ov.querySelector("#ed-name").value.trim();
        const surname = ov.querySelector("#ed-surname").value.trim();
        
        console.log('[EDIT_PERSON] Name:', name, 'Surname:', surname);
        
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

        // Сохраняем дерево
        saveTree(true).then(() => {
            ov.remove();
            render();
            const savedName = [p.name, p.patronymic, p.surname].filter(Boolean).join(" ");
            showStatusMessage(`✅ Сохранено: ${savedName}`);
        });
    };
    document.body.appendChild(ov);
}

async function deletePerson(pid) {
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
    // Фильтруем браки - поддерживаем оба формата: [a,b] и {persons: [a,b]}
    treeData.marriages = (treeData.marriages || []).filter(m => {
        let a, b;
        if (Array.isArray(m)) {
            [a, b] = m;
        } else if (m && m.persons && Array.isArray(m.persons)) {
            [a, b] = m.persons;
        } else {
            return false; // Неверный формат - удаляем
        }
        return a !== pid && b !== pid && String(a) !== pid && String(b) !== pid;
    });
    if (centerId === pid || String(centerId) === pid) {
        centerId = Object.keys(persons)[0] || null;
        treeData.current_center = centerId;
    }
    
    // Сохраняем
    await saveTree();
    
    // Перерисовываем (не перезагружаем с сервера!)
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
    ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
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
        saveTree(true).then(() => {
            ov.remove();
            render();
        });
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
    ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
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
            if (par) {
                // ВАЖНО: Добавляем как строку!
                par.parents = [...(par.parents || []).map(String), String(newId)];
                console.log('[ADD_RELATIVE] Added', relation, newId, 'to parents of', pidStr, ':', par.parents);
                
                // === АВТОМАТИЧЕСКИ ДОБАВЛЯЕМ СУПРУГА ЕСЛИ ЕСТЬ ВТОРОЙ РОДИТЕЛЬ ===
                const otherParentId = par.parents.find(id => String(id) !== String(newId));
                if (otherParentId) {
                    const otherParent = treeData.persons[otherParentId];
                    if (otherParent && !otherParent.spouse_ids.includes(newId)) {
                        // Делаем их супругами
                        otherParent.spouse_ids = [...(otherParent.spouse_ids || []), newId];
                        np.spouse_ids = [otherParentId];
                        const pair = [String(newId), String(otherParentId)].sort();
                        // Проверяем, нет ли уже такого брака
                        const exists = treeData.marriages.some(([a, b]) => (a === newId && b === otherParentId) || (a === otherParentId && b === newId));
                        if (!exists) {
                            treeData.marriages = [...(treeData.marriages || []), pair];
                        }
                        console.log('[ADD_RELATIVE] Auto-added marriage between', newId, 'and', otherParentId);
                    }
                }
            }
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
        // После добавления родителя - делаем его центром для отображения
        if (relation === "father" || relation === "mother") {
            centerId = newId;
            treeData.current_center = newId;
            console.log('[ADD_RELATIVE] Set center to new parent:', newId);
        }
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

    ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
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
            ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
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
    ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
    
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
            ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
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
    ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
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
    ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
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
                <p>Приложение со��дано для удобного построения и визуализации семейных генеалогических деревьев с возможностью экспорта, резервного копирования и работы в веб-интерфейсе.</p>
            </div>
            <div class="tree-modal-btns">
                <button type="button" class="cancel">Закрыть</button>
            </div>
        </div>`;

    ov.querySelector(".cancel").onclick = () => ov.remove();
    ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
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
            } else if (act === "render-mode") {
                openRenderModeDialog();
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
            } else if (act === "backups") {
                showBackupManager();
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
    ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
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

    ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
    ov.querySelector(".cancel").onclick = () => ov.remove();
    ov.querySelector(".tree-modal").onclick = (e) => e.stopPropagation();
    document.body.appendChild(ov);
    qInp.focus();
}

/**
 * Открывает диалог выбора режима отрисовки
 */
function openRenderModeDialog() {
    const currentMode = getRenderMode();
    
    const ov = document.createElement("div");
    ov.className = "tree-modal-overlay";
    ov.innerHTML = `
        <div class="tree-modal tree-render-mode-modal">
            <h3>🎨 Режим отрисовки</h3>
            <p style="color: #64748b; font-size: 14px; margin-bottom: 16px;">
                Выберите способ отображения семейного дерева
            </p>
            
            <div class="render-mode-options">
                <label class="render-mode-option ${currentMode === 'generations' ? 'active' : ''}">
                    <input type="radio" name="render-mode" value="generations" ${currentMode === 'generations' ? 'checked' : ''}>
                    <div class="mode-card">
                        <div class="mode-icon">🌳</div>
                        <div class="mode-name">По поколениям</div>
                        <div class="mode-desc">
                            Чёткая иерархия: предки сверху, потомки снизу. 
                            Все в одном поколении на одной линии.
                        </div>
                    </div>
                </label>
                
                <label class="render-mode-option ${currentMode === 'classic' ? 'active' : ''}">
                    <input type="radio" name="render-mode" value="classic" ${currentMode === 'classic' ? 'checked' : ''}>
                    <div class="mode-card">
                        <div class="mode-icon">🔀</div>
                        <div class="mode-name">Классический</div>
                        <div class="mode-desc">
                            Традиционное дерево с автоматической 
                            компоновкой поддеревьев.
                        </div>
                    </div>
                </label>
            </div>
            
            <div class="tree-modal-btns">
                <button type="button" class="cancel">Отмена</button>
                <button type="button" class="ok" id="apply-render-mode">Применить</button>
            </div>
        </div>`;
    
    // Обработчик выбора режима
    const applyBtn = ov.querySelector("#apply-render-mode");
    applyBtn.onclick = () => {
        const selectedMode = ov.querySelector('input[name="render-mode"]:checked')?.value;
        if (selectedMode && selectedMode !== currentMode) {
            setRenderMode(selectedMode);
        }
        ov.remove();
    };
    
    // Клик по карточке тоже выбирает режим
    ov.querySelectorAll(".render-mode-option").forEach(option => {
        option.onclick = (e) => {
            const radio = option.querySelector('input[type="radio"]');
            radio.checked = true;
            ov.querySelectorAll(".render-mode-option").forEach(o => o.classList.remove("active"));
            option.classList.add("active");
        };
    });
    
    ov.querySelector(".cancel").onclick = () => ov.remove();
    ov.querySelector(".tree-modal").onclick = (e) => e.stopPropagation();
    
    ov.onclick = (e) => {
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove();
    };
    
    document.body.appendChild(ov);
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

console.log('[TREE.JS] URL:', window.location.search);
console.log('[TREE.JS] isAdminViewCheck:', isAdminViewCheck);

// Вызываем ПОСЛЕ загрузки DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[TREE.JS] DOMContentLoaded - calling initApp()');
        initApp();
    });
} else {
    console.log('[TREE.JS] DOM already loaded - calling initApp()');
    initApp();
}

function initApp() {
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

    // ❌ УБРАЛИ checkFirstRun() отсюда - вызовем после загрузки дерева
}

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
    
    ov.onclick = (e) => { 
        // Не закрываем если было выделение текста
        const sel = window.getSelection();
        if (sel && sel.toString().length > 0) return;
        if (e.target === ov) ov.remove(); 
    };
    document.body.appendChild(ov);
    ov.querySelector("#welcome-name").focus();
}

// === АВТОСОХРАНЕНИЕ ПРИ ЗАКРЫТИИ СТРАНИЦЫ (важно для мобильных) ===
let saveTimeout = null;

// Сохраняем дерево при закрытии/обновлении страницы
window.addEventListener('beforeunload', (e) => {
    console.log('[AUTO-SAVE] beforeunload triggered at', new Date().toLocaleTimeString());
    
    // Сохраняем в localStorage для быстрого восстановления
    if (treeData && treeData.persons) {
        localStorage.setItem('family_tree_backup', JSON.stringify(treeData));
        console.log('[AUTO-SAVE] Saved to localStorage');
    }
    
    // ЗАЩИТА: Не отправляем пустое дерево на сервер!
    const personsCount = treeData && treeData.persons ? Object.keys(treeData.persons).length : 0;
    if (personsCount === 0) {
        console.log('[AUTO-SAVE] Skipping server save - tree is empty');
        return;
    }
    
    // Отправляем на сервер используя sendBeacon (работает даже при закрытии)
    if (personsCount > 0) {
        const blob = new Blob([JSON.stringify(treeData)], {type: 'application/json'});
        navigator.sendBeacon('/api/tree', blob);
        console.log('[AUTO-SAVE] Sent to server via sendBeacon:', personsCount, 'persons');
    }
});

// Сохранение при уходе в фон (mobile)
document.addEventListener('visibilitychange', async () => {
    if (document.visibilityState === 'hidden') {
        console.log('[AUTO-SAVE] visibilitychange hidden at', new Date().toLocaleTimeString());
        
        // ЗАЩИТА: Не сохраняем пустое дерево!
        const personsCount = treeData && treeData.persons ? Object.keys(treeData.persons).length : 0;
        if (personsCount === 0) {
            console.log('[AUTO-SAVE] Skipping save - tree is empty');
            return;
        }
        
        // Пользователь свернул браузер или перешёл на другую вкладку
        if (treeData && treeData.persons) {
            // Сохраняем в localStorage
            localStorage.setItem('family_tree_backup', JSON.stringify(treeData));
            console.log('[AUTO-SAVE] Saved to localStorage');
            
            // Отправляем на сервер
            try {
                await fetch('/api/tree', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(treeData)
                });
                console.log('[AUTO-SAVE] Sent to server:', personsCount, 'persons');
            } catch (e) {
                console.warn('[AUTO-SAVE] Server save failed:', e);
            }
        }
    }
});

// Периодическое автосохранение каждые 60 секунд (1 минута)
console.log('[AUTO-SAVE] Periodic save started: every 60 seconds');
setInterval(() => {
    const personsCount = treeData && treeData.persons ? Object.keys(treeData.persons).length : 0;

    // ЗАЩИТА: Не сохраняем пустое дерево!
    if (personsCount === 0) {
        return;
    }

    if (treeData && treeData.persons && personsCount > 0) {
        // Сохраняем в localStorage
        localStorage.setItem('family_tree_backup', JSON.stringify(treeData));

        // Отправляем на сервер
        fetch('/api/tree', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(treeData)
        }).then(() => {
            console.log('[AUTO-SAVE] Periodic save to server at', new Date().toLocaleTimeString(), ':', personsCount, 'persons');
        }).catch(e => {
            console.warn('[AUTO-SAVE] Periodic save failed:', e);
        });
    }
}, 60000);  // Автосохранение каждую минуту (60000 мс)