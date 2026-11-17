/* Parse the exact release HTML with jsdom. Media payloads are separately decoded with ffmpeg/Pillow. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {JSDOM, VirtualConsole} = require('jsdom');
const source = fs.readFileSync(process.argv[2], 'utf8')
  .replace(/(data:(?:audio|image)\/[\w.+-]+;base64,)[\w+/=]+/g, '$1AA==');
const errors = [];
const consoleEvents = new VirtualConsole();
consoleEvents.on('jsdomError', e => errors.push(e.message));
const dom = new JSDOM(source, {
  url: 'https://yds.test/offline', runScripts: 'dangerously', pretendToBeVisual: true,
  virtualConsole: consoleEvents,
  beforeParse(w) {
    w.HTMLElement.prototype.scrollIntoView = function () {};
    w.HTMLMediaElement.prototype.play = function () {
      this.dispatchEvent(new w.Event('playing'));
      return Promise.resolve();
    };
    w.HTMLMediaElement.prototype.pause = function () {};
    w.HTMLMediaElement.prototype.load = function () {};
    w.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
    w.HTMLDialogElement.prototype.close = function () { this.open = false; };
  },
});
try {
  const w = dom.window, d = w.document;
  const find = selector => {
    const result = d.querySelector(selector);
    assert(result, selector);
    return result;
  };
  const click = selector => find(selector).click();
  const action = (name, attrs = '') => click(`[data-action="${name}"]${attrs}`);
  const nav = name => `#yds-tab-${name}`;
  const tab = name => {
    click(nav(name));
    assert.equal(find(nav(name)).getAttribute('aria-selected'), 'true', name);
  };
  const state = () => w.YDSApp.getState();
  const snapshotDir = process.env.YDS_STATIC_SNAPSHOTS;
  const snapshots = [];
  function snapshot(name, width, height) {
    if (!snapshotDir) return;
    const clone = d.documentElement.cloneNode(true);
    clone.querySelectorAll('script,[hidden],dialog:not([open])').forEach(node => node.remove());
    clone.querySelectorAll('img[data-visual-id]').forEach(img => {
      const local = path.resolve(__dirname, '../../images', img.dataset.visualId + '.png');
      if (fs.existsSync(local)) img.src = pathToFileURL(local).href;
    });
    fs.mkdirSync(snapshotDir, {recursive: true});
    const file = path.resolve(snapshotDir, name + '.html');
    fs.writeFileSync(file, '<!doctype html>' + clone.outerHTML);
    snapshots.push({name, width, height, file});
  }
  assert.equal(d.documentElement.lang, 'tr');
  assert.equal(find(nav('dashboard')).getAttribute('aria-selected'), 'true');
  snapshot('dashboard_mobile', 390, 844);
  find(nav('dashboard')).focus();
  find(nav('dashboard')).dispatchEvent(new w.KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
  assert.equal(find(nav('cards')).getAttribute('aria-selected'), 'true');
  assert.equal(d.activeElement.id, 'yds-tab-cards');
  assert(find('.yds-study-visual img').alt.length > 0);
  snapshot('card_desktop', 1440, 900);
  const button = find('.yds-study-visual button');
  button.focus();
  button.click();
  const dialog = find('#yds-visual-dialog');
  assert(dialog.open);
  dialog.dispatchEvent(new w.Event('cancel', { cancelable: true }));
  assert(!dialog.open);
  assert.equal(d.activeElement, button);
  const word = find('#yds-main [data-yds-play][data-yds-kind="word"]');
  word.focus();
  word.click();
  const clip = w.YDS_BOOK_DATA.audio.items[word.dataset.ydsPlay][word.dataset.ydsKind];
  assert.equal(find('audio').getAttribute('src'), clip.src);
  assert.match(find('#yds-audio-status').textContent, /Çalıyor/);
  action('audio-close');
  assert.equal(d.activeElement, word);
  assert(!find('audio').hasAttribute('src'));
  action('favorite');
  assert(Object.values(state().cards).some(card => card.favorite));
  for (const name of ['audio', 'challenge', 'notes', 'book']) tab(name);
  assert(!find('#legacy-book').hidden);
  click('.yds-book-back');
  assert(find('#legacy-book').hidden);
  tab('study');
  assert.equal(find('#yds-study-day').options.length, 5);
  assert(find('#yds-study-feedback'));
  action('study-step', '[data-step="1"]');
  assert(!d.querySelector('#yds-study-feedback'));
  const transfer = w.YDS_TRANSFER_CONTENT.days[0].items[1];
  click(`#yds-study-option-${(transfer.correct + 1) % transfer.options.length}`);
  const reason = find('#yds-study-reason');
  reason.value = 'Gerçek DOM gerekçe sınaması.';
  reason.dispatchEvent(new w.Event('input', {bubbles: true}));
  action('study-check');
  assert.match(find('#yds-study-feedback').textContent, /yeniden incele/);
  assert.match(find('.yds-study-reason').textContent, /Gerçek DOM gerekçe sınaması/);
  assert.equal(d.activeElement.id, 'yds-study-feedback');
  snapshot('transfer_mobile', 390, 844);
  action('study-review');
  action('study-retry');
  click(`#yds-study-option-${transfer.correct}`);
  action('study-check');
  assert.equal(state().study[transfer.id].choice, transfer.correct);
  assert.notEqual(state().study[transfer.id].first, transfer.correct);
  tab('exam');
  action('start-exam');
  assert.equal(d.querySelectorAll('[data-action="exam-jump"]').length, 80);
  snapshot('exam_mobile', 390, 844);
  const q = w.YDS_BOOK_DATA.assessment.simulation.groups[0].questions[0];
  click(`[data-exam-choice="${q.id}"][value="${q.answer}"]`);
  action('flag-question');
  action('pause-exam');
  action('resume-exam');
  action('exam-step', '[data-step="1"]');
  action('exam-jump', '[data-index="0"]');
  assert(find(`[data-exam-choice="${q.id}"][value="${q.answer}"]`).checked);
  action('submit-exam');
  action('confirm-submit');
  assert(find(`[data-exam-choice="${q.id}"][value="${q.answer}"]`).disabled);
  assert.equal(state().firstAttempt.answers[q.id], q.answer);
  assert.equal(JSON.parse(w.localStorage.getItem('yds-son5-interactive-v2')).firstAttempt.answers[q.id], q.answer);
  assert.deepEqual(errors, []);
  if (snapshotDir) fs.writeFileSync(path.join(snapshotDir, 'static_view_manifest.json'), JSON.stringify({views: snapshots}));
  console.log(JSON.stringify({
    mode: 'jsdom runtime with exact release source, compact media placeholders and stubbed native media events',
    checks: ['boot and all tabs', 'keyboard navigation and focus', 'visual dialog cancel and focus return',
      'offline audio mapping and dock interactions', 'favorite and book navigation',
      'transfer DOM events, hidden explanation, reason, review, retry and first answer',
      '80 exam controls, answer, flag, pause, jump, submission, read-only choices and local data',
      'zero jsdom errors'],
  }, null, 2));
} finally {
  dom.window.close();
}
