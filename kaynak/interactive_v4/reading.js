  App.prototype.readingAnchor = function(id) {
    if (!this.book || typeof id !== 'string') return null;
    var element = document.getElementById(id);
    return element && this.book.contains(element) ? element : null;
  };
  App.prototype.openReadingAnchor = function(id) {
    var target = this.readingAnchor(id);
    if (!target) return;
    this.ui.tab = 'book';
    this.render();
    target.tabIndex = -1;
    target.focus({preventScroll:true});
    target.scrollIntoView({block:'start',behavior:'instant'});
  };
  App.prototype.saveReadingMark = function() {
    var nav = this.book.querySelector('nav');
    var navRect = nav.getBoundingClientRect();
    var readingLine = Math.min(innerHeight * .55, Math.max(innerHeight * .22, navRect.top <= 10 ? navRect.bottom + 10 : 0));
    var anchors = this.book.querySelectorAll('main section.chapter[id],main :is(h2,h3,h4)[id],main article:is(.vocab,.question)[id]');
    if (!anchors.length) return;
    var chosen = anchors[0];
    for (var anchor of anchors) {
      if (!anchor.getClientRects().length) continue;
      if (anchor.getBoundingClientRect().top > readingLine) break;
      chosen = anchor;
    }
    var title = chosen.matches('h2,h3,h4') ? chosen : chosen.querySelector('h1,h2,h3,p strong');
    var label = (title ? title.textContent : chosen.id).trim().slice(0,110);
    this.state.readingMark = {id:chosen.id, label:label, time:Date.now()};
    this.save();
    this.toast('Ayraç kaydedildi · '+label);
    this.refreshReadingLink();
  };
  App.prototype.refreshReadingLink = function() {
    if (!this.book) return;
    var marker = this.book.querySelector('[data-reading-resume]');
    if (marker) {
      marker.hidden = !this.state.readingMark;
      if(this.state.readingMark) marker.title=this.state.readingMark.label;
    }
  };
  App.prototype.readingMenu = function() {
    var mark=this.state.readingMark;
    var days=['Cümle ve kanıt','Neden ve koşul','İç içe yapılar','Metin ve çıkarım','Kümülatif tekrar'];
    return '<section class="yds-reading-menu" aria-label="Kitabın günlük dersleri"><h2>Günün dersini aç</h2><div class="yds-reading-days">'+days.map(function(name,i){
      return btn('<small>'+DAY[i+1]+'</small><span>'+name+'</span>','read-day','data-day="'+(i+1)+'"');
    }).join('')+'</div>'+(mark?'<div class="yds-actions">'+btn('Ayraçtan devam et · '+esc(mark.label),'read-mark','','yds-primary')+'</div>':'')+'</section>';
  };
