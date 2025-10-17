// Landing Page JavaScript Enhancements

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                
                // Special animation for stats counters
                if (entry.target.classList.contains('hero-stats')) {
                    animateStats();
                }
            }
        });
    }, observerOptions);

    // Observe elements for animation
    const animateElements = document.querySelectorAll('.feature-card, .testimonial-card, .process-step, .hero-stats');
    animateElements.forEach(el => {
        observer.observe(el);
    });

    // Stats animation
    function animateStats() {
        const counters = document.querySelectorAll('.counter');
        
        counters.forEach(counter => {
            const target = parseFloat(counter.getAttribute('data-target'));
            const isPercentage = counter.textContent.includes('%');
            const isPlus = counter.textContent.includes('+');
            let currentValue = 0;
            const increment = target / 60; // 60 steps for smooth animation
            
            const timer = setInterval(() => {
                currentValue += increment;
                if (currentValue >= target) {
                    currentValue = target;
                    clearInterval(timer);
                }
                
                let displayValue;
                if (isPercentage) {
                    displayValue = `${currentValue.toFixed(1)}%`;
                } else if (isPlus) {
                    displayValue = `${Math.round(currentValue)}+`;
                } else {
                    displayValue = Math.round(currentValue);
                }
                
                counter.textContent = displayValue;
            }, 30);
        });
    }

    // Parallax effect for hero background
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const heroSection = document.querySelector('.hero-section');
        
        if (heroSection) {
            const rate = scrolled * -0.5;
            heroSection.style.transform = `translateY(${rate}px)`;
        }

        // Floating cards animation based on scroll
        const floatingCards = document.querySelectorAll('.floating-card');
        floatingCards.forEach((card, index) => {
            const rate = scrolled * (0.2 + index * 0.1);
            card.style.transform = `translateY(${rate}px)`;
        });
    });

    // Loading animation for images
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('load', function() {
            this.classList.add('loaded');
        });
        
        // If already loaded
        if (img.complete) {
            img.classList.add('loaded');
        }
    });

    // Add click ripple effect to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    // Navbar background on scroll (for landing page)
    const navbar = document.querySelector('.navbar');
    if (navbar && navbar.classList.contains('bg-transparent')) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 100) {
                navbar.classList.remove('bg-transparent');
                navbar.classList.add('bg-dark');
                navbar.style.transition = 'background-color 0.3s ease';
            } else {
                navbar.classList.remove('bg-dark');
                navbar.classList.add('bg-transparent');
            }
        });
    }

    // Mobile menu optimization
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Close mobile menu when clicking on a link
        const navLinks = navbarCollapse.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992) { // Bootstrap lg breakpoint
                    navbarCollapse.classList.remove('show');
                }
            });
        });
    }

    // Live time update
    function updateLiveTime() {
        const timeElement = document.getElementById('live-time');
        if (timeElement) {
            const now = new Date();
            const timeString = now.toLocaleTimeString('tr-TR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            timeElement.textContent = timeString;
        }
    }
    
    // Update time every second
    updateLiveTime();
    setInterval(updateLiveTime, 1000);

    // Preload critical images
    const criticalImages = [
        'https://images.unsplash.com/photo-1544890225-2f262442d32d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80',
        'https://images.unsplash.com/photo-1578662996442-48f60103fc96?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80'
    ];
    
    criticalImages.forEach(src => {
        const img = new Image();
        img.src = src;
    });
});

// CSS for animations via JavaScript
const style = document.createElement('style');
style.textContent = `
    .animate-in {
        animation: slideInUp 0.8s ease-out forwards;
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    img {
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    img.loaded {
        opacity: 1;
    }
    
    .btn {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
    
    .hero-section {
        transform: translateZ(0);
        backface-visibility: hidden;
    }
    
    .floating-card {
        transform: translateZ(0);
        backface-visibility: hidden;
    }
`;

document.head.appendChild(style);