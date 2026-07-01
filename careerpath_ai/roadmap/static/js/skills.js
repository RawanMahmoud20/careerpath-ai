document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('skillsForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        const checkedBoxes = document.querySelectorAll('input[name="skills"]:checked');
        const selectedSkills = Array.from(checkedBoxes).map(cb => cb.value);

        if (selectedSkills.length === 0) {
            if (typeof showToast === 'function') {
                showToast('⚠️ Please select at least one skill before proceeding!');
            } else {
                alert('Please select at least one skill!');
            }
            return;
        }

        fetch(SAVE_SKILLS_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ skills: selectedSkills })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (typeof showToast === 'function') {
                    showToast('✨ Skills saved successfully! Redirecting to roadmap...');
                }
                setTimeout(() => {
                    window.location.href = data.redirect_url || '/roadmap/';
                }, 1500);
            } else {
                if (typeof showToast === 'function') {
                    showToast('❌ Error: ' + (data.error || 'Failed to save skills.'));
                }
            }
        })
        .catch(() => {
            if (typeof showToast === 'function') {
                showToast('❌ Connection error. Please try again.');
            }
        });
    });
});