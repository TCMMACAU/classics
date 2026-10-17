#!/usr/bin/env python3
"""Build static site into docs/ from books/*/ *.md + books.json (stdlib only)."""
import json, os, re, html, shutil, pathlib, urllib.parse
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
    return f'''<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}｜經典原文</title><link rel="stylesheet" href="{prefix}assets/style.css"><link rel="manifest" href="{prefix}manifest.webmanifest"><meta name="theme-color" content="#1e1b16"><script data-goatcounter="https://tcmmacau.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script></head><body><header class="top"><p class="kicker">經索</p><h1>經典原文</h1><nav class="crumbs"><a href="{prefix}index.html">首頁</a> · <a href="{prefix}search.html">搜尋</a></nav></header>'''
def foot():
    return f'''<footer><p>{html.escape(META["source_note"])}</p><p>供閱讀檢索，不是處方依據。本站原文由原站遷移，底本見各書頁面。</p><p class="no-print">可加入主畫面方便診症時開啟：Android 用瀏覽器選單揀「加入主畫面」；iPhone／iPad 用「分享」再揀「加入主畫面」。</p><p class="no-print"><a href="https://tcmmacau.github.io/classics/sitemap/">網站地圖</a></p></footer><script src="assets/app.js"></script></body></html>'''
# fix script prefix per depth handled by replacing in caller
def main():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT/"assets").mkdir(parents=True)
    shutil.copy(ROOT/"assets/style.css", OUT/"assets/style.css")
    shutil.copy(ROOT/"assets/app.js", OUT/"assets/app.js")
    shutil.copy(ROOT/"assets/sw.js", OUT/"sw.js")
    shutil.copy(ROOT/"assets/manifest.webmanifest", OUT/"manifest.webmanifest")
    (OUT/"icons").mkdir(exist_ok=True)
    shutil.copy(ROOT/"assets/icons/icon-192.png", OUT/"icons/icon-192.png")
    shutil.copy(ROOT/"assets/icons/icon-512.png", OUT/"icons/icon-512.png")
    search_index=[]
    # homepage
    cards=[]
    total=0
    book_pages={}
    for b in META["books"]:
        total+=b["entries"]
        cards.append(f'<a class="card" href="{b["id"]}/index.html"><h2>{html.escape(b["title"])}</h2><p class="muted">{html.escape(b["blurb"])}</p><p class="count">{b["entries"]} 條 · {b["sections"]} 篇</p></a>')
    home=head("經典原文","")+f'''<main><form class="searchbar" action="search.html"><input name="q" placeholder="桂枝湯、甘草、不寐、丹沙"><button>搜尋</button></form>
<section><h2>我嘅加減</h2><p class="muted">只留喺呢部機。有連結嘅人睇唔到。可匯出／匯入備份。</p><ul class="clean" id="my-notes"></ul><button class="btn" id="export-notes">匯出加減</button> <button class="btn" id="import-notes">匯入加減</button><input type="file" id="import-file" accept="application/json" hidden></section>
<section><h2>索引</h2><div class="grid"><a class="card" href="fangji/index.html"><h3>方劑總目</h3><p class="muted">按方名回查條文出處</p></a><a class="card" href="yao/index.html"><h3>藥物總目</h3><p class="muted">以《神農本草經》藥名為綱</p></a><a class="card" href="bingmen/index.html"><h3>病門索引</h3><p class="muted">以《臨證指南醫案》門類為綱</p></a><a class="card" href="clinical/index.html"><h3>臨床入口</h3><p class="muted">診症時查原文用；不作自動辨證</p></a></div></section><p class="muted">共 {len(META["books"])} 本書 · {total} 條</p><div class="grid">{''.join(cards)}</div></main>'''+foot()
    # homepage foot script already correct
    (OUT/"index.html").write_text(home,encoding="utf-8")
    # search page
    sp=head("搜尋","")+'''<main><h2>搜尋原文</h2><form class="searchbar" id="search-form"><input id="q" placeholder="桂枝湯、甘草、不寐、丹沙"><button>搜尋</button></form><div id="results"></div></main>'''+foot()
    # auto-run query param
    sp=sp.replace("</body>", "<script>document.addEventListener('DOMContentLoaded',()=>{const qp=new URLSearchParams(location.search).get('q'); if(qp){document.getElementById('q').value=qp; setTimeout(()=>document.getElementById('search-form').dispatchEvent(new Event('submit')),50);}});</script></body>")
    (OUT/"search.html").write_text(sp,encoding="utf-8")
    (OUT/".nojekyll").write_text("",encoding="utf-8")
    collected={}
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
        collected[b["id"]]={"meta":b,"sections":sections}
        # book index
        groups={}
        for fm,entries,stem in sections:
            groups.setdefault(fm.get("group",""),[]).append((fm,entries,stem))
        parts=[head(b["title"],"../"), f'<main><nav class="crumbs"><a href="../index.html">首頁</a> / {html.escape(b["title"])}</nav><h2>{html.escape(b["title"])}</h2><p class="muted">{html.escape(b["blurb"])}</p><p><strong>底本：</strong>{html.escape(b["base_edition"])}</p>{('<p><strong>作者：</strong>'+html.escape(b['author'])+'</p>') if b.get('author') else ''}{('<p><strong>來源：</strong><a href="'+html.escape(b['source_url'])+'">'+html.escape(b.get('source_name',''))+'</a></p>') if b.get('source_url') else ''}<p class="count">{b["entries"]} 條 · {len(sections)} 篇</p>']
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
                body.append(f'<article class="entry" id="{e["id"]}" data-id="{e["id"]}"><span class="no">{html.escape(e["no"])}</span>{html.escape(e["text"])}<button class="note-btn" type="button">加減</button><a class="print-link" href="../patient.html?id={e["id"]}">病人閱讀頁</a><div class="note-area"></div></article>')
            body.append(f'<p>{prev_link}{next_link}</p></main>')
            body.append(foot().replace('src="assets/','src="../assets/'))
            (OUT/b["id"]/f"{stem}.html").write_text(''.join(body),encoding="utf-8")

    # ---------- Part 1 indexes (generated from corpus, structural only) ----------
    OLD_IDS=["neijing","shanghan","jingui","xindian","wenbing","sisheng","bencao","shuzheng","yinshi","yian","xichun"]
    def entry_url(slug, stem, eid): return f"../{slug}/{stem}.html#{eid}"
    def clean_formula(cand):
        cand=cand.strip("，。；：、 \t「」『』（）()")
        for sep in ["」","）",")","︰","：",":"]:
            if sep in cand: cand=cand.split(sep)[-1]
        for pre in ["後以","宜用","復以","原方","不用水者","暫以","從仲景少陰咽痛用","仿孫真人","噦者","故以","當以","而益之曰","黃者","宜","用","以","亦","暫","從","仿","與","故","當"]:
            if cand.startswith(pre) and len(cand)>len(pre)+1: cand=cand[len(pre):]
        return cand.strip("，。；：、 「」『』（）()")
    # 方劑總目: (A) 「X主之」 anchored in shanghan/jingui/wenbing/xindian ; (B) xichun section headings ending in formula suffix
    formulas={}
    def add_formula(name, slug, stem, fm, e):
        if not name or len(name)<2 or len(name)>14: return
        if any(x in name for x in ["云","不得","主之","云云"]): return
        formulas.setdefault(name,[]).append((slug,stem,fm,e))
    SUF=r"(?:湯|丸|散|飲|膏|丹|煎|酒)"
    for slug in ["shanghan","jingui","wenbing","xindian"]:
        if slug not in collected: continue
        for fm,entries,stem in collected[slug]["sections"]:
            for e in entries:
                for m in re.finditer(r"([^，。；：、\s]+?"+SUF+r")主之", e["text"]):
                    add_formula(clean_formula(m.group(1)), slug, stem, fm, e)
    if "xichun" in collected:
        for fm,entries,stem in collected["xichun"]["sections"]:
            title=re.sub(r"（\d+）$","",fm.get("section","").strip())
            if re.search(SUF+r"$", title) and len(title)<=12 and "問" not in title:
                for e in entries[:1]:
                    add_formula(title, "xichun", stem, fm, e)
    (OUT/"fangji").mkdir(exist_ok=True)
    fparts=[head("方劑總目","../"), '<main><nav class="crumbs"><a href="../index.html">首頁</a> / 方劑總目</nav><h2>方劑總目</h2><p class="muted">由現有語料自動生成：傷寒論、金匱要略、溫病條辨、金匱要略心典以「方名＋主之」句式抽取；醫學衷中參西錄以方名篇題抽取。同名方合併列出，連結到原文條文。不錄組成與主治說明。供閱讀檢索，不是處方依據。</p>', f'<p class="count">共 {len(formulas)} 方</p>']
    for name in sorted(formulas):
        occ=formulas[name]
        links='；'.join(f'<a href="{entry_url(slug,stem,e["id"])}">{html.escape(collected[slug]["meta"]["title"])} · {html.escape(fm.get("group",""))} · {html.escape(fm.get("section",""))} 第{html.escape(e["no"])}條</a>' for slug,stem,fm,e in occ)
        fparts.append(f'<div class="result" id="f-{sorted(formulas).index(name)+1:03d}"><strong>{html.escape(name)}</strong>（{len(occ)} 處）<br>{links}</div>')
    fparts.append('</main>'); fparts.append(foot().replace('src="assets/','src="../assets/'))
    (OUT/"fangji"/"index.html").write_text(''.join(fparts),encoding="utf-8")

    # 藥物總目: bencao entry first token as drug name (exact matching)
    drugs=[]; drug_seen={}
    if "bencao" in collected:
        for fm,entries,stem in collected["bencao"]["sections"]:
            for e in entries:
                name=re.split(r"[\s　]", e["text"].strip())[0].strip()
                if not name: continue
                if name not in drug_seen: drug_seen[name]=[]; drugs.append(name)
                drug_seen[name].append((stem,fm,e))
    shuzheng_by_title={}
    if "shuzheng" in collected:
        for fm,entries,stem in collected["shuzheng"]["sections"]:
            shuzheng_by_title.setdefault(fm.get("section",""),[]).append((stem,fm))
    yian_sections=collected.get("yian",{}).get("sections",[])
    (OUT/"yao").mkdir(exist_ok=True)
    yparts=[head("藥物總目","../"), '<main><nav class="crumbs"><a href="../index.html">首頁</a> / 藥物總目</nav><h2>藥物總目</h2><p class="muted">以《神農本草經》條首藥名為綱（共 '+str(len(drugs))+' 藥），連結本經原文、《本經疏證》同名篇，及《臨證指南醫案》原文中同名出現之條文。藥名一字者（如術、黃）易生歧義，不作醫案連結，只列本經與疏證。供閱讀檢索，不是處方依據。</p>']
    drug_match_stats={"shuzheng":0,"yian_drugs":0,"yian_occ":0}
    for di,name in enumerate(drugs,1):
        bencao_links='；'.join(f'<a href="{entry_url("bencao",stem,e["id"])}">本經 · {html.escape(fm.get("group",""))} 第{html.escape(e["no"])}條</a>' for stem,fm,e in drug_seen[name])
        sz=shuzheng_by_title.get(name,[])
        if sz: drug_match_stats["shuzheng"]+=1
        sz_txt='；'.join(f'<a href="../shuzheng/{stem}.html">{html.escape(fm.get("group",""))} · {html.escape(fm.get("section",""))}</a>' for stem,fm in sz) or '未見同名篇'
        occ=[]
        if len(name)>=2:
            for fm,entries,stem in yian_sections:
                for e in entries:
                    if name in e["text"]: occ.append((stem,fm,e))
        if occ: drug_match_stats["yian_drugs"]+=1; drug_match_stats["yian_occ"]+=len(occ)
        # per-drug page
        dparts=[head(name+"｜藥物總目","../"), f'<main><nav class="crumbs"><a href="../index.html">首頁</a> / <a href="index.html">藥物總目</a> / {html.escape(name)}</nav><h2>{html.escape(name)}</h2><h3>神農本草經</h3><p>{bencao_links}</p><h3>本經疏證</h3><p>{sz_txt}</p><h3>臨證指南醫案出現（{len(occ)} 條）</h3>']
        if len(name)<2: dparts.append('<p class="muted">藥名只有一字，未作醫案連結，以免歧義誤連。</p>')
        elif occ: dparts.append('<ul class="clean">'+''.join(f'<li><a href="{entry_url("yian",stem,e["id"])}">{html.escape(fm.get("group",""))} · {html.escape(fm.get("section",""))} 第{html.escape(e["no"])}條</a></li>' for stem,fm,e in occ)+'</ul>')
        else: dparts.append('<p class="muted">未見同名出現。</p>')
        dparts.append('</main>'); dparts.append(foot().replace('src="assets/','src="../assets/'))
        (OUT/"yao"/f"{di:03d}.html").write_text(''.join(dparts),encoding="utf-8")
        yparts.append(f'<div class="result"><a href="{di:03d}.html"><strong>{html.escape(name)}</strong></a> 本經 {len(drug_seen[name])} 條 · 疏證 {"有同名篇" if sz else "未見"} · 醫案 {len(occ) if len(name)>=2 else "—"} 條</div>')
    yparts.append('</main>'); yparts.append(foot().replace('src="assets/','src="../assets/'))
    (OUT/"yao"/"index.html").write_text(''.join(yparts),encoding="utf-8")

    # 病門索引: yian sections as spine, related = other old books' section titles containing the 門 name
    (OUT/"bingmen").mkdir(exist_ok=True)
    bparts=[head("病門索引","../"), '<main><nav class="crumbs"><a href="../index.html">首頁</a> / 病門索引</nav><h2>病門索引</h2><p class="muted">以《臨證指南醫案》原有門類與篇目為綱；「相關篇目」只按其他各書篇題是否包含該門名作標題比對，不加病證詮釋。供閱讀檢索，不是處方依據。</p>']
    related_total=0; men_count=0
    if "yian" in collected:
        for fm,entries,stem in collected["yian"]["sections"]:
            men=fm.get("section",""); men_count+=1
            rel=[]
            if len(men)>=2:
                for slug in OLD_IDS:
                    if slug=="yian" or slug not in collected: continue
                    for fm2,entries2,stem2 in collected[slug]["sections"]:
                        if men in fm2.get("section",""):
                            rel.append(f'<a href="../{slug}/{stem2}.html">{html.escape(collected[slug]["meta"]["title"])} · {html.escape(fm2.get("section",""))}</a>')
            related_total+=len(rel)
            bparts.append(f'<div class="result"><a href="../yian/{stem}.html"><strong>{html.escape(men)}</strong></a> <span class="muted">{html.escape(fm.get("group",""))} · {len(entries)} 案</span>' + (('<br>相關篇目：'+'；'.join(rel)) if rel else '') + '</div>')
    bparts.append('</main>'); bparts.append(foot().replace('src="assets/','src="../assets/'))
    (OUT/"bingmen"/"index.html").write_text(''.join(bparts),encoding="utf-8")
    print(f"indexes: formulas={len(formulas)} drugs={len(drugs)} shuzheng_matched={drug_match_stats['shuzheng']} yian_drugs={drug_match_stats['yian_drugs']} yian_occ={drug_match_stats['yian_occ']} men={men_count} related={related_total}")


    # ---------- 病人閱讀頁 ----------
    pat=head("病人閱讀頁","")+'<main><h2>病人閱讀頁</h2><div id="patient-view"><p class="muted">載入緊…</p></div><p class="no-print"><button class="btn" onclick="window.print()">列印</button></p></main>'+foot()
    (OUT/"patient.html").write_text(pat,encoding="utf-8")

    # ---------- 臨床入口 ----------
    (OUT/"clinical"/"men").mkdir(parents=True, exist_ok=True)
    formula_order={name:i+1 for i,name in enumerate(sorted(formulas))}
    drug_order={name:i+1 for i,name in enumerate(drugs)}
    men_meta=[]
    if "yian" in collected:
        for mi,(fm,entries,stem) in enumerate(collected["yian"]["sections"],1):
            men=fm.get("section","")
            combined=" ".join(e["text"] for e in entries)
            f_hits=[name for name in sorted(formulas) if name in combined]
            d_hits=[name for name in drugs if len(name)>=2 and name in combined]
            rel=[]
            if len(men)>=2:
                for slug in OLD_IDS:
                    if slug=="yian" or slug not in collected: continue
                    for fm2,entries2,stem2 in collected[slug]["sections"]:
                        if men in fm2.get("section",""):
                            rel.append(f'<a href="../../{slug}/{stem2}.html">{html.escape(collected[slug]["meta"]["title"])} · {html.escape(fm2.get("section",""))}</a>')
            men_meta.append((mi,men,fm,entries,stem,f_hits,d_hits,rel))
            mp=[head(men+"｜臨床入口","../../"),
                f'<main><nav class="crumbs"><a href="../../index.html">首頁</a> / <a href="../index.html">臨床入口</a> / {html.escape(men)}</nav><h2>{html.escape(men)}</h2>',
                f'<h3>原篇</h3><p><a href="../../yian/{stem}.html">{html.escape(fm.get("group",""))} · {html.escape(men)}</a>（{len(entries)} 案）</p>']
            if rel: mp.append('<h3>相關篇目（篇題比對）</h3><p>'+'；'.join(rel)+'</p>')
            mp.append('<h3>方劑總目命中</h3>')
            if f_hits: mp.append('<ul class="clean">'+''.join(f'<li><a href="../../fangji/index.html#f-{formula_order[n]:03d}">{html.escape(n)}</a></li>' for n in f_hits)+'</ul>')
            else: mp.append('<p class="muted">呢一門原文未見方劑總目方名出現。</p>')
            mp.append('<h3>藥物總目命中</h3>')
            if d_hits: mp.append('<ul class="clean">'+''.join(f'<li><a href="../../yao/{drug_order[n]:03d}.html">{html.escape(n)}</a></li>' for n in d_hits)+'</ul>')
            else: mp.append('<p class="muted">呢一門原文未見藥物總目藥名出現。</p>')
            mp.append('<p class="muted">以上只係索引比對結果，唔係辨證或處方建議。供閱讀檢索，不是處方依據。</p></main>')
            mp.append(foot().replace('src="assets/','src="../../assets/'))
            (OUT/"clinical"/"men"/f"{mi:03d}.html").write_text(''.join(mp),encoding="utf-8")
    cparts=[head("臨床入口","../"),
      '<main><nav class="crumbs"><a href="../index.html">首頁</a> / 臨床入口</nav><h2>臨床入口</h2>',
      '<p>呢一頁係畀醫師診症時查返原文用嘅工作入口：幫你快啲搵返經典條文、方名同藥名出處。佢唔做自動辨證，唔會開方，亦唔會畀劑量；最後判斷要由醫師面診評估之後自己決定。</p>',
      '<p><strong>切勿喺呢度輸入任何可以識別病人身份嘅資料</strong>（例如姓名、聯絡方法、身份證號碼）。呢度只應該放醫師自己嘅工作筆記（加減），而加減只存喺呢部機嘅瀏覽器入面，唔會上傳去任何伺服器。</p>',
      '<h3>覆診快速開啟（我的加減，按最後修改排先）</h3><ul class="clean" id="clinical-notes"></ul><button class="btn" id="export-notes">匯出加減</button> <button class="btn" id="import-notes">匯入加減</button><input type="file" id="import-file" accept="application/json" hidden>',
      '<h3>病門入口</h3><p class="muted">以《臨證指南醫案》112 門為綱，一頁睇晒原篇、相關篇目、方劑總目命中同藥物總目命中。全部只係現有索引嘅比對結果。</p><ul class="clean">']
    for mi,men,fm,entries,stem,f_hits,d_hits,rel in men_meta:
        cparts.append(f'<li><a href="men/{mi:03d}.html">{html.escape(men)}</a> <span class="muted">{html.escape(fm.get("group",""))} · {len(entries)} 案 · 方 {len(f_hits)} · 藥 {len(d_hits)}</span></li>')
    cparts.append('</ul><p class="muted">可加入主畫面方便診症時開啟：Android 用瀏覽器選單揀「加入主畫面」；iPhone／iPad 用「分享」再揀「加入主畫面」。</p></main>')
    cparts.append(foot().replace('src="assets/','src="../assets/'))
    (OUT/"clinical"/"index.html").write_text(''.join(cparts),encoding="utf-8")
    print(f"clinical: men={len(men_meta)}")


    # ---------- 網站地圖 (human page) + sitemap.xml + robots.txt ----------
    (OUT/"sitemap").mkdir(exist_ok=True)
    sm=[head("網站地圖","../"), '<main><nav class="crumbs"><a href="../index.html">首頁</a> / 網站地圖</nav><h2>網站地圖</h2><h3>索引與工具</h3><ul class="clean">'
         '<li><a href="../index.html">首頁</a></li><li><a href="../search.html">搜尋原文</a></li>'
         '<li><a href="../fangji/index.html">方劑總目</a></li><li><a href="../yao/index.html">藥物總目</a></li>'
         '<li><a href="../bingmen/index.html">病門索引</a></li><li><a href="../clinical/index.html">臨床入口</a></li></ul>'
         '<h3>書目</h3><p class="muted">撳入書名去到該書篇目，篇目入面再去各篇原文。</p><ul class="clean">']
    for b in META["books"]:
        sm.append(f'<li><a href="../{b["id"]}/index.html">{html.escape(b["title"])}</a> <span class="muted">{html.escape(b["blurb"])}（{b["entries"]} 條 · {b["sections"]} 篇）</span></li>')
    sm.append('</ul></main>'); sm.append(foot().replace('src="assets/','src="../assets/'))
    (OUT/"sitemap"/"index.html").write_text(''.join(sm),encoding="utf-8")

    BASE="https://tcmmacau.github.io/classics/"
    urls=[]
    for fp in sorted(OUT.rglob("*.html")):
        rel=fp.relative_to(OUT).as_posix()
        if rel=="patient.html":  # utility-only view (needs ?id=), not a crawlable page
            continue
        if rel.endswith("/index.html") or rel=="index.html":
            loc=BASE+urllib.parse.quote(rel[: -len("index.html")])
        else:
            loc=BASE+urllib.parse.quote(rel)
        urls.append(loc)
    # homepage first, then the rest in path order
    urls.sort(key=lambda u: (u!=BASE, u))
    xml=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml.append(f"<url><loc>{html.escape(u)}</loc></url>")
    xml.append("</urlset>")
    (OUT/"sitemap.xml").write_text("\n".join(xml)+"\n",encoding="utf-8")
    (OUT/"robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: https://tcmmacau.github.io/classics/sitemap.xml\n",encoding="utf-8")
    print(f"sitemap: {len(urls)} urls")

    (OUT/"search-index.json").write_text(json.dumps(search_index,ensure_ascii=False),encoding="utf-8")
    print(f"built {len(search_index)} entries, {len(META['books'])} books -> {OUT}")
if __name__=="__main__": main()
