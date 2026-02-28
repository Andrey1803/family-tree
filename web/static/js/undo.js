/**
 * Менеджер отмены/повтора действий для веб-версии.
 * Совместим с форматом данных desktop-версии.
 */

class UndoManager {
    constructor(maxSteps = 50) {
        this.maxSteps = maxSteps;
        this.undoStack = [];
        this.redoStack = [];
        this.ignoreChanges = false;
    }

    /**
     * Сохраняет текущее состояние дерева для возможной отмены.
     * Вызывается ПЕРЕД изменением данных.
     */
    saveState(treeData) {
        if (this.ignoreChanges) return;

        // Сохраняем глубокую копию состояния
        const state = {
            persons: JSON.parse(JSON.stringify(treeData.persons || {})),
            marriages: JSON.parse(JSON.stringify(treeData.marriages || [])),
            current_center: treeData.current_center,
        };

        this.undoStack.push(state);

        // Ограничиваем размер стека
        if (this.undoStack.length > this.maxSteps) {
            this.undoStack.shift();
        }

        // Очищаем redo стек при новом действии
        this.redoStack = [];

        this.onUpdate();
    }

    /**
     * Отменяет последнее действие.
     */
    undo(treeData) {
        if (this.undoStack.length === 0) {
            return false;
        }

        // Сохраняем текущее состояние для redo
        const currentState = {
            persons: JSON.parse(JSON.stringify(treeData.persons || {})),
            marriages: JSON.parse(JSON.stringify(treeData.marriages || [])),
            current_center: treeData.current_center,
        };
        this.redoStack.push(currentState);

        // Восстанавливаем предыдущее состояние
        const prevState = this.undoStack.pop();
        treeData.persons = prevState.persons;
        treeData.marriages = prevState.marriages;
        treeData.current_center = prevState.current_center;

        this.ignoreChanges = true;
        setTimeout(() => { this.ignoreChanges = false; }, 0);

        this.onUpdate();
        return true;
    }

    /**
     * Повторяет отменённое действие.
     */
    redo(treeData) {
        if (this.redoStack.length === 0) {
            return false;
        }

        // Сохраняем текущее состояние для undo
        const currentState = {
            persons: JSON.parse(JSON.stringify(treeData.persons || {})),
            marriages: JSON.parse(JSON.stringify(treeData.marriages || [])),
            current_center: treeData.current_center,
        };
        this.undoStack.push(currentState);

        // Восстанавливаем состояние из redo
        const nextState = this.redoStack.pop();
        treeData.persons = nextState.persons;
        treeData.marriages = nextState.marriages;
        treeData.current_center = nextState.current_center;

        this.ignoreChanges = true;
        setTimeout(() => { this.ignoreChanges = false; }, 0);

        this.onUpdate();
        return true;
    }

    /**
     * Проверяет, доступна ли отмена.
     */
    canUndo() {
        return this.undoStack.length > 0;
    }

    /**
     * Проверяет, доступен ли повтор.
     */
    canRedo() {
        return this.redoStack.length > 0;
    }

    /**
     * Очищает оба стека.
     */
    clear() {
        this.undoStack = [];
        this.redoStack = [];
        this.onUpdate();
    }

    /**
     * Вызывается при обновлении стеков.
     * Переопределяется для обновления UI.
     */
    onUpdate() {
        // Переопределяется внешним кодом
    }

    /**
     * Сохраняет состояние перед редактированием персоны.
     */
    beforeEdit(treeData, personId) {
        this.saveState(treeData);
    }

    /**
     * Сохраняет состояние перед добавлением персоны.
     */
    beforeAddPerson(treeData) {
        this.saveState(treeData);
    }

    /**
     * Сохраняет состояние перед удалением персоны.
     */
    beforeDeletePerson(treeData, personId) {
        this.saveState(treeData);
    }

    /**
     * Сохраняет состояние перед добавлением родственника.
     */
    beforeAddRelative(treeData) {
        this.saveState(treeData);
    }

    /**
     * Сохраняет состояние перед изменением брака.
     */
    beforeMarriageChange(treeData) {
        this.saveState(treeData);
    }
}

// Глобальный экземпляр
window.undoManager = new UndoManager(50);

/**
 * Интеграция с tree.js
 */
function setupUndoRedo() {
    const originalSaveTree = window.saveTree;
    
    if (originalSaveTree) {
        window.saveTree = function() {
            // Не сохраняем состояние при восстановлении из undo/redo
            if (window.undoManager && !window.undoManager.ignoreChanges) {
                // Сохраняем состояние перед изменением
                // Вызывается после изменения, поэтому сохраняем предыдущее состояние
            }
            return originalSaveTree.apply(this, arguments);
        };
    }

    // Обновляем меню и горячие клавиши
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
            e.preventDefault();
            if (window.undoManager && window.undoManager.canUndo()) {
                window.undoManager.undo(window.treeData);
                if (typeof window.render === 'function') {
                    window.render();
                }
                if (typeof window.saveTree === 'function') {
                    window.saveTree();
                }
                updateUndoRedoMenu();
            }
        }
        if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
            e.preventDefault();
            if (window.undoManager && window.undoManager.canRedo()) {
                window.undoManager.redo(window.treeData);
                if (typeof window.render === 'function') {
                    window.render();
                }
                if (typeof window.saveTree === 'function') {
                    window.saveTree();
                }
                updateUndoRedoMenu();
            }
        }
    });

    updateUndoRedoMenu();
}

/**
 * Обновляет состояние кнопок меню Отмена/Повтор.
 */
function updateUndoRedoMenu() {
    const undoBtn = document.querySelector('[data-action="undo"]');
    const redoBtn = document.querySelector('[data-action="redo"]');
    
    if (undoBtn) {
        undoBtn.disabled = !window.undoManager || !window.undoManager.canUndo();
        undoBtn.style.opacity = undoBtn.disabled ? '0.5' : '1';
        undoBtn.style.cursor = undoBtn.disabled ? 'not-allowed' : 'pointer';
    }
    
    if (redoBtn) {
        redoBtn.disabled = !window.undoManager || !window.undoManager.canRedo();
        redoBtn.style.opacity = redoBtn.disabled ? '0.5' : '1';
        redoBtn.style.cursor = redoBtn.disabled ? 'not-allowed' : 'pointer';
    }
}

/**
 * Обёртки для функций редактирования с поддержкой undo/redo.
 */
function wrapWithUndo(func, undoActionName) {
    return function(...args) {
        if (window.undoManager) {
            window.undoManager.saveState(window.treeData);
        }
        return func.apply(this, args);
    };
}

// Экспорт
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UndoManager, setupUndoRedo, updateUndoRedoMenu };
}
