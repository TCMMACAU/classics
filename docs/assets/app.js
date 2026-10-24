// 我嘅加減：只存喺呢部機嘅瀏覽器 localStorage，唔會上傳。KEY 保持 classics-notes-v1，舊筆記相容。
const KEY='classics-notes-v1';
const SW_URL=(document.currentScript&&document.currentScript.src)?new URL('../sw.js',document.currentScript.src).href:'sw.js';
if('serviceWorker' in navigator){window.addEventListener('load',()=>{navigator.serviceWorker.register(SW_URL).catch(()=>{});});}
function loadNotes(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return{}}}
function saveNotes(n){localStorage.setItem(KEY,JSON.stringify(n))}
// 條文已讀：只存喺呢部機 localStorage，KEY classics-read-v1，格式 {條文編號:1}
const READ_KEY='classics-read-v1';
function loadRead(){try{const o=JSON.parse(localStorage.getItem(READ_KEY)||'{}');return (o&&typeof o==='object'&&!Array.isArray(o))?o:{}}catch(e){return{}}}
function saveRead(r){localStorage.setItem(READ_KEY,JSON.stringify(r))}
function countPrefix(r,pre){let c=0;for(const k in r){if(k.startsWith(pre))c++;}return c;}
function renderReadProgress(){
  const r=loadRead();
  document.querySelectorAll('.read-progress').forEach(p=>{
    const total=+p.dataset.total||0;
    const n=p.dataset.page? document.querySelectorAll('.entry.is-read').length : countPrefix(r,p.dataset.prefix||'\u0000');
    p.textContent=n? ('已讀 '+n+'／'+total+' 條'+(n>=total?' ✓':'')) : '';
  });
  document.querySelectorAll('.toc-item[data-prefix]').forEach(li=>{
    const n=countPrefix(r,li.dataset.prefix), total=+li.dataset.total||0, m=li.querySelector('.read-mark'); if(!m)return;
    m.textContent= n>=total&&total? '✓ 讀完' : (n? '已讀 '+n+'／'+total : '');
  });
  document.querySelectorAll('.read-count').forEach(p=>{const n=countPrefix(r,p.dataset.prefix);p.textContent=n?('已讀 '+n+'／'+p.dataset.total+' 條'):'';});
}
// 舊格式係純文字字串，新格式係 {證型,判斷,覆診,updated}；兩種都讀到
function normalizeNote(v){
  if(typeof v==='string') return {'證型':'','判斷':v,'覆診':'','updated':''};
  if(v&&typeof v==='object') return {'證型':String(v['證型']||''),'判斷':String(v['判斷']||v.text||''),'覆診':String(v['覆診']||''),'updated':String(v.updated||'')};
  return {'證型':'','判斷':'','覆診':'','updated':''};
}
function noteHasContent(n){return !!(n['證型']||n['判斷']||n['覆診']);}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function noteSummary(n){
  const parts=[];
  if(n['證型'])parts.push('證型：'+n['證型']);
  if(n['判斷'])parts.push('判斷：'+n['判斷']);
  if(n['覆診'])parts.push('覆診：'+n['覆診']);
  return parts.join('；');
}
function renderNote(el,id){
  const notes=loadNotes(); const wrap=el.querySelector('.note-area'); if(!wrap)return;
  wrap.innerHTML='';
  if(notes[id]!==undefined){
    const n=normalizeNote(notes[id]);
    if(noteHasContent(n)){const d=document.createElement('div');d.className='saved-note';d.textContent=noteSummary(n);wrap.appendChild(d);}
  }
}
function sortedNoteIds(notes){
  return Object.keys(notes).sort((a,b)=>{
    const ta=normalizeNote(notes[a]).updated||''; const tb=normalizeNote(notes[b]).updated||'';
    if(ta===tb) return a.localeCompare(b);
    return ta<tb?1:-1; // 最後修改排先，冇時間嘅舊筆記排後
  });
}
function renderHomeNotes(){
  const list=document.getElementById('my-notes'); if(!list)return;
  const notes=loadNotes(); const ids=sortedNoteIds(notes);
  list.innerHTML=ids.length? ids.map(id=>'<li><code>'+esc(id)+'</code>：'+esc(noteSummary(normalizeNote(notes[id])))+'</li>').join('') : '<li class="muted">暫時未有加減。</li>';
}
function bindExportImport(prefix){
  const exp=document.getElementById('export-notes'); if(!exp)return;
  exp.onclick=()=>{
    const raw=loadNotes(); const out={};
    Object.keys(raw).forEach(id=>{if(id!=='__read__')out[id]=normalizeNote(raw[id]);});
    out['__read__']=Object.keys(loadRead()).sort(); // 已讀紀錄；舊版匯出檔冇呢個鍵
    const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='經索備份.json';a.click();
  };
  const imp=document.getElementById('import-notes'), file=document.getElementById('import-file');
  if(imp){imp.onclick=()=>file.click(); file.onchange=()=>{const f=file.files[0]; if(!f)return; f.text().then(t=>{try{
      const obj=JSON.parse(t); if(typeof obj!=='object'||Array.isArray(obj))throw 0;
      const clean={}; let read=null;
      if(Object.prototype.hasOwnProperty.call(obj,'__read__')){
        if(!Array.isArray(obj.__read__))throw 0;
        read={}; obj.__read__.forEach(id=>{if(typeof id==='string'&&id)read[id]=1;});
        delete obj.__read__;
      }
      for(const [id,v] of Object.entries(obj)){
        if(typeof v==='string') clean[id]=v;
        else if(v&&typeof v==='object'&&!Array.isArray(v)) clean[id]=normalizeNote(v);
        else throw 0;
      }
      saveNotes(clean); if(read)saveRead(read); location.reload();
    }catch(e){alert('檔案格式唔啱');}});};}
}

