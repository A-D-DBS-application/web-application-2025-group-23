/**
 * DEVICE DETECTION USAGE EXAMPLES
 * 
 * The deviceDetection system is automatically loaded on all pages.
 * Here are examples of how to use it in your application.
 */

// =============================================================================
// 1. BASIC DEVICE INFO ACCESS
// =============================================================================

// The device info is stored in window.deviceInfo after page load
// Example: window.deviceInfo.deviceType → 'iphone', 'ipad', 'android-phone', etc.

console.log(window.deviceInfo);
// Output:
// {
//   deviceType: 'iphone',
//   deviceCategory: 'mobile',
//   width: 375,
//   height: 667,
//   isMobile: true,
//   isSmallMobile: true,
//   isTablet: false,
//   isDesktop: false,
//   hasTouch: true,
//   browser: 'safari',
//   devicePixelRatio: 2,
//   ...
// }


// =============================================================================
// 2. CHECK DEVICE TYPE
// =============================================================================

// Check if user is on a specific device
if (deviceDetection.is('iphone')) {
    console.log('User is on iPhone');
}

if (deviceDetection.is('ipad')) {
    console.log('User is on iPad');
}

if (deviceDetection.is('android-phone')) {
    console.log('User is on Android phone');
}

// Check device categories
if (deviceDetection.is('mobile')) {
    console.log('User is on a mobile device (phone)');
}

if (deviceDetection.is('tablet')) {
    console.log('User is on a tablet');
}

if (deviceDetection.is('desktop')) {
    console.log('User is on a desktop');
}


// =============================================================================
// 3. CHECK SCREEN SIZE
// =============================================================================

if (window.deviceInfo.isMobile) {
    console.log('Screen is mobile size (≤768px)');
}

if (window.deviceInfo.isSmallMobile) {
    console.log('Screen is very small (≤480px)');
}

if (window.deviceInfo.isTablet) {
    console.log('Screen is tablet size (768px - 1024px)');
}

if (window.deviceInfo.isDesktop) {
    console.log('Screen is desktop size (>1024px)');
}

// Get exact screen dimensions
console.log(`Screen: ${window.deviceInfo.width}x${window.deviceInfo.height}px`);
console.log(`Device Pixel Ratio: ${window.deviceInfo.devicePixelRatio}`);


// =============================================================================
// 4. CHECK TOUCH CAPABILITY
// =============================================================================

if (window.deviceInfo.hasTouch) {
    console.log('Device supports touch input');
    // Add touch-specific event listeners
    document.addEventListener('touchstart', handleTouchStart);
} else {
    console.log('Device uses mouse/pointer input');
}


// =============================================================================
// 5. CHECK BROWSER
// =============================================================================

if (window.deviceInfo.browser === 'safari') {
    console.log('User is on Safari - apply Safari-specific fixes if needed');
}

if (window.deviceInfo.browser === 'chrome') {
    console.log('User is on Chrome');
}

// Available browsers: firefox, chrome, safari, edge, opera, unknown


// =============================================================================
// 6. GET VIEWPORT STRING (SHORTHAND)
// =============================================================================

const viewport = deviceDetection.getViewportString();
console.log(viewport); // Returns: 'small-mobile', 'mobile', 'tablet', or 'desktop'

// Use for classes or conditional rendering
document.body.classList.add(`viewport-${viewport}`);


// =============================================================================
// 7. PRACTICAL EXAMPLES
// =============================================================================

// Example 1: Show/hide elements based on device type
function showHideElements() {
    const desktopOnly = document.querySelectorAll('.desktop-only');
    const mobileOnly = document.querySelectorAll('.mobile-only');
    
    desktopOnly.forEach(el => {
        el.style.display = window.deviceInfo.isDesktop ? 'block' : 'none';
    });
    
    mobileOnly.forEach(el => {
        el.style.display = window.deviceInfo.isMobile ? 'block' : 'none';
    });
}

