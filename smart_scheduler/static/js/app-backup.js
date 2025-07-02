// ===================================================================
// JARVIS AI Assistant - Complete JavaScript Application
// Drop-in replacement for app.js
// ===================================================================

'use strict';

// Global Configuration
const CONFIG = {
    API_BASE_URL: '/api',
    TOAST_DURATION: 4000,
    ANIMATION_DELAY: 100,
    MAX_DESCRIPTION_LENGTH: 1000,
    MIN_TITLE_LENGTH: 3,
    MAX_TITLE_LENGTH: 100
};

// Global Variables
let isEditing = false;
let taskToDelete = null;
let currentTasks = [];
let isLoading = false;

// ===================================================================
// JARVIS APP CLASS - Main Application Controller
// ===================================================================

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
                console.log('🤖 JARVIS AI Assistant initialized successfully');
            });
        } else {
            // Fallback for browsers without requestIdleCallback
            setTimeout(() => {
                this.setupEventListeners();
                this.optimizePerformance();
                this.isInitialized = true;
                console.log('🤖 JARVIS AI Assistant initialized successfully');
            }, 100);
        }
    }

    setupEventListeners() {
        // Use event delegation for better performance
        document.addEventListener('click', this.handleClicks.bind(this), { passive: false });
        document.addEventListener('keydown', this.handleKeydown.bind(this), { passive: false });
        document.addEventListener('submit', this.handleFormSubmit.bind(this), { passive: false });
        
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

        // Enter to submit forms in modals
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            const activeModal = document.querySelector('.modal-backdrop:not(.hidden)');
            if (activeModal) {
                const form = activeModal.querySelector('form');
                if (form) {
                    e.preventDefault();
                    form.dispatchEvent(new Event('submit'));
                }
            }
        }
    }

    handleFormSubmit(e) {
        if (e.target.id === 'task-form') {
            e.preventDefault();
            this.handleTaskSubmit(e);
        }
    }

    handleResize() {
        // Handle responsive adjustments if needed
        const modals = document.querySelectorAll('.modal-backdrop:not(.hidden)');
        modals.forEach(modal => {
            // Ensure modals remain properly positioned on resize
            this.ensureModalPositioning(modal);
        });
    }

    // ===================================================================
    // MODAL MANAGEMENT
    // ===================================================================

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Modal ${modalId} not found`);
            return;
        }
        
        // Ensure proper positioning
        this.ensureModalPositioning(modal);
        
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Focus management
        setTimeout(() => {
            const firstInput = modal.querySelector('input, textarea, select, button');
            if (firstInput) {
                firstInput.focus();
            }
        }, 150);
        
        console.log(`📱 Modal ${modalId} opened`);
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
        
        console.log(`📱 Modal ${modalId} closed`);
    }

    closeAllModals() {
        const modals = document.querySelectorAll('.modal-backdrop:not(.hidden)');
        modals.forEach(modal => {
            modal.classList.add('hidden');
        });
        document.body.style.overflow = 'auto';
        
        // Reset any modal-specific state
        this.resetTaskForm();
        taskToDelete = null;
    }

    ensureModalPositioning(modal) {
        // Ensure modal is properly centered and covers full viewport
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
    }

    closeTaskModal() {
        this.closeModal('task-modal');
        this.resetTaskForm();
    }

    closeDeleteModal() {
        this.closeModal('delete-modal');
        taskToDelete = null;
    }

    resetTaskForm() {
        const form = document.getElementById('task-form');
        if (form) {
            form.reset();
        }
        
        // Reset form state
        isEditing = false;
        const modalTitle = document.getElementById('modal-title');
        const submitBtn = document.getElementById('submit-btn');
        const counter = document.getElementById('description-counter');
        
        if (modalTitle) modalTitle.textContent = 'Create New Task';
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-plus mr-2"></i>Create Task';
            submitBtn.disabled = false;
        }
        if (counter) {
            counter.textContent = '0';
            counter.className = 'text-gray-500';
        }
        
        // Clear validation states
        const inputs = form?.querySelectorAll('input, textarea, select');
        inputs?.forEach(input => {
            input.setCustomValidity('');
            input.classList.remove('error');
        });
    }

    // ===================================================================
    // API COMMUNICATION
    // ===================================================================

    async apiRequest(endpoint, options = {}) {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        const controller = new AbortController();
        
        // Set timeout
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                signal: controller.signal,
                ...options
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    }

    // ===================================================================
    // TASK MANAGEMENT
    // ===================================================================

    async completeTask(taskId) {
        const button = document.querySelector(`[data-task-id="${taskId}"][data-action="complete"]`);
        if (!button) return;
        
        const originalHTML = button.innerHTML;
        
        try {
            // Show loading state
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            button.disabled = true;
            
            await this.apiRequest(`/tasks/${taskId}/complete`, {
                method: 'PATCH'
            });
            
            this.showToast('Task completed successfully! 🎉', 'success');
            
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
            this.showToast('Failed to complete task. Please try again.', 'error');
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }

    async editTask(taskId) {
        try {
            this.showToast('Loading task details...', 'info', 2000);
            
            const task = await this.apiRequest(`/tasks/${taskId}`);
            
            // Set editing mode
            isEditing = true;
            
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
            
            // Update character counter
            const descriptionTextarea = document.getElementById('task-description');
            const counter = document.getElementById('description-counter');
            if (descriptionTextarea && counter) {
                const length = descriptionTextarea.value.length;
                counter.textContent = length;
                counter.className = length > 800 ? 'text-red-400' : 
                                   length > 600 ? 'text-yellow-400' : 'text-gray-500';
            }
            
            this.openModal('task-modal');
            
        } catch (error) {
            console.error('Error loading task:', error);
            this.showToast('Failed to load task details. Please try again.', 'error');
        }
    }

    deleteTask(taskId) {
        taskToDelete = taskId;
        this.openModal('delete-modal');
    }

    async confirmDeleteTask() {
        if (!taskToDelete) return;
        
        const deleteBtn = document.getElementById('confirm-delete-btn');
        const originalHTML = deleteBtn.innerHTML;
        
        try {
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Deleting...';
            deleteBtn.disabled = true;
            
            await this.apiRequest(`/tasks/${taskToDelete}`, {
                method: 'DELETE'
            });
            
            this.showToast('Task deleted successfully', 'success');
            this.closeModal('delete-modal');
            
            // Animate task removal
            const taskCard = document.querySelector(`[data-task-id="${taskToDelete}"]`);
            if (taskCard) {
                taskCard.style.transition = 'all 0.3s ease';
                taskCard.style.transform = 'scale(0) rotate(5deg)';
                taskCard.style.opacity = '0';
                setTimeout(() => taskCard.remove(), 300);
            }
            
            taskToDelete = null;
            setTimeout(() => window.location.reload(), 1000);
            
        } catch (error) {
            console.error('Error deleting task:', error);
            this.showToast('Failed to delete task. Please try again.', 'error');
            deleteBtn.innerHTML = originalHTML;
            deleteBtn.disabled = false;
        }
    }

    // ===================================================================
    // FORM HANDLING
    // ===================================================================

    async handleTaskSubmit(event) {
        event.preventDefault();
        
        if (isLoading) return;
        
        const form = event.target;
        const formData = new FormData(form);
        
        // Extract form data
        const taskData = {
            title: formData.get('title')?.trim() || document.getElementById('task-title')?.value?.trim(),
            description: formData.get('description')?.trim() || document.getElementById('task-description')?.value?.trim(),
            priority: formData.get('priority') || document.getElementById('task-priority')?.value || 'medium',
            category: formData.get('category') || document.getElementById('task-category')?.value || '',
            estimated_duration: parseInt(formData.get('estimated_duration') || document.getElementById('task-duration')?.value) || null
        };
        
        // Validate data
        const validation = this.validateTaskData(taskData);
        if (!validation.isValid) {
            this.showToast(validation.message, 'error');
            return;
        }
        
        // Set loading state
        this.setSubmitButtonLoading(true);
        isLoading = true;
        
        try {
            const taskId = document.getElementById('task-id')?.value;
            const method = isEditing && taskId ? 'PUT' : 'POST';
            const endpoint = isEditing && taskId ? `/tasks/${taskId}` : '/tasks';
            
            const response = await this.apiRequest(endpoint, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(taskData)
            });
            
            this.showToast(
                isEditing ? 'Task updated successfully! ✨' : 'Task created successfully! 🎉', 
                'success'
            );
            
            this.closeTaskModal();
            
            // Refresh page after delay
            setTimeout(() => {
                window.location.reload();
            }, 1500);
            
        } catch (error) {
            console.error('Error saving task:', error);
            this.showToast('Failed to save task. Please try again.', 'error');
        } finally {
            this.setSubmitButtonLoading(false);
            isLoading = false;
        }
    }

    validateTaskData(data) {
        if (!data.title) {
            return { isValid: false, message: 'Task title is required' };
        }
        
        if (data.title.length < CONFIG.MIN_TITLE_LENGTH) {
            return { isValid: false, message: `Title must be at least ${CONFIG.MIN_TITLE_LENGTH} characters long` };
        }
        
        if (data.title.length > CONFIG.MAX_TITLE_LENGTH) {
            return { isValid: false, message: `Title must be less than ${CONFIG.MAX_TITLE_LENGTH} characters` };
        }
        
        if (data.description && data.description.length > CONFIG.MAX_DESCRIPTION_LENGTH) {
            return { isValid: false, message: `Description must be less than ${CONFIG.MAX_DESCRIPTION_LENGTH} characters` };
        }
        
        if (data.estimated_duration && (data.estimated_duration < 5 || data.estimated_duration > 480)) {
            return { isValid: false, message: 'Duration must be between 5 minutes and 8 hours' };
        }
        
        return { isValid: true };
    }

    setSubmitButtonLoading(loading) {
        const submitBtn = document.getElementById('submit-btn');
        if (!submitBtn) return;
        
        if (loading) {
            submitBtn.dataset.originalHtml = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
            submitBtn.disabled = true;
        } else {
            submitBtn.innerHTML = submitBtn.dataset.originalHtml || 
                                 '<i class="fas fa-plus mr-2"></i>Create Task';
            submitBtn.disabled = false;
            delete submitBtn.dataset.originalHtml;
        }
    }

    // ===================================================================
    // UI ENHANCEMENTS
    // ===================================================================

    showToast(message, type = 'info', duration = CONFIG.TOAST_DURATION) {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.toast');
        existingToasts.forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.className = `toast fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg transform transition-all duration-300 max-w-sm translate-x-full opacity-0`;
        
        // Style based on type
        const styles = {
            success: 'bg-green-600 border border-green-500 text-white',
            error: 'bg-red-600 border border-red-500 text-white',
            warning: 'bg-yellow-600 border border-yellow-500 text-white',
            info: 'bg-blue-600 border border-blue-500 text-white'
        };
        
        toast.className += ` ${styles[type] || styles.info}`;
        
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        const icon = icons[type] || icons.info;
        
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${icon} mr-3 text-lg"></i>
                <span class="font-medium">${this.escapeHtml(message)}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white/70 hover:text-white transition-colors">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Add to DOM
        document.body.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
            toast.style.opacity = '1';
        });

        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                toast.style.transform = 'translateX(100%)';
                toast.style.opacity = '0';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 300);
            }, duration);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ===================================================================
    // PERFORMANCE OPTIMIZATIONS
    // ===================================================================

    optimizePerformance() {
        // Debounce utility
        this.debounce = (func, wait, immediate) => {
            return (...args) => {
                const later = () => {
                    this.debounceTimers.delete(func);
                    if (!immediate) func.apply(this, args);
                };
                const callNow = immediate && !this.debounceTimers.has(func);
                clearTimeout(this.debounceTimers.get(func));
                this.debounceTimers.set(func, setTimeout(later, wait));
                if (callNow) func.apply(this, args);
            };
        };

        // Initialize animations with performance considerations
        this.initializeAnimations();
        
        // Setup character counters and form validation
        this.initializeFormValidation();
    }

    initializeAnimations() {
        // Staggered animations for cards
        const animatedElements = document.querySelectorAll('.task-card, .stat-card, .action-btn');
        
        animatedElements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * CONFIG.ANIMATION_DELAY);
        });

        // Initialize progress bars
        this.initializeProgressBars();
    }

    initializeProgressBars() {
        const progressElements = document.querySelectorAll('.progress-fill');
        
        progressElements.forEach((element, index) => {
            const progress = element.getAttribute('data-progress') || 
                            element.style.width?.replace('%', '') || 0;
            
            // Reset width for animation
            element.style.width = '0%';
            
            // Animate to target width
            setTimeout(() => {
                element.style.transition = 'width 1s ease-out';
                element.style.width = `${progress}%`;
            }, index * CONFIG.ANIMATION_DELAY);
        });
    }

    initializeFormValidation() {
        const descriptionTextarea = document.getElementById('task-description');
        const counter = document.getElementById('description-counter');
        const titleInput = document.getElementById('task-title');
        
        if (descriptionTextarea && counter) {
            descriptionTextarea.addEventListener('input', (e) => {
                const length = e.target.value.length;
                counter.textContent = length;
                
                // Update counter color based on length
                counter.className = length > 800 ? 'text-red-400' : 
                                   length > 600 ? 'text-yellow-400' : 'text-gray-500';
                
                // Prevent further input if max length reached
                if (length >= CONFIG.MAX_DESCRIPTION_LENGTH) {
                    e.target.value = e.target.value.substring(0, CONFIG.MAX_DESCRIPTION_LENGTH);
                    counter.textContent = CONFIG.MAX_DESCRIPTION_LENGTH;
                    counter.className = 'text-red-400';
                    this.showToast('Maximum description length reached', 'warning', 2000);
                }
            });
        }
        
        // Real-time title validation
        if (titleInput) {
            titleInput.addEventListener('input', (e) => {
                const length = e.target.value.length;
                const submitBtn = document.getElementById('submit-btn');
                
                if (length < CONFIG.MIN_TITLE_LENGTH && length > 0) {
                    e.target.setCustomValidity('Title must be at least 3 characters long');
                    if (submitBtn) submitBtn.disabled = true;
                } else if (length > CONFIG.MAX_TITLE_LENGTH) {
                    e.target.setCustomValidity('Title must be less than 100 characters');
                    if (submitBtn) submitBtn.disabled = true;
                } else {
                    e.target.setCustomValidity('');
                    if (submitBtn) submitBtn.disabled = false;
                }
            });
        }
    }

    // ===================================================================
    // UTILITY FUNCTIONS
    // ===================================================================

    copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                this.showToast('Copied to clipboard!', 'success', 2000);
            }).catch(() => {
                this.fallbackCopyToClipboard(text);
            });
        } else {
            this.fallbackCopyToClipboard(text);
        }
    }

    fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            this.showToast('Copied to clipboard!', 'success', 2000);
        } catch (err) {
            this.showToast('Failed to copy to clipboard', 'error');
        }
        
        document.body.removeChild(textArea);
    }

    cleanup() {
        // Clear all timers
        this.debounceTimers.forEach(timer => clearTimeout(timer));
        this.debounceTimers.clear();
        
        // Remove any lingering event listeners
        document.body.style.overflow = 'auto';
        
        console.log('🧹 JARVIS App cleaned up');
    }
}

// ===================================================================
// ANIMATION UTILITIES
// ===================================================================

function animateNumber(element, start, end, duration, isPercentage = false) {
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const currentValue = start + (end - start) * easeOutQuart(progress);
        const displayValue = isPercentage ? 
            `${currentValue.toFixed(1)}%` : 
            Math.floor(currentValue);
        
        element.textContent = displayValue;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function easeOutQuart(t) {
    return 1 - Math.pow(1 - t, 4);
}

// ===================================================================
// RIPPLE EFFECT
// ===================================================================

document.addEventListener('click', function(e) {
    const button = e.target.closest('.btn-primary, .btn-secondary, .btn-danger, .stat-card, .action-btn');
    if (!button) return;

    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    const ripple = document.createElement('span');
    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        transform: scale(0);
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

// ===================================================================
// GLOBAL INITIALIZATION
// ===================================================================

// Initialize the application
let jarvisApp;

document.addEventListener('DOMContentLoaded', () => {
    jarvisApp = new JarvisApp();
    
    console.log('🤖 JARVIS AI Assistant loaded successfully');
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
        jarvisApp.showToast('An error occurred while processing your request.', 'error');
    }
});

// Network status monitoring
window.addEventListener('online', () => {
    jarvisApp?.showToast('Connection restored', 'success', 2000);
});

window.addEventListener('offline', () => {
    jarvisApp?.showToast('Connection lost - working offline', 'warning', 5000);
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    jarvisApp?.cleanup();
});

// Keyboard navigation enhancement
document.addEventListener('keydown', function(e) {
    // Tab navigation improvements
    if (e.key === 'Tab') {
        document.body.classList.add('keyboard-navigation');
    }
});

document.addEventListener('mousedown', function() {
    document.body.classList.remove('keyboard-navigation');
});

// Export for global access
window.JARVIS = {
    app: () => jarvisApp,
    openModal,
    closeModal,
    showToast,
    copyToClipboard
};

console.log('🚀 JARVIS AI Assistant JavaScript fully loaded');