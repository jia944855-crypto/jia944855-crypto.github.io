/* The four category labels are menu controls, not destination pages. */
(function () {
  const selector = 'a[data-submenu-only]';
  const style = document.createElement('style');
  style.textContent = `
    .elementor-nav-menu li.local-submenu-open > .sub-menu {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
    }
    .elementor-nav-menu a[data-submenu-only] { cursor: pointer; }
    .elementor-nav-menu a[data-submenu-only]:focus-visible {
      outline: 2px solid #3882bd;
      outline-offset: 3px;
    }
  `;
  document.head.appendChild(style);

  function closeExcept(current) {
    document.querySelectorAll('li.local-submenu-open').forEach(function (item) {
      if (item === current) return;
      item.classList.remove('local-submenu-open');
      const label = item.querySelector(':scope > ' + selector);
      if (label) label.setAttribute('aria-expanded', 'false');
    });
  }

  document.addEventListener('click', function (event) {
    const label = event.target.closest(selector);
    if (!label) {
      if (!event.target.closest('.elementor-nav-menu')) closeExcept(null);
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    const item = label.closest('li.menu-item-has-children');
    if (!item) return;
    const wasOpen = item.classList.contains('local-submenu-open');
    closeExcept(null);
    if (!wasOpen) {
      item.classList.add('local-submenu-open');
      label.setAttribute('aria-expanded', 'true');
    }
  }, true);

  document.addEventListener('keydown', function (event) {
    const label = event.target.closest(selector);
    if (label && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      label.click();
    } else if (event.key === 'Escape') {
      closeExcept(null);
    }
  }, true);
})();
