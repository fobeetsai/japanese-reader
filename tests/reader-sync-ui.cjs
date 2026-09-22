const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=process.argv[2]||path.join(__dirname,'..');
const C=require(path.join(root,'static/master/sync-core.js'));
const article=id=>({id,title:id,content:'安全なテスト文章。'});
const data=articles=>({articles,words:[],grammars:[],sentences:[]});
const initial=C.capture(C.empty(),data([article('localA')]),'seed');
const cloud={a:[],b:[C.capture(C.empty(),data([article('onlyB')]),'b')]},writes=[];
const storage=new Map([['yuedu_gaoshou_saved_articles',JSON.stringify(C.data(initial).articles)]]);
const elements=new Map();let callback,failKey=null,applied;
function el(id){if(!elements.has(id))elements.set(id,{hidden:false,disabled:false,textContent:'',value:'',listeners:{},addEventListener(name,fn){this.listeners[name]=fn;},click(){return this.listeners.click?.({});},showModal(){},close(){}});return elements.get(id);}
const events={};
const ctx={console,ReaderSyncCore:C,READER_GOOGLE_CLIENT_ID:'public.apps.googleusercontent.com',crypto:globalThis.crypto,Blob,URL,AbortSignal,
  setTimeout:()=>1,clearTimeout(){},
  localStorage:{getItem:k=>storage.get(k)??null,setItem(k,v){if(k===failKey){failKey=null;throw new Error('quota');}storage.set(k,v);},removeItem:k=>storage.delete(k)},
  ReaderLibrary:{apply:d=>{applied=d;}},
  document:{readyState:'complete',visibilityState:'visible',getElementById:el,querySelectorAll:()=>[],addEventListener(){},createElement:()=>el('created'),head:{append:s=>s.onload()}},
  addEventListener:(n,f)=>events[n]=f,
  google:{accounts:{oauth2:{hasGrantedAllScopes:()=>true,initTokenClient:options=>{callback=options.callback;return {requestAccessToken(){}};}}}},
  ReaderDriveStore:class{constructor(token){this.token=token;}async request(){return {sub:this.token,email:this.token+'@example.test'};}async readAll(){return cloud[this.token];}async write(doc){writes.push({account:this.token,doc});cloud[this.token].push(doc);}}
};ctx.window=ctx;
vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,'static/master/reader-cloud.js'),'utf8'),ctx);
(async()=>{
  const incoming=C.capture(C.empty(),data([article('new')]),'backup');
  await el('readerBackupFile').listeners.change({target:{files:[{size:500,text:async()=>JSON.stringify(incoming)}],value:''}});
  const before=storage.get('yuedu_gaoshou_saved_articles');
  failKey='yuedu_gaoshou_notebook';el('readerConfirmImport').click();
  assert.equal(storage.get('yuedu_gaoshou_saved_articles'),before);
  assert.equal(el('readerSyncStatus').textContent,'匯入未完成');
  await callback({access_token:'a',expires_in:3600});
  assert.equal(writes.length,0,'first login must not silently upload local data');
  assert.equal(el('readerAccountChoice').hidden,false);
  await el('readerAcceptAccount').click();
  assert.equal(writes.length,1);assert.equal(writes[0].account,'a');
  assert.equal(el('readerSyncStatus').textContent,'本次同步完成');
  await callback({access_token:'b',expires_in:3600});
  assert.equal(writes.length,1,'switching accounts must not upload previous account data');
  await el('readerAcceptAccount').click();
  assert.equal(writes.filter(x=>x.account==='b').length,0);
  assert.equal(applied.articles.length,1);assert.equal(applied.articles[0].id,'onlyB');
  assert(!JSON.stringify(cloud.b).includes('localA'));
  events.storage({key:'reader_sync_account_v1',newValue:'other'});
  await el('readerSyncNow').click();
  assert.equal(el('readerSyncStatus').textContent,'需要登入 Google');
  console.log('PASS UI controller: quota rollback, first-account consent, account switching isolation, remote restore, cross-tab disconnect, verified success status');
})().catch(e=>{console.error(e);process.exitCode=1;});
