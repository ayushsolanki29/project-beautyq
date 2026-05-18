// ===== Sidebar Dropdown Accordion =====
document.addEventListener('DOMContentLoaded', function() {
    // Dropdown buttons toggle
    const dropdownBtns = document.querySelectorAll('.dropdown-btn');
    
    dropdownBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Toggle active class on button
            this.classList.toggle('active');
            
            // Toggle dropdown container
            const dropdownContainer = this.nextElementSibling;
            if (dropdownContainer && dropdownContainer.classList.contains('dropdown-container')) {
                if (dropdownContainer.style.display === 'block') {
                    dropdownContainer.style.display = 'none';
                } else {
                    dropdownContainer.style.display = 'block';
                }
            }
        });
    });

    // Keep active dropdown open based on current URL (optional)
    const currentPath = window.location.pathname;
    const allLinks = document.querySelectorAll('.dropdown-container a, .nav-link');
    allLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.background = 'rgb(31, 31, 31)';
            link.style.color = 'white';
            link.style.borderLeftColor = '#0f0f0f';
            
            // Open parent dropdown if exists
            const parentDropdown = link.closest('.dropdown-container');
            if (parentDropdown) {
                parentDropdown.style.display = 'block';
                const parentBtn = parentDropdown.previousElementSibling;
                if (parentBtn && parentBtn.classList.contains('dropdown-btn')) {
                    parentBtn.classList.add('active');
                }
            }
        }
    });
});

// ===== Sidebar Toggle (Desktop) =====
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    
    // Check if it already has the collapsed style class
    if (sidebar.classList.contains('collapsed')) {
        // 1. Expand Layout
        sidebar.classList.remove('collapsed');
        sidebar.style.width = ''; // Removes inline overrides so CSS takes over
        content.style.marginLeft = ''; // Removes inline overrides so CSS takes over
        
        // 2. Show text labels safely
        document.querySelectorAll('.sidebar .link-text').forEach(el => {
            el.style.display = 'inline';
        });
        document.querySelectorAll('.sidebar .drop-arrow').forEach(el => {
            el.style.display = 'inline-block';
        });
        
        const brandHeading = document.querySelector('.sidebar-brand h4');
        if (brandHeading) {
            brandHeading.innerHTML = 'BeautyQ <span class="text-primary text-sm">PRO</span>';
        }
    } else {
        // 1. Collapse Layout
        sidebar.classList.add('collapsed');
        sidebar.style.width = '80px';
        content.style.marginLeft = '80px';
        
        // 2. Hide text labels safely
        document.querySelectorAll('.sidebar .link-text').forEach(el => {
            el.style.display = 'none';
        });
        document.querySelectorAll('.sidebar .drop-arrow').forEach(el => {
            el.style.display = 'none';
        });
        
        const brandHeading = document.querySelector('.sidebar-brand h4');
        if (brandHeading) {
            brandHeading.innerHTML = 'BQ';
        }
        
        // 3. Auto-close all open sub-dropdown lists
        document.querySelectorAll('.dropdown-container').forEach(el => {
            el.style.display = 'none';
        });
        document.querySelectorAll('.dropdown-btn').forEach(el => {
            el.classList.remove('active');
        });
    }
}
// ===== Mobile Sidebar Toggle =====
function toggleMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    sidebar.classList.toggle('show');
    overlay.classList.toggle('active');
    
    // Prevent body scroll when sidebar is open
    document.body.style.overflow = sidebar.classList.contains('show') ? 'hidden' : '';
}

// Close mobile sidebar when clicking overlay
document.addEventListener('DOMContentLoaded', function() {
    const overlay = document.getElementById('sidebarOverlay');
    if (overlay) {
        overlay.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.remove('show');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }
    
    // Close mobile sidebar on window resize if screen becomes large
    window.addEventListener('resize', function() {
        if (window.innerWidth > 992) {
            const sidebar = document.querySelector('.sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            sidebar.classList.remove('show');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    });
});

// ===== Initialize Bootstrap Tooltips & Popovers (if any) =====
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// ===== Notifications Badge (example) =====
document.addEventListener('DOMContentLoaded', function() {
    const notifBtn = document.querySelector('.fa-bell')?.parentElement;
    if (notifBtn) {
        // Dynamic notifications logic can go here
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById('revenueChart');

    if (ctx) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    data: [4500, 5200, 4800, 6100, 7200, 6800],
                    borderColor: '#b79b7a',   
                    backgroundColor: 'rgba(183,155,122,0.25)', 
                    tension: 0.45,
                    fill: true,
                    pointRadius: 0,   
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#2d2d2a',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: '#9a9a95',
                            font: { size: 12 }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: '#eeeeee' },
                        ticks: {
                            color: '#9a9a95',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }
});