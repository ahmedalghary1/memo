const themeToggle=document.querySelector('[data-dashboard-theme-toggle]');
const syncDashboardTheme=()=>{
  const light=document.documentElement.dataset.dashboardTheme==='light';
  themeToggle?.setAttribute('aria-label',light?'التبديل إلى الوضع الداكن':'التبديل إلى الوضع الفاتح');
  themeToggle?.setAttribute('aria-pressed',String(light));
  const label=themeToggle?.querySelector('[data-dashboard-theme-label]');
  if(label)label.textContent=light?'الوضع الداكن':'الوضع الفاتح';
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content',light?'#f5f2ec':'#101518');
};
themeToggle?.addEventListener('click',()=>{
  const next=document.documentElement.dataset.dashboardTheme==='light'?'dark':'light';
  document.documentElement.dataset.dashboardTheme=next;
  try{localStorage.setItem('memo-dashboard-theme',next)}catch(e){}
  syncDashboardTheme();
});
syncDashboardTheme();

const menuButton=document.querySelector('.dash-menu');
const sidebar=document.querySelector('.dash-sidebar');
const scrim=document.querySelector('.dash-scrim');
const closeMenu=()=>{sidebar?.classList.remove('is-open');scrim?.classList.remove('is-open');menuButton?.setAttribute('aria-expanded','false');document.body.classList.remove('dash-locked')};
menuButton?.addEventListener('click',()=>{const opening=!sidebar.classList.contains('is-open');sidebar.classList.toggle('is-open',opening);scrim?.classList.toggle('is-open',opening);menuButton.setAttribute('aria-expanded',String(opening));document.body.classList.toggle('dash-locked',opening);if(opening)sidebar.querySelector('a')?.focus()});
scrim?.addEventListener('click',closeMenu);
sidebar?.addEventListener('keydown',event=>{if(event.key==='Escape'){closeMenu();menuButton?.focus()}});
addEventListener('resize',()=>{if(innerWidth>900)closeMenu()});

const navLinks=[...document.querySelectorAll('.dash-sidebar nav a')];
const activeLink=navLinks.sort((a,b)=>new URL(b.href).pathname.length-new URL(a.href).pathname.length).find(link=>{
  const path=new URL(link.href).pathname;
  return location.pathname===path||(path!=='/dashboard/'&&location.pathname.startsWith(path));
});
activeLink?.setAttribute('aria-current','page');
navLinks.forEach(link=>link.addEventListener('click',()=>{if(innerWidth<=900)closeMenu()}));

document.querySelectorAll('[data-collection-picker]').forEach(picker=>{
  const search=picker.querySelector('.collection-picker__search');
  const options=[...picker.querySelectorAll('.collection-picker__options label')];
  const empty=picker.querySelector('.collection-picker__empty');
  search?.addEventListener('input',()=>{
    const query=search.value.trim().toLocaleLowerCase('ar');
    let visible=0;
    options.forEach(label=>{
      const match=label.textContent.toLocaleLowerCase('ar').includes(query);
      label.parentElement.hidden=!match;
      if(match)visible++;
    });
    if(empty)empty.hidden=visible>0;
  });
});

document.querySelectorAll('[data-formset]').forEach(section=>{
  const rows=section.querySelector('[data-form-rows]');
  const template=section.querySelector('template[data-empty-form]');
  const total=section.querySelector('input[name$="-TOTAL_FORMS"]');
  const addForm=(values={})=>{
    const index=Number(total.value);
    const wrapper=document.createElement('div');
    wrapper.innerHTML=template.innerHTML.replaceAll('__prefix__',String(index)).trim();
    const row=wrapper.firstElementChild;
    row.classList.add('is-new');rows.append(row);total.value=String(index+1);
    Object.entries(values).forEach(([field,value])=>{const input=row.querySelector(`[name$="-${field}"]`);if(input){if(input.type==='checkbox')input.checked=Boolean(value);else input.value=String(value)}});
    return row;
  };
  section.querySelector('[data-add-form]')?.addEventListener('click',()=>{
    const row=addForm();row.querySelector('select,input:not([type="hidden"])')?.focus();
    row.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});
  });
  rows?.addEventListener('change',event=>{
    if(!event.target.matches('input[name$="-DELETE"]'))return;
    event.target.closest('.editor-row')?.classList.toggle('is-deleted',event.target.checked);
  });
  const builder=section.querySelector('[data-variant-builder]');
  if(builder){
    const color=builder.querySelector('[data-builder-color]'),sizePicker=builder.querySelector('[data-size-picker]'),sizes=[...builder.querySelectorAll('[data-builder-size]')],summary=builder.querySelector('[data-size-summary]'),stock=builder.querySelector('[data-builder-stock]'),message=builder.querySelector('[data-builder-message]');
    const syncBuilder=()=>{const selected=sizes.filter(input=>input.checked);summary.textContent=selected.length?selected.map(input=>input.dataset.name).join('، '):'اختر المقاسات';sizePicker.classList.toggle('is-disabled',!color.value);if(!color.value)sizePicker.removeAttribute('open')};
    color.addEventListener('change',syncBuilder);sizes.forEach(input=>input.addEventListener('change',syncBuilder));syncBuilder();
    sizePicker.addEventListener('click',event=>{if(!color.value){event.preventDefault();message.textContent='اختر اللون أولًا لعرض قائمة المقاسات.';color.focus()}});
    builder.querySelector('[data-build-variants]').addEventListener('click',()=>{
      const selected=sizes.filter(input=>input.checked);if(!color.value){message.textContent='اختر اللون أولًا.';color.focus();return}if(!selected.length){message.textContent='اختر مقاسًا واحدًا على الأقل.';sizePicker.open=true;return}
      const existing=new Set([...rows.querySelectorAll('.editor-row:not(.is-deleted)')].map(row=>`${row.querySelector('[name$="-color"]')?.value}|${row.querySelector('[name$="-size"]')?.value}`));let added=0;
      selected.forEach(size=>{const key=`${color.value}|${size.value}`;if(existing.has(key))return;addForm({color:color.value,size:size.value,stock_quantity:Math.max(0,Number(stock.value)||0),is_active:true,low_stock_threshold:3});existing.add(key);added++});
      message.textContent=added?`تمت إضافة ${added} من المقاسات للون ${color.selectedOptions[0].dataset.name}.`:'كل المقاسات المختارة مضافة بالفعل.';sizes.forEach(input=>input.checked=false);sizePicker.removeAttribute('open');syncBuilder();rows.lastElementChild?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});
    });
  }
});
