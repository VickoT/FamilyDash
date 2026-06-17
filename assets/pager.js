// Uppdaterar sid-indikatorn (punkterna) när man swipar mellan skärmar.
(function () {
  function setup() {
    var pager = document.querySelector('.pager');
    var dots = document.querySelectorAll('.pager-dot');
    if (!pager || dots.length === 0) {
      // Dash renderar layouten efter sidladdning – försök igen strax.
      return setTimeout(setup, 300);
    }
    function update() {
      var i = Math.round(pager.scrollLeft / pager.clientWidth);
      dots.forEach(function (d, idx) { d.classList.toggle('active', idx === i); });
    }
    pager.addEventListener('scroll', update, { passive: true });
    update();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
  } else {
    setup();
  }
})();
