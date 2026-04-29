// main.js — E-Registro Brasil

document.addEventListener('DOMContentLoaded', function () {

  // Auto-dismiss messages after 5s
  document.querySelectorAll('[data-auto-dismiss]').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.4s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  // Dismiss on button click
  document.querySelectorAll('[data-dismiss]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const target = btn.closest('[data-auto-dismiss]');
      if (target) {
        target.style.transition = 'opacity 0.3s ease';
        target.style.opacity = '0';
        setTimeout(() => target.remove(), 300);
      }
    });
  });

  // Mobile menu toggle
  const menuBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  if (menuBtn && mobileMenu) {
    menuBtn.addEventListener('click', function () {
      mobileMenu.classList.toggle('hidden');
    });
  }

  // CPF mask
  document.querySelectorAll('input[name="cpf"], input[name="customer_cpf"]').forEach(function (input) {
    input.addEventListener('input', function () {
      let v = this.value.replace(/\D/g, '').substring(0, 11);
      v = v.replace(/(\d{3})(\d)/, '$1.$2');
      v = v.replace(/(\d{3})(\d)/, '$1.$2');
      v = v.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
      this.value = v;
    });
  });

  // Phone mask
  document.querySelectorAll('input[name="phone"], input[name="customer_phone"]').forEach(function (input) {
    input.addEventListener('input', function () {
      let v = this.value.replace(/\D/g, '').substring(0, 11);
      if (v.length > 10) {
        v = v.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
      } else {
        v = v.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
      }
      this.value = v;
    });
  });

});
