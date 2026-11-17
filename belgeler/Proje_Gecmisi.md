# YDS Son 5 Gün | Proje geçmişi

İngilizce YDS için hazırlanan beş günlük program, geçmiş kitapçıklarda görülen dilsel ayrımları özgün derslere, örneklere ve sınav provasına dönüştürdü. Programın ortak çekirdeğinde 176 görsel sözcük ve kalıp kartı, ayrıntılı dil bilgisi anlatımı, okuma atölyeleri ve gerekçeli çözümler yer alır.

| Sürüm | Yapılan çalışma | Kapsam ve doğrulama |
|---|---|---|
| 1 · Hazırlık kitabı | Geçmiş sınavların kaynak incelemesi, beş günlük plan, sözcük atlası, dil bilgisi, okuma atölyeleri ve özgün sorular bir araya getirildi. | İki tam ve on kısmi kitapçıkta toplam 240 görünür soru incelendi. Öğretim seçkisi için tam ve kısmi dosyaların farklı kapsama sahip olduğu kayda geçirildi. |
| 2 · Sesli öğrenme | Dikte, anlamdan hatırlama, cümle tamamlama, ince ayrımlar, tekrar planı ve ses kütüphanesi eklendi. | 176 ana hedef için üçer görev ve 32 ayrım sorusu hazırlandı. Son ses arşivi, 1.226 girdide 1.537 MP3 içerir. |
| 3 · HTML onarımı | Büyük CSS atlasları tekil görsellerle değiştirildi. Ses kütüphanesi ile görseller ilişkilendirildi. İpucu, klavye odağı, sınav süresi ve yedek birleştirme düzeltildi. | Öğretim metni önceki HTML ile karşılaştırıldı. Gömülü görsel ve seslerin bütünlüğü, DOM davranışı ve yedek birleştirme senaryoları denetlendi. Ayrıntılar [üçüncü sürüm kaydında](HTML_V3_Onarim_ve_Dogrulama.md). |
| 4 · İçerik ve prova incelemesi | 23 çoktan seçmeli madde ve dört açık uçlu görev düzenlendi. Beş güne 20 çözümlü örnek ve 20 aktarım sorusu eklendi. Puanlamada önceki soru bankasının anahtarı korundu. PDF görselleri ve cevap formu, HTML'de günlük okuma girişi, ayraç ve oynatıcı yeniden işlendi. | Soru ve seçenek gerekçeleri, medya dosyaları, PDF düzeni ve DOM davranışı denetlendi. Ayrıntılar [dördüncü baskı kaydında](Dorduncu_Baski_Inceleme.md). |

## Yöntem ve sınırlar

[Derlem yöntemi](../kaynak/source_analysis.md), dosya bazında görünen soru numaralarını ve yüzey biçimi sayımını açıklar. [Envanter](../kaynak/source_inventory.json) dosya kimliklerini ve SHA-256 özetlerini, [sayım dökümü](../kaynak/corpus_stats.json) toplu sonuçları ve kullanılan örüntüleri verir. Kitapçık PDF'leri, toplu soru metinleri ve örnek alıntı alanları bu dağıtımdan çıkarılmıştır. [Kaynakça](../kaynak/references.md) resmî belgelere ve öğretim kararlarının araştırma dayanaklarına bağlanır.

Kısmi ÖSYM seçkisinin rastgele örneklendiği varsayılamaz. Yüzey sayımı aday seçeneklerini de kapsar ve sözcüğün kullanıldığı anlamı etiketlemez. Öğretim sorularının güçlüğü öğrenci verileriyle kalibre edilmemiştir. Deneme sonucu, gerçek YDS puanı tahmini olarak yorumlanmamalıdır.

## Çıktılar

- [Etkileşimli kitap](../index.html)
- [Basılabilir hazırlık kitabı](../kitap/YDS_Son_5_Gun_Hazirlik_Kitabi.pdf)
- [Yeniden üretim adımları](Yeniden_Uretim.md)
- [Lisanslar ve atıflar](Lisanslar_ve_Atiflar.md)

Öğretim tasarımında geri çağırma için Karpicke ve Roediger, tekrar aralıkları için Cepeda ve çalışma arkadaşları, görsel ve sözel öğelerin birlikte kullanımı için Mayer ve Anderson, mekân temelli hatırlama için Massen ve çalışma arkadaşları, aktarım için Butler'ın çalışmaları referans alındı. [Kaynakça](../kaynak/references.md), yazarları, makaleleri ve bulguların bu projeye hangi sınırlarla uygulandığını verir.

## Gelecekteki uygulama için devralma notu

Uygulama yeni bir platforma taşınırken kart, ders görevi, madde ve ses kimlikleri korunabilir. `vocabulary.json` kartları, `enrichment_v2.json` çalışma görevlerini, `study.json` günlük aktarım alıştırmalarını, `assessment.json` ve `assessment_v3_archive.json` sürümlü soru bankalarını, `audio_manifest_v2.json` ise yerel ses dosyalarını ve özetlerini tanımlar. Veri düzeni için [öğrenme katmanı sözleşmesine](../kaynak/interactive_learning_spec.md) bakılabilir.

Mevcut kaynaklar, çevrimdışı kullanım için tek dosyalı HTML ve medya klasörleriyle çalışan statik web sürümü üretir. Öğrenen ilerlemesi tarayıcının yerel depolamasında tutulur ve JSON yedeği olarak dışa aktarılabilir. Yeni bir uygulamada, eski anahtarlarla değerlendirme ve ilk yanıtı koruma davranışı yedek içe aktarma testleriyle taşınabilir. Bugünkü sürümde reklam bulunmaz. Ticari bir dağıtım veya reklam ekleme kararı öncesinde öğretim içeriği, görseller, yazılım, ses ve üçüncü taraf bileşenler için geçerli kullanım hakları ayrıca incelenmelidir.
