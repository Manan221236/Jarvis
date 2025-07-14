// ===================================================================
// JARVIS AI Assistant - Complete JavaScript Application
// Modern, performant, and accessible frontend functionality
// ===================================================================

class JarvisApp {
    constructor() {
        this.isEditing = false;
        this.taskToDelete = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeModals();
        this.setupKeyboardShortcuts();
        this.addRippleEffects();
        console.log('🤖 JARVIS AI Assistant initialized successfully');
    }

    // ===================================================================
    // EVENT BINDING
    // ===================================================================

    bindEvents() {
        // Click event delegation
        document.addEventListener('click', this.handleClicks.bind(this), { passive: false });
        
        // Form submissions
        document.addEventListener('submit', this.handleFormSubmit.bind(this), { passive: false });
        
        // Keyboard events
        document.addEventListener('keydown', this.handleKeydown.bind(this), { passive: false });
        
        // Optimize resize handling with debouncing
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        }, { passive: true });

        // Initialize character counters
        this.initializeCharacterCounters();
    }

    handleClicks(e) {
        // Handle data-action clicks
        const actionElement = e.target.closest('[data-action]');
        if (actionElement) {
            const action = actionElement.getAttribute('data-action');
            const taskId = actionElement.getAttribute('data-task-id');
            
            e.preventDefault();
            
            switch (action) {
                case 'open-task-modal':
                    this.openModal('task-modal');
                    break;
                case 'close-task-modal':
                    this.closeTaskModal();
                    break;
                case 'close-delete-modal':
                    this.closeDeleteModal();
                    break;
                case 'complete':
                    if (taskId) this.completeTask(taskId);
                    break;
                case 'edit':
                    if (taskId) this.editTask(taskId);
                    break;
                case 'delete':
                    if (taskId) this.deleteTask(taskId);
                    break;
                case 'confirm-delete':
                    this.confirmDeleteTask();
                    break;
            }
            return;
        }

        // Handle modal backdrop clicks
        if (e.target.classList.contains('modal-backdrop')) {
            this.closeAllModals();
            e.preventDefault();
        }
    }

    handleKeydown(e) {
        // Enhanced keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch (e.key.toLowerCase()) {
                case 'n':
                    e.preventDefault();
                    this.openModal('task-modal');
                    break;
                case '/':
                    e.preventDefault();
                    this.showToast('Keyboard Shortcuts: Ctrl+N (New Task), Escape (Close Modal)', 'info', 5000);
                    break;
            }
        }

        // Escape key handling
        if (e.key === 'Escape') {
            this.closeAllModals();
        }

        // Enter key in search inputs
        if (e.key === 'Enter' && e.target.id === 'search-input') {
            e.preventDefault();
            this.applyFilters();
        }
    }

    handleFormSubmit(e) {
        // Handle task form submission
        if (e.target.id === 'task-form') {
            e.preventDefault();
            this.handleTaskSubmit(e);
        }
    }

    handleResize() {
        // Responsive adjustments
        this.adjustModalSizing();
    }

    // ===================================================================
    // MODAL MANAGEMENT
    // ===================================================================

    initializeModals() {
        // Ensure all modals are properly hidden on initialization
        document.querySelectorAll('.modal-backdrop').forEach(modal => {
            modal.classList.add('hidden');
            modal.style.display = 'none';
        });

        // Add modal observers for focus management
        this.setupModalObservers();
    }

    setupModalObservers() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const modal = mutation.target;
                    if (!modal.classList.contains('hidden')) {
                        this.focusFirstInput(modal);
                    }
                }
            });
        });

        document.querySelectorAll('.modal-backdrop').forEach(modal => {
            observer.observe(modal, { attributes: true });
        });
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Modal ${modalId} not found`);
            return;
        }

        // Close any other open modals first
        this.closeAllModals();

        // Show the modal
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        // Focus management
        setTimeout(() => this.focusFirstInput(modal), 150);

        console.log(`📱 Modal ${modalId} opened`);
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        modal.classList.add('hidden');
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';

        console.log(`📱 Modal ${modalId} closed`);
    }

    closeAllModals() {
        const modals = document.querySelectorAll('.modal-backdrop:not(.hidden)');
        modals.forEach(modal => {
            modal.classList.add('hidden');
            modal.style.display = 'none';
        });
        document.body.style.overflow = 'auto';

        // Reset any modal-specific state
        this.resetTaskForm();
        this.taskToDelete = null;
    }

    closeTaskModal() {
        this.closeModal('task-modal');
        this.resetTaskForm();
    }

    closeDeleteModal() {
        this.closeModal('delete-modal');
        this.taskToDelete = null;
    }

    focusFirstInput(modal) {
        const firstInput = modal.querySelector('input, textarea, select, button');
        if (firstInput) {
            firstInput.focus();
        }
    }

    adjustModalSizing() {
        // Responsive modal adjustments
        const modals = document.querySelectorAll('.modal-content');
        modals.forEach(modal => {
            if (window.innerWidth < 768) {
                modal.style.maxHeight = 'calc(100vh - 2rem)';
                modal.style.margin = '1rem';
            } else {
                modal.style.maxHeight = '90vh';
                modal.style.margin = 'auto';
            }
        });
    }

    // ===================================================================
    // TASK MANAGEMENT
    // ===================================================================

    resetTaskForm() {
        const form = document.getElementById('task-form');
        if (!form) return;

        form.reset();
        
        // Reset form elements
        const elements = {
            'task-id': '',
            'task-title': '',
            'task-due-date': '',
            'modal-title': 'Create New Task',
            'submit-btn': '<i class="fas fa-save mr-2"></i>Create Task'
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                    element.value = value;
                } else {
                    element.innerHTML = value;
                }
            }
        });

        this.isEditing = false;
        this.updateCharacterCounters();
    }

    async handleTaskSubmit(event) {
        const formData = new FormData(event.target);
        const dueDateRaw = formData.get('due_date');
        const dueDate = dueDateRaw ? new Date(dueDateRaw).toISOString() : null;
        const taskData = {
            title: formData.get('title'),
            due_date: dueDate, // Add due_date to payload
            description: formData.get('description') || null,
            priority: formData.get('priority'),
            category: formData.get('category') || null,
            estimated_duration: parseInt(formData.get('estimated_duration')) || null
        };

        try {
            const taskId = formData.get('task_id');
            const url = this.isEditing ? `/api/tasks/${taskId}` : '/api/tasks';
            const method = this.isEditing ? 'PUT' : 'POST';

            await this.apiRequest(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData)
            });

            this.showToast(
                this.isEditing ? 'Task updated successfully! ✨' : 'Task created successfully! 🎉',
                'success'
            );
            this.closeTaskModal();
            setTimeout(() => window.location.reload(), 1000);

        } catch (error) {
            console.error('Error saving task:', error);
            this.showToast('Failed to save task. Please try again.', 'error');
        }
    }

    async editTask(taskId) {
        try {
            const task = await this.apiRequest(`/api/tasks/${taskId}`);

            this.isEditing = true;
            document.getElementById('modal-title').textContent = 'Edit Task';
            document.getElementById('submit-btn').innerHTML = '<i class="fas fa-save mr-2"></i>Update Task';

            // Populate form fields
            const fields = {
                'task-id': task.id,
                'task-title': task.title,
                'task-due-date': task.due_date ? new Date(task.due_date).toISOString().slice(0, 16) : '',
                'task-description': task.description || '',
                'task-priority': task.priority,
                'task-category': task.category || '',
                'task-duration': task.estimated_duration || ''
            };

            Object.entries(fields).forEach(([id, value]) => {
                const element = document.getElementById(id);
                if (element) element.value = value;
            });

            this.updateCharacterCounters();
            this.openModal('task-modal');

        } catch (error) {
            console.error('Error loading task:', error);
            this.showToast('Failed to load task details. Please try again.', 'error');
        }
    }

    deleteTask(taskId) {
        this.taskToDelete = taskId;
        this.openModal('delete-modal');
    }

    async confirmDeleteTask() {
        if (!this.taskToDelete) return;

        const deleteBtn = document.getElementById('confirm-delete-btn');
        const originalHTML = deleteBtn.innerHTML;

        try {
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Deleting...';
            deleteBtn.disabled = true;

            await this.apiRequest(`/api/tasks/${this.taskToDelete}`, {
                method: 'DELETE'
            });

            this.showToast('Task deleted successfully', 'success');
            this.closeDeleteModal();

            // Animate task removal
            const taskCard = document.querySelector(`[data-task-id="${this.taskToDelete}"]`);
            if (taskCard) {
                taskCard.style.transition = 'all 0.3s ease';
                taskCard.style.transform = 'scale(0) rotate(5deg)';
                taskCard.style.opacity = '0';
                setTimeout(() => taskCard.remove(), 300);
            }

            this.taskToDelete = null;
            setTimeout(() => window.location.reload(), 1000);

        } catch (error) {
            console.error('Error deleting task:', error);
            this.showToast('Failed to delete task. Please try again.', 'error');
        } finally {
            deleteBtn.innerHTML = originalHTML;
            deleteBtn.disabled = false;
        }
    }

    async completeTask(taskId) {
        try {
            await this.apiRequest(`/api/tasks/${taskId}/complete`, {
                method: 'PATCH'
            });

            this.showToast('Task completed! 🎉', 'success');

            // Animate completion
            const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
            if (taskCard) {
                taskCard.style.transition = 'all 0.5s ease';
                taskCard.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                taskCard.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    taskCard.style.transform = 'scale(1)';
                }, 200);
            }

            setTimeout(() => window.location.reload(), 1500);

        } catch (error) {
            console.error('Error completing task:', error);
            this.showToast('Failed to complete task. Please try again.', 'error');
        }
    }

    // ===================================================================
    // FILTERING & SEARCH
    // ===================================================================

    applyFilters() {
        const params = new URLSearchParams();

        const filters = {
            search: document.getElementById('search-input')?.value,
            status: document.getElementById('status-filter')?.value,
            priority: document.getElementById('priority-filter')?.value,
            category: document.getElementById('category-filter')?.value
        };

        Object.entries(filters).forEach(([key, value]) => {
            if (value) params.append(key, value);
        });

        window.location.href = `/tasks?${params.toString()}`;
    }

    // ===================================================================
    // UI ENHANCEMENTS
    // ===================================================================

    initializeCharacterCounters() {
        const textareas = document.querySelectorAll('textarea[maxlength]');
        textareas.forEach(textarea => {
            const counter = document.getElementById(textarea.id.replace('task-', '') + '-counter');
            if (counter) {
                textarea.addEventListener('input', () => {
                    counter.textContent = textarea.value.length;
                    
                    // Visual feedback for character limits
                    const maxLength = parseInt(textarea.getAttribute('maxlength'));
                    const percentage = (textarea.value.length / maxLength) * 100;
                    
                    counter.className = percentage > 90 ? 'text-red-400' : 
                                       percentage > 75 ? 'text-yellow-400' : 'text-gray-500';
                });
            }
        });
    }

    updateCharacterCounters() {
        const textareas = document.querySelectorAll('textarea[maxlength]');
        textareas.forEach(textarea => {
            const event = new Event('input');
            textarea.dispatchEvent(event);
        });
    }

    addRippleEffects() {
        // Add ripple effect to buttons
        document.addEventListener('click', function(e) {
            const button = e.target.closest('button, .btn-primary, .btn-secondary, .btn-danger');
            if (!button) return;

            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.3);
                transform: scale(0);
                left: ${x}px;
                top: ${y}px;
                width: ${size}px;
                height: ${size}px;
                animation: ripple 0.6s linear;
                pointer-events: none;
                z-index: 1;
            `;

            // Ensure button has relative positioning
            const originalPosition = getComputedStyle(button).position;
            if (originalPosition === 'static') {
                button.style.position = 'relative';
            }
            button.style.overflow = 'hidden';

            button.appendChild(ripple);

            setTimeout(() => {
                ripple.remove();
                // Restore original position if it was static
                if (originalPosition === 'static') {
                    button.style.position = '';
                }
            }, 600);
        });
    }

    setupKeyboardShortcuts() {
        // Additional keyboard shortcuts can be added here
        document.addEventListener('keydown', (e) => {
            // Alt + T for tasks page
            if (e.altKey && e.key.toLowerCase() === 't') {
                e.preventDefault();
                window.location.href = '/tasks';
            }
            
            // Alt + D for dashboard
            if (e.altKey && e.key.toLowerCase() === 'd') {
                e.preventDefault();
                window.location.href = '/';
            }
        });
    }

    // ===================================================================
    // UTILITY FUNCTIONS
    // ===================================================================

    async apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    showToast(message, type = 'info', duration = 4000) {
        const container = this.getToastContainer();
        const toast = document.createElement('div');

        const colors = {
            success: 'bg-green-600 border-green-500',
            error: 'bg-red-600 border-red-500',
            warning: 'bg-yellow-600 border-yellow-500',
            info: 'bg-blue-600 border-blue-500'
        };

        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        toast.className = `${colors[type]} text-white px-6 py-4 rounded-xl shadow-lg border backdrop-blur-xl flex items-center space-x-3 transform translate-x-full transition-all duration-300`;
        toast.innerHTML = `
            <i class="${icons[type]} flex-shrink-0"></i>
            <span class="font-medium">${message}</span>
            <button onclick="this.parentElement.remove()" class="ml-auto text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(toast);

        // Animate in
        setTimeout(() => toast.classList.remove('translate-x-full'), 100);

        // Auto remove
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('translate-x-full');
                setTimeout(() => toast.remove(), 300);
            }
        }, duration);
    }

    getToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'fixed top-6 right-6 z-[9999] space-y-3 max-w-sm';
            document.body.appendChild(container);
        }
        return container;
    }

    formatDuration(minutes) {
        if (!minutes) return 'Not set';
        if (minutes < 60) return `${minutes}m`;
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return mins ? `${hours}h ${mins}m` : `${hours}h`;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Copied to clipboard!', 'success', 2000);
        }).catch(() => {
            this.showToast('Failed to copy to clipboard', 'error');
        });
    }
}

// ===================================================================
// GLOBAL INITIALIZATION
// ===================================================================

// Initialize the application
let jarvisApp;

document.addEventListener('DOMContentLoaded', () => {
    jarvisApp = new JarvisApp();
});

// ===================================================================
// GLOBAL FUNCTIONS FOR BACKWARD COMPATIBILITY
// ===================================================================

function openModal(modalId) {
    jarvisApp?.openModal(modalId);
}

function closeModal(modalId) {
    jarvisApp?.closeModal(modalId);
}

function closeTaskModal() {
    jarvisApp?.closeTaskModal();
}

function closeDeleteModal() {
    jarvisApp?.closeDeleteModal();
}

function showToast(message, type, duration) {
    jarvisApp?.showToast(message, type, duration);
}

function completeTask(taskId) {
    jarvisApp?.completeTask(taskId);
}

function editTask(taskId) {
    jarvisApp?.editTask(taskId);
}

function deleteTask(taskId) {
    jarvisApp?.deleteTask(taskId);
}

function confirmDeleteTask() {
    jarvisApp?.confirmDeleteTask();
}

function handleTaskSubmit(event) {
    jarvisApp?.handleTaskSubmit(event);
}

function applyFilters() {
    jarvisApp?.applyFilters();
}

function copyToClipboard(text) {
    jarvisApp?.copyToClipboard(text);
}

// ===================================================================
// ERROR HANDLING AND PERFORMANCE MONITORING
// ===================================================================

// Global error handler
window.addEventListener('error', function(e) {
    console.error('💥 Unhandled error:', e.error);
    if (jarvisApp) {
        jarvisApp.showToast('An unexpected error occurred. Please refresh the page.', 'error', 8000);
    }
});

// Promise rejection handler
window.addEventListener('unhandledrejection', function(e) {
    console.error('💥 Unhandled promise rejection:', e.reason);
    if (jarvisApp) {
        jarvisApp.showToast('An error occurred while processing your request.', 'error', 5000);
    }
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', () => {
        setTimeout(() => {
            const perfData = performance.getEntriesByType('navigation')[0];
            console.log(`🚀 Page loaded in ${Math.round(perfData.loadEventEnd - perfData.fetchStart)}ms`);
        }, 0);
    });
}

// ===================================================================
// CSS ANIMATIONS KEYFRAMES (if not in CSS)
// ===================================================================

// Add ripple animation if not defined in CSS
if (!document.querySelector('style[data-ripple]')) {
    const style = document.createElement('style');
    style.setAttribute('data-ripple', 'true');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}