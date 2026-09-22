const assert=require('node:assert/strict');
const path=require('node:path');
const root=process.argv[2]||path.join(__dirname,'..');
const C=require(path.join(root,'static/master/sync-core.js'));
const Drive=require(path.join(root,'static/master/drive-store.js'));
const blank=()=>({articles:[],words:[],grammars:[],sentences:[]});
const article=(id,title=id)=>({id,title,content:'今日は日本語を勉強します。',savedAt:'2026/9/22',sentenceCount:1,wordCount:3});
const seed=C.capture(C.empty(),{...blank(),articles:[article('one')]},'a');
const a=C.capture(seed,{...blank(),articles:[article('one'),article('two')]},'a');
const b=C.capture(seed,{...blank(),articles:[article('one'),article('three')]},'b');
const union=C.merge(a,b);assert.equal(C.counts(union).articles,3);
assert.equal(C.stable(C.merge(a,b)),C.stable(C.merge(b,a)));
assert.equal(C.stable(C.merge(union,union)),C.stable(union));
const removed=C.capture(union,{...blank(),articles:[article('two'),article('three')]},'a');
assert.equal(C.counts(C.merge(removed,seed)).articles,2);
const restored=C.merge(C.empty(),removed);assert.equal(C.counts(restored).articles,2);
const imported=C.importBackup(removed,seed,'importer');assert.equal(C.counts(imported).articles,3);
const different=C.capture(seed,{...blank(),articles:[article('one','new title')]},'b');
assert.equal(C.data(C.importBackup(different,seed,'importer')).articles[0].title,'new title');
const complete=C.capture(C.empty(),{articles:[article('a')],words:[{surface:'日文',reading:'にほんご'}],grammars:[{id:123,title:'ために',level:'N3'}],sentences:[{text:'毎日読む。',translation:'每天閱讀。'}]},'a');
assert.deepEqual(C.counts(C.validate(JSON.parse(JSON.stringify(complete)))),{articles:1,words:1,grammars:1,sentences:1});
assert.equal(typeof C.data(complete).grammars[0].id,'number');
for(const invalid of [{}, {format:'reading-master-backup',version:9,records:[]}, {...seed,records:[...seed.records,...seed.records]}, {...seed,records:[{...seed.records[0],clock:Infinity}]}]) assert.throws(()=>C.validate(invalid));
assert.throws(()=>C.capture(C.empty(),{...blank(),articles:[article("x');alert(1)//")]},'a'));
const unchanged=C.capture(seed,C.data(seed),'b');assert.equal(C.stable(seed),C.stable(unchanged));
const html=require('node:fs').readFileSync(path.join(root,'master.html'),'utf8');
assert(!html.includes('${st.text}</div>'));
assert(!html.includes("onclick=\"window.speakJapanese('${w.surface"));
let files=[], serial=0, writes=0;
const mock=async(url,options={})=>{
  const u=new URL(url);
  if(options.method==='POST'){
    writes++;
    const boundary=options.headers['Content-Type'].split('boundary=')[1];
    const pieces=options.body.split('--'+boundary).slice(1,3).map(p=>JSON.parse(p.split('\r\n\r\n')[1].trim()));
    const f={id:String(++serial),...pieces[0],data:pieces[1]};files.push(f);
    return new Response(JSON.stringify({id:f.id}));
  }
  if(u.searchParams.get('alt')==='media')return new Response(JSON.stringify(files.find(f=>f.id===u.pathname.split('/').pop()).data));
  return new Response(JSON.stringify({files:files.map(({data,...f})=>f)}));
};
(async()=>{
  const da=new Drive('account-a',mock),db=new Drive('account-a',mock);
  await Promise.all([da.write(a,'writer-a',1),db.write(b,'writer-b',1)]);
  assert.equal(C.counts(C.merge(...await da.readAll())).articles,3);
  await da.write(removed,'writer-a',2);
  assert.equal(C.counts(C.merge(...await db.readAll())).articles,2);
  assert.equal((await da.list()).length,2);
  assert.equal(files.length,3); // immutable earlier snapshots remain available
  const expired=new Drive('expired',async()=>new Response('{}',{status:401}));
  await assert.rejects(()=>expired.readAll(),/授權已到期/);
  const broken=new Drive('ok',async()=>{throw new Error('offline');});
  await assert.rejects(()=>broken.write(a,'writer-a',3),/offline/);
  const badReadback=new Drive('ok',async(url,opts={})=>opts.method==='POST'?new Response('{"id":"x"}'):new Response('{}'));
  await assert.rejects(()=>badReadback.write(a,'writer-a',3),/回讀驗證/);
  assert.equal(writes,3);
  console.log('PASS: two-device merge, concurrent uploads, delete propagation, cleared-device restore, additive import, complete backup, stable IDs, validation, token expiry, offline errors, readback verification, safe renderer hooks');
})().catch(e=>{console.error(e);process.exitCode=1;});
