/**
 * Lyra Enhanced Dashboard Frontend Integration
 * Production-ready JavaScript for connecting to the enhanced dashboard backend
 * 
 * Usage: Include this file in your existing frontend and call LyraDashboard.init()
 */

class LyraDashboard {
    constructor() {
        this.API_BASE = 'https://your-backend-url.railway.app'; // Replace with your deployed backend URL
        this.REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes
        this.COUNTDOWN_INTERVAL = 60 * 1000; // 1 minute
        
        this.authToken = null;
        this.refreshTimer = null;
        this.countdownTimer = null;
        this.isInitialized = false;
    }

    /**
     * Initialize the enhanced dashboard
     * Call this after user login/authentication
     */
    async init(authToken = null) {
        console.log('🚀 Initializing Lyra Enhanced Dashboard...');
        
        this.authToken = authToken || localStorage.getItem('authToken');
        
        if (!this.authToken) {
            console.warn('No auth token found. User must be logged in to use enhanced dashboard.');
            return false;
        }

        try {
            await this.loadDashboardWidgets();
            await this.loadCalendarTicker();
            
            this.setupEventHandlers();
            
            this.startAutoRefresh();
            
            this.isInitialized = true;
            console.log('✅ Enhanced Dashboard initialized successfully!');
            
            this.showNotification('🎉 Enhanced dashboard loaded! All systems ready.', 'success');
            
            return true;
            
        } catch (error) {
            console.error('❌ Failed to initialize enhanced dashboard:', error);
            this.showNotification('Failed to load enhanced dashboard. Please refresh the page.', 'error');
            return false;
        }
    }

    /**
     * Load real-time dashboard widgets
     */
    async loadDashboardWidgets() {
        try {
            const response = await this.apiCall('/dashboard/widgets');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            const widgets = data.widgets;
            
            this.updateElement('total-content', widgets.content_stats.total_generated);
            this.updateElement('this-week', widgets.content_stats.this_week);
            this.updateElement('approved-content', widgets.content_stats.approved);
            this.updateElement('approval-rate', `${widgets.content_stats.approval_rate}%`);
            
            this.updateElement('pending-count', widgets.quick_stats.pending_approval);
            this.updateElement('platforms-active', widgets.quick_stats.platforms_active);
            
            this.updateUpcomingPosts(widgets.upcoming_posts);
            
            console.log('✅ Dashboard widgets updated successfully');
            
        } catch (error) {
            console.error('❌ Failed to load dashboard widgets:', error);
            this.showNotification('Failed to load dashboard statistics', 'error');
        }
    }

