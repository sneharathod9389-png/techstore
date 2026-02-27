// ── Auth State ──────────────────────────────────────────────────────────────
let currentUser = null;

async function checkAuth() {
  const res = await fetch('/api/me');
  const data = await res.json();
  currentUser = data.logged_in ? data : null;
  updateNavbar();
}

function updateNavbar() {
  const navOrders = document.getElementById('nav-orders');
  const navCart = document.getElementById('nav-cart');
  const userMenu = document.getElementById('user-menu');
  const btnSignin = document.getElementById('btn-signin');
  const userGreeting = document.getElementById('user-greeting');

  if (currentUser) {
    navOrders && (navOrders.style.display = 'block');
    navCart && (navCart.style.display = 'flex');
    userMenu && (userMenu.style.display = 'flex');
    btnSignin && (btnSignin.style.display = 'none');
    userGreeting && (userGreeting.textContent = `Hi, ${currentUser.name.split(' ')[0]}!`);
    updateCartCount();
  } else {
    navOrders && (navOrders.style.display = 'none');
    navCart && (navCart.style.display = 'none');
    userMenu && (userMenu.style.display = 'none');
    btnSignin && (btnSignin.style.display = 'block');
  }
}

async function updateCartCount() {
  if (!currentUser) return;
  const res = await fetch('/api/cart');
  const items = await res.json();
  const totalQty = items.reduce((s, i) => s + i.quantity, 0);
  const el = document.getElementById('nav-cart-count');
  if (el) el.textContent = totalQty;
}

// ── Modal ────────────────────────────────────────────────────────────────────
function openModal(tab = 'login') {
  const overlay = document.getElementById('modal-overlay');
  if (overlay) {
    overlay.classList.add('active');
    switchTab(tab);
  }
}

function closeModal() {
  const overlay = document.getElementById('modal-overlay');
  if (overlay) overlay.classList.remove('active');
}

function switchTab(tab) {
  document.getElementById('form-login').style.display = tab === 'login' ? 'block' : 'none';
  document.getElementById('form-register').style.display = tab === 'register' ? 'block' : 'none';
  document.getElementById('tab-login').classList.toggle('active', tab === 'login');
  document.getElementById('tab-register').classList.toggle('active', tab === 'register');
}

async function doLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const err = document.getElementById('login-error');
  err.textContent = '';

  const res = await fetch('/api/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email, password})
  });
  const data = await res.json();
  if (data.success) {
    currentUser = {logged_in: true, name: data.name};
    closeModal();
    updateNavbar();
    showToast(`Welcome back, ${data.name.split(' ')[0]}! 👋`, 'success');
  } else {
    err.textContent = data.error || 'Login failed';
  }
}

async function doRegister(e) {
  e.preventDefault();
  const name = document.getElementById('reg-name').value;
  const email = document.getElementById('reg-email').value;
  const phone = document.getElementById('reg-phone').value;
  const password = document.getElementById('reg-password').value;
  const err = document.getElementById('reg-error');
  err.textContent = '';

  const res = await fetch('/api/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name, email, phone, password})
  });
  const data = await res.json();
  if (data.success) {
    currentUser = {logged_in: true, name: data.name};
    closeModal();
    updateNavbar();
    showToast(`Welcome to TechStore, ${data.name.split(' ')[0]}! 🎉`, 'success');
  } else {
    err.textContent = data.error || 'Registration failed';
  }
}

async function logout() {
  await fetch('/api/logout', {method: 'POST'});
  currentUser = null;
  updateNavbar();
  showToast('Signed out successfully.', 'success');
  if (window.location.pathname !== '/' && window.location.pathname !== '/shop') {
    window.location.href = '/';
  }
}

// ── Product Card Renderer ────────────────────────────────────────────────────
function renderProductCard(p, clickable = false) {
  const stars = '★'.repeat(Math.round(p.rating)) + '☆'.repeat(5 - Math.round(p.rating));
  const price = '$' + p.price.toLocaleString('en-US', {minimumFractionDigits: 2});
  const inStock = p.stock > 0;
  const isService = p.category === 'service';

  return `
    <div class="product-card" ${clickable ? `onclick="openProductModal(${p.id})"` : `onclick="window.location='/shop'"` }>
      <div class="product-img">
        <img src="${p.image_url}" alt="${p.name}" loading="lazy"/>
        <span class="cat-badge">${p.category}</span>
      </div>
      <div class="product-info">
        <div class="product-brand">${p.brand}</div>
        <div class="product-name">${p.name}</div>
        <div class="product-rating">
          <span class="stars">${stars}</span>
          <span class="count">${p.rating} (${p.review_count})</span>
        </div>
        <div class="product-footer">
          <div>
            <div class="product-price">${price}</div>
            <div class="product-stock ${!inStock ? 'out' : ''}">${isService ? '✓ Available' : (inStock ? `✓ In Stock` : '✗ Out of Stock')}</div>
          </div>
          <button class="add-btn" ${!inStock ? 'disabled' : ''} onclick="event.stopPropagation(); quickAddToCart(${p.id})">
            ${isService ? 'Book' : 'Add'}
          </button>
        </div>
      </div>
    </div>
  `;
}

// ── Cart Functions ────────────────────────────────────────────────────────────
async function addToCart(productId, qty = 1) {
  if (!currentUser) {
    openModal('login');
    showToast('Please sign in to add items to cart.', 'error');
    return false;
  }
  const res = await fetch('/api/cart', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({product_id: productId, quantity: qty})
  });
  const data = await res.json();
  if (data.success) {
    await updateCartCount();
    showToast('Added to cart! 🛒', 'success');
    return true;
  } else {
    showToast(data.error || 'Failed to add to cart.', 'error');
    return false;
  }
}

async function quickAddToCart(productId) {
  await addToCart(productId, 1);
}

// ── Toast ────────────────────────────────────────────────────────────────────
function showToast(message, type = 'success') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ── Navbar Scroll Effect ──────────────────────────────────────────────────────
window.addEventListener('scroll', () => {
  const navbar = document.getElementById('navbar');
  if (navbar) {
    navbar.style.borderBottomColor = window.scrollY > 10
      ? 'rgba(255,255,255,0.12)'
      : 'rgba(255,255,255,0.08)';
  }
});

// ── Init ──────────────────────────────────────────────────────────────────────
checkAuth();
