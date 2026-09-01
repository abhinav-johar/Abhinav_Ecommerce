// ==========================================================
// One8 E-commerce - main.js
// Global, site-wide behavior only. Cart-specific logic lives
// in cart.js; checkout-specific logic lives in checkout.js.
// ==========================================================

// ---------------- Mobile nav toggle ----------------
const navToggle = document.getElementById('navToggle');
const mainNav = document.getElementById('mainNav');

if (navToggle && mainNav) {
    navToggle.addEventListener('click', function () {
        const isOpen = mainNav.classList.toggle('open');
        navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
}

// ---------------- Keep navbar cart badge accurate on every page load ----------------
document.addEventListener('DOMContentLoaded', function () {
    fetch('/cart/data', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.json())
        .then(data => {
            const badge = document.getElementById('cartCountBadge');
            if (!badge) return;
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.hidden = false;
            } else {
                badge.hidden = true;
            }
        })
        .catch(() => {});
});