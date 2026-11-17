# HTML sürüm 3 · Onarım ve doğrulama kaydı

Bu sürüm yalnız HTML uygulamasını ve onun dağıtım paketlerini günceller. Özgün PDF ve ses dosyaları aynı baytlardır.

## Giderilen sorunlar

- Büyük atlasları taşıyan 11 CSS değişkeni kaldırıldı. Chromium'un CSS değişken sınırını aşan bu değerler, resim verileri dosyada bulunsa da görsellerin kullanılamamasına yol açıyordu. 176 resim artık tek tek gömülü PNG ve sıradan img öğesiyle kullanılıyor.
- Ses kütüphanesine ve aktif oynatıcıya görsel/anlam bağlamı eklendi. Her sesli öğenin mevcut ana resim veya açıkça etiketlenen ortak kavram ilişkisi var.
- Panolar eşit bölündüğünde bazı kartlara komşu hücreden ince şerit karışıyordu. Kırpma gerçek ayırıcı çizgilere göre yeniden yapıldı; kaynak çizim içeriği değiştirilmedi.
- 130 kalıbın mevcut öğretim notları, hedefin Türkçe anlamı ve kart içindeki bütün aile/kalıp ses düğmeleri tamamlandı.
- Gizli yanıtta görsel, oynatıcı metni ve erişilebilir adlar birlikte gizleniyor. İpucu açık seçimle veriliyor; kullanılan yardım kayda giriyor.
- Sayfalama odağı, eski hedefin yeniden çalması, belgenin tamamındaki hareket tercihi ve sabit oynatıcı için alt boşluk kuralı düzeltildi.
- Aynı sınavın daha yeni yedeğinin sessizce atlanması, teslim edilmiş yedekteki boşların yerel yanıtlarla doldurulması ve sürenin iki kez sayılması önlendi. İlk teslim ayrı ve sabit tutuluyor.
- Tam kitap notlarında iki farklı metin sessizce birbirinin üzerine yazılmıyor. Çatışan metinler etiketlenerek saklanıyor; tekrar içe aktarma aynı eski metni çoğaltmıyor. Çok uzun birleşimler açık bildirimle uygulanmıyor, mevcut not korunuyor.

## Korunan içerik

Eski HTML'nin normalize edilmiş öğretim metni SHA-256 değeri yeni sürümde aynıdır: `07cd2f2fca4a258245fa38106503dd0739d5e7a93e409d2c14169472de85ddd4`. 176 kart, 180 beş seçenekli soru, açıklamalı çözümler ve 31 SVG şema korunur. Eski kitap içinde 352 yerel img başvurusu vardır: 176 kart ve 176 hafıza panosu hücresi.

915 ek telaffuz kaydı tam tanımlı yeni kelime kartları olarak sayılmaz. 130 kalıp ve beş okuma için kullanılan 135 ortak görsel ilişkisi açıklamalarıyla işaretlidir. Ana kartların her biri kendi özgün görselini kullanır.

## Son dosya üzerinde kontroller

| Denetim | Sonuç |
|---|---:|
| Birleşik kitap/uygulama DOM etkileşim senaryoları | 30/30 |
| Onarıma yönelik kapsamlı DOM/durum test grupları | 14/14 |
| Bağımsız redteam regresyonları | 29/29 |
| Gerçek HTML'den çıkarılan ve kaynakla eşleşen PNG | 176/176 |
| Gerçek HTML'den çıkarılan ve kaynakla eşleşen MP3 | 1537/1537 |
| Gömülü görsellerden piksel eşitliğiyle yeniden kurulan atlas | 11/11 |
| HTML5 SVG ağaçları kaynakla eşdeğer şema | 31/31 |

Test grupları bütün 1.226 ses kartını, bütün aile/kalıp düğmelerini, 130 öğretim notunu ve 176 görsel eşleşmesini dolaşır. Ses kütüphanesi sayısı, edinilmiş yeterlik veya benzersiz kelime sayısı değildir.

Statik görüntü incelemesi: 13 uygulama durumu, 390 ve 1280 piksel genişlikler, açık/koyu tema, kart, ses kütüphanesi, gizli/açılmış yanıt, ortak görsel, okuma, prova ve kitap içi resimler. Çıktılar JavaScript'in oluşturduğu DOM'dan WeasyPrint ile alınmıştır. Bu araç canlı tarayıcı değildir. Kendi form öğesi varsayımları için yalnız denetim katmanında sıfırlama uygulanmış, genişlik medya sorguları denetim genişliğine göre çözülmüştür. Yerel tarayıcı ses denetimleri, kaydırma kapları, CSS dönüşümleri ve bazı modern CSS işlevleri aynı biçimde çizilmediği için ham statik taşma adayları tarayıcı hatası sayılmamıştır.

## Açık doğrulama sınırı

Canlı tarayıcı bu ortamın URL güvenlik politikası nedeniyle kullanılamadı; alternatif yol denenmedi. Gerçek tarayıcıda tüm etkileşimlerin ve duyulabilir sesin gözlendiği iddia edilmez. DOM testlerinde medya işlevleri benzetimdir; gerçek ses baytlarının varlığı ve bütünlüğü ayrı denetlenir. Önceki gerçek ses dosyası çözümleme ve fonem/kaynak incelemelerinin sonuçları korunur; sesler bu sürümde yeniden üretilmedi.

## Başlıca teknik kanıt

- Chromium CSSVariableData: https://chromium.googlesource.com/chromium/src/+/ab30ca95a699b434a885dd6b573a9fe4158caa76/third_party/blink/renderer/core/css/css_variable_data.h
- Chromium CSSVariableParser: https://chromium.googlesource.com/chromium/src/+/480fdcf3cba9c05cb1a50b27ab220a22aaea4311/third_party/blink/renderer/core/css/parser/css_variable_parser.cc
- W3C CSS Variables, §3.3: https://www.w3.org/TR/css-variables/

Tekrar aralıkları öğretim kararıdır; herkes için optimal veya garantili değildir. Otomatik telaffuz puanı, dil düzeyi tanısı ve resmî sınav puanı tahmini yoktur.
