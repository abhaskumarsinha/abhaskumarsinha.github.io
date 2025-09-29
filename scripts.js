// Particle Background with Neural Network Effect
const createParticleBackground = () => {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.querySelector('.particles-background').appendChild(renderer.domElement);

    const particlesCount = 1000;
    const positions = new Float32Array(particlesCount * 3);
    const particlePositions = [];

    for(let i = 0; i < particlesCount * 3; i += 3) {
        const x = (Math.random() - 0.5) * 10;
        const y = (Math.random() - 0.5) * 10;
        const z = (Math.random() - 0.5) * 10;
        positions[i] = x;
        positions[i + 1] = y;
        positions[i + 2] = z;
        particlePositions.push({ x, y, z });
    }

    const particles = new THREE.Points(
        new THREE.BufferGeometry(),
        new THREE.PointsMaterial({
            color: 0x00f6ff,
            size: 0.05,
            transparent: true
        })
    );

    particles.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    scene.add(particles);

    // Neural network lines
    const lineGeometry = new THREE.BufferGeometry();
    const lineMaterial = new THREE.LineBasicMaterial({
        color: 0x00f6ff,
        transparent: true,
        opacity: 0.3
    });
    const linePositions = new Float32Array(particlesCount * 6);
    lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
    scene.add(lines);

    camera.position.z = 5;

    const animate = () => {
        requestAnimationFrame(animate);
        particles.rotation.x += 0.0001;
        particles.rotation.y += 0.0001;

        // Update neural network connections
        let lineIndex = 0;
        const maxDistance = 0.8;
        for(let i = 0; i < particlePositions.length; i++) {
            for(let j = i + 1; j < particlePositions.length; j++) {
                const dx = particlePositions[i].x - particlePositions[j].x;
                const dy = particlePositions[i].y - particlePositions[j].y;
                const dz = particlePositions[i].z - particlePositions[j].z;
                const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);

                if(distance < maxDistance && lineIndex < particlesCount * 2) {
                    linePositions[lineIndex * 3] = particlePositions[i].x;
                    linePositions[lineIndex * 3 + 1] = particlePositions[i].y;
                    linePositions[lineIndex * 3 + 2] = particlePositions[i].z;
                    linePositions[lineIndex * 3 + 3] = particlePositions[j].x;
                    linePositions[lineIndex * 3 + 4] = particlePositions[j].y;
                    linePositions[lineIndex * 3 + 5] = particlePositions[j].z;
                    lineIndex++;
                }
            }
        }
        lines.geometry.attributes.position.needsUpdate = true;

        renderer.render(scene, camera);
    };

    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
};

// Mouse Gradient Spotlight
const createMouseSpotlight = () => {
    const spotlight = document.createElement('div');
    spotlight.className = 'mouse-spotlight';
    document.body.appendChild(spotlight);

    document.addEventListener('mousemove', (e) => {
        spotlight.style.left = e.clientX + 'px';
        spotlight.style.top = e.clientY + 'px';
    });
};

// Custom Cursor
const createCustomCursor = () => {
    const cursor = document.createElement('div');
    cursor.className = 'custom-cursor';
    document.body.appendChild(cursor);

    const cursorTrail = document.createElement('div');
    cursorTrail.className = 'cursor-trail';
    document.body.appendChild(cursorTrail);

    document.addEventListener('mousemove', (e) => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
        cursorTrail.style.left = e.clientX + 'px';
        cursorTrail.style.top = e.clientY + 'px';
    });

    // Add hover effect
    const interactiveElements = document.querySelectorAll('a, button, .project-card, .testimonial-card');
    interactiveElements.forEach(el => {
        el.addEventListener('mouseenter', () => cursor.classList.add('hover'));
        el.addEventListener('mouseleave', () => cursor.classList.remove('hover'));
    });
};

// Holographic Card Tilt Effect
const initHolographicTilt = () => {
    const cards = document.querySelectorAll('.project-card, .testimonial-card');
    
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-5px)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
        });
    });
};

// Scroll-triggered Animations
const initScrollAnimations = () => {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if(entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                
                // Stagger child elements
                const children = entry.target.querySelectorAll('.project-card, .testimonial-card, .skill');
                children.forEach((child, index) => {
                    setTimeout(() => {
                        child.classList.add('fade-in');
                    }, index * 100);
                });
            }
        });
    }, observerOptions);

    const sections = document.querySelectorAll('section');
    sections.forEach(section => observer.observe(section));
};

// Parallax Scrolling
const initParallax = () => {
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.hero, .particles-background');
        
        parallaxElements.forEach(el => {
            const speed = el.dataset.speed || 0.5;
            el.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });
};

// Ripple Effect on Click
const createRippleEffect = () => {
    const buttons = document.querySelectorAll('.cta-button, .project-link');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.className = 'ripple';
            this.appendChild(ripple);
            
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
};

// Initialize all effects
document.addEventListener('DOMContentLoaded', () => {
    createParticleBackground();
    createMouseSpotlight();
    createCustomCursor();
    initHolographicTilt();
    initScrollAnimations();
    initParallax();
    createRippleEffect();
});