#!/usr/bin/env python3
"""
Türkiye Çalışma Yaşamı Kaynakçası (Koç & Koç, 2004) → APA 7 CSV

Girdi : data/kaynak_metin/*.txt   (her satır bir kaynakça kaydı, harf sayfası başına bir dosya)
Çıktı : data/kaynakca_apa7.csv    (UTF-8 BOM, Excel uyumlu)
        data/kaynakca.json        (arama motoru için)
        data/data.js              (index.html'nin çevrimdışı da çalışması için window.KAYNAKCA)

Kullanım: python3 scripts/parse_to_apa.py
"""
import csv, glob, json, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "kaynak_metin")
OUT = os.path.join(ROOT, "data")
BASE_URL = "https://sendika.org/2006/03/turkiye-calisma-yasami-kaynakcasi-"
SLUG = {"A": "a", "B": "b", "C": "c", "Ç": "c-2-6530", "D": "d", "E": "e", "F": "f", "G": "g", "H": "h",
        "I": "i", "İ": "i-2-6537", "J": "j", "K": "k", "L": "l", "M": "m", "N": "n", "O": "o",
        "Ö": "o-2-6544", "P": "p", "Q": "q", "R": "r", "S": "s", "Ş": "s-2-6549", "T": "t-6550",
        "U": "u-6551", "Ü": "u-2-6552", "V": "v", "W": "w", "Y": "y", "Z": "z"}

UP = "A-ZÇĞİÖŞÜÂÎÛÉÈÄ"
LOW = "a-zçğıöşüâîûéèäß"
INIT_RE = re.compile(rf"^((?:[{UP}](?:[{LOW}]{{1,2}})?\.\s?){{1,4}}|[{UP}](?=\s*-\s|\s*$))"
                     rf"(\s*\((?:ed|eds|der|haz|çev|Ed|Der|Haz)\.?\))?"
                     rf"(\s*(?:v\.d\.|vd\.|ve Diğerleri|ve diğerleri|ve Diğ\.|et al\.))?"
                     rf"(?:\s*-\s*(.+))?$")
YEAR_RE = re.compile(r"^(?:(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+)?"
                     r"((?:1[89]|20)\d\d)(?:\s*[-–/]\s*((?:1[89]|20)?\d\d))?\s*(\(\?\)|\?)?$")
PAGES_RE = re.compile(r"^(\d+)\s*s\.?$")
PUB_RE = re.compile(r"(Yay\b|Yay\.|Yayın|Yayınevi|Mat\.|Matb|Matbaa|Basımevi|Kitabevi|Kitapevi|Kitaplığı|Press|Verlag|"
                    r"Books|Publications|Publishing|Editions|Éditions|Ltd|A\.Ş\.|\bNo\.?\s*\d|Fak\.|Fakültesi|Üniv|"
                    r"SBE|Enstitü|Gn\.\s?Md|Genel Müdürlüğü|Başkanlığı Yay|Bakanlığı Yay|Ofset|Offset|Tesisi|"
                    r"Merkezi Yay|Vakfı Yay|Sendikası Yay|Derneği Yay|DPT[: ]|DİE\b|ILO|UÇB|Ajans|Neşriyat|Neşriyatı)", re.I)
THESIS_RE = re.compile(r"\((Doktora Tezi|Yüksek Lisans Tezi|Bilim Uzmanlığı Tezi|Uzmanlık Tezi|Lisans Tezi|"
                       r"Doçentlik Tezi|Mezuniyet Tezi|Bitirme Tezi|Tez|Lisans Bitirme Tezi|Master Tezi|"
                       r"Seminer Çalışması|Doktora Çalışması|Yayınlanmamış Doktora Tezi|Yayınlanmamış Yüksek Lisans Tezi)\)", re.I)
