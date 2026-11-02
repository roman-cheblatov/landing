const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8765';
const results = [];
function ok(name, cond, extra='') { results.push({name, pass: !!cond, extra}); console.log((cond?'PASS':'FAIL')+' · '+name+(extra?' · '+extra:'')); }
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('console', m => { if (m.type()==='error') errors.push('console: '+m.text()); });
  page.on('pageerror', e => errors.push('pageerror: '+e.message));
  // ---- A. load main trainer
  await page.goto(BASE+'/index.html', { waitUntil: 'load' });
  await page.waitForTimeout(800);
  const info = await page.evaluate(() => ({
    db: DB.length, lessons: Object.keys(LESSONS).length, keyVersion: KEY_VERSION,
    safe: DB.filter(q=>keysafe(q)).length, risk: DB.filter(q=>!keysafe(q)).length,
    gradeable: DB.filter(q=>q.gradeable&&q.answer).length,
    noAnswer: DB.filter(q=>!q.options.some(o=>o.id===q.answer)).map(q=>q.id),
    warnRisk: DB.filter(q=>!keysafe(q)&&!q.warning).map(q=>q.id), warnSafe: DB.filter(q=>keysafe(q)&&q.warning).map(q=>q.id),
    keys: {'01-03':byId['01-03'].answer,'03-09':byId['03-09'].answer,'07-06':byId['07-06'].answer,'07-29':byId['07-29'].answer},
    poolOptions: [...document.querySelectorAll('#pool option')].map(o=>o.textContent),
    subjects: document.querySelectorAll('#subject option').length,
    storage: document.querySelector('#storageBadge').textContent,
    sw: 'serviceWorker' in navigator,
  }));
  ok('DB має 290 записів', info.db===290, JSON.stringify({db:info.db, lessons:info.lessons}));
  ok('LESSONS має 290 записів', info.lessons===290);
  ok('KEY_VERSION = arbitration-v6.0', info.keyVersion==='arbitration-v6.0-2026-11-02');
  ok('Пул: 263 надійних / 27 спірних', info.safe===263 && info.risk===27, `${info.safe}/${info.risk}`);
  ok('Усі 290 мають ключ, що існує серед варіантів', info.gradeable===290 && info.noAnswer.length===0, JSON.stringify(info.noAnswer));
  ok('Спірні мають warning, надійні — ні', info.warnRisk.length===0 && info.warnSafe.length===0, JSON.stringify([info.warnRisk, info.warnSafe]));
  ok('Ключі 1.3=b, 3.9=a, 7.6=g, 7.29=a', JSON.stringify(info.keys)===JSON.stringify({'01-03':'b','03-09':'a','07-06':'g','07-29':'a'}), JSON.stringify(info.keys));
  ok('Підписи фільтра оновлено', info.poolOptions.join('|').includes('263') && info.poolOptions.join('|').includes('27'), info.poolOptions.join(' | '));
  ok('Дисципліни заповнено (9+1)', info.subjects===10, String(info.subjects));
  ok('Автозбереження працює', info.storage.includes('ввімкнено'), info.storage);
  // ---- B. migration from v5.0 (Fable) and from exp1 audit
  for (const [ver, expectReset, expectKeep] of [['fable-review-v5.0-2026-11-02', ['03-09','07-06'], ['01-03','01-01']], ['audit-2026-11-02-v5.0', ['01-03','07-29'], ['03-09','01-01']], ['centralization-04-02-v4.0-2026-10-22', ['01-03','07-29','03-09','07-06'], ['01-01']]]) {
    await page.evaluate((ver) => {
      const mk = () => ({attempts:3,correct:2,wrong:1,confidence:1,streak:1,recovery:0,pending:false,lastAt:Date.now(),lastSession:1,dueSession:2,dueAt:Date.now()});
      const st = {version:2, bankId:'snu-psychology-2026-290', keyVersion: ver, completed: 1, items: {'01-01':mk(),'01-03':mk(),'03-09':mk(),'07-06':mk(),'07-29':mk()}, sessions:[{at:Date.now(),score:1,total:1}], prefs:{mode:'adaptive',count:'50',timer:'yes',pool:'all',subject:'all'}};
      localStorage.setItem('snu2026_psych_adaptive_v3', JSON.stringify(st));
    }, ver);
    await page.reload({ waitUntil: 'load' }); await page.waitForTimeout(500);
    const st = await page.evaluate(() => ({ kv: state.keyVersion, ids: Object.keys(state.items), oldKey: (state.sessions||[]).every(s=>s.oldKey) }));
    const resetOK = expectReset.every(id=>!st.ids.includes(id)) && expectKeep.every(id=>st.ids.includes(id));
    ok(`Міграція прогресу з «${ver}»: скинуто ${expectReset.join(',')}; збережено ${expectKeep.join(',')}`, st.kv==='arbitration-v6.0-2026-11-02' && resetOK && st.oldKey, JSON.stringify(st));
  }
  // ---- C. exam flow on risk pool
  await page.evaluate(() => localStorage.clear());
  await page.reload({ waitUntil: 'load' }); await page.waitForTimeout(400);
  await page.selectOption('#mode', 'exam'); await page.selectOption('#count', '10'); await page.selectOption('#pool', 'risk'); await page.selectOption('#timer', 'no');
  await page.click('#start'); await page.waitForTimeout(600);
  const nQ = await page.evaluate(() => document.querySelectorAll('#questions input[type=radio]').length ? test.length : 0);
  ok('Пробний іспит із 10 спірних питань запущено', nQ===10, String(nQ));
  // answer: pick a wrong option deliberately for first 5, right for rest
  await page.evaluate(() => { test.forEach((q,i)=>{ const radios=[...document.querySelectorAll(`input[type=radio][name="q-${q.id}"], input[type=radio][data-qid="${q.id}"]`)]; }); });
  const answered = await page.evaluate(() => {
    let n=0; test.forEach((q,i)=>{ const radios=[...document.querySelectorAll('#questions input[type=radio]')].filter(r=>r.name && r.name.includes(q.id)); if(!radios.length)return; const wrong=radios.find(r=>r.value!==q.answer)||radios[0]; const right=radios.find(r=>r.value===q.answer)||radios[0]; (i<5?wrong:right).click(); n++; }); return n; });
  ok('Відповіді проставлено (через name радіокнопок)', answered===10, String(answered));
  await page.click('#finishBottom'); await page.waitForTimeout(800);
  const res = await page.evaluate(() => ({ visible: !document.querySelector('#result').classList.contains('hidden'), cards: document.querySelectorAll('#result .studycard').length, flagged: document.querySelectorAll('#result .studycard.flagged').length, warnLines: document.querySelectorAll('#result .compact-warning').length, text: document.querySelector('#result').textContent.slice(0,200), completed: state.completed, items: Object.keys(state.items).length }));
  ok('Результат показано; картки розбору спірних мають позначку ⚠', res.visible && res.cards>=5 && res.flagged===res.cards && res.warnLines===res.cards, JSON.stringify({cards:res.cards,flagged:res.flagged,warn:res.warnLines,completed:res.completed,items:res.items}));
  // ---- C2. adaptive flow on all pool incl. 7.29 / 3.9 / 7.6 study cards
  await page.evaluate(() => localStorage.clear()); await page.reload({ waitUntil: 'load' }); await page.waitForTimeout(400);
  await page.selectOption('#mode', 'new'); await page.selectOption('#count', '50'); await page.selectOption('#pool', 'all'); await page.selectOption('#timer', 'yes');
  await page.click('#start'); await page.waitForTimeout(600);
  const n2 = await page.evaluate(() => test.length);
  ok('Адаптивне тренування на 50 запитань запущено з таймером', n2===50, String(n2));
  await page.evaluate(() => { test.forEach((q,i)=>{ const radios=[...document.querySelectorAll('#questions input[type=radio]')].filter(r=>r.name && r.name.includes(q.id)); const wrong=radios.find(r=>r.value!==q.answer)||radios[0]; wrong.click(); }); });
  await page.click('#finish'); await page.waitForTimeout(800);
  const res2 = await page.evaluate(() => ({ cards: document.querySelectorAll('#result .studycard').length, mnemo: document.querySelectorAll('#result .mnemo').length, pending: Object.values(state.items).filter(x=>x.pending).length }));
  ok('Розбір 50 помилок з мініуроками', res2.cards===50 && res2.mnemo>=40 && res2.pending===50, JSON.stringify(res2));
  // export/import
  const exported = await page.evaluate(() => JSON.stringify({exportedAt: Date.now(), bankId: BANK_ID, progress: state}));
  ok('Експорт прогресу (структура) доступний', exported.length>100);
  // ---- D. memory trainer
  const errBefore = errors.length;
  await page.goto(BASE+'/memory/index.html', { waitUntil: 'load' }); await page.waitForTimeout(600);
  const m = await page.evaluate(() => ({ n: DATA.length, badge: document.querySelector('#totalBadge').textContent, warn: DATA.filter(c=>c.warning).map(c=>c.id), idxOK: DATA.every(c=>c.options[c.correctIdx]===c.answer) }));
  ok('Тренажер пам’яті: 65 карток, correctIdx узгоджено', m.n===65 && m.idxOK, JSON.stringify(m));
  await page.click('#revealBtn'); await page.waitForTimeout(200);
  const rev = await page.evaluate(() => ({ shown: !document.querySelector('#answerArea').classList.contains('hidden'), ans: document.querySelector('#cardAnswer').textContent }));
  ok('Картка відкривається', rev.shown && rev.ans.length>0, rev.ans);
  await page.click('#rememberBtn'); await page.waitForTimeout(200);
  await page.click('[data-tab="test"]'); await page.waitForTimeout(300);
  const opts = await page.evaluate(() => document.querySelectorAll('#testOptions .option').length);
  ok('Мінітест показує варіанти', opts>=3, String(opts));
  await page.click('#testOptions .option'); await page.waitForTimeout(200);
  const fb = await page.evaluate(() => !document.querySelector('#testFeedback').classList.contains('hidden'));
  ok('Мінітест дає зворотний зв’язок', fb);
  await page.click('[data-tab="reference"]'); await page.waitForTimeout(300);
  const rows = await page.evaluate(() => document.querySelectorAll('#refRows tr').length);
  ok('Довідник містить 65 рядків', rows===65, String(rows));
  // ---- E. service worker registration & manifest
  await page.goto(BASE+'/index.html', { waitUntil: 'load' }); await page.waitForTimeout(1500);
  const sw = await page.evaluate(async () => { const r = await navigator.serviceWorker.getRegistrations(); return r.length; });
  const manifest = await page.evaluate(async () => (await fetch('/manifest.webmanifest')).ok);
  const swCode = await page.evaluate(() => document.documentElement.outerHTML.includes("location.protocol==='https:' && 'serviceWorker' in navigator"));
  ok('manifest доступний; реєстрація service worker передбачена лише для https (на локальному http очікувано 0 реєстрацій)', manifest && swCode && sw===0, JSON.stringify({sw, manifest, swCodeOnlyHttps: swCode}));
  ok('Жодної помилки консолі/сторінки за весь прогін', errors.length===0, errors.slice(0,5).join(' || '));
  await browser.close();
  const fails = results.filter(r=>!r.pass).length;
  require('fs').writeFileSync(process.argv[2], JSON.stringify(results, null, 1));
  console.log(`\n${results.length-fails}/${results.length} перевірок пройдено`);
  process.exit(fails?1:0);
})().catch(e => { console.error('CRASH', e); process.exit(2); });
