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
  if(target.pathname===location.pathname&&!target.search){
    link.setAttribute('aria-current','page');
    if(link.closest('.mobile-menu'))qsa('details.menu-category',link.closest('.mobile-menu')).forEach(branch=>{if(branch.contains(link))branch.open=true});
  }
});

const video=qs('[data-pause-offscreen]'); const videoToggle=qs('[data-video-toggle]');
if(video){if(matchMedia('(prefers-reduced-motion: reduce)').matches)video.pause();else new IntersectionObserver(([e])=>e.isIntersecting?video.play().catch(()=>{}):video.pause(),{threshold:.15}).observe(video);videoToggle?.addEventListener('click',()=>{if(video.paused){video.play();videoToggle.textContent='Pause';videoToggle.setAttribute('aria-label','Pause video')}else{video.pause();videoToggle.textContent='Play';videoToggle.setAttribute('aria-label','Play video')}})}

const variantForm=qs('[data-variant-form]');
if(variantForm){const variants=JSON.parse(variantForm.dataset.variants||'[]'), colorInputs=qsa('input[name="color"]',variantForm), sizeInputs=qsa('input[name="size"]',variantForm), id=qs('[data-variant-id]',variantForm), stock=qs('[data-stock]',variantForm), add=qs('[data-add-button]',variantForm), mobile=qs('[data-mobile-add]'), selectedColor=qs('[data-selected-color]',variantForm), mobileColorLabel=qs('[data-selected-color-mobile]'), mobileSwatches=qsa('.mobile-swatch');
function update(){const checkedColor=qs('input[name="color"]:checked',variantForm),checkedSize=qs('input[name="size"]:checked',variantForm),color=checkedColor?.value??'',size=checkedSize?.value??'',needsColor=colorInputs.length>0,needsSize=sizeInputs.length>0;if(checkedColor&&selectedColor)selectedColor.textContent=checkedColor.dataset.label||'';if(checkedColor&&mobileColorLabel)mobileColorLabel.textContent=checkedColor.dataset.label||'';mobileSwatches.forEach(btn=>btn.classList.toggle('is-active',btn.dataset.colorSlug===color));sizeInputs.forEach(s=>{const match=variants.some(v=>v.color===color&&v.size===s.value&&v.stock>0);s.disabled=needsColor&&!checkedColor||!!checkedColor&&!match;if(s.disabled&&s.checked)s.checked=false});window.dispatchEvent(new CustomEvent('productcolorchange',{detail:{color}}));if(checkedColor&&color){const url=new URL(location.href);url.searchParams.set('color',color);history.replaceState({},'',url)}const activeSize=qs('input[name="size"]:checked',variantForm)?.value??'';const v=variants.find(x=>x.color===color&&x.size===activeSize);if(!v){id.value='';const missing=[];if(needsColor&&!checkedColor)missing.push('color');if(needsSize&&!qs('input[name="size"]:checked',variantForm))missing.push('size');stock.textContent=missing.length?`Choose ${missing.join(' and ')}.`:'No stock is currently available.';stock.className='stock-message';add.disabled=true;add.textContent=missing.length?`Choose ${missing.join(' and ')}`:'Unavailable';if(mobile){mobile.disabled=true;mobile.textContent=missing.length?`Choose ${missing.join(' and ')}`:'Unavailable'}return}id.value=v.id;const ok=v.stock>0;add.disabled=!ok;add.textContent=ok?'Add to bag':'Sold out';stock.textContent=v.status==='low'?`Only ${v.stock} left.`:ok?'In stock and ready to ship.':'This option is unavailable.';stock.className=`stock-message ${v.status}`;if(mobile){mobile.disabled=!ok;mobile.textContent=ok?'Add to bag':'Unavailable'}}
  [...colorInputs,...sizeInputs].forEach(i=>i.addEventListener('change',update));mobileSwatches.forEach(btn=>btn.addEventListener('click',()=>{const slug=btn.dataset.colorSlug;const target=colorInputs.find(i=>i.value===slug);if(target){target.checked=true;target.dispatchEvent(new Event('change',{bubbles:true}))}}));mobile?.addEventListener('click',()=>variantForm.requestSubmit());const firstColor=colorInputs.find(input=>!input.disabled);if(firstColor&&!colorInputs.some(input=>input.checked))firstColor.click();else update();
}

