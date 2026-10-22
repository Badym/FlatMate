/*
 * Zachowania interfejsu: przełącznik motywu, podgląd hasła, wskaźnik siły
 * hasła i automatyczne chowanie komunikatów. Wyłącznie przez atrybuty
 * data-fm-*, bez handlerów inline (CSP).
 */
(function () {
  "use strict";

  var STORAGE_KEY = "fm-theme";
  var root = document.documentElement;

  function readStoredTheme() {
    try {
      return window.localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      return null;
    }
  }

  function setTheme(theme) {
    root.setAttribute("data-bs-theme", theme);
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch (error) {
      // Motyw obowiązuje do przeładowania strony.
    }
  }

  function togglePassword(button) {
    var input = document.getElementById(button.getAttribute("data-fm-toggle-password"));
    if (!input) {
      return;
    }
    var show = input.type === "password";
    input.type = show ? "text" : "password";
    button.setAttribute("aria-pressed", String(show));
    button.setAttribute("aria-label", show ? "Ukryj hasło" : "Pokaż hasło");
    var icon = button.querySelector(".bi");
    if (icon) {
      icon.classList.toggle("bi-eye", !show);
      icon.classList.toggle("bi-eye-slash", show);
    }
  }

  document.addEventListener("click", function (event) {
    var themeToggle = event.target.closest("[data-fm-theme-toggle]");
    if (themeToggle) {
      setTheme(root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark");
      return;
    }
    var passwordToggle = event.target.closest("[data-fm-toggle-password]");
    if (passwordToggle) {
      togglePassword(passwordToggle);
    }
  });

  // Zmiana motywu systemowego, dopóki użytkownik nie wybrał własnego.
  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (event) {
      if (!readStoredTheme()) {
        root.setAttribute("data-bs-theme", event.matches ? "dark" : "light");
      }
    });
  }

  // Wskaźnik siły hasła: długość względem minlength i różnorodność znaków.
  var METER_LABELS = ["", "Za krótkie", "Wystarczające", "Dobre", "Silne"];

  function passwordLevel(value, minLength) {
    if (!value) {
      return 0;
    }
    if (value.length < minLength) {
      return 1;
    }
    var variety = [/[a-ząćęłńóśźż]/, /[A-ZĄĆĘŁŃÓŚŹŻ]/, /\d/, /[^\w\s]/].filter(function (pattern) {
      return pattern.test(value);
    }).length;
    if (value.length >= minLength + 4 && variety >= 3) {
      return 4;
    }
    return variety >= 2 ? 3 : 2;
  }

  document.querySelectorAll("[data-fm-meter-for]").forEach(function (meter) {
    var inputId = meter.getAttribute("data-fm-meter-for");
    var input = document.getElementById(inputId);
    var label = document.querySelector('[data-fm-meter-label="' + inputId + '"]');
    if (!input) {
      return;
    }
    var minLength = parseInt(input.getAttribute("minlength"), 10) || 12;
    var defaultLabel = label ? label.textContent : "";

    input.addEventListener("input", function () {
      var level = passwordLevel(input.value, minLength);
      meter.setAttribute("data-level", String(level));
      if (label) {
        label.textContent = level === 0 ? defaultLabel : METER_LABELS[level];
      }
    });
  });

  // Komunikaty informacyjne znikają same po kilku sekundach.
  document.querySelectorAll("[data-fm-autohide]").forEach(function (alert) {
    window.setTimeout(function () {
      if (window.bootstrap) {
        window.bootstrap.Alert.getOrCreateInstance(alert).close();
      }
    }, 6000);
  });
})();
