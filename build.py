#!/usr/bin/env python3
"""Build static site into docs/ from books/*/ *.md + books.json (stdlib only)."""
import json, os, re, html, shutil, pathlib
ROOT=pathlib.Path(__file__).parent
OUT=ROOT/"docs"
META=json.loads((ROOT/"books.json").read_text(encoding="utf-8"))
def parse_md(p):
    t=p.read_text(encoding="utf-8")
    m=re.match(r"---\n(.*?)\n---\n", t, re.S)
    fm={}
    if m:
        for line in m.group(1).splitlines():
            if ": " in line:
                k,v=line.split(": ",1); fm[k]=v
    entries=[]
    for em in re.finditer(r"<!-- entry id=(\S+) no=(\S+) -->\n\*\*(.+?)\*\* (.*)", t):
        entries.append({"id":em.group(1),"no":em.group(3),"text":em.group(4).strip()})
    return fm, entries
def head(title, prefix):
    return f'''<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}｜經典原文</title><link rel="stylesheet" href="{prefix}assets/style.css"></head><body><header class="top"><p class="kicker">經索</p><h1>經典原文</h1><nav class="crumbs"><a href="{prefix}index.html">首頁</a> · <a href="{prefix}search.html">搜尋</a></nav></header>'''
def foot():
    return f'''<footer><p>{html.escape(META["source_note"])}</p><p>供閱讀檢索，不是處方依據。本站原文由原站遷移，底本見各書頁面。</p></footer><script src="assets/app.js"></script></body></html>'''
# fix script prefix per depth handled by replacing in caller
def main():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT/"assets").mkdir(parents=True)
    shutil.copy(ROOT/"assets/style.css", OUT/"assets/style.css")
    shutil.copy(ROOT/"assets/app.js", OUT/"assets/app.js")
    search_index=[]
    # homepage
    cards=[]
    total=0
    book_pages={}
    for b in META["books"]:
        total+=b["entries"]
        cards.append(f'<a class="card" href="{b["id"]}/index.html"><h2>{html.escape(b["title"])}</h2><p class="muted">{html.escape(b["blurb"])}</p><p class="count">{b["entries"]} 條 · {b["sections"]} 篇</p></a>')
    home=head("經典原文","")+f'''<main><form class="searchbar" action="search.html"><input name="q" placeholder="桂枝湯、甘草、不寐、丹沙"><button>搜尋</button></form>
<section><h2>我嘅加減</h2><p class="muted">只留喺呢部機。有連結嘅人睇唔到。可匯出／匯入備份。</p><ul class="clean" id="my-notes"></ul><button class="btn" id="export-notes">匯出加減 JSON</button> <button class="btn" id="import-notes">匯入加減 JSON</button><input type="file" id="import-file" accept="application/json" hidden></section>
<p class="muted">共 {len(META["books"])} 本書 · {total} 條</p><div class="grid">{''.join(cards)}</div></main>'''+foot().replace('src="assets/','src="')
    # homepage foot script already correct
    (OUT/"index.html").write_text(home,encoding="utf-8")
    # search page
    sp=head("搜尋","")+'''<main><h2>搜尋原文</h2><form class="searchbar" id="search-form"><input id="q" placeholder="桂枝湯、甘草、不寐、丹沙"><button>搜尋</button></form><div id="results"></div></main>'''+foot()
    # auto-run query param
    sp=sp.replace("</body>", "<script>document.addEventListener('DOMContentLoaded',()=>{const qp=new URLSearchParams(location.search).get('q'); if(qp){document.getElementById('q').value=qp; setTimeout(()=>document.getElementById('search-form').dispatchEvent(new Event('submit')),50);}});</script></body>")
    (OUT/"search.html").write_text(sp,encoding="utf-8")
    (OUT/".nojekyll").write_text("",encoding="utf-8")
    # books
    for b in META["books"]:
        bdir=ROOT/"books"/b["id"]
        files=sorted(bdir.glob("*.md"))
        sections=[]
        for p in files:
            fm, entries = parse_md(p)
            sections.append((fm,entries,p.stem))
            for e in entries:
                search_index.append({"id":e["id"],"book":b["title"],"group":fm.get("group",""),"section":fm.get("section",""),"no":e["no"],"text":e["text"],"url":f'{b["id"]}/{p.stem}.html#{e["id"]}'})
        # book index
        groups={}
        for fm,entries,stem in sections:
            groups.setdefault(fm.get("group",""),[]).append((fm,entries,stem))
        parts=[head(b["title"],"../"), f'<main><nav class="crumbs"><a href="../index.html">首頁</a> / {html.escape(b["title"])}</nav><h2>{html.escape(b["title"])}</h2><p class="muted">{html.escape(b["blurb"])}</p><p><strong>底本：</strong>{html.escape(b["base_edition"])}</p><p class="count">{b["entries"]} 條 · {len(sections)} 篇</p>']
        for gname, secs in groups.items():
            parts.append(f'<h3>{html.escape(gname)}</h3><ul class="clean">')
            for fm,entries,stem in secs:
                parts.append(f'<li><a href="{stem}.html">{html.escape(fm.get("section",""))}</a> <span class="muted">（{len(entries)} 條）</span></li>')
            parts.append('</ul>')
        parts.append('</main>')
        parts.append(foot().replace('src="assets/','src="../assets/'))
        (OUT/b["id"]).mkdir(parents=True, exist_ok=True)
        (OUT/b["id"]/"index.html").write_text(''.join(parts),encoding="utf-8")
        # chapter pages, with prev/next
        for idx,(fm,entries,stem) in enumerate(sections):
            prev_link=f'<a href="{sections[idx-1][2]}.html">← 上一篇</a> ' if idx>0 else ''
            next_link=f' <a href="{sections[idx+1][2]}.html">下一篇 →</a>' if idx < len(sections)-1 else ''
            body=[head(f'{fm.get("section","")}｜{b["title"]}',"../"),
              f'<main><nav class="crumbs"><a href="../index.html">首頁</a> / <a href="index.html">{html.escape(b["title"])}</a> / {html.escape(fm.get("group",""))}</nav><h2>{html.escape(fm.get("section",""))}</h2><p class="muted">{html.escape(b["title"])} · {html.escape(fm.get("group",""))}</p><p>{prev_link}{next_link}</p>']
            for e in entries:
                body.append(f'<article class="entry" id="{e["id"]}" data-id="{e["id"]}"><span class="no">{html.escape(e["no"])}</span>{html.escape(e["text"])}<button class="note-btn" type="button">加減</button><div class="note-area"></div></article>')
            body.append(f'<p>{prev_link}{next_link}</p></main>')
            body.append(foot().replace('src="assets/','src="../assets/'))
            (OUT/b["id"]/f"{stem}.html").write_text(''.join(body),encoding="utf-8")
    (OUT/"search-index.json").write_text(json.dumps(search_index,ensure_ascii=False),encoding="utf-8")
    print(f"built {len(search_index)} entries, {len(META['books'])} books -> {OUT}")
if __name__=="__main__": main()
