#!/usr/bin/env python3
"""
sendika.org'daki "Türkiye Çalışma Yaşamı Kaynakçası" harf sayfalarını indirir ve
her harf için data/kaynak_metin/NN_HARF.txt (satır başına bir kayıt) üretir.

Kullanım:
    python3 scripts/fetch_sendika.py                 # 30 harfi siteden indir
    python3 scripts/fetch_sendika.py --harf Ç İ Ö    # yalnız belirli harfler
    python3 scripts/fetch_sendika.py --html-dir ./indirilenler   # önceden kaydedilmiş .html dosyalarından

Sonra:  python3 scripts/parse_to_apa.py

Not: Site Next.js ile sunulduğu için içerik <script>self.__next_f.push(...)</script>
blokları içinde gelir; betik bu blokları birleştirip makale HTML'ini çıkarır.
Türkçe harfli sayfaların adresleri sonda sayısal kimlik taşır (…-c-2-6530 gibi);
kimliksiz eski adresler (…-c-2) 404 döndürür.
"""
import argparse, glob, html, json, os, re, sys, time, unicodedata
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "kaynak_metin")
BASE = "https://sendika.org/2006/03/turkiye-calisma-yasami-kaynakcasi-"
PAGES = [("01", "A", "a"), ("02", "B", "b"), ("03", "C", "c"), ("04", "Ç", "c-2-6530"), ("05", "D", "d"),
         ("06", "E", "e"), ("07", "F", "f"), ("08", "G", "g"), ("09", "H", "h"), ("10", "I", "i"),
         ("11", "İ", "i-2-6537"), ("12", "J", "j"), ("13", "K", "k"), ("14", "L", "l"), ("15", "M", "m"),
         ("16", "N", "n"), ("17", "O", "o"), ("18", "Ö", "o-2-6544"), ("19", "P", "p"), ("20", "Q", "q"),
         ("21", "R", "r"), ("22", "S", "s"), ("23", "Ş", "s-2-6549"), ("24", "T", "t-6550"),
         ("25", "U", "u-6551"), ("26", "Ü", "u-2-6552"), ("27", "V", "v"), ("28", "W", "w"),
         ("29", "Y", "y"), ("30", "Z", "z")]
UA = "Mozilla/5.0 (kaynakca-arama; akademik amaçlı)"


def article_html(page_html):
    """Next.js akış verisinden makale gövdesini çıkar; bulunamazsa klasik DOM'a düş."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)</script>', page_html, re.S)
    if chunks:
        s = "".join(json.loads(c) for c in chunks)
        parts = re.split(r"\n[0-9a-f]+:T[0-9a-f]+,", s)
        best = max(parts, key=lambda x: x.count("<br"))
        if best.count("<br") or best.lstrip().startswith("<p>"):
            return best
    m = re.search(r'<div[^>]+class="[^"]*entry-content[^"]*"[^>]*>(.*?)</div>\s*<(?:footer|div class="(?:share|related))',
                  page_html, re.S)
    return m.group(1) if m else ""


def to_lines(art):
    art = art.split("[box type='info']")[0]
    art = re.sub(r"<br\s*/?>", "\n", art)
    art = re.sub(r"</p>", "\n", art)
    art = re.sub(r"<[^>]+>", "", art)
    art = html.unescape(art)
    lines = [re.sub(r"\s+", " ", l).strip() for l in art.split("\n")]
    return [l for l in lines if len(l) > 2]


def is_404(page_html):
    return "404 Sayfa Bulunamadı" in page_html[:5000] or '"404 Sayfa Bulunamadı' in page_html


def fetch(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print(f"   deneme {a + 1}: {e}", file=sys.stderr)
            time.sleep(2 + 2 * a)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harf", nargs="*", help="yalnız bu harfleri işle (ör. Ç İ Ö Ş Ü)")
    ap.add_argument("--html-dir", help="siteden değil, bu klasördeki kayıtlı .html dosyalarından oku")
    ap.add_argument("--bekle", type=float, default=1.5, help="istekler arası saniye (varsayılan 1.5)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    want = {unicodedata.normalize("NFC", h) for h in a.harf} if a.harf else None
    local = {}
    if a.html_dir:
        for f in glob.glob(os.path.join(a.html_dir, "*.html")):
            local[unicodedata.normalize("NFC", os.path.basename(f))] = f
    ok = bad = 0
    for no, harf, slug in PAGES:
        if want and harf not in want:
            continue
        if a.html_dir:
            f = local.get(f"{no}_{harf}.html")
            page = open(f, encoding="utf-8").read() if f else None
            src = f or "(yok)"
        else:
            src = BASE + slug + "/"
            page = fetch(src)
            time.sleep(a.bekle)
        if not page or is_404(page):
            print(f"✗ {harf}: sayfa alınamadı ya da 404 → {src}")
            bad += 1
            continue
        lines = to_lines(article_html(page))
        if not lines:
            print(f"✗ {harf}: içerik bulunamadı → {src}")
            bad += 1
            continue
        path = os.path.join(OUT, f"{no}_{harf}.txt")
        open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print(f"✓ {harf}: {len(lines)} satır → {os.path.relpath(path, ROOT)}")
        ok += 1
    print(f"\n{ok} harf yazıldı, {bad} başarısız.")


if __name__ == "__main__":
    main()
