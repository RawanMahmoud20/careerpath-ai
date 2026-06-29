/**
 * CareerPath AI - Roadmap Interactive Logic
 * toggle task status and update via AJAX 
 */

document.addEventListener('DOMContentLoaded', function() {
//   close any open status menu when clicking outside of task cards
    document.addEventListener('click', e => {
        if (!e.target.closest('.task-card')) {
            document.querySelectorAll('.status-menu.open').forEach(m => m.classList.remove('open'));
        }
    });
});

// using data-ref attribute to identify the task card and its corresponding menu
function toggleStatusMenu(card) {
    const ref = card.dataset.ref;
    const menuId = 'menu-' + ref.replace(/[^a-z0-9]/gi, '-').toLowerCase();
    const menu = document.getElementById(menuId);
    if (!menu) return;

    document.querySelectorAll('.status-menu.open').forEach(m => {
        if (m !== menu) m.classList.remove('open');
    });
    menu.classList.toggle('open');
}

// send the new status to the backend and update the UI optimistically
function setStatus(e, taskRef, newStatus) {
    e.stopPropagation();  // not allow the click to bubble up to the card and close the menu
    document.querySelectorAll('.status-menu.open').forEach(m => m.classList.remove('open'));

    const cardId = 'task-' + taskRef.replace(/[^a-z0-9]/gi, '-').toLowerCase();
    const card = document.getElementById(cardId);
    if (!card) return;

    // preventing flicker by removing all status classes first
    card.classList.remove('status-not_started', 'status-in_progress', 'status-completed');
    card.classList.add('status-' + newStatus);

    const checkEl = card.querySelector('.task-check');
    if (checkEl) {
        checkEl.textContent = newStatus === 'completed' ? '✓' : newStatus === 'in_progress' ? '⟳' : '';
    }

    // sending data via Fetch API to the enhanced Back-end
    fetch(UPDATE_TASK_URL, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json', 
            'X-CSRFToken': CSRF_TOKEN 
        },
        body: JSON.stringify({ task_ref: taskRef, status: newStatus }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const labels = {
                completed: '✓ Marked complete successfully! ✨',
                in_progress: '⟳ Task is now In Progress',
                not_started: 'Task reset to not started'
            };
            // calling your custom toast notification function defined in base.html
            if (typeof showToast === 'function') {
                showToast(labels[newStatus] || 'Updated successfully');
            }
        } else {
            if (typeof showToast === 'function') {
                showToast('❌ Failed to update: ' + (data.error || 'Server error'));
            }
        }
    })
    .catch(() => {
        if (typeof showToast === 'function') {
            showToast('❌ Error in saving — please check internet connection');
        }
    });
}