// ==========================================================
// One8 E-commerce - Global JS
// Handles the slide-in cart drawer: loading, rendering,
// quantity changes, item removal, and the navbar cart badge.
// ==========================================================

const cartDrawerEl = document.getElementById('cartDrawer');
const cartDrawer = cartDrawerEl ? new bootstrap.Offcanvas(cartDrawerEl) : null;

function formatRupees(amount) {
    return '₹' + Math.round(amount).toLocaleString('en-IN');
}

function updateCartBadge(count) {
    const badge = document.getElementById('cartCountBadge');
    if (!badge) return;
    if (count > 0) {
        badge.textContent = count;
        badge.classList.remove('d-none');
    } else {
        badge.classList.add('d-none');
    }
}

function renderCartDrawer(data) {
    const itemsContainer = document.getElementById('cartDrawerItems');
    const countLabel = document.getElementById('cartDrawerCount');
    const subtotalLabel = document.getElementById('cartDrawerSubtotal');
    const checkoutBtn = document.getElementById('cartDrawerCheckoutBtn');

    updateCartBadge(data.count);
    countLabel.textContent = data.count + (data.count === 1 ? ' Item' : ' Items');
    subtotalLabel.textContent = formatRupees(data.subtotal);
    checkoutBtn.href = data.checkout_url;

    if (!data.items.length) {
        itemsContainer.innerHTML = '<p class="text-muted text-center mt-5">Your bag is empty.</p>';
        return;
    }

    itemsContainer.innerHTML = data.items.map(item => `
        <div class="d-flex align-items-start py-3 border-bottom" data-item-id="${item.id}">
            <img src="${item.product_image || 'https://via.placeholder.com/80x80?text=No+Image'}"
                 alt="${item.product_name}" style="width:70px; height:70px; object-fit:cover;" class="rounded me-3">
            <div class="flex-grow-1">
                <p class="mb-1 fw-bold">${item.product_name}</p>
                ${item.color ? `<p class="mb-0 small text-muted">Color: ${item.color}</p>` : ''}
                ${item.size ? `<p class="mb-1 small text-muted">Size: ${item.size}</p>` : ''}
                <div class="d-flex align-items-center gap-2 mt-2">
                    <button class="btn btn-sm btn-outline-secondary cart-qty-btn" data-item-id="${item.id}" data-delta="-1">-</button>
                    <span>${item.quantity}</span>
                    <button class="btn btn-sm btn-outline-secondary cart-qty-btn" data-item-id="${item.id}" data-delta="1">+</button>
                    <button class="btn btn-sm btn-link text-danger ms-2 cart-remove-btn" data-item-id="${item.id}">
                        <i class="bi bi-trash"></i> Remove
                    </button>
                </div>
            </div>
            <p class="fw-bold mb-0">${formatRupees(item.line_total)}</p>
        </div>
    `).join('');
}

function loadCartDrawer() {
    fetch('/cart/data', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(res => res.json())
        .then(data => renderCartDrawer(data))
        .catch(() => {
            document.getElementById('cartDrawerItems').innerHTML =
                '<p class="text-danger text-center mt-5">Could not load cart.</p>';
        });
}

function updateCartItemQuantity(itemId, newQuantity) {
    const formData = new FormData();
    formData.append('quantity', newQuantity);
    // CSRF token pulled from any existing form on the page (they all render one)
    const csrfInput = document.querySelector('input[name="csrf_token"]');
    if (csrfInput) formData.append('csrf_token', csrfInput.value);

    fetch(`/cart/update/${itemId}`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderCartDrawer(data);
            } else {
                alert(data.message || 'Could not update item.');
            }
        });
}

function removeCartItem(itemId) {
    const csrfInput = document.querySelector('input[name="csrf_token"]');
    const formData = new FormData();
    if (csrfInput) formData.append('csrf_token', csrfInput.value);

    fetch(`/cart/remove/${itemId}`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
    })
        .then(res => res.json())
        .then(data => renderCartDrawer(data));
}

// Event delegation: handles +/- and remove buttons even though
// the drawer's contents are re-rendered dynamically.
document.addEventListener('click', function (e) {
    const qtyBtn = e.target.closest('.cart-qty-btn');
    if (qtyBtn) {
        const itemId = qtyBtn.dataset.itemId;
        const delta = parseInt(qtyBtn.dataset.delta, 10);
        const row = qtyBtn.closest('[data-item-id]');
        const currentQty = parseInt(row.querySelector('span').textContent, 10);
        const newQty = currentQty + delta;
        if (newQty >= 1) {
            updateCartItemQuantity(itemId, newQty);
        } else {
            removeCartItem(itemId);
        }
    }

    const removeBtn = e.target.closest('.cart-remove-btn');
    if (removeBtn) {
        removeCartItem(removeBtn.dataset.itemId);
    }
});

// Load drawer contents once when the offcanvas is about to open
// (covers navbar cart icon clicks on any page)
if (cartDrawerEl) {
    cartDrawerEl.addEventListener('show.bs.offcanvas', function () {
        document.getElementById('cartAddedBanner').classList.add('d-none');
        loadCartDrawer();
    });
}

// Keep the navbar badge accurate on every page load
document.addEventListener('DOMContentLoaded', function () {
    fetch('/cart/data', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.json())
        .then(data => updateCartBadge(data.count))
        .catch(() => {});
});

// ==========================================================
// Add-to-Cart forms (product_detail.html) -> AJAX submit,
// open the drawer with a "just added" banner instead of navigating.
// ==========================================================
document.addEventListener('submit', function (e) {
    const form = e.target;
    if (!form.classList.contains('ajax-add-to-cart')) return;

    e.preventDefault();

    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
    })
        .then(res => res.json().then(data => ({ ok: res.ok, data })))
        .then(({ ok, data }) => {
            if (ok && data.success) {
                renderCartDrawer(data);
                const banner = document.getElementById('cartAddedBanner');
                document.getElementById('cartAddedMessage').textContent = data.message;
                banner.classList.remove('d-none');
                if (cartDrawer) cartDrawer.show();
            } else {
                alert(data.message || 'Could not add item to bag.');
            }
        })
        .catch(() => alert('Something went wrong. Please try again.'));
});