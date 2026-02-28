/**
 * Админ-панель — Семейное древо
 * ТОЛЬКО статистика и просмотр деревьев других пользователей
 */

let usersData = [];
let treesData = [];
let currentUserId = null;

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    loadStats();
    setupSearch();
    setupRefresh();
});

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
        
    } catch (err) {
        console.error('Users error:', err);
        document.getElementById('users-table').innerHTML = '<tr><td colspan="8">Ошибка загрузки</td></tr>';
    }
}

// Рендер таблицы пользователей
function renderUsersTable(users) {
    const tbody = document.getElementById('users-table');
    if (!users.length) {
        tbody.innerHTML = '<tr><td colspan="8" class="muted">Нет пользователей</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(u => `
        <tr>
            <td>${u.id}</td>
            <td><strong>${escapeHtml(u.login)}</strong></td>
            <td>${escapeHtml(u.email || '—')}</td>
            <td>${formatDate(u.created_at)}</td>
            <td>${formatDate(u.last_login) || '—'}</td>
            <td><span class="status-${u.is_active ? 'active' : 'inactive'}">${u.is_active ? 'Активен' : 'Не активен'}</span></td>
            <td>${u.is_admin ? '👑' : '—'}</td>
            <td>
                <button class="btn-view" onclick="viewUserTrees(${u.id})">🌳 Деревья</button>
                <button class="btn-toggle ${u.is_active ? 'active' : ''}" onclick="toggleUser(${u.id})">
                    ${u.is_active ? 'Деактивировать' : 'Активировать'}
                </button>
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

// Просмотр деревьев пользователя
async function viewUserTrees(userId) {
    currentUserId = userId;
    await loadTrees(userId);
    
    // Переключение на вкладку деревьев
    document.querySelector('[data-tab="trees"]').click();
}

// Загрузка всех деревьев (для вкладки Деревья)
async function loadAllTrees() {
    try {
        // Сначала загружаем пользователей для фильтра
        if (!usersData.length) {
            await loadUsers();
        }
        
        const r = await fetch('/api/admin/trees');
        if (!r.ok) throw new Error('Ошибка загрузки деревьев');
        const data = await r.json();
        treesData = data.trees || [];
        
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
                <button class="btn-view" onclick="viewTreeDetails('${t.id}')">Просмотреть</button>
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

// Просмотр деталей дерева
async function viewTreeDetails(treeId) {
    const tree = treesData.find(t => t.id == treeId);
    if (!tree) return;
    
    const modal = document.getElementById('tree-modal-overlay');
    const title = document.getElementById('modal-tree-title');
    const viewer = document.getElementById('tree-viewer');
    
    title.textContent = `🌳 ${tree.name}`;
    
    const persons = Object.values(tree.persons || {});
    if (!persons.length) {
        viewer.innerHTML = '<div class="muted">Дерево пусто</div>';
    } else {
        viewer.innerHTML = persons.map(p => `
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
