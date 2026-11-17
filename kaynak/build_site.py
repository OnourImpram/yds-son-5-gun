"""Add the Pages PDF download link to the generated external-media HTML."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent
EXTERNAL_HTML = ROOT / 'output' / 'YDS_Son_5_Gun_Sesli_Etkilesimli_Kitap_Harici_Ses.html'
PDF_LINK = './kitap/YDS_Son_5_Gun_Hazirlik_Kitabi.pdf'
HEAD_END = '</head>'
HERO_SPLIT = '</div></div><div class="yds-hero-art" aria-hidden="true">'
DOWNLOAD_STYLE = (
    '<style>.yds-pdf-download{margin:12px 0 0}'
    '.yds-pdf-download a{color:var(--yds-teal);text-underline-offset:.16em}'
    '.yds-pdf-download a:focus-visible{outline:2px solid currentColor;outline-offset:3px}'
    '</style>'
)


def replace_once(html, marker, replacement):
    if html.count(marker) != 1:
        raise ValueError(f'Expected exactly one Pages insertion point: {marker}')
    return html.replace(marker, replacement, 1)


def main():
    html = EXTERNAL_HTML.read_text(encoding='utf-8')
    pdf_mb = round((SITE / PDF_LINK).stat().st_size / 1_000_000)
    download = (
        f'<p class="yds-pdf-download"><a href="{PDF_LINK}" download>'
        'Kitabı PDF olarak indir</a> '
        f'<small class="yds-muted">({pdf_mb} MB)</small></p>'
    )
    hero = '</div>' + download + HERO_SPLIT.removeprefix('</div>')
    html = replace_once(html, HEAD_END, DOWNLOAD_STYLE + HEAD_END)
    html = replace_once(html, HERO_SPLIT, hero)
    (SITE / 'index.html').write_text(html, encoding='utf-8')


if __name__ == '__main__':
    main()
