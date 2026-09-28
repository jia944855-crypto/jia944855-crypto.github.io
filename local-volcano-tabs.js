/* Keep the retained Creation tabs usable in the offline Elementor mirror. */
(function () {
  const widget = document.querySelector('.elementor-1397 .elementor-element-11c04076');
  if (!widget) return;
  const titles = Array.from(widget.querySelectorAll('.elementor-tab-title[data-tab]'));
  const panels = Array.from(widget.querySelectorAll('.elementor-tab-content[data-tab]'));

  function activate(tab) {
    titles.forEach(function (title) {
      const selected = title.dataset.tab === tab;
      title.classList.toggle('elementor-active', selected);
      title.setAttribute('aria-selected', String(selected));
      title.setAttribute('aria-expanded', String(selected));
      title.tabIndex = selected ? 0 : -1;
    });
    panels.forEach(function (panel) {
      const selected = panel.dataset.tab === tab;
      panel.classList.toggle('elementor-active', selected);
      panel.hidden = !selected;
      panel.style.display = selected ? 'block' : 'none';
    });
  }

  widget.addEventListener('click', function (event) {
    const title = event.target.closest('.elementor-tab-title[data-tab]');
    if (title && widget.contains(title)) activate(title.dataset.tab);
  });
  widget.addEventListener('keydown', function (event) {
    const title = event.target.closest('.elementor-tab-title[data-tab]');
    if (title && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      activate(title.dataset.tab);
    }
  });
  activate('1');
})();
