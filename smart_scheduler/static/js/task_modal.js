// Shared Task Modal Logic for Tasks and Schedule Pages
// Requires Flatpickr (should be loaded in the template)

let isEditing = false;
let taskToDelete = null;

// Modal management
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    closeAllModals();
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    setTimeout(() => {
        const firstInput = modal.querySelector('input:not([type="hidden"]), textarea, select');
        if (firstInput) firstInput.focus();
    }, 100);
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.add('hidden');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    if (modalId === 'task-modal') resetTaskForm();
    if (modalId === 'delete-modal') taskToDelete = null;
}

function closeAllModals() {
    const modals = document.querySelectorAll('.modal-backdrop');
    modals.forEach(modal => {
        modal.classList.add('hidden');
        modal.style.display = 'none';
    });
    document.body.style.overflow = 'auto';
}

function resetTaskForm() {
    const form = document.getElementById('task-form');
    if (!form) return;
    form.reset();
    const elements = {
        'task-id': '',
        'task-title': '',
        'task-due-date': '',
        'task-description': '',
        'task-priority': 'medium',
        'task-category': '',
        'task-duration': ''
    };
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) element.value = value;
    });
    const modalTitle = document.getElementById('modal-title');
    const submitBtn = document.getElementById('submit-btn');
    if (modalTitle) modalTitle.textContent = 'Create New Task';
    if (submitBtn) submitBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Create Task';
    isEditing = false;
    updateCharacterCounter();
}

function updateCharacterCounter() {
    const description = document.getElementById('task-description');
    const counter = document.getElementById('description-counter');
    if (description && counter) counter.textContent = description.value.length;
}

function editTask(taskId) {
    if (!taskId) return;
    const modalTitle = document.getElementById('modal-title');
    if (modalTitle) modalTitle.textContent = 'Loading Task...';
    openModal('task-modal');
    fetch(`/api/tasks/${taskId}`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            return response.json();
        })
        .then(task => {
            isEditing = true;
            const modalTitle = document.getElementById('modal-title');
            const submitBtn = document.getElementById('submit-btn');
            if (modalTitle) modalTitle.textContent = 'Edit Task';
            if (submitBtn) submitBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Update Task';
            populateTaskForm(task);
        })
        .catch(error => {
            showToast(`Failed to load task: ${error.message}`, 'error');
            closeModal('task-modal');
        });
}

// --- Type selector and delete button logic ---
function updateModalTypeFields(type) {
    const taskFields = document.getElementById('task-fields');
    if (type === 'task') {
        taskFields.style.display = '';
    } else {
        taskFields.style.display = 'none';
    }
}

function showDeleteButton(show) {
    const btn = document.getElementById('delete-btn');
    if (btn) btn.classList.toggle('hidden', !show);
}

// --- Patch populateTaskForm to set type and show delete button ---
function populateTaskForm(task) {
    const fields = [
        { id: 'task-id', value: task.id || '', type: 'number' },
        { id: 'task-title', value: task.title || '', type: 'text' },
        { id: 'task-description', value: task.description || '', type: 'text' },
        { id: 'task-priority', value: task.priority || 'medium', type: 'select' },
        { id: 'task-category', value: task.category || '', type: 'text' },
        { id: 'task-duration', value: task.estimated_duration || '', type: 'number' }
    ];
    fields.forEach(field => {
        const element = document.getElementById(field.id);
        if (!element) return;
        if (field.type === 'number' && field.value) element.value = parseInt(field.value) || '';
        else element.value = field.value;
    });
    // Set due date using Flatpickr's setDate
    const dueDateInput = document.getElementById('task-due-date');
    if (dueDateInput && task.due_date) {
        if (dueDateInput._flatpickr) {
            dueDateInput._flatpickr.setDate(task.due_date, true, 'Y-m-d H:i');
        } else {
            dueDateInput.value = formatDateForFlatpickr(task.due_date);
        }
    } else if (dueDateInput) {
        dueDateInput.value = '';
    }
    // Set type selector
    const typeSelect = document.getElementById('task-type');
    if (typeSelect) {
        typeSelect.value = task.type || 'task';
        updateModalTypeFields(typeSelect.value);
    }
    // Show delete button if editing
    showDeleteButton(!!task.id);
    updateCharacterCounter();
    const titleField = document.getElementById('task-title');
    if (titleField) setTimeout(() => { titleField.focus(); titleField.select(); }, 200);
    // Set modal title and button for edit mode
    const modalTitle = document.getElementById('modal-title');
    const submitBtn = document.getElementById('submit-btn');
    if (task.id) {
        if (modalTitle) modalTitle.textContent = 'Edit Task';
        if (submitBtn) submitBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Update Task';
    } else {
        if (modalTitle) modalTitle.textContent = 'Create New Task';
        if (submitBtn) submitBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Create Task';
    }
}

