/* Run with NODE_PATH pointing to an installed jsdom and the path to the assembled v4 HTML. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM, VirtualConsole} = require('jsdom');
const html = fs.readFileSync(process.argv[2], 'utf8')
  .replace(/data:(?:audio\/mpeg|image\/[a-z]+);base64,[A-Za-z0-9+/=]+/g, 'data:,');
const archive = require('../assessment_v3_archive.json');
const current = require('../assessment.json');
const oldFirst = archive.simulation.groups[0].questions[0];
const newFirst = current.simulation.groups[0].questions[0];
const replaced = archive.diagnostic.concat(Object.values(archive.daily).flat()).find(q => q.id === 'G2-18');
const untouched = archive.diagnostic[0];
assert.notEqual(oldFirst.answer,newFirst.answer);
const appKey = 'yds-son5-interactive-v2';
const bookKey = 'yds-son5-2026-v1';
const now = 1_795_000_000_000;
const attempt = {startedAt:now-100000,updatedAt:now-1000,runningSince:now-5000,elapsed:120000,
  submittedAt:0, answers:{[oldFirst.id]:oldFirst.answer},confidence:{[oldFirst.id]:'Düşük'},flags:{[oldFirst.id]:true},index:0};
const legacyState = {schema:2,version:'3.0',updatedAt:now-1000,exam:attempt,
  firstAttempt:{...attempt,startedAt:now-1000000,submittedAt:now-200000,runningSince:0},
  practice:{[oldFirst.id]:{choice:oldFirst.answer,time:12,confidence:'Orta'},
    [replaced.id]:{choice:replaced.answer,time:14,confidence:'Yüksek'}}};
const legacyBook = {[oldFirst.id]:String(oldFirst.answer),['conf-'+oldFirst.id]:'Düşük',
  [replaced.id]:String(replaced.answer),['conf-'+replaced.id]:'Yüksek',
  [untouched.id]:String(untouched.answer),'conf-S17':'Orta'};
const errors=[];
const clone = value => JSON.parse(JSON.stringify(value));
function open(state,book){
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => errors.push(error.message));
  return new JSDOM(html,{url:'https://yds.test/local',runScripts:'dangerously',virtualConsole,beforeParse(w){
    w.Date.now=()=>now;
    w.HTMLMediaElement.prototype.play=()=>Promise.resolve();
    w.HTMLMediaElement.prototype.pause=()=>{};
    w.HTMLMediaElement.prototype.load=()=>{};
    w.HTMLElement.prototype.scrollIntoView=()=>{};
    if(state)w.localStorage.setItem(appKey,JSON.stringify(state));
    if(book)w.localStorage.setItem(bookKey,JSON.stringify(book));
    Object.defineProperty(w,'YDSApp',{configurable:true,set(v){
      const init=v.init;v.init=function(options){return (w.capturedApp=init.call(v,options));};
      Object.defineProperty(w,'YDSApp',{value:v,writable:true,configurable:true});
    }});
  }});
}
async function exported(w,app){
  let backup;
  w.URL.createObjectURL=blob=>{backup=blob;return 'blob:https://yds.test/test';};
  w.URL.revokeObjectURL=()=>{};
  w.HTMLAnchorElement.prototype.click=()=>{};
  app.exportProgress();
  assert.ok(backup,'Expected a JSON export Blob');
  return await new Promise((resolve,reject)=>{
    const reader=new w.FileReader();
    reader.onload=()=>resolve(JSON.parse(reader.result));
    reader.onerror=reject;
    reader.readAsText(backup);
  });
}
function tab(w,id){w.document.querySelector('[data-action=tab][data-tab='+id+']').click();}
function assertExam(app,bank){
  assert.equal(app.state.exam.bank,bank);
  assert.equal(app.state.firstAttempt.bank,3);
  assert.equal(app.examStats(app.state.firstAttempt).correct,1);
  assert.equal(app.examStats(app.state.firstAttempt).lowCorrect,1);
}
async function run(){
  const first=open(legacyState,legacyBook),w=first.window,app=w.capturedApp;
  assert.ok(app,errors.join('\n'));
  assert.equal(w.YDSApp.version,'4.0');
  assert.equal(w.YDS_BOOK_DATA.version,'4.0');
  assertExam(app,3);
  assert.equal(app.elapsed(),125000);
  assert.equal(app.state.exam.flags.S01,true);
  tab(w,'exam');
  assert.deepEqual(Array.from(w.document.querySelectorAll('[data-exam-choice]')).map(i=>i.parentElement.lastElementChild.textContent),oldFirst.options);
  assert.equal(w.document.querySelector('[data-exam-choice]:checked').value,String(oldFirst.answer));
  assert.equal(w.document.querySelector('#yds-exam-clock').textContent,'177:55');
  assert.equal(app.state.practice.S01.choice,newFirst.answer);
  assert.equal(app.state.practice.S01.correct,true);
  assert.equal(app.state.practice['G2-18'],undefined);
  assert.equal(app.state.practiceHistory[0].confidence,'Yüksek');
  tab(w,'book');
  assert.equal(w.document.querySelector('input[name=S01]:checked').value,String(newFirst.answer));
  assert.equal(w.document.querySelector('input[name='+untouched.id+']:checked').value,String(untouched.answer));
  assert.equal(w.document.querySelector('input[name=G2-18]:checked'),null);
  const history=w.document.querySelector('#yds-assessment-history');
  assert.ok(history.textContent.includes(replaced.stem));
  assert.ok(history.textContent.includes('Önceki anahtara göre doğru'));
  assert.ok(history.textContent.includes('Güven: Orta'));
  tab(w,'notes');
  assert.equal(w.document.querySelectorAll('#yds-assessment-history').length,1);
  tab(w,'exam');
  app.submitExam('manual');
  assert.equal(app.examStats(app.state.exam).correct,1);
  w.document.querySelector('[data-action=new-exam]').click();
  w.document.querySelector('[data-action=start-exam]').click();
  assertExam(app,4);
  assert.equal(app.questions[0].answer,newFirst.answer);
  assert.deepEqual(Array.from(w.document.querySelectorAll('[data-exam-choice]')).map(i=>i.parentElement.lastElementChild.textContent),newFirst.options);
  const snapshot=await exported(w,app);
  assert.equal(snapshot.version,'4.0');
  assert.equal(snapshot.state.exam.bank,4);
  assert.equal(snapshot.state.practiceBank,4);
  assert.equal(snapshot.legacy.assessmentBank,4);
  const second=open(),other=second.window,app2=other.capturedApp;
  async function receive(payload){await app2.importProgress({size:1000,text:async()=>JSON.stringify(payload)});}
  await receive(snapshot);
  assertExam(app2,4);
  assert.equal(app2.state.practice.S01.choice,newFirst.answer);
  assert.equal(app2.state.practiceHistory.length,1);
  assert.equal(other.YDSLegacyBridge.exportState().S01,String(newFirst.answer));
  assert.equal(other.YDSLegacyBridge.exportAssessmentHistory().length,2);
  await receive({type:'YDS_PROGRESS',schema:2,state:legacyState,legacy:legacyBook});
  assertExam(app2,4);
  assert.equal(app2.state.practiceHistory.length,1);
  assert.equal(other.YDSLegacyBridge.exportAssessmentHistory().length,2);
  assert.equal(other.YDSLegacyBridge.exportState().S01,String(newFirst.answer));
  assert.equal(Object.hasOwn(other.YDSLegacyBridge.exportState(),'G2-18'),false);
  const conflict=clone(snapshot);
  conflict.state.exam.bank=3;
  conflict.state.exam.updatedAt+=10000;
  conflict.state.exam.answers.S01=oldFirst.answer;
  await receive(conflict);
  assertExam(app2,4);
  assert.equal(app2.state.exam.answers.S01,undefined);
  other.close(); w.close();
  assert.deepEqual(errors,[]);
  console.log('✓ Old exam options, timer, score, flags, first attempt, revised exam, book permutation, incompatible-response archive, confidence-only archive, and repeat import');
}
run().catch(e=>{console.error(e);process.exit(1);});
