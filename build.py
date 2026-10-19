#!/usr/bin/env python3
"""Build post.cold.fyi from cards/*/card.json.

No dependencies. Run from the repo root:  python3 build.py
Writes index.html, about/index.html, c/<id>/index.html, feed.json, sitemap.xml.
Cards are added by tools/publish.py in the private post-inbox repo, never by hand-editing HTML.
"""
import html, json, os, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent
SITE = "https://post.cold.fyi"
BOX = ["Third Polar Arch", "ATTN: post.cold.fyi", "PO Box 120264", "Boston, MA 02112-0264"]
CONTACT = "hello@thirdpolararch.com"
KIND_ORDER = ["mail art", "postcard", "letter", "ephemera"]

e = lambda s: html.escape(str(s), quote=True)


def load_cards():
    cards = []
    for p in sorted((ROOT / "cards").glob("*/card.json")):
        c = json.loads(p.read_text())
        c["_dir"] = p.parent.name
        cards.append(c)
    # newest received first, then id descending
    cards.sort(key=lambda c: (c.get("received", ""), c["id"]), reverse=True)
    return cards


def page(title, body, desc="Mail art and postcards sent to a Boston PO box, cataloged by Third Polar Arch.", canonical="/", depth=0, og_image=None):
    up = "../" * depth
    og = f'<meta property="og:image" content="{SITE}/{og_image}">' if og_image else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{canonical}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
{og}
<link rel="icon" href="{up}assets/icon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@400;500;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/post.css">
</head>
<body>
<div class="airmail" aria-hidden="true"></div>
<header class="mast">
  <a class="wordmark" href="{up}">Post</a>
  <nav><a href="{up}">Archive</a><a href="{up}about/">Send something</a></nav>
</header>
<main>
{body}
</main>
<footer class="foot">
  <p>Post is the mail archive of <a href="https://thirdpolararch.com">Third Polar Arch</a>, Boston. Fronts only. Nothing is returned and no reply is owed.</p>
  <p>Want something taken down? Email <a href="mailto:{CONTACT}?subject=Post%20takedown">{CONTACT}</a> with the catalog number.</p>
</footer>
</body>
</html>
"""


def address_block(big=True):
    cls = "address big" if big else "address"
    return f"""<address class="{cls}">
  <span class="to">Send anything to</span>
  {"".join(f"<span>{e(line)}</span>" for line in BOX)}
</address>"""


def tile(c):
    origin = c.get("origin", {}).get("value", "")
    date = c.get("date", {}).get("value", "")
    meta = ", ".join(x for x in (origin, date) if x)
    if c.get("made"):
        meta = c.get("printed", "")
    alt = c.get("alt") or c.get("title", "")
    label = c.get("series") if c.get("made") else c.get("kind", "")
    return f"""<li class="tile" data-kind="{e(c.get('kind',''))}">
  <a href="c/{e(c['id'])}/">
    <span class="mount"><img src="cards/{e(c['_dir'])}/front.webp" alt="{e(alt)}" loading="lazy" width="{c['images']['front_w']}" height="{c['images']['front_h']}"></span>
    <span class="tline"><span class="no">{e(c['id'])}</span><span class="kind">{e(label)}</span></span>
    <span class="ttitle">{e(c.get('title',''))}</span>
    <span class="tmeta">{e(meta)}</span>
  </a>
</li>"""


def build_index(all_cards):
    cards = [c for c in all_cards if not c.get("made")]
    made = sorted((c for c in all_cards if c.get("made")), key=lambda c: c["id"])
    kinds = [k for k in KIND_ORDER if any(c.get("kind") == k for c in cards)]
    if cards:
        filt = ""
        if len(kinds) > 1:
            btns = "".join(f'<button type="button" data-kind="{e(k)}" aria-pressed="false">{e(k.capitalize())}</button>' for k in kinds)
            filt = f'<div class="filter" role="group" aria-label="Show only"><button type="button" data-kind="" aria-pressed="true">Everything</button>{btns}</div>'
        grid = f'{filt}<ol class="grid" reversed>{"".join(tile(c) for c in cards)}</ol>'
        count = f'<p class="count">{len(cards)} piece{"s" if len(cards)!=1 else ""} cataloged, newest first.</p>'
    else:
        grid = '<div class="empty"><p>Nothing is cataloged yet. The first piece that lands in the box goes here.</p></div>'
        count = ""
    body = f"""<section class="intro">
  <div class="lede">
    <h1>Mail sent to a box in Boston, cataloged.</h1>
    <p>Postcards, mail art, letters and paper ephemera that arrive at the Third Polar Arch PO box. Each piece gets a catalog number and the plain facts: where it came from, the postmark, the stamps, the paper, and a date estimate with its reasoning. Where something is a guess, it says so.</p>
  </div>
  {address_block()}
