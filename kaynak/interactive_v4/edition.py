"""Join the print book, study screen and versioned assessments into an offline edition."""
from pathlib import Path
import re
from .ux import patch as ux
from . import bank

HERE = Path(__file__).resolve().parent

def assemble(shell, study, previous, current):
    shell = bank.apply(ux.apply(shell, study), previous, current)
    def replace(old, new):
        nonlocal shell
        if shell.count(old) != 1:
            raise ValueError('Unexpected template: '+old[:90])
        shell = shell.replace(old,new,1)

    replace('  App.prototype.dashboard = function() {', (HERE/'reading.js').read_text()+'  App.prototype.dashboard = function() {')
    replace('Bilgiyi tanı.<br>Sonra yardımsız getir.', 'Beş günlük YDS çalışman')
    replace('Kitabın açıklamalarını dinleme, hatırlama ve yeni bağlamda kullanma çalışmalarıyla birleştir. Her seçim ve gerekçe, sonraki tekrarını belirlesin.', 'Günün dersini okuyabilir, görselli kartları dinleyebilir veya son yanlışlarını yeniden çözebilirsin.')
    replace("</div></div><div class=\"yds-stat-grid\">'+[['Kaydı tutulan hedef'", "</div></div>'+this.readingMenu()+'<div class=\"yds-stat-grid\">'+[['Çalışılan kart'")
    replace("    out.updatedAt=finite(raw.updatedAt);", """    var mark=raw.readingMark;
    if(mark && typeof mark.id==='string' && mark.id.length<=200 && this.readingAnchor(mark.id))out.readingMark={id:mark.id,label:String(mark.label||mark.id).slice(0,110),time:finite(mark.time)};
    out.updatedAt=finite(raw.updatedAt);""")
    replace("      Object.entries(incoming.cards).forEach", """      if(incoming.readingMark && (!current.readingMark || incoming.readingMark.time>current.readingMark.time))current.readingMark=incoming.readingMark;
      Object.entries(incoming.cards).forEach""")
    replace("      case 'skip':", """      case 'read-day':this.openReadingAnchor('day'+el.dataset.day);break;
      case 'read-mark':if(this.state.readingMark)this.openReadingAnchor(this.state.readingMark.id);break;
      case 'skip':""")
    replace("    if(!isBook){var views=", "    if(!isBook&&this.book){var oldHistory=this.book.querySelector('#yds-assessment-history');if(oldHistory)oldHistory.remove();}\n    if(!isBook){var views=")
    replace("      var previous=this.book.querySelector(", "      this.refreshReadingLink();\n      var previous=this.book.querySelector(")
    replace("function(event){var zoom=event.target.closest('[data-legacy-visual]');", """function(event){
      var action=event.target.closest('[data-reading-action]');
      if(action){
        if(action.dataset.readingAction==='save')self.saveReadingMark();
        if(action.dataset.readingAction==='resume'&&self.state.readingMark)self.openReadingAnchor(self.state.readingMark.id);
        if(action.dataset.readingAction==='study'){
          Object.assign(self.ui,{tab:'study',studyDay:Number(action.dataset.day),studyIndex:0,studyReview:false,studyReviewIds:[],studyRetry:false,studyAnswer:null,studyReason:''});
          self.render();self.focusContent('#yds-study-heading');
        }
        return;
      }
      var zoom=event.target.closest('[data-legacy-visual]');""")
    replace('<button id="recall"', '<button type="button" data-reading-action="save">Buraya ayraç koy</button><button type="button" data-reading-action="resume" data-reading-resume hidden>Ayraçtan devam et</button><button id="recall"')
    for day in range(1,6):
        pattern=r'(<section class="chapter" id="day'+str(day)+r'">\s*<h1>[^<]*</h1>)'
        shell,n=re.subn(pattern,lambda m:m.group(1)+'<button type="button" data-reading-action="study" data-day="'+str(day)+'">Bu günün aktarım örneklerini aç</button>',shell)
        if n!=1: raise ValueError('Day anchor '+str(day))
    replace('</style></head>', '''.yds-reading-menu{margin:1.1rem 0 1.6rem}.yds-reading-menu h2{margin:0 0 .65rem;font-size:1.24em}.yds-reading-days{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:.5rem}.yds-reading-days button{text-align:left;display:flex;flex-direction:column;gap:.2em;align-items:flex-start;justify-content:flex-start}.yds-reading-days small{color:var(--yds-muted)}.yds-reading-days span{font-weight:650}@media(max-width:450px){.yds-reading-days{grid-template-columns:repeat(2,minmax(0,1fr))}}#legacy-book button[data-reading-action=study]{margin-bottom:.5rem}</style></head>''')
    return shell
