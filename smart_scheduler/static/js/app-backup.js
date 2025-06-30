// Performance-optimized JavaScript for Jarvis AI Assistant
class JarvisApp {
    constructor() {
        this.isInitialized = false;
        this.debounceTimers = new Map();
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        // Use requestIdleCallback for non-critical initialization
        if ('requestIdleCallback' in window) {
            requestIdleCallback(() => {
                this.setupEventListeners();
                this.optimizePerformance();
                this.isInitialized = true;
            });
        } else {
            // Fallback for browsers without requestIdleCallback
            setTimeout(() => {
                this.setupEventListeners();
                this.optimizePerformance();
                this.isInitialized = true;
            }, 100);
        }
    }

    setupEventListeners() {
        // Use event delegation for better performance
        document.addEventListener('click', this.handleClicks.bind(this), { passive: false });
        document.addEventListener('keydown', this.handleKeydown.bind(this), { passive: false });
        
        // Optimize resize handling with debouncing
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        }, { passive: true });
    }

    handleClicks(e) {
        // Handle modal backdrop clicks
        if (e.target.classList.contains('modal-backdrop')) {
            this.closeAllModals();
            e.preventDefault();
        }
    }

    handleKeydown(e) {
        // Enhanced keyboard shortcuts
        if (e.key === 'Escape') {
            this.closeAllModals();
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            this.openModal('task-modal');
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const modal = document.getElementById('task-modal');
            if (modal && !modal.classList.contains('hidden')) {
                this.closeModal('task-modal');
            } else {
                this.openModal('task-modal');
            }
        }
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        // Ensure proper positioning
        modal.style.cssText = `
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            z-index: 9999 !important;
            padding: 1rem !important;
        `;
        
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Focus management
        requestAnimationFrame(() => {
            const firstInput = modal.querySelector('input:not([type="hidden"]), textarea, select');
            if (firstInput) {
                firstInput.focus();
            }
        });
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
        
        // Reset forms
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }

    closeAllModals() {
        const modals = document.querySelectorAll('.modal-backdrop:not(.hidden)');
        modals.forEach(modal => {
            modal.classList.add('hidden');
        });
        document.body.style.overflow = 'auto';
    }

    optimizePerformance() {
        // Lazy load animations with Intersection Observer
        this.setupIntersectionObserver();
        
        // Preload critical resources
        this.preloadCriticalResources();
        
        // Optimize images and lazy load
        this.optimizeImages();
    }

    setupIntersectionObserver() {
        if (!('IntersectionObserver' in window)) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    requestAnimationFrame(() => {
                        entry.target.classList.add('animate-fade-in');
                    });
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px'
        });

        // Observe elements that should animate
        document.querySelectorAll('.task-card, .stat-card, .glass').forEach(el => {
            observer.observe(el);
        });
    }

    preloadCriticalResources() {
        // Preload commonly used icons and fonts
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2';
        link.as = 'font';
        link.type = 'font/woff2';
        link.crossOrigin = 'anonymous';
        document.head.appendChild(link);
    }

    optimizeImages() {
        // Add lazy loading to images
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
        });
    }

    handleResize() {
        // Handle responsive adjustments efficiently
        const cards = document.querySelectorAll('.task-card');
        cards.forEach(card => {
            // Force reflow only if necessary
            if (card.style.transform) {
                card.style.transform = 'none';
                card.offsetHeight; // Force reflow
                card.style.transform = '';
            }
        });
    }

    // Debounced function helper
    debounce(func, wait, key) {
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }
        
        const timer = setTimeout(() => {
            func();
            this.debounceTimers.delete(key);
        }, wait);
        
        this.debounceTimers.set(key, timer);
    }

    // Optimized API request method
    async apiRequest(endpoint, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
        
        try {
            const response = await fetch(`/api${endpoint}`, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`Request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    }

    // Enhanced toast notification system
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        const colors = {
            'success': 'bg-green-600 border-green-500',
            'error': 'bg-red-600 border-red-500',
            'warning': 'bg-yellow-600 border-yellow-500',
            'info': 'bg-blue-600 border-blue-500'
        };
        
        const icons = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };
        
        toast.className = `${colors[type]} text-white px-6 py-4 rounded-xl shadow-2xl border flex items-center space-x-3 transform translate-x-full transition-all duration-300 backdrop-blur-lg max-w-sm`;
        toast.innerHTML = `
            <i class="${icons[type]}"></i>
            <span class="font-medium flex-1">${message}</span>
            <button onclick="this.remove()" class="ml-2 text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded">
                <i class="fas fa-times text-sm"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        // Animate in with requestAnimationFrame for smooth performance
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
        });
        
        // Auto remove
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.transform = 'translateX(100%)';
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }
        }, duration);
    }

    // Memory management
    cleanup() {
        // Clear all timers
        this.debounceTimers.forEach(timer => clearTimeout(timer));
        this.debounceTimers.clear();
        
        // Remove event listeners if needed
        // This would be called when navigating away or cleaning up
    }
}