qsa('.product-card').forEach(card=>{
  const image=qs('[data-card-image]',card),swatches=qsa('[data-card-swatch]',card),links=qsa('[data-card-link]',card);
  swatches.forEach((swatch,index)=>swatch.addEventListener('click',()=>{
    swatches.forEach(item=>item.classList.remove('is-active'));swatch.classList.add('is-active');
    if(image&&swatch.dataset.image){image.classList.add('is-changing');const preload=new Image();preload.onload=()=>{image.src=swatch.dataset.image;image.alt=swatch.dataset.alt||'';requestAnimationFrame(()=>image.classList.remove('is-changing'))};preload.src=swatch.dataset.image}
    links.forEach(link=>{const url=new URL(link.href,location.href);url.searchParams.set('color',swatch.dataset.color);link.href=url});
  }));
  swatches[0]?.classList.add('is-active');
});

qsa('.toast').forEach(t=>setTimeout(()=>t.remove(),4500));

if(variantForm){
  const addButton=qs('[data-add-button]',variantForm), buyButton=qs('[data-buy-button]',variantForm);
  const syncBuy=()=>{if(buyButton)buyButton.disabled=addButton?.disabled??true};
  new MutationObserver(syncBuy).observe(addButton,{attributes:true,attributeFilter:['disabled']});
  variantForm.addEventListener('change',()=>queueMicrotask(syncBuy));
  const firstColor=qs('input[name="color"]',variantForm); if(firstColor&&!qs('input[name="color"]:checked',variantForm))firstColor.click();
  syncBuy();
}
qs('[data-share]')?.addEventListener('click',async()=>{try{if(navigator.share)await navigator.share({title:document.title,url:location.href});else{await navigator.clipboard.writeText(location.href);alert('Product link copied.')}}catch(error){if(error.name!=='AbortError')console.warn(error)}});
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
const money=value=>`${Math.round(Number.isFinite(value)?value:0).toLocaleString('en-US')} EGP`;
  const updateCheckoutTotal=()=>{
    const method=qs('input[name="shipping_method"]:checked',checkoutForm)?.value||qs('select[name="shipping_method"]',checkoutForm)?.value||'standard';
    const shipping=shippingPrices[method]??shippingPrices.standard;
    if(shippingTotal)shippingTotal.textContent=money(shipping);
    if(grandTotal)grandTotal.textContent=money(baseTotal+shipping);
if(estimate)estimate.textContent=method==='express'?'Estimated delivery in 1–2 business days.':'Estimated delivery in 2–5 business days.';
  };
  qsa('input[name="shipping_method"],select[name="shipping_method"]',checkoutForm).forEach(input=>input.addEventListener('change',updateCheckoutTotal));
  const savedAddress=qs('[data-saved-address]',checkoutForm);
  savedAddress?.addEventListener('change',()=>{
    const option=savedAddress.selectedOptions[0];if(!option?.value)return;
    const values={name:option.dataset.name,phone:option.dataset.phone,governorate:option.dataset.governorate,area:option.dataset.area,address:option.dataset.address,notes:option.dataset.notes};
const details=[option.dataset.building&&`Building ${option.dataset.building}`,option.dataset.floor&&`Floor ${option.dataset.floor}`,option.dataset.apartment&&`Apartment ${option.dataset.apartment}`].filter(Boolean).join(', ');values.details=details;
    Object.entries(values).forEach(([name,value])=>{const field=checkoutForm.elements.namedItem(name);if(field)field.value=value||''});
  });
  const summaryDetails=qs('[data-checkout-summary-details]',checkoutSummary);if(summaryDetails&&matchMedia('(max-width:767px)').matches)summaryDetails.removeAttribute('open');
