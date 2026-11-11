/* Podgląd hasła (components/form_field.html, password_toggle=True): [data-fm-toggle-password="<id pola>"]. */

function toggle(button) {
  const input = document.getElementById(button.dataset.fmTogglePassword);
  if (!input) {
    return;
  }
  const show = input.type === "password";
  input.type = show ? "text" : "password";
  button.setAttribute("aria-pressed", String(show));
  button.setAttribute("aria-label", show ? "Ukryj hasło" : "Pokaż hasło");
  const icon = button.querySelector(".bi");
  if (icon) {
    icon.classList.toggle("bi-eye", !show);
    icon.classList.toggle("bi-eye-slash", show);
  }
}

export function initPasswordToggle() {
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-fm-toggle-password]");
    if (button) {
      toggle(button);
    }
  });
}