</section>
<section class="archive" aria-label="Archive">
{count}
{grid}
</section>
{made_section(made)}
<script>
(function(){{
  var f=document.querySelector('.archive .filter'); if(!f) return;
  f.addEventListener('click',function(ev){{
    var b=ev.target.closest('button'); if(!b) return;
    var k=b.getAttribute('data-kind');
    f.querySelectorAll('button').forEach(function(x){{x.setAttribute('aria-pressed', x===b?'true':'false');}});
    document.querySelectorAll('.archive .tile').forEach(function(t){{t.hidden = k && t.getAttribute('data-kind')!==k;}});
  }});
}})();
</script>"""
    return page("Post - mail sent to Boston, cataloged", body)


def made_section(made):
    if not made:
        return ""
    series = []
    for c in made:
        if c.get("series") not in series:
            series.append(c.get("series"))
    groups = "".join(
        f'<h3 class="series">{e(s)}</h3><ol class="grid">{"".join(tile(c) for c in made if c.get("series") == s)}</ol>'
        for s in series)
    return f"""<section class="archive made" id="made" aria-label="Made here">
<h2 class="madehead">Made here</h2>
<p class="count">Postcards Third Polar Arch has printed and sent out. Fronts only, with the print specs.</p>
{groups}
</section>"""


def field_row(f):
    est = f.get("status") == "estimated"
    flag = '<span class="est" title="Estimated, not confirmed">est.</span>' if est else ""
    basis = f'<span class="basis">{e(f["basis"])}</span>' if f.get("basis") else ""
    return f'<div class="row"><dt>{e(f["label"])}</dt><dd>{e(f["value"])}{flag}{basis}</dd></div>'


def build_card(c, prev_c, next_c):
    d = c["_dir"]
    up = "../../"
    rows = []
    for key, label in (("origin", "Origin"), ("postmark", "Postmark"), ("date", "Date")):
        if c.get(key):
            f = dict(c[key]); f["label"] = label
            rows.append(field_row(f))
    for f in c.get("catalog", []):
        rows.append(field_row(f))
    if c.get("made"):
        rows.insert(0, field_row({"label": "Series", "value": c.get("series", "")}))
        rows.append(field_row({"label": "Printed", "value": c.get("printed", "")}))
        rows.append(field_row({"label": "Made by", "value": "Third Polar Arch"}))
    else:
        rows.append(field_row({"label": "Received", "value": c.get("received", "")}))
    if c.get("link"):
        rows.append(f'<div class="row"><dt>See</dt><dd><a href="{e(c["link"]["url"])}">{e(c["link"]["label"])}</a></dd></div>')
    if c.get("via") and c["via"] != "direct":
        rows.append(field_row({"label": "Via", "value": c["via"]}))
    back = ""
    if c["images"].get("back"):
        back = f'<figure class="plate back"><img src="{up}cards/{e(d)}/back.webp" alt="Back of {e(c["id"])}, blank card" width="{c["images"]["back_w"]}" height="{c["images"]["back_h"]}"><figcaption>Back. Shown because the card is unused.</figcaption></figure>'
    notes = ""
    if c.get("sender_note"):
        notes += f'<div class="note"><h2>From the sender</h2><blockquote>{e(c["sender_note"])}</blockquote></div>'
    if c.get("tpa_note"):
        notes += f'<div class="note"><h2>Notes</h2><p>{e(c["tpa_note"])}</p></div>'
    newer, older = ("Previous", "Next") if c.get("made") else ("Newer", "Older")
    nav = '<nav class="pager">'
    nav += f'<a href="{up}c/{e(prev_c["id"])}/" rel="prev">{newer}: {e(prev_c["id"])}</a>' if prev_c else "<span></span>"
    nav += f'<a href="{up}c/{e(next_c["id"])}/" rel="next">{older}: {e(next_c["id"])}</a>' if next_c else "<span></span>"
    nav += "</nav>"
    alt = c.get("alt") or c.get("title", "")
    body = f"""<article class="entry">
  <div class="plates">
    <figure class="plate"><img src="{up}cards/{e(d)}/front.webp" alt="{e(alt)}" width="{c['images']['front_w']}" height="{c['images']['front_h']}"></figure>
    {back}
  </div>
  <div class="ledger">
    <p class="no big">{e(c['id'])} <span class="kind">{e(c.get('kind',''))}</span></p>
    <h1>{e(c.get('title',''))}</h1>
    <dl>{''.join(rows)}</dl>
    {notes}
    <p class="legend"><span class="est">est.</span> marks an estimate. Everything unmarked was read directly off the piece.</p>
  </div>
