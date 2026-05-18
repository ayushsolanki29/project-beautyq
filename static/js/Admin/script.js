/**
 * BeautyQ Global Script
 */

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    
    sidebar.classList.toggle('collapsed');
    localStorage.setItem(
        'sidebarState',
        sidebar.classList.contains('collapsed') ? 'mini' : 'full'
    );
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. Restore Sidebar State
    const sidebar = document.getElementById('sidebar');
    if (sidebar && localStorage.getItem('sidebarState') === 'mini') {
        sidebar.classList.add('collapsed');
    }

    // 2. Dropdown Logic
    const dropdownBtns = document.querySelectorAll(".dropdown-btn");
    dropdownBtns.forEach(btn => {
        btn.addEventListener("click", function () {
            this.classList.toggle("active");
            const dropdown = this.nextElementSibling;
            if (dropdown) {
                dropdown.style.display = (dropdown.style.display === "block") ? "none" : "block";
            }
        });
    });

    // 3. Chart Logic (Only if canvas exists)
    const chartCanvas = document.getElementById('revenueChart');
    if (chartCanvas) {
        // We get the data from hidden data-attributes in the HTML
        const labels = JSON.parse(chartCanvas.getAttribute('data-labels') || '[]');
        const data = JSON.parse(chartCanvas.getAttribute('data-values') || '[]');
        initRevenueChart(chartCanvas, labels, data);
    }
});

function initRevenueChart(canvasElement, labels, data) {
    const ctx = canvasElement.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.2)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Revenue',
                data: data,
                borderColor: '#3b82f6',
                borderWidth: 3,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointBackgroundColor: '#3b82f6'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                x: { grid: { display: false } }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. LINE CHART SETUP
    const lineCtx = document.getElementById('analyticsLineChart');
    if (lineCtx) {
        const labels = JSON.parse(lineCtx.getAttribute('data-labels') || '[]');
        const data = JSON.parse(lineCtx.getAttribute('data-values') || '[]');
        
        new Chart(lineCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Revenue',
                    data: data,
                    borderColor: '#3b82f6',
                    tension: 0.4,
                    fill: true,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)'
                }]
            }
        });
    }

    // 2. PIE CHART SETUP
    const pieCtx = document.getElementById('analyticsPieChart');
    if (pieCtx) {
        const labels = JSON.parse(pieCtx.getAttribute('data-labels') || '[]');
        const data = JSON.parse(pieCtx.getAttribute('data-values') || '[]');

        new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: ['#3b82f6', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444']
                }]
            },
            options: {
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
});


// -------------------------------------------------for all users page -------
// Inside your DOMContentLoaded listener in script.js
const userSearch = document.getElementById('userSearch');
if (userSearch) {
    userSearch.addEventListener('keyup', function() {
        const value = this.value.toLowerCase();
        const rows = document.querySelectorAll('#userTable tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(value) ? '' : 'none';
        });
    });
}

function toggleSidebarDropdown(buttonElement) {
    // Toggles active state classes for background & arrow rotation shifts
    buttonElement.classList.toggle("active");
    
    const container = buttonElement.nextElementSibling;
    if (container) {
        if (container.style.display === "block") {
            container.style.display = "none";
        } else {
            container.style.display = "block";
        }
    }
}
 

//------------------------ role_permmisions.html ----------------------------------

// Dynamic redirection based on selected role
if (request.resolver_match.url_name == 'role_permissions') {
    function changeRoleView(roleCode) {
        window.location.href = `?role=${roleCode}`;
    }

    // Handles background updating via AJAX asynchronously when toggle switches are toggled
    function togglePermissionState(checkboxElement) {
        const permissionId = checkboxElement.getAttribute('data-perm-id');
        const isChecked = checkboxElement.checked;

        fetch('/role-permissions/update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Fetches Django's default CSRF safety token
            },
            body: JSON.stringify({
                'id': permissionId,
                'is_allowed': isChecked
            })
        })
        .then(response => response.json())
        .then(data => {
            if(data.status === 'success') {
                console.log("Permission configuration updated smoothly.");
            } else {
                alert("Failed to modify database permission states.");
                checkboxElement.checked = !isChecked; // Reverts switch state if database update fails
            }
        })
        .catch(error => {
            console.error('Error:', error);
            checkboxElement.checked = !isChecked;
        });
    }

    // Standard helper module logic to capture default cross-site request forgery cookies securely
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
}