checkoutForm.addEventListener('submit',()=>{const button=qs('button[type="submit"]',checkoutForm);if(button){button.disabled=true;button.textContent='Placing order…'}});
  updateCheckoutTotal();
}

const liveSearch=qs('[data-live-search]');
if(liveSearch){
  const input=qs('input[type="search"]',liveSearch),results=qs('#search-live-results');let timer,controller;
  const escapeHtml=value=>String(value).replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  input?.addEventListener('input',()=>{
    clearTimeout(timer);controller?.abort();const query=input.value.trim();
    if(query.length<2){results.replaceChildren();input.setAttribute('aria-expanded','false');return}
results.innerHTML='<p class="search-loading">Searching…</p>';
timer=setTimeout(async()=>{controller=new AbortController();try{const url=new URL(liveSearch.dataset.suggestUrl,location.origin);url.searchParams.set('q',query);const response=await fetch(url,{signal:controller.signal,headers:{'X-Requested-With':'XMLHttpRequest'}});if(!response.ok)throw new Error('search failed');const data=await response.json();results.innerHTML=data.results.length?data.results.map(item=>`<a href="${escapeHtml(item.url)}">${item.image?`<img src="${escapeHtml(item.image)}" alt="" width="52" height="66">`:''}<span><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.category)} · ${escapeHtml(item.price)} EGP</small></span></a>`).join(''):'<p class="search-loading">No matching results.</p>';input.setAttribute('aria-expanded',String(data.results.length>0));}catch(error){if(error.name!=='AbortError')results.replaceChildren()}},220);
  });
}

