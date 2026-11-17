#!/usr/bin/env python3
"""Assemble the complete book and its offline audio learning application."""
from __future__ import annotations
import argparse, base64, copy, hashlib, json, re
from pathlib import Path
from lxml import html, etree
from interactive_v3.visual_assets import embedded_visuals

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'output'
LEGACY = OUTPUT / 'YDS_Son_5_Gun_Etkilesimli_Kitap.html'
CHECKPOINT = ROOT / 'interactive_v2' / 'legacy_original.html'

def load(name):
    return json.loads((ROOT / name).read_text())

def js_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')

def selectors(text):
    result, start, depth = [], 0, 0
    for i, ch in enumerate(text):
        if ch in '([': depth += 1
        elif ch in ')]': depth -= 1
        elif ch == ',' and not depth:
            result.append(text[start:i]); start = i+1
    result.append(text[start:])
    return result

def scope_css(css):
    result, pos = [], 0
    while pos < len(css):
        opening = css.find('{', pos)
        if opening < 0:
            result.append(css[pos:]); break
        header = css[pos:opening].strip()
        depth, closing, quote = 1, opening+1, None
        while closing < len(css) and depth:
            c = css[closing]
            if quote:
                if c == quote and css[closing-1] != '\\': quote = None
            elif c in '\"\'': quote = c
            elif c == '{': depth += 1
            elif c == '}': depth -= 1
            closing += 1
        body = css[opening+1:closing-1]
        if header.startswith('@'):
            result.append(header+'{'+scope_css(body)+'}')
        else:
            scoped = []
            for selector in selectors(header):
                selector = selector.strip()
                if selector.startswith('.recall-mode '):
                    scoped.append('body.recall-mode #legacy-book '+selector[len('.recall-mode '):])
                elif selector in ('body', 'html'):
                    scoped.append('#legacy-book')
                elif selector.startswith('body ') or selector.startswith('html '):
                    scoped.append('#legacy-book '+selector[5:])
                else:
                    scoped.append('#legacy-book '+selector)
            result.append(','.join(scoped)+'{'+body+'}')
        pos = closing
    return ''.join(result)

def button(target_id, kind, label, word):
    el=html.Element('button',type='button')
    el.set('class','yds-inline-audio')
    el.set('data-yds-play',target_id)
    el.set('data-yds-kind',kind)
    el.set('aria-label',word+' — '+label)
    el.text='▶ '+label
    return el

def content_text(body):
    return re.sub(r'\s+', ' ', ' '.join(body.itertext())).strip()

