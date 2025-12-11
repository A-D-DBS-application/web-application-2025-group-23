/**
 * Device Detection System
 * Automatically detects device type and stores information
 * Available globally as window.deviceInfo
 */

const deviceDetection = {
    // Detect device type
    detectDevice() {
        const ua = navigator.userAgent.toLowerCase();
        
        // Device type detection
        const isIPhone = /iphone/.test(ua);
        const isIPad = /ipad|android(?!.*mobile)/.test(ua);
        const isAndroid = /android/.test(ua);
        const isWindows = /win/.test(ua);
        const isMac = /mac/.test(ua);
        
        // Device category
        let deviceType = 'unknown';
        let deviceCategory = 'desktop';
        
        if (isIPhone) {
            deviceType = 'iphone';
            deviceCategory = 'mobile';
        } else if (isIPad) {
            deviceType = 'ipad';
            deviceCategory = 'tablet';
        } else if (isAndroid) {
            // Check if it's a tablet or phone
            if (/tablet|nexus 7|nexus 10|xoom|kindle|playbook|silk|gt-p/.test(ua)) {
                deviceType = 'android-tablet';
                deviceCategory = 'tablet';
            } else {
                deviceType = 'android-phone';
                deviceCategory = 'mobile';
            }
        } else if (isWindows) {
            deviceType = 'windows';
            deviceCategory = 'desktop';
        } else if (isMac) {
            deviceType = 'mac';
            deviceCategory = 'desktop';
        }
        
        return { deviceType, deviceCategory };
    },
    
    // Get screen size info
    getScreenInfo() {
        return {
            width: window.innerWidth,
            height: window.innerHeight,
            isMobile: window.innerWidth <= 768,
            isSmallMobile: window.innerWidth <= 480,
            isTablet: window.innerWidth > 768 && window.innerWidth <= 1024,
            isDesktop: window.innerWidth > 1024,
            devicePixelRatio: window.devicePixelRatio || 1
        };
    },
    
    // Check if device supports touch
    supportsTouch() {
        return () => {
            return (('ontouchstart' in window) ||
                    (navigator.maxTouchPoints > 0) ||
                    (navigator.msMaxTouchPoints > 0));
        };
    },
    
    // Get browser info
    getBrowserInfo() {
        const ua = navigator.userAgent.toLowerCase();
        let browser = 'unknown';
        
        if (/firefox/.test(ua)) browser = 'firefox';
        else if (/chrome/.test(ua)) browser = 'chrome';
        else if (/safari/.test(ua)) browser = 'safari';
        else if (/edge/.test(ua) || /edg/.test(ua)) browser = 'edge';
        else if (/opera/.test(ua)) browser = 'opera';
        
        return { browser, userAgent: ua };
    },
    
    // Initialize and store info
    init() {
        const device = this.detectDevice();
        const screen = this.getScreenInfo();
        const browser = this.getBrowserInfo();
        const hasTouch = this.supportsTouch()();
        
        const deviceInfo = {
            ...device,
            ...screen,
            hasTouch,
            ...browser,
            timestamp: new Date().toISOString()
        };
        
        // Store globally
        window.deviceInfo = deviceInfo;
        
        // Store in sessionStorage for persistence across page loads
        sessionStorage.setItem('deviceInfo', JSON.stringify(deviceInfo));
        
        return deviceInfo;
    },
    
    // Log device info to console (useful for debugging)
    logInfo() {
        if (!window.deviceInfo) this.init();
        
        console.group('📱 Device Information');
        console.log('Device Type:', window.deviceInfo.deviceType);
        console.log('Device Category:', window.deviceInfo.deviceCategory);
        console.log('Screen Size:', `${window.deviceInfo.width}x${window.deviceInfo.height}px`);
        console.log('Screen Type:', {
            isMobile: window.deviceInfo.isMobile,
            isSmallMobile: window.deviceInfo.isSmallMobile,
            isTablet: window.deviceInfo.isTablet,
            isDesktop: window.deviceInfo.isDesktop
        });
        console.log('Touch Supported:', window.deviceInfo.hasTouch);
        console.log('Browser:', window.deviceInfo.browser);
        console.log('Device Pixel Ratio:', window.deviceInfo.devicePixelRatio);
        console.groupEnd();
    },
    
    // Check if specific device type
    is(type) {
        if (!window.deviceInfo) this.init();
        return window.deviceInfo.deviceType === type || 
               window.deviceInfo.deviceCategory === type;
    },
    
    // Get viewport info as string
    getViewportString() {
        if (!window.deviceInfo) this.init();
        const info = window.deviceInfo;
        
        if (info.isSmallMobile) return 'small-mobile';
        if (info.isMobile) return 'mobile';
        if (info.isTablet) return 'tablet';
        if (info.isDesktop) return 'desktop';
        return 'unknown';
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    deviceDetection.init();
    
    // Optional: Show device info in console for development
    // Uncomment to enable:
    // deviceDetection.logInfo();
    
    // Handle data-href navigation
    document.addEventListener('click', function(e) {
        const target = e.target.closest('[data-href]');
        if (target && !target.disabled) {
            const href = target.getAttribute('data-href');
            if (href) {
                window.location.href = href;
            }
        }
    });
});

// Re-initialize on window resize (for responsive design changes)
let resizeTimeout;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        deviceDetection.init();
    }, 250);
});

// Make available globally
window.deviceDetection = deviceDetection;
