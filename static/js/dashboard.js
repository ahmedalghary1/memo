const menuButton=document.querySelector('.dash-menu');
const sidebar=document.querySelector('.dash-sidebar');
const scrim=document.querySelector('.dash-scrim');
const closeMenu=()=>{sidebar?.classList.remove('is-open');scrim?.classList.remove('is-open');menuButton?.setAttribute('aria-expanded','false');document.body.classList.remove('dash-locked')};
menuButton?.addEventListener('click',()=>{const opening=!sidebar.classList.contains('is-open');sidebar.classList.toggle('is-open',opening);scrim?.classList.toggle('is-open',opening);menuButton.setAttribute('aria-expanded',String(opening));document.body.classList.toggle('dash-locked',opening);if(opening)sidebar.querySelector('a')?.focus()});
scrim?.addEventListener('click',closeMenu);
sidebar?.addEventListener('keydown',event=>{if(event.key==='Escape'){closeMenu();menuButton?.focus()}});
addEventListener('resize',()=>{if(innerWidth>900)closeMenu()});
