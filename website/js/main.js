/* ==========================================================================
   ForgeBI Homepage Interactive Script
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    
    // ---------------------------------------------------
    // 1. Particle Generator for Hero Section
    // ---------------------------------------------------
    const initParticles = () => {
        const container = document.getElementById('particles');
        if (!container) return;
        
        const count = 15;
        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.classList.add('particle');
            
            // Randomize position
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.top = `${Math.random() * 100}%`;
            
            // Randomize speed & delay
            const duration = 6 + Math.random() * 6;
            const delay = Math.random() * -8;
            particle.style.animationDuration = `${duration}s`;
            particle.style.animationDelay = `${delay}s`;
            
            // Randomize size
            const size = 1 + Math.random() * 3;
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            
            container.appendChild(particle);
        }
    };
    initParticles();

    // ---------------------------------------------------
    // 2. Sticky Navbar Scroll Effect
    // ---------------------------------------------------
    const navbar = document.getElementById('navbar');
    const handleScroll = () => {
        if (window.scrollY > 40) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    };
    window.addEventListener('scroll', handleScroll);
    handleScroll(); // initialize state

    // ---------------------------------------------------
    // 3. Mobile Menu Toggle
    // ---------------------------------------------------
    const mobileToggle = document.getElementById('mobile-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener('click', () => {
            mobileToggle.classList.toggle('open');
            navMenu.classList.toggle('open');
        });
        
        // Close menu when clicking nav links
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileToggle.classList.remove('open');
                navMenu.classList.remove('open');
            });
        });
    }

    // ---------------------------------------------------
    // 4. Scroll Reveal Animations (Fade-in / Slide-up)
    // ---------------------------------------------------
    const revealElements = document.querySelectorAll('.fade-in-up');
    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.08,
        rootMargin: '0px 0px -40px 0px'
    });
    
    revealElements.forEach(el => revealObserver.observe(el));

    // ---------------------------------------------------
    // 5. Interactive Department Preview Swapper (Platform Section)
    // ---------------------------------------------------
    const deptCards = document.querySelectorAll('.dept-card');
    const previewContainer = document.getElementById('platform-preview-content');
    const browserAddress = document.getElementById('browser-address');
    
    // Mapping of department templates
    const templates = {
        sales: {
            url: 'forgebi.com/sales-dashboard',
            html: `
                <div class="dept-preview sales-preview active">
                    <div class="dept-preview-header">
                        <h3>Sales Performance Cockpit</h3>
                        <div class="badge-gold-outline">Sales Active</div>
                    </div>
                    <div class="preview-metrics">
                        <div class="preview-metric-box">
                            <span>Total Net Sales Value</span>
                            <h4>$1,489,200</h4>
                            <small class="positive">↑ 8.4% MoM</small>
                        </div>
                        <div class="preview-metric-box">
                            <span>Average Basket Value</span>
                            <h4>$456.20</h4>
                            <small class="positive">↑ 2.1% MoM</small>
                        </div>
                    </div>
                    <div class="preview-bar-chart">
                        <div class="bar-chart-title">Branchwise Revenue (Target vs Actual)</div>
                        <div class="mock-bars">
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 80%"></div>
                                <div class="bar-target" style="height: 90%"></div>
                                <span class="bar-label">East</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 95%"></div>
                                <div class="bar-target" style="height: 85%"></div>
                                <span class="bar-label">West</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 60%"></div>
                                <div class="bar-target" style="height: 70%"></div>
                                <span class="bar-label">North</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 100%"></div>
                                <div class="bar-target" style="height: 95%"></div>
                                <span class="bar-label">South</span>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        inventory: {
            url: 'forgebi.com/inventory/aging-stock',
            html: `
                <div class="dept-preview inventory-preview active">
                    <div class="dept-preview-header">
                        <h3>Inventory Aging & Movement</h3>
                        <div class="badge-gold-outline">Stock Active</div>
                    </div>
                    <div class="preview-metrics">
                        <div class="preview-metric-box">
                            <span>Total Stock Valuation</span>
                            <h4>$3,120,400</h4>
                            <small class="negative">↓ 1.4% Stock Cost</small>
                        </div>
                        <div class="preview-metric-box">
                            <span>Out-Of-Stock Events</span>
                            <h4>2 Cases</h4>
                            <small class="positive">Improved 85%</small>
                        </div>
                    </div>
                    <div class="preview-bar-chart">
                        <div class="bar-chart-title">Stock Valuation by Age Block</div>
                        <div class="mock-bars">
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 45%; background-color:#E26D5C;"></div>
                                <span class="bar-label">90d+</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 70%; background-color:#E7C169;"></div>
                                <span class="bar-label">60d-90d</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 98%; background-color:#72B095;"></div>
                                <span class="bar-label">30d-60d</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 100%; background-color:#72B095;"></div>
                                <span class="bar-label">&lt;30d</span>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        accounts: {
            url: 'forgebi.com/accounts/profitability',
            html: `
                <div class="dept-preview accounts-preview active">
                    <div class="dept-preview-header">
                        <h3>Profitability & ROAS Analyzer</h3>
                        <div class="badge-gold-outline">Accounts Sync</div>
                    </div>
                    <div class="preview-metrics">
                        <div class="preview-metric-box">
                            <span>Gross Margin %</span>
                            <h4>42.8%</h4>
                            <small class="positive">↑ 1.8% MoM</small>
                        </div>
                        <div class="preview-metric-box">
                            <span>EBITDA Metric</span>
                            <h4>$342,800</h4>
                            <small class="positive">↑ 11.2% YTD</small>
                        </div>
                    </div>
                    <div class="preview-table-mock">
                        <div class="table-row-mock header">
                            <span>Expense Head</span><span>Budget</span><span>Actual</span>
                        </div>
                        <div class="table-row-mock">
                            <span>Marketing Ads</span><span>$45,000</span><span>$42,100</span>
                        </div>
                        <div class="table-row-mock">
                            <span>SaaS Licenses</span><span>$12,000</span><span>$11,850</span>
                        </div>
                    </div>
                </div>
            `
        },
        procurement: {
            url: 'forgebi.com/procurement/vendors',
            html: `
                <div class="dept-preview procurement-preview active">
                    <div class="dept-preview-header">
                        <h3>Vendor Performance & Lead-time</h3>
                        <div class="badge-gold-outline">Procurement</div>
                    </div>
                    <div class="preview-metrics">
                        <div class="preview-metric-box">
                            <span>Average Lead Time</span>
                            <h4>4.2 Days</h4>
                            <small class="positive">Improved 1.1d</small>
                        </div>
                        <div class="preview-metric-box">
                            <span>Procurement Spend</span>
                            <h4>$894,300</h4>
                            <small class="negative">↑ 4.2% MoM</small>
                        </div>
                    </div>
                    <div class="preview-list-mock">
                        <div class="list-item-mock">
                            <span>Vendor Alpha (Metal Sheets)</span>
                            <strong style="color: #72B095">96% Delivery Rate</strong>
                        </div>
                        <div class="list-item-mock">
                            <span>Vendor Beta (Electronics)</span>
                            <strong style="color: #E7C169">84% Delivery Rate</strong>
                        </div>
                    </div>
                </div>
            `
        },
        marketing: {
            url: 'forgebi.com/marketing/campaigns',
            html: `
                <div class="dept-preview marketing-preview active">
                    <div class="dept-preview-header">
                        <h3>Campaign Performance Analytics</h3>
                        <div class="badge-gold-outline">Marketing live</div>
                    </div>
                    <div class="preview-metrics">
                        <div class="preview-metric-box">
                            <span>Customer Acquisition Cost</span>
                            <h4>$14.20</h4>
                            <small class="positive">↓ 12% Cost Reduction</small>
                        </div>
                        <div class="preview-metric-box">
                            <span>Conversion Rates</span>
                            <h4>3.48%</h4>
                            <small class="positive">↑ 0.6% MoM</small>
                        </div>
                    </div>
                    <div class="preview-bar-chart">
                        <div class="bar-chart-title">Ad Spend Channels ROAS</div>
                        <div class="mock-bars">
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 80%"></div>
                                <span class="bar-label">Google</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 95%"></div>
                                <span class="bar-label">Meta</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 50%"></div>
                                <span class="bar-label">Email</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 60%"></div>
                                <span class="bar-label">LinkedIn</span>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        customercare: {
            url: 'forgebi.com/customer-care/dormant',
            html: `
                <div class="dept-preview customer-preview active">
                    <div class="dept-preview-header">
                        <h3>Customer Health Metrics</h3>
                        <div class="badge-gold-outline">Customer Care</div>
                    </div>
                    <div class="preview-metrics">
                        <div class="preview-metric-box">
                            <span>Net Promoter Score</span>
                            <h4>72 / 100</h4>
                            <small class="positive">↑ 2.1 NPS MoM</small>
                        </div>
                        <div class="preview-metric-box">
                            <span>Dormant Accounts</span>
                            <h4>12 Alert</h4>
                            <small class="negative">High Risk segment</small>
                        </div>
                    </div>
                    <div class="preview-list-mock">
                        <div class="list-item-mock">
                            <span>Acme Corp (No buy 45d)</span>
                            <strong style="color: #E26D5C">High Risk Churn</strong>
                        </div>
                        <div class="list-item-mock">
                            <span>Globex Ltd (No buy 30d)</span>
                            <strong style="color: #E7C169">Medium Risk</strong>
                        </div>
                    </div>
                </div>
            `
        },
        hr: {
            url: 'forgebi.com/hr/headcounts',
            html: `
                <div class="dept-preview hr-preview active">
                    <div class="dept-preview-header">
                        <h3>Human Resources & Headcounts</h3>
                        <div class="badge-gold-outline">HR module</div>
                    </div>
                    <div class="preview-metrics">
                        <div class="preview-metric-box">
                            <span>FTE Count</span>
                            <h4>184 Members</h4>
                            <small class="positive">↑ 4 net growth</small>
                        </div>
                        <div class="preview-metric-box">
                            <span>Monthly Retention Index</span>
                            <h4>98.4%</h4>
                            <small class="positive">↑ 1.2% MoM</small>
                        </div>
                    </div>
                    <div class="preview-bar-chart">
                        <div class="bar-chart-title">Department FTE Allocation</div>
                        <div class="mock-bars">
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 90%"></div>
                                <span class="bar-label">Sales</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 70%"></div>
                                <span class="bar-label">Ops</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 50%"></div>
                                <span class="bar-label">IT</span>
                            </div>
                            <div class="mock-bar-group">
                                <div class="bar-actual" style="height: 40%"></div>
                                <span class="bar-label">Fin</span>
                            </div>
                        </div>
                    </div>
                </div>
            `
        },
        directors: {
            url: 'forgebi.com/directors-hub/cockpit',
            html: `
                <div class="dept-preview directors-preview active">
                    <div class="dept-preview-header">
                        <h3>Directors Executive Cockpit</h3>
                        <div class="badge-gold-outline">Directors Hub</div>
                    </div>
                    <div class="preview-metrics">
                        <div class="preview-metric-box">
                            <span>Group Total NSV</span>
                            <h4>$24.8M</h4>
                            <small class="positive">↑ 14.8% YoY</small>
                        </div>
                        <div class="preview-metric-box">
                            <span>Consolidated Margin</span>
                            <h4>31.4%</h4>
                            <small class="positive">Target closure PASS</small>
                        </div>
                    </div>
                    <div class="preview-table-mock">
                        <div class="table-row-mock header">
                            <span>Regional Hub</span><span>Sales YTD</span><span>KPI Status</span>
                        </div>
                        <div class="table-row-mock">
                            <span>India East</span><span>$12.4M</span><span style="color:#72B095">Optimal</span>
                        </div>
                        <div class="table-row-mock">
                            <span>India South</span><span>$8.2M</span><span style="color:#72B095">Optimal</span>
                        </div>
                    </div>
                </div>
            `
        },
        execution: {
            url: 'forgebi.com/execution-tracker/tasks',
            html: `
                <div class="dept-preview execution-preview active">
                    <div class="dept-preview-header">
                        <h3>Execution Tracker & Milestones</h3>
                        <div class="badge-gold-outline">Execution Track</div>
                    </div>
                    <div class="preview-metrics">
                        <div class="preview-metric-box">
                            <span>Project Completion Rate</span>
                            <h4>92.5%</h4>
                            <small class="positive">↑ 2.5% this week</small>
                        </div>
                        <div class="preview-metric-box">
                            <span>Overdue Tasks</span>
                            <h4>0 Tasks</h4>
                            <small class="positive">All targets green</small>
                        </div>
                    </div>
                    <div class="preview-list-mock">
                        <div class="list-item-mock">
                            <span>Migrate warehouse databases</span>
                            <strong style="color: #72B095">Done</strong>
                        </div>
                        <div class="list-item-mock">
                            <span>Configure custom dashboard views</span>
                            <strong style="color: #C8A04D">In Progress</strong>
                        </div>
                    </div>
                </div>
            `
        }
    };
    
    // Switch preview on hover
    if (deptCards.length > 0 && previewContainer && browserAddress) {
        deptCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                // Remove active class from all cards
                deptCards.forEach(c => c.classList.remove('active'));
                
                // Add active class to hovered card
                card.classList.add('active');
                
                // Get department name
                const dept = card.getAttribute('data-dept');
                if (templates[dept]) {
                    // Update preview content and URL
                    browserAddress.textContent = templates[dept].url;
                    
                    // Simple fade animation
                    previewContainer.style.opacity = 0;
                    setTimeout(() => {
                        previewContainer.innerHTML = templates[dept].html;
                        previewContainer.style.opacity = 1;
                    }, 150);
                }
            });
        });
    }

    // ---------------------------------------------------
    // 6. Showcase Slider (Carousel Carousel in Browser frame)
    // ---------------------------------------------------
    const track = document.getElementById('carousel-track');
    const slides = document.querySelectorAll('.carousel-slide');
    const prevBtn = document.getElementById('carousel-prev');
    const nextBtn = document.getElementById('carousel-next');
    const indicatorsContainer = document.getElementById('carousel-indicators');
    
    if (track && slides.length > 0) {
        let currentIndex = 0;
        
        const updateCarousel = (index) => {
            // Adjust bounds
            if (index < 0) index = slides.length - 1;
            if (index >= slides.length) index = 0;
            
            currentIndex = index;
            
            // Slide transition by percentage
            track.style.transform = `translateX(-${currentIndex * 100}%)`;
            
            // Toggle active classes on slides
            slides.forEach((slide, idx) => {
                if (idx === currentIndex) {
                    slide.classList.add('active');
                } else {
                    slide.classList.remove('active');
                }
            });
            
            // Toggle active classes on indicators
            const indicators = indicatorsContainer.querySelectorAll('.indicator');
            if (indicators.length > 0) {
                indicators.forEach((ind, idx) => {
                    if (idx === currentIndex) {
                        ind.classList.add('active');
                    } else {
                        ind.classList.remove('active');
                    }
                });
            }
        };
        
        // Navigation clicks
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                updateCarousel(currentIndex + 1);
            });
        }
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                updateCarousel(currentIndex - 1);
            });
        }
        
        // Indicator clicks
        if (indicatorsContainer) {
            const indicators = indicatorsContainer.querySelectorAll('.indicator');
            indicators.forEach(indicator => {
                indicator.addEventListener('click', () => {
                    const index = parseInt(indicator.getAttribute('data-index'), 10);
                    updateCarousel(index);
                });
            });
        }
        
        // Auto-run carousel every 8 seconds
        let carouselInterval = setInterval(() => {
            updateCarousel(currentIndex + 1);
        }, 8000);
        
        // Pause auto-run on hover
        const carouselContainer = document.querySelector('.carousel-container');
        if (carouselContainer) {
            carouselContainer.addEventListener('mouseenter', () => {
                clearInterval(carouselInterval);
            });
            carouselContainer.addEventListener('mouseleave', () => {
                carouselInterval = setInterval(() => {
                    updateCarousel(currentIndex + 1);
                }, 8000);
            });
        }
    }

    // ---------------------------------------------------
    // 7. Scroll-Driven Timeline Progress Line
    // ---------------------------------------------------
    const progressFill = document.getElementById('timeline-progress-fill');
    const timelineSteps = document.querySelectorAll('.timeline-step');
    
    if (progressFill && timelineSteps.length > 0) {
        const updateTimelineProgress = () => {
            const container = document.querySelector('.timeline-container');
            const rect = container.getBoundingClientRect();
            
            // Check if timeline section is in viewport
            const viewportHeight = window.innerHeight;
            
            if (rect.top < viewportHeight && rect.bottom > 0) {
                const totalHeight = rect.height;
                const visibleTop = Math.max(0, viewportHeight / 2 - rect.top);
                const progressPercent = Math.min(100, Math.max(0, (visibleTop / totalHeight) * 100));
                
                progressFill.style.height = `${progressPercent}%`;
                
                // Toggle active nodes based on visibility
                timelineSteps.forEach((step, idx) => {
                    const stepRect = step.getBoundingClientRect();
                    if (stepRect.top < viewportHeight / 2) {
                        step.classList.add('active');
                    } else {
                        step.classList.remove('active');
                    }
                });
            }
        };
        
        window.addEventListener('scroll', updateTimelineProgress);
        updateTimelineProgress(); // run once
    }

    // ---------------------------------------------------
    // 8. Custom Button Ripple Effect
    // ---------------------------------------------------
    const rippleButtons = document.querySelectorAll('.btn-ripple');
    rippleButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('btn-ripple-span');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            btn.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});
