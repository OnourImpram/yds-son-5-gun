from pathlib import Path
import json,re,html,base64,csv,collections,math,os
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether,Flowable,CondPageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,Color,white
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing,Rect,String,Line,Polygon,Circle
from reportlab.graphics import renderSVG,renderPDF
from PIL import Image as PILImage
from pdf_study import answer_sheet, destination, draw_atlas_cell, study_blocks

B=Path(__file__).parent;OUT=Path(os.environ.get('YDS_OUTPUT',B/'output'));AS=B/'assets'
OUT.mkdir(parents=True,exist_ok=True);AS.mkdir(exist_ok=True)
for name,file in [('Body','NotoSans-Regular.ttf'),('BodyBold','NotoSans-Bold.ttf'),('BodyItalic','NotoSans-Italic.ttf'),('BodyBI','NotoSans-BoldItalic.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/noto/'+file))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='BodyItalic',boldItalic='BodyBI')
pdfmetrics.registerFont(TTFont('Symbols','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('SymbolsBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('Symbols',normal='Symbols',bold='SymbolsBold',italic='Symbols',boldItalic='SymbolsBold')
INK=HexColor('#16334B');TEAL=HexColor('#237B76');GOLD=HexColor('#C88B2D');PALE=HexColor('#EEF5F3');GREY=HexColor('#52616A');BORDER=HexColor('#CCD8DC');PAPER=HexColor('#FCFAF6')
PAGE_W,PAGE_H=A4;M=43;W=PAGE_W-2*M
ST={
'body':ParagraphStyle('body',fontName='Body',fontSize=10.1,leading=14.6,textColor=INK,spaceAfter=7,allowWidows=0,allowOrphans=0),
'small':ParagraphStyle('small',fontName='Body',fontSize=8.9,leading=12.6,textColor=INK,spaceAfter=5),
'h1':ParagraphStyle('h1',fontName='BodyBold',fontSize=23,leading=29,textColor=INK,spaceBefore=5,spaceAfter=18,keepWithNext=True),
'h2':ParagraphStyle('h2',fontName='BodyBold',fontSize=15.5,leading=20,textColor=TEAL,spaceBefore=15,spaceAfter=9,keepWithNext=True),
'h3':ParagraphStyle('h3',fontName='BodyBold',fontSize=12,leading=16.5,textColor=INK,spaceBefore=12,spaceAfter=6,keepWithNext=True),
'h4':ParagraphStyle('h4',fontName='BodyBold',fontSize=10.5,leading=15,textColor=INK,spaceBefore=9,spaceAfter=5,keepWithNext=True),
'caption':ParagraphStyle('caption',fontName='BodyItalic',fontSize=8.3,leading=11.5,textColor=GREY,spaceAfter=10),
'quote':ParagraphStyle('quote',fontName='Body',fontSize=10.1,leading=14.6,textColor=INK,leftIndent=12,rightIndent=8,borderColor=BORDER,borderWidth=0.5,borderPadding=9,backColor=PALE,spaceBefore=5,spaceAfter=10),
'table':ParagraphStyle('table',fontName='Body',fontSize=8.4,leading=11.7,textColor=INK),
'tablehead':ParagraphStyle('tablehead',fontName='BodyBold',fontSize=8.5,leading=11.5,textColor=white),
'cardtitle':ParagraphStyle('cardtitle',fontName='BodyBold',fontSize=15,leading=19,textColor=TEAL,spaceAfter=7),
'solution':ParagraphStyle('solution',fontName='Body',fontSize=9.5,leading=13.6,textColor=INK,spaceAfter=5),
}

def clean(s):
    return str(s).replace('\u00ad','').replace('\u2011','-').replace('\u200b','').replace('\u202f',' ')

def inline(s):
    s=html.escape(clean(s),quote=False)
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)',r'<i>\1</i>',s)
    s=re.sub(r'`([^`]+)`',r'<font color="#237B76">\1</font>',s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',r'<link href="\2" color="#237B76">\1</link>',s)
    s=re.sub(r'\[([^\]]+)\]\(#([A-Za-z0-9_-]+)\)',r'<link href="#\2" color="#237B76"><u>\1</u></link>',s)
    return s.replace('→','<font name="Symbols">→</font>').replace('\n','<br/>')

def P(s,style='body'):
    return Paragraph(inline(s),ST[style])

counter=collections.Counter()
def heading(text,level=2,anchor=None,toc=False):
    level=max(1,min(level,4));p=P(text,'h'+str(level));counter['headings']+=1
    p._bookmark=anchor or 'head_'+str(counter['headings'])
    p._headtext=clean(re.sub(r'[*`]+','',text));p._level=level;p._toc=toc
    return p

def wraptext(s,maxw,fontsize=9,font='Body'):
    lines=[]
    for raw in str(s).split('\n'):
        line=''
        for word in raw.split():
            trial=(line+' '+word).strip()
            if pdfmetrics.stringWidth(trial,font,fontsize)>maxw and line:
                lines.append(line);line=word
            else:line=trial
        lines.append(line)
    return lines

def drawtext(d,s,x,y,maxw,fs=9,bold=False,color=INK,center=False):
    font=('SymbolsBold' if bold else 'Symbols') if '→' in str(s) else ('BodyBold' if bold else 'Body');lines=wraptext(s,maxw,fs,font)
    for i,line in enumerate(lines):d.add(String(x+(maxw/2 if center else 0),y-i*fs*1.35,line,fontName=font,fontSize=fs,fillColor=color,textAnchor='middle' if center else 'start'))
    return len(lines)*fs*1.35

def make_diagram(spec):
    width=W;typ=spec['type'];title=spec.get('title','')
    if typ=='grid':
        cols=spec['columns'];rows=spec['rows'];n=len(cols);cw=width/n
        fs=8.5 if n>=4 else 9.0
        allrows=[cols]+rows
        heights=[max(len(wraptext(cell,cw-18,fs,'BodyBold' if i==0 else 'Body')) for cell in row)*fs*1.35+18 for i,row in enumerate(allrows)]
        height=sum(heights)+38;d=Drawing(width,height);drawtext(d,title,0,height-15,width,11.5,True)
        y=height-34
        for ri,(row,rh) in enumerate(zip(allrows,heights)):
            for ci,cell in enumerate(row):
                d.add(Rect(ci*cw,y-rh,cw,rh,fillColor=TEAL if ri==0 else (PALE if ri%2 else white),strokeColor=BORDER,strokeWidth=.5))
                drawtext(d,cell,ci*cw+9,y-14,cw-18,fs,ri==0,white if ri==0 else INK)
            y-=rh
    elif typ=='contrast':
        ps=spec['panels'];gap=14;cw=(width-gap)/2;heights=[]
        for p in ps:
            heights.append(36+len(wraptext(p.get('sentence',''),cw-24,9.6))*13+len(wraptext(p.get('meaning',''),cw-24,8.7))*12+25)
        h=max(heights);height=h+38;d=Drawing(width,height);drawtext(d,title,0,height-15,width,11.5,True)
        for i,p in enumerate(ps):
            x=i*(cw+gap);d.add(Rect(x,3,cw,h,rx=7,ry=7,fillColor=PALE if i==0 else PAPER,strokeColor=BORDER,strokeWidth=.7))
            y=h-14;drawtext(d,p['label'],x+12,y,cw-24,10,True,TEAL);y-=25
            y-=drawtext(d,p.get('sentence',''),x+12,y,cw-24,9.6);y-=12
            drawtext(d,p.get('meaning',''),x+12,y,cw-24,8.7,False,GREY)
    elif typ=='flow':
        nodes=spec['nodes'];n=len(nodes);gap=12;cw=(width-gap*(n-1))/n;fs=8.7
        hs=[len(wraptext(x,cw-16,fs))*12+25 for x in nodes];boxh=max(hs);notes=spec.get('notes',[])
        nh=sum(len(wraptext(x,width-18,8.5))*12+4 for x in notes)
        height=boxh+nh+57;d=Drawing(width,height);drawtext(d,title,0,height-15,width,11.5,True)
        y=height-38-boxh
        for i,node in enumerate(nodes):
            x=i*(cw+gap);d.add(Rect(x,y,cw,boxh,rx=6,ry=6,fillColor=PALE,strokeColor=TEAL,strokeWidth=.7));drawtext(d,node,x+8,y+boxh-17,cw-16,fs,True,INK,True)
        for a,b in spec.get('edges',[]):
            x1=(a+1)*cw+a*gap;x2=b*(cw+gap);yy=y+boxh/2
            if b>a+1:
                top=y+boxh+8
                d.add(Line(x1-8,y+boxh,x1-8,top,strokeColor=GOLD,strokeWidth=1.3));d.add(Line(x1-8,top,x2+8,top,strokeColor=GOLD,strokeWidth=1.3));d.add(Line(x2+8,top,x2+8,y+boxh+3,strokeColor=GOLD,strokeWidth=1.3));d.add(Polygon([x2+8,y+boxh+1,x2+4,y+boxh+6,x2+12,y+boxh+6],fillColor=GOLD,strokeColor=GOLD))
            else:
                d.add(Line(x1,yy,x2-3,yy,strokeColor=GOLD,strokeWidth=1.3));d.add(Polygon([x2-3,yy,x2-7,yy+3,x2-7,yy-3],fillColor=GOLD,strokeColor=GOLD))
        yy=y-17
        for note in notes:yy-=drawtext(d,'• '+note,6,yy,width-12,8.5,False,GREY)+4
    else:raise ValueError(typ)
    d.hAlign='CENTER';return d

DIAGRAMS={}
def load_diagrams():
    path=B/'grammar_manifest.json'
    if path.exists():
        for spec in json.loads(path.read_text())['diagrams']:
            if spec['key']=='g2_connector':spec['columns'][1]='Öbek veya mastar'
            d=make_diagram(spec);DIAGRAMS[spec['key']]=d;renderSVG.drawToFile(d,str(AS/(spec['key']+'.svg')))
    extra=[
    {'key':'lex_morphology','type':'grid','title':'Parça ile sözcüğün görevini birlikte gör','columns':['Parçalar','Birleşik biçim','Anlam ve görev'],'rows':[['re- + assess + -ment','reassessment','yeniden değerlendirme · isim'],['un- + reliable','unreliable','güvenilir olmayan · sıfat'],['accurate + -ly','accurately','doğru biçimde · zarf'],['interpret + -ation','interpretation','yorum · isim']]},
    {'key':'lex_prepositions','type':'grid','title':'Edat için başlangıç haritası','columns':['İpucu','Örnek','Korunacak ilişki'],'rows':[['FROM · kaynak','arise from a problem','sorundan doğmak'],['TO · hedef','contribute to improvement','iyileşmeye katkı'],['WITH · beraberlik','provide people with tools','insanlara araç sağlamak'],['ON · dayanma','depend on evidence','kanıta bağlı olmak'],['FOR · amaç / yarar','allocate funds for repairs','onarım için ayırmak'],['IN · alan / katılım','participate in a study','araştırmaya katılmak']]},
    {'key':'lex_research','type':'grid','title':'Araştırma odasında bilgi akışı','columns':['Adım','Sözcükler','Kontrol'],'rows':[['Soru sor ve incele','investigate · carry out','ne inceleniyor?'],['Veriyi elde et','obtain · measure','nasıl ölçülüyor?'],['Anlamlandır ve denetle','interpret · verify','hangi dayanak var?'],['İletişim yönünü koru','author implies / reader infers','yazar ima eder / okur çıkarır']]},
    {'key':'lex_change','type':'grid','title':'Değişim atölyesinde üç eksen','columns':['Başlangıç ve süre','Kolaylık ve engel','Zararın derecesi'],'rows':[['trigger · başlat','facilitate · kolaylaştır','mitigate · azalt'],['sustain · sürdür','hinder · engelle','exacerbate · ağırlaştır'],['cease · sona er','prevent · önle','alleviate · hafiflet']]},
    {'key':'lex_resources','type':'grid','title':'Kaynağın yolculuğu','columns':['Kaynak işlemi','Örnek','Karşı yön'],'rows':[['acquire · edin','araç edinmek','elde olmaması'],['allocate · tahsis et','bütçe ayırmak','paylaştırmamak'],['distribute · dağıt','malzeme dağıtmak','tek yerde toplamak'],['consume · tüket','enerji kullanmak','conserve · korumak'],['deplete · tüketip azalt','stokları eritmek','replenish · yeniden doldurmak']]},
    {'key':'lex_argument','type':'grid','title':'İddiayı gerekçeye bağla','columns':['İşlem','Sözcük','Sınır'],'rows':[['İddia kur','claim · assert · contend','iddia henüz kanıt değildir'],['Dayanak veya itiraz getir','support · challenge','desteklemek kesinleştirmez'],['Gerekçelendir veya çürüt','justify · refute','sorgulamak çürütmek değildir'],['Olasılığı koru','cannot rule out','dışlayamamak kanıtlamak değildir'],['Makul bul','plausible','makul olan kesin olmak zorunda değildir']]},
    {'key':'memory_rooms','type':'grid','title':'Dört hafıza mekânı','columns':['Araştırma odası','Değişim atölyesi','Kent ve doğa','Tartışma salonu'],'rows':[['kanıt · ölçüm · örneklem','neden · engel · dönüşüm','kaynak · toplum · çevre','iddia · sınır · gerekçe'],['V001–V040','V041–V080','V081–V120','V121–V160'],['Salı + V161–164','Çarşamba + V165–168','Perşembe + V169–172','Cuma + V173–176']]},
    {'key':'time_reference','type':'grid','title':'Olay zamanı ve bakış noktası','columns':['Olay','Referans','Yapı'],'rows':[['geçmişte bitti','şimdiyle bağlantı','has finished'],['daha önce bitti','geçmişteki ikinci nokta','had finished'],['önce tamamlanacak','gelecekteki son tarih','will have finished'],['geçmişte olmuş olabilir','şimdiki çıkarım','may have finished']]},
    {'key':'evidence_scope','type':'grid','title':'Metnin izin verdiği iddia','columns':['Metin','Korunabilen yorum','Eklenemeyen kesinlik'],'rows':[['may help','yardımcı olabilir','kesinlikle yardımcı olur'],['some participants','katılımcıların bir bölümü','bütün katılımcılar'],['associated with','ilişkili','neden olur'],['not necessarily','zorunlu olarak değil','hiçbir zaman değil']]},
    {'key':'connector_bridge','type':'grid','title':'Boşluğun iki kıyısını birleştir','columns':['Önceki cümle','Boşluğun işi','Sonraki cümle'],'rows':[['bir güçlük','güçlüğü somutlaştır','bu güçlüğe rağmen yarar'],['bir iddia','kanıt veya örnek','dolayısıyla sonuç'],['bir olay','açıklama veya bağ','this / such / these ile gönderim']]}
    ]
    for s in extra:
        d=make_diagram(s);DIAGRAMS[s['key']]=d;renderSVG.drawToFile(d,str(AS/(s['key']+'.svg')))
    d=Drawing(W,338);drawtext(d,'Zaman çizgisinde olay ve bakış noktası',0,320,W,11.5,True)
    tracks=[('has finished',260,459,'bitirme','şimdi','Tamamlanan olayın şimdiyle bağlantısı',0),('had finished',215,350,'önce bitirme','geçmiş referans','Geçmişteki ikinci olaydan önce tamamlanma',1),('will have finished',355,470,'bitirme','gelecek son tarih','Gelecekteki referans noktasına kadar tamamlanma',2),('may have finished',260,459,'olası bitirme','şimdiki çıkarım','Geçmiş olayın olasılığı hakkında değerlendirme',3)]
    for label,event,ref,el,rl,note,idx in tracks:
        y=275-idx*73;drawtext(d,label,0,y+6,130,9.3,True,TEAL)
        d.add(Line(143,y,500,y,strokeColor=BORDER,strokeWidth=1.5));d.add(Polygon([505,y,498,y+3,498,y-3],fillColor=GREY,strokeColor=GREY))
        d.add(Circle(event,y,4,fillColor=GOLD,strokeColor=GOLD));d.add(Line(ref,y-8,ref,y+8,strokeColor=TEAL,strokeWidth=1.5))
        drawtext(d,el,event-45,y+16,95,8.1,False,INK,True);drawtext(d,rl,ref-45,y-20,92,8.1,False,TEAL,True)
        drawtext(d,note,143,y-40,355,8.4,False,GREY)
        if idx==1:drawtext(d,'şimdi',460,y+16,42,8,False,GREY,True)
        if idx==2:drawtext(d,'şimdi',145,y+16,48,8,False,GREY,True)
    d.hAlign='CENTER';DIAGRAMS['time_reference']=d;renderSVG.drawToFile(d,str(AS/'time_reference.svg'))

def md_blocks(text):
    lines=text.splitlines();i=0;out=[]
    while i<len(lines):
        s=lines[i].strip()
        if not s:i+=1;continue
        m=re.match(r'^(#{1,6})\s+(.+)',s)
        if m:out.append(heading(m[2],min(4,len(m[1]))));i+=1;continue
        im=re.match(r'^!\[(.*?)\]\(diagram:([^)]+)\)$',s)
        if im:
            key=im[2]
            if key not in DIAGRAMS:raise ValueError('Missing diagram '+key)
            out.extend([Spacer(1,7),DIAGRAMS[key],P(im[1],'caption')]);i+=1;continue
        if s.startswith('|') and i+1<len(lines) and re.match(r'^\s*\|?[\s:|-]+\|',lines[i+1]):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                raw=lines[i].strip()
                if not re.fullmatch(r'[\s|:-]+',raw):rows.append([x.strip() for x in raw.strip('|').split('|')])
                i+=1
            n=max(len(x) for x in rows);rows=[r+['']*(n-len(r)) for r in rows]
            if n==2:widths=[W*.31,W*.69]
            elif n==3:widths=[W*.25,W*.36,W*.39]
            elif n==4:widths=[W*.21,W*.24,W*.27,W*.28]
            elif n==5:widths=[W*.28,W*.18,W*.18,W*.18,W*.18]
            else:widths=[W/n]*n
            ts=Table([[P(x,'tablehead' if ri==0 else 'table') for x in r] for ri,r in enumerate(rows)],colWidths=widths,repeatRows=1,hAlign='LEFT')
            ts.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,PALE]),('GRID',(0,0),(-1,-1),.5,BORDER),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            out.extend([Spacer(1,5),ts,Spacer(1,10)]);continue
        if s.startswith('```'):
            arr=[];i+=1
            while i<len(lines) and not lines[i].strip().startswith('```'):arr.append(lines[i]);i+=1
            out.append(P('\n'.join(arr),'quote'));i+=1;continue
        if re.match(r'^[-_*]{3,}$',s):out.append(Spacer(1,8));i+=1;continue
        if s.startswith('>'):
            arr=[]
            while i<len(lines) and lines[i].strip().startswith('>'):arr.append(lines[i].strip()[1:].lstrip());i+=1
            out.append(P('\n'.join(arr),'quote'));continue
        if re.match(r'^[-*+]\s+',s) or re.match(r'^\d+[.)]\s+',s):
            out.append(P(s,'body'));i+=1;continue
        arr=[s];i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#{1,6}\s|!\[|\||>|```|[-*+]\s|\d+[.)]\s)',lines[i].strip()):arr.append(lines[i].strip());i+=1
        out.append(P(' '.join(arr),'body'))
    return out

