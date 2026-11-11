/* Komunikaty flash (components/flash_messages.html): [data-fm-autohide] znikają same po kilku sekundach. */

const AUTOHIDE_MS = 6000;

export function initFlashMessages() {
  document.querySelectorAll("[data-fm-autohide]").forEach((alert) => {
    window.setTimeout(() => {
      window.bootstrap?.Alert.getOrCreateInstance(alert).close();
    }, AUTOHIDE_MS);
  });
}
