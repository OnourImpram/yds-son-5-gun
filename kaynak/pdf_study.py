"""Print-specific navigation and worksheets for the YDS book."""

from functools import lru_cache
import json

from reportlab.platypus import Flowable



@lru_cache(maxsize=1)
def atlas_geometry(catalog):
    source = json.loads(catalog.read_text(encoding='utf-8'))
    geometry = {
        entry['src'].rsplit('/', 1)[-1]: (catalog.parent / entry['src'], entry['width'], entry['height'])
        for entry in source['sources']
    }
    return {
        item['id']: (*geometry[item['atlas']], tuple(item['crop_box']))
        for item in source['items'].values()
    }


def draw_atlas_cell(canvas, catalog, item_id, width, height):
    """Fit a lossless atlas crop to its frame while preserving aspect ratio."""
    path, image_width, image_height, (left, top, right, bottom) = atlas_geometry(catalog)[item_id]
    cell_width, cell_height = right - left, bottom - top
    scale = min(width / cell_width, height / cell_height)
    drawn_width, drawn_height = cell_width * scale, cell_height * scale
    x, y = (width - drawn_width) / 2, (height - drawn_height) / 2

    canvas.saveState()
    boundary = canvas.beginPath()
    boundary.rect(x, y, drawn_width, drawn_height)
    canvas.clipPath(boundary, stroke=0, fill=0)
    canvas.drawImage(str(path), x - left * scale, y - (image_height - bottom) * scale,
                     width=image_width * scale, height=image_height * scale, mask='auto')
    canvas.restoreState()

def destination(flowable, anchor):
    flowable._pdf_destination = anchor
    return flowable


def answer_sheet(*, width, ink, muted, line):
    """One-page, independent first-pass record with no answers visible."""

    class SimulationAnswerSheet(Flowable):
        def __init__(self):
            super().__init__()
            self.width = width
            self.height = 567

        def draw(self):
            c = self.canv
            group_width = self.width / 4
            row_height = 23
            top = 518
            c.setFillColor(ink)
            c.setFont('Body', 9)
            c.drawString(0, 556, 'Başlangıç ____ : ____     Bitiş ____ : ____     Toplam ____ dk')
            c.drawString(0, 536, 'Güven: D = düşük, O = orta, Y = yüksek. Boş bıraktığın maddeye seçenek işaretleme.')
            for group in range(4):
                x = group * group_width
                c.setFillColor(ink)
                c.setFont('BodyBold', 8.2)
                for label, center in [('No.', 10), ('A', 30), ('B', 44), ('C', 58), ('D', 72), ('E', 86), ('Güven', 108)]:
                    c.drawCentredString(x + center, top, label)
                for row in range(20):
                    y = top - (row + 1) * row_height
                    item = group * 20 + row + 1
                    c.setStrokeColor(line)
                    c.setLineWidth(.42)
                    c.line(x + 1, y + 11, x + group_width - 6, y + 11)
                    c.setFillColor(ink)
                    c.setFont('Body', 8.5)
                    c.drawCentredString(x + 10, y - 1, f'{item:02}')
                    c.setStrokeColor(muted)
                    c.setLineWidth(.55)
                    for center in (30, 44, 58, 72, 86):
                        c.circle(x + center, y + 2, 3.45, fill=0, stroke=1)
                    c.line(x + 99, y - 2, x + 117, y - 2)
                c.setStrokeColor(line)
                c.line(x + 1, top - 20 * row_height - 11, x + group_width - 6, top - 20 * row_height - 11)
            c.setFillColor(ink)
            c.setFont('Body', 9)
            c.drawString(0, 26, 'İlk geçişte geri dönülecek maddeler: ___________________________________________')
            c.drawString(0, 6, 'İlk geçiş sonucu     Doğru: ____ / 80     Yanlış: ____     Boş: ____')

    return SimulationAnswerSheet()


def study_blocks(day, title, instructions, heading, paragraph, keep_together, page_break):
    """Give a learner worked contrasts before independent attempts and feedback."""
    number = day['day']
    start = f'study_day{number}'
    key = f'{start}_key'
    items = day['items']
    contrasts = [item for item in items if item['type'] == 'contrast']
    attempts = [item for item in items if item['type'] == 'transfer']
    assert len(contrasts) == len(attempts) == 4, start
    assert {item['pairId'] for item in contrasts} == {item['pairId'] for item in attempts}, start

    def item_anchor(item):
        return f'exercise_{item["pairId"]}_{item["type"]}'

    def item_prompt(item):
        label = item['id']
        yield destination(paragraph(f'**{label} · {item["skill"]}**'), item_anchor(item))
        yield paragraph(item['prompt'])
        for i, option in enumerate(item['options']):
            yield paragraph(f'**{chr(65+i)})** {option}', 'small')

    def feedback(item):
        correct = chr(65 + item['correct'])
        return paragraph(f'**{correct}.** {item["feedback"]}', 'solution')

    out = [
        page_break(),
        heading(title, 2, start, True),
        paragraph(day['focus']),
        paragraph(instructions, 'small'),
        heading('Ayrımı çözümle', 3),
        paragraph('A ve B arasındaki anlam farkını söyle. Ardından doğru seçeneğin gerekçesini oku.'),
    ]
    for item in contrasts:
        out.append(keep_together([*item_prompt(item), feedback(item)]))

    out.extend([
        page_break(),
        heading('Yeni bağlamda dene', 3, f'{start}_attempts'),
        paragraph('Her yeni örneği yardımsız çöz. Seçeneğini ve diğer seçeneği neden elediğini yaz.'),
    ])
    for item in attempts:
        out.append(keep_together([*item_prompt(item),
                                  paragraph('Yanıt: ____   Dayanak: __________________________________________', 'caption')]))
    out.extend([
        paragraph(f'[Dört soruyu bitirdim · değerlendirmeye geç](#{key})', 'small'),
        page_break(),
        heading('Bağımsız uygulama çözümleri', 3, key),
    ])
    contrasts_by_pair = {item['pairId']: item for item in contrasts}
    for item in attempts:
        label = item['id']
        contrast = contrasts_by_pair[item['pairId']]
        out.append(keep_together([
            paragraph(f'**{label} · {item["skill"]}**'),
            feedback(item),
            paragraph(f'[Uygulamaya dön](#{item_anchor(item)}) · [İlgili örneği incele](#{item_anchor(contrast)})', 'small')
        ]))
    return out
