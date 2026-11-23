"""Build the November 2026 YDS/2 supplement for the web and for print."""

import json
from html import escape
from pathlib import Path

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer

from build_book import INK, PAGE_H, PAGE_W, ST, TEAL, inline

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent
HTML_NAME = "2026-yds-2.html"
PDF_NAME = "YDS_2026_2_Calisma_Eki.pdf"
PDF_PATH = SITE / "kitap" / PDF_NAME
LETTERS = "ABCDE"


def read_content():
    data = json.loads((ROOT / "content" / "yds2_2026.json").read_text(encoding="utf-8"))
    numbers = [item["number"] for item in data["items"]]
    if len(numbers) != 8 or numbers != sorted(set(numbers)):
        raise ValueError("The supplement must have eight unique official question numbers in order.")
    for item in data["items"]:
        if (
            item["answer"] not in LETTERS
            or item["official_key"] not in LETTERS
            or len(item["options"]) != len(LETTERS)
            or set(item["distractors"]) != set(LETTERS) - {item["answer"]}
            or item["day"] not in range(1, 6)
        ):
            raise ValueError(f"Invalid item structure for official question {item['number']}.")
    return data


def web_text(value):
    return escape(value).replace("\n", "<br>")


def official_page(source, item):
    return f"{source['url']}#page={item['page'] + 2}"


def web_item(item, position, source):
    number = item["number"]
    answer = item["answer"]
    link = escape(official_page(source, item), quote=True)
    title = f"{position}. {web_text(item['type'])}"
    instruction, _, passage = item["prompt"].partition("\n\n")
    options_language = "tr" if item["type"] == "İngilizceden Türkçeye çeviri" else "en"
    options = "\n".join(
        f'<label><input type="radio" name="q{number}" value="{letter}">'
        f'<span><strong>{letter}.</strong> {web_text(option)}</span></label>'
        for letter, option in zip(LETTERS, item["options"], strict=True)
    )
    reasons = "\n".join(
        f"<li><strong>{letter}.</strong> {web_text(item['distractors'][letter])}</li>"
        for letter in LETTERS if letter != answer
    )
    return f"""
<article id="soru-{number}">
  <h2>{title}</h2>
  <p class="meta">Kitap · {item['day']}. gün | <a href="{link}">ÖSYM · {number}. soru, s. {item['page']}</a></p>
  <p class="skill">{web_text(item['skill'])}</p>
  <form data-answer="{answer}">
    <fieldset>
      <legend>{web_text(instruction)}<span class="passage" lang="en">{web_text(passage)}</span></legend>
      <div class="options" lang="{options_language}">{options}</div>
    </fieldset>
    <details class="tip"><summary>İpucunu aç</summary><p>{web_text(item['tip'])}</p></details>
    <button class="check" type="submit">Yanıtı kontrol et</button>
    <p class="feedback" role="status"></p>
    <section class="solution" hidden>
      <h3>Çözüm · {answer}</h3>
      <p>{web_text(item['explanation'])}</p>
      <ul>{reasons}</ul>
      <p class="meta">ÖSYM'nin yayımladığı {number}. sorunun yanıtı · {item['official_key']}</p>
    </section>
  </form>
</article>
"""


def build_html(data):
    template = (ROOT / "content" / "yds2_template.html").read_text(encoding="utf-8")
    values = {
        "TITLE": web_text(data["title"]),
        "INTRO": web_text(data["intro"]),
        "SOURCE_TITLE": web_text(data["source"]["title"]),
        "SOURCE_URL": escape(data["source"]["url"], quote=True),
        "SOURCE_DATE": web_text(data["source"]["date"]),
        "PDF_NAME": PDF_NAME,
        "ITEMS": "\n".join(
            web_item(item, position, data["source"])
            for position, item in enumerate(data["items"], 1)
        ),
    }
    for key, value in values.items():
        template = template.replace(f"@@{key}@@", value)
    (SITE / HTML_NAME).write_text(template, encoding="utf-8")


