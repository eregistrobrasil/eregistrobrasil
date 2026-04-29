// cart.js — E-Registro Brasil

function getCookie(name) {
  const cookies = document.cookie.split(';');
  for (let c of cookies) {
    const [k, v] = c.trim().split('=');
    if (k === name) return decodeURIComponent(v);
  }
  return null;
}

document.addEventListener('DOMContentLoaded', function () {

  // Atualizar quantidade via AJAX
  document.querySelectorAll('[data-update-cart]').forEach(function (form) {
    form.addEventListener('change', function () {
      const formData = new FormData(form);
      fetch(form.action, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' },
        body: formData,
      })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          // Atualizar badge do carrinho
          const badge = document.getElementById('cart-badge');
          if (badge && data.cart_count !== undefined) {
            badge.textContent = data.cart_count;
            badge.classList.toggle('hidden', data.cart_count === 0);
          }
          // Reload para atualizar totais
          window.location.reload();
        }
      })
      .catch(() => window.location.reload());
    });
  });

});
