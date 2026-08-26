const body = document.body;
const qs = (s, root = document) => root.querySelector(s);
const qsa = (s, root = document) => [...root.querySelectorAll(s)];

function dialog(openButton, closeButton, panel, openClass = 'is-open') {
  if (!openButton || !panel) return;
  let previous;
  const focusables = () => qsa('a,button,input,select,textarea,[tabindex]:not([tabindex="-1"])', panel).filter(el => !el.disabled);
  const open = () => { previous = document.activeElement; panel.hidden = false; requestAnimationFrame(() => panel.classList.add(openClass)); body.classList.add('is-locked'); openButton.setAttribute('aria-expanded','true'); focusables()[0]?.focus(); };
  const close = () => { panel.classList.remove(openClass); body.classList.remove('is-locked'); openButton.setAttribute('aria-expanded','false'); setTimeout(() => panel.hidden = true, 360); previous?.focus(); };
  openButton.addEventListener('click', open); closeButton?.addEventListener('click', close);
  panel.addEventListener('keydown', e => { if (e.key === 'Escape') close(); if (e.key === 'Tab') { const f = focusables(); if (!f.length) return; const first=f[0], last=f.at(-1); if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()} } });
}

dialog(qs('[data-menu-open]'), qs('[data-menu-close]'), qs('#mobile-menu'));
dialog(qs('[data-search-open]'), qs('[data-search-close]'), qs('#search-overlay'));
const cartOpen=qs('[data-cart-open]'), cartDrawer=qs('#cart-drawer'), cartBackdrop=qs('[data-cart-backdrop]');
if(cartOpen&&cartDrawer){const close=()=>{cartDrawer.classList.remove('is-open');cartBackdrop?.classList.remove('is-open');body.classList.remove('is-locked');cartOpen.setAttribute('aria-expanded','false');setTimeout(()=>{cartDrawer.hidden=true;if(cartBackdrop)cartBackdrop.hidden=true},300)};cartOpen.addEventListener('click',e=>{e.preventDefault();cartDrawer.hidden=false;if(cartBackdrop)cartBackdrop.hidden=false;requestAnimationFrame(()=>{cartDrawer.classList.add('is-open');cartBackdrop?.classList.add('is-open')});body.classList.add('is-locked');cartOpen.setAttribute('aria-expanded','true');qs('[data-cart-close]',cartDrawer)?.focus()});qs('[data-cart-close]',cartDrawer)?.addEventListener('click',close);cartBackdrop?.addEventListener('click',close);cartDrawer.addEventListener('keydown',e=>{if(e.key==='Escape')close()})}
cartDrawer?.addEventListener('keydown',event=>{if(event.key!=='Tab')return;const focusable=qsa('a,button,input,select,textarea,[tabindex]:not([tabindex="-1"])',cartDrawer).filter(el=>!el.disabled);if(!focusable.length)return;const first=focusable[0],last=focusable.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}});

const menuLinks = qsa('#mobile-menu nav a'); menuLinks.forEach((a,i) => a.style.setProperty('--i', i));
const header = qs('[data-header]'); let lastY = 0;
addEventListener('scroll', () => { const y=scrollY; header?.classList.toggle('is-sticky', y>40); header?.classList.toggle('is-hidden', y>lastY && y>500); lastY=y; }, {passive:true});

const filter = qs('#filters'); const filterOpen=qs('[data-filter-open]'); const filterClose=qs('[data-filter-close]');
if(filter&&filterOpen){filterOpen.addEventListener('click',()=>{filter.classList.add('is-open');body.classList.add('is-locked');filterOpen.setAttribute('aria-expanded','true')});filterClose?.addEventListener('click',()=>{filter.classList.remove('is-open');body.classList.remove('is-locked');filterOpen.setAttribute('aria-expanded','false')})}