EDITION_RE = re.compile(r"\(((?:[^()]*?\s)?\d+\.\s*(?:Basım|Baskı|bs\.?)(?:[^()]*)?)\)|\((\d+(?:st|nd|rd|th)\s+ed(?:ition)?\.?)\)", re.I)
NOTE_RE = re.compile(r"\((Çoğaltma|Tarihsiz(?:\s*-\s*[^)]*)?|Teksir|Daktilo|Fotokopi|Broşür|Afiş|Bildiri|Tebliğ|Yayınlanmamış)\)", re.I)
CITY_WORDS = set("""Ankara İstanbul İzmir Bursa Adana Zonguldak Eskişehir Kocaeli İzmit Konya Kayseri Samsun Trabzon Antalya
Mersin Gaziantep Diyarbakır Erzurum Malatya Sivas Karabük Afyon Denizli Manisa Balıkesir Edirne Tekirdağ Çorum Elazığ
Lefkoşa Lefkoşe Mağusa Girne Cenevre Brüksel Köln Bonn Berlin Frankfurt Münih Hamburg Stuttgart Düsseldorf Duisburg
Viyana Paris Londra London Stockholm Stokholm Amsterdam Lahey Leiden Kopenhag Oslo Washington New York Moskova Sofya
Atina Roma Tokyo Tahran Beyrut Kahire Bern Zürih Leipzig Essen Dortmund Hannover Bremen Kassel Mainz Nürnberg
Hollanda Almanya Fransa Belçika İsveç Danimarka Avusturya İsviçre Ereğli Kdz.Ereğli Gölcük Adapazarı Sakarya Sivas
Kırıkkale Batman Aliağa Kırıkkale Iskenderun İskenderun Isparta Uşak Kütahya Soma Bartın Rize Ordu Giresun Van""".split())
MONTHS = "Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık"


def fold(s):
    """Türkçe duyarsız arama anahtarı: küçük harf + aksan kaldırma + ı/i birleştirme."""
    s = s.replace("İ", "i").replace("I", "ı").lower()
    s = s.replace("ı", "i")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip()


def split_top(s):
    """Parantez içini bölmeden virgülle ayır."""
    parts, depth, buf, q = [], 0, "", False
    balanced = s.count('"') % 2 == 0
    for ch in s:
        if ch == '"' and balanced:
            q = not q
        elif ch in "“":
            depth += 1
        elif ch in "”":
            depth = max(0, depth - 1)
        if ch == "," and q:
            buf += ch; continue
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append(buf.strip()); buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf.strip())
    return [p for p in parts if p]


def fmt_initials(ini):
    # "A.F.V." -> "A. F. V." ; "Th." kalır ; "A" -> "A."
    toks = re.findall(rf"[{UP}](?:[{LOW}]{{1,2}})?\.?", ini)
    return " ".join(t if t.endswith(".") else t + "." for t in toks)


def is_single_name(s):
    return bool(re.fullmatch(rf"[{UP}][{LOW}]+(?:-[{UP}]?[{LOW}]+)?", s))


CORP_RE = re.compile(r"Sendika|Dernek|Derneği|Birli|Grubu|Vakf|Kurum|Bakanlı|Müdürlü|Başkanlı|Konfederasyon|Federasyon|"
                     r"Merkez|Enstitü|Üniv|Odası|Partisi|Cemiyet|Kooperatif|Teşkilat|Şube|Öğretmen|Meclis|Komisyon|"
                     r"Büro|Office|Ministry|Organi[sz]ation|Council|Union|Kulüb|Platform|Belediye|Konseyi|Sekreterli")