</article>
{nav}"""
    desc = f"{c['id']}: {c.get('title','')}. {c.get('origin',{}).get('value','')}."
    return page(f"{c['id']} - {c.get('title','')} - Post", body, desc=desc, canonical=f"/c/{c['id']}/", depth=2, og_image=f"cards/{d}/front.webp")


def build_about():
    body = f"""<article class="about">
  <h1>Send something</h1>
  {address_block()}
  <div class="prose">
    <p>Postcards, mail art, letters, ephemera. Some of it is art, some of it is a gas-station postcard; it all gets cataloged.</p>
    <p>The archive also keeps the postcards Third Polar Arch prints and sends out, under <a href="../#made">Made here</a>.</p>
    <h2>The deal</h2>
    <p>Nothing is returned, nothing is sent back, and no reply is owed in either direction.</p>
    <p>You keep your copyright. By sending, you give Third Polar Arch a permanent, non-exclusive right to photograph, catalog and show the front of what you sent, and to use those images to promote this archive. The physical piece stays here.</p>
    <p>We choose what gets shown. Not everything goes up. Anything explicit, hateful, or carrying someone's personal information stays off.</p>
    <h2>What gets shown</h2>
    <p>Fronts only. Backs and envelopes are never shown, because that is where addresses and private messages live. The one exception is an unused card with a blank back, where the back is just printer's information.</p>
    <p>If you want your name or a note attached, write it on the piece or tuck in a slip saying so. Otherwise the entry credits the place it came from, not the person.</p>
    <h2>Takedowns</h2>
    <p>Email <a href="mailto:{CONTACT}?subject=Post%20takedown">{CONTACT}</a> with the catalog number and it comes down.</p>
    <h2>How entries are written</h2>
    <p>Each entry sticks to what can be read off the piece or reasonably worked out from it: postmark, stamps, printing method, card stock, publisher marks. Dates are usually estimates from the card type and are marked as such, with the reasoning shown. No interpretation, no mood writing.</p>
  </div>
</article>"""
    return page("Send something - Post", body, canonical="/about/", depth=1)


def main():
    cards = load_cards()
    (ROOT / "index.html").write_text(build_index(cards))
    (ROOT / "about").mkdir(exist_ok=True)
    (ROOT / "about/index.html").write_text(build_about())
    cdir = ROOT / "c"
    live = set()
    for group in ([c for c in cards if not c.get("made")], sorted([c for c in cards if c.get("made")], key=lambda c: c["id"])):
        for i, c in enumerate(group):
            out = cdir / c["id"]
            out.mkdir(parents=True, exist_ok=True)
            (out / "index.html").write_text(build_card(c, group[i - 1] if i > 0 else None, group[i + 1] if i + 1 < len(group) else None))
            live.add(c["id"])
    # remove pages for cards that were taken down
    if cdir.exists():
        for p in cdir.iterdir():
            if p.is_dir() and p.name not in live:
                for f in p.iterdir():
                    f.unlink()
                p.rmdir()
    feed = [{"id": c["id"], "title": c.get("title"), "kind": c.get("kind"), "received": c.get("received"),
             "origin": c.get("origin", {}).get("value"), "url": f"{SITE}/c/{c['id']}/",
             "image": f"{SITE}/cards/{c['_dir']}/front.webp", "made_here": bool(c.get("made"))} for c in cards]
    (ROOT / "feed.json").write_text(json.dumps(feed, indent=1))
    urls = ["/", "/about/"] + [f"/c/{c['id']}/" for c in cards]
    today = datetime.date.today().isoformat()
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    print(f"built {len(cards)} cards")


if __name__ == "__main__":
    main()
