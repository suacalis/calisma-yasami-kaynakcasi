# Türkiye Çalışma Yaşamı Kaynakçası — Arama Motoru

Canan Koç ve Yıldırım Koç'un derlediği **Türkiye Çalışma Yaşamı Kaynakçası**'nın (Ekim 2004; sendika.org'da harf harf yayımlanmıştır) aranabilir ve APA 7 biçimli sürümü. Sendika yayınları, çalışma raporları, tüzükler, mevzuat, tezler, anılar ve işçi edebiyatı gibi on binlerce kaydı kapsar.

## Özellikler

- **Türkçe karakter duyarsız arama.** `isci` yazınca `işçi`, `sendikasi` yazınca `Sendikası` bulunur. Eşleşme kelime başından yapılır.
- **Sorgu sözdizimi**
  - `grev maden`: iki kelimeyi de içeren kayıtlar (VE)
  - `"toplu iş sözleşmesi"`: tam ifade
  - `-tüzük`: bu kelimeyi içerenleri hariç tutar
  - `1960..1970` ya da `1960-1970`: yıl aralığı
  - `"Koç Y"` + alan = *Yazar / kurum*: belirli bir yazar
- **Alan seçimi:** tüm alanlar, yazar/kurum, başlık, yayıncı ya da şehir
- **Filtreler:** harf, yayın türü, yazar türü (kişi/kurum), dil, yalnız çoğaltmalar, yalnız tarihsizler, yıl aralığı. Yıllara göre dağılım grafiği eklidir.
- **Sıralama:** kaynakça sırası, yıl (artan/azalan) ya da başlık
- **APA 7 künyesi:** başlıklar italik gösterilir, tek tıkla kopyalanır. Özgün kayıt ve ayrıştırılmış alanlar her kaydın altında açılabilir.
- **Dışa aktarma** (o anki arama/filtre sonucu):
  - **CSV**, UTF-8 BOM ile (Excel'de Türkçe karakterler bozulmadan açılır)
  - **RIS**: Zotero, Mendeley, EndNote
  - **APA kaynakça (.txt)**: alfabetik sıralı
- **Paylaşılabilir bağlantı:** arama ve filtreler adres çubuğuna yazılır (`#q=grev&tur=Rapor`). Tek bir kayda da bağlantı verilebilir (`#k1234`).
- Açık/koyu tema, mobil uyumlu düzen, `/` tuşuyla arama kutusuna odaklanma

## Dosya yapısı

```
index.html                   Arama motoru (tek dosya, bağımlılıksız)
data/
  data.js                    Arama motorunun yüklediği veri (window.KAYNAKCA); file:// ile de çalışır
  kaynakca.json              Aynı veri, JSON olarak
  kaynakca_apa7.csv          Ana çıktı: APA 7 CSV (UTF-8 BOM)
  kaynak_metin/NN_HARF.txt   Siteden çıkarılmış ham kayıtlar (satır başına bir kayıt)
scripts/
  fetch_sendika.py           sendika.org'dan harf sayfalarını indirip kaynak_metin/ üretir
  parse_to_apa.py            kaynak_metin/ → CSV + JSON + data.js
.nojekyll                    GitHub Pages'in Jekyll işlemesini kapatır
```

### CSV sütunları

| Sütun | Açıklama |
|---|---|
| `id` | Sıra numarası |
| `harf` | Kaynakçadaki harf bölümü |
| `yazar` | Kişi yazar(lar) `Soyad, A.; Soyad, B.` biçiminde ya da kurum adı. Rol varsa eklenir: `(Ed.)`, `(Der.)`, `(Haz.)` |
| `yazar_turu` | `Kişi` / `Kurum` |
| `yil` | Yayın yılı. `1976?` belirsiz yıl; `Tarihsiz` ya da boş değer yıl bilgisi olmadığını gösterir |
| `baslik` | Başlık (alt başlıklar virgülle) |
| `baski` | Baskı bilgisi (ör. `Genişletilmiş 3. Baskı`) |
| `tez_turu` | Doktora Tezi, Yüksek Lisans Tezi vb. |
| `yayinci` | Yayıncı / yayın dizisi / kurum |
| `sehir` | Yayın yeri |
| `sayfa_sayisi` | Toplam sayfa |
| `notlar` | Çoğaltma, Teksir vb. |
| `tur` | Otomatik sınıflama: Kitap / Yayın, Rapor, Tüzük / Yönetmelik, Mevzuat, Genel Kurul / Konuşma, Bildiri / Seminer, Tez, Edebiyat / Anı |
| `dil` | `tr`, `en`, `de`, `fr` (başlıktan tahmin) |
| `apa7` | APA 7 künyesi (düz metin) |
| `ham_kayit` | Kaynakçadaki özgün satır |
| `kaynak_url` | Kaydın bulunduğu sendika.org sayfası |

### APA 7 dönüşüm kuralları

- Kişi yazarlar: `Soyad, A. B.`. İki ve daha fazla yazar `A, B, & C` biçiminde yazılır. `v.d.` ve `ve Diğerleri` ifadeleri `vd.` olur.
- Kurum yazar tam adıyla yazılır. Yayıncı yazarla aynıysa tekrarlanmaz (APA 7, §9.25).
- Tarih: `(1976)`. Belirsiz yıl `(ca. 1976)`, tarihsiz kayıt `(t.y.)` olarak yazılır.
- Başlıktaki ilk virgülden sonrası alt başlık sayılır ve iki noktayla ayrılır: `Başlık: Alt başlık`.
- Baskı: `(3. bs.)`. Tez: `[Doktora tezi, Kurum]`. Çoğaltmalar: `[Çoğaltma]`.
- APA 7'de yer bilgisi ve sayfa sayısı kitap künyesine girmez; bunlar CSV'de ayrı sütunlarda tutulur.

**Uyarı:** Künyeler 10.000'i aşkın serbest biçimli kayıttan kural tabanlı olarak üretilmiştir. Kaynakçanın kendi yazımındaki tutarsızlıklar (eksik virgüller, yarım kalmış satırlar, yazar–başlık sınırının belirsiz olduğu kayıtlar) bazı künyelerde hataya yol açabilir. 

## Kaynak ve haklar

- Kaynakça: Koç, C., & Koç, Y. (2004). *Türkiye çalışma yaşamı kaynakçası*. Sendika.Org. [Sunuş](https://sendika.org/2006/03/turkiye-calisma-yasami-kaynakcasi-sunus/) · [PDF](https://sendika.org/wp-content/uploads/2015/05/1324174914b.pdf)
- Kaynakça metninin hakları derleyicilerine ve Sendika.Org'a aittir. Bu depo, kaynakçayı araştırmacılar için aranabilir kılmak amacıyla hazırlanmış bir erişim aracıdır; kullanırken özgün kaynağa atıf yapınız.
- Kod (`index.html`, `scripts/`) MIT lisanslıdır; bkz. `LICENSE`.
# calisma-yasami-kaynakcasi
