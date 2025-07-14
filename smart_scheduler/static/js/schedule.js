// schedule.js - Calendar/Schedule Page Logic
// Requires Luxon (already included in template)

const DateTime = luxon.DateTime;

// State
let currentView = 'month'; // 'month', 'week', 'day'
let currentDate = DateTime.now();
let filters = {
    type: '',
    status: '',
    category: '',
    project_id: '',
    completed: ''
};

// DOM Elements
const calendarContainer = document.getElementById('calendar-container');
const calendarRange = document.getElementById('calendar-range');
const analyticsContainer = document.getElementById('schedule-analytics');
const remindersContainer = document.getElementById('upcoming-reminders');
const monthBtn = document.getElementById('month-view-btn');
const weekBtn = document.getElementById('week-view-btn');
const dayBtn = document.getElementById('day-view-btn');

// --- View Persistence ---
function saveCurrentView() {
    localStorage.setItem('scheduleCurrentView', currentView);
}
function loadCurrentView() {
    const v = localStorage.getItem('scheduleCurrentView');
    if (v === 'month' || v === 'week' || v === 'day') {
        currentView = v;
    }
}

// --- Button Highlighting ---
function updateViewButtons() {
    if (monthBtn && weekBtn && dayBtn) {
        monthBtn.classList.remove('btn-primary');
        monthBtn.classList.add('btn-secondary');
        weekBtn.classList.remove('btn-primary');
        weekBtn.classList.add('btn-secondary');
        dayBtn.classList.remove('btn-primary');
        dayBtn.classList.add('btn-secondary');
        if (currentView === 'month') {
            monthBtn.classList.add('btn-primary');
            monthBtn.classList.remove('btn-secondary');
        } else if (currentView === 'week') {
            weekBtn.classList.add('btn-primary');
            weekBtn.classList.remove('btn-secondary');
        } else if (currentView === 'day') {
            dayBtn.classList.add('btn-primary');
            dayBtn.classList.remove('btn-secondary');
        }
    }
}

// --- Fetch Data ---
async function fetchSchedule() {
    const {start, end} = getDateRange();
    const params = new URLSearchParams({
        start_date: start.toISO(),
        end_date: end.toISO(),
    });
    if (filters.type) params.append('type', filters.type);
    if (filters.status) params.append('status', filters.status);
    if (filters.category) params.append('category', filters.category);
    if (filters.project_id) params.append('project_id', filters.project_id);
    if (filters.completed) params.append('completed', filters.completed);
    const res = await fetch(`/api/schedule?${params.toString()}`);
    return res.json();
}

async function fetchAnalytics() {
    const res = await fetch('/api/deadlines/analytics');
    return res.json();
}

async function fetchReminders() {
    const res = await fetch('/api/notifications?upcoming=true');
    return res.json();
}

// --- Date Range Helpers ---
function getDateRange() {
    if (currentView === 'month') {
        const start = currentDate.startOf('month').startOf('week');
        const end = currentDate.endOf('month').endOf('week');
        return {start, end};
    } else if (currentView === 'week') {
        const start = currentDate.startOf('week');
        const end = currentDate.endOf('week');
        return {start, end};
    } else {
        // day
        const start = currentDate.startOf('day');
        const end = currentDate.endOf('day');
        return {start, end};
    }
}

function updateCalendarRangeLabel() {
    const {start, end} = getDateRange();
    if (currentView === 'day') {
        calendarRange.textContent = start.toFormat('DDD');
    } else {
        calendarRange.textContent = `${start.toFormat('DDD')} - ${end.toFormat('DDD')}`;
    }
}

// --- Modal Management ---
// Remove old openItemModal and closeItemModal functions entirely
// All modal logic now uses openModal('task-modal'), closeModal('task-modal'), resetTaskForm(), and populateTaskForm()

