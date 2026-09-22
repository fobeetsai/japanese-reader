/* Pure data model shared by the browser and offline integration tests. */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ReaderSyncCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';
  const kinds = ['articles', 'words', 'grammars', 'sentences'];
  const FORMAT = 'reading-master-backup';
  const limit = 10000;
  function fail(message) { throw new Error(message); }
  function text(value, max = 200000) {
    if (typeof value !== 'string' || value.length > max) fail('備份文字格式或長度不正確');
    return value;
  }
  function item(kind, value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) fail('收藏格式不正確');
    const fields = {
      articles:['id','title','content','savedAt','sentenceCount','wordCount','grammarCount'],
      words:['surface','baseForm','reading','jlpt','pos','meaning','example','exampleTrans','addedAt'],
      grammars:['id','title','level','meaningZh','meaningJa','form','example','translation','note','addedAt'],
      sentences:['text','translation','date']
    }[kind];
    if (!fields) fail('未知的收藏分類');
    const out = {};
    for (const key of fields) {
      if (value[key] == null) continue;
      if (['sentenceCount','wordCount','grammarCount'].includes(key)) {
        if (!Number.isSafeInteger(value[key]) || value[key] < 0) fail('收藏統計格式不正確');
        out[key] = value[key];
      } else if (kind === 'grammars' && key === 'id' && Number.isSafeInteger(value[key])) out[key] = value[key];
      else out[key] = text(typeof value[key] === 'number' ? String(value[key]) : value[key]);
    }
    if (kind === 'articles') {
      if (!/^[a-zA-Z0-9_-]{1,150}$/.test(out.id || '') || !out.title || !out.content) fail('收藏文章缺少有效 ID、標題或正文');
    }
    if (kind === 'words' && !out.surface) fail('收藏單字缺少文字');
    if (kind === 'grammars' && (!out.id || !out.title)) fail('收藏文法缺少 ID 或標題');
    if (kind === 'sentences' && !out.text) fail('收藏句子缺少文字');
    // Level values are used in existing CSS classes; never allow markup there.
    for (const key of ['jlpt','level']) if (out[key] && !/^(N[1-5](?:[~〜～／/、-]N?[1-5])?|未分級|未分類|不明)$/i.test(out[key])) out[key] = '';
    return out;
  }
  function keyFor(kind, value) { return kind + ':' + (kind === 'words' ? value.surface : kind === 'sentences' ? value.text : value.id); }
  function normalizeData(data) {
    const out = {};
    for (const kind of kinds) {
      if (!Array.isArray(data[kind]) || data[kind].length > limit) fail('備份分類或筆數不正確');
      const list = data[kind].map(x => item(kind, x));
      if (new Set(list.map(v => keyFor(kind,v))).size !== list.length) fail('備份含有重複的收藏 ID');
      out[kind] = list;
    }
    return out;
  }
  function empty() { return {format:FORMAT,version:1,records:[]}; }
  function validate(doc) {
    if (!doc || doc.format !== FORMAT || doc.version !== 1 || !Array.isArray(doc.records) || doc.records.length > limit * 4) fail('不是支援的閱讀高手備份');
    const seen = new Set();
    const records = doc.records.map(r => {
      if (!r || !kinds.includes(r.kind) || typeof r.deleted !== 'boolean' || !Number.isSafeInteger(r.clock) || r.clock < 1 || r.clock > 1e12 || !/^[a-zA-Z0-9_-]{1,150}$/.test(r.actor)) fail('備份版本紀錄不正確');
      text(r.key,200160);
      if (!r.key.startsWith(r.kind + ':') || seen.has(r.key)) fail('備份含有重複或無效的索引');
      seen.add(r.key);
      const result = {kind:r.kind,key:r.key,clock:r.clock,actor:r.actor,deleted:r.deleted};
      if (!r.deleted) {
        result.value = item(r.kind,r.value);
        if (keyFor(r.kind,result.value) !== r.key) fail('備份索引與內容不符');
      }
      return result;
    });
    return {format:FORMAT,version:1,records};
  }
  function stable(doc) { return JSON.stringify({...doc,records:[...doc.records].sort((a,b)=>a.key.localeCompare(b.key))}); }
  function compare(a,b) { return a.clock-b.clock || a.actor.localeCompare(b.actor) || JSON.stringify(a).localeCompare(JSON.stringify(b)); }
  function merge(...docs) {
    const map = new Map();
    for (const doc of docs) for (const r of validate(doc).records) {
      const before = map.get(r.key);
      if (!before || compare(r,before)>0) map.set(r.key,r);
    }
    return validate({...empty(),records:[...map.values()]});
  }
  function capture(doc, rawData, actor) {
    doc = validate(doc);
    const data = normalizeData(rawData);
    let clock = Math.max(0,...doc.records.map(r=>r.clock));
    const map = new Map(doc.records.map(r=>[r.key,r]));
    const present = new Set();
    for (const kind of kinds) for (const value of data[kind]) {
      const key = keyFor(kind,value); present.add(key);
      const old = map.get(key);
      if (!old || old.deleted || JSON.stringify(old.value)!==JSON.stringify(value)) map.set(key,{kind,key,value,actor,clock:++clock,deleted:false});
    }
    for (const [key,old] of map) if (!old.deleted && !present.has(key)) map.set(key,{kind:old.kind,key,actor,clock:++clock,deleted:true});
    return validate({...empty(),records:[...map.values()]});
  }
  function data(doc) {
    const out = Object.fromEntries(kinds.map(k=>[k,[]]));
    for (const r of validate(doc).records) if (!r.deleted) out[r.kind].push(r.value);
    return out;
  }
  function counts(doc) { return Object.fromEntries(Object.entries(data(doc)).map(([k,v])=>[k,v.length])); }
  // Import is additive: deletion markers in an old backup cannot erase current work.
  function importBackup(current, backup, actor) {
    const combined = data(current), incoming = data(validate(backup));
    for (const kind of kinds) {
      const values = new Map(combined[kind].map(v=>[keyFor(kind,v),v]));
      for (const value of incoming[kind]) if (!values.has(keyFor(kind,value))) values.set(keyFor(kind,value),value);
      combined[kind] = [...values.values()];
    }
    return capture(current,combined,actor);
  }
  return {empty,validate,normalizeData,capture,merge,data,counts,stable,importBackup};
});
