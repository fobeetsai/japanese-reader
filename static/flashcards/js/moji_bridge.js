/* Personal MOJi companion: official links + user-selected files. No account/API access. */
(function (root) {
  'use strict';
  const LIMIT = 500;
  const clean = value => String(value ?? '').trim();
  function sourceUrl(value) {
    if (!clean(value)) return '';
    const url = new URL(clean(value));
    if (url.protocol !== 'https:' || !['www.mojidict.com', 'mojidict.com'].includes(url.hostname) || url.username || url.password || url.port)
      throw new Error('請使用 https://www.mojidict.com/ 的詞表或詞條分享網址。');
    for (const key of url.searchParams.keys()) {
      if (!['text', 'word', 'wordId', 'id', 'shareId', 'from', 'utm_source'].includes(key))
        throw new Error('網址帶有未辨識參數，請使用 MOJi「分享」產生的純連結，勿貼入登入憑證。');
    }
    url.hash = '';
    return url.href;
  }
  function parse(text, delimiter) {
    const lines = String(text).replace(/^\uFEFF/, '').split(/\r?\n/).filter(line => line.trim());
    if (lines.length > LIMIT) throw new Error('一次最多 500 筆，請分批整理；尚未匯入任何資料。');
    return lines.map((line, index) => {
      const parts = line.split(delimiter === 'tab' ? '\t' : '|').map(clean);
      if (parts.length !== 4) throw new Error(`第 ${index + 1} 筆不是四欄。請整理為「日文 | 讀音 | 中文 | 例句」，沒有內容的欄位也要保留分隔符。`);
      return {front:parts[0], reading:parts[1], back:parts[2], example:parts[3], include:true};
    });
  }
  const key = card => JSON.stringify(['front','reading','back','example'].map(k => clean(card[k])));
  function prepare(rows, existing, skipDuplicates) {
    const seen = new Set(skipDuplicates ? existing.map(key) : []);
    const cards = []; let skipped = 0;
    for (const [i, row] of rows.entries()) {
      if (!row.include) { skipped++; continue; }
      if (!clean(row.front) || !clean(row.back)) throw new Error(`第 ${i + 1} 筆缺少日文或中文，請補齊或取消勾選。`);
      if (skipDuplicates && seen.has(key(row))) { skipped++; continue; }
      seen.add(key(row));
      cards.push(Object.fromEntries(['front','reading','back','example'].map(k=>[k,clean(row[k])])));
    }
    return {cards,skipped};
  }
  // Text extraction preserves every nonempty PDF text item; layout is provisional.
  function pdfLines(items) {
    const lines = [];
    for (const item of items.filter(i => typeof i.str === 'string' && i.str.trim()).sort((a,b)=>b.transform[5]-a.transform[5] || a.transform[4]-b.transform[4])) {
      const y = item.transform[5];
      let line = lines.find(l => Math.abs(l.y-y) < 2);
      if (!line) { line={y,items:[]}; lines.push(line); }
      line.items.push(item);
    }
    return lines.sort((a,b)=>b.y-a.y).map(line=>line.items.sort((a,b)=>a.transform[4]-b.transform[4]).map(i=>i.str).join(' ')).join('\n');
  }
  root.MojiCompanion = {parse, prepare, sourceUrl, pdfLines};
  if (typeof module !== 'undefined' && module.exports) module.exports = root.MojiCompanion;
  if (typeof document === 'undefined') return;
  document.addEventListener('DOMContentLoaded', () => {
    const $ = id => document.getElementById(id);
    const modal = $('modal-moji');
    if (!modal) return;
    let rows = [], generation = 0;
    const status = text => { $('moji-status').textContent=text; };
    function invalidate() { rows=[]; $('moji-preview').replaceChildren(); $('moji-import').disabled=true; }
    $('btn-moji-workspace').onclick = () => { modal.classList.add('open'); renderSources(); };
    $('moji-text').oninput = invalidate;
    $('moji-format').onchange = invalidate;
    function renderSources() {
      $('moji-sources').replaceChildren();
      const seen=new Set();
      for(const deck of window.app?.decks || []) {
        if(!deck.mojiSourceUrl || seen.has(deck.mojiSourceUrl)) continue;
        let url; try { url=sourceUrl(deck.mojiSourceUrl); } catch { continue; }
        seen.add(url);
        const a=document.createElement('a'); a.href=url; a.target='_blank'; a.rel='noopener noreferrer'; a.textContent=deck.name; a.className='btn-secondary';
        $('moji-sources').append(a);
      }
    }
    $('moji-open-source').onclick = () => {
      try { const url=sourceUrl($('moji-source').value); if(!url) throw Error('請先貼上 MOJi 分享網址。'); window.open(url,'_blank','noopener,noreferrer'); }
      catch(e) { status(e.message); }
    };
    $('moji-search').onclick=()=>{ const word=$('moji-query').value.trim(); if(word) window.app.openMojiDict(word); else status('請輸入要查的單字或文型。'); };
    $('moji-sample').onclick=()=>{
      $('moji-text').value='確かめる | たしかめる | 確認、查明 | 出発時間を確かめる。\n～たびに | ～たびに | 每當……就…… | この写真を見るたびに、旅行を思い出す。';
      $('moji-format').value='pipe'; invalidate(); status('已載入自編格式示例（不是 MOJi 資料）。可修改後按預覽。');
    };
    $('moji-preview-button').onclick=()=>{
      invalidate();
      try {
        rows=parse($('moji-text').value,$('moji-format').value);
        if(!rows.length) throw Error('請先貼上整理好的內容。');
        for(const [i,row] of rows.entries()) {
          const fieldset=document.createElement('fieldset'); fieldset.className='moji-row';
          const legend=document.createElement('legend'); legend.textContent=`第 ${i+1} 筆`; fieldset.append(legend);
          const label=document.createElement('label'), box=document.createElement('input'); box.type='checkbox';box.checked=true;box.onchange=()=>{row.include=box.checked;};label.append(box,document.createTextNode(' 匯入此筆'));fieldset.append(label);
          for(const [k,name] of [['front','日文／文型'],['reading','讀音'],['back','中文意思'],['example','例句／接續說明']]) {
            const l=document.createElement('label');l.textContent=name;
            const input=document.createElement('textarea');input.className='form-textarea';input.rows=2;input.value=row[k];input.oninput=()=>{row[k]=input.value;};l.append(input);fieldset.append(l);
          }
          $('moji-preview').append(fieldset);
        }
        $('moji-import').disabled=false;status(`共 ${rows.length} 筆，請逐筆核對。空白中文不會自動翻譯，需補齊才能匯入。`);
      } catch(e) {status(e.message);}
    };
    $('moji-file').onchange=async()=>{
      const file=$('moji-file').files[0]; if(!file)return;
      const ticket=++generation; invalidate();
      if(file.size>20*1024*1024)return status('檔案上限 20 MB，請拆小後重試。');
      if($('moji-text').value && !confirm('讀取檔案會取代整理區文字，確定繼續？'))return;
      for(const id of ['moji-file','moji-text','moji-sample','moji-preview-button']) $(id).disabled=true;
      status('正在本機讀取檔案…');
      let loadingTask;
      try {
        let text;
        if(/\.pdf$/i.test(file.name)) {
          const pdfjs=await import('../vendor/pdfjs/pdf.min.mjs');
          pdfjs.GlobalWorkerOptions.workerSrc=new URL('../vendor/pdfjs/pdf.worker.min.mjs',document.querySelector('script[src*="moji_bridge.js"]').src).href;
          loadingTask=pdfjs.getDocument({data:new Uint8Array(await file.arrayBuffer()),isEvalSupported:false,
            cMapUrl:new URL('../vendor/pdfjs/cmaps/',document.querySelector('script[src*="moji_bridge.js"]').src).href,cMapPacked:true});
          const pdf=await loadingTask.promise;
          if(pdf.numPages>50) throw Error('一次最多 50 頁 PDF，請先按章節匯出。');
          const pages=[];
          for(let i=1;i<=pdf.numPages;i++) {
            if(ticket!==generation)return;
            status(`正在擷取 PDF：${i}／${pdf.numPages} 頁…`);
            const p=await pdf.getPage(i);pages.push(pdfLines((await p.getTextContent()).items));p.cleanup();
          }
          text=pages.join('\n\n');
          if(!text.trim())throw Error('PDF 沒有可擷取文字，可能是掃描影像。請改貼文字或使用既有照片辨識功能。');
        } else if(/\.(txt|tsv)$/i.test(file.name)) text=await file.text();
        else throw Error('請選 PDF、UTF-8 TXT 或 TSV；Excel 請用主畫面的 Excel 匯入。');
        if(ticket!==generation)return;
        $('moji-text').value=text;
        if(/\.tsv$/i.test(file.name))$('moji-format').value='tab';
        if(!$('moji-name').value)$('moji-name').value=file.name.replace(/\.[^.]+$/,'');
        status('已擷取至整理區，尚未建卡。PDF 欄位順序可能錯亂；請對照原檔，整理為四欄後再預覽。');
      }catch(e){if(ticket===generation)status('讀取失敗：'+e.message);}
      finally {
        if(loadingTask)await loadingTask.destroy().catch(()=>{});
        for(const id of ['moji-file','moji-text','moji-sample','moji-preview-button']) $(id).disabled=false;
      }
    };
    modal.addEventListener('click',e=>{if(e.target===modal||e.target.closest('.modal-close'))generation++;});
    $('moji-import').onclick=()=>{
      try {
        const app=window.app;if(app.syncBusy)throw Error('同步進行中，請等同步完成再匯入。');
        const name=$('moji-name').value.trim();if(!name)throw Error('請填寫新牌組名稱。');
        const url=sourceUrl($('moji-source').value);
        const result=prepare(rows,app.cards,$('moji-dedup').checked);
        if(!result.cards.length)throw Error('沒有可新增的卡片（可能全部重複或未勾選）。');
        const type=$('moji-kind').value;
        const deck={id:'deck_moji_'+crypto.randomUUID(),name,category:'moji',categoryName:'MOJi 學習',icon:'📖',color:'#0891b2',reviewGroupSize:20,
          desc:'個人整理匯入 · '+type,mojiSourceUrl:url};
        const cards=result.cards.map(c=>app.anki.createCard({...c,id:'card_'+crypto.randomUUID(),deckId:deck.id,tags:['個人整理',type],notes:url?'來源參考：'+url:'個人整理匯入'}));
        const decks=[...app.decks,deck], allCards=[...app.cards,...cards];
        if(!app.sync.saveLocalData({decks,cards:allCards}))throw Error('儲存空間不足，尚未新增牌組。');
        app.decks=decks;app.cards=allCards;app.currentCategory='all';app.renderCategoryTabs();app.renderDeckList();app.updateHeaderStats();app.showView('view-decks');
        invalidate();renderSources();status(`已建立「${name}」：${cards.length} 張卡片，略過 ${result.skipped} 筆。回到牌組即可複習；若要換機，請按同步。`);
      }catch(e){status(e.message);}
    };
  });
})(typeof window !== 'undefined' ? window : globalThis);
