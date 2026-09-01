// ==========================================================
// One8 E-commerce - cart.js
// Slide-in cart drawer: open/close, render, add/update/remove.
// Loaded on every page since the cart trigger lives in the navbar.
// ==========================================================

const cartDrawerEl = document.getElementById('cartDrawer');
const drawerBackdrop = document.getElementById('drawerBackdrop');
const cartTrigger = document.getElementById('cartTrigger');
const cartDrawerClose = document.getElementById('cartDrawerClose');

function formatRupees(amount) {
    return '₹' + Math.round(amount).toLocaleString('en-IN');
}

function updateCartBadge(count) {
    const badge = document.getElementById('cartCountBadge');
    if (!badge) return;
    if (count > 0) {
        badge.textContent = count;
        badge.hidden = false;
    } else {
        badge.hidden = true;
    }
}

function openCartDrawer() {
    if (!cartDrawerEl) return;
    cartDrawerEl.classList.add('open');
    cartDrawerEl.setAttribute('aria-hidden', 'false');
    drawerBackdrop.classList.add('open');
    document.getElementById('cartAddedBanner').hidden = true;
    loadCartDrawer();
}

function closeCartDrawer() {
    if (!cartDrawerEl) return;
    cartDrawerEl.classList.remove('open');
    cartDrawerEl.setAttribute('aria-hidden', 'true');
    drawerBackdrop.classList.remove('open');
}

if (cartTrigger) cartTrigger.addEventListener('click', openCartDrawer);
if (cartDrawerClose) cartDrawerClose.addEventListener('click', closeCartDrawer);
if (drawerBackdrop) drawerBackdrop.addEventListener('click', closeCartDrawer);

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
        itemsContainer.innerHTML = '<p class="muted center" style="margin-top:3rem;">Your bag is empty.</p>';
        return;
    }

    itemsContainer.innerHTML = data.items.map(item => `
        <div class="cart-item-row" data-item-id="${item.id}">
            <img src="${item.product_image || 'https://via.placeholder.com/80x80?text=No+Image'}" alt="${item.product_name}">
            <div class="cart-item-info">
                <p class="item-name">${item.product_name}</p>
                ${item.color ? `<p class="muted">Color: ${item.color}</p>` : ''}
                ${item.size ? `<p class="muted">Size: ${item.size}</p>` : ''}
                <div class="qty-control">
                    <button class="qty-btn cart-qty-btn" data-item-id="${item.id}" data-delta="-1">-</button>
                    <span>${item.quantity}</span>
                    <button class="qty-btn cart-qty-btn" data-item-id="${item.id}" data-delta="1">+</button>
                    <button class="remove-link cart-remove-btn" data-item-id="${item.id}">
                        <i class="bi bi-trash"></i> Remove
                    </button>
                </div>
            </div>
            <p style="font-weight:700; white-space:nowrap;">${formatRupees(item.line_total)}</p>
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
                '<p class="center" style="color:var(--color-danger); margin-top:3rem;">Could not load cart.</p>';
        });
}

function updateCartItemQuantity(itemId, newQuantity) {
    const formData = new FormData();
    formData.append('quantity', newQuantity);
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

// ==========================================================
// Add-to-Cart forms (any page: product_detail.html, product
// cards on index/product_list, etc.) -> AJAX submit, open the
// drawer with a "just added" banner instead of navigating.
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
                document.getElementById('cartAddedMessage').textContent = data.message;
                document.getElementById('cartAddedBanner').hidden = false;
                openCartDrawer();
            } else {
                alert(data.message || 'Could not add item to bag.');
            }
        })
        .catch(() => alert('Something went wrong. Please try again.'));
});