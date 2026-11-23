"""Publish the external-media book and the YDS/2 supplement to Pages."""

from pathlib import Path

from build_yds2 import HTML_NAME, PDF_NAME, main as build_supplement

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent
EXTERNAL_HTML = ROOT / 'output' / 'YDS_Son_5_Gun_Sesli_Etkilesimli_Kitap_Harici_Ses.html'
PDF_LINK = './kitap/YDS_Son_5_Gun_Hazirlik_Kitabi.pdf'
HEAD_END = '</head>'
HERO_SPLIT = '</div></div><div class="yds-hero-art" aria-hidden="true">'
DOWNLOAD_STYLE = (
    '<style>.yds-pdf-download{margin:12px 0 0}'
    '.yds-pdf-download a,.yds-exam-supplement a{color:var(--yds-teal);text-underline-offset:.16em}'
    '.yds-exam-supplement{border-left:3px solid var(--yds-teal);margin-top:16px;padding:2px 0 2px 12px}'
    '.yds-exam-supplement strong{display:block}'
    '.yds-exam-supplement a{display:inline-block;margin:4px 10px 0 0}'
    '.yds-pdf-download a:focus-visible,.yds-exam-supplement a:focus-visible'
    '{outline:2px solid currentColor;outline-offset:3px}'
    '</style>'
)


def replace_once(html, marker, replacement):
    if html.count(marker) != 1:
        raise ValueError(f'Expected exactly one Pages insertion point: {marker}')
    return html.replace(marker, replacement, 1)


def main():
    html = EXTERNAL_HTML.read_text(encoding='utf-8')
    build_supplement()
    pdf_mb = round((SITE / PDF_LINK).stat().st_size / 1_000_000)
    download = (
        f'<p class="yds-pdf-download"><a href="{PDF_LINK}" download>'
        'Kitabı PDF olarak indir</a> '
        f'<small class="yds-muted">({pdf_mb} MB)</small></p>'
    )
    supplement = (
        '<div class="yds-exam-supplement">'
        '<strong>22 Kasım 2026 · İngilizce YDS/2 çalışma eki</strong>'
        f'<a href="./{HTML_NAME}">8 alıştırmayı çöz</a> '
        f'<a href="./kitap/{PDF_NAME}" download>Çalışma ekini PDF olarak indir</a>'
        '</div>'
    )
    hero = '</div>' + supplement + download + HERO_SPLIT.removeprefix('</div>')
    html = replace_once(html, HEAD_END, DOWNLOAD_STYLE + HEAD_END)
    html = replace_once(html, HERO_SPLIT, hero)
    (SITE / 'index.html').write_text(html, encoding='utf-8')


if __name__ == '__main__':
    main()
