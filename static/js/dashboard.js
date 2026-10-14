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