// 朗讀：用系統 Web Speech，偏好粵語（zh-HK / yue）；唔支援就隱藏掣。只讀單條，唔連讀成篇。
let speakingEl=null, cantoneseTipShown=false;
function speechSupported(){return typeof window!=='undefined' && 'speechSynthesis' in window && typeof SpeechSynthesisUtterance!=='undefined';}
function pickVoice(){
  const voices=speechSynthesis.getVoices()||[];
  const langs=voices.map(v=>({v, lang:(v.lang||'').toLowerCase(), name:(v.name||'')}));
  const prefer=['zh-hk','yue-hk','yue','zh-yue'];
  for(const p of prefer){
    const hit=langs.find(x=>x.lang===p || x.lang.startsWith(p+'-') || x.lang.startsWith(p));
    if(hit) return {voice:hit.v, cantonese:true};
  }
  const byName=langs.find(x=>/cantonese|粵語|香港|hong\s*kong|\byue\b/i.test(x.name));
  if(byName) return {voice:byName.v, cantonese:true};
  const tw=langs.find(x=>x.lang==='zh-tw'||x.lang.startsWith('zh-tw'));
  if(tw) return {voice:tw.v, cantonese:false};
  const cn=langs.find(x=>x.lang==='zh-cn'||x.lang.startsWith('zh-cn')||x.lang.startsWith('zh'));
  if(cn) return {voice:cn.v, cantonese:false};
  return {voice:null, cantonese:false};
}
function entrySpeakText(el){
  const clone=el.cloneNode(true);
  clone.querySelectorAll('.read-btn,.note-btn,.speak-btn,.print-link,.note-area,.no,.saved-note,.note-box').forEach(n=>n.remove());
  return (clone.textContent||'').replace(/\s+/g,' ').trim();
}
function stopSpeaking(){
  try{speechSynthesis.cancel();}catch(e){}
  if(speakingEl){
    speakingEl.classList.remove('is-speaking');
    const b=speakingEl.querySelector('.speak-btn');
    if(b){b.textContent='朗讀';b.setAttribute('aria-pressed','false');}
    speakingEl=null;
  }
}
function showCantoneseTip(nearEl){
  if(cantoneseTipShown) return;
  cantoneseTipShown=true;
  const tip=document.createElement('p');
  tip.className='muted speak-tip';
  tip.textContent='提示：系統未搵到粵語聲，而家可能用普通話讀。iPhone／Android 請喺系統「朗讀／文字轉語音」設定揀粵語（廣東話）。';
  const main=nearEl.closest('main')||nearEl.parentElement;
  if(main){
    const first=main.querySelector('.entry');
    if(first) main.insertBefore(tip, first);
    else main.prepend(tip);
  }
}
function speakEntry(el){
  if(!speechSupported()) return;
  if(speakingEl===el){stopSpeaking();return;}
  stopSpeaking();
  const text=entrySpeakText(el);
  if(!text) return;
  // Chrome 有時要等 voiceschanged；先試一次，空就等一下再試
  const go=()=>{
    const {voice,cantonese}=pickVoice();
    if(!cantonese){
      const b=el.querySelector('.speak-btn');
      if(b) b.title='請喺系統設定揀粵語（廣東話）聲；而家可能用普通話讀';
      showCantoneseTip(el);
    }
    const u=new SpeechSynthesisUtterance(text);
    if(voice){u.voice=voice;u.lang=voice.lang||'zh-HK';}
    else u.lang='zh-HK';
    u.rate=1; u.pitch=1;
    const clear=()=>{
      if(speakingEl===el){
        el.classList.remove('is-speaking');
        const b=el.querySelector('.speak-btn');
        if(b){b.textContent='朗讀';b.setAttribute('aria-pressed','false');}
        speakingEl=null;
      }
    };
    u.onend=clear; u.onerror=clear;
    speakingEl=el;
    el.classList.add('is-speaking');
    const b=el.querySelector('.speak-btn');
    if(b){b.textContent='停止';b.setAttribute('aria-pressed','true');}
    speechSynthesis.speak(u);
  };
  if((speechSynthesis.getVoices()||[]).length) go();
  else{
    let started=false;
    const kick=()=>{if(started)return;started=true;speechSynthesis.removeEventListener('voiceschanged',kick);go();};
    speechSynthesis.addEventListener('voiceschanged',kick);
    setTimeout(kick,400);
  }
}

