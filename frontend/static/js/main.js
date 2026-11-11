/*
 * Punkt wejścia skryptów (<script type="module"> w layouts/base.html).
 *
 * Każdy komponent z templates/components/, który ma zachowanie, ma swój moduł
 * w components/ i reaguje wyłącznie na atrybuty data-fm-* (bez inline JS, CSP).
 */
import { initFlashMessages } from "./components/flash-messages.js";
import { initPasswordMeter } from "./components/password-meter.js";
import { initPasswordToggle } from "./components/password-toggle.js";
import { initThemeToggle } from "./components/theme-toggle.js";

initThemeToggle();
initPasswordToggle();
initPasswordMeter();
initFlashMessages();
