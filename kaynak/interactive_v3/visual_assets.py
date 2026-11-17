#!/usr/bin/env python3
"""Prepare exact-pixel, individually addressable YDS vocabulary illustrations.

The original artwork comprises eleven 4 x 4 PNG atlases.  Earlier HTML put each
complete atlas in a CSS custom property as a multi-megabyte data URL.  Chromium
rejects over-limit custom-property values; all eleven original declarations
exceeded its 2,097,152-character CSSVariableData limit.  Ordinary image sources
also allow the book, vocabulary library, and audio player to use the same image
contract without requiring sprite-position CSS.

This script performs no image generation, retouching, recolouring, resizing, or
creative editing.  It extracts each tile losslessly from the original pixels.
The generated atlas grids are not perfectly uniform: some third-row gutters
are over 20 pixels above the nominal quarter boundary.  Crop boundaries are
therefore found at the actual pale gutter lines near each expected division,
not at equal quarters.  Adjacent crops share an exact boundary, so a
reconstructed board is byte-for-byte identical in decoded pixel data.

Usage:
    python book/interactive_v3/visual_assets.py

Integration contract:
    visuals = embedded_visuals(book_dir / 'visual_catalog_v3.json')
    data['visuals'] = visuals
    item = data['visuals']['items']['V001']
    # <img src=item['src'] alt=item['alt'] width=item['width']
    #      height=item['height'] loading='lazy' decoding='async'>

Do not put the returned data URLs in CSS custom properties.  The generated
catalog uses relative file paths for maintainability; embedded_visuals converts
those paths to ordinary image data URLs for a self-contained HTML deliverable.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


GRID = 4
EXPECTED_CARDS = 176
EXPECTED_ATLASES = 11
CHROMIUM_CUSTOM_PROPERTY_LIMIT = 2_097_152
SOURCE_URLS = [
    'https://chromium.googlesource.com/chromium/src/+'
    '/ab30ca95a699b434a885dd6b573a9fe4158caa76/'
    'third_party/blink/renderer/core/css/css_variable_data.h',
    'https://chromium.googlesource.com/chromium/src/+'
    '/480fdcf3cba9c05cb1a50b27ab220a22aaea4311/'
    'third_party/blink/renderer/core/css/parser/css_variable_parser.cc',
    'https://www.w3.org/TR/css-variables/#long-variables',
]

# These are deliberately named associations, not newly illustrated targets.
# Each link was checked against the actual supplemental example and the
# existing visual_scene.  In particular, P08 uses its budget-share sense;
# C16 explicitly separates statistical significance from effect size.
ASSOCIATION_ROWS = [
    ('P01', 'V032', 'Uygulama', 'Deneyin adım adım yapılması, carry out kalıbının gerçekleştirme anlamını gösterir.'),
    ('P02', 'V009', 'Araştırma', 'İpucunu izleyen büyüteç, look into ile anlatılan konuyu araştırma eylemine bağlanır.'),
    ('P03', 'V012', 'Cevaba ulaşma', 'İpuçlarının son yapboz parçasında birleşmesi, nedenini öğrenme sonucunu hatırlatır.'),
    ('P04', 'V012', 'Çözümleme', 'Bir araya gelen parçalar, mekanizmanın nasıl çalıştığını zihinde çözmeye ipucu olur.'),
    ('P05', 'V137', 'Açıkça gösterme', 'Rehberin belirli nesneyi göstermesi, bir boşluğu veya noktayı açıkça belirtmeye bağlanır.'),
    ('P06', 'V137', 'Açıklama', 'Belirli nesneyi açıkça gösteren rehber, örnekteki soruyu ortaya koyma anlamını hatırlatır; bu örnekte yolculuk anlatılmaz.'),
    ('P07', 'V083', 'Kaynak kullanma', 'Kullanılabilir araç ve malzemeler, draw on ile bir bilgi kaynağından yararlanmayı çağrıştırır.'),
    ('P08', 'V166', 'Bütçedeki pay', 'Sepetlere ayrılan farklı miktarlar, bütçenin paylara ayrılmasını hatırlatır; bu örnekte account for neden açıklamaz, pay oluşturur.'),
    ('P09', 'V015', 'Gönderim', 'Levhanın belirli bir nesneye yönelmesi, zamirin daha önceki bir ifadeye gönderimde bulunmasına ipucudur.'),
    ('P10', 'V019', 'Simge ve anlam', 'Haritadaki hava simgesi bir durumu temsil eder; aynı ilişki R harfinin retention yerine kullanılmasında vardır.'),
    ('P11', 'V128', 'Önceki temel', 'Yapının desteklenen temeli, yeni açıklamanın önceki ayrım üzerine kurulmasını çağrıştırır.'),
    ('P12', 'V009', 'Araştırmayı sürdürme', 'Devam eden ipucu izi, ilk bulguların ardından ek görüşmelerle incelemeyi sürdürmeyi hatırlatır.'),
    ('P13', 'V048', 'Değişim yaratma', 'Kolu çevirince çarkın harekete geçmesi, bir değişikliğin sonuç doğurmasını gösterir.'),
    ('P14', 'V042', 'Ortaya çıkma', 'Duvar açılınca beliren yeni sorun, belirsiz yönergelerin yeni yorumlara yol açmasına bağlanır.'),
    ('P15', 'V046', 'Sonuca varma', 'Bir yere varan yol, bir olayın ardından gelen sonucu hatırlatır.'),
    ('P16', 'V043', 'Kaynağa dönme', 'Dallardan köke doğru iz sürmek, sonucun hangi nedenden kaynaklandığını bulmaya ipucudur.'),
    ('P17', 'V046', 'Sonuç doğurma', 'Yolun sonunda ulaşılan yer, result in sonrasında verilen sonucu hatırlatır.'),
    ('P18', 'V043', 'Köken', 'Gövde ve kökler, stem from kalıbının kaynaklanma anlamıyla aynı hafıza sahnesini paylaşır.'),
    ('P19', 'V123', 'Konuyu dile getirme', 'Konuşmacı sahnesi, tartışmada bir konuyu gündeme getirmeye ipucudur; bring up tek başına iddiayı kesin savunmak demek değildir.'),
    ('P20', 'V162', 'Azaltma', 'Kısaltılan kurdele, gereksiz ambalajın miktarını azaltmayı hatırlatır.'),
    ('P21', 'V063', 'Aşamalı sonlandırma', 'Duran pompa son durumu gösterir; phase out bu sona birden değil aşamalarla ulaşmayı anlatır.'),
    ('P22', 'V062', 'Devam etme', 'Fırtınaya rağmen büyüyen bitki, kesintilere rağmen çalışmayı sürdürmeye ipucudur.'),
    ('P23', 'V050', 'İlerlemenin engellenmesi', 'Engeller arasında zorlanan koşucu, kaynak yetersizliğinin ilerlemeyi yavaşlatmasını hatırlatır.'),
    ('P24', 'V165', 'Bütün ve parçalar', 'Sepetteki ayrı meyveler, bir bütünü bileşenlerine ayırmayı çağrıştırır; örnek cümlede makinenin bozulması anlamı kullanılmaz.'),
    ('P25', 'V088', 'Tüketme', 'Boşalan depo, kalan kaynağın kullanılarak tüketilmesini hatırlatır.'),
    ('P26', 'V081', 'Kaynağın bitmesi', 'Boş depo ve kovalar, kullanılacak kaynağın kalmamasına ipucudur; scarce kıtlığı, run out of tükenmeyi vurgular.'),
    ('P27', 'V165', 'Bütünü oluşturma', 'Farklı meyvelerin bir sepetin içeriğini oluşturması, küçük çiftliklerin işletmelerin çoğunu oluşturmasına bağlanır.'),
    ('P28', 'V165', 'İçerik', 'Meyve sepetinin bileşenleri, koleksiyonun hangi ayrı arşivlerden oluştuğunu hatırlatır.'),
    ('P29', 'V128', 'Dayanma', 'Yapıyı ayakta tutan destek, bir işin tedarikçilere dayanması için ortak ipucudur.'),
    ('P30', 'V155', 'Koşula bağlılık', 'Kapının uygun anahtara bağlı açılması, erişimin belgenin durumuna bağlı olmasını hatırlatır.'),
    ('P31', 'V110', 'Düzenlemede öngörme', 'Ortak kuralları belirleyen kurul, anlaşmada yıllık incelemelerin öngörülmesine ipucudur; örnekte geçim sağlama anlamı yoktur.'),
    ('P32', 'V039', 'Ayırıp saklama', 'Elekten ayrılan ve elde tutulan taşlar, ileride kullanılacak parayı ayırma fikrine bağlanır.'),
    ('P33', 'V149', 'Yer kaplama', 'Masanın büyük bölümünü kaplayan kitaplar, dolapların odada yer kaplamasını hatırlatır.'),
    ('P34', 'V028', 'Ele alınan konu', 'Uygun yapboz parçası, bir bölümün ilgili konuyu ele alması için ortak ipucudur; deal with bağlama göre başa çıkmak da olabilir.'),
    ('P35', 'V176', 'Sorumluluğu devralma', 'Atölyeleri denetleyen kişi, bakım işinin sorumluluğunu üstlenmeye bağlanır; görüntü yalnız yeni sorumluluğa ipucudur.'),
    ('P36', 'V146', 'Eksikliği dengeleme', 'Farklı ağırlıkların teraziyi dengelemesi, bir eksikliği başka bir katkıyla telafi etmeyi hatırlatır.'),
    ('P37', 'V054', 'Bağlantının kesilmesi', 'Yolu tamamen kapatan engel, köye erişimin kesilmesine ortak ipucudur.'),
    ('P38', 'V160', 'Olasılığı eleme', 'Dedektifin imkânsız seçeneği çıkarması, rule out ile olasılığı eleme anlamını gösterir.'),
    ('P39', 'V128', 'Destekleme', 'Yapının temelini desteklemek, bir iddiayı kanıtla desteklemeyi çağrıştırır.'),
    ('P40', 'V129', 'Kabul etmeme', 'Karşıt yönde çekilen kapı, öneriye olumsuz cevap vermeye ipucudur; turn down burada reddetmektir.'),
    ('P41', 'V122', 'Öneri ileri sürme', 'Henüz doğrulanmamış düşünceyi dile getiren kişi, bir açıklamayı değerlendirmeye sunmayı hatırlatır.'),
    ('P42', 'V140', 'Çözüm bulma', 'Araçlarıyla yapılabilir çözüm kuran usta, grubun uygulanabilir bir çözüm üretmesine ipucudur.'),
    ('P43', 'V168', 'Gerektirme', 'Köprüdeki çatlağın incelemeyi gerektirmesi, call for further examination kalıbıyla aynı ilişkiyi taşır.'),
    ('P44', 'V127', 'Sorgulama', 'Sağlam sanılan köprünün sorgulanması, bir sonucun güvenilirliğini sorgulamaya ipucudur.'),
    ('P45', 'V161', 'İstekle bekleme', 'Kitaplığa isteyerek yönelen kişi, beklenen şeye duyulan isteği hatırlatır; look forward to gelecekteki bir olaya olumlu beklenti taşır.'),
    ('P46', 'V170', 'Katlanma', 'Yağmur ve rüzgâra dayanan kule, rahatsız edici bir duruma katlanmayı çağrıştırır.'),
    ('P47', 'V106', 'Talebe yetişme', 'Bekleyen müşteriler, personelin artan talebin hızına yetişip yetişememesini hatırlatır.'),
    ('P48', 'V080', 'Tesadüfen karşılaşma', 'Virajda beklenmedik geyikle karşılaşmak, bilinmeyen mektuba rastlamayla aynı sürpriz ipucunu paylaşır.'),
    ('P49', 'V164', 'Açığa çıkarma', 'Saklı resmin ortaya çıkarılması, gözden kaçan varsayımların görünür hâle gelmesini hatırlatır.'),
    ('P50', 'V015', 'İşaret etme', 'Levhanın bir yöne işaret etmesi, kayıtların belirli bir tarihe işaret etmesine bağlanır.'),
    ('C01', 'V009', 'Araştırma yürütme', 'İpuçlarını sistemli biçimde izleyen araştırmacı, araştırma yürütmeye ortak ipucudur.'),
    ('C02', 'V013', 'Veri edinme', 'Raftan alınan dosya, arşivlerden veri toplamayı çağrıştırır.'),
    ('C03', 'V001', 'Kanıt sunma', 'İncelenebilen ayak izleri, iddiayı destekleyen kanıtın somut ipucudur.'),
    ('C04', 'V004', 'Sonuç çıkarma', 'Islak şemsiyeden yağmur sonucu çıkarılması, verilenden sonuca ilerlemeyi gösterir.'),
    ('C05', 'V021', 'Sınanacak açıklama', 'Henüz denenmemiş tohum beklentisi hipoteze ipucudur; test a hypothesis bunun sınanmasını anlatır.'),
    ('C06', 'V002', 'Etkiyi değerlendirme', 'Köprüyü ölçütlerle tartan mühendis, değerlendirmenin dayandığı ölçütleri hatırlatır.'),
    ('C07', 'V114', 'Onay alma', 'Geçişe izin veren görevli, izin ve onay kavramına ipucudur; araştırmadaki consent bilgilendirilmiş onam bağlamına göre değerlendirilir.'),
    ('C08', 'V032', 'Deney yapma', 'Deneyi adım adım uygulayan görevli, conduct an experiment kalıbını doğrudan çağrıştırır.'),
    ('C09', 'V024', 'Örneklem', 'Kazandan alınan kaşık örneklem fikrini gösterir; örneklemin temsil edici olması ayrıca değerlendirilir.'),
    ('C10', 'V008', 'Güvenilirlik', 'Aynı saati gösteren saatler tutarlılık ipucudur; reliable source için kaynağın niteliği de incelenir.'),
    ('C11', 'V001', 'Gözleme dayanan kanıt', 'Gözlenebilen ayak izleri, yalnızca hoş bir açıklamadan farklı olarak incelenebilir kanıtı hatırlatır.'),
    ('C12', 'V128', 'Çerçevenin desteği', 'Yapının taşıyıcı desteği, değişken seçimine yön veren kuramsal çerçeve için bir benzetmedir.'),
    ('C13', 'V006', 'Alttaki varsayım', 'Halının altını görmeden basmak, gerekçenin dayandığı sorgulanmamış varsayımı hatırlatır.'),
    ('C14', 'V031', 'Açıklama', 'Kırık saksıyı açıklayan izler bir açıklamaya ipucudur; alternative explanation farklı bir açıklamanın da mümkün olduğunu söyler.'),
    ('C15', 'V030', 'İlk ve geçici bulgu', 'Silinebilir taslak, ilk bulguların yeniden incelenebileceğini hatırlatır.'),
    ('C16', 'V029', 'Anlamlılık ayrımı', 'Bu görsel yalnız significant sözcüğünü çağrıştırır; istatistiksel anlamlılık büyük etki demek değildir. Örnekteki but small bu ayrımı korur.'),
    ('C17', 'V036', 'İlişki ve neden', 'Birlikte büyüyen bitkiler arasındaki neden okunun yokluğu, ilişkinin tek başına nedensellik kurmadığını hatırlatır.'),
    ('C18', 'V026', 'Uyum ve tutarlılık', 'Aynı yaprak desenleri, bulgunun bir açıklamayla tutarlı olmasını çağrıştırır; tek açıklamayı kanıtlamaz.'),
    ('C19', 'V001', 'Kanıt ışığında', 'Dedektifin kanıtı incelemesi, iddianın yeni kanıt dikkate alınarak değiştirilmesine ipucudur.'),
    ('C20', 'V018', 'Belirli ölçüde', 'Ölçü şeridi, anlaşmanın tümüyle değil belirli bir dereceye kadar olmasını hatırlatır.'),
    ('C21', 'V069', 'Büyük değişim', 'Tırtıldan kelebeğe dönüşüm, substantial change için belirgin değişim ipucudur.'),
    ('C22', 'V064', 'Azalma', 'Sırayla küçülen bitkiler, miktarın zaman içinde azalmasını hatırlatır.'),
    ('C23', 'V106', 'Talep artışı', 'Bekleyen müşteriler örnekteki talebe ipucudur; sharp increase artışın keskinliğini bildirir, resim tek başına değişim hızını ölçmez.'),
    ('C24', 'V141', 'Zararlı etki', 'Bitkiye zarar veren tuz, adverse effects kalıbındaki olumsuz sonucu hatırlatır.'),
    ('C25', 'V096', 'Tehdit', 'Korunmasız fideye yaklaşan keçi, olası zararın oluşturduğu tehdidi gösterir.'),
    ('C26', 'V056', 'Riski azaltma', 'Kum torbaları zararı hafifletmeye ipucudur; mitigate riski tamamen ortadan kaldırmayı zorunlu kılmaz.'),
    ('C27', 'V055', 'Yükü hafifletme', 'Çantadan çıkarılan taşlar, ek personelin baskıyı azaltmasını hatırlatır.'),
    ('C28', 'V057', 'Gerginliği artırma', 'Yellenince büyüyen ateş, zaten bulunan sorunun ağırlaşmasına ipucudur.'),
    ('C29', 'V049', 'Erişimi kolaylaştırma', 'Arabanın basamakları rampayla aşması, erişimi kolaylaştırmanın somut örneğidir.'),
    ('C30', 'V050', 'İlerlemeyi güçleştirme', 'Koşucunun önündeki engeller, ilerlemeyi yavaşlatan eksik kayıtları hatırlatır.'),
    ('C31', 'V078', 'Kısıtlama getirme', 'Yola zorunlu engel koyan görevli, başkalarına kısıtlama getirme fikrini gösterir.'),
    ('C32', 'V077', 'Politikayı uygulama', 'Modelin gerçek köprüye dönüşmesi, kararın uygulamaya geçirilmesine ipucudur.'),
    ('C33', 'V069', 'Dönüşüm geçirme', 'Tırtılın kelebeğe dönüşmesi, dönüşümden geçen özneye ipucudur.'),
    ('C34', 'V067', 'Değişime uyum', 'Mevsime uygun kürk geliştiren tilki, değişen koşullara uyum sağlamayı gösterir.'),
    ('C35', 'V073', 'Düzeyi koruma', 'Bisikleti düzenli bakımla çalışır tutmak, standartların sürekliliğine ipucudur.'),
    ('C36', 'V061', 'Büyümeyi sürdürme', 'Ağır meyveli dalı ayakta tutan destek, büyümenin sürdürülebilmesi için gereken desteği hatırlatır.'),
    ('C37', 'V074', 'Bütünlüğü koruma', 'Koruyucu cam içindeki el yazması, bir yapının veya kaydın bütünlüğünü korumaya ipucudur.'),
    ('C38', 'V075', 'Engeli aşma', 'Dağcının duvarın üstüne çıkması, güçlüğü aşarak ilerlemeyi gösterir.'),
    ('C39', 'V046', 'Sonuçları olma', 'Yolun ulaştığı yer, bir bulgunun sonraki tasarım kararları için sonuçlar taşımasını hatırlatır.'),
    ('C40', 'V002', 'Dikkate alma', 'Mühendisin değerlendirme kartları, karar verirken ilgili ölçütleri hesaba katmayı çağrıştırır.'),
    ('C41', 'V084', 'Kaynak ayırma', 'Projelere ayrılan malzemeler, kaynakların amaçlara göre paylaştırılmasını gösterir.'),
    ('C42', 'V081', 'Kısıtlı bulunabilirlik', 'Neredeyse boş depo, ihtiyaç duyulan kaynağın kolay bulunamamasını hatırlatır.'),
    ('C43', 'V106', 'Artan talep', 'Tezgâh önünde bekleyenler, tedarikçiye yönelen talep baskısına ipucudur.'),
    ('C44', 'V102', 'Gereklilikleri karşılama', 'Makinenin çalışması için gereken pil, gereken koşulların karşılanması gerektiğini hatırlatır.'),
    ('C45', 'V101', 'Erişim kazanma', 'Açık kapı ve rampa, kayıtlara ulaşabilmenin somut ipucudur.'),
    ('C46', 'V103', 'Yardım sağlama', 'Ziyaretçiye sunulan battaniye, ihtiyaç duyana yardım sağlamayı gösterir.'),
    ('C47', 'V087', 'Tasarruf', 'Damlayan musluğun kapatılması su tasarrufudur; aynı koruma fikri enerji için kullanılır.'),
    ('C48', 'V088', 'Rezervi tüketme', 'Boşalan kömür deposu, ayrılmış kaynakların tüketilmesini hatırlatır.'),
    ('C49', 'V089', 'Yeniden doldurma', 'Boşalan bardağın doldurulması, azalan malzemeleri yeniden tamamlama fikrini gösterir.'),
    ('C50', 'V092', 'Yaşam alanı', 'Kunduzun yaşadığı çevre habitat için ipucudur; habitat loss bu yaşam alanının kaybını anlatır.'),
    ('C51', 'V090', 'Yenilenebilir kaynak', 'Güneş ve rüzgârla tekrar çalışan pompa, yenilenebilir kaynakları çağrıştırır.'),
    ('C52', 'V096', 'Zarara açıklık', 'Çitsiz fide, bir tehdide karşı savunmasız olmayı gösterir.'),
    ('C53', 'V098', 'Bir grupta yaygınlık', 'Ağaçların çoğundaki aynı leke, bir özelliğin belirli grupta yaygın olmasına ipucudur.'),
    ('C54', 'V166', 'Eşit olmayan dağılım', 'Sepetlerdeki farklı elma miktarları, unequal distribution kalıbını doğrudan canlandırır.'),
    ('C55', 'V108', 'Yük getirme', 'Aşırı dolu çanta, bir düzenlemenin kişiye veya kuruma ek yük getirmesine ipucudur.'),
    ('C56', 'V109', 'Toplumsal refah', 'Farklı yaşlardan kişilerin bakımını sağlayan topluluk, social welfare kavramına ipucudur.'),
    ('C57', 'V111', 'Kurala uyma', 'Belirlenen şeritte giden bisikletli, düzenlemelere uymayı gösterir.'),
    ('C58', 'V116', 'Katılma', 'Ağaç diken gruba katılan kişi, sürece katılımı canlandırır.'),
    ('C59', 'V117', 'Karşılıklı iş birliği', 'Ağır kirişi birlikte kaldıran iki kişi, mutual cooperation için ortak çabayı gösterir.'),
    ('C60', 'V061', 'Sürdürülebilirlik', 'Meyveli dalın desteklenmesi süreklilik ipucudur; sürdürülebilir kalkınma yalnız hızlı büyüme anlamına gelmez.'),
    ('C61', 'V132', 'İkna edici kanıt', 'Birbirini tamamlayan güçlü ipuçları, kanıtın ikna ediciliğini hatırlatır.'),
    ('C62', 'V131', 'Akla yatkın açıklama', 'İzlerin olası ziyaretçiyi düşündürmesi, kesinleşmemiş ama makul açıklamaya ipucudur.'),
    ('C63', 'V030', 'Geçici sonuç', 'Silinebilir köprü taslağı, yeni bilgiyle değişebilecek geçici sonucu hatırlatır.'),
    ('C64', 'V121', 'Sınırları kabul etme', 'Kendi heykelindeki çatlağı kabul eden kişi, çalışmanın sınırlarını açıkça belirtmeye ipucudur.'),
    ('C65', 'V127', 'Kaygı uyandırma', 'Köprünün zayıflığının fark edilmesi, eksik bir kaydın güvenilirlik kaygısı uyandırmasına bağlanır.'),
    ('C66', 'V127', 'Varsayımı sorgulama', 'Sağlam kabul edilen köprüyü sorgulamak, yerleşmiş varsayımlara itiraz etmeyi hatırlatır.'),
    ('C67', 'V125', 'Kararı gerekçelendirme', 'Ustanın seçtiği kirişi nedenleriyle göstermesi, bir kararı dayanaklarıyla açıklamaya ipucudur.'),
    ('C68', 'V126', 'İddiayı çürütme', 'Suyun dibine batan taş, yanlış iddianın karşı kanıtla çürütülmesini gösterir.'),
    ('C69', 'V130', 'Reformu savunma', 'Ağacın korunmasını savunan kişi, bir değişiklik talebini desteklemeye ortak ipucudur.'),
    ('C70', 'V127', 'Çekince bildirme', 'Köprünün sağlamlığını sorgulayan kişi, yorum hakkında çekince belirtmeye ipucudur; çekince tam reddetme zorunluluğu taşımaz.'),
    ('C71', 'V145', 'Belirgin çeşitlilik', 'Farklı meyveler, bölgeler arasındaki çeşitliliği çağrıştırır; variation mutlaka zaman içindeki dalgalanma değildir.'),
    ('C72', 'V134', 'Küçük iyileşme', 'Sepete eklenen tek çakılın yarattığı küçük fark, marginal improvement için miktar ipucudur.'),
    ('C73', 'V171', 'İhmal edilebilir etki', 'Teraziyi neredeyse etkilemeyen kum tanesi, negligible effect kalıbını canlandırır.'),
    ('C74', 'V147', 'Yeterli kanıt', 'Saksıya yetecek su miktarı, bir iddia için yeterli dayanak bulunması fikrine ipucudur.'),
    ('C75', 'V148', 'Yeterli açıklama', 'Temel ihtiyacı karşılayan çatı, açıklamanın gereken düzeyi karşılamasını hatırlatır.'),
    ('C76', 'V158', 'Koşula bakmaksızın', 'Hava değişse de yürüyen kişi, regardless of kalıbının belirtilen koşulu dışarıda tutmasını gösterir.'),
    ('C77', 'V152', 'Karşıtlık', 'Yan yana farklı bahçeler, iki yöntemin karşılaştırmalı karşıtlığına ipucudur.'),
    ('C78', 'V144', 'Kavramları ayırma', 'Dairelerden ayrılan üçgen, hatırlama ve tanıma gibi iki kavramın ayrılmasına ortak ipucudur.'),
    ('C79', 'V125', 'Gerekçe', 'Yapısal tercihinin nedenini gösteren usta, kararın hangi gerekçeye dayandığını hatırlatır.'),
    ('C80', 'V018', 'Derece ve sınır', 'Ölçü şeridi, yöntemin ancak belirli bir ölçüde yararlı olduğu anlamını çağrıştırır.'),
    ('R01', 'V074', 'Arşivi koruma', 'Korunan el yazması, metindeki arşiv belgelerine bağlanır; belgeleri korumak her ayrıntıyı doğrulamakla aynı işlem değildir.'),
    ('R02', 'V036', 'Nedensellik sınırı', 'Birlikte değişen bitkiler arasındaki neden okunun yokluğu, su tüketimindeki azalmanın nedenini ayırma sorununu hatırlatır.'),
    ('R03', 'V083', 'Paylaşılan kaynak', 'Araç, su ve tohumlar, kooperatifin ortak deposundaki kaynaklara ipucudur.'),
    ('R04', 'V101', 'Erişim ve kullanım', 'Açık kapı ve rampa erişim benzetmesidir; metin, bir siteye girebilmenin onu etkili kullanabilmekten farklı olduğunu açıklar.'),
    ('R05', 'V001', 'Kanıt ve sınırlar', 'Kanıtı inceleyen dedektif, metindeki kararları eldeki kanıt ve sınırlarla orantılı kurma temasına ipucudur.'),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_data_url(data: bytes) -> str:
    return 'data:image/png;base64,' + base64.b64encode(data).decode('ascii')


def gutter_boundaries(source: Image.Image) -> tuple[list[int], list[int], dict[str, Any]]:
    """Locate each original board's real pale separators deterministically.

    Find the near-white line with the highest cross-board coverage within 65
    pixels of each expected division.  If several pixels are within 0.005 of
    that maximum, choose their central candidate.  A fail-closed 90% coverage
    threshold and 24-pixel maximum candidate spread prevent silent guesses.
    The warmer paper on atlas 10 needs a 235/255 pale threshold; every chosen
    line and score is written to the catalog for independent verification.
    """
    pixels = np.asarray(source.convert('RGB'))
    minimum = pixels.min(axis=2)
    maximum = pixels.max(axis=2)
    pale = (minimum >= 235) & ((maximum - minimum) <= 20)
    result: dict[str, list[int]] = {}
    audit: dict[str, Any] = {}
    for axis, label, dimension in ((0, 'x', source.width), (1, 'y', source.height)):
        coverage = pale.mean(axis=axis)
        bounds = [0]
        measurements = []
        for division in (1, 2, 3):
            nominal = division * dimension / GRID
            lo, hi = max(1, int(nominal - 65)), min(dimension - 1, int(nominal + 65))
            best_coverage = float(coverage[lo:hi].max())
            candidates = np.flatnonzero(coverage[lo:hi] >= best_coverage - 0.005) + lo
            if best_coverage < 0.9 or int(candidates[-1] - candidates[0]) > 24:
                raise ValueError(f'Ambiguous source gutter: {label} division {division}')
            cut = int(candidates[len(candidates) // 2])
            bounds.append(cut)
            measurements.append({
                'nominal_equal_quarter': nominal,
                'actual_gutter_boundary': cut,
                'pale_line_coverage': float(coverage[cut]),
                'near_maximum_candidates': [int(value) for value in candidates],
            })
        bounds.append(dimension)
        result[label] = bounds
        audit[label] = measurements
    return result['x'], result['y'], audit


def contact_sheet(book_dir: Path, items: dict[str, Any]) -> str:
    """Make a labelled QA-only sheet, retaining native-size pixels in its tiles.

    The sheet samples all eleven boards, including their first/last rows.  It
    is not used as a learning image, and the original tile assets are untouched.
    """
    sample_numbers = [1, 16, 17, 33, 42, 49, 65, 81, 97, 113, 129, 145, 151, 161, 170, 176]
    heading_height = 32
    cell_width = max(item['width'] for item in items.values())
    cell_height = max(item['height'] for item in items.values()) + heading_height + 4
    sheet = Image.new('RGB', (4 * cell_width, 4 * cell_height), '#edf0f2')
    draw = ImageDraw.Draw(sheet)
    font_path = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    font = ImageFont.truetype(str(font_path), 18) if font_path.exists() else ImageFont.load_default()
    for sample_index, number in enumerate(sample_numbers):
        card_id = f'V{number:03d}'
        item = items[card_id]
        row, column = divmod(sample_index, 4)
        x, y = column * cell_width, row * cell_height
        draw.text((x + 8, y + 5), f'{card_id} · {item["word"]}', fill='#172d36', font=font)
        with Image.open(book_dir / item['src']) as tile:
            sheet.paste(tile, (x + (cell_width - tile.width) // 2, y + heading_height))
    output_path = book_dir / 'assets_v3' / '_visual_qa_contact_sheet.png'
    sheet.save(output_path, format='PNG', optimize=True)
    return output_path.relative_to(book_dir).as_posix()


def embedded_visuals(catalog_path: Path | str, *, published_images: Path | None = None) -> dict[str, Any]:
    """Read the validated catalog and embed original tile PNGs once in JSON.

    Both file bytes and decoded dimensions are validated before embedding.
    This helper intentionally excludes validation/source metadata from the
    runtime object, keeping the public app contract small and stable.
    """
    catalog_path = Path(catalog_path).resolve()
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    image_root = published_images.resolve() if published_images else catalog_path.parent
    items: dict[str, Any] = {}
    for card_id, item in catalog['items'].items():
        image_source = f'{card_id}.png' if published_images else item['src']
        path = (image_root / image_source).resolve()
        if not path.is_relative_to(image_root):
            raise ValueError(f'Asset escapes the book directory: {card_id}')
        raw = path.read_bytes()
        if sha256(raw) != item['sha256']:
            raise ValueError(f'Asset checksum mismatch: {card_id}')
        with Image.open(path) as image:
            if image.size != (item['width'], item['height']):
                raise ValueError(f'Asset dimensions mismatch: {card_id}')
            image.load()
        items[card_id] = {
            key: item[key]
            for key in ('id', 'word', 'alt', 'width', 'height')
        }
        items[card_id]['src'] = png_data_url(raw)
    return {
        'version': catalog['version'],
        'kind': 'lossless-original-vocabulary-illustrations',
        'count': len(items),
        'items': items,
        'associations': catalog.get('associations', {}),
    }


def prepare(book_dir: Path) -> dict[str, Any]:
    book_dir = book_dir.resolve()
    vocab_path = book_dir / 'vocabulary.json'
    vocabulary = json.loads(vocab_path.read_text(encoding='utf-8'))
    expected_ids = [f'V{i:03d}' for i in range(1, EXPECTED_CARDS + 1)]
    actual_ids = [item.get('id') for item in vocabulary]
    if actual_ids != expected_ids:
        raise ValueError('Vocabulary order must be exactly V001 through V176.')
    for item in vocabulary:
        if not str(item.get('visual_scene', '')).strip():
            raise ValueError(f'Missing semantic alt text for {item["id"]}')

    output_dir = book_dir / 'assets_v3'
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog: dict[str, Any] = {
        'version': '3.0',
        'kind': 'lossless-original-vocabulary-illustrations',
        'method': {
            'source_artwork': 'Existing original 4-by-4 atlas PNGs; unchanged.',
            'mapping': 'V(n) uses atlas floor((n-1)/16)+1, row floor(((n-1)%16)/4), column (n-1)%4.',
            'boundaries': 'Actual pale gutter lines nearest nominal quarter divisions; no pixel gaps or overlaps.',
            'gutter_detection': 'Pale=min(R,G,B)>=235 and max(R,G,B)-min(R,G,B)<=20; highest coverage within +/-65px of nominal division; choose central candidate within 0.005 of best coverage; require >=90% coverage and <=24px candidate spread.',
            'encoding': 'Lossless PNG; decoded pixel values are preserved exactly.',
            'runtime': 'Ordinary HTML img element with direct embedded PNG data URL.',
        },
        'diagnosis': {
            'failed_mechanism': 'Entire atlas PNG data URLs stored in CSS custom properties.',
            'chromium_custom_property_limit': CHROMIUM_CUSTOM_PROPERTY_LIMIT,
            'source_urls': SOURCE_URLS,
            'independent_ui_omission': 'The earlier audio library and audio dock did not insert vocabulary image elements.',
        },
        'vocabulary_sha256': sha256(vocab_path.read_bytes()),
        'sources': [],
        'items': {},
    }
    total_bytes = 0
    max_data_url_characters = 0
    reconstruct_passes = 0
    pixel_match_passes = 0

    for atlas_index in range(1, EXPECTED_ATLASES + 1):
        source_path = book_dir / 'assets' / f'atlas_{atlas_index:02d}.png'
        source_bytes = source_path.read_bytes()
        source_hash = sha256(source_bytes)
        with Image.open(source_path) as loaded:
            loaded.load()
            source = loaded.copy()
        width, height = source.size
        x_bounds, y_bounds, gutter_audit = gutter_boundaries(source)
        reconstructed = Image.new(source.mode, source.size)
        original_data_url_characters = len(png_data_url(source_bytes))
        source_record = {
            'src': source_path.relative_to(book_dir).as_posix(),
            'atlas_number': atlas_index,
            'width': width,
            'height': height,
            'mode': source.mode,
            'bytes': len(source_bytes),
            'sha256': source_hash,
            'pixel_sha256': sha256(source.tobytes()),
            'former_css_data_url_characters': original_data_url_characters,
            'exceeded_chromium_css_variable_limit': (
                original_data_url_characters > CHROMIUM_CUSTOM_PROPERTY_LIMIT
            ),
            'x_boundaries': x_bounds,
            'y_boundaries': y_bounds,
            'gutter_detection': gutter_audit,
        }
        catalog['sources'].append(source_record)

        for offset in range(GRID * GRID):
            vocabulary_index = (atlas_index - 1) * GRID * GRID + offset
            card = vocabulary[vocabulary_index]
            card_id = card['id']
            row, column = divmod(offset, GRID)
            crop_box = (
                x_bounds[column], y_bounds[row],
                x_bounds[column + 1], y_bounds[row + 1],
            )
            tile = source.crop(crop_box)
            target_path = output_dir / f'{card_id}.png'
            tile.save(target_path, format='PNG', optimize=True)
            raw = target_path.read_bytes()
            with Image.open(target_path) as decoded:
                decoded.load()
                if decoded.mode != tile.mode or decoded.size != tile.size:
                    raise ValueError(f'Lossless crop format failure: {card_id}')
                if decoded.tobytes() != tile.tobytes():
                    raise ValueError(f'Pixel mismatch after PNG encoding: {card_id}')
                reconstructed.paste(decoded, (crop_box[0], crop_box[1]))
            pixel_match_passes += 1
            data_url_characters = len(png_data_url(raw))
            max_data_url_characters = max(max_data_url_characters, data_url_characters)
            total_bytes += len(raw)
            catalog['items'][card_id] = {
                'id': card_id,
                'word': card['word'],
                'alt': card['visual_scene'],
                'src': target_path.relative_to(book_dir).as_posix(),
                'width': tile.width,
                'height': tile.height,
                'mode': tile.mode,
                'bytes': len(raw),
                'data_url_characters': data_url_characters,
                'sha256': sha256(raw),
                'pixel_sha256': sha256(tile.tobytes()),
                'atlas': source_path.name,
                'atlas_sha256': source_hash,
                'row': row,
                'column': column,
                'crop_box': list(crop_box),
            }
        if reconstructed.tobytes() != source.tobytes():
            raise ValueError(f'Atlas reconstruction failed: {source_path.name}')
        source_record['reconstruction_pixel_match'] = True
        reconstruct_passes += 1

    catalog['qa'] = {
        'card_count': len(catalog['items']),
        'source_count': len(catalog['sources']),
        'all_card_ids_present_once': list(catalog['items']) == expected_ids,
        'lossless_crop_matches': pixel_match_passes,
        'pixel_exact_atlas_reconstructions': reconstruct_passes,
        'nonempty_semantic_alt_texts': sum(bool(x['alt'].strip()) for x in catalog['items'].values()),
        'total_tile_png_bytes': total_bytes,
        'maximum_tile_data_url_characters': max_data_url_characters,
        'all_legacy_atlas_css_variables_exceeded_limit': all(
            x['exceeded_chromium_css_variable_limit'] for x in catalog['sources']
        ),
        'artwork_changed': False,
        'boundaries_follow_real_gutters': True,
    }

    supplemental_path = book_dir / 'supplemental_audio_targets_v2.json'
    readings_path = book_dir / 'reading_audio_targets_v2.json'
    targets = (
        json.loads(supplemental_path.read_text(encoding='utf-8'))
        + json.loads(readings_path.read_text(encoding='utf-8'))
    )
    target_map = {item['id']: item for item in targets}
    association_ids = [row[0] for row in ASSOCIATION_ROWS]
    if len(association_ids) != len(set(association_ids)):
        raise ValueError('Duplicate curated association ID.')
    if set(association_ids) != set(target_map):
        raise ValueError('Association coverage must exactly match the 130 supplemental targets and five readings.')
    catalog['associations'] = {}
    for target_id, card_id, cue, reason in ASSOCIATION_ROWS:
        item = catalog['items'][card_id]
        target = target_map[target_id]
        prefix = 'Metin ipucu' if target_id.startswith('R') else 'Bağlı kavram'
        catalog['associations'][target_id] = {
            'card_id': card_id,
            'label': f'{prefix}: {cue} · {item["word"]}',
            'reason': reason,
            'target_word': target['word'],
            'source_word': item['word'],
            'kind': 'shared-semantic-cue',
            'notice': 'Mevcut kelime kartından paylaşılan hafıza ipucu; bu öğe için ayrı çizim değildir.',
        }
    catalog['association_source_sha256'] = {
        'supplemental_audio_targets_v2.json': sha256(supplemental_path.read_bytes()),
        'reading_audio_targets_v2.json': sha256(readings_path.read_bytes()),
    }
    catalog['qa']['curated_supplemental_associations'] = 130
    catalog['qa']['curated_reading_associations'] = 5
    catalog['qa']['all_associations_reference_existing_cards'] = all(
        value['card_id'] in catalog['items'] for value in catalog['associations'].values()
    )
    catalog['qa']['representative_contact_sheet'] = contact_sheet(book_dir, catalog['items'])
    output_path = book_dir / 'visual_catalog_v3.json'
    output_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--book-dir', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    catalog = prepare(args.book_dir)
    print(json.dumps(catalog['qa'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