function formatDateForFlatpickr(dateStr) {
    // Accepts ISO or string, returns 'Y-m-d H:i' for Flatpickr
    const d = new Date(dateStr);
    if (isNaN(d)) return '';
    const pad = n => n.toString().padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function isSchedulePage() {
    return window.location.pathname.includes('/schedule');
}

function showTypeSelector(show) {
    const row = document.getElementById('type-selector-row');
    if (row) row.style.display = show ? '' : 'none';
}

// --- Patch resetTaskForm to hide delete button and reset type ---
function resetTaskForm() {
    const form = document.getElementById('task-form');
    if (!form) return;
    form.reset();
    const elements = {
        'task-id': '',
        'task-title': '',
        'task-due-date': '',
        'task-description': '',
        'task-priority': 'medium',
        'task-category': '',
        'task-duration': ''
    };
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) element.value = value;
    });
    const modalTitle = document.getElementById('modal-title');
    const submitBtn = document.getElementById('submit-btn');
    if (modalTitle) modalTitle.textContent = 'Create New Task';
    if (submitBtn) submitBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Create Task';
    isEditing = false;
    // Reset type selector
    const typeSelect = document.getElementById('task-type');
    if (typeSelect) {
        typeSelect.value = 'task';
        updateModalTypeFields('task');
    }
    showDeleteButton(false);
    updateCharacterCounter();
    // Show/hide type selector based on page
    showTypeSelector(isSchedulePage());
}

// --- Patch handleTaskSubmit to use correct API for type ---
function handleTaskSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const type = formData.get('type') || 'task';
    const taskData = {
        title: formData.get('title')?.trim() || '',
        due_date: formData.get('due_date') || null,
        description: formData.get('description')?.trim() || null
    };
    if (type === 'task') {
        taskData.priority = formData.get('priority') || 'medium';
        taskData.category = formData.get('category')?.trim() || null;
        taskData.estimated_duration = parseInt(formData.get('estimated_duration')) || null;
    }
    if (!taskData.title) { showToast('Task title is required', 'error'); return; }
    if (!taskData.due_date) { showToast('Due date is required', 'error'); return; }
    const id = formData.get('task_id');
    let url = '', method = '', isEdit = !!id;
    if (type === 'task') {
        url = isEdit ? `/api/tasks/${id}` : '/api/tasks';
        method = isEdit ? 'PUT' : 'POST';
    } else {
        url = isEdit ? `/api/deadlines/${id}` : '/api/deadlines';
        method = isEdit ? 'PUT' : 'POST';
    }
    const submitBtn = document.getElementById('submit-btn');
    const originalHTML = submitBtn?.innerHTML;
    if (submitBtn) { submitBtn.disabled = true; submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...'; }
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(taskData)
    })
    .then(response => {
        if (!response.ok) { return response.text().then(text => { throw new Error(`HTTP ${response.status}: ${text}`); }); }
        return response.json();
    })
    .then(result => {
        showToast(isEdit ? (type === 'task' ? 'Task updated successfully! ✨' : 'Deadline updated! ✨') : (type === 'task' ? 'Task created! 🎉' : 'Deadline created! 🎉'), 'success');
        closeModal('task-modal');
        setTimeout(() => { window.location.reload(); }, 500);
    })
    .catch(error => {
        showToast(`Failed to save: ${error.message}`, 'error');
    })
    .finally(() => {
        if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = isEdit ? '<i class="fas fa-save mr-2"></i>Update Task' : '<i class="fas fa-save mr-2"></i>Create Task'; }
    });
}