// --- Calendar Item Click Handler ---
function showItemsForDate(dateKey, items) {
    // Create a modal or popover listing all items for the date
    // Each item: title, type, edit button, delete button
    // Also: Add New button
    let modal = document.getElementById('date-items-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'date-items-modal';
        modal.className = 'modal-backdrop';
        modal.innerHTML = `<div class="modal-content bg-gray-900/95 rounded-2xl p-8 max-w-md w-full mx-4 border border-blue-500/20">
            <div class="text-center mb-4">
                <h3 class="text-xl font-bold text-white mb-2">Items for ${dateKey}</h3>
            </div>
            <div id="date-items-list"></div>
            <div class="mt-6 flex justify-center">
                <button id="add-new-item-btn" class="btn-primary">Add New</button>
                <button onclick="document.getElementById('date-items-modal').remove()" class="ml-4 px-6 py-3 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-800 transition-colors">Cancel</button>
            </div>
        </div>`;
        document.body.appendChild(modal);
    }
    const list = modal.querySelector('#date-items-list');
    list.innerHTML = '';
    items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'flex justify-between items-center mb-2 p-2 rounded bg-gray-800/60';
        div.innerHTML = `<span class="text-white">${item.title} <span class="text-xs text-gray-400">(${item.type})</span></span>
            <div>
                <button class="text-blue-400 hover:text-blue-300 p-1 mr-2" title="Edit">✏️</button>
                <button class="text-red-400 hover:text-red-300 p-1" title="Delete">🗑️</button>
            </div>`;
        // Edit button
        div.querySelector('.text-blue-400').onclick = async () => {
            let fullItem = item;
            if (item.type === 'task') {
                const res = await fetch(`/api/tasks/${item.id}`);
                if (res.ok) fullItem = await res.json();
            } else if (item.type === 'deadline') {
                const res = await fetch(`/api/deadlines/${item.id}`);
                if (res.ok) fullItem = await res.json();
            }
            isEditing = true;
            openModal('task-modal');
            populateTaskForm(fullItem);
            modal.remove();
        };
        // Delete button
        div.querySelector('.text-red-400').onclick = async () => {
            let url = item.type === 'task' ? `/api/tasks/${item.id}` : `/api/deadlines/${item.id}`;
            if (confirm(`Delete this ${item.type}?`)) {
                const res = await fetch(url, { method: 'DELETE' });
                if (res.ok) {
                    showToast(item.type.charAt(0).toUpperCase() + item.type.slice(1) + ' deleted!', 'success');
                    modal.remove();
                    setTimeout(() => window.location.reload(), 500);
                } else {
                    showToast('Failed to delete', 'error');
                }
            }
        };
        list.appendChild(div);
    });
    // Add New button
    modal.querySelector('#add-new-item-btn').onclick = () => {
        isEditing = false;
        resetTaskForm();
        // Set due date to the selected date
        const dueDateInput = document.getElementById('task-due-date');
        if (dueDateInput && dueDateInput._flatpickr) {
            dueDateInput._flatpickr.setDate(dateKey, true, 'Y-m-d');
        } else if (dueDateInput) {
            dueDateInput.value = dateKey;
        }
        // Show type selector
        const typeSelect = document.getElementById('task-type');
        if (typeSelect) typeSelect.disabled = false;
        openModal('task-modal');
        modal.remove();
    };
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// --- Calendar Rendering ---
function renderCalendar(items) {
    // Responsive container for week view
    if (currentView === 'week') {
        calendarContainer.classList.add('overflow-x-auto');
    } else {
        calendarContainer.classList.remove('overflow-x-auto');
    }
    calendarContainer.innerHTML = '';
    if (currentView === 'month') {
        const {start, end} = getDateRange();
        const itemMap = {};
        for (const item of items) {
            const dateKey = DateTime.fromISO(item.due_date).toISODate();
            if (!itemMap[dateKey]) itemMap[dateKey] = [];
            itemMap[dateKey].push(item);
        }
        const weeks = [];
        let week = [];
        let cursor = start;
        while (cursor <= end) {
            for (let i = 0; i < 7; i++) {
                week.push(cursor);
                cursor = cursor.plus({ days: 1 });
            }
            weeks.push(week);
            week = [];
        }
        const table = document.createElement('table');
        table.className = 'w-full text-sm';
        const thead = document.createElement('thead');
        thead.innerHTML = `<tr>${['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => `<th class='pb-2 text-gray-400 font-semibold'>${d}</th>`).join('')}</tr>`;
        table.appendChild(thead);
        const tbody = document.createElement('tbody');
        for (const week of weeks) {
            const tr = document.createElement('tr');
            for (const day of week) {
                const td = document.createElement('td');
                td.className = 'align-top p-1 min-w-[100px] h-[90px] relative';
                const isToday = day.hasSame(DateTime.now(), 'day');
                const isCurrentMonth = day.hasSame(currentDate, 'month');
                if (isToday) {
                    td.className += ' border-2 border-blue-400 rounded-lg';
                }
                if (!isCurrentMonth) {
                    td.className += ' opacity-40';
                }
                td.innerHTML = `<div class='text-xs font-bold mb-1 ${isToday ? 'text-blue-400' : 'text-gray-300'}'>${day.day}</div>`;
                const dateKey = day.toISODate();
                if (itemMap[dateKey]) {
                    td.style.cursor = 'pointer';
                    td.onclick = (e) => {
                        e.stopPropagation();
                        showItemsForDate(dateKey, itemMap[dateKey]);
                    };
                } else if (isCurrentMonth) {
                    td.style.cursor = 'pointer';
                    td.onclick = (e) => {
                        e.stopPropagation();
                        isEditing = false;
                        resetTaskForm();
                        document.getElementById('task-due-date').value = day.startOf('day').toFormat('yyyy-MM-dd HH:mm');
                        // Show type selector
                        const typeSelect = document.getElementById('task-type');
                        if (typeSelect) typeSelect.disabled = false;
                        openModal('task-modal');
                    };
                }
                tr.appendChild(td);
            }
            tbody.appendChild(tr);
        }
        table.appendChild(tbody);
        calendarContainer.appendChild(table);
        return;
    }
    // ... (week and day view rendering can be restored similarly if needed) ...
}

