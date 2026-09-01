const body = document.body;
const qs = (s, root = document) => root.querySelector(s);
const qsa = (s, root = document) => [...root.querySelectorAll(s)];

function dialog(openButton, closeButton, panel, openClass = 'is-open') {
  if (!openButton || !panel) return;
  let previous;
  const focusables = () => qsa('a,button,input,select,textarea,[tabindex]:not([tabindex="-1"])', panel).filter(el => !el.disabled && el.tabIndex !== -1);
  const open = () => { previous = document.activeElement; panel.hidden = false; requestAnimationFrame(() => panel.classList.add(openClass)); body.classList.add('is-locked'); openButton.setAttribute('aria-expanded','true'); focusables()[0]?.focus(); };
  const close = () => { panel.classList.remove(openClass); body.classList.remove('is-locked'); openButton.setAttribute('aria-expanded','false'); setTimeout(() => panel.hidden = true, 360); previous?.focus(); };
  openButton.addEventListener('click', open); closeButton?.addEventListener('click', close);
  qsa('[data-dialog-dismiss]', panel).forEach(button => button.addEventListener('click', close));
  panel.addEventListener('keydown', e => { if (e.key === 'Escape') close(); if (e.key === 'Tab') { const f = focusables(); if (!f.length) return; const first=f[0], last=f.at(-1); if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()} } });
}

dialog(qs('[data-menu-open]'), qs('[data-menu-close]'), qs('#mobile-menu'));
dialog(qs('[data-search-open]'), qs('[data-search-close]'), qs('#search-overlay'));
const cartOpen=qs('[data-cart-open]'), cartDrawer=qs('#cart-drawer'), cartBackdrop=qs('[data-cart-backdrop]');
if(cartOpen&&cartDrawer){let cartPrevious;const close=()=>{cartDrawer.classList.remove('is-open');cartBackdrop?.classList.remove('is-open');body.classList.remove('is-locked');cartOpen.setAttribute('aria-expanded','false');setTimeout(()=>{cartDrawer.hidden=true;if(cartBackdrop)cartBackdrop.hidden=true},300);cartPrevious?.focus()};cartOpen.addEventListener('click',e=>{e.preventDefault();cartPrevious=document.activeElement;cartDrawer.hidden=false;if(cartBackdrop)cartBackdrop.hidden=false;requestAnimationFrame(()=>{cartDrawer.classList.add('is-open');cartBackdrop?.classList.add('is-open')});body.classList.add('is-locked');cartOpen.setAttribute('aria-expanded','true');qs('[data-cart-close]',cartDrawer)?.focus()});qs('[data-cart-close]',cartDrawer)?.addEventListener('click',close);cartBackdrop?.addEventListener('click',close);cartDrawer.addEventListener('keydown',e=>{if(e.key==='Escape')close()})}
cartDrawer?.addEventListener('keydown',event=>{if(event.key!=='Tab')return;const focusable=qsa('a,button,input,select,textarea,[tabindex]:not([tabindex="-1"])',cartDrawer).filter(el=>!el.disabled);if(!focusable.length)return;const first=focusable[0],last=focusable.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}});

const menuLinks = qsa('#mobile-menu nav a'); menuLinks.forEach((a,i) => a.style.setProperty('--i', i));
const header = qs('[data-header]'); let lastY = 0;
addEventListener('scroll', () => { const y=scrollY; header?.classList.toggle('is-sticky', y>40); header?.classList.toggle('is-hidden', y>lastY && y>500); lastY=y; }, {passive:true});

