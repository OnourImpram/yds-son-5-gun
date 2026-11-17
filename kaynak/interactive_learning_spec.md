# YDS etkileşimli öğrenme katmanı — veri ve uygulama sözleşmesi

**Sürüm:** 2.0 · **İçerik denetimi:** 17 Kasım 2026 · **Öğretim dönemi:** 17–21 Kasım 2026.

Bu katman mevcut kitabın bilimsel iddialarını veya sınav verilerini değiştirmez. Kaynak `vocabulary.json` içindeki 176 hedefi yeni öğrenme görevlerine dönüştürür. Eklenen karşılaştırma soruları özgün öğretim materyalidir; gerçek YDS soruları veya kalibre edilmiş bir ölçme aracı değildir.

## 1. Teslim edilen öğrenme içeriği

| Bileşen | Sayı | Öğrenenin yaptığı iş | Denetimin sınırı |
|---|---:|---|---|
| Dinle ve yaz | 176 | Sözcük/ifade kaydını dinleyip İngilizce yazma | İşitilen hedefin yazımı; konuşma kalitesi puanı değildir |
| Anlamdan getir | 176 | Türkçe anlam ipucundan İngilizce hedefi üretme | İlgili kartın hedefi; bütün geçerli eş anlamlıları tüketmez |
| Cümleyi tamamla | 176 | Hedefi kaynak örneğe uygun biçimde üretme | Verilen çekim yönergesi ve kaynak cümle; serbest metin değerlendirmesi değildir |
| İnce ayrımlar | 32 | Dört seçenek arasından anlam/yapı ayrımını seçme | Her soruda bir hedef cevap ve dört seçenek açıklaması |
| Manuel hatırlama derecesi | 4 | Kendi yardım kullanımını ve üretimini değerlendirme | Öz bildirim; kalıcı öğrenmenin veya aksanın ölçümü değildir |

Toplam **560 yeni görev** vardır. Kart hedeflerinin gün dağılımı kaynakla aynıdır: ilk dört günün her birinde 44 hedef; beşinci gün bütün hedefler için kümülatif tekrar yapılabilir. Aynı hedefin üç görevde kullanılması üç ayrı sözcük öğrenildiği anlamına gelmez.

## 2. JSON yapısı

`enrichment_v2.json` kök alanları:

```text
schema_version, status, created_date, source_vocabulary_sha256,
content_notice, targets, confusions, normalization,
self_rating_rubric, review_policy, sources, validation
```

`targets` dizisinin her kaydı aynı kaynak kimliğini kullanır:

```text
{
  id: V001, day: 1, word: evidence,
  dictation: {
    id: D-V001, audio_key: V001.word, prompt,
    accepted_answers, feedback_scope
  },
  recall: {
    id: R-V001, prompt, hint, accepted_answers, feedback_scope
  },
  cloze: {
    id: C-V001, source_field: example, source_sentence,
    prompt, answer, accepted_answers, answer_span,
    instruction, form_cue, grammar_explanation,
    explanation, feedback_scope
  }
}
```

`audio_key` mantıksal anahtardır: `V001.word`, ses manifestindeki `items.V001.word` kaydına eşlenir. Sesin yerel yolu bu dosyada yeniden tanımlanmaz; ses manifesti tek yetkili kaynaktır.

`cloze.prompt` yalnız bir boşluk içeren İngilizce cümledir. `cloze.instruction` üstünde görünmelidir. Bu yönerge bazı cümlelerde anlamca mümkün olabilecek başka bir zamanı dışlamak için beklenen zamanı veya biçimi açıkça söyler. Örneğin **assessed** beklenen bir geçmiş olay görevinde, çekim yönergesi olmadan **assesses** biçimini yalnız cümleye bakarak yanlış saymak uygun değildir.

