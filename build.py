#!/usr/bin/env python3
"""articles.json থেকে প্রতিটা লেখার আলাদা পাতা (a/<id>/index.html) ও sitemap.xml বানায়।
GitHub Actions এটা নিজে থেকে চালায়। হাতে চালাতে চাইলে: python3 build.py"""
import json, os, shutil, html, datetime, urllib.request
import xml.etree.ElementTree as ET

SITE = "https://sastobataion.github.io"
BASE = "/"
NAME = "স্বাস্থ্য বাতায়ন টিপস"
GC = "sastobataion"  # GoatCounter কোড (ভিজিটর গণনা)
EYE = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>'
L = {"food": "খাবার", "sleep": "ঘুম", "move": "ব্যায়াম", "mind": "মনের যত্ন", "safe": "সুরক্ষা",
     "child": "শিশু", "women": "নারী", "elder": "বয়স্ক", "chronic": "দীর্ঘমেয়াদি রোগ"}
CHANNEL_ID = "UC5crqMPnKmVbGh_S5jBSWIQ"  # ইউটিউব চ্যানেল Gkquiztube
DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"

def b36(n):
    s = ""
    while True:
        s = DIGITS[n % 36] + s
        n //= 36
        if n == 0:
            return s

def aid(a):
    # সাইটের JavaScript-এর aid() ফাংশনের সঙ্গে হুবহু একই হিসাব
    if a.get("id"):
        return a["id"]
    x = 5381
    u = a["title"].encode("utf-16-le")
    for i in range(0, len(u), 2):
        x = ((x << 5) + x + (u[i] | (u[i + 1] << 8))) & 0xFFFFFFFF
    return "a" + b36(x)

def esc(s):
    return html.escape(str(s), quote=True)

def bn_date(d):
    m = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
    t = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
    try:
        y, mo, da = map(int, d.split("-"))
        return f"{da} {m[mo-1]} {y}".translate(t)
    except Exception:
        return ""

CSS = """:root{--bg:#fff;--sf:#f2f6f4;--ink:#14201d;--mu:#55665f;--ln:#dfe6e2;--br:#1f7a5c;--bi:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#0e1815;--sf:#162622;--ink:#e8f1ed;--mu:#9db3aa;--ln:#263c35;--br:#4fc29a;--bi:#06231a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Hind Siliguri","Noto Sans Bengali",system-ui,sans-serif;font-size:18px;line-height:1.8}
.w{max-width:720px;margin:0 auto;padding:0 16px}
header{border-bottom:1px solid var(--ln);padding:10px 0}
.logo{display:flex;align-items:center;gap:8px;font-family:"Noto Serif Bengali",serif;font-weight:800;font-size:22px;color:var(--br);text-decoration:none}
.logo img{width:34px;height:34px}
h1{font-family:"Noto Serif Bengali",serif;font-size:clamp(26px,5vw,36px);font-weight:800;line-height:1.4;margin:6px 0 8px}
.tag{color:var(--br);font-weight:600;font-size:15px}.mt{color:var(--mu);font-size:15px;margin:0 0 12px}
.hero{width:100%;border-radius:10px;display:block;margin:10px 0}
.vid{width:100%;aspect-ratio:16/9;border:0;border-radius:8px;margin:8px 0}
.box{border-top:1px solid var(--ln);margin-top:18px;padding-top:12px}.box h2{font-size:19px;margin:0 0 6px}
.box a,.back a{color:var(--br)}.box p{margin:2px 0;color:var(--mu);font-size:16px}
button{background:var(--br);color:var(--bi);border:0;border-radius:999px;padding:6px 22px;font:inherit;font-weight:600;cursor:pointer;margin-top:10px}
.sl{display:inline-block;margin:10px 0 0 12px;color:var(--br);font-weight:600}.vc{display:flex;align-items:center;gap:6px;color:var(--mu)}.vc b{color:var(--ink)}
footer{border-top:1px solid var(--ln);margin-top:28px;padding:18px 0 32px;color:var(--mu);font-size:15px}
.ab{background:var(--sf);border-radius:10px;padding:12px 16px;margin-top:18px;font-size:16px}.ab b{display:block}.ab a{color:var(--br)}
.note{background:var(--sf);border-left:5px solid #d9742b;border-radius:8px;padding:10px 14px;margin-top:16px;font-size:16px}"""

