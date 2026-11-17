"""Apply the offline UI improvements to either existing YDS HTML edition."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def apply(html: str, study: dict) -> str:
    def replace(old, new):
        nonlocal html
        if html.count(old) != 1:
            raise ValueError(f"Expected exactly one UI marker: {old[:120]}")
        html = html.replace(old, new, 1)

    replace("</style></head>", (HERE / "ux.css").read_text() + "</style></head>")
    replace("    this.vocab = Array.isArray", """
    this.study = window.YDS_TRANSFER_CONTENT || {};
    this.studyDays = Array.isArray(this.study.days) ? this.study.days : [];
    this.studyMap = new Map(this.studyDays.flatMap(function(d){return d.items.map(function(q){return [q.id,q];});}));
    this.vocab = Array.isArray""")
    replace("    this.player = new Audio();", """
    Object.assign(this.ui,{studyDay:1,studyIndex:0,studyReview:false,studyReviewIds:[],studyRetry:false,studyAnswer:null,studyReason:''});
    this.player = new Audio();""")
    replace("practice:{},challenges:{},activity:{}", "practice:{},challenges:{},study:{},activity:{}")
    replace("    out.exam=exam(raw.exam);", """    Object.entries(raw.study || {}).forEach(function(pair){
      var q=self.studyMap.get(pair[0]), r=pair[1];
      if(q&&r&&[r.first,r.choice].every(function(n){return Number.isInteger(n)&&n>=0&&n<q.options.length;}))out.study[pair[0]]={first:r.first,firstTime:finite(r.firstTime,finite(r.time)),choice:r.choice,reason:String(r.reason||'').slice(0,1500),time:finite(r.time)};
    });
    out.exam=exam(raw.exam);""")
    replace("      ['challenges','activity'].forEach(", """      Object.entries(incoming.study).forEach(function(p){
        var previous=current.study[p[0]], next=p[1];
        if(!previous){current.study[p[0]]=next;return;}
        var earliest=previous.firstTime<=next.firstTime?previous:next;
        var latest=previous.time>=next.time?previous:next;
        current.study[p[0]]=Object.assign({},latest,{first:earliest.first,firstTime:earliest.firstTime});
      });
      ['challenges','activity'].forEach(""")
    replace("  App.prototype.stats = function()", (HERE / "study.js").read_text() + "  App.prototype.stats = function()")
    replace("challenge:this.challengeView,exam:", "challenge:this.challengeView,study:this.studyView,exam:")
    replace("challenge:'İnce ayrımlar',exam:", "challenge:'İnce ayrımlar',study:'Aktarım atölyesi',exam:")
    replace("['challenge','İnce ayrımlar'],['exam'", "['challenge','İnce ayrımlar'],['study','Aktarım atölyesi'],['exam'")
    replace("'dashboard','cards','audio','challenge','exam','notes','book'", "'dashboard','cards','audio','challenge','study','exam','notes','book'")
    replace("+btn('Tam kitabı aç','tab','data-tab=\"book\"')", """+btn('Aktarımı çalış','tab','data-tab="study"')+btn('Tam kitabı aç','tab','data-tab="book"')""")
    replace("    if(el.id==='yds-card-answer'){", "    if(el.id==='yds-study-reason'){this.ui.studyReason=el.value;return;}\n    if(el.id==='yds-card-answer'){")
    replace("    switch(action){\n      case 'open-visual'", """    if(action.startsWith('study-')){this.studyAction(action,el);return;}
    switch(action){
      case 'skip':if(this.ui.tab==='book'&&this.book){var bookHeading=this.book.querySelector('h1');if(bookHeading){bookHeading.tabIndex=-1;bookHeading.focus({preventScroll:true});bookHeading.scrollIntoView();}}else this.focusContent('h1,h2');break;
      case 'audio-close':this.clearAudio();if(this.audioReturnTarget&&this.audioReturnTarget.isConnected)this.audioReturnTarget.focus();else if(this.ui.tab==='book')this.root.querySelector('.yds-book-back').focus();else this.focusContent('h1,h2');break;
      case 'open-visual'""")
    replace("var id=this.ui.ids[this.ui.index],rerender=false;", """var id=this.ui.ids[this.ui.index],rerender=false;
    if(el.id==='yds-study-day'){Object.assign(this.ui,{studyDay:Number(el.value),studyIndex:0,studyReview:false,studyReviewIds:[],studyRetry:false,studyAnswer:null,studyReason:''});this.render();return;}
    if(el.name==='yds-study-choice'){this.ui.studyAnswer=Number(el.value);return;}""")
    replace("this.root.innerHTML='<div class=\"yds-header\">", """this.root.innerHTML='<a class="yds-skip" href="#yds-main" data-action="skip">İçeriğe geç</a><div class="yds-header">""")
    replace("data-tab=\"'+x[0]+'\" role=\"tab\"", "data-tab=\"'+x[0]+'\" id=\"yds-tab-'+x[0]+'\" role=\"tab\" aria-controls=\"'+(x[0]==='book'?'legacy-book':'yds-main')+'\"")
    replace("Çalışma alanına alttaki Panel düğmesinden dönebilirsin.</div><div", """Çalışma alanına Panel düğmesinden dönebilirsin.</div>'+btn('Panele dön','tab','data-tab="dashboard" hidden','yds-book-back')+'<div""")
    replace("+btn('Panel','tab','data-tab=\"dashboard\"')+'</div>", """+btn('Kapat','audio-close','aria-label="Ses oynatıcısını kapat"')+' '+btn('Panel','tab','data-tab="dashboard"')+'</div>""")
    replace("    this.main=this.root.querySelector('#yds-main');this.root.querySelector('#yds-audio-element').appendChild(this.player);", """
    this.main=this.root.querySelector('#yds-main');this.root.querySelector('#yds-audio-element').appendChild(this.player);
    var dock=this.root.querySelector('.yds-audio-dock');
    if(typeof ResizeObserver==='function')new ResizeObserver(function(){
      if(dock.offsetHeight)document.body.style.setProperty('--yds-dock-space',(dock.offsetHeight+30)+'px');
    }).observe(dock);
    if(this.book){
      this.book.setAttribute('role','tabpanel');
      this.book.setAttribute('aria-labelledby','yds-tab-book');
      this.book.querySelectorAll('img[data-vocab-image]').forEach(function(img){
        var control=document.createElement('button');
        control.type='button';
        control.className='yds-legacy-zoom';
        control.dataset.legacyVisual=img.dataset.vocabImage;
        control.setAttribute('aria-label',(img.alt||'Kelime kartı görseli')+' · Büyüt');
        img.before(control);
        control.appendChild(img);
      });
    }""")
    replace("    var self=this,selectedKind=kind||'word',src=", "    if(!this.currentAudio||!this.root.querySelector('.yds-audio-dock').contains(document.activeElement))this.audioReturnTarget=document.activeElement;\n    var self=this,selectedKind=kind||'word',src=")
    replace("if(promise&&promise.catch)promise.catch(function(){self.audioStatus", "if(promise&&promise.catch)promise.catch(function(){if(!self.currentAudio||self.currentAudio.src!==src)return;self.audioStatus")
    replace("    repeat.disabled=!audio;", "    this.root.dataset.audioActive=String(!!audio);repeat.disabled=!audio;")
    replace("this.player.removeAttribute('src');this.updateAudioContext()", "this.player.removeAttribute('src');this.player.load();this.updateAudioContext()")
    replace("this.root.querySelector('#yds-book-note').hidden=!isBook;", "this.root.querySelector('#yds-book-note').hidden=!isBook;this.root.querySelector('.yds-book-back').hidden=!isBook;this.main.setAttribute('aria-labelledby','yds-tab-'+this.ui.tab);")
    replace("var next=id?this.root.querySelector('#'+id):null;", """var next=id?document.getElementById(id):null;
    if(!next&&active&&active.type==='radio'&&active.name)next=Array.from(this.main.querySelectorAll('input[type="radio"]')).find(function(el){return el.name===active.name&&el.value===active.value;});
    """)
    replace("    if(this.book)this.book.addEventListener('click',function(event){var audio=", """    this.root.querySelector('#yds-visual-dialog').addEventListener('cancel',function(event){event.preventDefault();self.closeVisual();});
    if(this.book)this.book.addEventListener('click',function(event){var zoom=event.target.closest('[data-legacy-visual]');if(zoom){self.openVisual(zoom.dataset.legacyVisual);return;}var audio=""")
    replace("if(this.root.scrollIntoView)this.root.scrollIntoView({behavior:'auto',block:'start'});", """if(el.getAttribute('role')!=='tab')this.root.querySelector('#yds-tab-'+this.ui.tab).focus({preventScroll:true});this.root.scrollIntoView({behavior:'instant',block:'start'});""")
    # Deliver the dataset before the app's initialization, independent of its media mode.
    payload = json.dumps(study, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    replace("  var instance = null;", "  window.YDS_TRANSFER_CONTENT="+payload+";\n  var instance = null;")
    return html