// Toast notification (minimal)
function showToast(message, type='info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-6 right-6 z-[9999] space-y-3 max-w-sm';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `px-4 py-3 rounded-lg shadow-lg text-white mb-2 transition-all duration-300 translate-x-full ${type === 'error' ? 'bg-red-600' : type === 'success' ? 'bg-green-600' : 'bg-blue-600'}`;
    toast.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white/70 hover:text-white"><i class="fas fa-times"></i></button>
        </div>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.classList.remove('translate-x-full'), 100);
    setTimeout(() => { if (toast.parentElement) { toast.classList.add('translate-x-full'); setTimeout(() => toast.remove(), 300); } }, type === 'error' ? 8000 : 4000);
}

// Flatpickr initialization
function initFlatpickr() {
    if (window.flatpickr) {
        flatpickr('#task-due-date', {
            enableTime: true,
            dateFormat: 'Y-m-d H:i',
            altInput: true,
            altFormat: 'F j, Y h:i K',
            minDate: 'today',
            time_24hr: false
        });
    }
}

// For Tasks page: open modal for editing a task
window.openTaskEditModal = function(task) {
    isEditing = true;
    resetTaskForm();
    // Set type to 'task' and update fields
    const typeSelect = document.getElementById('task-type');
    if (typeSelect) {
        typeSelect.value = 'task';
        updateModalTypeFields('task');
    }
    // Populate form fields
    populateTaskForm({ ...task, type: 'task' });
    showDeleteButton(!!task.id);
    // Set modal title and button for edit mode
    const modalTitle = document.getElementById('modal-title');
    const submitBtn = document.getElementById('submit-btn');
    if (modalTitle) modalTitle.textContent = 'Edit Task';
    if (submitBtn) submitBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Update Task';
    // Show/hide type selector based on page
    showTypeSelector(isSchedulePage());
    openModal('task-modal');
};

document.addEventListener('DOMContentLoaded', function() {
    // Flatpickr
    initFlatpickr();
    // Character counter
    const description = document.getElementById('task-description');
    if (description) description.addEventListener('input', updateCharacterCounter);
    // Form submission
    const form = document.getElementById('task-form');
    if (form) form.addEventListener('submit', handleTaskSubmit);
    // Close modal on backdrop click
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-backdrop')) {
            const modalId = e.target.id;
            if (modalId) closeModal(modalId);
        }
    });
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'n') { e.preventDefault(); openModal('task-modal'); }
        if (e.key === 'Escape') closeAllModals();
    });
    // Type selector logic
    const typeSelect = document.getElementById('task-type');
    if (typeSelect) {
        typeSelect.addEventListener('change', function() {
            updateModalTypeFields(typeSelect.value);
        });
    }
    // Delete button logic
    const deleteBtn = document.getElementById('delete-btn');
    if (deleteBtn) {
        deleteBtn.onclick = async function() {
            const id = document.getElementById('task-id').value;
            const type = document.getElementById('task-type').value;
            if (!id) {
                console.error('Delete failed: No task id found');
                showToast('Delete failed: No task id found', 'error');
                return;
            }
            if (!confirm('Delete this ' + type + '?')) return;
            let url = '', method = 'DELETE';
            if (type === 'task') url = `/api/tasks/${id}`;
            else url = `/api/deadlines/${id}`;
            try {
                console.log(`Attempting to delete ${type} with id:`, id, 'URL:', url);
                const res = await fetch(url, { method });
                if (!res.ok) {
                    const errText = await res.text();
                    console.error('Delete failed:', errText);
                    throw new Error(errText);
                }
                showToast(type.charAt(0).toUpperCase() + type.slice(1) + ' deleted successfully!', 'success');
                closeModal('task-modal');
                setTimeout(() => window.location.reload(), 500);
            } catch (err) {
                showToast('Failed to delete: ' + err.message, 'error');
                console.error('Failed to delete:', err);
            }
        };
    }
}); 