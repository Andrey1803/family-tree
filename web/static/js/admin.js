/**
 * Админ-панель — Семейное древо
 * ТОЛЬКО статистика и просмотр деревьев других пользователей
 */

let usersData = [];
let treesData = [];
let currentUserId = null;
let usersRefreshInterval = null;

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    loadStats();
    setupSearch();
    setupRefresh();
    // Загружаем пользователей сразу при загрузке страницы
    loadUsers();
    
    // Автоматически переключаемся на вкладку пользователей
    const usersTabBtn = document.querySelector('.tab-btn[data-tab="users"]');
    const usersPane = document.getElementById('tab-users');
    if (usersTabBtn && usersPane) {
        // Переключаем классы активности
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        usersTabBtn.classList.add('active');
        usersPane.classList.add('active');
        console.log('[ADMIN] Switched to users tab by default');
    }
});

// Автообновление списка пользователей каждые 30 секунд
function startUsersAutoRefresh() {
    if (usersRefreshInterval) {
        clearInterval(usersRefreshInterval);
    }
    usersRefreshInterval = setInterval(() => {
        // Обновляем только если вкладка пользователей активна
        const usersTab = document.querySelector('.tab-btn[data-tab="users"]');
        if (usersTab && usersTab.classList.contains('active')) {
            loadUsers();
        }
    }, 30000); // 30 секунд
    
    console.log('[ADMIN] Users auto-refresh started (30s)');
}

// Остановка автообновления
function stopUsersAutoRefresh() {
    if (usersRefreshInterval) {
        clearInterval(usersRefreshInterval);
        usersRefreshInterval = null;
        console.log('[ADMIN] Users auto-refresh stopped');
    }
}

// Переключение вкладок
function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // Переключение кнопок
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Переключение контента
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            
            // Загрузка данных для вкладки
            if (tabId === 'users') loadUsers();
            if (tabId === 'trees') loadAllTrees();  // Загружаем ВСЕ деревья
        });
    });
}

// Загрузка статистики
async function loadStats() {
    try {
        const r = await fetch('/api/admin/stats');
        if (!r.ok) throw new Error('Ошибка загрузки статистики');
        const data = await r.json();
        
        // Обновление карточек
        document.getElementById('stat-total-users').textContent = data.overview.total_users || 0;
        document.getElementById('stat-active-users').textContent = data.overview.active_users || 0;
        document.getElementById('stat-total-trees').textContent = data.overview.total_trees || 0;
        document.getElementById('stat-total-persons').textContent = data.overview.total_persons || 0;
        document.getElementById('stat-active-sessions').textContent = data.overview.active_sessions || 0;
        
        // Последние регистрации
        const usersTbody = document.getElementById('recent-users');
        usersTbody.innerHTML = (data.recent_users || []).map(u => `
            <tr>
                <td>${escapeHtml(u.login)}</td>
                <td>${escapeHtml(u.email || '—')}</td>
                <td>${formatDate(u.created_at)}</td>
            </tr>
        `).join('');
        
        // Последние синхронизации
        const syncsTbody = document.getElementById('recent-syncs');
        syncsTbody.innerHTML = (data.recent_syncs || []).map(s => `
            <tr>
                <td>${escapeHtml(s.login)}</td>
                <td>${escapeHtml(s.action)}</td>
                <td>${s.entities_count || 0}</td>
                <td><span class="status-${s.status === 'success' ? 'active' : 'inactive'}">${s.status}</span></td>
                <td>${formatDate(s.created_at)}</td>
            </tr>
        `).join('');
        
        // График по дням
        renderDailyChart(data.daily_stats || []);
        
    } catch (err) {
        console.error('Stats error:', err);
    }
}