def parse_authors(segs):
    """Kişi yazar(lar)ı ayrıştır. Dönüş: (authors[list of dict], role, etal, tüketilen segment sayısı) ya da None."""
    if len(segs) < 2:
        return None
    authors, role, etal = [], "", False
    i = 0
    surname = segs[0]
    if len(surname) > 40 or re.search(r"\d", surname) or len(surname.split()) > 3 or CORP_RE.search(surname):
        return None
    # "Aktan, C.C. Değişim ve Devlet" — baş harflerden sonra virgül unutulmuş
    m0 = re.match(rf"^((?:[{UP}]\.){{1,3}}(?:\s*\((?:ed|der|haz)\.?\))?)\s+([{UP}].{{3,}})$", segs[1])
    if m0:
        segs = [segs[0], m0.group(1), m0.group(2)] + segs[2:]
    while True:
        if i + 1 >= len(segs):
            break
        nxt = segs[i + 1]
        m = INIT_RE.match(nxt)
        full_given = None
        if not m:
            # "Cahit, Neriman, ..." — tam ad
            if (not authors and is_single_name(surname) and is_single_name(nxt) and len(segs) >= 4
                    and not YEAR_RE.match(segs[i + 2])):
                full_given = nxt
            else:
                break
        if full_given:
            authors.append({"soyad": surname, "ad": full_given, "apa": f"{surname}, {full_given[0]}."})
            i += 2
            if i < len(segs) and INIT_RE.match(segs[i]) is None and i + 1 < len(segs) and INIT_RE.match(segs[i + 1]) and is_single_name(segs[i].split(" ")[-1]):
                surname = segs[i]; i -= 1; continue
            break
        ini, rl, et, rest = m.group(1), m.group(2), m.group(3), m.group(4)
        # yalnızca harf olan tek segment (örn. "A") başlık olabilir; en az bir nokta ya da tire şartı
        if "." not in ini and not rest:
            break
        authors.append({"soyad": surname.strip(), "ad": ini.strip(), "apa": f"{surname.strip()}, {fmt_initials(ini)}"})
        if rl:
            r = rl.strip("() .").lower()
            role = {"ed": "Ed.", "eds": "Ed.", "der": "Der.", "haz": "Haz.", "çev": "Çev."}.get(r, r)
        if et:
            etal = True
        i += 1
        if rest:
            surname = rest.strip()
            continue
        # "Quataert, D., Zürcher, E.J., ..." — virgülle ikinci yazar
        if (i + 2 < len(segs) and re.fullmatch(rf"[{UP}][{LOW}'’]+(?:[- ][{UP}][{LOW}]+)?", segs[i + 1] or "")
                and INIT_RE.match(segs[i + 2]) and "." in segs[i + 2]):
            surname = segs[i + 1]; i += 1
            continue
        break
    if not authors:
        return None
    return authors, role, etal, i + 1, segs


def apa_authors(authors, role, etal):
    names = [a["apa"] for a in authors]
    if len(names) == 1:
        s = names[0]
    elif len(names) <= 20:
        s = ", ".join(names[:-1]) + ", & " + names[-1]
    else:
        s = ", ".join(names[:19]) + ", . . . " + names[-1]
    if etal:
        s += ", vd."
    if role:
        s += f" ({role})"
    return s


def classify(t):
    tl = t.lower()
    if THESIS_RE.search(t) or re.search(r"\b(doktora|yüksek lisans|lisans|uzmanlık|bitirme|master|mezuniyet|doçentlik|sanatta yeterlik) tezi\b|\(tez\)", tl):
        return "Tez"
    if re.search(r"tüzü|nizamname|yönetmeli|talimatname|statü", tl):
        return "Tüzük / Yönetmelik"
    if re.search(r"\brapor|\breport\b|\bbericht", tl):
        return "Rapor"
    if re.search(r"tutanak|konuşma|genel kurul|kongre|kurultay", tl):
        return "Genel Kurul / Konuşma"
    if re.search(r"\bkanun|\byasa(sı|ları|lar)?\b|\bmevzuat|tüzüğü ve|kararname|içtihat", tl):
        return "Mevzuat"
    if re.search(r"sempozyum|seminer|bildiri|tebliğ|konferans|kongresi|panel", tl):
        return "Bildiri / Seminer"
    if re.search(r"\broman(ı|lar)?\b|\böykü|\bhikaye|\bşiir|\btiyatro|\banı(lar|ları|larım)?\b|\bhatıra", tl):
        return "Edebiyat / Anı"
    return "Kitap / Yayın"


EN = set("the of and in on for to a an labour labor workers trade unions report study turkey turkish with by from".split())
DE = set("der die das und in für von zur zum im türkei türkische arbeiter gewerkschaft bericht".split())
FR = set("le la les des du et en pour sur travail travailleurs turquie syndicats".split())


