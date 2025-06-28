// Performance-optimized JavaScript
class JarvisApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.optimizePerformance();
    }

    setupEventListeners() {
        // Use event delegation for better performance
        document.addEventListener('click', this.handleClicks.bind(this));
        document.addEventListener('keydown', this.handleKeydown.bind(this));
    }

    handleClicks(e) {
        // Handle all clicks with event delegation
        if (e.target.closest('.modal-backdrop') && e.target.classList.contains('modal-backdrop')) {
            this.closeAllModals();
        }
    }

    handleKeydown(e) {
        if (e.key === 'Escape') {
            this.closeAllModals();
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            this.openModal('task-modal');
        }
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }

    closeAllModals() {
        const modals = document.querySelectorAll('.modal-backdrop:not(.hidden)');
        modals.forEach(modal => {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
    }

    optimizePerformance() {
        // Lazy load animations
        this.setupIntersectionObserver();
        
        // Debounce resize events
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        });
    }

    setupIntersectionObserver() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px'
        });

        // Observe elements that should animate
        document.querySelectorAll('.task-card, .stat-card').forEach(el => {
            observer.observe(el);
        });
    }

    handleResize() {
        // Handle responsive adjustments
        const cards = document.querySelectorAll('.task-card');
        cards.forEach(card => {
            card.style.transform = 'none';
            card.offsetHeight; // Force reflow
            card.style.transform = '';
        });
    }

    // API methods with better error handling
    async apiRequest(endpoint, options = {}) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
            
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

    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        const colors = {
            'success': 'bg-green-600',
            'error': 'bg-red-600',
            'info': 'bg-blue-600'
        };
        
        toast.className = `${colors[type]} text-white px-6 py-4 rounded-xl shadow-lg flex items-center space-x-3 transform translate-x-full transition-transform duration-300`;
        toast.innerHTML = `
            <span class="font-medium">${message}</span>
            <button onclick="this.parentElement.remove()" class="text-white/80 hover:text-white">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        // Animate in
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
        });
        
        // Auto remove
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => toast.remove(), 300);
            }
        }, duration);
    }
}

// Initialize optimized app
document.addEventListener('DOMContentLoaded', () => {
    window.jarvis = new JarvisApp();
});

// Global functions for backward compatibility
function openModal(modalId) {
    window.jarvis?.openModal(modalId);
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

function showToast(message, type, duration) {
    window.jarvis?.showToast(message, type, duration);
}