`answer_span`, özgün `source_sentence` içindeki yarı açık `[başlangıç, bitiş)` karakter aralığıdır. Bu aralık çıkarılıp `____` yerleştirildiğinde `prompt`; boşluk `answer` ile doldurulduğunda özgün cümle elde edilir. Kaynak cümlenin kelimeleri, nicelikleri, kipliği veya iddiası yeniden yazılmaz.

`confusions` kayıtları:

```text
{
  id: X01, type: single_choice, skill, stem,
  options: [A, B, C, D], answer: 0…3,
  explanations: [A açıklaması, B açıklaması, C açıklaması, D açıklaması],
  rationale, related_vocab: [V004, V005], day, difficulty: 1…3,
  error_code: K/G/B/Ç, error_category,
  source_refs, provenance
}
```

`error_code`, hata defterindeki öğretim yolunu belirtir: K kelime/kalıp, G dil bilgisi, B bağlam/mantık, Ç çıkarım/kapsam. Bu atama öğrenenin psikolojik durumu veya tekil hatanın gerçek nedeni hakkında tanı değildir.

Cevap anahtarı **sıfır tabanlıdır**. Seçenekler taşınırsa açıklamaları da aynı sırayla taşınmalıdır. Mevcut sette A/B/C/D anahtarları sekizer kez kullanılır; bu denge soru geçerliğinin kanıtı değildir. Zorluk alanı yazarın öğretim sıralamasıdır; deneysel madde güçlüğü değildir.

## 3. Cevabı göstermeden geri çağırma

### Görünür ve erişilebilir alanlar

Öğrenme görünümü bütün kartı gösterebilir. Anlamdan getir, dinle ve yaz veya cümleyi tamamla görünümünde yanıt açılana kadar şu alanlar hedefi sızdırmamalıdır:

- Kart başlığı, yan gezinme listesi ve seçili kart etiketi.
- Oynatıcı başlığı, ses düğmesinin `title` ve `aria-label` alanları.
- Önceki görünümden kalan oynatma başlığı veya durum mesajı.
- Görselin içine yazılmış hedef, görsel açıklaması, alternatif metin veya açık kart ayrıntısı.
- Hata defterine ekleme gibi eylemlerden gelen hedefi adlandıran bildirimler.

Gizli hedef için erişilebilir düğme adı **“Hedef kaydını dinle”** olabilir. Dinleme görevinde hedef sesinin duyulması görevin kendisidir; yazımının etiketle görünmesi gereksiz ipucudur. Anlamdan getirmede ses, görsel veya ilk harf açılması ise yardım olarak kaydedilir.

Görsel veya ses ipucu isteğe bağlı açılabilir. İpucu kullanıldıktan sonra doğru cevap verilmesi, **yardımlı doğru** sayılır. Kart yeniden kapatılıp hemen okunmuş cevabın tekrarlanması bağımsız gecikmeli hatırlama gibi etiketlenmez.

Bu çalışma kitabı bütün yanıtları istemci dosyasında içerir. Tarayıcı kaynak koduna bilinçli erişim engellenmez; amaç gözetimli sınav güvenliği değil, çalışma arayüzünün cevabı istemeden göstermemesidir.

### Görev akışı

1. İpucu/boşluk/öğretim yönergesini göster; doğru biçimi gizle.
2. Öğrenen kendi yanıtını yazar. Boş yanıt, doğru veya yanlış olarak otomatik kaydedilmez.
3. Yanıt gönderildiğinde hedefle eşleşme açıklanır ve doğru biçim açılır.
4. Cümle görevi, biçimin neden gerektiğini ve özgün Türkçe karşılığını gösterir.
5. Öğrenen yardım kullanımını dikkate alarak hatırlama derecesini seçer.
6. Bir sonraki kartta yanıt, görünür çözüm, ipucu, önceki görev kaydı ve hata bayrakları sıfırlanır.

Bir karta iki kez değerlendirme düğmesi basılması, iki bağımsız deneme üretmemelidir. Gerçek yeniden deneme için yeni görev turu gerekir.

