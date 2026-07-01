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

document.addEventListener('DOMContentLoaded', function () {
//get all task status select elements
  const statusSelects = document.querySelectorAll('.task-status-select');

  statusSelects.forEach(select => {
    select.addEventListener('change', function () {
      const tr = this.closest('tr');
      const taskRef = tr.getAttribute('data-task-ref');
      const newStatus = this.value;
      const badge = tr.querySelector('.status-badge');

     //send a POST request to the backend to update the task status
      fetch('/dashboard/update-status/', { // تأكدي أن هذا الـ URL يطابق الـ path المسجل في urls.py لدالة update_task_status
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken') // جلب توكن الحماية الخاص بـ Django
        },
        body: JSON.stringify({
          task_ref: taskRef,
          status: newStatus
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
         //update the badge class and text based on the new status
          badge.className = 'badge status-badge rounded-pill px-3 py-1.5 ';
          if (newStatus === 'completed') {
            badge.classList.add('bg-success-subtle', 'text-success');
            badge.textContent = 'Completed';
          } else if (newStatus === 'in_progress') {
            badge.classList.add('bg-warning-subtle', 'text-warning-emphasis');
            badge.textContent = 'In Progress';
          } else {
            badge.classList.add('bg-secondary-subtle', 'text-secondary');
            badge.textContent = 'Not Started';
          }
          
          // display a toast notification for successful update
          showToast(`Task updated to ${newStatus.replace('_', ' ')} successfully! ✨`);
        } else {
          showToast('❌ Error: ' + (data.error || 'Could not update status.'));
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('❌ Network error. Try again.');
      });
    });
  });
});

// to get CSRF Token from cookies in Django
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