const filter=qs('#filters'),filterOpen=qs('[data-filter-open]'),filterClose=qs('[data-filter-close]'),filterBackdrop=qs('[data-filter-backdrop]');
if(filter&&filterOpen){
  const filterMobile=matchMedia('(max-width:920px)');
  const closeFilter=()=>{
    filter.classList.remove('is-open');filterBackdrop?.classList.remove('is-open');body.classList.remove('is-locked');filterOpen.setAttribute('aria-expanded','false');
    if(filterMobile.matches)filter.inert=true;
    setTimeout(()=>{if(filterBackdrop)filterBackdrop.hidden=true},280);
    filterOpen.focus();
  };
  const openFilter=()=>{
    if(!filterMobile.matches){filter.scrollIntoView({behavior:'smooth',block:'start'});return}
    filter.inert=false;if(filterBackdrop)filterBackdrop.hidden=false;
    requestAnimationFrame(()=>{filter.classList.add('is-open');filterBackdrop?.classList.add('is-open')});
    body.classList.add('is-locked');filterOpen.setAttribute('aria-expanded','true');
    qs('button,input,select,a',filter)?.focus();
  };
  const syncFilterMode=()=>{filter.inert=filterMobile.matches&&!filter.classList.contains('is-open');if(!filterMobile.matches){filterBackdrop?.classList.remove('is-open');if(filterBackdrop)filterBackdrop.hidden=true;body.classList.remove('is-locked')}};
  filterOpen.addEventListener('click',openFilter);filterClose?.addEventListener('click',closeFilter);filterBackdrop?.addEventListener('click',closeFilter);
  filter.addEventListener('keydown',event=>{
    if(event.key==='Escape'){closeFilter();return}
    if(event.key!=='Tab'||!filterMobile.matches)return;
    const focusable=qsa('a,button,input,select,[tabindex]:not([tabindex="-1"])',filter).filter(element=>!element.disabled&&element.offsetParent!==null);
    if(!focusable.length)return;
    const first=focusable[0],last=focusable.at(-1);
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}
    else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}
  });
  filterMobile.addEventListener('change',syncFilterMode);syncFilterMode();
}

const preserveQuery=(form,allowedKeys=[])=>{
  const params=new URLSearchParams(location.search);
  params.forEach((value,key)=>{
    if(key==='page'||allowedKeys.includes(key)||form.elements.namedItem(key))return;
    const hidden=document.createElement('input');hidden.type='hidden';hidden.name=key;hidden.value=value;form.append(hidden);
  });
};
const sortForm=qs('.sort-form'),sortSelect=qs('.sort-form select');
if(sortForm&&sortSelect){
  sortSelect.removeAttribute('onchange');
  sortSelect.addEventListener('change',()=>sortForm.requestSubmit());
  sortForm.addEventListener('submit',event=>preserveQuery(event.currentTarget,['sort']));
}
qs('.filters form')?.addEventListener('submit',event=>preserveQuery(event.currentTarget,['size','color','price_min','price_max','available']));

qsa('.pagination a').forEach(link=>{
  const page=new URL(link.href,location.href).searchParams.get('page');
  const params=new URLSearchParams(location.search);if(page)params.set('page',page);link.href=`?${params}`;
});
qsa('.active-filters a[data-filter-key]').forEach(link=>{
  const key=link.dataset.filterKey,value=link.dataset.filterValue,params=new URLSearchParams(location.search),values=params.getAll(key).filter(item=>item!==value);
  params.delete(key);values.forEach(item=>params.append(key,item));params.delete('page');link.href=`?${params}`;
});

qsa('.desktop-nav a,.mobile-menu nav a').forEach(link=>{
  const target=new URL(link.href,location.href);
  if(target.pathname===location.pathname&&!target.search)link.setAttribute('aria-current','page');
});

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
qsa('[data-quantity-stepper]').forEach(stepper=>{
  const input=qs('input[name="quantity"]',stepper),minimum=Math.max(1,Number(input?.min)||1);
  if(!input)return;
  const commit=value=>{
    input.value=String(Math.max(minimum,Number.isFinite(value)?Math.trunc(value):minimum));
    input.dispatchEvent(new Event('change',{bubbles:true}));
    if(stepper.matches('form[data-auto-submit]'))stepper.requestSubmit();
  };
  qs('[data-qty-minus]',stepper)?.addEventListener('click',()=>commit(Number(input.value)-1));
  qs('[data-qty-plus]',stepper)?.addEventListener('click',()=>commit(Number(input.value)+1));
  input.addEventListener('change',()=>{const normalized=Math.max(minimum,Math.trunc(Number(input.value))||minimum);input.value=String(normalized)});
});

const motionHero=qs('[data-motion-hero]');
if(motionHero){
  const reduceMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const homeSections=qsa('.category-rail,.ref-products,.essentials-banner,.service-strip,.ref-newsletter,.instagram-strip');
  homeSections.forEach(section=>{
    qsa('.product-card,.category-rail__grid>a',section).forEach((item,index)=>item.style.setProperty('--reveal-index',Math.min(index,7)));
  });
  document.body.classList.add('home-motion-ready');
  if(reduceMotion){
    homeSections.forEach(section=>section.classList.add('home-reveal-visible'));
  }else{
    const revealObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{
      if(entry.isIntersecting){entry.target.classList.add('home-reveal-visible');revealObserver.unobserve(entry.target)}
    }),{threshold:.12,rootMargin:'0px 0px -45px'});
    homeSections.forEach(section=>revealObserver.observe(section));

    if(matchMedia('(pointer:fine)').matches){
      let pointerFrame;
      const setHeroMotion=(x,y)=>{motionHero.style.setProperty('--hero-x',`${x}px`);motionHero.style.setProperty('--hero-y',`${y}px`)};
      motionHero.addEventListener('pointermove',event=>{
        const bounds=motionHero.getBoundingClientRect();
        const x=((event.clientX-bounds.left)/bounds.width-.5)*18;
        const y=((event.clientY-bounds.top)/bounds.height-.5)*12;
        cancelAnimationFrame(pointerFrame);
        pointerFrame=requestAnimationFrame(()=>setHeroMotion(x,y));
      });
      motionHero.addEventListener('pointerleave',()=>setHeroMotion(0,0));
    }
  }
}

