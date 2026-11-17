# Ses kalite denetimi — son kayıt

**Kapsam:** 1.226 girdi, 1.537 MP3. Toplam **73 dakika 37,872 saniye** (4.417,872 saniye); **53.869.058 bayt**. Beş bütünleşik okumanın toplamı **7 dakika 21,480 saniye**.

## Tamamlanan kontroller

- 1.537 dosyanın tamamı ses olarak çözümlendi: tümü 24 kHz ve tek kanal; boş/sessiz dosya, sayısal taşma ve kırpılmış örnek saptanmadı. Son dosyaların SHA-256 değerleri ve geçerli metin/fonem işlerine ait özetleri uyuşuyor.
- 1.221 telaffuz başlığının fonem dizileri gözden geçirildi. İsim–fiil ayrımları, *invalid* sıfatı, *lead* fiili, *biodiverse* vurgusu ve harf yer tutucuları gibi riskli durumlar ayrıca düzeltildi. Beş ana kartta ayrı isim ve fiil sesleri var.
- Son dosyaların **tamamı**, hedef metin verilmeden `base.en` konuşma tanıyıcıdan geçirildi. Büyük/küçük harf ve noktalama normalizasyonundan sonra **1384** transkript tam eşleşti; **153** sonuç farklıydı. Bu oran telaffuz başarısı ya da insan anlaşılırlığı puanı değildir.
- Daha güçlü `small.en` tanıyıcıyla son sürümde **88 farklı dosya** yeniden incelendi. Bu küme beş tam okuma metnini ve son 27 açıklık düzenlemesini kapsar. Önceki aday dalga biçimleri de karşılaştırılmıştır; onların sayısı teslim dosyası sayısı gibi gösterilmemiştir.
- Beş okumada **not, no, may, might, could, would, necessarily, only, yet, all, some** ifadelerinin bütün gerçekleşimleri kontrol edildi. İki tanıyıcı da bu sınırlandırıcı ifadeleri korudu; güçlü tanıyıcıda R02 ve R05'in bütün sözcükleri normalizasyondan sonra eşleşti.

## Bulguların sınırı

Amerikan İngilizcesi tanıyıcının *catalogue* yerine *catalog* yazması ses hatası değildir. *Led/lead*, *make up/makeup*, harf ve sayı gibi yakın sesli yazımlar da tek başına yanlış telaffuz kanıtı değildir. Bazı kısa kelimelerde otomatik tanıma yine belirsiz kaldı; örneğin *scarce*, *rural*, *succinct* ve *challenge*. İstenen fonemler hedef sözcüklerle uyumludur; otomatik transkript bu örneklerde kesin hakem olarak kabul edilmemiştir.

Okumaların güçlü tanıyıcı çıktısında R03 ve R04 başındaki *a/the* ile R03'teki *seed/seeds* ayrımı da belirsiz kaldı. Kaynak İngilizce metin ve hedef fonemler değiştirilmedi. Bunlar gerçek ses kusuru olarak kesinleştirilmiş bulgular değildir. Bütün kayıtların bir insan fonetik uzmanı tarafından dinlendiği veya kusursuz telaffuz garantisi verildiği ileri sürülmez.

Ayrıntılı sayısal denetim ve dosya özetleri `AUDIO_QA_FINAL.json`; kaynak/lisans bilgileri `SES_KAYNAKLARI.md`; her sesin hedef metni, süresi ve SHA-256 değeri [ses manifestinde](../kaynak/audio_manifest_v2.json) bulunur.
