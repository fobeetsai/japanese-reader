// Offline integration tests: two isolated browser stores share a mocked Gist API.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const SyncManager = require('../static/flashcards/js/sync_manager.js');
const gistId = 'a'.repeat(32);
let cloud, writes = 0, failNetwork = false;
const makeData = word => ({decks:[{id:'d',name:'Deck'}],cards:[{id:'c',deckId:'d',front:word,back:'中文'}],logs:{}});
function device(data) {
  const storage = new Map();
  const elements = new Map();
  const el = id => {
    if (!elements.has(id)) elements.set(id, {value:'', checked:false, textContent:'', classList:{contains:()=>false,remove(){},add(){}}});
    return elements.get(id);
  };
  const context = {console, crypto:globalThis.crypto, TextEncoder, AbortSignal,
    localStorage:{getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
    document:{readyState:'loading',addEventListener(){},getElementById:el,querySelectorAll:()=>[]},
    window:{}, confirm:()=>true, alert:()=>{},
    fetch:async(url,options={})=>{
      if (failNetwork) throw Error('offline');
      if(options.method === 'POST' || options.method === 'PATCH') {
        cloud = JSON.parse(JSON.parse(options.body).files['ankiflash_sync_data.json'].content);
        writes++;
        return {ok:true,json:async()=>({id:gistId})};
      }
      return {ok:true,json:async()=>({files:{'ankiflash_sync_data.json':{content:JSON.stringify(cloud)}}})};
    }};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(require.resolve('../static/flashcards/js/sync_manager.js'),'utf8'),context);
  vm.runInContext(fs.readFileSync(require.resolve('../static/flashcards/js/app.js'),'utf8'),context);
  const app = Object.create(context.window.FlashcardApp.prototype);
  app.sync = new context.window.SyncManager();
  Object.assign(app,structuredClone(data),{settings:{},refreshAfterSync(){}});
  app.sync.saveLocalData(data);
  el('sync-github-token').value = 'test-placeholder-not-a-real-token';
  return {app,el,context,storage};
}
(async()=>{
  const a = device(makeData('A'));
  await a.app.syncCloud(); assert.equal(writes,1,a.el('sync-status-msg').textContent); assert.equal(a.app.settings.gistId,gistId);
  const b = device(makeData('B'));
  b.el('sync-gist-id').value = gistId;
  await b.app.syncCloud(); assert.equal(writes,1); assert.match(b.el('sync-status-msg').textContent,/首次連接/);
  await b.app.downloadFromCloud(); assert.equal(b.app.cards[0].front,'A');
  assert.equal(JSON.parse(b.storage.get('ankiflash_sync_recovery_v1')).local.cards[0].front,'B');
  b.app.cards[0].front = 'B edited'; b.app.logs = {'2026-09-16':{reviewed:3}}; b.app.saveData();
  await b.app.syncCloud(); assert.equal(cloud.cards[0].front,'B edited');
  await a.app.syncCloud(); assert.equal(a.app.cards[0].front,'B edited'); assert.equal(a.app.logs['2026-09-16'].reviewed,3);
  const equalWrites = writes; await a.app.syncCloud(); assert.equal(writes,equalWrites);
  a.app.cards[0].front = 'A conflict'; a.app.saveData();
  b.app.cards[0].front = 'B conflict'; b.app.saveData(); await b.app.syncCloud();
  const conflictWrites = writes; await a.app.syncCloud(); assert.equal(writes,conflictWrites); assert.equal(a.app.cards[0].front,'A conflict');
  assert.equal(cloud.cards[0].front,'B conflict');
  await a.app.syncCloud('overwrite'); assert.equal(cloud.cards[0].front,'A conflict');
  assert.equal(JSON.parse(a.storage.get('ankiflash_sync_recovery_v1')).remote.cards[0].front,'B conflict');
  failNetwork = true; await b.app.syncCloud(); assert.equal(b.app.cards[0].front,'B conflict'); assert.match(b.el('sync-status-msg').textContent,/未完成/); failNetwork=false;
  cloud = {decks:[],cards:[{id:'invalid'}],logs:{}};
  await b.app.downloadFromCloud(); assert.equal(b.app.cards[0].front,'B conflict');
  const m = new SyncManager();
  assert.throws(()=>m.validateData({decks:[],cards:{},logs:{}}));
  assert.throws(()=>m.validateData({...makeData('a'),decks:[{id:'d',name:'A'},{id:'d',name:'B'}]}));
  assert.equal(await m.fingerprint(makeData('a')),await m.fingerprint({logs:{},cards:makeData('a').cards,decks:makeData('a').decks}));
  // Failure midway through storing a snapshot must restore the earlier keys.
  const original = b.storage.get(b.app.sync.STORAGE_KEY_DECKS);
  const set = b.context.localStorage.setItem;
  let failed = false;
  b.context.localStorage.setItem=(k,v)=>{if(k === b.app.sync.STORAGE_KEY_CARDS && !failed){failed=true;throw Error('quota test');}set(k,v);};
  assert.equal(b.app.sync.saveLocalData(makeData('quota')),false);
  assert.equal(b.storage.get(b.app.sync.STORAGE_KEY_DECKS),original);
  console.log('PASS: initial link, A/B upload/download, logs, no-op, conflict, explicit resolution, recovery, offline, malformed data, canonical hash, storage rollback');
})().catch(e=>{console.error(e);process.exitCode=1;});


