// 我嘅加減：只存喺呢部機嘅瀏覽器 localStorage，唔會上傳。KEY 保持 classics-notes-v1，舊筆記相容。
const KEY='classics-notes-v1';
const SW_URL=(document.currentScript&&document.currentScript.src)?new URL('../sw.js',document.currentScript.src).href:'sw.js';
if('serviceWorker' in navigator){window.addEventListener('load',()=>{navigator.serviceWorker.register(SW_URL).catch(()=>{});});}
function loadNotes(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return{}}}
function saveNotes(n){localStorage.setItem(KEY,JSON.stringify(n))}
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
    Object.keys(raw).forEach(id=>{out[id]=normalizeNote(raw[id]);});
    const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='加減備份.json';a.click();
  };
  const imp=document.getElementById('import-notes'), file=document.getElementById('import-file');
  if(imp){imp.onclick=()=>file.click(); file.onchange=()=>{const f=file.files[0]; if(!f)return; f.text().then(t=>{try{
      const obj=JSON.parse(t); if(typeof obj!=='object'||Array.isArray(obj))throw 0;
      const clean={};
      for(const [id,v] of Object.entries(obj)){
        if(typeof v==='string') clean[id]=v;
        else if(v&&typeof v==='object'&&!Array.isArray(v)) clean[id]=normalizeNote(v);
        else throw 0;
      }
      saveNotes(clean); location.reload();
    }catch(e){alert('檔案格式唔啱');}});};}
}
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.entry').forEach(el=>{
    const id=el.dataset.id; renderNote(el,id);
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
