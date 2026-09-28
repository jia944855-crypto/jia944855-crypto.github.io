(function () {
  var consentKey = 'santorini-local-cookie-choice';
  var consentedClass = 'santorini-cookie-consented';

  function hasConsent() {
    try {
      return window.localStorage.getItem(consentKey) === '1';
    } catch (error) {
      return false;
    }
  }

  function saveConsent() {
    try {
      window.localStorage.setItem(consentKey, '1');
    } catch (error) {
      // Some file:// browser contexts can disable storage; the current page
      // still receives the class below and closes the dialog immediately.
    }
    document.documentElement.classList.add(consentedClass);
  }

  var style = document.createElement('style');
  style.textContent = '.' + consentedClass + ' .cky-consent-container,' +
    '.' + consentedClass + ' .cky-modal,' +
    '.' + consentedClass + ' .cky-overlay,' +
    '.' + consentedClass + ' .cky-btn-revisit-wrapper { display: none !important; }';
  document.head.appendChild(style);

  if (hasConsent()) {
    document.documentElement.classList.add(consentedClass);
  }

  document.addEventListener('click', function (event) {
    var button = event.target.closest && event.target.closest(
      '[data-cky-tag="accept-button"], ' +
      '[data-cky-tag="reject-button"], ' +
      '[data-cky-tag="detail-accept-button"], ' +
      '[data-cky-tag="detail-reject-button"], ' +
      '[data-cky-tag="detail-save-button"]'
    );

    if (button) {
      saveConsent();
    }
  }, true);
}());