// Task Management Functions (Optimized)
class TaskManager {
    constructor(app) {
        this.app = app;
        this.taskToDelete = null;
        this.isEditing = false;
    }

    async completeTask(taskId) {
        const button = document.getElementById(`complete-btn-${taskId}`);
        if (!button) return;
        
        const originalHTML = button.innerHTML;
        
        try {
            // Show loading state
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            button.disabled = true;
            
            await this.app.apiRequest(`/tasks/${taskId}/complete`, {
                method: 'PATCH'
            });
            
            this.app.showToast('Task completed successfully! 🎉', 'success');
            
            // Animate task completion
            const taskCard = button.closest('.task-card');
            if (taskCard) {
                taskCard.style.transition = 'all 0.5s ease';
                taskCard.style.opacity = '0.7';
                taskCard.style.transform = 'scale(0.98)';
            }
            
            // Reload after animation
            setTimeout(() => {
                window.location.reload();
            }, 1500);
            
        } catch (error) {
            console.error('Error completing task:', error);
            this.app.showToast('Failed to complete task. Please try again.', 'error');
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }

    async editTask(taskId) {
        try {
            this.app.showToast('Loading task details...', 'info', 2000);
            
            const task = await this.app.apiRequest(`/tasks/${taskId}`);
            
            // Set editing mode
            this.isEditing = true;
            
            // Update modal
            document.getElementById('modal-title').textContent = 'Edit Task';
            document.getElementById('submit-btn').innerHTML = '<i class="fas fa-save mr-2"></i>Update Task';
            
            // Populate form
            document.getElementById('task-id').value = task.id;
            document.getElementById('task-title').value = task.title;
            document.getElementById('task-description').value = task.description || '';
            document.getElementById('task-priority').value = task.priority;
            document.getElementById('task-category').value = task.category || '';
            document.getElementById('task-duration').value = task.estimated_duration || '';
            
            this.app.openModal('task-modal');
            
        } catch (error) {
            console.error('Error loading task:', error);
            this.app.showToast('Failed to load task details. Please try again.', 'error');
        }
    }

    deleteTask(taskId) {
        this.taskToDelete = taskId;
        this.app.openModal('delete-modal');
    }

    async confirmDeleteTask() {
        if (!this.taskToDelete) return;
        
        const deleteBtn = document.getElementById('confirm-delete-btn');
        const originalHTML = deleteBtn.innerHTML;
        
        try {
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Deleting...';
            deleteBtn.disabled = true;
            
            await this.app.apiRequest(`/tasks/${this.taskToDelete}`, {
                method: 'DELETE'
            });
            
            this.app.showToast('Task deleted successfully', 'success');
            this.app.closeModal('delete-modal');
            
            // Animate task removal
            const taskCard = document.querySelector(`[data-task-id="${this.taskToDelete}"]`);
            if (taskCard) {
                taskCard.style.transition = 'all 0.3s ease';
                taskCard.style.transform = 'scale(0) rotate(5deg)';
                taskCard.style.opacity = '0';
                setTimeout(() => taskCard.remove(), 300);
            }
            
            setTimeout(() => window.location.reload(), 1000);
            
        } catch (error) {
            console.error('Error deleting task:', error);
            this.app.showToast('Failed to delete task. Please try again.', 'error');
            deleteBtn.innerHTML = originalHTML;
            deleteBtn.disabled = false;
        }
    }

    async handleTaskSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const submitBtn = document.getElementById('submit-btn');
        const originalHTML = submitBtn.innerHTML;
        
        try {
            submitBtn.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${this.isEditing ? 'Updating...' : 'Creating...'}`;
            submitBtn.disabled = true;
            
            const taskData = {
                title: formData.get('title'),
                description: formData.get('description') || null,
                priority: formData.get('priority'),
                category: formData.get('category') || null,
                estimated_duration: parseInt(formData.get('estimated_duration')) || null
            };
            
            const taskId = formData.get('task_id');
            const url = this.isEditing ? `/tasks/${taskId}` : '/tasks';
            const method = this.isEditing ? 'PUT' : 'POST';
            
            await this.app.apiRequest(url, {
                method: method,
                body: JSON.stringify(taskData)
            });
            
            this.app.showToast(this.isEditing ? 'Task updated successfully! ✨' : 'Task created successfully! 🎉', 'success');
            
            this.app.closeModal('task-modal');
            setTimeout(() => window.location.reload(), 1500);
            
        } catch (error) {
            console.error('Error saving task:', error);
            this.app.showToast('Failed to save task. Please try again.', 'error');
            submitBtn.innerHTML = originalHTML;
            submitBtn.disabled = false;
        }
    }

    // Filter functions with debouncing
    applyFilters() {
        const status = document.getElementById('status-filter')?.value;
        const priority = document.getElementById('priority-filter')?.value;
        const category = document.getElementById('category-filter')?.value;
        const search = document.getElementById('search-input')?.value;
        
        const params = new URLSearchParams();
        if (status) params.set('status', status);
        if (priority) params.set('priority', priority);
        if (category) params.set('category', category);
        if (search) params.set('search', search);
        
        // Use replaceState to avoid adding to browser history
        const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
        window.history.replaceState({}, '', newUrl);
        window.location.reload();
    }

    handleSearch() {
        this.app.debounce(() => {
            this.applyFilters();
        }, 500, 'search');
    }
}

// Initialize the optimized app
let jarvisApp, taskManager;

document.addEventListener('DOMContentLoaded', () => {
    jarvisApp = new JarvisApp();
    taskManager = new TaskManager(jarvisApp);
    
    // Add enhanced loading animations
    const elements = document.querySelectorAll('.task-card, .stat-card');
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
});

// Global functions for backward compatibility
function openModal(modalId) {
    jarvisApp?.openModal(modalId);
}

function closeModal(modalId) {
    jarvisApp?.closeModal(modalId);
}

function closeTaskModal() {
    jarvisApp?.closeModal('task-modal');
    taskManager.isEditing = false;
}

function closeDeleteModal() {
    jarvisApp?.closeModal('delete-modal');
    taskManager.taskToDelete = null;
}

function showToast(message, type, duration) {
    jarvisApp?.showToast(message, type, duration);
}

function completeTask(taskId) {
    taskManager?.completeTask(taskId);
}

function editTask(taskId) {
    taskManager?.editTask(taskId);
}

function deleteTask(taskId) {
    taskManager?.deleteTask(taskId);
}

function confirmDeleteTask() {
    taskManager?.confirmDeleteTask();
}

function handleTaskSubmit(event) {
    taskManager?.handleTaskSubmit(event);
}

function applyFilters() {
    taskManager?.applyFilters();
}

function handleSearch() {
    taskManager?.handleSearch();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    jarvisApp?.cleanup();
});