## 4. Yazım denetimi

Bu görevler sınırlı, açık cevap anahtarına sahiptir. Denetim şu sırayla uygulanabilir:

1. Unicode NFKC normalizasyonu.
2. İngilizce cevap girişinde Türkçe `İ` → `I`, `ı` → `i`; ardından İngilizce küçük harfe çevirme.
3. Kıvrık apostrofları düz apostrofa çevirme.
4. U+2010–U+2015 ve U+2212 çizgilerini ASCII `-` biçimine çevirme.
5. Birden fazla boşluğu birleştirme; baştaki ve sondaki boşlukları temizleme.
6. Yalnız çevreleyen tırnakları ve sondaki `. , ! ? ; :` işaretlerini görmezden gelme.
7. Aynı normalizasyondan geçmiş `accepted_answers` girdilerinden biriyle tam eşleşme.

**Silinmemesi gereken ayrımlar:** sözcük içindeki harfler, sözcük sırası, çoğul/fiil ekleri, çok sözcüklü ifadenin boşlukları ve zorunlu parçaları. `accountfor`, `account for` yerine otomatik kabul edilmez. `derived`, `derive` yerine her görevde otomatik kabul edilmez.

Kaynak hedefler içinde açıkça kabul edilen ek yazım çifti `cooperate / co-operate`; çekimli örnekte `cooperated / co-operated` biçimidir. Bu kabul Cambridge yazım kaydına dayanır. Bütün tireleri kaldırmak veya bütün benzer yazımları başarı saymak gerekmez. Yazım yakınlığı istenirse öğretici bir ipucu üretebilir; başarı kaydı üretmez.

Eşleşmeyen yanıt için uygun geri bildirim:

> Beklenen hedef biçimle eşleşmedi. Bu görev ilgili kartın hedefini denetler; başka bir geçerli eş anlamlı kullanmış olman bütün İngilizce ifadenin yanlış olduğu anlamına gelmez.

## 5. Manuel hatırlama rubriği

| Derece | Etiket | Gözlenebilir ölçüt | Önerilen sonraki tekrar |
|---:|---|---|---|
| 0 | Tekrar | Üretemedim; yanlıştı; cevabı görmeden yanıtlayamadım | 10 dakika |
| 1 | Zor | İpucu veya belirgin tereddütle buldum; bağımsız kullanım zayıf | 2 saat |
| 2 | İyi | Yardımsız doğru ürettim ve örnekteki kullanımı açıklayabiliyorum | 1 gün |
| 3 | Kolay | Yardımsız ürettim; benzerinden ayırıp yeni cümlede kullanabiliyorum | 2 gün |

Son iki ölçüt öz değerlendirmedir. Yeni cümle dilsel olarak değerlendirilmeden “otomatik doğrulanmış transfer” denmez. Kendi sesini kaydedip örnekle karşılaştırmak, manuel fark etme uygulaması olabilir; doğrulanmış bir model olmadan otomatik aksan/akıcılık/telaffuz puanı verilmez.

İlk yanlış deneme ile çözüm görüldükten sonraki tanıma ayrı tutulmalıdır. İpucu veya çözümden sonra hissedilen kolaylık ilk denemeyi geriye dönük yardımsız başarıya çevirmemelidir. Öğrenen yeni bir bağımsız denemede başarılı olduğunda sonraki kaydı değişebilir.

## 6. Beş günlük tekrar sezgiseli

Takvim **Europe/Istanbul** saat dilimindedir. Özel çalışma penceresi 17 Kasım 2026 00:00 ile 21 Kasım 2026 18:00 arasındadır. Gün bitişi öğretim tercihidir; bir araştırmanın hesapladığı evrensel son tekrar saati değildir.

```text
normal_due = now + {0: 10 dakika, 1: 2 saat, 2: 1 gün, 3: 2 gün}[derece]

if window_start <= now < window_end and normal_due > window_end:
    due = window_end
else:
    due = normal_due
```

