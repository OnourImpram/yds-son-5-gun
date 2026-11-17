"""Check every question, live dataset and media reference against editorial sources."""
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from lxml import html

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT/name).read_bytes())

def whitelist_questions(a):
    return a['diagnostic']+sum(a['daily'].values(),[])+[q for group in a['simulation']['groups'] for q in group['questions']]

def norm(s):
    return ' '.join(s.split())
def check(path, external):
    raw=path.read_bytes()
    key=b'<script>window.YDS_BOOK_DATA='
    start=raw.index(key)+len(key)
    end=raw.index(b';document.querySelectorAll(',start)
    data=json.loads(raw[start:end])
    dom=html.fromstring(raw[:raw.index(b'<script>')]+b'</body></html>',parser=html.HTMLParser(encoding='utf-8',huge_tree=True))
    a=load('assessment.json')
    assert data['assessment']==a and data['vocabulary']==load('vocabulary.json') and data['enrichment']==load('enrichment_v2.json')
    assert data['version']=='4.0'
    marker=b'window.YDS_TRANSFER_CONTENT='
    offset=raw.index(marker)+len(marker)
    assert json.loads(raw[offset:raw.index(b';\n',offset)])==load('study.json')
    assert len(dom.xpath('//article[@class="question"][@data-answer]'))==180
    solutions={i.findtext('summary').split(' ')[0]:i for i in dom.xpath('//details[@class="solution"]')}
    qs=whitelist_questions(a)
    for q in qs:
        tag=dom.get_element_by_id('q_'+q['id'])
        assert int(tag.get('data-answer'))==q['answer'],q['id']
        assert norm(' '.join(tag.xpath('./p')[0].itertext()))==norm(q['id']+' '+q['stem']),q['id']
        assert [norm(str(node.find('strong').tail or '')) for node in tag.xpath('./label[@class="option"]')]==list(map(norm,q['options'])),q['id']
        p=solutions[q['id']].xpath('./p')
        assert norm(p[0].find('strong').tail)==norm(q['rationale']),q['id']
        assert [norm(el.find('strong').tail) for el in p[1:]]==list(map(norm,q['explanations'])),q['id']
    cat=load('visual_catalog_v3.json')['items'];manifest=load('audio_manifest_v2.json')['items']
    valid=0
    def matches(src,expected,sha,media):
        if external:
            assert src==expected, (src,expected)
        else:
            prefix='data:'+media+';base64,'
            assert src.startswith(prefix)
            assert hashlib.sha256(base64.b64decode(src[len(prefix):],validate=True)).hexdigest()==sha
    for key,v in cat.items():
        asset=data['visuals']['items'][key]
        assert (v['width'],v['height'],v['alt'])==(asset['width'],asset['height'],asset['alt'])
        matches(asset['src'],'images/'+key+'.png',v['sha256'],'image/png')
    for key,r in manifest.items():
        for kind in ('word','example','noun'):
            if not r.get(kind): continue
            v=r[kind]
            matches(data['audio']['items'][key][kind]['src'],v['src'],v['sha256'],'audio/mpeg');valid+=1
    assert valid==1537 and len(cat)==176 and len(dom.xpath('//img[@data-vocab-image]'))==352
    return dict(filename=path.name,sha256=hashlib.sha256(raw).hexdigest(),file_bytes=len(raw),questions=len(qs),matched_option_rationales=sum(len(q['explanations']) for q in qs),word_images=len(cat),audios=valid,media_mode='relative' if external else 'inline',study_items=40)
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('html',type=Path)
    parser.add_argument('--external',action='store_true')
    args=parser.parse_args()
    print(json.dumps(check(args.html,args.external),ensure_ascii=False,indent=2))
