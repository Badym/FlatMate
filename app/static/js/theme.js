/*
 * Ustawia motyw przed narysowaniem strony, żeby nie mignął jasny widok.
 * Ładowany synchronicznie w <head>; bez inline JS (CSP: script-src 'self').
 */
(function () {
  "use strict";

  var stored = null;
  try {
    stored = window.localStorage.getItem("fm-theme");
  } catch (error) {
    // Brak dostępu do localStorage (np. tryb prywatny): motyw systemowy.
  }

  var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  var theme = stored === "light" || stored === "dark" ? stored : prefersDark ? "dark" : "light";
  document.documentElement.setAttribute("data-bs-theme", theme);
})();
