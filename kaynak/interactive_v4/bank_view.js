  App.prototype.assessmentHistoryView = function() {
    var banks=window.YDSAssessmentBanks;
    var book=window.YDSLegacyBridge&&window.YDSLegacyBridge.exportAssessmentHistory();
    var records=banks.archive(this.state.practiceHistory.concat(book||[]));
    if(!records.length)return '';
    return '<details id="yds-assessment-history" class="yds-panel"><summary>Önceki baskıdan korunan kitap yanıtları · '+records.length+'</summary>'
      +'<p>Soru veya metin değiştiğinde eski yanıt burada kendi seçeneği ve anahtarıyla gösterilir. Yeni soruyu yeniden yanıtlayabilirsin.</p>'
      +records.map(function(record){
        var q=banks.questions.get(record.id),hasAnswer=record.choice!==null;
        var option=function(index){return String.fromCharCode(65+index)+' — '+q.options[index];};
        return '<details><summary>'+esc(record.id)+' · '+(record.source==='practice'?'Puanlanan kayıt':'Kitap seçimi')+(record.time?' · '+esc(shortDate(record.time)):'')+'</summary>'
          +'<p>'+esc(q.stem)+'</p>'+(q._group&&q._group.passage?'<details><summary>Önceki metin</summary><p lang="en">'+esc(q._group.passage)+'</p></details>':'')
          +'<p>Eski seçim: '+(hasAnswer?esc(option(record.choice)):'Boş')+(record.confidence?' · Güven: '+esc(record.confidence):'')+'</p>'
          +(hasAnswer?'<p>Önceki anahtara göre '+(record.choice===q.answer?'doğru':'yanlış')+'. Doğru yanıt: '+esc(option(q.answer))+'</p>':'')
          +'</details>';
      }).join('')+'</details>';
  };