const backToTop=qs('[data-back-to-top]');
if(backToTop){addEventListener('scroll',()=>backToTop.classList.toggle('is-visible',scrollY>700),{passive:true});backToTop.addEventListener('click',()=>scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'}));}

const gallery=qs('[data-gallery]'),galleryCurrent=qs('[data-gallery-current]'),galleryTotal=qs('[data-gallery-total]'),lightbox=qs('[data-product-lightbox]'),galleryNext=qs('[data-gallery-next]'),galleryPrev=qs('[data-gallery-prev]');
if(gallery){
  const figures=qsa('figure',gallery);let visibleFigures=[...figures],activeImage=0,galleryFrame;
  const updateMobileNav=(idx,total)=>{
    if(galleryPrev)galleryPrev.classList.toggle('is-hidden',idx<=0);
    if(galleryNext)galleryNext.classList.toggle('is-hidden',idx>=total-1);
  };
  const setFeatured=target=>{
    if(!target)return;
    activeImage=Math.max(0,visibleFigures.indexOf(target));
    visibleFigures.forEach((fig,index)=>{
      const isTarget=(fig===target);
      fig.classList.toggle('is-featured',isTarget);
      qs('[data-gallery-image]',fig)?.classList.toggle('is-active',isTarget);
    });
    if(galleryCurrent)galleryCurrent.textContent=String(activeImage+1);
    updateMobileNav(activeImage,visibleFigures.length);
  };
  const syncColor=color=>{
    const matched=figures.filter(figure=>figure.dataset.galleryColor===color),generic=figures.filter(figure=>!figure.dataset.galleryColor);
    visibleFigures=matched.length?matched:(generic.length?generic:figures);
    figures.forEach(figure=>figure.hidden=!visibleFigures.includes(figure));
    const hasMultiple=visibleFigures.length>1;
    gallery.classList.toggle('has-single-image',!hasMultiple);
    if(galleryTotal)galleryTotal.textContent=String(visibleFigures.length);
    if(galleryNext)galleryNext.style.display=hasMultiple?'':'none';
    if(galleryPrev)galleryPrev.style.display=hasMultiple?'':'none';
    const primaryFigure=visibleFigures.find(figure=>figure.dataset.isPrimary==='true')||visibleFigures[0];
    setFeatured(primaryFigure);
    if(window.innerWidth<=767&&primaryFigure){
      gallery.scrollTo({left:primaryFigure.offsetLeft,behavior:'auto'});
    }else{
      gallery.scrollTo({left:0,top:0,behavior:'auto'});
    }
    gallery.classList.remove('is-switching');
    requestAnimationFrame(()=>gallery.classList.add('is-switching'));
  };
  const openLightbox=index=>{
    if(!lightbox||!visibleFigures.length)return;
    activeImage=(index+visibleFigures.length)%visibleFigures.length;
    const source=qs('img',visibleFigures[activeImage]),image=qs('[data-lightbox-image]',lightbox);
    image.src=source.currentSrc||source.src;image.alt=source.alt;
    qs('[data-lightbox-count]',lightbox).textContent=`${activeImage+1} / ${visibleFigures.length}`;
    lightbox.hidden=false;body.classList.add('is-locked');
    qs('[data-lightbox-close]',lightbox)?.focus();
  };
  const stepLightbox=step=>openLightbox(activeImage+step);
  figures.forEach(figure=>{
    qs('[data-gallery-image]',figure)?.addEventListener('click',()=>{
      if(window.innerWidth>767&&!figure.classList.contains('is-featured')){
        setFeatured(figure);
        return;
      }
      openLightbox(visibleFigures.indexOf(figure));
    });
  });
  gallery.addEventListener('scroll',()=>{
    cancelAnimationFrame(galleryFrame);
    galleryFrame=requestAnimationFrame(()=>{
      const center=gallery.scrollLeft+gallery.clientWidth/2;
      let closest=0,distance=Infinity;
      visibleFigures.forEach((figure,index)=>{
        const nextDistance=Math.abs(figure.offsetLeft+figure.offsetWidth/2-center);
        if(nextDistance<distance){distance=nextDistance;closest=index;}
      });
      if(galleryCurrent)galleryCurrent.textContent=String(closest+1);
      updateMobileNav(closest,visibleFigures.length);
      if(window.innerWidth<=767&&visibleFigures[closest]){
        activeImage=closest;
        visibleFigures.forEach((fig,idx)=>{
          fig.classList.toggle('is-featured',idx===closest);
          qs('[data-gallery-image]',fig)?.classList.toggle('is-active',idx===closest);
        });
      }
    });
  },{passive:true});
  galleryNext?.addEventListener('click',e=>{
    e.preventDefault();
    const nextIdx=activeImage+1;
    if(nextIdx<visibleFigures.length){
      const target=visibleFigures[nextIdx];
      gallery.scrollTo({left:target.offsetLeft,behavior:'smooth'});
    }
  });
  galleryPrev?.addEventListener('click',e=>{
    e.preventDefault();
    const prevIdx=activeImage-1;
    if(prevIdx>=0){
      const target=visibleFigures[prevIdx];
      gallery.scrollTo({left:target.offsetLeft,behavior:'smooth'});
    }
  });
  const closeLightbox=()=>{
    if(!lightbox)return;
    lightbox.hidden=true;
    body.classList.remove('is-locked');
    qs('[data-gallery-image]',visibleFigures[activeImage])?.focus();
  };
  qs('[data-lightbox-close]',lightbox)?.addEventListener('click',closeLightbox);
  qs('[data-lightbox-prev]',lightbox)?.addEventListener('click',()=>stepLightbox(-1));
  qs('[data-lightbox-next]',lightbox)?.addEventListener('click',()=>stepLightbox(1));
  lightbox?.addEventListener('keydown',event=>{
    if(event.key==='Escape')closeLightbox();
    if(event.key==='ArrowLeft')stepLightbox(-1);
    if(event.key==='ArrowRight')stepLightbox(1);
  });
  addEventListener('productcolorchange',event=>syncColor(event.detail.color));
  syncColor(qs('input[name="color"]:checked',variantForm)?.value||'');
}

const networkConnection=navigator.connection||navigator.mozConnection||navigator.webkitConnection;
if(video&&(networkConnection?.saveData||networkConnection?.effectiveType?.includes('2g'))){video.pause();video.removeAttribute('autoplay');qsa('source',video).forEach(source=>{source.dataset.src=source.src;source.removeAttribute('src')});video.load();if(videoToggle){videoToggle.textContent='Play';videoToggle.setAttribute('aria-label','Play video')}}