    /**
     * Load calendar ticker with countdown timers
     */
    async loadCalendarTicker(daysAhead = 7) {
        try {
            const response = await this.apiCall(`/dashboard/calendar-ticker?days_ahead=${daysAhead}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            this.updateCalendarTicker(data.ticker_items, data.next_post);
            
            console.log(`✅ Calendar ticker updated: ${data.total_upcoming} upcoming posts`);
            
        } catch (error) {
            console.error('❌ Failed to load calendar ticker:', error);
            this.showNotification('Failed to load upcoming posts', 'error');
        }
    }

    /**
     * Quick action: Generate new content
     */
    async quickGenerateContent() {
        const button = document.getElementById('quick-generate-btn');
        if (!button) return;
        
        const originalText = button.textContent;
        
        try {
            button.textContent = '🔄 Generating...';
            button.disabled = true;
            
            const response = await this.apiCall('/dashboard/quick-actions/generate-content', {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.message === "Content generated successfully") {
                this.showNotification(
                    `✅ New ${result.platform} content generated! Preview: ${result.content_preview}`, 
                    'success'
                );
                
                await this.loadDashboardWidgets();
                
                if (this.isModalOpen('pending-approvals-modal')) {
                    await this.loadPendingApprovals();
                }
            }
            
            console.log('✅ Content generated:', result);
            
        } catch (error) {
            console.error('❌ Quick generation failed:', error);
            this.showNotification('❌ Content generation failed. Please try again.', 'error');
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    /**
     * Load pending approvals
     */
    async loadPendingApprovals() {
        try {
            const response = await this.apiCall('/dashboard/quick-actions/pending-approvals');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            this.updateElement('pending-count', data.total_pending);
            
            this.updatePendingApprovalsList(data.pending_approvals);
            
            this.showModal('pending-approvals-modal');
            
            console.log(`✅ Loaded ${data.total_pending} pending approvals`);
            
        } catch (error) {
            console.error('❌ Failed to load pending approvals:', error);
            this.showNotification('Failed to load pending approvals', 'error');
        }
    }

    /**
     * Approve content by ID
     */
    async approveContent(contentId) {
        try {
            const response = await this.apiCall(`/dashboard/content/${contentId}/approve`, {
                method: 'PUT'
            });
            
            if (response.ok) {
                this.showNotification('✅ Content approved successfully!', 'success');
                
                await this.loadPendingApprovals();
                await this.loadDashboardWidgets();
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
        } catch (error) {
            console.error('Failed to approve content:', error);
            this.showNotification('❌ Failed to approve content', 'error');
        }
    }

    /**
     * Update upcoming posts display
     */
    updateUpcomingPosts(upcomingPosts) {
        const container = document.getElementById('upcoming-posts');
        if (!container) return;
        
        if (upcomingPosts && upcomingPosts.length > 0) {
            container.innerHTML = upcomingPosts.map(post => `
                <div class="upcoming-post">
                    <span class="platform-badge ${post.platform}">${post.platform.toUpperCase()}</span>
                    <span class="countdown ${post.hours_until < 2 ? 'urgent' : ''}">${post.hours_until}h remaining</span>
                    <span class="days-count">${post.days_until} days</span>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="no-posts">No upcoming posts scheduled</p>';
        }
    }

    /**
     * Update calendar ticker display
     */
    updateCalendarTicker(tickerItems, nextPost) {
        const ticker = document.getElementById('calendar-ticker');
        if (!ticker) return;
        
        if (tickerItems && tickerItems.length > 0) {
            ticker.innerHTML = tickerItems.map((item, index) => `
                <div class="ticker-item ${index === 0 && nextPost ? 'next-post' : ''} ${item.countdown.total_minutes < 60 ? 'urgent' : ''}">
                    <span class="platform-badge ${item.platform}">${item.platform}</span>
                    <span class="content-preview">${item.content_preview}</span>
                    <span class="countdown ${item.countdown.total_minutes < 60 ? 'urgent' : item.countdown.total_minutes < 360 ? 'soon' : ''}">
                        ${item.countdown.days}d ${item.countdown.hours}h ${item.countdown.minutes}m
                    </span>
                </div>
            `).join('');
        } else {
            ticker.innerHTML = '<div class="no-posts">No upcoming posts in the next 7 days</div>';
        }
    }

    /**
     * Update pending approvals list
     */
    updatePendingApprovalsList(pendingApprovals) {
        const list = document.querySelector('#pending-approvals-modal .approvals-list');
        if (!list) return;
        
        if (pendingApprovals && pendingApprovals.length > 0) {
            list.innerHTML = pendingApprovals.map(content => `
                <div class="approval-item" data-id="${content.id}">
                    <div class="content-header">
                        <span class="platform-badge ${content.platform}">${content.platform}</span>
                        <span class="content-type">${content.content_type}</span>
                        <span class="created-date">${new Date(content.created_at).toLocaleDateString()}</span>
                    </div>
                    <div class="content-preview">${content.content_preview}</div>
                    <div class="approval-actions">
                        <button onclick="LyraDashboard.instance.approveContent(${content.id})" class="approve-btn">✅ Approve</button>
                        <button onclick="LyraDashboard.instance.editContent(${content.id})" class="edit-btn">✏️ Edit</button>
                        <button onclick="LyraDashboard.instance.viewFullContent(${content.id})" class="view-btn">👁️ View Full</button>
                    </div>
                </div>
            `).join('');
        } else {
            list.innerHTML = '<div class="no-pending">🎉 All content approved! No pending items.</div>';
        }
    }

    /**
     * Set up event handlers for dashboard interactions
     */
    setupEventHandlers() {
        const generateBtn = document.getElementById('quick-generate-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.quickGenerateContent());
        }
        
        const approvalsBtn = document.getElementById('pending-approvals-btn');
        if (approvalsBtn) {
            approvalsBtn.addEventListener('click', () => this.loadPendingApprovals());
        }
        
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            const closeBtn = modal.querySelector('.close-btn, .notification-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.hideModal(modal.id));
            }
            
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal(modal.id);
                }
            });
        });
        
        console.log('✅ Event handlers set up successfully');
    }

    /**
     * Start auto-refresh timers
     */
    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            console.log('🔄 Auto-refreshing dashboard...');
            this.loadDashboardWidgets();
        }, this.REFRESH_INTERVAL);
        
        this.countdownTimer = setInterval(() => {
            this.updateCountdownTimers();
        }, this.COUNTDOWN_INTERVAL);
        
        console.log('✅ Auto-refresh timers started');
    }

    /**
     * Stop auto-refresh timers
     */
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
        
        if (this.countdownTimer) {
            clearInterval(this.countdownTimer);
            this.countdownTimer = null;
        }
        
        console.log('⏹️ Auto-refresh timers stopped');
    }

    /**
     * Update countdown timers in real-time
     */
    updateCountdownTimers() {
        const countdowns = document.querySelectorAll('.countdown');
        countdowns.forEach(countdown => {
        });
        
        this.loadCalendarTicker();
    }

    /**
     * Make authenticated API calls
     */
    async apiCall(endpoint, options = {}) {
        const url = `${this.API_BASE}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${this.authToken}`,
                'Content-Type': 'application/json'
            }
        };
        
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        return fetch(url, mergedOptions);
    }

    /**
     * Utility: Update element text content
     */
    updateElement(id, content) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = content;
        }
    }

    /**
     * Utility: Show modal
     */
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
        }
    }

    /**
     * Utility: Hide modal
     */
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Utility: Check if modal is open
     */
    isModalOpen(modalId) {
        const modal = document.getElementById(modalId);
        return modal && modal.style.display === 'block';
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `lyra-notification ${type}`;
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.remove('show');
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }
        }, 5000);
    }

    /**
     * Placeholder methods for content actions
     */
    editContent(contentId) {
        this.showNotification(`✏️ Opening content editor for item #${contentId}...`, 'info');
        console.log(`✏️ Editing content ${contentId}`);
    }

    viewFullContent(contentId) {
        this.showNotification(`👁️ Opening full preview for content #${contentId}...`, 'info');
        console.log(`👁️ Viewing content ${contentId}`);
    }

    /**
     * Cleanup method
     */
    destroy() {
        this.stopAutoRefresh();
        this.isInitialized = false;
        console.log('🧹 Enhanced Dashboard cleaned up');
    }
}

LyraDashboard.instance = new LyraDashboard();

if (typeof module !== 'undefined' && module.exports) {
    module.exports = LyraDashboard;
}

document.addEventListener('DOMContentLoaded', function() {
    const authToken = localStorage.getItem('authToken');
    if (authToken && document.getElementById('dashboard-container')) {
        LyraDashboard.instance.init(authToken);
    }
});