class CellImage(Flowable):
    def __init__(self,idx,width=126):
        super().__init__();self.idx=idx;self.width=width;self.height=width*.75
    def draw(self):
        draw_atlas_cell(self.canv,B/'visual_catalog_v3.json',
                        f'V{self.idx:03d}',self.width,self.height)

class MemoryBoard(Flowable):
    def __init__(self,start,show_words=False,vocab=None):
        super().__init__();self.start=start;self.width=W;self.height=570;self.show_words=show_words;self.vocab=vocab or {}
    def draw(self):
        c=self.canv;gap=9;cw=(W-3*gap)/4;ch=137
        for j in range(16):
            idx=self.start+j
            if idx>176:continue
            row,col=divmod(j,4);x=col*(cw+gap);y=self.height-(row+1)*ch
            im=CellImage(idx,cw);im.drawOn(c,x,y+35)
            c.setFont('BodyBold',8.2);c.setFillColor(INK)
            label=f'V{idx:03d}'
            if self.show_words:label+=' '+self.vocab[label]['word']
            c.drawString(x,y+22,label);c.setStrokeColor(BORDER);c.line(x,y+9,x+cw,y+9)

def card(v):
    idx=int(v['id'][1:]);title=P(v['id']+'   '+v['word'],'cardtitle')
    side=[title,P('**'+v['meaning']+'** · '+v.get('pos',''),'small'),P('**Görsel:** '+v['visual_scene'],'small'),P('**Hafıza hikâyesi:** '+v['mnemonic_story'],'small')]
    top=Table([[CellImage(idx,127),side]],colWidths=[140,W-18-140]);top.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    def joinval(x):return '; '.join(map(str,x)) if isinstance(x,list) else str(x)
    body=[top,P('**Çağrışım ve ilişkili biçimler:** '+v['association']+' | '+joinval(v.get('family',[])),'small'),P('**Örnek:** '+v['example']+'\n'+v['translation'],'small'),P('**Yeni bağlam:** '+v['transfer_example']+'\n'+v['transfer_translation'],'small'),P('**Sınav kullanımı:** '+v['exam_context'],'small'),P('**Birlikte öğren:** '+joinval(v.get('collocations',[])),'small'),P('**Karıştırma:** '+v['confusion'],'small'),P('**Hatırla:** '+v['recall_prompt'],'small')]
    if v.get('source_refs'):body.append(P('**Kaynak gözlemi:** '+joinval(v['source_refs']),'caption'))
    t=Table([[body]],colWidths=[W]);t.setStyle(TableStyle([('BOX',(0,0),(-1,-1),.6,BORDER),('BACKGROUND',(0,0),(-1,-1),white),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return [destination(t,'card_'+v['id']),Spacer(1,11)]

def question(q,group=None):
    label=q['id']
    items=[destination(P('**'+label+'**  '+q['stem']),'question_'+label)]
    if q.get('passage'):items.insert(0,destination(P(q['passage'],'quote'),'passage_'+label))
    for j,opt in enumerate(q['options']):items.append(P(f'**{chr(65+j)})** {opt}','body'))
    links=[f'[Çözüm](#solution_{label})']
    if group and group.get('passage'):
        links.insert(0,f'[Ortak metin](#group_{group["id"]})')
    items.append(P('Yanıt: _____   Güven: düşük / orta / yüksek   Dayanak: ______________  ·  '+' · '.join(links),'caption'))
    counter['mcq']+=1
    return [KeepTogether(items),Spacer(1,5)]

def solution(q,group=None):
    label=q['id']
    correct=chr(65+q['answer'])
    items=[destination(P('**'+label+' · '+correct+'**  '+q.get('rationale',''),'solution'),'solution_'+label)]
    for i,exp in enumerate(q['explanations']):items.append(P('**'+chr(65+i)+(' doğru' if i==q['answer'] else ' yanlış')+':** '+exp,'solution'))
    target='passage_' if q.get('passage') else 'question_'
    links=[f'[Soruya dön](#{target}{label})']
    if group and group.get('passage'):
        links.append(f'[Ortak metin](#group_{group["id"]})')
    items.append(P('Beceri: '+q.get('skill',q.get('type',''))+' · Hata kaynağını K/G/B/Ç/R/D/Z ile işaretle. · '+' · '.join(links),'caption'))
    return [KeepTogether(items),Spacer(1,7)]

def assessment_key(qs):
    columns=8 if len(qs)>20 else 5
    rows=[]
    for start in range(0,len(qs),columns):
        row=[]
        for q in qs[start:start+columns]:
            row.append(P(f'[{q["id"]}](#solution_{q["id"]}) · **{chr(65+q["answer"])}**','small'))
        rows.append(row+['']*(columns-len(row)))
    key=Table(rows,colWidths=[W/columns]*columns,hAlign='LEFT')
    key.setStyle(TableStyle([('ROWBACKGROUNDS',(0,0),(-1,-1),[PALE,white]),
                             ('GRID',(0,0),(-1,-1),.35,BORDER),
                             ('TOPPADDING',(0,0),(-1,-1),6),
                             ('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    return key


def assessment_block(title,qs,anchor):
    arr=[heading(title,2,anchor,True),P('Önce yanıtı ve güven düzeyini kaydet. Çözümler bu testin bütün sorularından sonra başlar. Her soru için tek bir en uygun seçenek vardır.')]
    for q in qs:arr+=question(q)
    arr += [PageBreak(),heading(title+' açıklamalı çözümler',2,anchor+'_solutions',True),
            P(f'[Testin başına dön](#{anchor})','small'),assessment_key(qs),Spacer(1,12)]
    for q in qs:arr+=solution(q)
    return arr

class BookDoc(BaseDocTemplate):
    def __init__(self,path,**kwargs):
        super().__init__(path,pagesize=A4,leftMargin=M,rightMargin=M,topMargin=49,bottomMargin=47,**kwargs)
        self.chapter='YDS Son 5 Gün';self.addPageTemplates([PageTemplate(id='book',frames=[Frame(M,47,W,PAGE_H-96,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=self.onpage)])
    def onpage(self,c,d):
        if d.page==1:return
        c.saveState();c.setFont('Body',8);c.setFillColor(GREY);c.drawString(M,PAGE_H-27,'YDS SON 5 GÜN  •  ONOUR IMPRAM')
        c.setFillColor(TEAL);c.drawRightString(PAGE_W-M,PAGE_H-27,'İçindekiler');c.setFillColor(GREY)
        c.linkRect('', 'contents', (PAGE_W-M-46,PAGE_H-31,PAGE_W-M,PAGE_H-17), relative=0, thickness=0)
        c.setStrokeColor(BORDER);c.setLineWidth(.5);c.line(M,34,PAGE_W-M,34)
        c.setFont('Body',8);c.drawString(M,22,'17–21 Kasım 2026  |  Konu anlatımı · Uygulama · Çözüm');c.setFont('BodyBold',9);c.drawRightString(PAGE_W-M,22,str(d.page));c.restoreState()
    def afterFlowable(self,f):
        key=getattr(f,'_pdf_destination',None) or getattr(f,'_bookmark',None)
        if key:
            height=getattr(f,'height',None) or getattr(f,'_height',0)
            top=min(PAGE_H,self.frame._y+height+10)
            self.canv.bookmarkHorizontalAbsolute(key,top,left=M)
        if hasattr(f,'_bookmark'):
            level=0 if f._level==1 else 1
            if f._toc:self.notify('TOCEntry',(level,f._headtext,self.page,key));self.canv.addOutlineEntry(f._headtext,key,level=level,closed=False)

class Cover(Flowable):
    def __init__(self):super().__init__();self.width=W;self.height=690
    def draw(self):
        c=self.canv;c.setFillColor(PAPER);c.rect(-M,-50,PAGE_W,PAGE_H,stroke=0,fill=1)
        c.setFillColor(TEAL);c.rect(0,630,58,7,stroke=0,fill=1);c.setFont('BodyBold',11);c.drawString(0,603,'YOĞUNLAŞTIRILMIŞ HAZIRLIK KİTABI')
        c.setFillColor(INK);c.setFont('BodyBold',46);c.drawString(0,535,'YDS');c.setFont('BodyBold',38);c.drawString(0,482,'Son 5 Gün')
        c.setFont('Body',17);c.drawString(0,440,'17–21 Kasım 2026');c.setFont('Body',12);c.drawString(0,411,'Salı · Çarşamba · Perşembe · Cuma · Cumartesi')
        c.setFillColor(TEAL);c.setFont('BodyBold',18);c.drawString(0,352,'85 ve üzeri hedefi için bütünleşik öğretim')
        p=P('Dil bilgisi ve cümle yapısı · 176 görsel kelime kartı\nOkuma ve çeviri · Sarmal hatırlama · 80 soruluk prova\nHer seçeneği açıklayan çözümler','body');p.wrapOn(c,W,100);p.drawOn(c,0,273)
        for i,idx in enumerate([1,58,91,160]):
            im=CellImage(idx,112);im.drawOn(c,i*130,130)
        c.setFillColor(INK);c.setFont('BodyBold',14);c.drawString(0,80,'Onour Impram için');c.setFont('Body',9);c.drawString(0,57,'Kişisel öğrenme nüshası  •  17 Kasım 2026')

def html_inline(s):
    s=html.escape(clean(s));s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s);s=re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)',r'<em>\1</em>',s);s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s);return s.replace('\n','<br>')

def md_html(text):
    # Pandoc supplies semantic Markdown conversion; diagram URIs are replaced by exact embedded SVGs.
    import subprocess
    h=subprocess.run(['pandoc','-f','markdown','-t','html5'],input=text,text=True,capture_output=True,check=True).stdout
    def rep(m):
        key=m[1];f=AS/(key+'.svg')
        if not f.exists():raise ValueError('Missing HTML diagram '+key)
        raw=f.read_text();raw=raw[raw.index('<svg'):]
        ids=re.findall(r'\bid="([^"]+)"',raw)
        for ident in ids:
            new=key+'_'+ident
            raw=raw.replace('id="'+ident+'"','id="'+new+'"').replace('url(#'+ident+')','url(#'+new+')').replace('href="#'+ident+'"','href="#'+new+'"')
        return '<figure class="diagram">'+raw+'</figure>'
    h=re.sub(r'<img src="diagram:([^"]+)"[^>]*>',rep,h)
    h=re.sub(r'<p><strong>((?:P\d|C\d|Gün \d)[^<]*(?:yanıtları|çözümleri)):</strong>(.*?)</p>',r'<details class="lesson-answer"><summary>\1</summary><p>\2</p></details>',h,flags=re.S)
    # Keep standalone exercises useful for retrieval: their answer sections start closed.
    heads=list(re.finditer(r'<h([2-4])\b[^>]*>(.*?)</h\1>',h,re.S));ranges=[]
    for i,m in enumerate(heads):
        title=re.sub('<[^>]+>','',m[2]).lower()
        if any(k in title for k in ['açıklamalı çözüm','yanıt anahtarı','hatırlama anahtarı','transfer anahtarı','ilk hatırlama sorularının anahtarı','türkçe anlam ve','anlam ve değerlendirme anahtarı','sorularının yanıtları']):
            end=next((n.start() for n in heads[i+1:] if int(n[1])<=int(m[1])),len(h))
            ranges.append((m.start(),m.end(),end,re.sub('<[^>]+>','',m[2])))
    for start,mid,end,title in reversed(ranges):h=h[:start]+'<details class="lesson-answer"><summary>'+title+'</summary>'+h[mid:end]+'</details>'+h[end:]
    return h

def html_question(q):
    out='<article class="question" id="q_'+q['id']+'" data-answer="'+str(q['answer'])+'">'
    if q.get('passage'):out+='<blockquote>'+html_inline(q['passage'])+'</blockquote>'
    out+='<p><strong>'+q['id']+'</strong> '+html_inline(q['stem'])+'</p>'
    for i,opt in enumerate(q['options']):out+='<label class="option"><input type="radio" name="'+q['id']+'" value="'+str(i)+'"> <strong>'+chr(65+i)+')</strong> '+html_inline(opt)+'</label>'
    out+='<label class="confidence">Güven <select data-confidence="'+q['id']+'"><option>Seç</option><option>Düşük</option><option>Orta</option><option>Yüksek</option></select></label></article>'
    return out

def html_solution(q):
    out='<details class="solution"><summary>'+q['id']+' açıklamalı çözüm</summary><p><strong>Doğru cevap '+chr(65+q['answer'])+'.</strong> '+html_inline(q.get('rationale',''))+'</p>'
    for i,x in enumerate(q['explanations']):out+='<p><strong>'+chr(65+i)+(' doğru' if i==q['answer'] else ' yanlış')+':</strong> '+html_inline(x)+'</p>'
    return out+'</details>'

def html_test(title,qs,tid):
    h='<section class="test" id="'+tid+'"><h2>'+title+'</h2>'
    h+=''.join(html_question(q) for q in qs)
    h+='<button class="score" data-test="'+tid+'">Bu testin sonucunu hesapla</button><p class="result" aria-live="polite"></p><h3>Açıklamalı çözümler</h3>'
    h+=''.join(html_solution(q) for q in qs);return h+'</section>'

def html_card(v):
    idx=int(v['id'][1:]);atlas=(idx-1)//16+1;row,col=divmod((idx-1)%16,4)
    im=f'<div role="img" aria-label="{html.escape(v["visual_scene"])}" class="wordimage" style="background-image:var(--atlas-{atlas});background-position:{col*100/3}% {row*100/3}%"></div>'
    def j(x):return '; '.join(map(str,x)) if isinstance(x,list) else str(x)
    h='<article class="vocab" id="'+v['id']+'"><div class="cardhead">'+im+'<div><small>'+v['id']+'</small><h3>'+html.escape(v['word'])+'</h3><p class="learning">'+html_inline(v['meaning']+' · '+v.get('pos',''))+'</p><p class="learning"><strong>Görsel:</strong> '+html_inline(v['visual_scene'])+'</p></div></div><div class="learning">'
    for label,key in [('Hafıza hikâyesi','mnemonic_story'),('Çağrışım','association'),('Sözcük ailesi ve ilişkili ifadeler','family'),('İngilizce örnek','example'),('Türkçesi','translation'),('Yeni bağlam','transfer_example'),('Türkçesi','transfer_translation'),('Sınav kullanımı','exam_context'),('Birlikte öğren','collocations'),('Karıştırma','confusion')]:h+='<p><strong>'+label+':</strong> '+html_inline(j(v.get(key,'')))+'</p>'
    if v.get('source_refs'):h+='<p class="source"><strong>Kaynak gözlemi:</strong> '+html_inline(j(v['source_refs']))+'</p>'
    h+='</div><p><strong>Hatırla:</strong> '+html_inline(v['recall_prompt'])+'</p><details><summary>Yanıtı aç</summary><p>'+html_inline(v['recall_answer'])+'</p></details></article>'
    return h

DAY_TITLES={1:'Salı · 17 Kasım | Cümle ve kanıt',2:'Çarşamba · 18 Kasım | Neden, koşul ve değişim',3:'Perşembe · 19 Kasım | İç içe yapılar ve kaynaklar',4:'Cuma · 20 Kasım | Metin, iddia ve seçenekler',5:'Cumartesi · 21 Kasım | Birleştirme ve sınav provası'}
DAY_INTRO={
1:'Bugünün somut ürünü, uzun bir cümlenin omurgasını bulabilmek ve araştırma dilindeki bir ifadenin kanıt kuvvetini korumaktır. Kelime kartlarını araştırma odasına yerleştir. Bölüm sonunda bir paragrafı özne, zaman ve kapsam açısından açıklayacak; 20 soruluk testte kararlarının gerekçesini göstereceksin.',
2:'Bugün önermeler arasındaki ilişkiyi kuracaksın: neden ile koşulu, amaç ile gerçekleşmiş sonucu, olasılık ile zorunluluğu ayır. Değişim atölyesinin kelimeleri bu ilişkilerin fiilleridir. Dünkü kelimeleri önce yardım almadan geri getir; ardından yeni kelimeleri modal ve bağlaçlarla aynı cümlede kullan.',
3:'Bugün uzun cümlelerin içindeki tanımlama, bildirme ve eylem ilişkilerini çözeceksin. Kaynak, toplum ve çevre kelimelerini relative clause, isim cümleciği ve nonfinite yapılar içinde kullan. Bir çevirinin doğru görünmesi yeterli değildir: yapanı, etkilenen öğeyi, zamanı, kapsamı ve mantık bağını tek tek koru.',
4:'Bugün tek cümleden metnin bütününe geçeceksin. İddia ile dayanak arasındaki uzaklığı, gönderim zincirini ve paragraftaki cümlenin işini belirle. Tartışma salonunun kelimeleri bir yazarın tutumunu ve kesinlik derecesini adlandırır. Diyalog, yakın anlam, paragraf tamamlama ve bütünlük sorularında bu ayrımları aynı anda kullan.',
5:'Bugün yeni bir geniş konu kümesi açılmıyor. Önce bilgiyi seçenek olmadan üret, sonra 80 soruluk sınav düzeninde kullan. Simülasyonun ilk 180 dakikadaki yanıtlarını sabitle; açıklamalarla düzelttiğin cevapları ilk sonuca ekleme. Bu özgün prova öğrenilen ayrımları sınar; güçlüğü resmî YDS ile eşitlenmiş bir puan tahmin aracı değildir.'}

def split_markers(text,prefix):
    parts=re.split(r'^# '+prefix+r'(\d+)\s*$',text,flags=re.M)
    return {int(parts[i]):parts[i+1].strip() for i in range(1,len(parts),2)}

def assessment_teaching_days(text):
    names=['Birinci','İkinci','Üçüncü','Dördüncü','Beşinci','Altıncı','Yedinci','Sekizinci','Dokuzuncu','Onuncu']
    mapping={1:1,2:2,3:2,4:3,5:3,6:3,7:4,8:4,9:4,10:4}
    days={i:[] for i in range(1,6)}
    cut=re.search(r'^## Beşinci gün',text,re.M)
    if cut:days[5].append(text[cut.start():]);text=text[:cut.start()]
    chunks=re.split(r'(?=^### )',text,flags=re.M)
    for chunk in chunks:
        found=next((i+1 for i,n in enumerate(names) if re.match(r'^### '+n+r' soru ailesi',chunk)),None)
        if found:days[mapping[found]].append(chunk)
        elif not chunk.startswith('### '):days[1].append(chunk)
        else:days[5].append(chunk)
    return {d:'\n\n'.join(c) for d,c in days.items()}

def retrieval_md(day,vocab):
    if day==1:return ''
    old=[v for v in vocab if v['day']==day-1]
    if day>=3:old += [v for v in vocab if v['day']<day-1 and int(v['id'][1:])%4==day%4]
    prompt='## Önceki bilgiyi kapalı kitap geri getir\n\nAşağıdaki anlamlardan İngilizce sözcüğü veya ifadeyi üret; ardından onunla bir doğru eşdizim ya da edat kalıbı yaz. Her satır için sözcük 1, doğru kullanım 1 puandır. Bu, öğrenme kaydıdır; YDS puanı değildir. Önceki günün bütün 44 hedefi ve daha eski günlerden dönüşümlü örnekler birlikte kullanılır.\n\n'
    prompt+='\n\n'.join(f'**R{day}.{i+1:02d}** {v["meaning"]} → __________________  Kullanım: __________________' for i,v in enumerate(old))
    key='## Geri çağırma yanıt anahtarı\n\n'+ '\n\n'.join(f'**R{day}.{i+1:02d}** {v["word"]}; örnek kullanım: {v["collocations"][0] if v.get("collocations") else v["example"]}. ({v["id"]})' for i,v in enumerate(old))
    return prompt,key

def html_memoryboard(start,vocab):
    out='<div class="memoryboard">'
    for idx in range(start,min(start+16,177)):
        k=(idx-1)//16+1;row,col=divmod((idx-1)%16,4);v=vocab[f'V{idx:03d}']
        out+=f'<div><div role="img" aria-label="{html.escape(v["visual_scene"])}" class="wordimage" style="background-image:var(--atlas-{k});background-position:{col*100/3}% {row*100/3}%"></div><label>V{idx:03d} <input class="memory-input" data-memory="V{idx:03d}" aria-label="V{idx:03d} hatırlama cevabı"></label></div>'
    return out+'</div>'

def transfer_pdf(items):
    out=[heading('Seçeneksiz bağımsız transfer',2,'transfer',True),P('Bu görevlerde seçenek yoktur. Yanıtını İngilizce üret veya belirtilen anlam ayrımını açıkla. Model yanıtlar ve puan ölçütleri bütün görevlerden sonra gelir. Aynı anlamı ve istenen yapıyı koruyan başka doğru yanıtlar da kabul edilebilir.')]
    for q in items:out += [P('**'+q['id']+' · '+q['skill']+'**'),P(q['prompt']),P('Yanıt: __________________________________________________________________\n________________________________________________________________________','small'),Spacer(1,12)]
    out += [PageBreak(),heading('Transfer görevlerinin çözüm ve değerlendirmesi',2,'transfer_answers',True)]
    for q in items:out += [P('**'+q['id']+'** '+q['model_answer']),P('**Kabul sınırı:** '+q['accepted_variants']),P('**Değerlendirme:** '+q['rubric']+' En çok '+str(q['max_points'])+' puan.','solution')]
    return out

def transfer_html(items):
    out='<section id="transfer"><h2>Seçeneksiz bağımsız transfer</h2><p>Önce kendi yanıtını yaz. Çözüm ve puan ölçütleri görevlerin sonunda kapalı bölümlerde bulunur.</p>'
    for q in items:out+='<article class="question"><h3>'+q['id']+' · '+html.escape(q['skill'])+'</h3><p>'+html_inline(q['prompt'])+'</p><textarea data-note="'+q['id']+'" aria-label="'+q['id']+' yanıtı"></textarea></article>'
    out+='<h2>Transfer çözümleri</h2>'
    for q in items:out+='<details><summary>'+q['id']+' çözüm ve ölçüt</summary><p>'+html_inline(q['model_answer'])+'</p><p>'+html_inline(q['accepted_variants'])+'</p><p>'+html_inline(q['rubric'])+' En çok '+str(q['max_points'])+' puan.</p></details>'
    return out+'</section>'

def error_md(day):
    return '''## Sonucu bilgiye dönüştür

Toplam doğru: ____ / 20. Yüksek güvenli yanlış: ____. Düşük güvenli doğru: ____. Gerekçesi kurulamadığı için yeniden öğrenilecek doğru: ____.

| Madde | Hata kodu | Doğru cevabın dayanağı | Bir sonraki soruda uygulayacağım kural |
|---|---|---|---|
| ______ | K / G / B / Ç / R / D / Z | __________________ | __________________ |
| ______ | K / G / B / Ç / R / D / Z | __________________ | __________________ |
| ______ | K / G / B / Ç / R / D / Z | __________________ | __________________ |

**16–20 doğru:** Açıklamalarını kontrol et; özellikle yüksek güvenli yanlışları onar. **12–15 doğru:** Tekrarlanan iki hata kodunu seç ve bu günün ilgili açıklamasını kapatıp örneği yeniden kur. **0–11 doğru:** Soruya geçmeden cümlenin özne–fiil omurgasını ve bağlaç ilişkisini sesli açıkla; aynı maddeleri anahtarsız yeniden çöz. Bu aralıklar öğretim için seçilmiştir; yeterlik düzeyi veya gerçek YDS puanı tahmini değildir.

Bir sonraki güne taşınacak üç ifade: __________________. Her biriyle bugünkü örneğin konusundan farklı bir İngilizce cümle üret. Ertesi gün ilk okumadan önce bu üç cümleyi hatırlamayı dene.
'''

def build_all(html_only=False,pdf_only=False):
    study_path=B/'study.json'
    study=json.loads(study_path.read_text()) if study_path.exists() else None
    days_by_number={day['day']:day for day in study['days']} if study else {}
    if study and set(days_by_number)!=set(range(1,6)):
        raise ValueError('Çalışma dosyasında birden beşe kadar günler bulunmalı.')
    load_diagrams();vocab=json.loads((B/'vocabulary.json').read_text());vmap={v['id']:v for v in vocab};a=json.loads((B/'assessment.json').read_text())
    assert len(vocab)==176 and all(len([v for v in vocab if v['day']==i])==44 for i in range(1,5))
    lex=split_markers((B/'lexical_lessons.md').read_text(),'LEX_DAY');labs=split_markers((B/'reading_labs.md').read_text(),'LAB_DAY');teaching=assessment_teaching_days((B/'assessment_teaching.md').read_text())
    assert set(lex)==set(range(1,6)) and set(labs)==set(range(1,6))
    story=[Cover(),PageBreak(),heading('İçindekiler',1,'contents')];toc=TableOfContents();toc.levelStyles=[ParagraphStyle('TOC1',fontName='BodyBold',fontSize=11,leading=16,textColor=INK,spaceBefore=7),ParagraphStyle('TOC2',fontName='Body',fontSize=9.2,leading=13,textColor=GREY,leftIndent=12,spaceBefore=3)];story+=[toc,PageBreak()]
    H=[];md_export=[]
    def addmd(s,hide=False):
        story.extend(md_blocks(s))
        if not pdf_only:
            rendered=md_html(s)
            H.append('<details><summary>Yanıt anahtarını aç</summary>'+rendered+'</details>' if hide else rendered)
            md_export.append(s)
    def chapter(title,anchor):
        story.extend([PageBreak(),heading(title,1,anchor,True)]);H.append('<section class="chapter" id="'+anchor+'"><h1>'+html.escape(title)+'</h1>');md_export.append('# '+title)
    def subsection(title,anchor):
        story.append(heading(title,2,anchor,True));H.append('<h2 id="'+anchor+'">'+html.escape(title)+'</h2>');md_export.append('## '+title)
    story.append(heading('Kitaba giriş',1,'intro',True));H.append('<section class="chapter" id="intro">');addmd((B/'frontmatter.md').read_text());story += [DIAGRAMS['memory_rooms'],P('Her mekânın anlam ilişkileri, kelime kartlarında ve okuma parçalarında yeniden kurulur.','caption')];H.append('' if pdf_only else md_html('![Dört hafıza mekânı](diagram:memory_rooms)'));H.append('</section>')
    chapter('Başlangıç tanılaması','diagnostic');addmd('20 maddeyi açıklamalara bakmadan çöz. Süreni, yanıtını ve güvenini kaydet. Bu küçük set güçlü ve zayıf ayrımları görünür kılar; gerçek YDS puanını tahmin etmez.\n\n'+a['notice']);story+=assessment_block('20 soruluk tanılayıcı test',a['diagnostic'],'diagnostic_test');H.append(html_test('20 soruluk tanılayıcı test',a['diagnostic'],'diagnostic_test'));H.append('</section>')
    for day in range(1,6):
        chapter(DAY_TITLES[day],f'day{day}');addmd(DAY_INTRO[day])
        if day in (2,3,4):
            prompts,key=retrieval_md(day,vocab)
            story.append(destination(Spacer(1,1),f'retrieval_{day}'))
            addmd(prompts)
            story.append(P(f'[Geri çağırma yanıt anahtarı](#retrieval_key_{day})','small'))
            story.extend([PageBreak(),destination(Spacer(1,1),f'retrieval_key_{day}')])
            addmd(key)
            story.append(P(f'[Geri çağırma görevine dön](#retrieval_{day})','small'))
        subsection('Dil bilgisi ve anlam atölyesi',f'day{day}_grammar');addmd((B/f'grammar_day{day}.md').read_text())
        subsection('Kelimeyi yapı içinde öğren',f'day{day}_lexical');addmd(lex[day])
        if day<=4:
            if day!=4:story.append(PageBreak())
            subsection('Görsel kelime kartları',f'day{day}_cards');addmd('Karttaki resmi, kelimenin temel anlamıyla birlikte oku. Hikâye bir hatırlama desteğidir; gerçek köken açıklaması olarak kullanılmaz. Her kartın **Hatırla** sorusunu yanıtını açmadan çöz. Yanıt anahtarı bu günün bütün kartlarından sonra gelir. Elektronik sürümde üstteki **Hatırlama modu** düğmesi anlam ve açıklamaları gizler.')
            story.append(P(f'[Kart sorularının yanıtları](#day{day}_card_answers) · [Alfabetik dizin](#index)','small'))
            dayv=[v for v in vocab if v['day']==day]
            for v in dayv:story+=card(v);H.append(html_card(v));md_export.append('### '+v['id']+' '+v['word']+'\n\n'+'\n\n'.join(f'**{k}:** {v[k]}' for k in ['meaning','visual_scene','mnemonic_story','association','example','translation','transfer_example','transfer_translation','exam_context','confusion','recall_prompt','recall_answer']))
            story.append(PageBreak());subsection('Kart sorularının yanıtları',f'day{day}_card_answers');ans='\n\n'.join('**'+v['id']+' '+v['word']+'** '+v['recall_answer'] for v in dayv);addmd(ans,hide=True)
            story.append(P(f'[Görsel kartlara dön](#day{day}_cards)','small'))
        if teaching[day]:subsection('Soru türlerinin çözüm mantığı',f'day{day}_questions');addmd(teaching[day])
        subsection('Bütünleşik okuma ve transfer',f'day{day}_reading');addmd(labs[day])
        if day in days_by_number and not html_only:
            story.extend(study_blocks(days_by_number[day],study['title'],study['instructions'],
                                      heading,P,KeepTogether,PageBreak))
        if day<=4:
            story.append(PageBreak());qs=a['daily'][str(day)];story+=assessment_block('Gün '+str(day)+' kümülatif testi',qs,f'day{day}_test');H.append(html_test('Gün '+str(day)+' kümülatif testi',qs,f'day{day}_test'));addmd(error_md(day))
        else:
            story.append(PageBreak());subsection('176 görselle bağımsız hatırlama', 'visual_recall');addmd('Her resme bakıp İngilizce hedefi yaz; ardından onunla doğru bir cümle kur. V kodu yanıt anahtarına bağlanır. Sözcüğü hatırlayamıyorsan resimdeki eylemi Türkçe adlandır; sonra İngilizceyi yeniden dene. Bir resmi tanımak yeterli değildir: kelimeyi ve kullanımını üretmek gerekir. Çok anlamlı sözcükte kartın öğrettiği başka doğru anlamı yazmışsan onu da ayrıca belirt. Anahtar bütün panolardan sonra gelir.')
            for start in range(1,177,16):
                story += [CondPageBreak(650),heading(f'Hafıza panosu · V{start:03d}–V{start+15:03d}',3),MemoryBoard(start,vocab=vmap)];H.append('<h3>'+f'Hafıza panosu V{start:03d}–V{start+15:03d}'+'</h3>'+html_memoryboard(start,vmap))
            story.append(PageBreak());subsection('Görsel hatırlama anahtarı','visual_key');story.append(P('[Hafıza panolarına dön](#visual_recall)','small'));addmd('\n\n'.join(f'**{v["id"]} {v["word"]}** — {v["meaning"]}' for v in vocab),hide=True)
            story.append(PageBreak());subsection('80 soruluk özgün sınav simülasyonu','simulation');addmd('**Süre: 180 dakika.** Beş seçenekten tek bir en uygun cevabı seç. Birinci geçişte verdiğin cevapları ve süreyi sabitle. Bütün sorular bitmeden çözümleri açma. Metinlerdeki araştırma, kurum ve sayılar kurgusal öğretim bağlamlarıdır. Sorular YDS biçimine göre hazırlanmıştır; resmî sorular değildir ve zorlukları deneysel olarak YDS ile eşitlenmemiştir. **68/80 burada aritmetik olarak %85 başarıdır; gerçek sınavda 85 alacağının kanıtı değildir.**')
            story.append(P('[İşaretleme formuna git](#simulation_form) · [İlk soruya geç](#group_S01-16)','small'))
            story += [PageBreak(),heading('Simülasyon işaretleme formu',2,'simulation_form',True),
                      P('Bu sayfayı prova sırasında ayrı tutabilirsin. Her satırda bir seçenek işaretle ve o andaki güvenini yaz.'),
                      answer_sheet(width=W,ink=INK,muted=GREY,line=BORDER),
                      P('[İlk soruya geç](#group_S01-16)','small'),PageBreak()]
            H.append('<section class="test" id="simulation_test">');sim=[];groups_by_item={}
            for g in a['simulation']['groups']:
                story += [CondPageBreak(610 if g.get('passage') else 190),heading(g['id']+' · '+g['type'],3,'group_'+g['id'])];H.append('<h3>'+html.escape(g['id']+' · '+g['type'])+'</h3>')
                if g.get('instructions'):story.append(P(g['instructions'],'small'));H.append('<p>'+html_inline(g['instructions'])+'</p>')
                if g.get('passage'):
                    story.append(P(g['passage'],'quote'));H.append('<blockquote>'+html_inline(g['passage'])+'</blockquote>')
                for q in g['questions']:
                    story+=question(q,group=g)
                    H.append(html_question(q))
                    sim.append(q)
                    groups_by_item[q['id']]=g
            H.append('<button type="button" class="score" data-test="simulation_test">Simülasyonu değerlendir</button><p class="result" aria-live="polite"></p></section>')
            story.append(PageBreak());subsection('Simülasyon cevap çizelgesi ve açıklamalı çözümler','simulation_solutions')
            keyrows=['| Sorular | Cevaplar |','|---|---|']
            for i in range(0,80,10):keyrows.append('| '+str(i+1)+'–'+str(i+10)+' | '+' · '.join(q['id']+': '+chr(65+q['answer']) for q in sim[i:i+10])+' |')
            if not pdf_only:
                H.append(md_html('\n'.join(keyrows)))
            story.append(P('[Simülasyonun başına dön](#simulation) · [İşaretleme formu](#simulation_form)','small'))
            story.extend([assessment_key(sim),Spacer(1,14)])
            for q in sim:story+=solution(q,group=groups_by_item[q['id']]);H.append(html_solution(q))
            addmd('## Simülasyon değerlendirmesi\n\nİlk 180 dakikada doğru: ____/80. Çözümlerden sonra bağımsız düzeltilen: ____. Hâlâ açıklanamayan: ____. Toplam sonucu soru ailelerine ayır: kelime 6; dil bilgisi 10; cloze 10; cümle tamamlama 10; çeviri 6; okuma 20; diyalog 5; yakın anlam 4; paragraf tamamlama 4; bütünlük 5. Paydaları farklı alanları yalnız yanlış sayısıyla kıyaslama. Bir alanda 2/4 yanlış, başka alanda 2/20 yanlıştan farklı bir örüntüdür.\n\nYüksek güvenli yanlışlarda doğru cevabın dayanağını ve kendi seçeneğinin değiştirdiği tek ilişkiyi yaz. Düşük güvenli doğrularda neden diğer dört seçeneğin elendiğini açıklamayı dene. Süre sorunu varsa ilk zorlanılan maddeyi ve orada yeni kanıt üretmeden geçirilen tekrarları kaydet. Aynı soruyu yeniden çözmenin başarısını, görülmemiş bir sınavdaki performansla eşitleme.')
            story+=transfer_pdf(a['transfer']);H.append(transfer_html(a['transfer']))
            addmd('## Son bağımsız kontrol\n\nBir arkadaşına açıklıyormuş gibi üç dakikada şu ayrımları anlat: **imply / infer; arise / rise / raise; given that / provided that; despite / although; needn\'t have / didn\'t need to; few / a few; not all / none; plausible / certain.** Ardından kaynak, kanıt ve koşul içeren üç yeni İngilizce cümle kur. Açıklamadığın farkı yalnız kelime listesine bakarak geçmiş sayma; ilgili günün örneğini kapatıp yeniden üret. Son kontrolün amacı yeni malzeme biriktirmek değil, öğrendiğin ayrımları yardımsız kullanabilmektir.')
        H.append('</section>')
    chapter('Geçmiş sınavların sistematik incelemesi','corpus');addmd(re.sub(r'^# .*\n','',(B/'source_analysis.md').read_text(),count=1));H.append('</section>')
    chapter('Kaynaklar ve kanıt sınırları','references');addmd(re.sub(r'^# .*\n','',(B/'references.md').read_text(),count=1));H.append('</section>')
    chapter('Alfabetik kelime dizini','index');idx=['| Sözcük / ifade | Kart | Öğrenme günü |','|---|---|---|']
    for v in sorted(vocab,key=lambda x:x['word'].lower()):idx.append('| '+v['word']+' | '+v['id']+' | '+['','Salı','Çarşamba','Perşembe','Cuma'][v['day']]+' |')
    if not html_only:
        for i in range(2,len(idx)):
            idx[i]=re.sub(r'\| (V\d{3}) \|',r'| [\1](#card_\1) |',idx[i])
    if not html_only and not pdf_only:
        story.extend(md_blocks('\n'.join(idx)))
        H.append(md_html(re.sub(r'\[(V\d{3})\]\(#card_V\d{3}\)',r'\1','\n'.join(idx))))
    else:
        addmd('\n'.join(idx))
    H.append('</section>')
    pdf=OUT/'YDS_Son_5_Gun_Hazirlik_Kitabi.pdf'
    if not html_only:
        doc=BookDoc(str(pdf),title='YDS Son 5 Gün Yoğunlaştırılmış Hazırlık Kitabı',author='Onour Impram için hazırlanmıştır',subject='17–21 Kasım 2026 · Bütünleşik İngilizce öğretimi');doc.multiBuild(story)
    if pdf_only:return
    htmlpath=OUT/'YDS_Son_5_Gun_Etkilesimli_Kitap.html';htmlpath.write_text(html_shell(''.join(H)),encoding='utf8')
    if html_only:return
    import fitz
    d=fitz.open(pdf);stats={'pdf_pages':len(d),'pdf_text_words':sum(len(p.get_text().split()) for p in d),'vocabulary_cards':len(vocab),'illustrated_cells':176,'diagram_count':len(DIAGRAMS),'diagnostic_mcq':20,'daily_mcq':80,'simulation_mcq':80,'transfer_tasks':len(a['transfer']),'grammar_applications':80,'source_booklets':12,'visible_source_questions':240,'pdf_bytes':pdf.stat().st_size,'html_bytes':htmlpath.stat().st_size};d.close();(OUT/'Kitap_Dokumu.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print(json.dumps(stats,ensure_ascii=False,indent=2))

def html_shell(body):
    seen=collections.Counter()
    def unique_id(m):
        ident=m[1];seen[ident]+=1
        return 'id="'+ident+('__'+str(seen[ident]) if seen[ident]>1 else '')+'"'
    body=re.sub(r'\bid="([^"]+)"',unique_id,body)
    atlas=''.join('--atlas-'+str(i)+':url(data:image/png;base64,'+base64.b64encode((AS/f'atlas_{i:02d}.png').read_bytes()).decode()+');' for i in range(1,12))
    css='''
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f4f2ec;color:#16334b;font:17px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}header{background:#16334b;color:white;padding:3rem max(5vw,24px)}header h1{font-size:clamp(2rem,5vw,3.8rem);line-height:1.1;margin:.3em 0}header p{max-width:75ch}nav{position:sticky;top:0;background:#fffefbf5;border-bottom:1px solid #ccd8dc;padding:.6rem 1rem;z-index:10;display:flex;flex-wrap:wrap;gap:.6rem;align-items:center}nav a,button{display:inline-block;border:1px solid #bed0ce;border-radius:5px;padding:.4rem .75rem;background:#eef5f3;color:#164f4c;text-decoration:none;font:inherit;font-size:.9rem;cursor:pointer}nav label{margin-left:auto;font-size:.85rem}nav input{max-width:13rem}main{max-width:1050px;margin:auto;background:white;padding:2rem 3rem}.chapter{border-top:4px solid #237b76;margin-top:4rem;padding-top:1rem;scroll-margin-top:6rem}h1,h2,h3,h4{line-height:1.25;scroll-margin-top:6rem}h1{font-size:2.2rem}h2{color:#237b76;margin-top:2.4rem;font-size:1.65rem}h3{margin-top:1.8rem;font-size:1.2rem}p{margin:.8rem 0}a{color:#176c68}table{width:100%;border-collapse:collapse;font-size:.93rem;margin:1.4rem 0;display:table}td,th{border:1px solid #ccd8dc;padding:.65rem;text-align:left;vertical-align:top}th{background:#237b76;color:white}tr:nth-child(even){background:#eef5f3}blockquote{margin:1.3rem 0;background:#f2f6f4;border-left:4px solid #237b76;padding:1.1rem 1.3rem;white-space:normal}figure{margin:1.5rem 0}.diagram svg{width:100%;height:auto;max-width:100%}.diagram svg text{font-family:Arial,sans-serif!important}figcaption{font-size:.85rem;color:#52616a}.vocab{border:1px solid #ccd8dc;padding:1.2rem;margin:1.7rem 0;break-inside:avoid}.cardhead{display:flex;gap:1.3rem;align-items:start}.cardhead h3{font-size:1.7rem;margin:.2rem 0;color:#237b76}.wordimage{width:180px;aspect-ratio:4/3;flex-shrink:0;background-size:400% 400%;background-repeat:no-repeat}.vocab p{font-size:.96rem}.vocab small,.source{color:#52616a}.recall-mode .learning{display:none}.question{padding:1.2rem;border:1px solid #ccd8dc;margin:1.2rem 0;scroll-margin-top:6rem}.option{display:block;padding:.45rem .5rem;cursor:pointer;border-radius:4px}.option:hover{background:#eef5f3}input[type=radio]{accent-color:#237b76}input,textarea,select{font:inherit;color:#16334b;border:1px solid #a9bec2;border-radius:4px;padding:.35rem;background:white}textarea{width:100%;min-height:100px}.confidence{display:block;margin-top:.9rem;font-size:.86rem;color:#52616a}.confidence select{font-size:.85rem}details{border:1px solid #ccd8dc;border-radius:4px;padding:.7rem 1rem;margin:.7rem 0}summary{cursor:pointer;font-weight:650;color:#237b76}.result{font-weight:700;background:#eef5f3;padding:.9rem}.result:empty{display:none}.correct{border-left:5px solid #237b76}.incorrect{border-left:5px solid #b75540}.memoryboard{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:1.5rem 0}.memoryboard .wordimage{width:100%}.memoryboard label{font-size:.8rem}.memory-input{width:100%;font-size:.85rem;margin-top:.3rem}.search-hit{outline:4px solid #dfb35b;outline-offset:4px}.toolbar-status{font-size:.8rem;color:#435f68}footer{max-width:1050px;margin:auto;padding:2rem 3rem;color:#52616a}button:focus-visible,a:focus-visible,summary:focus-visible,input:focus-visible{outline:3px solid #bd8024;outline-offset:3px}@media(max-width:700px){main{padding:1rem}body{font-size:16px}nav{gap:.3rem;position:static}nav label{width:100%;margin-left:0}.wordimage{width:115px}.cardhead{gap:.8rem}.memoryboard{grid-template-columns:repeat(2,1fr)}table{font-size:.8rem}td,th{padding:.35rem}.chapter{scroll-margin-top:1rem}}@media print{nav,button,footer{display:none}body{background:white;font-size:10.5pt}main{max-width:none;padding:0}.chapter{break-before:page}header{background:white;color:#16334b}.question,.vocab{break-inside:avoid}details:not([open])>:not(summary){display:none}.recall-mode .learning{display:block}}
'''
    nav='<nav aria-label="Kitap bölümleri">'+''.join('<a href="#day'+str(i)+'">'+['','Salı','Çarşamba','Perşembe','Cuma','Cumartesi'][i]+'</a>' for i in range(1,6))+'<a href="#diagnostic">Tanılama</a><a href="#simulation">Simülasyon</a><a href="#index">Dizin</a><button id="recall" aria-pressed="false">Hatırlama modu</button><label>Kitapta bul <input id="search" type="search" placeholder="kelime veya konu"></label><button id="find">Bul / sonraki</button><span id="search-status" class="toolbar-status" aria-live="polite"></span></nav>'
    js=r'''
const KEY='yds-son5-2026-v1';let state={};try{state=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}function persist(){try{localStorage.setItem(KEY,JSON.stringify(state))}catch(e){document.getElementById('save-status').textContent='Bu tarayıcı yerel kayda izin vermiyor; yanıtlar sayfa açıkken korunur.'}}
document.querySelectorAll('input[type=radio]').forEach(el=>{if(state[el.name]===el.value)el.checked=true;el.addEventListener('change',()=>{state[el.name]=el.value;persist()})});document.querySelectorAll('[data-note],[data-memory],[data-confidence]').forEach(el=>{const k=el.dataset.note||el.dataset.memory||('conf-'+el.dataset.confidence);if(state[k]!==undefined)el.value=state[k];el.addEventListener('input',()=>{state[k]=el.value;persist()})});
document.querySelectorAll('.score').forEach(btn=>btn.addEventListener('click',()=>{const box=document.getElementById(btn.dataset.test);let total=0,correct=0,blank=0,highWrong=0,lowCorrect=0;box.querySelectorAll('.question[data-answer]').forEach(q=>{total++;let pick=q.querySelector('input:checked');q.classList.remove('correct','incorrect');if(!pick){blank++;return}let ok=pick.value===q.dataset.answer;correct+=ok?1:0;q.classList.add(ok?'correct':'incorrect');const conf=q.querySelector('select')?.value;if(!ok&&conf==='Yüksek')highWrong++;if(ok&&conf==='Düşük')lowCorrect++});box.querySelector('.result').textContent=`${correct}/${total} doğru · ${total-correct-blank} yanlış · ${blank} boş · Yüksek güvenli yanlış: ${highWrong} · Düşük güvenli doğru: ${lowCorrect}. Bu sonuç öğretim içindir; resmî YDS puanı tahmini değildir.`}));
document.getElementById('recall').addEventListener('click',function(){const on=document.body.classList.toggle('recall-mode');this.setAttribute('aria-pressed',on);this.textContent=on?'Açıklamaları göster':'Hatırlama modu'});
function normalizeSearch(s){return s.toLocaleLowerCase('tr').replace(/ı/g,'i')}let last='',hits=[],pos=-1;function findNext(){const query=normalizeSearch(document.getElementById('search').value.trim());document.querySelectorAll('.search-hit').forEach(e=>e.classList.remove('search-hit'));if(!query){document.getElementById('search-status').textContent='';return}if(query!==last){last=query;hits=[...document.querySelectorAll('main h1,main h2,main h3,main p,main td')].filter(e=>normalizeSearch(e.textContent).includes(query));pos=-1}if(!hits.length){document.getElementById('search-status').textContent='Sonuç bulunamadı';return}pos=(pos+1)%hits.length;let el=hits[pos];if(el.closest('.learning')&&document.body.classList.contains('recall-mode')){document.body.classList.remove('recall-mode');const r=document.getElementById('recall');r.setAttribute('aria-pressed','false');r.textContent='Hatırlama modu'}for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;el.classList.add('search-hit');el.scrollIntoView({block:'center'});document.getElementById('search-status').textContent=`${pos+1}/${hits.length}`}document.getElementById('find').addEventListener('click',findNext);document.getElementById('search').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();findNext()}});
'''
    return '<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>YDS Son 5 Gün | Onour Impram</title><style>:root{'+atlas+'}'+css+'</style></head><body><header><p>ONOUR IMPRAM İÇİN · 17–21 KASIM 2026</p><h1>YDS Son 5 Gün</h1><p>Yoğunlaştırılmış Hazırlık Kitabı · Konu anlatımı, 176 görsel kelime kartı, bütünleşik okuma, kümülatif testler ve açıklamalı sınav simülasyonu.</p><p id="save-status">Bu kitap çevrimdışı çalışır. Test yanıtları ve yazılı notlar, tarayıcı izin verdiğinde aynı tarayıcıda yerel olarak saklanır. Çözümleri kendi yanıtını ürettikten sonra aç.</p></header>'+nav+'<main>'+body+'</main><footer>17 Kasım 2026 · Kişisel öğrenme nüshası. Özgün öğretim testleri resmî YDS soruları veya puan tahmin araçları değildir. Kanıt sınırları ve kaynaklar kitabın sonunda açıklanmıştır.</footer><script>'+js+'</script></body></html>'

if __name__=='__main__':
    import sys
    build_all(html_only='--html-only' in sys.argv,pdf_only='--pdf-only' in sys.argv)

