/* Przełącznik motywu (components/theme_toggle.html): przycisk [data-fm-theme-toggle]. */

const STORAGE_KEY = "fm-theme";
const root = document.documentElement;

function storedTheme() {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function applyTheme(theme, persist) {
  root.setAttribute("data-bs-theme", theme);
  if (!persist) {
    return;
  }
  try {
    window.localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Motyw obowiązuje do przeładowania strony.
  }
}

export function initThemeToggle() {
  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-fm-theme-toggle]")) {
      applyTheme(root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark", true);
    }
  });

  // Zmiana motywu systemowego, dopóki użytkownik nie wybrał własnego.
  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (event) => {
      if (!storedTheme()) {
        applyTheme(event.matches ? "dark" : "light", false);
      }
    });
  }
}