Son tarihten sonra program normal aralıkları kullanır; geçmişte bir tekrar zamanı yaratarak sonsuz “tekrar zamanı geldi” döngüsü kurmaz. Tarih sınırına kadar zaten zamanı gelmiş görevler önce sunulur. Aynı kartın bütün görevleri ayrı hedef kelimeler gibi sayılmaz.

Yanlış yanıt 10 dakikalık onarım tekrarı için uygun bir sinyaldir. Doğru fakat düşük güvenli/yardımlı yanıt 2 saatlik yakın tekrar için kullanılabilir. Yüksek güvenle verilen yanlış, incelenecek bir uyumsuzluktur; kendi başına “yanlış öğrenme tanısı” değildir. Öncelik için zamanın gelmesi, hata, güven ve yardım kullanımı birlikte değerlendirilebilir.

**Ayrı tutulacak kayıtlar:** görüldü; yanıtlandı; doğru hedefle eşleşti; cevap açıldı; ipucu kullanıldı; öğrenenin güveni; manuel hatırlama derecesi; son tekrar; sıradaki tekrar. Yalnız bir karta bakmak “öğrenildi” sayılmaz. Prova puanı ile kelime geri çağırma oranı tek bir başarı puanında birleştirilmez.

Bu kesin aralıklar, pratik bir öğretim sezgiselidir. Geri çağırma ve aralıklandırma araştırmaları tasarıma dayanak verir; bu uygulamanın tamamı veya bu dakika değerleri bir YDS deneyinde sınanmış değildir. Karpicke ve Roediger'in yabancı dil sözcük çiftleri deneyi yinelenen geri çağırmayı, Cepeda ve arkadaşlarının çalışması ise tekrar aralığı ile son test gecikmesi arasındaki ilişkiyi destekler. İki araştırmadan da belirli YDS puan kazancı, herkeste eşit sonuç veya beş günde kalıcı ustalık garantisi çıkarılmaz. [L1–L2]

## 7. İnce ayrım sorularının denetim ilkeleri

Soruların tamamında bağlam veya yönerge tek hedef cevabı belirler. Özellikle şu tuzaklar giderilmiştir:

- `adopted / adapted` sorusunda istenen Türkçe anlam açıkça belirtilmiştir. Tek başına “adapted a new approach” dil bilgisel olarak mümkünken yanlış sayılmaz.
- `bring about / bring out` sorusunda meydana getirme ile mevcut farkı belirginleştirme açıkça ayrılmıştır.
- `prone to do` ile `prone to doing` birlikte kabul edilmiştir. Sık öğretilen tek kalıp bütün standart kullanımların sınırı sayılmamıştır. [E2]
- `be comprised of`, güncel öğrenici kaynaklarındaki kullanımı nedeniyle kabul edilmiştir. Hedef hata etken `comprises of` karışmasıdır; üslup tercihi evrensel dil yasağı yapılmamıştır. [E5]
- `requires repairing` biçimi edilgen anlamıyla öğretilir. [E6]
- `need not have done` ile `did not need to do` farkında ikinci yapı tek başına eylemin yapılmadığını kanıtlamaz. [E3]
- `not all` için zorunlu en dar çıkarım en az bir istisnadır; “mutlaka bazıları kabul etti” veya belirli bir oran eklenmez.
- `cannot rule out` dışlayamamayı, `consistent with` uyumluluğu bildirir; hiçbirisi tek başına kesin neden veya tek açıklama sayılmaz.
- Güvenirlik/doğruluk örneğinde reliable sözcüğü yalnız tekrar tutarlılığı anlamıyla sınırlandırılmıştır; bütün psikometrik güvenirlik kuramını temsil ettiği iddia edilmez.

## 8. Erişilebilirlik ve çalışma kayıtları

