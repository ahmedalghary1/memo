(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const body = document.body;

  if (reduceMotion) {
    document.documentElement.classList.remove('motion-capable');
    return;
  }

  const groups = [...document.querySelectorAll(
    'main > section, main > article, main > div, .site-footer, .dash-main > .dash-page'
  )];
  const expandedLayouts = [
    '.product-grid', '.product-rail', '.category-rail__grid', '.service-strip',
    '.info-grid', '.brand-principles', '.policy-steps', '.pdp-gallery',
    '.wishlist-list', '.account-stats'
  ].join(',');
  const backgroundElements = element =>
    element.matches('script,style,link,.ref-hero__overlay,.hero-motion') ||
    (element.matches('img,video,picture') && element.parentElement?.matches('section'));
  const direction = index => {
    const paths = [
      ['0px', '28px', '0deg'],
      ['-28px', '16px', '-.35deg'],
      ['26px', '20px', '.3deg'],
      ['0px', '34px', '0deg']
    ];
    return paths[index % paths.length];
  };

  const getTargets = group => {
    if (group.matches('[data-motion-hero]')) return [];
    let root = group;
    const shell = [...group.children].find(child => child.classList?.contains('shell'));
    if (shell && group.children.length === 1) root = shell;
    const targets = [];
    [...root.children].forEach(child => {
      if (backgroundElements(child)) return;
      if (child.matches(expandedLayouts)) {
        [...child.children].forEach(item => {
          if (!backgroundElements(item)) targets.push(item);
        });
      } else {
        targets.push(child);
      }
    });
    return targets.slice(0, 18);
  };

  groups.forEach(group => {
    const targets = getTargets(group);
    if (!targets.length) return;
    group.dataset.pageMotionGroup = '';
    const initial = group.getBoundingClientRect().top < window.innerHeight * .96;
    group.style.setProperty('--motion-start-delay', initial ? '500ms' : '0ms');
    targets.forEach((target, index) => {
      const [x, y, rotate] = direction(index);
      target.dataset.pageMotionItem = '';
      target.style.setProperty('--motion-order', Math.min(index, 8));
      target.style.setProperty('--motion-x', x);
      target.style.setProperty('--motion-y', y);
      target.style.setProperty('--motion-rotate', rotate);
    });
  });

  const standalone = [
    document.querySelector('.site-header'),
    document.querySelector('.dash-sidebar'),
    document.querySelector('.dash-top')
  ].filter(Boolean);
  standalone.forEach((item, index) => {
    item.dataset.pageMotionItem = '';
    item.style.setProperty('--motion-start-delay', '470ms');
    item.style.setProperty('--motion-order', index);
    item.style.setProperty('--motion-x', index === 1 ? '24px' : '0px');
    item.style.setProperty('--motion-y', index === 1 ? '0px' : '-14px');
  });

  body.classList.add('page-motion-ready');

  const reveal = group => group.classList.add('is-page-visible');
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      reveal(entry.target);
      observer.unobserve(entry.target);
    });
  }, { threshold: .08, rootMargin: '0px 0px -5%' });

  document.querySelectorAll('[data-page-motion-group]').forEach(group => observer.observe(group));
  requestAnimationFrame(() => requestAnimationFrame(() => standalone.forEach(reveal)));
  window.setTimeout(() => body.classList.add('motion-settled'), 1800);
})();
