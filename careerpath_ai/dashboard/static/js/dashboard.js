/**
 * Displays a clean toast notification on the bottom right of the screen.
 * @param {string} msg - The message to be displayed.
 * @param {number} duration - Time in milliseconds before the toast disappears.
 */
function showToast(msg, duration = 2500) {
  const toastElement = document.getElementById('cpToast');
  if (!toastElement) return;

  toastElement.textContent = msg;
  toastElement.classList.remove('d-none');
  
  setTimeout(() => {
    toastElement.classList.add('d-none');
  }, duration);
}