def lang(t):
    w = re.findall(r"[a-zäöüßéèàçğış]+", t.lower())
    if not w:
        return "tr"
    if re.search(r"[ğışİı]", t):
        return "tr"
    sc = {"en": sum(x in EN for x in w), "de": sum(x in DE for x in w), "fr": sum(x in FR for x in w)}
    best = max(sc, key=sc.get)
    return best if sc[best] >= 2 or (sc[best] >= 1 and len(w) <= 4) else "tr"


def looks_city(s):
    s2 = s.strip()
    if s2 in CITY_WORDS or s2.replace("Kdz. ", "Kdz.") in CITY_WORDS:
        return True
    words = s2.split()
    if 1 <= len(words) <= 3 and all(re.fullmatch(rf"[{UP}][{LOW}.]+", w) for w in words) and not PUB_RE.search(s2):
        return any(w in CITY_WORDS for w in words) or s2 in ("D.C.",)
    return False


def parse(line, harf):
    raw = line.strip()
    body = raw.rstrip(" .")
    rec = {"harf": harf, "ham_kayit": raw}

    notes = [m.group(1).capitalize() for m in NOTE_RE.finditer(body)]
    tarihsiz = any(n.lower().startswith("tarihsiz") for n in notes)
    notes = [n if not n.lower().startswith("tarihsiz") else n for n in notes if n.lower() != "tarihsiz"]
    body_n = NOTE_RE.sub("", body).strip(" ,.")
    body_n = re.sub(r"\s{2,}", " ", body_n)

    segs = split_top(body_n)
    # yazar
    pa = parse_authors(segs)
    if pa:
        authors, role, etal, used, segs = pa
        rec["yazar_turu"] = "Kişi"
        rec["yazar"] = "; ".join(f'{a["soyad"]}, {a["ad"]}' for a in authors) + (" vd." if etal else "") + (f" ({role})" if role else "")
        rec["apa_yazar"] = apa_authors(authors, role, etal)
        rest = segs[used:]
    else:
        rec["yazar_turu"] = "Kurum"
        rec["yazar"] = segs[0] if segs else ""
        rec["apa_yazar"] = rec["yazar"]
        rest = segs[1:]

    # sondan: sayfa, yıl, şehir
    sayfa = ""
    yil, yil_apa = "", ""
    if rest and PAGES_RE.match(rest[-1]):
        sayfa = PAGES_RE.match(rest[-1]).group(1); rest = rest[:-1]
    # yıl: sondan geriye doğru ilk tam eşleşen segment
    yidx = None
    for j in range(len(rest) - 1, max(-1, len(rest) - 4), -1):
        if YEAR_RE.match(rest[j]):
            yidx = j; break
    if yidx is None:
        # "Ankara 1976" / "Temmuz 1970" / "1977(?)" gibi gömülü yıl
        for j in range(len(rest) - 1, max(-1, len(rest) - 3), -1):
            m = re.search(r"((?:1[89]|20)\d\d)\s*(\(\?\))?$", rest[j])
            if m and j > 0 and m.start() > 0 and rest[j][m.start() - 1] == "/":
                yil = m.group(1)
                break
            if m and j > 0:
                yil = m.group(1) + ("?" if m.group(2) else "")
                pre = rest[j][:m.start()].strip(" ,")
                pre = re.sub(rf"\s*({MONTHS})$", "", pre).strip()
                rest = rest[:j] + ([pre] if pre else []) + rest[j + 1:]
                break
    else:
        m = YEAR_RE.match(rest[yidx])
        yil = m.group(1) + (("-" + m.group(2)) if m.group(2) else "") + ("?" if m.group(3) else "")
        rest = rest[:yidx] + rest[yidx + 1:]
    if not sayfa and rest and PAGES_RE.match(rest[-1]):
        sayfa = PAGES_RE.match(rest[-1]).group(1); rest = rest[:-1]

    sehir = ""
    if len(rest) >= 2 and rest[-1] == "D.C.":
        sehir = rest[-2] + ", D.C."; rest = rest[:-2]
    elif len(rest) >= 2 and looks_city(rest[-1]):
        sehir = rest[-1]; rest = rest[:-1]
    elif len(rest) >= 2 and re.fullmatch(rf"[{UP}][{LOW}]+", rest[-1]) and len(rest[-1]) <= 14 and not PUB_RE.search(rest[-1]):
        # tek kelimelik, bilinmeyen yer adı (ör. Nepal, Afyon)
        sehir = rest[-1]; rest = rest[:-1]

    # başlık içinde tekrar eden şehir / yıl / yazar segmentleri
    cleaned = []
    same_author_pub = []
    for k, x in enumerate(rest):
        if k > 0 and YEAR_RE.match(x):
            if not yil:
                yil = YEAR_RE.match(x).group(1)
            continue
        if k > 0 and looks_city(x) and k < len(rest) - 0:
            if not sehir:
                sehir = x
            continue
        if k > 0 and fold(x) == fold(rec["yazar"]):
            same_author_pub.append(x); continue
        cleaned.append(x)
    rest = cleaned

    # tez türü, baskı
    whole = ", ".join(rest)
    tez = ""
    mt = THESIS_RE.search(whole)
    if mt:
        tez = mt.group(1)
    baski = ""
    me = EDITION_RE.search(whole)
    if me:
        baski = (me.group(1) or me.group(2)).strip()

    # başlık / yayıncı ayrımı
    title_parts, pub_parts = [], []
    seen_pub = False
    for k, s in enumerate(rest):
        mt2 = THESIS_RE.search(s)
        if mt2 and s[mt2.end():].strip(" ,"):
            before, after = s[:mt2.start()].strip(" ,"), s[mt2.end():].strip(" ,")
            if before:
                (pub_parts if seen_pub else title_parts).append(EDITION_RE.sub("", before).strip())
            seen_pub = True; pub_parts.append(after); continue
        if mt2:
            b = EDITION_RE.sub("", s[:mt2.start()]).strip(" ,")
            if b:
                (pub_parts if seen_pub else title_parts).append(b)
            seen_pub = True; continue
        s_clean = THESIS_RE.sub("", EDITION_RE.sub("", s)).strip(" ,")
        if not s_clean:
            if tez and title_parts:
                seen_pub = True  # tezden sonra gelen kurum
            continue
        if k == 0:
            title_parts.append(s_clean); continue
        if seen_pub or PUB_RE.search(s_clean) or (tez and THESIS_RE.search(s)):
            seen_pub = True; pub_parts.append(s_clean)
        else:
            title_parts.append(s_clean)
    if title_parts and not pub_parts:
        mq = re.match(r"^(.+?[?!])\s+(.+)$", title_parts[-1])
        if mq and PUB_RE.search(mq.group(2)):
            title_parts[-1] = mq.group(1); pub_parts.append(mq.group(2))
    baslik = ", ".join(title_parts).strip()
    # "Başlık, Altbaşlık" → APA'da "Başlık: Altbaşlık" (yalnız ilk virgül)
    if len(title_parts) > 1:
        baslik_apa = title_parts[0] + ": " + ", ".join(title_parts[1:])
    else:
        baslik_apa = baslik
    yayinci = ", ".join(same_author_pub + pub_parts).strip()

    if tarihsiz and not yil:
        yil_apa = "t.y."
    elif not yil:
        yil_apa = "t.y."
    elif yil.endswith("?"):
        yil_apa = "ca. " + yil[:-1]
    else:
        yil_apa = yil

    # APA 7
    desc = []
    if baski:
        b = re.sub(r"\s*(Basım|Baskı|bs\.?)\s*", " bs. ", baski).strip()
        b = re.sub(r"\s{2,}", " ", b).replace(". bs. ", ". bs., ").rstrip(", ")
        desc_ed = f"({b[0].lower() + b[1:] if b[0].isalpha() else b})"
    else:
        desc_ed = ""
    if tez:
        kurum = yayinci or sehir
        desc.append(f"[{tez[0].upper() + tez[1:].lower()}{', ' + kurum if kurum else ''}]")
    if any(n.lower() == "çoğaltma" for n in notes):
        desc.append("[Çoğaltma]")
    t = baslik_apa.rstrip(".") if baslik_apa else "[Başlıksız]"
    apa = f"{rec['apa_yazar'].rstrip('.')}." if not rec["apa_yazar"].endswith(")") else rec["apa_yazar"] + "."
    apa = apa.replace("..", ".")
    apa += f" ({yil_apa}). "
    t_full = t + (" " + desc_ed if desc_ed else "") + (" " + " ".join(desc) if desc else "")
    apa += t_full + "."
    pub_apa = yayinci
    if re.match(r"^(Yay|Yayın|Yayınları)\b", pub_apa or "", re.I) or fold(pub_apa).startswith(fold(rec["yazar"]) + " ") and False:
        pub_apa = ""
    if pub_apa and fold(pub_apa) == fold(rec["yazar"]):
        pub_apa = ""
    if pub_apa and not tez:
        apa += " " + pub_apa.rstrip(".") + "."
    apa = re.sub(r"\s{2,}", " ", apa).replace("?.", "?").replace("!.", "!")

    rec.update({
        "yil": yil or ("Tarihsiz" if tarihsiz else ""),
        "baslik": baslik,
        "baski": baski,
        "tez_turu": tez,
        "yayinci": yayinci,
        "sehir": sehir,
        "sayfa_sayisi": sayfa,
        "notlar": "; ".join(dict.fromkeys(notes)),
        "tur": classify(raw),
        "dil": lang(baslik),
        "apa7": apa,
        "kaynak_url": BASE_URL + SLUG.get(harf, harf.lower()) + "/",
    })
    return rec


