"""Bind each saved assessment response to the question edition it was taken on."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _payload(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def _question_index(assessment):
    index = {
        question["id"]: (question, "", "")
        for group in [assessment["diagnostic"], *assessment["daily"].values()]
        for question in group
    }
    for group in assessment["simulation"]["groups"]:
        index.update({
            question["id"]: (question, group["passage"], group["instructions"])
            for question in group["questions"]
        })
    return index


def migration_map(previous, current):
    """Absent IDs are identical. Map compatible old choices, mark changed items null."""
    old, new = _question_index(previous), _question_index(current)
    if old.keys() != new.keys():
        raise ValueError("The migration requires stable question IDs")
    mapping = {}
    for item_id, (first, passage, instructions) in old.items():
        second, new_passage, new_instructions = new[item_id]
        if (first["stem"], first.get("passage"), passage, instructions) != (
            second["stem"], second.get("passage"), new_passage, new_instructions
        ) or set(first["options"]) != set(second["options"]):
            mapping[item_id] = None
            continue
        indices = [second["options"].index(option) for option in first["options"]]
        if indices[first["answer"]] != second["answer"]:
            mapping[item_id] = None
        elif indices != list(range(len(indices))):
            mapping[item_id] = indices
    return mapping


def apply(html: str, previous: dict, current: dict) -> str:
    def replace(old, new):
        nonlocal html
        if html.count(old) != 1:
            raise ValueError(f"Expected exactly one assessment marker: {old[:140]}")
        html = html.replace(old, new, 1)

    initialization = "const KEY='yds-son5-2026-v1';"
    data = {'diagnostic': previous['diagnostic'], 'daily': previous['daily'], 'simulation': previous['simulation']}
    replace(initialization, "const historical="+_payload(data)+",migration="+_payload(migration_map(previous,current))+";\n"
            +(HERE/"bank_runtime.js").read_text(encoding="utf-8")+initialization)
    replace("catch(e){}function persist()", "catch(e){}state=migrateBook(state);function persist()")
    replace("    getLastImportReport:function()", "    exportAssessmentHistory:function(){return archive(state.assessmentHistory);},\n    getLastImportReport:function()")
    replace("const out={};fields().forEach", "const out={assessmentBank:4,assessmentHistory:archive(state.assessmentHistory)};fields().forEach")
    replace("      options=options||{};\n      fields()", """      options=options||{};
      raw=migrateBook(raw);
      state.assessmentHistory=archive(state.assessmentHistory.concat(raw.assessmentHistory));
      fields()""")
    # Store migration and its marker together in the same legacy storage object.
    replace("  return {\n    exportState:function()", "  persist();\n  return {\n    exportState:function()")
    replace("window.YDSApp={version:'3.0'", "window.YDSApp={version:'4.0'")
    replace("this.data.version||'2.0'", "this.data.version||'4.0'")
    replace("version:version || '2.0'", "version:version || '4.0',practiceBank:4,practiceHistory:[]")
    replace("function newExam() { return {updatedAt:", "function newExam() { return {bank:4,updatedAt:")
    replace("""    this.questions = []; this.groups.forEach(function(g){g.questions.forEach(function(q){this.questions.push(Object.assign({_group:g},q));},this);},this);
    this.qmap = new Map(this.questions.map(function(q){return [q.id,q];}));""", """    this.currentQuestions = window.YDSAssessmentBanks.flattenExam(this.data.assessment);
    this.oldQuestions = window.YDSAssessmentBanks.flattenExam(window.YDSAssessmentBanks.historical);""")
    replace("Object.values(a.daily || {}).flat(),this.questions)", "Object.values(a.daily || {}).flat(),this.currentQuestions)")
    replace("  App.prototype.validateState = function(raw)", """  App.prototype.examQuestions = function(exam) {
    return exam && exam.bank===3 ? this.oldQuestions : this.currentQuestions;
  };
  Object.defineProperty(App.prototype,'questions',{get:function(){return this.examQuestions(this.state.exam);}});
  App.prototype.validateState = function(raw)""")
    replace("if(!rawExam||typeof rawExam!=='object')return e;['startedAt'", "if(!rawExam||typeof rawExam!=='object')return e;e.bank=Number(rawExam.bank)===3||((finite(rawExam.startedAt)||finite(rawExam.submittedAt))&&Number(rawExam.bank)!==4)?3:4;['startedAt'")
    replace("self.questions.length-1,Number(rawExam.index)", "self.examQuestions(e).length-1,Number(rawExam.index)")
    replace("self.questions.forEach(function(q){var v=(rawExam.answers", "self.examQuestions(e).forEach(function(q){var v=(rawExam.answers")
    replace("this.qmap.get(el.dataset.examChoice)", "this.questions.find(function(q){return q.id===el.dataset.examChoice;})")
    replace("this.questions.forEach(function(q){var g=q._group.type", "this.examQuestions(e).forEach(function(q){var g=q._group.type")
    replace("else if(next.startedAt&&next.startedAt===previous.startedAt){", """else if(next.startedAt&&next.startedAt===previous.startedAt){
        if(next.bank!==previous.bank){examMessage='Aynı başlangıç zamanına ait farklı soru sürümleri birleştirilmedi.';}
        else""")
    replace("'+r.correct+'/'+this.questions.length+' doğru", "'+r.correct+'/'+this.examQuestions(e).length+' doğru")
    replace("'+shortDate(e.submittedAt)+'</p><p class=\"yds-safe-note\">Yeni prova", "'+shortDate(e.submittedAt)+' · Soru sürümü '+e.bank+'</p><p class=\"yds-safe-note\">Yeni prova")
    replace("+(submitted?'Yanıtlar sabitlendi':paused?'Duraklatıldı':'Süre işliyor')+", "+'Sürüm '+e.bank+' · '+(submitted?'Yanıtlar sabitlendi':paused?'Duraklatıldı':'Süre işliyor')+")
    replace("self.questionNote(q,choice,e.confidence[q.id],'PROVA-');", "self.questionNote(q,choice,e.confidence[q.id],e.bank===3?'PROVA-':'PROVA4-');")
    replace("    Object.entries(raw.practice||{}).forEach", """    var banks=window.YDSAssessmentBanks;
    var history=banks.archive(raw.practiceHistory);
    Object.entries(raw.practice||{}).forEach""")
    replace("if(q&&r&&Number.isInteger(r.choice)&&r.choice>=0&&r.choice<q.options.length)out.practice[pair[0]]={choice:r.choice,correct:r.choice===q.answer,confidence:String(r.confidence||''),time:Number(r.time)||0};});", """if(!q||!r||!Number.isInteger(r.choice)||r.choice<0||r.choice>=q.options.length)return;
      var choice=r.choice,time=finite(r.time),certain=banks.confidence(r.confidence);
      if(Number(raw.practiceBank)!==4&&Object.prototype.hasOwnProperty.call(banks.migration,pair[0])){
        var order=banks.migration[pair[0]];
        if(!order){history.push({id:pair[0],choice:choice,confidence:certain,time:time,source:'practice'});return;}
        choice=order[choice];
      }
      out.practice[pair[0]]={choice:choice,correct:choice===q.answer,confidence:certain,time:time};
    });
    out.practiceHistory=banks.archive(history);""")
    replace("      Object.entries(incoming.practice).forEach", """      current.practiceHistory=window.YDSAssessmentBanks.archive(current.practiceHistory.concat(incoming.practiceHistory));
      Object.entries(incoming.practice).forEach""")
    replace("self.questionNote(q,choice,label,'KİTAP-');", "self.questionNote(q,choice,label,'KİTAP4-');")
    replace("  App.prototype.notesView = function() {", (HERE/"bank_view.js").read_text(encoding="utf-8")+"  App.prototype.notesView = function() {")
    replace("return '<p class=\"yds-kicker\">Hata defteri</p>", "return this.assessmentHistoryView()+'<p class=\"yds-kicker\">Hata defteri</p>")
    replace("    this.updateStorageStatus();this.updateTimer();this.maskAudio();", """    if(this.book){
      var previous=this.book.querySelector('#yds-assessment-history');
      if(previous)previous.remove();
      var history=isBook?this.assessmentHistoryView():'';
      if(history)this.book.insertAdjacentHTML('afterbegin',history);
    }
    this.updateStorageStatus();this.updateTimer();this.maskAudio();""")
    return html
