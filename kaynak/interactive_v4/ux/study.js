  App.prototype.studyView = function() {
    var self=this,day=this.studyDays.find(function(d){return d.day===self.ui.studyDay;})||this.studyDays[0];
    if(!day)return '<h2 id="yds-study-heading">Aktarım atölyesi</h2><p>Bu baskıda aktarım alıştırması bulunamadı.</p>';
    var scores=this.state.study;
    var items=this.ui.studyReview?day.items.filter(function(q){return self.ui.studyReviewIds.includes(q.id);}):day.items;
    this.ui.studyIndex=Math.max(0,Math.min(this.ui.studyIndex,items.length-1));
    var item=items[this.ui.studyIndex],state=item&&scores[item.id],answer=this.ui.studyAnswer;
    var applied=day.items.filter(function(q){return q.type==='transfer';});
    var first=applied.filter(function(q){return !!scores[q.id];});
    var correct=first.filter(function(q){return scores[q.id].first===q.correct;}).length;
    var wrong=day.items.filter(function(q){return scores[q.id]&&scores[q.id].choice!==q.correct;}).length;
    var header='<h1 id="yds-study-heading">'+esc(this.study.title||'Aktarım atölyesi')+'</h1><details class="yds-study-guide"><summary>Nasıl çalışılır?</summary><p class="yds-study-instructions">'+esc(this.study.instructions)+'</p></details>';
    header+='<div class="yds-toolbar yds-study-toolbar"><label>Çalışma günü <select id="yds-study-day">'+this.studyDays.map(function(d){return '<option value="'+d.day+'" '+(d===day?'selected':'')+'>Gün '+d.day+' · '+esc(d.name)+'</option>';}).join('')+'</select></label>'+btn('Son yanlışlar · '+wrong,'study-review','aria-pressed="'+!!this.ui.studyReview+'"')+'</div>';
    header+='<p class="yds-muted">'+esc(day.focus)+'</p><p>'+first.length+' / '+applied.length+' aktarım sorusu yanıtlandı. İlk yanıtların '+correct+' tanesi doğru.</p>';
    if(!item)return header+'<div class="yds-empty"><p>Bu gün için yeniden çalışılacak yanlış yok.</p>'+btn('Bütün alıştırmalara dön','study-review','')+'</div>';
    var worked=item.type==='contrast',showing=worked||(!!state&&!this.ui.studyRetry);
    var alternatives=item.options.map(function(option,index){
      var picked=worked?item.correct===index:showing?state.choice===index:answer===index;
      var decoration=showing?(index===item.correct?' <strong>· Doğru yanıt</strong>':picked?' <strong>· Seçimin</strong>':''):'';
      return '<label class="yds-study-option"><input type="radio" name="yds-study-choice" id="yds-study-option-'+index+'" value="'+index+'" '+(picked?'checked ':'')+(showing?'disabled':'')+'><span>'+esc(option)+'</span>'+decoration+'</label>';
    }).join('');
    var review=showing?'<section class="yds-study-feedback" id="yds-study-feedback" tabindex="-1"><h3>'+(worked?'Çözüm':state.choice===item.correct?'Doğru seçim':'Bu ayrımı yeniden incele')+'</h3><p>'+esc(item.feedback)+'</p></section>':'';
    var reasoning=worked?'':showing?(state.reason?'<p class="yds-study-reason"><strong>Gerekçen</strong><br>'+esc(state.reason)+'</p>':''):'<label class="yds-section-label" for="yds-study-reason">Gerekçeni bir cümleyle yaz</label><textarea id="yds-study-reason" class="yds-study-reason" maxlength="1500" rows="3">'+esc(this.ui.studyReason)+'</textarea>';
    var passage=item.prompt.split('\n');
    return header+'<article class="yds-panel yds-study-panel"><p class="yds-muted">'+(this.ui.studyIndex+1)+' / '+items.length+' · '+(worked?'Çözümlü örnek':'Yeni bağlamda uygula')+' · '+esc(item.skill)+'</p><h2 id="yds-study-item" tabindex="-1" class="yds-study-prompt">'+esc(passage.shift())+'</h2>'+passage.map(function(line){return '<p class="yds-study-prompt">'+esc(line)+'</p>';}).join('')+'<fieldset class="yds-study-options"><legend>'+(worked?'Seçenekler':'Yanıtın')+'</legend>'+alternatives+'</fieldset>'+reasoning+review+'<div class="yds-actions">'+btn('Önceki','study-step','data-step="-1" '+(this.ui.studyIndex===0?'disabled':''))+(worked?'':showing?btn('Tekrar çöz','study-retry',''):btn('Yanıtı denetle','study-check','','yds-primary'))+btn(worked?'Aktarım sorusuna geç':'Sonraki','study-step','data-step="1" '+(this.ui.studyIndex===items.length-1?'disabled':''),showing?'yds-primary':'')+'</div></article>';
  };
  App.prototype.studyAction = function(action,el) {
    var self=this,day=this.studyDays.find(function(d){return d.day===self.ui.studyDay;})||this.studyDays[0],scores=this.state.study;
    if(!day)return;
    var items=this.ui.studyReview?day.items.filter(function(q){return self.ui.studyReviewIds.includes(q.id);}):day.items;
    var item=items[this.ui.studyIndex];
    if(action==='study-check'&&item&&item.type==='transfer'){
      if(!Number.isInteger(this.ui.studyAnswer)){this.toast('Önce bir seçenek işaretle.');return;}
      var choice=this.ui.studyAnswer,old=scores[item.id];
      var now=Date.now();
      scores[item.id]={first:old?old.first:choice,firstTime:old?old.firstTime:now,choice:choice,reason:this.ui.studyReason.trim(),time:now};
      this.ui.studyRetry=false;this.ui.studyAnswer=null;this.ui.studyReason='';
      this.activity();this.save();this.render();this.focusContent('#yds-study-feedback');return;
    }
    if(action==='study-step')this.ui.studyIndex+=Number(el.dataset.step);
    if(action==='study-review'){this.ui.studyIndex=0;this.ui.studyReview=!this.ui.studyReview;this.ui.studyReviewIds=day.items.filter(function(q){return scores[q.id]&&scores[q.id].choice!==q.correct;}).map(function(q){return q.id;});}
    this.ui.studyRetry=action==='study-retry';this.ui.studyAnswer=null;this.ui.studyReason='';this.render();
    var target=this.main.querySelector(action==='study-retry'?'#yds-study-option-0':'#yds-study-item');
    if(target)this.focusContent('#'+target.id);
  };
