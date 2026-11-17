# Dördüncü baskıyı yeniden üretme

`kaynak/` dizini derslerin Markdown metinlerini, uygulama kodunu ve PDF üreticisini içerir. `vocabulary.json` ana kartları, `assessment.json` güncel soru bankasını, `assessment_v3_archive.json` geçmiş denemelerin özgün anahtarlarını ve `study.json` günlük çalışmaları taşır. `audio/` ve `images/` dizinleri derleme kaynaklarının yanında, site kökünde bulunur.

## Kurulum

Linux'ta Python 3.10+ ve Pandoc gerekir. PDF yazı tiplerinin Debian/Ubuntu paket adları `fonts-noto-core` ve `fonts-dejavu-core` şeklindedir. HTML üreticisi de PDF üreticisiyle aynı şablonu yüklediği için bu yazı tipleri her iki derleme için kullanılır. Testler için ayrıca Node.js, jsdom ve ffmpeg gerekir.

Site kökünden çalıştırın.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r kaynak/requirements.txt
cd kaynak
```

## PDF ve HTML

```sh
python build_book.py --pdf-only
python build_book.py --html-only
python build_interactive_v4.py --external-audio
python build_site.py
```

- PDF, `output/YDS_Son_5_Gun_Hazirlik_Kitabi.pdf` yoluna yazılır.
- `--html-only` etkileşimli uygulamanın kullanacağı ders gövdesini üretir. Yayımlanacak HTML, bu komutu izleyen `build_interactive_v4.py` komutunun çıktısıdır.
- `build_site.py`, harici medya HTML’sine PDF bağlantısını ekleyerek site kökündeki `index.html` dosyasını üretir. Bağlantı, `kitap/` altındaki dağıtım PDF’sini kullanır. PDF güncellenecekse yeni çıktıyı aynı adla `kitap/` dizinine kopyaladıktan sonra siteyi yeniden üretin. Tarayıcı bu dosyanın yanındaki `audio/` ve `images/` dizinlerini kullanır. Dosyaların SHA-256 değerleri derleme sırasında manifestlerle karşılaştırılır. Yerel önizleme için site kökünden `python -m http.server 8000` çalıştırıp `http://localhost:8000/` adresini açın.

Tek dosyalı çevrimdışı sürümü üretmek için aşağıdaki komutu çalıştırın. Çıktı `output/YDS_Son_5_Gun_Sesli_Etkilesimli_Kitap.html` dosyasıdır. Ses ve görseller bu dosyanın içine gömülür.

```sh
python build_interactive_v4.py
```

## Doğrulama

```sh
python qa_v4/check_release.py --external ../index.html
python qa_v4/check_release.py output/YDS_Son_5_Gun_Sesli_Etkilesimli_Kitap.html
python qa_v4/static_assets.py --all-audio output/YDS_Son_5_Gun_Sesli_Etkilesimli_Kitap.html
```

Node.js 20.19+ ile DOM denetimlerini yalıtılmış bir geçici dizine kurulan jsdom üzerinden çalıştırabilirsiniz.

```sh
qa_node_dir="$(mktemp -d)"
npm install --prefix "$qa_node_dir" jsdom@26.1.0
for test in assessment_bank_test final_dom reading_test; do
  NODE_PATH="$qa_node_dir/node_modules" node "qa_v4/$test.cjs" \
    output/YDS_Son_5_Gun_Sesli_Etkilesimli_Kitap.html || break
done
```

Temel derleme mevcut MP3 dosyalarını kullanır. Sentez modelini indirme veya sesleri yeniden üretme gerektirmez. [Ses üretim bilgisi](SES_KAYNAKLARI.md) ve [ses denetimi](SES_KALITE_DENETIMI.md) kayıtların nasıl hazırlandığını ve hangi kontrollerden geçtiğini açıklar. Tarayıcı oynatıcı olayları DOM testinde benzetilir. Ayrıca gömülü ses baytları ffmpeg ile çözümlenir. PDF'nin bayt düzeyindeki özeti üretim ortamına ve PDF zaman damgasına göre değişebilir.
