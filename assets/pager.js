// Swipe mellan skärmar. Native touch-scroll av overflow-containern är
// opålitlig i kioskens XWayland/Chromium, så vi driver svepet själva med
// pointer-events (funkar för både mus och touch) och scrollar manuellt.
(function () {
  function setup() {
    var pager = document.querySelector('.pager');
    if (!pager) { return setTimeout(setup, 300); }   // Dash renderar layouten efter load
    var dots = document.querySelectorAll('.pager-dot');

    function screenCount() { return pager.querySelectorAll('.screen').length; }

    function updateDots() {
      var i = Math.round(pager.scrollLeft / pager.clientWidth);
      dots.forEach(function (d, idx) { d.classList.toggle('active', idx === i); });
    }

    function go(i) {
      i = Math.max(0, Math.min(screenCount() - 1, i));
      pager.scrollTo({ left: i * pager.clientWidth, behavior: 'smooth' });
    }

    function modalOpen() {
      return Array.prototype.some.call(document.querySelectorAll('.modal'), function (m) {
        return getComputedStyle(m).display !== 'none';
      });
    }

    var dragging = false, startX = 0, startScroll = 0, moved = false, suppressClick = false;

    pager.addEventListener('pointerdown', function (e) {
      if (modalOpen()) return;            // svep inte bakom en öppen modal
      dragging = true; moved = false;
      startX = e.clientX; startScroll = pager.scrollLeft;
      pager.style.scrollSnapType = 'none';
    });

    pager.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      var dx = e.clientX - startX;
      if (Math.abs(dx) > 8) moved = true;
      pager.scrollLeft = startScroll - dx;   // finger-följning
    });

    function endDrag(e) {
      if (!dragging) return;
      dragging = false;
      pager.style.scrollSnapType = 'x mandatory';
      if (moved) suppressClick = true;       // svälj klicket efter ett svep
      var dx = (typeof e.clientX === 'number' ? e.clientX : startX) - startX;
      var current = Math.round(startScroll / pager.clientWidth);
      var target = current;
      if (Math.abs(dx) > pager.clientWidth * 0.12) {
        target = current + (dx < 0 ? 1 : -1);   // svep vänster -> nästa, höger -> föregående
      }
      go(target);
    }

    pager.addEventListener('pointerup', endDrag);
    pager.addEventListener('pointercancel', endDrag);

    // Hindra att ett svep råkar öppna en widget/modal
    pager.addEventListener('click', function (e) {
      if (suppressClick) { e.stopPropagation(); e.preventDefault(); suppressClick = false; }
    }, true);

    pager.addEventListener('scroll', updateDots, { passive: true });
    updateDots();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setup);
  else setup();
})();
