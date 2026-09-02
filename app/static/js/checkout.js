// ==========================================================
// One8 E-commerce - checkout.js
// Centered checkout modal: fetches checkout content via AJAX
// (no page navigation), and submits the place-order form the
// same way. Depends on cart.js being loaded first (uses
// closeCartDrawer() when opening checkout from the cart drawer).
// ==========================================================

const checkoutModalOverlay = document.getElementById('checkoutModalOverlay');
const checkoutModalBody = document.getElementById('checkoutModalBody');
const checkoutModalClose = document.getElementById('checkoutModalClose');

function openCheckoutModal() {
    if (!checkoutModalOverlay) return;

    checkoutModalOverlay.classList.add('open');
    checkoutModalBody.innerHTML = '<p class="muted center" style="margin-top:2rem;">Loading...</p>';

    fetch('/checkout/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.json())
        .then(data => {
            if (data.needs_login) {
                window.location.href = data.login_url;
                return;
            }
            if (!data.success) {
                checkoutModalBody.innerHTML = `<p class="center" style="color:var(--color-danger); margin-top:2rem;">${data.message}</p>`;
                return;
            }
            checkoutModalBody.innerHTML = data.html;
        })
        .catch(() => {
            checkoutModalBody.innerHTML = '<p class="center" style="color:var(--color-danger); margin-top:2rem;">Could not load checkout.</p>';
        });
}

function closeCheckoutModal() {
    if (!checkoutModalOverlay) return;
    checkoutModalOverlay.classList.remove('open');
}

if (checkoutModalClose) {
    checkoutModalClose.addEventListener('click', closeCheckoutModal);
}

if (checkoutModalOverlay) {
    checkoutModalOverlay.addEventListener('click', function (e) {
        if (e.target === checkoutModalOverlay) closeCheckoutModal();
    });
}

// Cart drawer's "Checkout Securely" button opens this modal instead of navigating
document.addEventListener('click', function (e) {
    if (e.target && e.target.id === 'cartDrawerCheckoutBtn') {
        e.preventDefault();
        if (typeof closeCartDrawer === 'function') closeCartDrawer();
        openCheckoutModal();
    }
});

// Place-order form is injected dynamically, so use delegation
document.addEventListener('submit', function (e) {
    const form = e.target;
    if (!form.classList.contains('ajax-place-order')) return;

    e.preventDefault();

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn ? submitBtn.textContent : '';
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Placing order...';
    }

    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData,
    })
        .then(res => res.json().then(data => ({ ok: res.ok, data })))
        .then(({ ok, data }) => {
            if (data.needs_login) {
                window.location.href = data.login_url;
                return;
            }
            if (ok && data.success) {
                // Order confirmation is a real page, not a modal - full navigation is correct here.
                window.location.href = data.redirect;
            } else {
                alert(data.message || 'Could not place order.');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }
            }
        })
        .catch(() => {
            alert('Something went wrong. Please try again.');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
});