document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.entry').forEach(el=>{
    const id=el.dataset.id; renderNote(el,id);
    const rb=el.querySelector('.read-btn');
    if(rb){
      const setR=on=>{rb.setAttribute('aria-pressed',on?'true':'false');el.classList.toggle('is-read',on);rb.title=on?'再撳取消已讀':'撳一下標記已讀';};
      setR(!!loadRead()[id]);
      rb.addEventListener('click',()=>{const r=loadRead(); const on=!r[id]; if(on)r[id]=1; else delete r[id]; saveRead(r); setR(on); renderReadProgress();});
    }
    const sb=el.querySelector('.speak-btn');
    if(sb){
      if(!speechSupported()){sb.hidden=true;sb.disabled=true;sb.title='呢個瀏覽器唔支援朗讀';}
      else{
        sb.title='用系統聲朗讀呢條（偏好粵語）';
        sb.addEventListener('click',()=>speakEntry(el));
      }
    }
    const btn=el.querySelector('.note-btn'); if(!btn)return;
    btn.addEventListener('click',()=>{
      const area=el.querySelector('.note-area'); const cur=normalizeNote(loadNotes()[id]);
      area.innerHTML='';
      const box=document.createElement('div'); box.className='note-box';
      const fields=[['證型','證型'],['判斷','判斷'],['覆診','覆診']];
      const inputs={};
      fields.forEach(([key,label])=>{
        const lab=document.createElement('label'); lab.textContent=label; lab.className='note-label';
        const inp=document.createElement('input'); inp.type='text'; inp.value=cur[key]||''; inp.className='note-input';
        inp.placeholder='（只留喺呢部機，唔好輸入病人識別資料）';
        box.appendChild(lab); box.appendChild(inp); inputs[key]=inp;
      });
      const save=document.createElement('button'); save.className='btn save'; save.textContent='儲存';
      const del=document.createElement('button'); del.className='btn del'; del.textContent='刪除';
      box.appendChild(save); box.appendChild(document.createTextNode(' ')); box.appendChild(del);
      area.appendChild(box);
      save.onclick=()=>{const n=loadNotes(); const v={'證型':inputs['證型'].value.trim(),'判斷':inputs['判斷'].value.trim(),'覆診':inputs['覆診'].value.trim(),'updated':new Date().toISOString()}; if(noteHasContent(v))n[id]=v; else delete n[id]; saveNotes(n); renderNote(el,id); renderHomeNotes();};
      del.onclick=()=>{const n=loadNotes(); delete n[id]; saveNotes(n); renderNote(el,id); renderHomeNotes();};
    });
  });
  renderHomeNotes();
  renderReadProgress();
  bindExportImport();
  // 臨床頁：覆診快速開啟（按最後修改排序，連去條文錨點）
  const clinicalList=document.getElementById('clinical-notes');
  if(clinicalList){
    (async()=>{
      const notes=loadNotes(); const ids=sortedNoteIds(notes);
      if(!ids.length){clinicalList.innerHTML='<li class="muted">暫時未有加減。</li>'; return;}
      let idx=[]; try{ idx=await (await fetch('../search-index.json')).json(); }catch(e){}
      const byId={}; idx.forEach(x=>{byId[x.id]=x;});
      clinicalList.innerHTML=ids.map(id=>{
        const n=normalizeNote(notes[id]); const x=byId[id];
        const when=n.updated? new Date(n.updated).toLocaleString() : '未有修改時間（舊筆記）';
        const title=x? esc(x.book+' · '+x.group+' · '+x.section+' 第'+x.no+'條') : esc(id);
        const href=x? ('../'+x.url) : '#';
        return '<li><a href="'+href+'">'+title+'</a><br><span class="muted">'+esc(when)+'</span><br>'+esc(noteSummary(n))+'</li>';
      }).join('');
    })();
  }
  // 病人閱讀頁：?id=條文編號，只顯示原文同出處
  const patient=document.getElementById('patient-view');
  if(patient){
    (async()=>{
      const id=new URLSearchParams(location.search).get('id')||'';
      try{
        const idx=await (await fetch('search-index.json')).json();
        const x=idx.find(v=>v.id===id);
        if(!x){patient.innerHTML='<p>搵唔到呢條條文。</p>'; return;}
        patient.innerHTML='<p class="muted">'+esc(x.book)+' · '+esc(x.group)+' · '+esc(x.section)+' 第'+esc(x.no)+'條</p><div class="patient-text">'+esc(x.text)+'</div><p class="muted" style="margin-top:2rem">供閱讀檢索，不是處方依據。</p>';
        document.title=x.book+' · '+x.section+'｜病人閱讀頁';
      }catch(e){ patient.innerHTML='<p>搵唔到呢條條文。</p>'; }
    })();
  }
  const form=document.getElementById('search-form');
  if(form){
    form.addEventListener('submit',async(e)=>{
      e.preventDefault();
      const q=document.getElementById('q').value.trim(); const out=document.getElementById('results');
      if(!q){out.innerHTML='';return;}
      out.innerHTML='<p class="muted">搜尋緊…</p>';
      const idx=await (await fetch('search-index.json')).json();
      const hits=idx.filter(x=>x.text.includes(q)||x.section.includes(q)||x.book.includes(q)).slice(0,200);
      out.innerHTML='<p class="muted">搵到 '+hits.length+' 條（最多顯示200）</p>'+hits.map(h=>'<div class="result"><a href="'+h.url+'">'+h.book+' · '+h.group+' · '+h.section+' 第'+h.no+'條</a><br>'+h.text.replace(/</g,'&lt;').slice(0,220)+'</div>').join('');
    });
  }
});