const checkoutForm=qs('[data-checkout-form]'),checkoutSummary=qs('[data-checkout-summary]');
if(checkoutForm&&checkoutSummary){
  const shippingTotal=qs('[data-shipping-total]',checkoutSummary),grandTotal=qs('[data-grand-total]',checkoutSummary),estimate=qs('[data-delivery-estimate]');
  const normalizeNumber=value=>Number(String(value??'').replace(/[٠-٩]/g,digit=>'٠١٢٣٤٥٦٧٨٩'.indexOf(digit)).replace(/[٬,\s]/g,'').replace('٫','.'));
  const shippingPrices={standard:normalizeNumber(checkoutSummary.dataset.standardShipping),express:normalizeNumber(checkoutSummary.dataset.expressShipping)};
  const parsedTotal=normalizeNumber(checkoutSummary.dataset.orderTotal),baseTotal=Number.isFinite(parsedTotal)?parsedTotal:0;
  const money=value=>`${Math.round(Number.isFinite(value)?value:0).toLocaleString('en-US')} ج.م`;
  const updateCheckoutTotal=()=>{
    const method=qs('input[name="shipping_method"]:checked',checkoutForm)?.value||qs('select[name="shipping_method"]',checkoutForm)?.value||'standard';
    const shipping=shippingPrices[method]??shippingPrices.standard;
    if(shippingTotal)shippingTotal.textContent=money(shipping);
    if(grandTotal)grandTotal.textContent=money(baseTotal+shipping);
    if(estimate)estimate.textContent=method==='express'?'الوصول المتوقع خلال 1–2 يوم عمل.':'الوصول المتوقع خلال 2–5 أيام عمل.';
  };
  qsa('input[name="shipping_method"],select[name="shipping_method"]',checkoutForm).forEach(input=>input.addEventListener('change',updateCheckoutTotal));
  const savedAddress=qs('[data-saved-address]',checkoutForm);
  savedAddress?.addEventListener('change',()=>{
    const option=savedAddress.selectedOptions[0];if(!option?.value)return;
    const values={name:option.dataset.name,phone:option.dataset.phone,governorate:option.dataset.governorate,area:option.dataset.area,address:option.dataset.address,notes:option.dataset.notes};
    const details=[option.dataset.building&&`مبنى ${option.dataset.building}`,option.dataset.floor&&`الدور ${option.dataset.floor}`,option.dataset.apartment&&`شقة ${option.dataset.apartment}`].filter(Boolean).join('، ');values.details=details;
    Object.entries(values).forEach(([name,value])=>{const field=checkoutForm.elements.namedItem(name);if(field)field.value=value||''});
  });
  const summaryDetails=qs('[data-checkout-summary-details]',checkoutSummary);if(summaryDetails&&matchMedia('(max-width:767px)').matches)summaryDetails.removeAttribute('open');
  checkoutForm.addEventListener('submit',()=>{const button=qs('button[type="submit"]',checkoutForm);if(button){button.disabled=true;button.textContent='جارٍ تسجيل الطلب…'}});
  updateCheckoutTotal();
}

const liveSearch=qs('[data-live-search]');
if(liveSearch){
  const input=qs('input[type="search"]',liveSearch),results=qs('#search-live-results');let timer,controller;
  const escapeHtml=value=>String(value).replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  input?.addEventListener('input',()=>{
    clearTimeout(timer);controller?.abort();const query=input.value.trim();
    if(query.length<2){results.replaceChildren();input.setAttribute('aria-expanded','false');return}
    results.innerHTML='<p class="search-loading">جارٍ البحث…</p>';
    timer=setTimeout(async()=>{controller=new AbortController();try{const url=new URL(liveSearch.dataset.suggestUrl,location.origin);url.searchParams.set('q',query);const response=await fetch(url,{signal:controller.signal,headers:{'X-Requested-With':'XMLHttpRequest'}});if(!response.ok)throw new Error('search failed');const data=await response.json();results.innerHTML=data.results.length?data.results.map(item=>`<a href="${escapeHtml(item.url)}">${item.image?`<img src="${escapeHtml(item.image)}" alt="" width="52" height="66">`:''}<span><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.category)} · ${escapeHtml(item.price)} ج.م</small></span></a>`).join(''):'<p class="search-loading">لا توجد نتائج مطابقة.</p>';input.setAttribute('aria-expanded',String(data.results.length>0));}catch(error){if(error.name!=='AbortError')results.replaceChildren()}},220);
  });
}

