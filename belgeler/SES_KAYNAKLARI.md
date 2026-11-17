# YDS ses kayıtları: kapsam, kaynak ve üretim bilgisi

Bu sesler kitabın İngilizce kelime, kalıp ve örnek cümlelerini dinleyerek çalışmak için üretildi. İnsan stüdyo kaydı değildir; Kokoro-82M v1.0 modelinin hazır **af_heart** sentetik sesi kullanılmıştır. Amerikan İngilizcesi hedeflenmiştir. Kullanıcıya veya başka bir kişiye ait ses örneği alınmamış; kişisel ses klonlaması yapılmamıştır.

## Kapsam

- 176 ana kelime/kalıp kartının her birinde bağımsız telaffuz ve kendi örnek cümlesinin kaydı.
- 50 çok sözcüklü fiil yapısının ve 80 collocation başlığının her birinde telaffuz ve mevcut örnek cümle kaydı.
- Kartlarda zaten bulunan sözcük ailesi ve collocation alanlarındaki 915 ek benzersiz ifade için bağımsız telaffuz: 431 aile biçimi ve 484 kelime birlikteliği.
- **Estimate, attribute, implement, permit ve advocate** için fiil ana kaydına ek olarak ayrı isim kaydı. Diğer açık rol seçimleri manifestte etiketlenmiştir: örneğin *invalid* sıfat, *lead* fiildir.

- Kitaptaki beş bütünleşik İngilizce okuma metninin tamamı, özgün metin korunarak seslendirilmiştir.

Böylece 1.226 kayıt girdisi için 1.537 MP3 dosyası hazırlanmıştır: 1.221 telaffuz, 306 örnek cümle, beş ek isim biçimi ve beş tam okuma metni. Gerçek tamamlanma sayısı ve dosya listesi [ses manifestinde](../kaynak/audio_manifest_v2.json) tutulur. Bu toplamlar, metindeki bütün tesadüfi sözcüklerin her çekiminin ayrı ayrı seslendirildiği anlamına gelmez; hedef kartları, öğretilen yapı başlıklarını ve kartların iki açık sözlük alanını kapsar.

## Sesin biçimi

MP3, tek kanal, 24 kHz, 96 kbps. Dinleme dosyaları yereldir; oynatım için ses üretim servisi, hesap, internet bağlantısı veya tarayıcı `speechSynthesis` desteği gerekmez. Kayıtların çevrimdışı çalışması için uygulama ile birlikte paketlenmeleri gerekir. Normal hız, üretimde 0,95 model hızıdır; arayüzdeki yavaşlatma oynatma hızını değiştirir.

Zayıf son ünsüzleri korumak için başa ve sona koruyucu boşluk eklenmiştir. Kısa sözlerde daha anlaşılır üretim elde etmek için bazı kayıtlar bir cümle veya tekrar bağlamı içinde sentezlenip modelin fonem zamanlamasıyla ayrılmıştır; bağlamın kendisi kelime kaydında yer almaz. Bu düzenlemeler ayrı denetim kaydında belirtilir. Dosyalar çözümlenerek örnekleme hızı, kanal sayısı, sessiz/boş kayıt, doygunluk, süre, SHA-256 ve hedef metin eşleşmesi denetlenir. Fonem kaynakları ile açık dilbilgisel rol düzeltmeleri saklanmıştır. Sentez motorunun fonem dizileri standart sözlük IPA gösterimi olarak sunulmaz.

## Lisans ve atıf

1. **Kokoro-82M / hexgrad**: Model ağırlıkları sağlayıcı tarafından Apache-2.0 olarak yayımlanmıştır. [Model kartı](https://huggingface.co/hexgrad/Kokoro-82M), [ses listesi](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md). Model kartı ve lisansın kopyaları `licenses/` klasöründedir.
2. **kokoro-onnx / thewh1teagle**, sürüm 0.6.0: MIT. [Kaynak](https://github.com/thewh1teagle/kokoro-onnx). ONNX dışa aktarımı `model-files-v1.1` yayımından alınmış, model ve ses paketi SHA-256 değerleri yayım kayıtlarıyla karşılaştırılmıştır.
3. **Misaki / hexgrad**, sürüm 0.9.4: Apache-2.0. [Kaynak](https://github.com/hexgrad/misaki). İngilizce sözcük türü ve bağlama duyarlı yazı–fonem dönüşümü kullanılmıştır; sözlük dışındaki birkaç biçimde eSpeak NG geri dönüşü vardır.
4. Model kartının eğitim verisi atıfları da korunmuştur: [Koniwa](https://github.com/koniwa/koniwa), CC BY 3.0; [SIWIS](https://datashare.ed.ac.uk/handle/10283/2353), CC BY 4.0. Bu atıflar kullanılan İngilizce sesin bu veri kümelerinden biri olduğu iddiası değildir. Sağlayıcı **af_heart** için ayrı ve eksiksiz bir eğitim kayıt dökümü yayımlamamıştır; burada model sağlayıcısının beyanı aktarılmış, bağımsız bir veri hakları incelemesi yapıldığı ileri sürülmemiştir.
5. Eş yazımlı sözcüklerin ses ayrımları ve seçili düzeltmeler, **Cambridge Dictionary** yayımlayıcı sayfalarıyla karşılaştırılmıştır. Sözlük ses dosyaları indirilip yeniden dağıtılmamıştır; bütün teslim edilen MP3'ler özgün sentezdir. İlgili sayfalar manifestte listelenmiştir.

## Denetimin sınırları

Otomatik konuşma tanıma, sentezdeki atlama/ekleme ve anlaşılabilirlik risklerini aramak için ek bir kontroldür. Yazım farkları (*programme/program*), aynı sesli biçimler ve kısa kelimelerde tanıyıcının yaptığı hatalar otomatik olarak telaffuz hatası sayılmaz. Aynı şekilde doğru transkript, vurgu ve her sesin kusursuz olduğu anlamına gelmez. Sözcük türü kontrolü, fonem incelemesi ve ses dosyası denetimleri bu yüzden ayrı yürütülür. Bir insan fonetik uzmanının bütün kayıtları tek tek dinlediği iddia edilmez.

## Son dosya toplamı

1.537 MP3, 73 dakika 37,872 saniye; beş tam okuma 7 dakika 21,480 saniye. Son sürümün bütün dosyaları çözümlenmiş ve otomatik konuşma tanımadan geçirilmiştir. Denetim sayıları, otomatik tanımanın belirsizlikleri ve insan dinlemesini kapsamayan bu kontrolün sınırları `SES_KALITE_DENETIMI.md` içinde açıklanır.
