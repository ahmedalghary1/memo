(() => {
  'use strict';

  const hero = document.querySelector('[data-hero-sequence]');
  if (!hero || matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const loadFallback = (globalName, fileName) => new Promise((resolve, reject) => {
    if (window[globalName]) return resolve();
    const script = document.createElement('script');
    script.src = `${hero.dataset.vendorBase}${fileName}`;
    script.onload = () => window[globalName] ? resolve() : reject(new Error(`${globalName} unavailable`));
    script.onerror = () => reject(new Error(`Could not load ${fileName}`));
    document.head.appendChild(script);
  });

  async function init() {
    // CDN is primary; the local files keep the hero working when a CDN is blocked.
    await loadFallback('gsap', 'gsap.min.js');
    await loadFallback('ScrollTrigger', 'ScrollTrigger.min.js');
    await loadFallback('Lenis', 'lenis.min.js');
    const { gsap, ScrollTrigger, Lenis } = window;

  gsap.registerPlugin(ScrollTrigger);
  const stage = hero.querySelector('.sequence-hero__stage');
  const canvas = hero.querySelector('.sequence-hero__canvas');
  const context = canvas.getContext('2d', { alpha: false });
  if (!context) return;
  const blendCanvas = document.createElement('canvas');
  const blendContext = blendCanvas.getContext('2d');
  if (!blendContext) return;

  const copy = hero.querySelector('.ref-hero__copy');
  const percent = hero.querySelector('[data-load-percent]');
  const bar = hero.querySelector('[data-load-bar]');
  const count = Number(hero.dataset.frameCount);
  const mobile = matchMedia('(max-width: 767px)').matches;
  const base = `${hero.dataset.frameBase}${mobile ? 'mobile/' : ''}`;
  const frames = new Array(count);
  let loaded = 0;
  let currentFrame = -1;

  const frameUrl = index => `${base}frame_${String(index + 1).padStart(3, '0')}.webp`;
  const updateProgress = () => {
    const progress = Math.round((loaded / count) * 100);
    percent.textContent = `${progress}%`;
    bar.style.width = `${progress}%`;
  };

  const loadFrame = index => new Promise((resolve, reject) => {
    const image = new Image();
    image.decoding = 'async';
    image.onload = () => {
      frames[index] = image;
      loaded += 1;
      updateProgress();
      resolve();
    };
    image.onerror = () => reject(new Error(`Could not load ${frameUrl(index)}`));
    image.src = frameUrl(index);
  });

  const resizeCanvas = () => {
    const bounds = stage.getBoundingClientRect();
    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(bounds.width * pixelRatio);
    canvas.height = Math.round(bounds.height * pixelRatio);
    blendCanvas.width = canvas.width;
    blendCanvas.height = canvas.height;
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    blendContext.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    currentFrame = -1;
    drawFrame(Math.max(0, Math.round((ScrollTrigger.getById('hero-sequence')?.progress || 0) * (count - 1))));
  };

  const drawFrame = index => {
    if (index === currentFrame || !frames[index]) return;
    currentFrame = index;
    const image = frames[index];
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const isPhone = matchMedia('(max-width: 767px)').matches;
    const topInset = isPhone ? 0 : Math.min(90, Math.max(64, height * 0.08));
    const bottomInset = isPhone ? 0 : Math.min(32, height * 0.04);
    const availableHeight = height - topInset - bottomInset;
    // Keep the complete logo and all three looks on phones; crop only the empty sides.
    const scale = isPhone
      ? Math.min(availableHeight / image.naturalHeight, width / (image.naturalWidth * 0.6))
      : Math.min(width / image.naturalWidth, availableHeight / image.naturalHeight);
    const drawWidth = image.naturalWidth * scale;
    const drawHeight = image.naturalHeight * scale;
    const left = (width - drawWidth) / 2;
    const top = topInset + (availableHeight - drawHeight) / 2;
    context.fillStyle = '#282a2c';
    context.fillRect(0, 0, width, height);

    blendContext.clearRect(0, 0, width, height);
    blendContext.drawImage(image, left, top, drawWidth, drawHeight);
    blendContext.globalCompositeOperation = 'destination-in';

    const horizontalFade = blendContext.createLinearGradient(left, 0, left + drawWidth, 0);
    horizontalFade.addColorStop(0, 'transparent');
    horizontalFade.addColorStop(0.16, '#000');
    horizontalFade.addColorStop(0.84, '#000');
    horizontalFade.addColorStop(1, 'transparent');
    blendContext.fillStyle = horizontalFade;
    blendContext.fillRect(0, 0, width, height);

    const verticalFade = blendContext.createLinearGradient(0, top, 0, top + drawHeight);
    verticalFade.addColorStop(0, 'transparent');
    verticalFade.addColorStop(0.04, '#000');
    verticalFade.addColorStop(0.95, '#000');
    verticalFade.addColorStop(1, 'transparent');
    blendContext.fillStyle = verticalFade;
    blendContext.fillRect(0, 0, width, height);
    blendContext.globalCompositeOperation = 'source-over';

    context.drawImage(blendCanvas, 0, 0, width, height);
  };

  const preload = async () => {
    hero.classList.add('is-loading');
    await loadFrame(0);
    let next = 1;
    const workers = Array.from({ length: Math.min(6, count - 1) }, async () => {
      while (next < count) {
        const index = next++;
        await loadFrame(index);
      }
    });
    await Promise.all(workers);
  };

  preload().then(() => {
    resizeCanvas();
    hero.classList.add('is-ready');
    hero.classList.remove('is-loading');

    const lenis = new Lenis({ lerp: 0.1, smoothWheel: true, anchors: true });
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add(time => lenis.raf(time * 1000));
    gsap.ticker.lagSmoothing(0);

    const isMobile = () => matchMedia('(max-width: 767px)').matches;
    const heroScroll = hero.querySelector('.hero-scroll');

    ScrollTrigger.create({
      id: 'hero-sequence',
      trigger: hero,
      pin: stage,
      pinSpacing: false,
      start: 'top top',
      end: 'bottom bottom',
      anticipatePin: 1,
      invalidateOnRefresh: true,
      onUpdate: self => {
        drawFrame(Math.min(count - 1, Math.round(self.progress * (count - 1))));
        const opacity = Math.max(0, 1 - self.progress / 0.12);
        copy.style.opacity = String(opacity);
        copy.style.pointerEvents = opacity > 0.1 ? 'auto' : 'none';
        if (heroScroll) {
          heroScroll.style.opacity = String(opacity);
          heroScroll.style.pointerEvents = opacity > 0.1 ? 'auto' : 'none';
        }
      }
    });

    const onResize = () => {
      resizeCanvas();
      ScrollTrigger.refresh();
    };
    window.addEventListener('resize', onResize, { passive: true });
    ScrollTrigger.refresh();
  }).catch(error => {
    console.error(error);
    hero.classList.remove('is-loading');
    // The first-frame poster stays visible and the rest of the page remains scrollable.
  });
  }

  init().catch(error => console.error(error));
})();