FIELDS = ["id", "harf", "yazar", "yazar_turu", "yil", "baslik", "baski", "tez_turu", "yayinci", "sehir",
          "sayfa_sayisi", "notlar", "tur", "dil", "apa7", "ham_kayit", "kaynak_url"]


def main():
    recs = []
    files = sorted(glob.glob(os.path.join(SRC, "*.txt")))
    for f in files:
        harf = os.path.basename(f).split("_", 1)[1].rsplit(".", 1)[0]
        harf = unicodedata.normalize("NFC", harf)
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line or len(line) <= 2:   # "A", "Ç" gibi harf başlıkları
                continue
            recs.append(parse(line, harf))
    order = "A B C Ç D E F G H I İ J K L M N O Ö P Q R S Ş T U Ü V W X Y Z".split()
    recs.sort(key=lambda r: order.index(r["harf"]) if r["harf"] in order else 99)  # stable: harf içi özgün sıra
    for i, r in enumerate(recs, 1):
        r["id"] = i
    with open(os.path.join(OUT, "kaynakca_apa7.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in recs:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    # arama motoru için kompakt JSON (dizi-dizi)
    keys = ["id", "harf", "yazar", "yazar_turu", "yil", "baslik", "baski", "tez_turu", "yayinci", "sehir",
            "sayfa_sayisi", "notlar", "tur", "dil", "apa7", "ham_kayit"]
    compact = {"alanlar": keys, "kayitlar": [[r.get(k, "") for k in keys] for r in recs],
               "kaynak": "Koç, C., & Koç, Y. (2004). Türkiye çalışma yaşamı kaynakçası. Sendika.Org.",
               "harf_url": {h: BASE_URL + s + "/" for h, s in SLUG.items()}}
    js = json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
    open(os.path.join(OUT, "kaynakca.json"), "w", encoding="utf-8").write(js)
    open(os.path.join(OUT, "data.js"), "w", encoding="utf-8").write("window.KAYNAKCA=" + js + ";\n")
    print(f"{len(recs)} kayıt yazıldı ({len(files)} harf dosyası).")


if __name__ == "__main__":
    main()
