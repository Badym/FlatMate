/*
 * Wskaźnik siły hasła (components/form_field.html, meter=True): [data-fm-meter-for="<id pola>"].
 * Ocenia długość względem minlength pola i różnorodność znaków; walidację i tak robi serwer.
 */

const LABELS = ["", "Za krótkie", "Wystarczające", "Dobre", "Silne"];
const CHARACTER_CLASSES = [/[a-ząćęłńóśźż]/, /[A-ZĄĆĘŁŃÓŚŹŻ]/, /\d/, /[^\w\s]/];

export function passwordLevel(value, minLength) {
  if (!value) {
    return 0;
  }
  if (value.length < minLength) {
    return 1;
  }
  const variety = CHARACTER_CLASSES.filter((pattern) => pattern.test(value)).length;
  if (value.length >= minLength + 4 && variety >= 3) {
    return 4;
  }
  return variety >= 2 ? 3 : 2;
}

export function initPasswordMeter() {
  document.querySelectorAll("[data-fm-meter-for]").forEach((meter) => {
    const inputId = meter.dataset.fmMeterFor;
    const input = document.getElementById(inputId);
    if (!input) {
      return;
    }
    const label = document.querySelector(`[data-fm-meter-label="${inputId}"]`);
    const defaultLabel = label ? label.textContent : "";
    const minLength = Number.parseInt(input.getAttribute("minlength"), 10) || 12;

    input.addEventListener("input", () => {
      const level = passwordLevel(input.value, minLength);
      meter.dataset.level = String(level);
      if (label) {
        label.textContent = level === 0 ? defaultLabel : LABELS[level];
      }
    });
  });
}