const backToTop=qs('[data-back-to-top]');
if(backToTop){addEventListener('scroll',()=>backToTop.classList.toggle('is-visible',scrollY>700),{passive:true});backToTop.addEventListener('click',()=>scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'}));}

const gallery=qs('[data-gallery]'),galleryCurrent=qs('[data-gallery-current]'),lightbox=qs('[data-product-lightbox]');
if(gallery){
  const galleryButtons=qsa('[data-gallery-image]',gallery),galleryImages=galleryButtons.map(button=>qs('img',button));let activeImage=0,galleryFrame;
  const selectImage=index=>{
    activeImage=(index+galleryImages.length)%galleryImages.length;
    galleryButtons.forEach((button,buttonIndex)=>button.classList.toggle('is-active',buttonIndex===activeImage));
    if(galleryCurrent)galleryCurrent.textContent=String(activeImage+1);
    if(matchMedia('(min-width:768px)').matches&&activeImage>0){
      const primary=galleryImages[0],selected=galleryImages[activeImage];
      [primary.src,selected.src]=[selected.src,primary.src];[primary.alt,selected.alt]=[selected.alt,primary.alt];
      activeImage=0;galleryButtons.forEach((button,index)=>button.classList.toggle('is-active',index===0));
    }
  };
  const openLightbox=index=>{if(!lightbox)return;activeImage=index;const image=qs('[data-lightbox-image]',lightbox),source=galleryImages[activeImage];image.src=source.currentSrc||source.src;image.alt=source.alt;qs('[data-lightbox-count]',lightbox).textContent=`${activeImage+1} / ${galleryImages.length}`;lightbox.hidden=false;body.classList.add('is-locked');qs('[data-lightbox-close]',lightbox)?.focus()};
  const stepLightbox=step=>{activeImage=(activeImage+step+galleryImages.length)%galleryImages.length;openLightbox(activeImage)};
  galleryButtons.forEach((button,index)=>button.addEventListener('click',()=>{if(index>0&&matchMedia('(min-width:768px)').matches)selectImage(index);else openLightbox(index)}));
  gallery.addEventListener('scroll',()=>{cancelAnimationFrame(galleryFrame);galleryFrame=requestAnimationFrame(()=>{const figures=qsa('figure',gallery),center=gallery.scrollLeft+gallery.clientWidth/2;let closest=0,distance=Infinity;figures.forEach((figure,index)=>{const figureCenter=figure.offsetLeft+figure.offsetWidth/2,nextDistance=Math.abs(figureCenter-center);if(nextDistance<distance){distance=nextDistance;closest=index}});if(galleryCurrent)galleryCurrent.textContent=String(closest+1)})},{passive:true});
  const closeLightbox=()=>{if(!lightbox)return;lightbox.hidden=true;body.classList.remove('is-locked');galleryButtons[activeImage]?.focus()};
  qs('[data-lightbox-close]',lightbox)?.addEventListener('click',closeLightbox);qs('[data-lightbox-prev]',lightbox)?.addEventListener('click',()=>stepLightbox(-1));qs('[data-lightbox-next]',lightbox)?.addEventListener('click',()=>stepLightbox(1));
  lightbox?.addEventListener('keydown',event=>{if(event.key==='Escape')closeLightbox();if(event.key==='ArrowLeft')stepLightbox(-1);if(event.key==='ArrowRight')stepLightbox(1)});
}

const networkConnection=navigator.connection||navigator.mozConnection||navigator.webkitConnection;
if(video&&(networkConnection?.saveData||networkConnection?.effectiveType?.includes('2g'))){video.pause();video.removeAttribute('autoplay');qsa('source',video).forEach(source=>{source.dataset.src=source.src;source.removeAttribute('src')});video.load();if(videoToggle){videoToggle.textContent='تشغيل';videoToggle.setAttribute('aria-label','تشغيل الفيديو')}}