def main(edition=3):
    parser=argparse.ArgumentParser()
    parser.add_argument('--partial', action='store_true', help='Allow an intermediate incomplete audio manifest for QA')
    parser.add_argument('--external-audio', action='store_true', help='Keep relative audio src paths for package builds')
    args=parser.parse_args()
    CHECKPOINT.parent.mkdir(exist_ok=True)
    if edition == 4:
        original=LEGACY.read_text()
    elif not CHECKPOINT.exists():
        CHECKPOINT.write_bytes(LEGACY.read_bytes())
    if edition != 4:
        original=CHECKPOINT.read_text()
    style=re.search(r'<style[^>]*>(.*?)</style>',original,re.S).group(1)
    atlas=re.match(r'\s*(:root\{.*?\})', style,re.S).group(1)
    legacy_css=scope_css(style.replace(atlas,'',1))
    original_body=re.search(r'<body[^>]*>(.*?)</body>',original,re.S).group(1)
    scripts=re.findall(r'<script[^>]*>(.*?)</script>',original_body,re.S)
    body_without_scripts=re.sub(r'<script[^>]*>.*?</script>','',original_body,flags=re.S)
    body=html.fragment_fromstring(body_without_scripts,create_parent='section',parser=html.HTMLParser(huge_tree=True))
    original_text=content_text(body)
    body.set('id','legacy-book')
    body.set('aria-label','Hazırlık kitabının tam içeriği')
    vocab=load('vocabulary.json')
    public_images = ROOT.parent / 'images'
    visuals = embedded_visuals(
        ROOT / 'visual_catalog_v3.json',
        published_images=public_images if public_images.is_dir() else None,
    )
    if edition == 4 and args.external_audio:
        for asset_id, item in visuals['items'].items():
            item['src']='images/'+asset_id+'.png'
    # Use ordinary image elements. Large CSS custom properties carrying an
    # entire atlas exceed browser limits, even when the PNG itself is valid.
    legacy_images=body.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," wordimage ")]')
    image_counts={item['id']:0 for item in vocab}
    for old in legacy_images:
        match=re.search(r'--atlas-(\d+)\);background-position:([\d.]+)%\s+([\d.]+)%',old.get('style',''))
        if not match: raise ValueError('Unmapped original vocabulary illustration.')
        atlas_no=int(match.group(1)); col=round(float(match.group(2))*3/100); row=round(float(match.group(3))*3/100)
        target_id=f'V{(atlas_no-1)*16+row*4+col+1:03d}'
        asset=visuals['items'][target_id]
        replacement=html.Element('img',{'class':old.get('class','wordimage'),
            'data-vocab-image':target_id,'alt':asset['alt'],
            'width':str(asset['width']),'height':str(asset['height']),
            'loading':'lazy','decoding':'async'})
        replacement.tail=old.tail
        old.getparent().replace(old,replacement)
        image_counts[target_id]+=1
    if set(image_counts.values())!={2}:
        raise ValueError('Each vocabulary illustration must occur in its card and memory board.')
    supplemental=load('supplemental_audio_targets_v2.json')
    extras_path=ROOT/'additional_audio_targets_v2.json'
    extras=load(extras_path.name) if extras_path.exists() else []
    readings_path=ROOT/'reading_audio_targets_v2.json'
    readings=load(readings_path.name) if readings_path.exists() else []
    audio=load('audio_manifest_v2.json')
    if not args.partial and not audio.get('complete'):
        raise RuntimeError('Audio production has not completed.')
    audio=copy.deepcopy(audio)
    audio_items=audio['items']
    if isinstance(audio_items,list):
        audio_items={r['id']:r for r in audio_items}; audio['items']=audio_items
    if not args.partial:
        expected_ids={r['id'] for r in vocab+supplemental+extras+readings}
        if set(audio_items)!=expected_ids:
            raise ValueError('Audio target inventory differs from the complete book inventory.')
        for target in vocab+supplemental:
            if not all(audio_items[target['id']].get(k) for k in ('word','example')):
                raise ValueError('Missing pronunciation or example: '+target['id'])
        for target in extras+readings:
            if not audio_items[target['id']].get('word'):
                raise ValueError('Missing pronunciation or reading: '+target['id'])
    public_audio = ROOT.parent / 'audio'
    audio_base = ROOT.parent if public_audio.is_dir() else ROOT / 'audio_v2'
    embedded, bytes_total = {}, 0
    for entry in audio_items.values():
        for kind in ['word','example','noun']:
            clip=entry.get(kind)
            if not isinstance(clip,dict) or not clip.get('src'): continue
            path=audio_base/clip['src']
            if not path.is_file():
                raise FileNotFoundError(path)
            blob=path.read_bytes()
            if hashlib.sha256(blob).hexdigest()!=clip['sha256']:
                raise ValueError('Audio hash mismatch: '+str(path))
            if not args.external_audio:
                key=clip['sha256']
                if key not in embedded:
                    embedded[key]='data:audio/mpeg;base64,'+base64.b64encode(blob).decode()
                    bytes_total+=len(blob)
                clip['src']=embedded[key]
        # Variants reuse the named noun entry, without duplicating its base64 data.
        for variant in entry.get('variants',[]):
            if entry.get('noun') and variant.get('sha256')==entry['noun'].get('sha256'):
                variant['src']=''; variant['audio_kind']='noun'
    inserted=[]
    for card in vocab:
        el=body.get_element_by_id(card['id'])
        controls=html.Element('div',{'class':'yds-book-audio'})
        controls.append(button(card['id'],'word','Kelimeyi dinle',card['word']))
        controls.append(button(card['id'],'example','Örnek cümleyi dinle',card['word']))
        row=audio_items.get(card['id'],{})
        if row.get('noun'):
            controls.append(button(card['id'],'noun','İsim biçimini dinle',card['word']))
            note=html.Element('small'); note.text=' Ana ses fiil biçimidir; isim kaydını ayrıca karşılaştır.'; controls.append(note)
        el.insert(1,controls); inserted.append(controls)
    for item in supplemental:
        matches=body.xpath('.//p[strong[starts-with(normalize-space(.),$key)]]',key=item['id']+' —')
        if len(matches)!=1: raise ValueError('Supplemental target location is not unique: '+item['id'])
        p=matches[0]
        controls=html.Element('span',{'class':'yds-book-audio'})
        controls.append(button(item['id'],'word','Kalıbı dinle',item['word']))
        controls.append(button(item['id'],'example','Örneği dinle',item['word']))
        p.addnext(controls); inserted.append(controls)
    for item in readings:
        matches=body.xpath('.//h3[normalize-space(.)=$title]',title=item['word'])
        if len(matches)!=1: raise ValueError('Reading heading is not unique: '+item['word'])
        controls=html.Element('div',{'class':'yds-book-audio'})
        controls.append(button(item['id'],'word','Okuma metnini dinle',item['word']))
        matches[0].addnext(controls); inserted.append(controls)
    # A pronunciation panel keeps every listed family member and card collocation reachable.
    extra_by_word={v['word'].casefold():v for v in extras}
    target_by_word={v['word'].casefold():v for v in vocab+supplemental+extras}
    if extras:
        for card in vocab:
            el=body.get_element_by_id(card['id'])
            details=html.Element('details',{'class':'yds-family-audio'})
            summary=etree.SubElement(details,'summary'); summary.text='Sözcük ailesini ve birlikte kullanılan kalıpları dinle'
            for field,title in [('family','Sözcük ailesi'),('collocations','Birlikte kullanılan kalıplar')]:
                section=etree.SubElement(details,'div')
                h=etree.SubElement(section,'p'); h.text=title
                for text in card[field]:
                    t=target_by_word.get(text.casefold())
                    if t: section.append(button(t['id'],'word',text,text))
            el.append(details); inserted.append(details)
    # The source text is unchanged; all additional controls are excluded from this check.
    verification=copy.deepcopy(body)
    for e in verification.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," yds-book-audio ") or contains(concat(" ",normalize-space(@class)," ")," yds-family-audio ")]'):
        e.getparent().remove(e)
    assert content_text(verification)==original_text, 'Original instructional text changed.'
    legacy_html=html.tostring(body,encoding='unicode',method='html')
    legacy_js='\n'.join(scripts).replace('document.querySelectorAll(',"document.getElementById('legacy-book').querySelectorAll(")
    legacy_js += r'''
window.YDSLegacyBridge=(function(){
  const root=document.getElementById('legacy-book');
  const LIMIT=100000,marker='\n\n[İçe aktarılan yedekteki farklı metin]\n';
  let lastReport={textConflicts:0,imported:0,preserved:0,unmergedConflicts:0};
  function fields(){const map=new Map();root.querySelectorAll('input[type=radio]').forEach(el=>{if(!map.has(el.name))map.set(el.name,{type:'radio',elements:[],allowed:[]});const r=map.get(el.name);r.elements.push(el);r.allowed.push(el.value)});root.querySelectorAll('[data-note],[data-memory],[data-confidence]').forEach(el=>{const k=el.dataset.note||el.dataset.memory||('conf-'+el.dataset.confidence);map.set(k,{type:el.tagName==='SELECT'?'select':'text',note:el.hasAttribute('data-note'),elements:[el],allowed:el.tagName==='SELECT'?Array.from(el.options).map(o=>o.value):null})});return map}
  return {
    exportState:function(){const out={};fields().forEach((r,k)=>{const v=state[k];if(typeof v==='string'&&v.length<=LIMIT&&(!r.allowed||r.allowed.includes(v)))out[k]=v});return out},
    getLastImportReport:function(){return Object.assign({},lastReport)},
    importState:function(raw,options){
      lastReport={textConflicts:0,imported:0,preserved:0,unmergedConflicts:0};
      if(!raw||typeof raw!=='object'||Array.isArray(raw))return 0;
      options=options||{};
      fields().forEach((r,k)=>{
        if(!Object.prototype.hasOwnProperty.call(raw,k))return;
        let v=raw[k];
        if(typeof v!=='string'||v.length>LIMIT||(r.allowed&&!r.allowed.includes(v)))return;
        const old=typeof state[k]==='string'?state[k]:'';
        if(options.preserveConflicts&&old&&old!==v){
          if(r.note){
            if(!v||old.endsWith(marker+v)||old.includes(marker+v+marker)){lastReport.preserved++;return}
            const merged=old+marker+v;
            if(merged.length>LIMIT){lastReport.unmergedConflicts++;lastReport.preserved++;return}
            v=merged;lastReport.textConflicts++;
          }else if(options.preferExisting){lastReport.preserved++;return}
        }
        state[k]=v;r.elements.forEach(el=>{if(r.type==='radio')el.checked=el.value===v;else el.value=v});lastReport.imported++;
      });
      persist();return lastReport.imported;
    }
  }
})();
'''
    data={'version':('4.0' if edition == 4 else '3.0'),'vocabulary':vocab,'assessment':load('assessment.json'),
          'enrichment':load('enrichment_v2.json'),'audio':audio,'supplemental':supplemental+extras+readings,
          'visuals':visuals}
    app_css=(ROOT/'interactive_v2/app.css').read_text()
    app_js=(ROOT/'interactive_v2/app.js').read_text()
    base_css='body{margin:0;background:#f7f5ef}html{scroll-behavior:smooth}[hidden]{display:none!important}.yds-book-audio{display:block;margin:.8rem 0}#legacy-book .yds-inline-audio{font-size:.85rem}#legacy-book .yds-family-audio button{font-size:.8rem;margin:.2rem}#legacy-book img.wordimage{display:block;height:auto;aspect-ratio:auto;object-fit:contain;background:none;max-width:100%}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}'
    hydration='document.querySelectorAll("#legacy-book img[data-vocab-image]").forEach(function(img){var asset=window.YDS_BOOK_DATA.visuals.items[img.dataset.vocabImage];if(asset)img.src=asset.src;});'
    assembled='<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><title>YDS Son 5 Gün · Görselli ve Sesli Etkileşimli Kitap</title><style>'+legacy_css+base_css+app_css+'</style></head><body><div id="yds-app"><p style="padding:2rem;font:1rem system-ui">Görselli ve sesli kitap açılıyor…</p></div>'+legacy_html+'<script>(function(){'+legacy_js+'})();</script><script>'+app_js+'</script><script>window.YDS_BOOK_DATA='+'__YDS_V4_DATA__'+';'+hydration+'window.YDSApp.init({root:document.getElementById("yds-app"),bookRoot:document.getElementById("legacy-book"),data:window.YDS_BOOK_DATA});</script></body></html>'
    if edition == 4:
        from interactive_v4.edition import assemble
        assembled=assemble(assembled,load('study.json'),load('assessment_v3_archive.json'),data['assessment'])
    if assembled.count('__YDS_V4_DATA__')!=1:
        raise ValueError('Missing unique runtime data slot')
    assembled=assembled.replace('__YDS_V4_DATA__',js_json(data),1)
    OUTPUT.mkdir(exist_ok=True)
    filename='YDS_Son_5_Gun_Sesli_Etkilesimli_Kitap'+('_Harici_Ses' if args.external_audio else '')+'.html'
    dest=OUTPUT/filename
    dest.write_text(assembled)
    # Lightweight fixture has the same DOM and code; omits only media payloads for logic QA.
    fixture=re.sub(r'data:image/png;base64,[A-Za-z0-9+/=]+','data:image/png;base64,',assembled)
    fixture=re.sub(r'data:audio/mpeg;base64,[A-Za-z0-9+/=]+','data:audio/mpeg;base64,',fixture)
    (ROOT/('qa_v4' if edition==4 else 'qa_v3')).mkdir(exist_ok=True)
    (ROOT/('qa_v4' if edition==4 else 'qa_v3')/('interactive_fixture_external.html' if args.external_audio else 'interactive_fixture.html')).write_text(fixture)
    report={'output':str(dest),'bytes':dest.stat().st_size,'vocabulary_cards':len(vocab),
            'supplemental_targets':len(supplemental),'additional_pronunciation_targets':len(extras),
            'audio_readings':len(readings),
            'audio_targets_in_manifest':len(audio_items),'embedded_unique_audio_files':len(embedded),
            'embedded_audio_bytes':bytes_total,'source_text_sha256':hashlib.sha256(original_text.encode()).hexdigest(),
            'original_instructional_text_preserved':True,'inline_audio_controls':len(body.xpath('.//button[@data-yds-play]')),
            'visuals':{'unique_images':len(visuals['items']),'native_legacy_image_elements':len(legacy_images),
                       'supplemental_associations':len(visuals.get('associations',{})),
                       'oversized_css_atlas_variables_removed':True,
                       'maximum_image_data_url_chars':max(len(v['src']) for v in visuals['items'].values())},
            'partial':args.partial,'external_audio':args.external_audio}
    (ROOT/('qa_v4' if edition==4 else 'qa_v3')/('build_report_external.json' if args.external_audio else 'build_report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