def build_pdf(data):
    kicker = ParagraphStyle(
        "Supplement eyebrow", parent=ST["small"], fontName="BodyBold", textColor=TEAL,
        fontSize=9, leading=13, spaceAfter=8,
    )
    title = ParagraphStyle("Supplement title", parent=ST["h1"], fontSize=24, spaceAfter=12)
    heading = ParagraphStyle("Supplement question", parent=ST["h3"], spaceBefore=4)
    prompt_style = ParagraphStyle("Supplement prompt", parent=ST["quote"], spaceBefore=14, spaceAfter=14)
    option_style = ParagraphStyle("Supplement option", parent=ST["body"], leftIndent=12, spaceAfter=2)
    credit = ParagraphStyle("Supplement source", parent=ST["small"], spaceBefore=12)

    doc = SimpleDocTemplate(
        str(PDF_PATH), title=data["title"], subject="YDS Son 5 Gün çalışma eki",
        pagesize=(PAGE_W, PAGE_H), leftMargin=48, rightMargin=48, topMargin=62, bottomMargin=53,
        invariant=True, lang="tr",
    )
    source = data["source"]
    source_link = (
        f'<link href="{escape(source["url"], quote=True)}" color="#17615B">'
        f'<u>{inline(source["title"])}</u></link> · {inline(source["date"])}'
    )
    story = [
        Paragraph("YDS SON 5 GÜN • 22 KASIM 2026", kicker),
        Paragraph(inline(data["title"]), title),
        Paragraph(inline(data["intro"]), ST["body"]),
        Paragraph(source_link, credit),
        Spacer(1, 14),
    ]
    for position, item in enumerate(data["items"], 1):
        number = item["number"]
        page_link = escape(official_page(source, item), quote=True)
        question = [
            Paragraph(f"{position}. {inline(item['type'])}", heading),
            Paragraph(
                f'Kitap · {item["day"]}. gün | <link href="{page_link}" color="#17615B">'
                f'<u>ÖSYM · {number}. soru, s. {item["page"]}</u></link>', ST["small"],
            ),
            Paragraph(inline(item["skill"]), ST["small"]),
            Paragraph(inline(item["prompt"]), prompt_style),
        ]
        question.extend(
            Paragraph(f"<b>{letter}.</b> {inline(option)}", option_style)
            for letter, option in zip(LETTERS, item["options"], strict=True)
        )
        question.append(Spacer(1, 12))
        story.append(KeepTogether(question))

    answer_key = " &nbsp;&nbsp; ".join(
        f"{position}. <b>{item['answer']}</b>" for position, item in enumerate(data["items"], 1)
    )
    story.extend([
        PageBreak(),
        Paragraph("YANIT ANAHTARI VE GEREKÇELER", kicker),
        Paragraph("Özgün alıştırmaların çözümleri", title),
        Paragraph(answer_key, ST["body"]),
        Spacer(1, 10),
    ])
    for position, item in enumerate(data["items"], 1):
        solution = [
            Paragraph(f"{position}. {inline(item['type'])} · {item['answer']}", heading),
            Paragraph(f"<b>İpucu</b> · {inline(item['tip'])}", ST["small"]),
            Paragraph(inline(item["explanation"]), ST["body"]),
        ]
        solution.extend(
            Paragraph(f"<b>{letter}.</b> {inline(item['distractors'][letter])}", option_style)
            for letter in LETTERS if letter != item["answer"]
        )
        solution.extend([
            Paragraph(
                f"ÖSYM'nin yayımladığı {item['number']}. sorunun yanıtı · {item['official_key']}", ST["small"]
            ),
            Spacer(1, 12),
        ])
        story.append(KeepTogether(solution))

    def on_page(canvas, current_doc):
        canvas.setStrokeColor(TEAL)
        canvas.setLineWidth(1)
        canvas.line(48, PAGE_H - 39, PAGE_W - 48, PAGE_H - 39)
        canvas.setFillColor(INK)
        canvas.setFont("Body", 8)
        canvas.drawString(48, 32, "YDS Son 5 Gün · 2026 YDS/2 çalışma eki")
        canvas.drawRightString(PAGE_W - 48, 32, str(current_doc.page))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)


def main():
    data = read_content()
    build_html(data)
    build_pdf(data)


if __name__ == "__main__":
    main()
