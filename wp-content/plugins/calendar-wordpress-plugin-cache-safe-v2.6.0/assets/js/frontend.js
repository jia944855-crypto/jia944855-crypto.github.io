(function(){
  'use strict';
  let lastFocused = null;

  function parseLocalDate(value){ if(!value) return null; const p=value.split('-').map(Number); return new Date(p[0],p[1]-1,p[2]); }
  function isoDate(d){ return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
  function normalize(s){ return (s||'').toString().toLocaleLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,''); }
  function getModalFromCard(card){ const calendar=card.closest('.mcp-calendar'); if(!calendar)return null; const id=calendar.getAttribute('data-modal-id'); return id?document.getElementById(id):null; }
  function openModal(card){ const tpl=card.querySelector('.mcp-popup-template'), modal=getModalFromCard(card); if(!tpl||!modal)return; lastFocused=document.activeElement; modal.querySelector('.mcp-modal-content').innerHTML=tpl.innerHTML; modal.classList.add('is-open'); modal.setAttribute('aria-hidden','false'); document.documentElement.classList.add('mcp-modal-open'); document.body.style.overflow='hidden'; const close=modal.querySelector('.mcp-modal-close'); if(close)close.focus({preventScroll:true}); }
  function closeModal(modal){ if(!modal)modal=document.querySelector('.mcp-modal.is-open'); if(!modal)return; modal.classList.remove('is-open'); modal.setAttribute('aria-hidden','true'); modal.querySelector('.mcp-modal-content').innerHTML=''; document.documentElement.classList.remove('mcp-modal-open'); document.body.style.overflow=''; if(lastFocused&&typeof lastFocused.focus==='function')lastFocused.focus({preventScroll:true}); }

  function initCalendar(wrap){
    let events=[]; try{ events=JSON.parse(wrap.dataset.events||'[]'); }catch(e){}
    const state={query:'',type:'all',range:'all',date:'',month:null,page:1,loading:false};
    const perPage=parseInt(wrap.dataset.postsPerPage||'12',10)||12;
    const order=wrap.dataset.order||'ASC';
    const today=new Date(); today.setHours(0,0,0,0);
    // Select today automatically when the calendar first loads.
    // This also makes the initial AJAX request show only events active today.
    state.date=isoDate(today);
    const currentMonth=new Date(today.getFullYear(),today.getMonth(),1);
    // Always open on the current month. Previous months are intentionally unavailable.
    state.month=new Date(currentMonth.getFullYear(),currentMonth.getMonth(),1);
    let searchTimer=null;

    function updateCardBadge(card, activeDate){
      const start=parseLocalDate(card.dataset.dateStart||card.dataset.date);
      const end=parseLocalDate(card.dataset.dateEnd||card.dataset.dateStart||card.dataset.date);
      let displayDate=start;
      // Never show a past date on the card badge. For an event that is already
      // running, show today. For a selected calendar date inside the event
      // range, show that selected date. Future events keep their start date.
      if(start && end){
        if(activeDate && activeDate>=start && activeDate<=end){
          displayDate=activeDate;
        }else if(today>=start && today<=end){
          displayDate=today;
        }
      }
      if(!displayDate) return;
      const month=card.querySelector('.mcp-date span'), day=card.querySelector('.mcp-date strong');
      if(month) month.textContent=displayDate.toLocaleDateString(undefined,{month:'short'}).replace('.','').toLocaleUpperCase();
      if(day) day.textContent=displayDate.getDate();
    }

    function refreshBadges(){
      const selectedDate=state.date?parseLocalDate(state.date):null;
      wrap.querySelectorAll('.mcp-card').forEach(card=>updateCardBadge(card,selectedDate));
    }

    function setLoading(on){
      state.loading=on;
      wrap.classList.toggle('is-loading',on);
      wrap.querySelectorAll('.mcp-page,.mcp-quick,.mcp-day').forEach(el=>el.disabled=on||el.classList.contains('is-empty')||(!el.classList.contains('has-event')&&el.classList.contains('mcp-day')));
    }

    function loadPage(page, scroll){
      if(state.loading) return;
      state.page=Math.max(1,parseInt(page||1,10));
      setLoading(true);
      const body=new URLSearchParams({
        action:'mcp_load_events', page:String(state.page),
        posts_per_page:String(perPage), order:order, query:state.query, type:state.type,
        range:state.range, date:state.date
      });
      fetch((window.MCP_AJAX&&MCP_AJAX.ajax_url)||'/wp-admin/admin-ajax.php',{
        method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'},body:body.toString(),credentials:'same-origin'
      }).then(r=>r.json()).then(res=>{
        if(!res||!res.success) throw new Error('Invalid response');
        const data=res.data||{};
        const grid=wrap.querySelector('.mcp-grid'), pagination=wrap.querySelector('.mcp-pagination-wrap');
        if(grid) grid.innerHTML=data.html||'';
        if(pagination) pagination.innerHTML=data.pagination||'';
        const count=wrap.querySelector('.mcp-result-count');
        if(count) count.textContent=(data.total||0)+' event'+((data.total||0)===1?'':'s');
        const no=wrap.querySelector('.mcp-no-results'); if(no) no.hidden=Number(data.total||0)!==0;
        // Refresh the calendar's event ranges from the uncached AJAX response.
        // This means newly edited/added events appear even if the page HTML itself
        // was served from LiteSpeed cache.
        if(Array.isArray(data.events)){
          events=data.events;
          renderMonth();
        }
        refreshBadges();
        if(scroll) wrap.querySelector('.mcp-results')?.scrollIntoView({behavior:'smooth',block:'start'});
      }).catch(()=>{
        const no=wrap.querySelector('.mcp-no-results');
        if(no){no.hidden=false;no.querySelector('strong').textContent='Could not load events';no.querySelector('span').textContent='Please refresh the page and try again.';}
      }).finally(()=>setLoading(false));
    }

    function updateClearButton(){
      const clear=wrap.querySelector('.mcp-clear-filters');
      if(clear) clear.style.visibility=(state.query||state.type!=='all'||state.range!=='all'||state.date)?'visible':'hidden';
    }

    function renderMonth(){
      const box=wrap.querySelector('.mcp-month-days'), label=wrap.querySelector('.mcp-month-label'); if(!box||!label)return;
      label.textContent=state.month.toLocaleDateString(undefined,{month:'long',year:'numeric'});
      const prevButton=wrap.querySelector('.mcp-month-prev');
      if(prevButton){
        const viewingCurrentOrEarlier=state.month.getFullYear()===currentMonth.getFullYear()&&state.month.getMonth()<=currentMonth.getMonth();
        prevButton.disabled=viewingCurrentOrEarlier;
        prevButton.setAttribute('aria-disabled',viewingCurrentOrEarlier?'true':'false');
      }
      box.innerHTML=''; const y=state.month.getFullYear(),m=state.month.getMonth(); let first=new Date(y,m,1).getDay(); first=(first+6)%7; const days=new Date(y,m+1,0).getDate();
      for(let i=0;i<first;i++){ const b=document.createElement('button');b.className='mcp-day is-empty';b.type='button';b.tabIndex=-1;b.disabled=true;box.appendChild(b); }
      for(let d=1;d<=days;d++){
        const date=new Date(y,m,d), key=isoDate(date), isPast=date<today, count=isPast?0:events.filter(e=>{const start=parseLocalDate(e.date_start||e.date),end=parseLocalDate(e.date_end||e.date_start||e.date),excludedDates=Array.isArray(e.excluded_dates)?e.excluded_dates:[],excluded=excludedDates.includes(key);return start&&end&&date>=start&&date<=end&&!excluded;}).length, b=document.createElement('button');
        const visualSelectedKey=state.date||isoDate(today);
        b.type='button';b.className='mcp-day'+(count?' has-event':'')+(visualSelectedKey===key?' is-selected':'')+(isoDate(today)===key?' is-today':'')+(isPast?' is-past':'');b.textContent=d;b.dataset.date=key;
        if(count){b.title=count+' event'+(count===1?'':'s');b.setAttribute('aria-label',key+', '+count+' events');} else {b.disabled=true;if(isPast)b.setAttribute('aria-label',key+', past date');}
        box.appendChild(b);
      }
      const selected=wrap.querySelector('.mcp-selected-date'); if(selected){selected.hidden=!state.date;selected.textContent=state.date?'Showing '+parseLocalDate(state.date).toLocaleDateString(undefined,{weekday:'short',day:'numeric',month:'long'})+' — clear date':'';}
    }

    function resetFilters(){
      state.query='';state.type='all';state.range='all';state.date='';state.page=1;
      const search=wrap.querySelector('.mcp-search');if(search)search.value='';
      const select=wrap.querySelector('.mcp-filter');if(select)select.value='all';
      wrap.querySelectorAll('.mcp-quick').forEach(x=>x.classList.toggle('is-active',x.dataset.range==='all'));
      renderMonth();updateClearButton();loadPage(1,false);
    }

    wrap.addEventListener('input',e=>{
      if(e.target.classList.contains('mcp-search')){
        state.query=e.target.value.trim();state.page=1;updateClearButton();
        clearTimeout(searchTimer);searchTimer=setTimeout(()=>loadPage(1,false),350);
      }
    });
    wrap.addEventListener('change',e=>{
      if(e.target.classList.contains('mcp-filter')){state.type=e.target.value;state.page=1;updateClearButton();loadPage(1,false);}
    });
    wrap.addEventListener('click',e=>{
      const page=e.target.closest('.mcp-page[data-page]');
      if(page&&!page.disabled){loadPage(page.dataset.page,true);return;}
      const q=e.target.closest('.mcp-quick');
      if(q){wrap.querySelectorAll('.mcp-quick').forEach(x=>x.classList.remove('is-active'));q.classList.add('is-active');state.range=q.dataset.range||'all';state.date='';state.page=1;renderMonth();updateClearButton();loadPage(1,false);return;}
      if(e.target.closest('.mcp-month-prev')){
        const previous=new Date(state.month.getFullYear(),state.month.getMonth()-1,1);
        if(previous>=currentMonth){state.month=previous;renderMonth();}
        return;
      }
      if(e.target.closest('.mcp-month-next')){state.month=new Date(state.month.getFullYear(),state.month.getMonth()+1,1);renderMonth();return;}
      const day=e.target.closest('.mcp-day.has-event');
      if(day){state.date=day.dataset.date;state.range='all';state.page=1;wrap.querySelectorAll('.mcp-quick').forEach(x=>x.classList.toggle('is-active',x.dataset.range==='all'));renderMonth();updateClearButton();loadPage(1,true);return;}
      if(e.target.closest('.mcp-selected-date')||e.target.closest('.mcp-clear-filters')){resetFilters();return;}
    });
    renderMonth();refreshBadges();
    const initialCount=wrap.querySelectorAll('.mcp-card').length;
    const count=wrap.querySelector('.mcp-result-count'); if(count&&!count.textContent)count.textContent=initialCount+' event'+(initialCount===1?'':'s');
    updateClearButton();
    // Replace the initial server-rendered list with today's active events.
    loadPage(1,false);
  }

  document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('.mcp-calendar').forEach(initCalendar));
  document.addEventListener('click',function(e){
    const cardBtn=e.target.closest('.mcp-card-button'); if(cardBtn){openModal(cardBtn.closest('.mcp-card'));return;}
    const closeBtn=e.target.closest('.mcp-modal-close'); if(closeBtn){closeModal(closeBtn.closest('.mcp-modal'));return;}
    if(e.target.classList.contains('mcp-modal-backdrop')){closeModal(e.target.closest('.mcp-modal'));return;}
    const copyBtn=e.target.closest('.mcp-copy'); if(copyBtn){const url=copyBtn.getAttribute('data-url')||window.location.href;if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(url).then(()=>copyBtn.textContent='COPIED');}else{const input=document.createElement('textarea');input.value=url;input.style.position='fixed';input.style.opacity='0';document.body.appendChild(input);input.select();document.execCommand('copy');input.remove();copyBtn.textContent='COPIED';}}
    const emailBtn=e.target.closest('.mcp-email-invite'); if(emailBtn){e.preventDefault();window.location.href='mailto:?subject='+encodeURIComponent(emailBtn.dataset.subject||'')+'&body='+encodeURIComponent(emailBtn.dataset.body||'');}
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});
})();