Butonların anlaşılır erişilebilir adları, görünür klavye odağı, cevap için etiketli giriş alanı ve yalnız renk kullanmayan sonuç mesajları olmalıdır. Görev yönergeleri yalnız renge, sese veya görsele bağlı kalmaz. Dinleme alıştırmasının hedefi ses olduğundan sesi duymayan kullanıcı için eşdeğer görsel test varmış gibi davranılmaz; aynı hedefin anlamdan üretme ve cümle görevi ayrı seçeneklerdir.

Tek oynatıcı yeni ses başladığında önceki sesi durdurmalıdır. Yavaş oynatma yardım olabilir; ölçüm puanını veya hedef telaffuz doğruluğunu temsil etmez. Ses kendiliğinden başlamamalıdır.

İlerleme tarayıcıda saklanıyorsa bu açıkça yazılmalıdır. Dışa aktarma ayrı bir yedek sağlar; yerel kaydın her tarayıcıda kalıcı olacağı garanti edilmez. Mikrofon kaydı eklenirse kullanıcının açık eylemiyle başlamalı, yüklendiği yer konusunda doğru bilgi vermeli ve yetkisiz sunucu aktarımı yapmamalıdır.

## 9. Doğrulama kaydı

İçerik doğrulaması `qa_v2/enrichment_audit.json` içinde tutulur. Yapısal kontroller bütün hedeflere uygulanır; 32 sorunun tek cevaplılığı ayrıca anlam ve yapı bakımından yeniden okunur. Denetim yalnız aynı verinin kendi kendine eşit olduğunu görmekten oluşmaz: yanlış seçeneklerin hangi kelime, koşul, zaman, rol veya kapsam farkıyla dışlandığı kaydedilir.

Uygulama denetiminde, yanıt açılmadan önce görünür ve erişilebilir hedef sızıntısı kontrol edilir. Bu inceleme içerik doğrulamasından ayrıdır; bir sorunun doğru yazılması arayüzde doğru gizlendiğini kendiliğinden kanıtlamaz.

### Kaynak anahtarları

- **E1:** Cambridge Dictionary, cooperate — https://dictionary.cambridge.org/dictionary/english/cooperate
- **E2:** Oxford Advanced Learner’s Dictionary, prone — https://www.oxfordlearnersdictionaries.com/definition/english/prone
- **E3:** Cambridge English Grammar Today, Need — https://dictionary.cambridge.org/grammar/british-grammar/need
- **E4:** Cambridge English Grammar Today, Conditionals: other expressions — https://dictionary.cambridge.org/grammar/british-grammar/conditionals-other-expressions-unless-should-as-long-as
- **E5:** Cambridge English Grammar Today, Consist, comprise or compose? — https://dictionary.cambridge.org/grammar/british-grammar/comprise
- **E6:** Oxford Advanced Learner’s Dictionary, require — https://www.oxfordlearnersdictionaries.com/us/definition/english/require
- **E7:** Cambridge Dictionary, oversight — https://dictionary.cambridge.org/dictionary/english/oversight
- **E8:** Cambridge English Grammar Today, In spite of and despite — https://dictionary.cambridge.org/grammar/british-grammar/in-spite-of-and-despite
- **E9:** BBC Learning English, Even though vs even if — https://downloads.bbc.co.uk/learningenglish/eiam/unit-1/181026_even_though_vs_even_if.pdf
- **L1:** Karpicke, J. D., & Roediger, H. L., III. (2008). The critical importance of retrieval for learning. Science, 319(5865), 966–968. DOI: 10.1126/science.1152408. https://pubmed.ncbi.nlm.nih.gov/18276894/
- **L2:** Cepeda, N. J., Vul, E., Rohrer, D., Wixted, J. T., & Pashler, H. (2008). Spacing effects in learning: A temporal ridgeline of optimal retention. Psychological Science, 19(11), 1095–1102. DOI: 10.1111/j.1467-9280.2008.02209.x. https://pubmed.ncbi.nlm.nih.gov/19076480/