// Рендер графика
function renderDailyChart(dailyStats) {
    const chart = document.getElementById('daily-chart');
    if (!dailyStats.length) {
        chart.innerHTML = '<div class="muted">Нет данных</div>';
        return;
    }
    
    const maxCount = Math.max(...dailyStats.map(d => d.sync_count || 0), 1);
    
    chart.innerHTML = dailyStats.slice(0, 15).reverse().map(d => {
        const height = ((d.sync_count || 0) / maxCount) * 100;
        const date = new Date(d.date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
        return `
            <div class="chart-bar" style="height: ${Math.max(height, 5)}%" 
                 data-date="${date}" title="${d.sync_count} синхр. ${d.total_entities} сущ."></div>
        `;
    }).join('');
}

// Загрузка пользователей
async function loadUsers() {
    try {
        const r = await fetch('/api/admin/users');
        if (!r.ok) throw new Error('Ошибка загрузки пользователей');
        const data = await r.json();
        usersData = data.users || [];

        renderUsersTable(usersData);
        updateUserFilter();
        
        // Запускаем автообновление после первой загрузки
        startUsersAutoRefresh();

    } catch (err) {
        console.error('Users error:', err);
        document.getElementById('users-table').innerHTML = '<tr><td colspan="8">Ошибка загрузки</td></tr>';
    }
}

// Рендер таблицы пользователей
function renderUsersTable(users) {
    const tbody = document.getElementById('users-table');
    if (!users.length) {
        tbody.innerHTML = '<tr><td colspan="9" class="muted">Нет пользователей</td></tr>';
        return;
    }

    console.log('[ADMIN] Rendering users:', users.length, 'users');
    console.log('[ADMIN] Online users:', users.filter(u => u.is_online).length);

    tbody.innerHTML = users.map(u => `
        <tr>
            <td>${u.id}</td>
            <td>
                <span class="online-indicator ${u.is_online ? 'online' : ''}" title="${u.is_online ? 'Онлайн' : 'Оффлайн'}"></span>
                <strong>${escapeHtml(u.login)}</strong>
            </td>
            <td>${escapeHtml(u.email || '—')}</td>
            <td>${formatDate(u.created_at)}</td>
            <td>${formatDate(u.last_login) || '—'}</td>
            <td><span class="status-${u.is_active ? 'active' : 'inactive'}">${u.is_active ? 'Активен' : 'Не активен'}</span></td>
            <td>${u.is_admin ? '👑' : '—'}</td>
            <td>
                <button class="btn-view" onclick="viewUserTrees('${escapeHtml(u.login)}')">🌳 Деревья</button>
                <button class="btn-toggle ${u.is_active ? 'active' : ''}" onclick="toggleUser(${u.id})">
                    ${u.is_active ? 'Деактивировать' : 'Активировать'}
                </button>
                ${u.login !== 'admin' ? `
                <button class="btn-delete" onclick="deleteUser(${u.id}, '${escapeHtml(u.login)}')">
                    ❌ Удалить
                </button>
                ` : ''}
            </td>
        </tr>
    `).join('');
}

// Поиск пользователей
function setupSearch() {
    document.getElementById('user-search').addEventListener('input', (e) => {
        const q = e.target.value.toLowerCase();
        const filtered = usersData.filter(u => 
            u.login.toLowerCase().includes(q) ||
            (u.email && u.email.toLowerCase().includes(q))
        );
        renderUsersTable(filtered);
    });
}

// Обновление
function setupRefresh() {
    document.getElementById('btn-refresh-users').addEventListener('click', loadUsers);
    document.getElementById('btn-refresh-trees').addEventListener('click', loadTrees);
}

// Переключение статуса пользователя
async function toggleUser(userId) {
    if (!confirm('Изменить статус пользователя?')) return;

    try {
        const r = await fetch(`/api/admin/user/${userId}/toggle`, { method: 'POST' });
        if (r.ok) {
            loadUsers();
        } else {
            alert('Ошибка изменения статуса');
        }
    } catch (err) {
        console.error('Toggle error:', err);
        alert('Ошибка: ' + err.message);
    }
}

// Удаление пользователя
async function deleteUser(userId, login) {
    if (!confirm(`⚠️ Вы уверены, что хотите удалить пользователя "${login}"?\n\nЭто действие нельзя отменить!`)) return;

    try {
        const r = await fetch(`/api/admin/user/${userId}/delete`, { method: 'POST' });
        const data = await r.json();

        if (r.ok) {
            alert('✅ ' + data.message);
            loadUsers();
        } else {
            alert('❌ ' + (data.error || 'Ошибка удаления'));
        }
    } catch (err) {
        console.error('Delete error:', err);
        alert('Ошибка: ' + err.message);
    }
}

// Просмотр деревьев пользователя
async function viewUserTrees(userId) {
    currentUserId = userId;
    await loadTrees(userId);
    
    // Переключение на вкладку деревьев
    document.querySelector('[data-tab="trees"]').click();
}

// Загрузка всех деревьев (для вкладки Деревья)
async function loadAllTrees() {
    console.log('[ADMIN] loadAllTrees called');
    try {
        // Сначала загружаем пользователей для фильтра
        if (!usersData.length) {
            console.log('[ADMIN] Loading users first...');
            await loadUsers();
            console.log('[ADMIN] Users loaded:', usersData.length);
        }

        console.log('[ADMIN] Fetching /api/admin/trees...');
        const r = await fetch('/api/admin/trees');
        console.log('[ADMIN] Response status:', r.status);
        if (!r.ok) throw new Error('Ошибка загрузки деревьев');
        const data = await r.json();
        console.log('[ADMIN] Received trees:', data.trees ? data.trees.length : 0);
        treesData = data.trees || [];
        
        // Логируем каждое дерево
        treesData.forEach((t, i) => {
            console.log(`[ADMIN] Tree ${i}: ${t.name}, persons: ${Object.keys(t.persons || {}).length}`);
        });

        renderTreesList(treesData);
        updateUserFilter();

    } catch (err) {
        console.error('Trees error:', err);
        document.getElementById('trees-list').innerHTML = '<div class="muted">Ошибка загрузки деревьев</div>';
    }
}

// Загрузка деревьев конкретного пользователя
async function loadTrees(userId = null) {
    try {
        const url = userId ? `/api/admin/user/${userId}/trees` : '/api/admin/trees';
        const r = await fetch(url);
        if (!r.ok) throw new Error('Ошибка загрузки деревьев');
        const data = await r.json();
        treesData = data.trees || [];
        
        renderTreesList(treesData);
        
    } catch (err) {
        console.error('Trees error:', err);
        document.getElementById('trees-list').innerHTML = '<div class="muted">Ошибка загрузки деревьев</div>';
    }
}

// Рендер списка деревьев
function renderTreesList(trees) {
    const list = document.getElementById('trees-list');
    if (!trees || !trees.length) {
        list.innerHTML = '<div class="muted">Нет деревьев</div>';
        return;
    }
    
    list.innerHTML = trees.map(t => {
        const personsCount = t.persons ? Object.keys(t.persons).length : 0;
        const marriagesCount = (t.marriages || []).length;
        const userLogin = t.user_login || 'Неизвестно';
        
        return `
        <div class="tree-item">
            <div class="tree-info">
                <h4>🌳 ${escapeHtml(t.name)}</h4>
                <div class="tree-meta">
                    <span>👤 Пользователь: ${escapeHtml(userLogin)}</span>
                    <span>👤 Персон: ${personsCount}</span>
                    <span>💍 Браков: ${marriagesCount}</span>
                    <span>📅 Обновлено: ${formatDate(t.updated_at)}</span>
                </div>
            </div>
            <div class="tree-actions">
                <button class="btn-view" onclick="viewTreeDetails('${t.id}')">📋 Список персон</button>
                <button class="btn-view btn-full-tree" onclick="openFullTree('${t.id}', '${escapeHtml(userLogin)}')">🌳 Открыть полное дерево</button>
            </div>
        </div>
    `}).join('');
}

// Обновление фильтра пользователей
let userFilterInitialized = false;

function updateUserFilter() {
    const select = document.getElementById('user-filter');
    select.innerHTML = '<option value="">Все пользователи</option>' +
        usersData.map(u => `<option value="${escapeHtml(u.login)}">${escapeHtml(u.login)}</option>`).join('');

    // Предотвращаем дублирование обработчика
    if (!userFilterInitialized) {
        select.addEventListener('change', () => {
            const selectedUser = select.value || null;
            if (selectedUser) {
                // Фильтруем деревья по пользователю
                const userTrees = treesData.filter(t => t.user_login === selectedUser);
                renderTreesList(userTrees);
            } else {
                renderTreesList(treesData);
            }
        });
        userFilterInitialized = true;
    }
}

// Открыть полное дерево с визуализацией
function openFullTree(treeId, userLogin) {
    console.log('[ADMIN] openFullTree called:', treeId, userLogin);
    console.log('[ADMIN] treesData:', treesData);
    console.log('[ADMIN] treesData length:', treesData.length);
    
    const tree = treesData.find(t => String(t.id) === String(treeId));
    if (!tree) {
        console.error('[ADMIN] Дерево не найдено! ID:', treeId);
        alert('Дерево не найдено. Попробуйте обновить страницу.');
        return;
    }

    console.log('[ADMIN] Found tree:', tree.name);
    console.log('[ADMIN] Persons count:', Object.keys(tree.persons || {}).length);

    // Сохраняем ТОЛЬКО ID дерева и логин, данные загрузим на странице
    const treeRef = {
        treeId: treeId,
        treeName: tree.name,
        treeOwner: userLogin,
        personsCount: Object.keys(tree.persons || {}).length
    };

    console.log('[ADMIN] Saving treeRef to localStorage:', treeRef);
    localStorage.setItem('adminTreeRef', JSON.stringify(treeRef));
    
    // Сохраняем полные данные дерева тоже (на случай если API не сработает)
    const treeDataForView = {
        persons: tree.persons,
        marriages: tree.marriages,
        current_center: Object.keys(tree.persons)[0] || null,
        treeName: tree.name,
        treeOwner: userLogin
    };
    localStorage.setItem('adminTreeData', JSON.stringify(treeDataForView));

    // Открываем страницу дерева в новой вкладке
    const url = window.location.origin + '/?admin_view=1&tree_owner=' + encodeURIComponent(userLogin);
    console.log('[ADMIN] Opening URL:', url);
    const newWindow = window.open(url, '_blank');
    
    // Фокус на новую вкладку
    if (newWindow) {
        newWindow.focus();
    }
}

// Просмотр деталей дерева
async function viewTreeDetails(treeId) {
    const tree = treesData.find(t => String(t.id) === String(treeId));
    if (!tree) {
        console.error('[ADMIN] Дерево не найдено:', treeId, treesData);
        return;
    }

    console.log('[ADMIN] Opening tree:', tree.name, 'Persons:', Object.keys(tree.persons || {}).length);

    const modal = document.getElementById('tree-modal-overlay');
    const title = document.getElementById('modal-tree-title');
    const viewer = document.getElementById('tree-viewer');

    title.textContent = `🌳 ${tree.name} (${tree.user_login || 'владелец'})`;

    const persons = Object.values(tree.persons || {});
    if (!persons.length) {
        viewer.innerHTML = '<div class="muted">Дерево пусто</div>';
    } else {
        viewer.innerHTML = `<div style="margin-bottom:15px;font-size:13px;color:#64748b;">Персон: ${persons.length} | Браков: ${(tree.marriages || []).length}</div>` +
            persons.map(p => `
            <div class="tree-viewer-person ${p.gender === 'Женский' ? 'female' : ''}">
                <h5>${escapeHtml([p.surname, p.name, p.patronymic].filter(Boolean).join(' '))}</h5>
                <div class="meta">
                    ${p.gender} •
                    ${p.birth_date || '??'} — ${p.is_deceased ? (p.death_date || '??') : 'н.в.'}
                    ${p.birth_place ? ' • ' + p.birth_place : ''}
                </div>
            </div>
        `).join('');
    }

    modal.style.display = 'flex';
}

function closeTreeModal() {
    document.getElementById('tree-modal-overlay').style.display = 'none';
}

// Утилиты
function escapeHtml(s) {
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function formatDate(iso) {
    if (!iso) return '';
    try {
        const d = new Date(iso);
        return d.toLocaleDateString('ru-RU', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return iso;
    }
}
