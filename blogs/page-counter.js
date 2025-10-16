/**
 * PageCounter - Secure view and share counter system
 * Frontend JavaScript library
 */

class PageCounter {
  constructor(config) {
    this.apiUrl = config.apiUrl; // Your deployed Apps Script URL
    this.apiKey = config.apiKey;
    this.pageId = config.pageId || this.generatePageId();
    this.viewCounted = false;
    this.userHash = this.getUserHash();
  }
  
  /**
   * Generate page ID from current URL
   */
  generatePageId() {
    const path = window.location.pathname;
    return path === '/' ? 'home' : path.replace(/\//g, '-').substring(1);
  }
  
  /**
   * Generate a semi-unique user hash (client-side fingerprint)
   */
  getUserHash() {
    // Check if hash exists in sessionStorage
    let hash = sessionStorage.getItem('userHash');
    if (hash) return hash;
    
    // Create a simple fingerprint
    const nav = window.navigator;
    const screen = window.screen;
    const data = [
      nav.userAgent,
      nav.language,
      screen.colorDepth,
      screen.width + 'x' + screen.height,
      new Date().getTimezoneOffset()
    ].join('|');
    
    // Simple hash function
    hash = this.simpleHash(data);
    sessionStorage.setItem('userHash', hash);
    return hash;
  }
  
  /**
   * Simple hash function
   */
  simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(36);
  }
  
  /**
   * Get current counts
   */
  async getCounts() {
    try {
      const url = `${this.apiUrl}?pageId=${encodeURIComponent(this.pageId)}&key=${encodeURIComponent(this.apiKey)}`;
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success) {
        return {
          views: data.views,
          shares: data.shares
        };
      } else {
        console.error('Counter API error:', data.error);
        return null;
      }
    } catch (error) {
      console.error('Counter fetch error:', error);
      return null;
    }
  }
  
  /**
   * Count a view (call this on page load)
   */
  async countView() {
    if (this.viewCounted) return;
    
    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          pageId: this.pageId,
          action: 'view',
          key: this.apiKey,
          userHash: this.userHash
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.viewCounted = true;
        return {
          views: data.views,
          shares: data.shares
        };
      } else {
        console.error('Counter API error:', data.error);
        return null;
      }
    } catch (error) {
      console.error('Counter error:', error);
      return null;
    }
  }
  
  /**
   * Count a share (call this when user clicks share button)
   */
  async countShare() {
    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          pageId: this.pageId,
          action: 'share',
          key: this.apiKey,
          userHash: this.userHash
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        return {
          views: data.views,
          shares: data.shares
        };
      } else {
        console.error('Counter API error:', data.error);
        return null;
      }
    } catch (error) {
      console.error('Counter error:', error);
      return null;
    }
  }
  
  /**
   * Update display elements
   */
  updateDisplay(counts) {
    if (!counts) return;
    
    // Update elements with data-counter-type attribute
    const viewElements = document.querySelectorAll('[data-counter-type="views"]');
    const shareElements = document.querySelectorAll('[data-counter-type="shares"]');
    
    viewElements.forEach(el => {
      el.textContent = this.formatCount(counts.views);
    });
    
    shareElements.forEach(el => {
      el.textContent = this.formatCount(counts.shares);
    });
  }
  
  /**
   * Format count for display (e.g., 1.2K, 5.3M)
   */
  formatCount(count) {
    if (count < 1000) return count.toString();
    if (count < 1000000) return (count / 1000).toFixed(1) + 'K';
    return (count / 1000000).toFixed(1) + 'M';
  }
  
  /**
   * Initialize counter - call this on page load
   */
  async init() {
    // Count the view
    const counts = await this.countView();
    
    // Update display
    if (counts) {
      this.updateDisplay(counts);
    }
    
    // Attach share button handlers
    this.attachShareHandlers();
  }
  
  /**
   * Attach handlers to share buttons
   */
  attachShareHandlers() {
    const shareButtons = document.querySelectorAll('[data-share-button]');
    
    shareButtons.forEach(button => {
      button.addEventListener('click', async () => {
        const counts = await this.countShare();
        if (counts) {
          this.updateDisplay(counts);
        }
      });
    });
  }
}

// Make it available globally
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PageCounter;
}
