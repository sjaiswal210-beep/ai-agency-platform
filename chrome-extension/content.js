/**
 * WhatsApp Image Reminder - Content Script
 * Shows a floating notification reminding users to attach an image
 * when WhatsApp Web is opened.
 */

(function () {
  'use strict';

  // Avoid duplicate injection
  if (document.querySelector('.wa-image-reminder-floater')) return;

  // Configuration
  const CONFIG = {
    autoHideDelay: 10000, // Auto-hide after 10 seconds (0 = never auto-hide)
    showOncePerSession: true, // Only show once per browser session
  };

  // Check if already shown this session
  if (CONFIG.showOncePerSession && sessionStorage.getItem('wa-reminder-shown')) {
    return;
  }

  function createFloater() {
    const floater = document.createElement('div');
    floater.className = 'wa-image-reminder-floater';
    floater.setAttribute('role', 'alert');
    floater.setAttribute('aria-live', 'polite');

    floater.innerHTML = `
      <span class="wa-image-reminder-icon">\u{1F4CE}</span>
      <span class="wa-image-reminder-text">
        Don't forget to <strong>attach an image</strong> with your message!
      </span>
      <button class="wa-image-reminder-close" aria-label="Dismiss notification" title="Dismiss">&times;</button>
    `;

    // Close button handler
    const closeBtn = floater.querySelector('.wa-image-reminder-close');
    closeBtn.addEventListener('click', () => dismissFloater(floater));

    document.body.appendChild(floater);

    // Mark as shown for this session
    if (CONFIG.showOncePerSession) {
      sessionStorage.setItem('wa-reminder-shown', 'true');
    }

    // Auto-hide after delay
    if (CONFIG.autoHideDelay > 0) {
      setTimeout(() => {
        if (document.body.contains(floater)) {
          dismissFloater(floater);
        }
      }, CONFIG.autoHideDelay);
    }
  }

  function dismissFloater(floater) {
    floater.classList.add('wa-hiding');
    floater.addEventListener('animationend', () => {
      floater.remove();
    });
  }

  // Wait for WhatsApp Web to fully load before showing
  function waitForApp() {
    const observer = new MutationObserver((mutations, obs) => {
      // WhatsApp Web renders the main app inside #app
      const app = document.querySelector('#app');
      if (app && app.children.length > 0) {
        obs.disconnect();
        // Small delay to let the UI settle
        setTimeout(createFloater, 1500);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // Fallback: show after 5 seconds even if detection fails
    setTimeout(() => {
      observer.disconnect();
      if (!document.querySelector('.wa-image-reminder-floater')) {
        createFloater();
      }
    }, 5000);
  }

  // Start observing
  if (document.readyState === 'complete') {
    waitForApp();
  } else {
    window.addEventListener('load', waitForApp);
  }
})();
