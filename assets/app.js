// 我嘅加減：只存喺呢部機嘅瀏覽器 localStorage，唔會上傳
const KEY='classics-notes-v1';
function loadNotes(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return{}}}
function saveNotes(n){localStorage.setItem(KEY,JSON.stringify(n))}
function renderNote(el,id){
  const notes=loadNotes(); const wrap=el.querySelector('.note-area'); if(!wrap)return;
  wrap.innerHTML='';
  if(notes[id]){const d=document.createElement('div');d.className='saved-note';d.textContent=notes[id];wrap.appendChild(d);}
}
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.entry').forEach(el=>{
    const id=el.dataset.id; renderNote(el,id);
    const btn=el.querySelector('.note-btn'); if(!btn)return;
    btn.addEventListener('click',()=>{
      const area=el.querySelector('.note-area'); const notes=loadNotes();
      area.innerHTML='<div class="note-box"><textarea placeholder="寫低你嘅加減／筆記（只留喺呢部機）">'+(notes[id]||'')+'</textarea><br><button class="btn save">儲存</button> <button class="btn del">刪除</button></div>';
      area.querySelector('.save').onclick=()=>{const v=area.querySelector('textarea').value.trim();const n=loadNotes(); if(v)n[id]=v; else delete n[id]; saveNotes(n); renderNote(el,id);};
      area.querySelector('.del').onclick=()=>{const n=loadNotes(); delete n[id]; saveNotes(n); renderNote(el,id);};
    });
  });
  const exp=document.getElementById('export-notes');
  if(exp){
    const list=document.getElementById('my-notes'); const notes=loadNotes(); const ids=Object.keys(notes);
    list.innerHTML=ids.length? ids.map(id=>'<li><code>'+id+'</code>：'+notes[id].replace(/</g,'&lt;')+'</li>').join('') : '<li class="muted">暫時未有加減。</li>';
    exp.onclick=()=>{const blob=new Blob([JSON.stringify(loadNotes(),null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='classics-notes.json';a.click();};
    const imp=document.getElementById('import-notes'), file=document.getElementById('import-file');
    if(imp){imp.onclick=()=>file.click(); file.onchange=()=>{const f=file.files[0]; if(!f)return; f.text().then(t=>{try{const obj=JSON.parse(t); if(typeof obj!=='object'||Array.isArray(obj))throw 0; saveNotes(obj); location.reload();}catch(e){alert('檔案格式唔啱');}});};}
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
