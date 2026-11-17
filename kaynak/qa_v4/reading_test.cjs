const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM,VirtualConsole}=require('jsdom');

const source=fs.readFileSync(process.argv[2],'utf8').replace(/data:(?:audio\/mpeg|image\/[a-z]+);base64,[a-z0-9+/=]+/gi,'data:,');
const store=new Map();
const problems=[];
function openBook() {
  const console=new VirtualConsole();
  console.on('jsdomError',e=>problems.push(e.message));
  return new JSDOM(source,{
    url:'https://yds.local/',runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:console,
    beforeParse(w){
      Object.defineProperty(w,'localStorage',{value:{getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,v)}});
      w.HTMLElement.prototype.scrollIntoView=function(){w.lastScrolled=this.id};
      w.HTMLMediaElement.prototype.pause=function(){};
      w.HTMLMediaElement.prototype.load=function(){};
    }
  });
}

let dom=openBook(), w=dom.window, doc=w.document;
const selector='main section.chapter[id],main :is(h2,h3,h4)[id],main article:is(.vocab,.question)[id]';
for(let day=1;day<=5;day++){
  doc.querySelector('[data-action="read-day"][data-day="'+day+'"]').click();
  assert.equal(w.lastScrolled,'day'+day);
  assert.equal(doc.getElementById('legacy-book').hidden,false);
  doc.querySelector('[data-reading-action="study"][data-day="'+day+'"]').click();
  assert.equal(doc.querySelector('#yds-study-day').value,String(day));
  assert.equal(doc.querySelector('.yds-app').dataset.view,'study');
  assert.equal(doc.querySelector('#yds-main details.yds-study-guide')?.open||false,false);
  doc.querySelector('[role=tab][data-tab=dashboard]').click();
}
doc.querySelector('[data-action="read-day"][data-day="3"]').click();
const book=doc.getElementById('legacy-book');
let seen=false;
for(const el of book.querySelectorAll(selector)){
  let top=seen?520:-260;
  if(el.id==='V093'){top=55;seen=true}
  el.getClientRects=()=>[1];el.getBoundingClientRect=()=>({top});
}
assert(seen);
book.querySelector('nav').getBoundingClientRect=()=>({top:0,bottom:75});
book.querySelector('[data-reading-action=save]').click();
assert.equal(w.YDSApp.getState().readingMark.id,'V093');
doc.querySelector('[role=tab][data-tab=dashboard]').click();
doc.querySelector('[data-action=read-mark]').click();
assert.equal(w.lastScrolled,'V093');
dom.window.close();
dom=openBook();w=dom.window;doc=w.document;
assert.equal(w.YDSApp.getState().readingMark.id,'V093');
doc.querySelector('[data-action=read-mark]').click();
assert.equal(w.lastScrolled,'V093');
assert.equal(doc.querySelector('[data-reading-resume]').hidden,false);
assert.deepEqual(problems,[]);
dom.window.close();
console.log('Five daily jumps and workshop handoffs, exact saved card, persistence across reopen, and return focus passed.');
