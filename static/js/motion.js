/**
 * MEMO — Luxury Fashion Motion & Interaction Engine
 * Follows SKILL-professional-web-motion.md
 * Integrates GSAP, ScrollTrigger, and Three.js ambient luxury canvas.
 */
(() => {
  'use strict';

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isMobile = window.innerWidth < 768;
  const body = document.body;

  // Reduced motion: reveal all immediately and exit
  if (reduceMotion) {
    document.documentElement.classList.remove('motion-capable');
    body.classList.remove('page-motion-ready');
    return;
  }

  const hasGSAP = typeof window.gsap !== 'undefined';
  const hasScrollTrigger = typeof window.ScrollTrigger !== 'undefined';
  const hasThree = typeof window.THREE !== 'undefined';
  const isDashboard = body.classList.contains('dashboard-shell');

  if (hasGSAP && hasScrollTrigger) {
    window.gsap.registerPlugin(window.ScrollTrigger);
    body.classList.add('gsap-active');
  }

  /* --------------------------------------------------------------------------
     1. Luxury Hero Ambient Atmosphere (Three.js)
     Subtle, floating golden/champagne dust filaments reacting to cursor.
     Runs strictly on the storefront homepage hero.
     -------------------------------------------------------------------------- */
  function initThreeHeroAtmosphere() {
    if (!hasThree || isDashboard || reduceMotion) return;
    const canvas = document.getElementById('hero-webgl');
    const heroSection = document.querySelector('.ref-hero');
    if (!canvas || !heroSection) return;

    let renderer, scene, camera, points, animationFrameId;
    let width = heroSection.clientWidth || window.innerWidth;
    let height = heroSection.clientHeight || window.innerHeight;
    let mouseX = 0, mouseY = 0;
    let targetX = 0, targetY = 0;
    let isVisible = true;

    try {
      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 1000);
      camera.position.z = 120;

      renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance'
      });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));

      // Generate a soft radial particle texture in-memory (no network latency)
      const textureCanvas = document.createElement('canvas');
      textureCanvas.width = 64;
      textureCanvas.height = 64;
      const ctx = textureCanvas.getContext('2d');
      const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
      grad.addColorStop(0, 'rgba(255, 245, 220, 1)');
      grad.addColorStop(0.3, 'rgba(225, 179, 77, 0.85)');
      grad.addColorStop(0.7, 'rgba(201, 163, 92, 0.25)');
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 64, 64);
      const particleTexture = new THREE.CanvasTexture(textureCanvas);

      // Luxury particle count: 25 on mobile, 85 on desktop for optimal 60fps
      const particleCount = isMobile ? 25 : 85;
      const geometry = new THREE.BufferGeometry();
      const positions = new Float32Array(particleCount * 3);
      const velocities = [];

      for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;
        positions[i3] = (Math.random() - 0.5) * 220;
        positions[i3 + 1] = (Math.random() - 0.5) * 130;
        positions[i3 + 2] = (Math.random() - 0.5) * 110;

        velocities.push({
          x: (Math.random() - 0.5) * 0.08,
          y: (Math.random() - 0.5) * 0.06 + 0.03, // gentle upward drift
          z: (Math.random() - 0.5) * 0.05,
          phase: Math.random() * Math.PI * 2,
          speed: 0.008 + Math.random() * 0.012
        });
      }

      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

      const material = new THREE.PointsMaterial({
        size: isMobile ? 5.5 : 7.0,
        map: particleTexture,
        transparent: true,
        opacity: 0.82,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      });

      points = new THREE.Points(geometry, material);
      scene.add(points);

      // Subtle mouse parallax
      const onPointerMove = (e) => {
        const rect = heroSection.getBoundingClientRect();
        mouseX = ((e.clientX - rect.left) / width - 0.5) * 2;
        mouseY = ((e.clientY - rect.top) / height - 0.5) * 2;
      };

      if (!isMobile) {
        heroSection.addEventListener('pointermove', onPointerMove, { passive: true });
        heroSection.addEventListener('pointerleave', () => {
          mouseX = 0;
          mouseY = 0;
        });
      }

      // Window resize handling
      const onResize = () => {
        if (!heroSection) return;
        width = heroSection.clientWidth || window.innerWidth;
        height = heroSection.clientHeight || window.innerHeight;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
      };
      window.addEventListener('resize', onResize, { passive: true });

      // Render loop
      let clock = 0;
      function animate() {
        if (!isVisible) return;
        clock += 0.016;

        // Smooth camera lerp towards mouse
        targetX += (mouseX * 12 - targetX) * 0.04;
        targetY += (-mouseY * 8 - targetY) * 0.04;
        camera.position.x = targetX;
        camera.position.y = targetY;
        camera.lookAt(0, 0, 0);

        // Update particle drift
        const pos = geometry.attributes.position.array;
        for (let i = 0; i < particleCount; i++) {
          const i3 = i * 3;
          const v = velocities[i];

          pos[i3] += Math.sin(clock + v.phase) * 0.05 + v.x;
          pos[i3 + 1] += v.y;
          pos[i3 + 2] += Math.cos(clock + v.phase) * 0.04 + v.z;

          // Wrap boundaries
          if (pos[i3 + 1] > 65) pos[i3 + 1] = -65;
          if (pos[i3] > 115) pos[i3] = -115;
          if (pos[i3] < -115) pos[i3] = 115;
        }
        geometry.attributes.position.needsUpdate = true;

        // Subtle overall rotation
        points.rotation.y = clock * 0.02;

        renderer.render(scene, camera);
        animationFrameId = requestAnimationFrame(animate);
      }

      // Pause rendering when hero is out of view (saves battery/GPU)
      if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(([entry]) => {
          isVisible = entry.isIntersecting;
          if (isVisible) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = requestAnimationFrame(animate);
          } else {
            cancelAnimationFrame(animationFrameId);
          }
        }, { threshold: 0.05 });
        observer.observe(heroSection);
      } else {
        animate();
      }

      // Page visibility API (pause when tab is inactive)
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
          isVisible = false;
          cancelAnimationFrame(animationFrameId);
        } else {
          isVisible = true;
          cancelAnimationFrame(animationFrameId);
          animationFrameId = requestAnimationFrame(animate);
        }
      });

      // ScrollTrigger: fade out canvas on scroll
      if (hasGSAP && hasScrollTrigger) {
        window.ScrollTrigger.create({
          trigger: heroSection,
          start: 'top top',
          end: 'bottom top',
          onUpdate: (self) => {
            if (canvas) {
              canvas.style.opacity = String(Math.max(0, 0.88 * (1 - self.progress * 1.3)));
            }
          }
        });
      }
    } catch (e) {
      console.warn('Three.js hero ambient atmosphere initialization skipped:', e);
    }
  }

  /* --------------------------------------------------------------------------
     2. Storefront Motion System (GSAP & ScrollTrigger)
     -------------------------------------------------------------------------- */
  function initStorefrontMotion() {
    if (!hasGSAP) return;
    const gsap = window.gsap;
    const ScrollTrigger = window.ScrollTrigger;

    // --- A. Home Hero Entrance Sequence & Parallax ---
    const hero = document.querySelector('.ref-hero');
    if (hero) {
      const heroImage = hero.querySelector('img');
      const kicker = hero.querySelector('.hero-kicker');
      const heading = hero.querySelector('.ref-hero__copy h1');
      const lead = hero.querySelector('.ref-hero__copy p');
      const buttons = hero.querySelectorAll('.ref-hero__copy > div a');

      // Hero campaign image subtle scale-in
      if (heroImage) {
        gsap.fromTo(heroImage,
          { scale: 1.07 },
          { scale: 1.0, duration: 1.6, ease: 'power2.out', clearProps: 'transform' }
        );

        // Smooth subtle parallax scrub on scroll
        if (ScrollTrigger) {
          gsap.to(heroImage, {
            yPercent: 12,
            ease: 'none',
            scrollTrigger: {
              trigger: hero,
              start: 'top top',
              end: 'bottom top',
              scrub: 0.4
            }
          });
        }
      }

      // Editorial text sequence
      const heroTL = gsap.timeline({ defaults: { ease: 'power3.out' }, delay: 0.2 });
      if (kicker) heroTL.fromTo(kicker, { opacity: 0, y: -14 }, { opacity: 1, y: 0, duration: 0.65 });
      if (heading) heroTL.fromTo(heading, { opacity: 0, y: 32 }, { opacity: 1, y: 0, duration: 0.95 }, '-=0.4');
      if (lead) heroTL.fromTo(lead, { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: 0.8 }, '-=0.55');
      if (buttons && buttons.length) {
        heroTL.fromTo(buttons, { opacity: 0, y: 16 }, { opacity: 1, y: 0, stagger: 0.12, duration: 0.75 }, '-=0.45');
      }

      // Hero scroll click helper
      const heroScroll = hero.querySelector('.hero-scroll');
      if (heroScroll) {
        heroScroll.addEventListener('click', () => {
          const nextSection = hero.nextElementSibling;
          if (nextSection) {
            nextSection.scrollIntoView({ behavior: 'smooth' });
          }
        });
      }
    }

    if (!ScrollTrigger) return;

    // --- B. Category Rail Staggered Reveal ---
    const catRail = document.querySelector('.category-rail');
    if (catRail) {
      const catTitle = catRail.querySelector('.section-title');
      const catItems = catRail.querySelectorAll('.category-rail__grid > a');

      if (catTitle) {
        gsap.from(catTitle, {
          opacity: 0,
          y: 22,
          duration: 0.75,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: catRail,
            start: 'top 86%',
            once: true
          }
        });
      }

      if (catItems.length) {
        gsap.from(catItems, {
          opacity: 0,
          y: 30,
          stagger: 0.07,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: catRail.querySelector('.category-rail__grid') || catRail,
            start: 'top 88%',
            once: true
          }
        });
      }
    }

    // --- C. Featured Products & Best Sellers Rails/Grids ---
    const productSections = document.querySelectorAll('.ref-products');
    productSections.forEach((section) => {
      const title = section.querySelector('.section-title');
      const cards = section.querySelectorAll('.product-card');

      if (title) {
        gsap.from(title, {
          opacity: 0,
          y: 20,
          duration: 0.7,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: section,
            start: 'top 86%',
            once: true
          }
        });
      }

      if (cards.length) {
        gsap.from(cards, {
          opacity: 0,
          y: 34,
          stagger: 0.08,
          duration: 0.85,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: section.querySelector('.product-grid, .product-rail') || section,
            start: 'top 88%',
            once: true
          }
        });
      }
    });

    // --- D. Essentials Video Banner Parallax & Reveal ---
    const banner = document.querySelector('.essentials-banner');
    if (banner) {
      const video = banner.querySelector('video');
      const bannerCopy = banner.querySelector('div') ? Array.from(banner.querySelector('div').children) : [];
      const playBtn = banner.querySelector('.play-button');

      if (video) {
        gsap.to(video, {
          yPercent: 8,
          ease: 'none',
          scrollTrigger: {
            trigger: banner,
            start: 'top bottom',
            end: 'bottom top',
            scrub: 0.5
          }
        });
      }

      if (bannerCopy.length) {
        gsap.from(bannerCopy, {
          opacity: 0,
          y: 24,
          stagger: 0.12,
          duration: 0.85,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: banner,
            start: 'top 82%',
            once: true
          }
        });
      }

      if (playBtn) {
        gsap.from(playBtn, {
          scale: 0.5,
          opacity: 0,
          duration: 0.65,
          ease: 'back.out(1.7)',
          scrollTrigger: {
            trigger: banner,
            start: 'top 82%',
            once: true
          }
        });
      }
    }

    // --- E. Service Guarantee Strip Stagger ---
    const serviceStrip = document.querySelector('.service-strip');
    if (serviceStrip) {
      const items = Array.from(serviceStrip.children).filter((el) => el.tagName === 'DIV');
      if (items.length) {
        gsap.from(items, {
          opacity: 0,
          y: 22,
          stagger: 0.09,
          duration: 0.75,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: serviceStrip,
            start: 'top 88%',
            once: true
          }
        });
      }
    }

    // --- F. Newsletter Section ---
    const newsletter = document.querySelector('.ref-newsletter');
    if (newsletter) {
      const elements = newsletter.querySelectorAll('.shell > *');
      if (elements.length) {
        gsap.from(elements, {
          opacity: 0,
          y: 24,
          stagger: 0.14,
          duration: 0.85,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: newsletter,
            start: 'top 85%',
            once: true
          }
        });
      }
    }

    // --- G. Lookbook / Instagram Strip ---
    const instaStrip = document.querySelector('.instagram-strip');
    if (instaStrip) {
      const title = instaStrip.querySelector('.section-title');
      const photos = instaStrip.querySelectorAll('div:last-child a');

      if (title) {
        gsap.from(title, {
          opacity: 0,
          y: 20,
          duration: 0.7,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: instaStrip,
            start: 'top 85%',
            once: true
          }
        });
      }

      if (photos.length) {
        gsap.from(photos, {
          opacity: 0,
          scale: 0.94,
          stagger: 0.06,
          duration: 0.75,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: instaStrip,
            start: 'top 88%',
            once: true
          }
        });
      }
    }

    // --- H. Collection & Shop Page ---
    const collectionHero = document.querySelector('.collection-hero');
    if (collectionHero) {
      gsap.from(Array.from(collectionHero.children), {
        opacity: 0,
        y: 22,
        stagger: 0.08,
        duration: 0.8,
        ease: 'power3.out'
      });
    }

    const shopResults = document.querySelector('.shop-results');
    if (shopResults) {
      const cards = shopResults.querySelectorAll('.product-card');
      if (cards.length) {
        gsap.from(cards, {
          opacity: 0,
          y: 30,
          stagger: 0.06,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: shopResults,
            start: 'top 88%',
            once: true
          }
        });
      }
    }

    // --- I. Product Detail Page (PDP) & Mobile Sticky Buybar ---
    const pdp = document.querySelector('.pdp');
    if (pdp) {
      const infoItems = pdp.querySelectorAll('.pdp-info > *');
      if (infoItems.length) {
        gsap.from(infoItems, {
          opacity: 0,
          y: 18,
          stagger: 0.05,
          duration: 0.7,
          ease: 'power3.out'
        });
      }

      // Mobile sticky buybar reveal on scroll past main CTA
      const addBtn = pdp.querySelector('[data-add-button]');
      const mobileBuybar = document.querySelector('.mobile-buybar');
      if (addBtn && mobileBuybar) {
        ScrollTrigger.create({
          trigger: addBtn,
          start: 'bottom top',
          onEnter: () => mobileBuybar.classList.add('is-visible'),
          onLeaveBack: () => mobileBuybar.classList.remove('is-visible')
        });
      }
    }

    // --- J. Information Pages (Shipping, Returns, About, Sizes, Contact) ---
    const infoPage = document.querySelector('.info-page');
    if (infoPage) {
      const headerElements = infoPage.querySelectorAll('header > *');
      if (headerElements.length) {
        gsap.from(headerElements, {
          opacity: 0,
          y: 20,
          stagger: 0.08,
          duration: 0.8,
          ease: 'power3.out'
        });
      }

      const infoCards = infoPage.querySelectorAll(
        '.info-grid article, .policy-steps article, .brand-principles article, .contact-layout > *'
      );
      if (infoCards.length) {
        gsap.from(infoCards, {
          opacity: 0,
          y: 26,
          stagger: 0.1,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: infoCards[0].parentElement,
            start: 'top 85%',
            once: true
          }
        });
      }
    }
  }

  /* --------------------------------------------------------------------------
     3. Dashboard Low-Motion Enhancements (Clean & Professional)
     -------------------------------------------------------------------------- */
  function initDashboardMotion() {
    if (!isDashboard || !hasGSAP) return;
    const gsap = window.gsap;

    // Fast, clean stagger for dashboard overview cards and panels
    const dashElements = document.querySelectorAll(
      '.dash-stats article, .dash-panel, .dash-grid > *'
    );
    if (dashElements.length) {
      gsap.from(dashElements, {
        opacity: 0,
        y: 16,
        stagger: 0.06,
        duration: 0.6,
        ease: 'power2.out',
        clearProps: 'transform'
      });
    }

    // Animated count-up for statistics numbers
    const statNumbers = document.querySelectorAll('.dash-stats strong, .account-stats strong');
    statNumbers.forEach((el) => {
      const text = el.textContent.trim();
      const val = parseFloat(text.replace(/[^0-9.]/g, ''));
      if (!isNaN(val) && val > 0) {
        const obj = { count: 0 };
        gsap.to(obj, {
          count: val,
          duration: 1.1,
          ease: 'power2.out',
          onUpdate: () => {
            el.textContent = Math.round(obj.count).toLocaleString('en-US');
          }
        });
      }
    });
  }

  /* --------------------------------------------------------------------------
     4. Universal Micro-interactions
     -------------------------------------------------------------------------- */
  function initMicroInteractions() {
    // A. Back to Top Button
    const backToTop = document.querySelector('[data-back-to-top]');
    if (backToTop) {
      let isVisible = false;
      const toggleBackToTop = () => {
        const shouldShow = window.scrollY > 400;
        if (shouldShow !== isVisible) {
          isVisible = shouldShow;
          backToTop.classList.toggle('is-visible', isVisible);
        }
      };

      window.addEventListener('scroll', toggleBackToTop, { passive: true });
      backToTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    // B. Wishlist Heart Pop Micro-interaction
    const wishButtons = document.querySelectorAll('.wish-form button, .pdp-tools button');
    wishButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        if (hasGSAP) {
          window.gsap.fromTo(
            btn,
            { scale: 0.72 },
            { scale: 1, duration: 0.45, ease: 'back.out(2.2)' }
          );
        }
      });
    });

    // C. Quantity Stepper Micro-bounce
    const steppers = document.querySelectorAll('[data-quantity-stepper]');
    steppers.forEach((stepper) => {
      const buttons = stepper.querySelectorAll('button');
      buttons.forEach((btn) => {
        btn.addEventListener('click', () => {
          if (hasGSAP) {
            window.gsap.fromTo(
              btn,
              { scale: 0.88 },
              { scale: 1, duration: 0.25, ease: 'power2.out' }
            );
          }
        });
      });
    });

    // D. Cart Link Badge Pulse Observer
    const cartBadge = document.querySelector('.cart-link b');
    if (cartBadge && 'MutationObserver' in window) {
      new MutationObserver(() => {
        cartBadge.classList.remove('pulse');
        void cartBadge.offsetWidth; // re-trigger
        cartBadge.classList.add('pulse');
      }).observe(cartBadge, { childList: true, characterData: true, subtree: true });
    }
  }

  /* --------------------------------------------------------------------------
     5. Non-GSAP Graceful Fallback
     -------------------------------------------------------------------------- */
  function initFallbackObserver() {
    if (hasGSAP) return;
    body.classList.add('page-motion-ready');

    const groups = document.querySelectorAll(
      'main > section, main > article, .site-footer, .dash-main > .dash-page'
    );
    const reveal = (el) => el.classList.add('is-page-visible');

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            reveal(entry.target);
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.08, rootMargin: '0px 0px -5%' });

      groups.forEach((group) => {
        group.dataset.pageMotionGroup = '';
        observer.observe(group);
      });
    } else {
      groups.forEach(reveal);
    }
  }

  /* --------------------------------------------------------------------------
     Execution on Ready
     -------------------------------------------------------------------------- */
  function onReady() {
    initThreeHeroAtmosphere();
    initStorefrontMotion();
    initDashboardMotion();
    initMicroInteractions();
    initFallbackObserver();

    window.setTimeout(() => {
      body.classList.add('motion-settled');
    }, 1200);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', onReady);
  } else {
    onReady();
  }
})();
