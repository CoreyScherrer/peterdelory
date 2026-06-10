/* nav.js — progressive enhancement for the mobile hamburger nav.
   The nav works without JS: the .nav-toggle <label> natively flips the
   .nav-toggle-cb checkbox, and CSS reveals the nav. This script only mirrors
   that checkbox state into aria-expanded for assistive tech — it must NOT
   toggle the checkbox itself (the label already does that natively). */
(function () {
  var cb = document.getElementById('nav-toggle-cb');
  var btn = document.querySelector('.nav-toggle');
  if (!cb || !btn) return;

  function sync() {
    btn.setAttribute('aria-expanded', cb.checked ? 'true' : 'false');
  }
  cb.addEventListener('change', sync);
  sync();
})();