// Example 2: Optimize image loading based on device pixel ratio
function loadOptimizedImage(baseUrl) {
    const scale = window.deviceInfo.devicePixelRatio > 1 ? '@2x' : '';
    return baseUrl.replace('.png', `${scale}.png`);
}

// Example 3: Adjust performance based on device
function optimizePerformance() {
    if (window.deviceInfo.isSmallMobile) {
        // Reduce animations, lazy load images, etc.
        document.documentElement.style.setProperty('--animation-duration', '0.1s');
    }
}

// Example 4: Device-specific warnings
function showDeviceWarnings() {
    if (window.deviceInfo.browser === 'safari' && window.deviceInfo.isMobile) {
        // Safari on iOS has specific limitations
        console.warn('Safari on iOS detected - some features may be limited');
    }
}

// Example 5: Send device info to server for analytics
function logDeviceInfo() {
    fetch('/api/analytics/device', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(window.deviceInfo)
    });
}

// Example 6: Dynamic navigation adjustment
function adjustNavigation() {
    const nav = document.querySelector('.nav');
    if (window.deviceInfo.isSmallMobile) {
        nav.classList.add('mobile-nav-compact');
    }
}


// =============================================================================
// 8. LISTEN TO WINDOW RESIZE (Responsive Changes)
// =============================================================================

// The device detection re-initializes on resize
// You can listen for changes:

window.addEventListener('resize', () => {
    console.log('Window resized');
    console.log(`New size: ${window.deviceInfo.width}x${window.deviceInfo.height}px`);
    console.log(`Current viewport: ${deviceDetection.getViewportString()}`);
});


// =============================================================================
// 9. DEBUG/DEVELOPMENT
// =============================================================================

// Enable detailed logging in console:
deviceDetection.logInfo();
// Shows:
// 📱 Device Information
//   Device Type: iphone
//   Device Category: mobile
//   Screen Size: 375x667px
//   Screen Type: { isMobile: true, isSmallMobile: true, isTablet: false, isDesktop: false }
//   Touch Supported: true
//   Browser: safari
//   Device Pixel Ratio: 2


// =============================================================================
// 10. AVAILABLE PROPERTIES ON window.deviceInfo
// =============================================================================

/*
{
  // Device type detection
  deviceType: 'iphone' | 'ipad' | 'android-tablet' | 'android-phone' | 'windows' | 'mac' | 'unknown',
  deviceCategory: 'mobile' | 'tablet' | 'desktop',
  
  // Screen information
  width: number,                    // Window width in pixels
  height: number,                   // Window height in pixels
  isMobile: boolean,                // width <= 768px
  isSmallMobile: boolean,           // width <= 480px
  isTablet: boolean,                // width > 768px && width <= 1024px
  isDesktop: boolean,               // width > 1024px
  devicePixelRatio: number,         // Screen pixel density (1, 1.5, 2, etc)
  
  // Capabilities
  hasTouch: boolean,                // Supports touch input
  
  // Browser info
  browser: 'firefox' | 'chrome' | 'safari' | 'edge' | 'opera' | 'unknown',
  userAgent: string,                // Full user agent string
  
  // Metadata
  timestamp: string                 // ISO timestamp of initialization
}
*/


// =============================================================================
// CSS CLASSES FOR DEVICE-SPECIFIC STYLING
// =============================================================================

// You can add a class to body for CSS hooks:
document.body.classList.add(`device-${window.deviceInfo.deviceCategory}`);

// Then in CSS:
// .device-mobile { /* Mobile-specific styles */ }
// .device-tablet { /* Tablet-specific styles */ }
// .device-desktop { /* Desktop-specific styles */ }

// Or based on viewport:
document.body.classList.add(`viewport-${deviceDetection.getViewportString()}`);

// .viewport-small-mobile { /* Extra small screens */ }
// .viewport-mobile { /* Mobile */ }
// .viewport-tablet { /* Tablet */ }
// .viewport-desktop { /* Desktop */ }