// --- Render Analytics ---
function renderAnalytics(stats) {
    analyticsContainer.innerHTML = '';
    if (!stats) return;
    analyticsContainer.innerHTML = `
        <div>Total: <span class="font-bold text-white">${stats.total}</span></div>
        <div>Completed: <span class="text-green-400 font-bold">${stats.completed}</span></div>
        <div>Overdue: <span class="text-red-400 font-bold">${stats.overdue}</span></div>
        <div>Upcoming: <span class="text-blue-400 font-bold">${stats.upcoming}</span></div>
    `;
}

// --- Render Reminders ---
function renderReminders(reminders) {
    remindersContainer.innerHTML = '';
    if (!reminders.length) {
        remindersContainer.innerHTML = '<div class="text-gray-400 text-center">No upcoming reminders.</div>';
        return;
    }
    for (const n of reminders) {
        const div = document.createElement('div');
        div.className = 'glass p-3 flex items-center gap-3';
        div.innerHTML = `
            <i class="fas fa-bell text-yellow-400"></i>
            <span>${n.message}</span>
            <span class="text-xs text-gray-400 ml-auto">${DateTime.fromISO(n.scheduled_time).toFormat('ff')}</span>
        `;
        remindersContainer.appendChild(div);
    }
}

// --- Event Handlers ---
function setupEventHandlers() {
    monthBtn.onclick = () => { currentView = 'month'; saveCurrentView(); updateViewButtons(); refresh(); };
    weekBtn.onclick = () => { currentView = 'week'; saveCurrentView(); updateViewButtons(); refresh(); };
    dayBtn.onclick = () => { currentView = 'day'; saveCurrentView(); updateViewButtons(); refresh(); };
    document.getElementById('apply-filters-btn').onclick = () => {
        filters.type = document.getElementById('type-filter').value;
        filters.status = document.getElementById('status-filter').value;
        filters.category = document.getElementById('category-filter').value;
        filters.project_id = document.getElementById('project-filter').value;
        filters.completed = document.getElementById('completed-filter').value;
        refresh();
    };
    document.getElementById('prev-btn').onclick = () => {
        if (currentView === 'month') {
            currentDate = currentDate.minus({ months: 1 });
        } else if (currentView === 'week') {
            currentDate = currentDate.minus({ weeks: 1 });
        } else {
            currentDate = currentDate.minus({ days: 1 });
        }
        refresh();
    };
    document.getElementById('next-btn').onclick = () => {
        if (currentView === 'month') {
            currentDate = currentDate.plus({ months: 1 });
        } else if (currentView === 'week') {
            currentDate = currentDate.plus({ weeks: 1 });
        } else {
            currentDate = currentDate.plus({ days: 1 });
        }
        refresh();
    };
    document.getElementById('today-btn').onclick = () => {
        currentDate = DateTime.now();
        refresh();
    };
}

// --- Main Refresh ---
async function refresh() {
    updateViewButtons();
    updateCalendarRangeLabel();
    const [items, stats, reminders] = await Promise.all([
        fetchSchedule(),
        fetchAnalytics(),
        fetchReminders()
    ]);
    renderCalendar(items);
    renderAnalytics(stats);
    renderReminders(reminders);
}

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    loadCurrentView();
    setupEventHandlers();
    updateViewButtons();
    refresh();
});

// --- Modal Form Submission with API Integration ---
document.getElementById('item-form').onsubmit = async function(e) {
    e.preventDefault();
    const id = document.getElementById('item-id').value;
    const type = document.getElementById('item-type').value;
    const title = document.getElementById('item-title').value.trim();
    const dueDate = document.getElementById('item-due-date').value;
    const description = document.getElementById('item-description').value.trim();
    const color = document.getElementById('item-color').value;
    const recurrence = document.getElementById('item-recurrence').value;
    const completed = document.getElementById('item-completed').checked;
    if (!title || !dueDate) {
        alert('Title and due date are required.');
        return;
    }
    const data = {
        title,
        due_date: new Date(dueDate).toISOString(),
        description,
        color,
        recurrence,
        completed
    };
    let url = '', method = '', isEdit = !!id;
    if (type === 'task') {
        url = isEdit ? `/api/tasks/${id}` : '/api/tasks';
        method = isEdit ? 'PUT' : 'POST';
        data.priority = 'medium'; // Default, can be enhanced
        data.status = completed ? 'completed' : 'pending';
    } else {
        url = isEdit ? `/api/deadlines/${id}` : '/api/deadlines';
        method = isEdit ? 'PUT' : 'POST';
        data.type = 'general'; // Default, can be enhanced
    }
    try {
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error(await res.text());
        closeModal('task-modal');
        refresh();
    } catch (err) {
        alert('Failed to save: ' + err.message);
    }
}; 