def page(a, pid, rel, today):
    c = a.get("cat") if a.get("cat") in L else "safe"
    url = f"{SITE}/a/{pid}/"
    wa = urllib.parse.quote(a["title"] + " " + url)
    fb = urllib.parse.quote(url)
    paras = a.get("body", [])
    desc = (paras[0] if paras else a["title"]).strip()
    desc = desc[:150] + ("…" if len(desc) > 150 else "")
    img = a.get("img", "")
    ogimg = f"{SITE}/{img}" if img.startswith("images/") else f"{SITE}/banner.png"
    date = a.get("date", "")
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "inLanguage": "bn",
          "mainEntityOfPage": url, "image": [ogimg],
          "author": ({"@type": "Person", "name": a["author"]} if a.get("author") else {"@type": "Organization", "name": NAME}),
          "publisher": {"@type": "Organization", "name": NAME, "logo": {"@type": "ImageObject", "url": f"{SITE}/logo.png"}}}
    if date:
        ld["datePublished"] = date
    if a.get("upd"):
        ld["dateModified"] = a["upd"]
    ldj = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
    upd = a.get("upd", "")
    meta = " · ".join(x for x in [bn_date(date) if date else "", ("হালনাগাদ: " + bn_date(upd)) if upd and upd != date else "", a.get("author", "")] if x)
    body = "".join(f"<p>{esc(p)}</p>" for p in paras)
    if img.startswith("images/"):
        body = f'<img class="hero" src="{BASE}{esc(img)}" alt="{esc(a["title"])}">' + body
    yt = a.get("yt", "")
    if len(yt) == 11 and all(ch.isalnum() or ch in "-_" for ch in yt):
        body += f'<iframe class="vid" src="https://www.youtube-nocookie.com/embed/{yt}" title="{esc(a["title"])}" loading="lazy" allowfullscreen></iframe>'
    if a.get("rev"):
        body += f'<p class="mt"><b>চিকিৎসক কর্তৃক পর্যালোচিত:</b> {esc(a["rev"])}</p>'
    srcs = ""
    for s in a.get("src", []) or []:
        t, u = s.get("t", ""), s.get("u", "")
        if u.startswith("https://"):
            srcs += f'<p><a href="{esc(u)}" rel="noopener" target="_blank">{esc(t or u)}</a></p>'
        elif t:
            srcs += f"<p>{esc(t)}</p>"
    if srcs:
        body += f'<div class="box"><h2>তথ্যসূত্র</h2>{srcs}</div>'
    if rel:
        links = "".join(f'<p><a href="{BASE}a/{esc(i)}/">{esc(t)}</a></p>' for i, t in rel)
        body += f'<div class="box"><h2>আরও পড়ুন</h2>{links}</div>'
    who = ("লেখক: " + esc(a["author"])) if a.get("author") else "প্রকাশক: Serajul Islam, সাইট মালিক, কেশবপুর, যশোর"
    body += f'<div class="ab"><b>{who}</b>এই লেখা সাধারণ তথ্যের জন্য, চিকিৎসকের পরামর্শের বিকল্প নয়। <a href="{BASE}#p=edit">সম্পাদকীয় নীতি</a></div>'
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(a['title'])} – {NAME}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(a['title'])}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{ogimg}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{BASE}logo.svg" type="image/svg+xml">
<link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600&family=Noto+Serif+Bengali:wght@800&display=swap" rel="stylesheet">
<script type="application/ld+json">{ldj}</script>
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="{SITE}/a/feed.xml">
<script data-goatcounter="https://{GC}.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
<style>{CSS}</style>
</head>
<body>
<header><div class="w"><a class="logo" href="{BASE}"><img src="{BASE}logo.svg" alt="">{NAME}</a></div></header>
<main class="w"><article>
<span class="tag">{esc(L[c])}</span>
<h1>{esc(a['title'])}</h1>
<p class="mt">{esc(meta)}</p>
{body}
<button id="sh" type="button">শেয়ার করুন</button>
<a class="sl" href="https://wa.me/?text={wa}" target="_blank" rel="noopener">হোয়াটসঅ্যাপ</a><a class="sl" href="https://www.facebook.com/sharer/sharer.php?u={fb}" target="_blank" rel="noopener">ফেসবুক</a>
<p class="back"><a href="{BASE}">← সব লেখা দেখুন</a></p>
</article></main>
<footer><div class="w"><div class="note">এই লেখা সাধারণ তথ্যের জন্য, চিকিৎসকের পরামর্শের বিকল্প নয়। শারীরিক সমস্যা থাকলে নিবন্ধিত চিকিৎসকের সঙ্গে কথা বলুন। জরুরি অবস্থায় এখনই নিকটস্থ হাসপাতালে যান।</div>
<p>© {NAME}। সাইট মালিক: Serajul Islam। যোগাযোগ: <a href="https://wa.me/8801724119866" style="color:var(--br)">হোয়াটসঅ্যাপ</a> · <a href="mailto:sastobataion@gmail.com" style="color:var(--br)">ইমেইল</a></p><p class="vc" id="vc" hidden><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg> মোট ভিজিটর: <b id="vcn"></b></p></div></footer>
<script>fetch("https://{GC}.goatcounter.com/counter/TOTAL.json").then(function(r){{return r.json()}}).then(function(j){{var n=parseInt(String(j.count_unique||j.count||"").replace(/\\D/g,""),10);if(n>0){{document.getElementById("vcn").textContent=n.toLocaleString("bn-BD");document.getElementById("vc").hidden=false}}}}).catch(function(){{}})</script>
<script>document.getElementById("sh").onclick=function(){{var d={{title:document.title,url:location.href}};if(navigator.share){{navigator.share(d).catch(function(){{}})}}else if(navigator.clipboard){{navigator.clipboard.writeText(d.url).then(function(){{document.getElementById("sh").textContent="লিংক কপি হয়েছে"}})}}}}</script>
</body>
</html>
"""

def parse_feed(data):
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    out = []
    for e in ET.fromstring(data).findall("a:entry", ns)[:6]:
        vid = e.findtext("yt:videoId", namespaces=ns)
        t = e.findtext("a:title", namespaces=ns)
        if vid and t:
            out.append({"id": vid, "t": t.strip(), "d": (e.findtext("a:published", namespaces=ns) or "")[:10]})
    return out

def fetch_videos():
    """চ্যানেলের সর্বশেষ ভিডিওর তালিকা videos.json-এ রাখে। না পেলে পুরনো ফাইল অক্ষত থাকে।"""
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        out = parse_feed(urllib.request.urlopen(req, timeout=20).read())
        if out:
            json.dump(out, open("videos.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"{len(out)}টা ভিডিও পাওয়া গেছে")
    except Exception as ex:
        print("ভিডিওর তালিকা আনা যায়নি:", ex)

def write_feed(vis, ids, today):
    from email.utils import format_datetime
    items = ""
    for a, pid in list(zip(vis, ids))[:20]:
        d = a.get("date") or today
        try:
            when = datetime.datetime.fromisoformat(d + "T06:00:00+00:00")
        except ValueError:
            when = datetime.datetime.now(datetime.timezone.utc)
        desc = (a.get("body") or [""])[0].strip()
        items += (f"<item><title>{esc(a['title'])}</title><link>{SITE}/a/{pid}/</link><guid isPermaLink=\"true\">{SITE}/a/{pid}/</guid>"
                  f"<pubDate>{format_datetime(when)}</pubDate><description>{esc(desc)}</description></item>\n")
    feed = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{NAME}</title><link>{SITE}/</link>'
            f'<description>সহজ বাংলায় স্বাস্থ্য পরামর্শ</description><language>bn</language>\n{items}</channel></rss>\n')
    open("a/feed.xml", "w", encoding="utf-8").write(feed)

def main():
    arts = json.load(open("articles.json", encoding="utf-8"))
    today = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=6)).date().isoformat()
    vis = [a for a in arts if not a.get("draft") and (not a.get("date") or a["date"] <= today)]
    shutil.rmtree("a", ignore_errors=True)
    os.makedirs("a")
    open("a/index.html", "w", encoding="utf-8").write(f'<!DOCTYPE html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={BASE}"><title>{NAME}</title>')
    seen, ids = set(), []
    for a in vis:
        pid, n = aid(a), 2
        while pid in seen:
            pid = f"{aid(a)}-{n}"; n += 1
        seen.add(pid); ids.append(pid)
    urls = [(SITE + "/", today)]
    for a, pid in zip(vis, ids):
        rel = [(i, x["title"]) for x, i in zip(vis, ids) if x is not a and x.get("cat") == a.get("cat")][:3]
        os.makedirs(f"a/{pid}", exist_ok=True)
        open(f"a/{pid}/index.html", "w", encoding="utf-8").write(page(a, pid, rel, today))
        urls.append((f"{SITE}/a/{pid}/", a.get("date") or today))
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n"
    open("sitemap.xml", "w", encoding="utf-8").write(sm)
    write_feed(vis, ids, today)
    print(f"{len(vis)}টা লেখার পাতা তৈরি হয়েছে")
    fetch_videos()

if __name__ == "__main__":
    main()
