/* catalogue.js — progressive enhancement for the Catalogue page.
   The full list is already in the DOM, earliest-first, with all decade markers.
   This adds filter-chip toggling and earliest/latest sorting. With JS off the
   complete list still renders; chips simply do nothing. */
(function () {
  var list = document.querySelector('.cat-list');
  if (!list) return;

  var chips = Array.prototype.slice.call(document.querySelectorAll('.cat-chip'));
  var sortBtn = document.querySelector('.cat-sort');
  var rows = Array.prototype.slice.call(list.querySelectorAll('.cat-row'));
  var decades = Array.prototype.slice.call(list.querySelectorAll('.cat-decade'));
  // Remember the original (earliest-first, with decade markers) DOM order.
  var originalOrder = Array.prototype.slice.call(list.children);
  var activeGroup = 'all';
  var latestFirst = false;

  function applyFilter() {
    rows.forEach(function (row) {
      var groups = (row.getAttribute('data-groups') || '').split(/\s+/);
      var show = activeGroup === 'all' || groups.indexOf(activeGroup) !== -1;
      row.hidden = !show;
    });
    // Hide a decade marker when every row beneath it (until the next marker) is hidden.
    if (!latestFirst) {
      decades.forEach(function (marker) {
        var visible = false;
        var node = marker.nextElementSibling;
        while (node && !node.classList.contains('cat-decade')) {
          if (node.classList.contains('cat-row') && !node.hidden) { visible = true; break; }
          node = node.nextElementSibling;
        }
        marker.hidden = !visible;
      });
    }
  }

  function render() {
    if (latestFirst) {
      // Flat list, newest-first, no decade markers.
      decades.forEach(function (m) { m.hidden = true; });
      rows.slice()
        .sort(function (a, b) {
          return (parseInt(b.getAttribute('data-year'), 10) || 0) -
                 (parseInt(a.getAttribute('data-year'), 10) || 0);
        })
        .forEach(function (row) { list.appendChild(row); });
    } else {
      // Restore the original earliest-first order with decade markers.
      originalOrder.forEach(function (node) { list.appendChild(node); });
    }
    applyFilter();
  }

  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      chips.forEach(function (c) { c.setAttribute('aria-pressed', 'false'); });
      chip.setAttribute('aria-pressed', 'true');
      activeGroup = chip.getAttribute('data-group') || 'all';
      applyFilter();
    });
  });

  if (sortBtn) {
    sortBtn.addEventListener('click', function () {
      latestFirst = !latestFirst;
      sortBtn.textContent = latestFirst ? 'Sort: Latest first' : 'Sort: Earliest first';
      render();
    });
  }
})();
