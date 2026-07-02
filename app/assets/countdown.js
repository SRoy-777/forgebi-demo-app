(function() {
    // State management
    let previousSales = null;
    const celebratedMilestones = new Set();
    let dailyTargetCelebrated = false;
    let currentAnimationSession = 0;
    
    // Audio Mute state loaded from localStorage
    let isMuted = localStorage.getItem('dashboard_muted') === 'true';

    // Inject dropdown overrides dynamically to bypass aggressive browser caching of static CSS
    const customDropdownStyle = document.createElement('style');
    customDropdownStyle.textContent = `
        #countdown-rm-dropdown,
        #countdown-rm-dropdown *,
        #countdown-zm-dropdown,
        #countdown-zm-dropdown * {
            background-color: #250505 !important;
            background: #250505 !important;
            color: #ffffff !important;
        }
        #countdown-rm-dropdown div[class*="-control"],
        #countdown-zm-dropdown div[class*="-control"],
        #countdown-rm-dropdown div[class*="Select-control"],
        #countdown-zm-dropdown div[class*="Select-control"],
        #countdown-rm-dropdown div[class*="Select__control"],
        #countdown-zm-dropdown div[class*="Select__control"] {
            background-color: #250505 !important;
            background: #250505 !important;
            border: 1px solid rgba(197, 160, 89, 0.3) !important;
            border-radius: 8px !important;
            box-shadow: none !important;
        }
        #countdown-rm-dropdown:hover div,
        #countdown-zm-dropdown:hover div,
        #countdown-rm-dropdown div[class*="-control"]:hover,
        #countdown-zm-dropdown div[class*="-control"]:hover {
            border-color: rgba(197, 160, 89, 0.8) !important;
        }
        #countdown-rm-dropdown div[class*="-placeholder"],
        #countdown-zm-dropdown div[class*="-placeholder"],
        #countdown-rm-dropdown div[class*="Select-placeholder"],
        #countdown-zm-dropdown div[class*="Select-placeholder"],
        #countdown-rm-dropdown .Select-placeholder,
        #countdown-zm-dropdown .Select-placeholder {
            color: rgba(255, 255, 255, 0.7) !important;
            opacity: 0.95 !important;
            background-color: transparent !important;
            background: transparent !important;
        }
        #countdown-rm-dropdown div[class*="-singleValue"],
        #countdown-zm-dropdown div[class*="-singleValue"],
        #countdown-rm-dropdown div[class*="Select-value"],
        #countdown-zm-dropdown div[class*="Select-value"],
        #countdown-rm-dropdown .Select-value-label,
        #countdown-zm-dropdown .Select-value-label,
        #countdown-rm-dropdown span,
        #countdown-zm-dropdown span {
            color: #ffffff !important;
            background-color: transparent !important;
            background: transparent !important;
        }
        #countdown-rm-dropdown input,
        #countdown-zm-dropdown input {
            color: #ffffff !important;
            background-color: transparent !important;
            background: transparent !important;
        }
        #countdown-rm-dropdown div[class*="-menu"],
        #countdown-zm-dropdown div[class*="-menu"],
        #countdown-rm-dropdown div[class*="Select-menu-outer"],
        #countdown-zm-dropdown div[class*="Select-menu-outer"],
        #countdown-rm-dropdown .Select-menu-outer,
        #countdown-zm-dropdown .Select-menu-outer {
            background-color: #1a0505 !important;
            background: #1a0505 !important;
            border: 1px solid rgba(197, 160, 89, 0.4) !important;
            border-radius: 8px !important;
            z-index: 2000 !important;
        }
        #countdown-rm-dropdown div[class*="-menu"] *,
        #countdown-zm-dropdown div[class*="-menu"] * {
            background-color: transparent !important;
            background: transparent !important;
        }
        #countdown-rm-dropdown div[class*="-option"],
        #countdown-zm-dropdown div[class*="-option"],
        #countdown-rm-dropdown div[class*="Select-option"],
        #countdown-zm-dropdown div[class*="Select-option"],
        #countdown-rm-dropdown .VirtualizedSelectOption,
        #countdown-zm-dropdown .VirtualizedSelectOption {
            color: #ffffff !important;
            background-color: transparent !important;
            background: transparent !important;
            padding: 8px 12px !important;
            cursor: pointer;
        }
        #countdown-rm-dropdown div[class*="-option"][class*="-isFocused"],
        #countdown-zm-dropdown div[class*="-option"][class*="-isFocused"],
        #countdown-rm-dropdown div[class*="Select-option"][class*="-isFocused"],
        #countdown-zm-dropdown div[class*="Select-option"][class*="-isFocused"],
        #countdown-rm-dropdown div[class*="Select-option"]:hover,
        #countdown-zm-dropdown div[class*="Select-option"]:hover,
        #countdown-rm-dropdown .VirtualizedSelectFocusedOption,
        #countdown-zm-dropdown .VirtualizedSelectFocusedOption,
        #countdown-rm-dropdown div[class*="-option"]:hover,
        #countdown-zm-dropdown div[class*="-option"]:hover {
            background-color: rgba(197, 160, 89, 0.25) !important;
            background: rgba(197, 160, 89, 0.25) !important;
            color: #ffffff !important;
        }
        #countdown-rm-dropdown div[class*="-option"][class*="-isSelected"],
        #countdown-zm-dropdown div[class*="-option"][class*="-isSelected"],
        #countdown-rm-dropdown div[class*="Select-option"][class*="-isSelected"],
        #countdown-zm-dropdown div[class*="Select-option"][class*="-isSelected"] {
            background-color: rgba(197, 160, 89, 0.45) !important;
            background: rgba(197, 160, 89, 0.45) !important;
            color: #ffffff !important;
        }
        #countdown-rm-dropdown div[class*="-indicatorContainer"],
        #countdown-zm-dropdown div[class*="-indicatorContainer"],
        #countdown-rm-dropdown div[class*="-indicatorContainer"] *,
        #countdown-zm-dropdown div[class*="-indicatorContainer"] *,
        #countdown-rm-dropdown div[class*="Select-clear-zone"],
        #countdown-zm-dropdown div[class*="Select-clear-zone"],
        #countdown-rm-dropdown div[class*="Select-arrow-zone"],
        #countdown-zm-dropdown div[class*="Select-arrow-zone"] {
            color: rgba(197, 160, 89, 0.8) !important;
            background-color: transparent !important;
            background: transparent !important;
        }
        #countdown-rm-dropdown .Select-arrow,
        #countdown-zm-dropdown .Select-arrow {
            border-color: rgba(197, 160, 89, 0.8) transparent transparent !important;
        }
    `;
    document.head.appendChild(customDropdownStyle);


    // Dynamic asset path resolver (for sub-paths/proxies like Hugging Face embedding URLs)
    function getAssetsPath(fileName) {
        const link = document.querySelector('link[href*="countdown.css"]');
        if (link) {
            const href = link.getAttribute('href');
            const idx = href.indexOf('countdown.css');
            if (idx !== -1) {
                return href.substring(0, idx) + fileName;
            }
        }
        return '/assets/' + fileName;
    }

    // Audio Elements
    const gearSound = new Audio(getAssetsPath('gear_spinning.mp3'));
    gearSound.loop = true;
    
    // Log any loading errors
    gearSound.addEventListener('error', (e) => {
        console.error("Gear audio load error. Code:", gearSound.error ? gearSound.error.code : 'unknown', "Message:", gearSound.error ? gearSound.error.message : '');
    });
    
    let fireworksSound = null;
    let fireworksTimeout = null;
    let fadeInterval = null;

    // Particles system globals
    let fireworks = [];
    let particles = [];
    let animFrameId = null;

    // Indian Formatting Helper
    function formatIndian(value) {
        const val = Math.round(value);
        const negative = val < 0;
        const absVal = Math.abs(val);
        let integerStr = absVal.toString();
        
        if (integerStr.length > 3) {
            const lastThree = integerStr.slice(-3);
            let remaining = integerStr.slice(0, -3);
            const parts = [];
            while (remaining.length > 2) {
                parts.unshift(remaining.slice(-2));
                remaining = remaining.slice(0, -2);
            }
            if (remaining.length > 0) {
                parts.unshift(remaining);
            }
            integerStr = parts.join(',') + ',' + lastThree;
        }
        return (negative ? '-' : '') + '₹ ' + integerStr;
    }

    // Audio handlers
    function playGearSound() {
        try {
            gearSound.pause();
            gearSound.currentTime = 0;
            gearSound.volume = 1.0;
            gearSound.play().catch(e => console.warn("Gear audio defer:", e));
        } catch (e) {
            console.error(e);
        }
    }

    function fadeGearSound() {
        try {
            let vol = 1.0;
            const interval = setInterval(() => {
                vol -= 0.25;
                if (vol <= 0) {
                    clearInterval(interval);
                    gearSound.pause();
                } else {
                    gearSound.volume = vol;
                }
            }, 50);
        } catch (e) {
            gearSound.pause();
        }
    }

    function playFireworksSound() {
        try {
            if (fireworksSound) {
                fireworksSound.pause();
                fireworksSound.currentTime = 0;
            } else {
                fireworksSound = new Audio(getAssetsPath('Fireworks.mp3'));
                fireworksSound.muted = isMuted; // Sync initial mute state
                fireworksSound.addEventListener('error', (e) => {
                    console.error("Fireworks audio load error. Code:", fireworksSound.error ? fireworksSound.error.code : 'unknown', "Message:", fireworksSound.error ? fireworksSound.error.message : '');
                });
            }
            
            if (fireworksTimeout) clearTimeout(fireworksTimeout);
            if (fadeInterval) clearInterval(fadeInterval);
            
            fireworksSound.volume = 1.0;
            fireworksSound.play().catch(e => console.warn("Fireworks audio defer:", e));
            
            // Stop and fade out after 5 seconds
            fireworksTimeout = setTimeout(() => {
                let fadeDuration = 1000; // 1 second fade out
                let intervalTime = 50;
                let steps = fadeDuration / intervalTime;
                let volumeStep = 1.0 / steps;
                
                fadeInterval = setInterval(() => {
                    if (fireworksSound.volume > volumeStep) {
                        fireworksSound.volume -= volumeStep;
                    } else {
                        fireworksSound.volume = 0;
                        fireworksSound.pause();
                        clearInterval(fadeInterval);
                    }
                }, intervalTime);
            }, 4000);
        } catch (e) {
            console.error(e);
        }
    }

    // DOM creation helpers
    function createTile(char) {
        const tile = document.createElement('div');
        const span = document.createElement('span');
        span.textContent = char;
        
        if (char === '₹') {
            tile.className = 'flip-tile symbol-tile';
            span.className = 'flip-char symbol-char';
        } else if (char === ',') {
            tile.className = 'flip-tile comma-tile';
            span.className = 'flip-char comma-char';
        } else if (char === ' ') {
            tile.className = 'flip-tile space-tile';
            span.className = 'flip-char space-char';
            tile.style.visibility = 'hidden';
            tile.style.width = '1.5vw';
        } else {
            tile.className = 'flip-tile';
            span.className = 'flip-char';
        }
        
        tile.appendChild(span);
        return tile;
    }

    // Flip Animations
    function flipSymbolDirectly(session, tile, span, nextChar) {
        return new Promise((resolve) => {
            tile.style.transition = 'transform 0.05s ease-in, filter 0.05s ease-in';
            tile.style.transform = 'rotateX(-90deg)';
            tile.style.filter = 'brightness(0.6)';
            
            setTimeout(() => {
                if (currentAnimationSession !== session) {
                    resolve();
                    return;
                }
                
                span.textContent = nextChar;
                
                if (nextChar === '₹') {
                    tile.className = 'flip-tile symbol-tile';
                    span.className = 'flip-char symbol-char';
                    tile.style.visibility = 'visible';
                    tile.style.width = '';
                } else if (nextChar === ',') {
                    tile.className = 'flip-tile comma-tile';
                    span.className = 'flip-char comma-char';
                    tile.style.visibility = 'visible';
                    tile.style.width = '';
                } else if (nextChar === ' ') {
                    tile.className = 'flip-tile space-tile';
                    span.className = 'flip-char space-char';
                    tile.style.visibility = 'hidden';
                    tile.style.width = '1.5vw';
                } else {
                    tile.className = 'flip-tile';
                    span.className = 'flip-char';
                    tile.style.visibility = 'visible';
                    tile.style.width = '';
                }
                
                tile.style.transition = 'none';
                tile.style.transform = 'rotateX(90deg)';
                tile.style.filter = 'brightness(1.4)';
                
                tile.offsetHeight; // trigger reflow
                
                tile.style.transition = 'transform 0.05s ease-out, filter 0.05s ease-out';
                tile.style.transform = 'rotateX(0deg)';
                tile.style.filter = 'brightness(1)';
                
                setTimeout(() => {
                    resolve();
                }, 50);
            }, 50);
        });
    }

    async function flipDigitSequentially(session, tile, span, startDigit, endDigit) {
        let current = startDigit;
        while (current !== endDigit) {
            if (currentAnimationSession !== session) return;
            current = (current + 1) % 10;
            await flipSymbolDirectly(session, tile, span, current.toString());
        }
    }

    function applyGoldGlow(tile) {
        tile.classList.add('glow-gold');
        setTimeout(() => {
            tile.classList.remove('glow-gold');
        }, 500);
    }

    function pulseSalesCard() {
        const card = document.getElementById('sales-card');
        if (card) {
            card.classList.remove('sales-card-pulse');
            card.offsetHeight; // force reflow
            card.classList.add('sales-card-pulse');
        }
    }

    // Particle Classes
    class Particle {
        constructor(x, y, color, speed, angle, gravity, resistance, fade, size, isConfetti = false) {
            this.x = x;
            this.y = y;
            this.color = color;
            this.vx = Math.cos(angle) * speed;
            this.vy = Math.sin(angle) * speed;
            this.gravity = gravity;
            this.resistance = resistance;
            this.fade = fade;
            this.alpha = 1.0;
            this.size = size;
            this.isConfetti = isConfetti;
            this.rotation = Math.random() * Math.PI * 2;
            this.rotSpeed = (Math.random() - 0.5) * 0.25;
        }
        
        update() {
            this.vx *= this.resistance;
            this.vy *= this.resistance;
            this.vy += this.gravity;
            this.x += this.vx;
            this.y += this.vy;
            this.alpha -= this.fade;
            if (this.isConfetti) {
                this.rotation += this.rotSpeed;
            }
        }
        
        draw(ctx) {
            ctx.save();
            ctx.globalAlpha = Math.max(0, this.alpha);
            ctx.translate(this.x, this.y);
            
            if (this.isConfetti) {
                ctx.rotate(this.rotation);
                ctx.fillStyle = this.color;
                ctx.fillRect(-this.size, -this.size / 2, this.size * 2, this.size);
            } else {
                ctx.beginPath();
                ctx.arc(0, 0, this.size, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.shadowBlur = this.size * 2;
                ctx.shadowColor = this.color;
                ctx.fill();
            }
            ctx.restore();
        }
    }

    class Firework {
        constructor(startX, startY, targetX, targetY, color, intensity) {
            this.x = startX;
            this.y = startY;
            this.targetX = targetX;
            this.targetY = targetY;
            this.color = color;
            this.intensity = intensity;
            
            const dx = targetX - startX;
            const dy = targetY - startY;
            this.tx = 40;
            this.vx = dx / this.tx;
            this.vy = dy / this.tx;
            this.gravity = 0.04;
            this.age = 0;
            this.exploded = false;
        }
        
        update() {
            this.x += this.vx;
            this.y += this.vy;
            this.vy += this.gravity;
            this.age++;
            
            if (Math.random() < 0.3) {
                particles.push(new Particle(
                    this.x, this.y, 
                    'rgba(255, 230, 180, 0.3)', 
                    Math.random() * 0.5, Math.random() * Math.PI * 2, 
                    0.01, 0.98, 0.04, 1 + Math.random() * 1.5
                ));
            }
            
            if (this.age >= this.tx || this.y <= this.targetY) {
                this.exploded = true;
                this.explode();
            }
        }
        
        draw(ctx) {
            ctx.beginPath();
            ctx.arc(this.x, this.y, 2.5, 0, Math.PI * 2);
            ctx.fillStyle = '#ffffff';
            ctx.shadowBlur = 8;
            ctx.shadowColor = '#ffeebb';
            ctx.fill();
        }
        
        explode() {
            let count = 40;
            let speedMax = 2.5;
            let colors = [this.color, '#ffffff', '#ffeedd'];
            
            if (this.intensity === 'small') {
                count = 30;
                speedMax = 2.0;
            } else if (this.intensity === 'medium') {
                count = 55;
                speedMax = 3.5;
                colors = [this.color, '#ffd700', '#ffffff', '#ff8800'];
            } else if (this.intensity === 'large') {
                count = 110;
                speedMax = 5.0;
                colors = [this.color, '#ffd700', '#ffffff', '#ff2200', '#e3d2b5'];
            }
            
            for (let i = 0; i < count; i++) {
                const angle = Math.random() * Math.PI * 2;
                const speed = (0.2 + Math.random() * 0.8) * speedMax;
                const color = colors[Math.floor(Math.random() * colors.length)];
                const size = 1 + Math.random() * (this.intensity === 'large' ? 3.0 : 2.0);
                const fade = 0.012 + Math.random() * 0.015;
                const gravity = 0.05;
                const resistance = 0.95;
                
                particles.push(new Particle(
                    this.x, this.y, 
                    color, speed, angle, 
                    gravity, resistance, fade, size
                ));
            }
            
            if (this.intensity === 'large') {
                const confColors = ['#ffd700', '#ffaa00', '#ffffff', '#c5a059'];
                for (let i = 0; i < 35; i++) {
                    const angle = Math.random() * Math.PI * 2;
                    const speed = (0.4 + Math.random() * 0.6) * 3.5;
                    const color = confColors[Math.floor(Math.random() * confColors.length)];
                    const size = 3 + Math.random() * 3;
                    const fade = 0.009 + Math.random() * 0.009;
                    const gravity = 0.07;
                    const resistance = 0.96;
                    
                    particles.push(new Particle(
                        this.x, this.y, 
                        color, speed, angle, 
                        gravity, resistance, fade, size, true
                    ));
                }
            }
        }
    }

    // Canvas management
    function getOrCreateCanvas() {
        let canvas = document.getElementById('celebration-canvas');
        if (!canvas) {
            const hero = document.querySelector('.countdown-hero-screen');
            if (!hero) return null;
            canvas = document.createElement('canvas');
            canvas.id = 'celebration-canvas';
            canvas.style.position = 'absolute';
            canvas.style.top = '0';
            canvas.style.left = '0';
            canvas.style.width = '100%';
            canvas.style.height = '100%';
            canvas.style.pointerEvents = 'none';
            canvas.style.zIndex = '8';
            hero.appendChild(canvas);
            
            const resize = () => {
                canvas.width = hero.clientWidth;
                canvas.height = hero.clientHeight;
            };
            resize();
            window.addEventListener('resize', resize);
            canvas._resizeHandler = resize;
        }
        return canvas;
    }

    function startAnimationLoop() {
        if (animFrameId) return;
        
        const canvas = getOrCreateCanvas();
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        const loop = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            for (let i = fireworks.length - 1; i >= 0; i--) {
                const f = fireworks[i];
                f.update();
                if (f.exploded) {
                    fireworks.splice(i, 1);
                } else {
                    f.draw(ctx);
                }
            }
            
            for (let i = particles.length - 1; i >= 0; i--) {
                const p = particles[i];
                p.update();
                if (p.alpha <= 0) {
                    particles.splice(i, 1);
                } else {
                    p.draw(ctx);
                }
            }
            
            if (fireworks.length === 0 && particles.length === 0) {
                cancelAnimationFrame(animFrameId);
                animFrameId = null;
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                if (canvas.parentNode) {
                    window.removeEventListener('resize', canvas._resizeHandler);
                    canvas.parentNode.removeChild(canvas);
                }
            } else {
                animFrameId = requestAnimationFrame(loop);
            }
        };
        
        animFrameId = requestAnimationFrame(loop);
    }

    function launchFirework(intensity) {
        const canvas = getOrCreateCanvas();
        if (!canvas) return;
        
        const card = document.getElementById('sales-card');
        let startX, startY;
        if (card) {
            const rect = card.getBoundingClientRect();
            const heroRect = card.parentElement.parentElement.getBoundingClientRect();
            startX = rect.left - heroRect.left + rect.width / 2;
            startY = rect.bottom - heroRect.top;
        } else {
            startX = canvas.width / 2;
            startY = canvas.height * 0.8;
        }
        
        const targetX = 0.15 * canvas.width + Math.random() * 0.7 * canvas.width;
        const targetY = 0.1 * canvas.height + Math.random() * 0.45 * canvas.height;
        
        const premiumColors = ['#c5a059', '#ffd700', '#ffffff', '#e3d2b5', '#ffaa00', '#ff2266', '#00ffcc'];
        const color = premiumColors[Math.floor(Math.random() * premiumColors.length)];
        
        fireworks.push(new Firework(startX, startY, targetX, targetY, color, intensity));
        startAnimationLoop();
    }

    function showerConfetti() {
        const canvas = getOrCreateCanvas();
        if (!canvas) return;
        
        const colors = ['#ffd700', '#ffaa00', '#ffffff', '#c5a059', '#e3d2b5'];
        for (let i = 0; i < 120; i++) {
            const x = Math.random() * canvas.width;
            const y = -15 - Math.random() * 30;
            const color = colors[Math.floor(Math.random() * colors.length)];
            const speed = 1 + Math.random() * 2.5;
            const angle = Math.PI / 4 + Math.random() * Math.PI / 2;
            const size = 3 + Math.random() * 4;
            const fade = 0.003 + Math.random() * 0.003;
            const gravity = 0.03 + Math.random() * 0.04;
            const resistance = 0.985;
            
            particles.push(new Particle(
                x, y, 
                color, speed, angle, 
                gravity, resistance, fade, size, true
            ));
        }
        startAnimationLoop();
    }

    function showBanner(text, durationMs) {
        const existing = document.querySelector('.achievement-banner');
        if (existing) existing.remove();
        
        const banner = document.createElement('div');
        banner.className = 'achievement-banner';
        
        const content = document.createElement('div');
        content.className = 'achievement-text';
        content.textContent = text;
        
        banner.appendChild(content);
        
        const hero = document.querySelector('.countdown-hero-screen');
        if (hero) {
            hero.appendChild(banner);
            setTimeout(() => banner.classList.add('show'), 50);
            
            setTimeout(() => {
                banner.classList.remove('show');
                setTimeout(() => banner.remove(), 500);
            }, durationMs);
        }
    }

    // Celebration Orchestrators
    function trigger10LakhCelebration() {
        const card = document.getElementById('sales-card');
        if (card) {
            card.classList.add('sales-card-pulse');
            card.style.boxShadow = '0 0 25px rgba(197, 160, 89, 0.4)';
            setTimeout(() => {
                card.classList.remove('sales-card-pulse');
                card.style.boxShadow = '';
            }, 4000);
        }
        playFireworksSound();
        for (let i = 0; i < 3; i++) {
            setTimeout(() => {
                launchFirework('small');
            }, i * 400);
        }
    }

    function trigger50LakhCelebration() {
        const card = document.getElementById('sales-card');
        if (card) {
            card.classList.add('sales-card-gold-border');
            card.classList.add('sales-card-emphasis');
            setTimeout(() => {
                card.classList.remove('sales-card-gold-border');
                card.classList.remove('sales-card-emphasis');
            }, 5000);
        }
        
        showBanner(`🎉 ₹50 LAKHS ACHIEVED`, 3000);
        playFireworksSound();
        for (let i = 0; i < 9; i++) {
            setTimeout(() => {
                launchFirework(i % 2 === 0 ? 'large' : 'medium');
            }, i * 250);
        }
        setTimeout(() => {
            showerConfetti();
        }, 400);
    }

    function triggerCroreCelebration(croreCount) {
        const card = document.getElementById('sales-card');
        if (card) {
            card.classList.add('sales-card-gold-border');
            card.classList.add('sales-card-emphasis');
            setTimeout(() => {
                card.classList.remove('sales-card-gold-border');
                card.classList.remove('sales-card-emphasis');
            }, 7000);
        }
        
        showBanner(`🎉 ₹${croreCount} ${croreCount === 1 ? 'CRORE' : 'CRORES'} ACHIEVED`, 5000);
        playFireworksSound();
        
        for (let i = 0; i < 12; i++) {
            setTimeout(() => {
                launchFirework(i % 3 === 0 ? 'medium' : 'large');
            }, i * 250);
        }
        
        setTimeout(() => {
            showerConfetti();
        }, 400);
    }

    function triggerDailyTargetCelebration() {
        const card = document.getElementById('sales-card');
        if (card) {
            card.classList.add('sales-card-gold-border');
            card.classList.add('sales-card-emphasis');
            setTimeout(() => {
                card.classList.remove('sales-card-gold-border');
                card.classList.remove('sales-card-emphasis');
            }, 7000);
        }
        
        showBanner(`🎯 DAILY TARGET ACHIEVED`, 5000);
        playFireworksSound();
        
        for (let i = 0; i < 10; i++) {
            setTimeout(() => {
                launchFirework(i % 2 === 0 ? 'large' : 'medium');
            }, i * 300);
        }
        
        showerConfetti();
    }

    function checkAndTriggerCelebrations(currSales, dailyTarget) {
        if (previousSales === null) {
            previousSales = currSales;
            const initialMilestone = Math.floor(currSales / 1000000);
            for (let m = 1; m <= initialMilestone; m++) {
                celebratedMilestones.add(m);
            }
            
            const dailyTargetMet = currSales >= dailyTarget && dailyTarget > 0;
            if (dailyTargetMet) {
                dailyTargetCelebrated = true;
            }
            
            // Trigger the highest achieved celebration on load after 1.2 seconds
            setTimeout(() => {
                if (dailyTargetMet) {
                    triggerDailyTargetCelebration();
                } else if (initialMilestone > 0) {
                    let highestMajorMilestone = 0;
                    for (let m = initialMilestone; m >= 1; m--) {
                        if (m % 10 === 0 || m % 10 === 5) {
                            highestMajorMilestone = m;
                            break;
                        }
                    }
                    
                    if (highestMajorMilestone > 0) {
                        if (highestMajorMilestone % 10 === 0) {
                            triggerCroreCelebration(highestMajorMilestone / 10);
                        } else {
                            trigger50LakhCelebration();
                        }
                    } else {
                        trigger10LakhCelebration();
                    }
                }
            }, 1200);
            
            return;
        }
        
        if (currSales <= previousSales) return;
        
        const prevMilestone = Math.floor(previousSales / 1000000);
        const currMilestone = Math.floor(currSales / 1000000);
        
        let selectedMilestone = null;
        let highestPriority = -1; // -1: none, 0: 10L, 1: 50L, 2: Crore
        
        if (currMilestone > prevMilestone) {
            for (let m = prevMilestone + 1; m <= currMilestone; m++) {
                if (!celebratedMilestones.has(m)) {
                    celebratedMilestones.add(m);
                    
                    let priority = 0;
                    if (m % 10 === 0) {
                        priority = 2; // Crore
                    } else if (m % 10 === 5) {
                        priority = 1; // 50L
                    }
                    
                    if (priority > highestPriority) {
                        highestPriority = priority;
                        selectedMilestone = m;
                    }
                }
            }
            
            // Trigger the single highest priority milestone celebration
            if (selectedMilestone !== null) {
                if (selectedMilestone % 10 === 0) {
                    triggerCroreCelebration(selectedMilestone / 10);
                } else if (selectedMilestone % 10 === 5) {
                    trigger50LakhCelebration();
                } else {
                    trigger10LakhCelebration();
                }
            }
        }
        
        if (dailyTarget > 0 && previousSales < dailyTarget && currSales >= dailyTarget && !dailyTargetCelebrated) {
            dailyTargetCelebrated = true;
            if (selectedMilestone !== null) {
                setTimeout(() => {
                    triggerDailyTargetCelebration();
                }, 6500);
            } else {
                triggerDailyTargetCelebration();
            }
        }
        
        previousSales = currSales;
    }

    // Main API update handle
    window.updateSalesVisuals = function(totalSales, dailyTarget) {
        const formatted = formatIndian(totalSales);
        const container = document.getElementById('countdown-digits');
        if (!container) return;
        
        let tiles = Array.from(container.children);
        
        if (tiles.length === 0) {
            for (let i = 0; i < formatted.length; i++) {
                const tile = createTile(formatted[i]);
                container.appendChild(tile);
            }
            checkAndTriggerCelebrations(totalSales, dailyTarget);
            return;
        }
        
        const diff = formatted.length - tiles.length;
        if (diff > 0) {
            for (let i = 0; i < diff; i++) {
                const tile = createTile(' ');
                container.insertBefore(tile, container.firstChild);
                tiles.unshift(tile);
            }
        }
        
        tiles = Array.from(container.children);
        const targetLength = tiles.length;
        const paddedFormatted = formatted.padStart(targetLength, ' ');
        
        currentAnimationSession++;
        const session = currentAnimationSession;
        
        let hasChanges = false;
        for (let i = 0; i < targetLength; i++) {
            const tile = tiles[i];
            const span = tile.querySelector('.flip-char');
            const oldChar = span ? span.textContent : '';
            const newChar = paddedFormatted[i];
            if (oldChar !== newChar) {
                hasChanges = true;
                break;
            }
        }
        
        if (hasChanges) {
            playGearSound();
            pulseSalesCard();
            
            const flipPromises = [];
            
            for (let i = 0; i < targetLength; i++) {
                const tile = tiles[i];
                const span = tile.querySelector('.flip-char');
                if (!span) continue;
                
                const oldChar = span.textContent;
                const newChar = paddedFormatted[i];
                
                if (oldChar !== newChar) {
                    const delay = i * 40;
                    
                    const promise = new Promise((resolve) => {
                        setTimeout(async () => {
                            if (session !== currentAnimationSession) {
                                resolve();
                                return;
                            }
                            
                            const isOldDigit = /^\d$/.test(oldChar.trim());
                            const isNewDigit = /^\d$/.test(newChar.trim());
                            
                            if (isOldDigit && isNewDigit) {
                                await flipDigitSequentially(session, tile, span, parseInt(oldChar), parseInt(newChar));
                            } else {
                                await flipSymbolDirectly(session, tile, span, newChar);
                            }
                            
                            if (/^\d$/.test(newChar)) {
                                applyGoldGlow(tile);
                            }
                            resolve();
                        }, delay);
                    });
                    flipPromises.push(promise);
                }
            }
            
            Promise.all(flipPromises).then(() => {
                if (session === currentAnimationSession) {
                    fadeGearSound();
                }
            });
        }
        
        checkAndTriggerCelebrations(totalSales, dailyTarget);
    };

    // Autoplay Unlocker for Modern Browsers (Unlocks audio after first user click/tap/keypress)
    let audioUnlocked = false;
    function unlockAudio() {
        if (audioUnlocked) return;
        
        gearSound.play()
            .then(() => {
                gearSound.pause();
                gearSound.currentTime = 0;
            })
            .catch(e => console.warn("Failed to pre-unlock gear audio:", e));
            
        if (!fireworksSound) {
            fireworksSound = new Audio(getAssetsPath('Fireworks.mp3'));
            fireworksSound.muted = isMuted; // Sync initial mute state
            fireworksSound.addEventListener('error', (e) => {
                console.error("Fireworks audio load error. Code:", fireworksSound.error ? fireworksSound.error.code : 'unknown', "Message:", fireworksSound.error ? fireworksSound.error.message : '');
            });
        }
        fireworksSound.play()
            .then(() => {
                fireworksSound.pause();
                fireworksSound.currentTime = 0;
            })
            .catch(e => console.warn("Failed to pre-unlock fireworks audio:", e));
            
        audioUnlocked = true;
        
        window.removeEventListener('click', unlockAudio);
        window.removeEventListener('touchstart', unlockAudio);
        window.removeEventListener('keydown', unlockAudio);
    }
    
    window.addEventListener('click', unlockAudio);
    window.addEventListener('touchstart', unlockAudio);
    window.addEventListener('keydown', unlockAudio);

    // Audio Mute/Unmute Controller & Persistence (Local Storage)
    function applyMuteState() {
        gearSound.muted = isMuted;
        if (fireworksSound) fireworksSound.muted = isMuted;
        
        const iconSpan = document.getElementById('audio-toggle-icon');
        if (iconSpan) {
            iconSpan.textContent = isMuted ? '🔇' : '🔊';
        }
        
        const btn = document.getElementById('audio-toggle-btn');
        if (btn) {
            if (isMuted) {
                btn.classList.add('muted');
            } else {
                btn.classList.remove('muted');
            }
        }
    }
    
    // Set initial mute state
    applyMuteState();
    
    // Periodically search for audio button on load (since Dash loads components asynchronously)
    const syncMuteBtnInterval = setInterval(() => {
        applyMuteState();
    }, 500);
    setTimeout(() => clearInterval(syncMuteBtnInterval), 10000);
    
    // Listen for button click
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('#audio-toggle-btn');
        if (btn) {
            isMuted = !isMuted;
            localStorage.setItem('dashboard_muted', isMuted);
            applyMuteState();
            unlockAudio(); // Bypasses browser user-interaction rules immediately on toggle
        }
    });
})();