const video=qs('[data-pause-offscreen]'); const videoToggle=qs('[data-video-toggle]');
if(video){if(matchMedia('(prefers-reduced-motion: reduce)').matches)video.pause();else new IntersectionObserver(([e])=>e.isIntersecting?video.play().catch(()=>{}):video.pause(),{threshold:.15}).observe(video);videoToggle?.addEventListener('click',()=>{if(video.paused){video.play();videoToggle.textContent='إيقاف';videoToggle.setAttribute('aria-label','إيقاف الفيديو')}else{video.pause();videoToggle.textContent='تشغيل';videoToggle.setAttribute('aria-label','تشغيل الفيديو')}})}

const variantForm=qs('[data-variant-form]');
if(variantForm){const variants=JSON.parse(variantForm.dataset.variants||'[]'), colorInputs=qsa('input[name="color"]',variantForm), sizeInputs=qsa('input[name="size"]',variantForm), id=qs('[data-variant-id]',variantForm), stock=qs('[data-stock]',variantForm), add=qs('[data-add-button]',variantForm), mobile=qs('[data-mobile-add]'), selectedColor=qs('[data-selected-color]',variantForm);
  function update(){const color=qs('input[name="color"]:checked',variantForm)?.value,size=qs('input[name="size"]:checked',variantForm)?.value;colorInputs.forEach(c=>{if(c.checked)selectedColor.textContent=c.dataset.label});sizeInputs.forEach(s=>{const match=variants.some(v=>v.color===color&&v.size===s.value&&v.stock>0);s.disabled=!!color&&!match});const v=variants.find(x=>x.color===color&&x.size===size);if(!v){id.value='';stock.textContent=color?'اختر مقاسك.':'اختر اللون والمقاس لمعرفة التوفر.';stock.className='stock-message';add.disabled=true;add.textContent='اختر المقاس أولًا';if(mobile){mobile.disabled=true;mobile.textContent='اختر المقاس'}return}id.value=v.id;const ok=v.stock>0;add.disabled=!ok;add.textContent=ok?'أضف إلى الحقيبة':'نفدت مؤقتًا';stock.textContent=v.status==='low'?`تبقّت ${v.stock} قطع فقط.`:ok?'متوفر وجاهز للشحن.':'هذا الاختيار غير متوفر.';stock.className=`stock-message ${v.status}`;if(mobile){mobile.disabled=!ok;mobile.textContent=ok?'أضف إلى الحقيبة':'غير متوفر'}}
  [...colorInputs,...sizeInputs].forEach(i=>i.addEventListener('change',update));mobile?.addEventListener('click',()=>variantForm.requestSubmit());
}

qsa('.toast').forEach(t=>setTimeout(()=>t.remove(),4500));

if(variantForm){
  const addButton=qs('[data-add-button]',variantForm), buyButton=qs('[data-buy-button]',variantForm);
  const syncBuy=()=>{if(buyButton)buyButton.disabled=addButton?.disabled??true};
  new MutationObserver(syncBuy).observe(addButton,{attributes:true,attributeFilter:['disabled']});
  variantForm.addEventListener('change',()=>queueMicrotask(syncBuy));
  const firstColor=qs('input[name="color"]',variantForm); if(firstColor&&!qs('input[name="color"]:checked',variantForm))firstColor.click();
  syncBuy();
}
qs('[data-share]')?.addEventListener('click',async()=>{try{if(navigator.share)await navigator.share({title:document.title,url:location.href});else{await navigator.clipboard.writeText(location.href);alert('تم نسخ رابط المنتج.')}}catch(error){if(error.name!=='AbortError')console.warn(error)}});
qsa('.drawer-qty').forEach(form=>{const input=qs('input[name="quantity"]',form);qs('[data-qty-minus]',form)?.addEventListener('click',()=>{input.value=Math.max(Number(input.min)||0,Number(input.value)-1);form.requestSubmit()});qs('[data-qty-plus]',form)?.addEventListener('click',()=>{input.value=Math.min(Number(input.max)||99,Number(input.value)+1);form.requestSubmit()})});
