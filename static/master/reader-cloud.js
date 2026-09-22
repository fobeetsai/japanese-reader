(() => {
  'use strict';
  const C=window.ReaderSyncCore;
  const KEYS={ledger:'reader_sync_ledger_v1',binding:'reader_sync_account_v1',recovery:'reader_sync_recovery_v1',last:'reader_sync_last_v1'};
  const $=id=>document.getElementById(id);
  const actor=crypto.randomUUID(); // Independent writer for every open page; no cross-tab overwrite.
  let doc=C.empty(), token='', expires=0, account=null, pendingAccount=null, busy=false, timer=0, sequence=0, pendingImport=null;
  const status=$('readerSyncStatus'), detail=$('readerSyncDetail');
  const message=(s,d='')=>{status.textContent=s; detail.textContent=d;document.querySelectorAll('[data-open-reader-sync]').forEach(button=>{button.textContent=s==='本次同步完成'?'☁ 已同步':s==='正在同步…'?'☁ 同步中…':/失敗|未完成|問題/.test(s)?'⚠ 同步未完成':s.includes('尚未同步')?'☁ 待同步':'☁ 收藏同步';});};
  const describe=d=>{const n=C.counts(d);return `${n.articles} 篇文章 · ${n.words} 個生詞 · ${n.grammars} 個文法 · ${n.sentences} 個收藏句`;};
  const readJSON=(key,fallback)=>{const raw=localStorage.getItem(key);return raw?JSON.parse(raw):fallback;};
  const readData=()=>({
    articles:readJSON('yuedu_gaoshou_saved_articles',readJSON('japanese_reader_saved_articles',[])),
    ...readJSON('yuedu_gaoshou_notebook',readJSON('japanese_reader_notebook',{words:[],grammars:[]})),
    sentences:readJSON('master_starred_sentences',[])
  });
  function capture() {
    const stored=readJSON(KEYS.ledger,C.empty());
    doc=C.capture(C.merge(doc,stored),readData(),actor);
    localStorage.setItem(KEYS.ledger,JSON.stringify(doc));
    $('readerLibraryCounts').textContent=describe(doc);
    return doc;
  }
  function commit(next,keepRecovery=true) {
    next=C.validate(next);
    const data=C.data(next);
    const writes={
      yuedu_gaoshou_saved_articles:JSON.stringify(data.articles),
      yuedu_gaoshou_notebook:JSON.stringify({words:data.words,grammars:data.grammars}),
      master_starred_sentences:JSON.stringify(data.sentences),
      [KEYS.ledger]:JSON.stringify(next)
    };
    const previous=Object.fromEntries(Object.keys(writes).map(k=>[k,localStorage.getItem(k)]));
    if(keepRecovery) localStorage.setItem(KEYS.recovery,JSON.stringify(doc));
    try {for(const [key,value] of Object.entries(writes)) localStorage.setItem(key,value);}
    catch(error) {for(const [key,value] of Object.entries(previous)) {if(value===null)localStorage.removeItem(key);else localStorage.setItem(key,value);} throw error;}
    doc=next;
    window.ReaderLibrary.apply(data);
    $('readerLibraryCounts').textContent=describe(doc);
  }
  function download(value,prefix='閱讀高手完整備份') {
    const blob=new Blob([JSON.stringify(value,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob), a=document.createElement('a');
    a.href=url;a.download=`${prefix}_${new Date().toISOString().replace(/[:.]/g,'-')}.json`;a.click();
    setTimeout(()=>URL.revokeObjectURL(url),10000);
  }
  function setBusy(value) {
    busy=value;
    ['readerConnect','readerSyncNow','readerImport','readerAcceptAccount','readerConfirmImport','readerDisconnect'].forEach(id=>$(id).disabled=value);
    $('readerConnect').disabled=value||!window.READER_GOOGLE_CLIENT_ID||!window.google?.accounts?.oauth2;
  }
  function schedule(){clearTimeout(timer);if(token&&account&&Date.now()<expires)timer=setTimeout(sync,5000);}
  function changed() {
    try {capture();message('已存於此裝置・尚未同步',token?'將在數秒後同步；離開前請確認「本次同步完成」。':'請登入 Google 後同步，或下載完整備份。');schedule();}
    catch(e){message('本機儲存或同步紀錄出現問題',e.message+'。請先下載完整備份。');}
  }
  window.ReaderCloud={changed,storageError:error=>message('本機儲存失敗',error.message+'。收藏未儲存，請先下載完整備份並釋放空間。')};
  async function sync() {
    if(busy)return;
    if(!token||Date.now()>=expires||!account){message('需要登入 Google', '收藏仍在此裝置；登入後即可同步。');return;}
    setBusy(true);clearTimeout(timer);
    const syncAccount=account.sub;
    const checkAccount=()=>{if(account?.sub!==syncAccount||localStorage.getItem(KEYS.binding)!==syncAccount)throw new Error('同步期間帳號已變更，已停止套用資料；請重新登入。');};
    try {
      message('正在同步…','正在比對此裝置與你的 Google Drive 收藏。');
      const store=new window.ReaderDriveStore(token);
      const remote=C.merge(C.empty(),...await store.readAll());
      checkAccount();
      const local=capture();
      const merged=C.merge(remote,local);
      if(C.stable(merged)!==C.stable(remote)) await store.write(merged,actor,++sequence);
      // Include edits made while the network request was in flight.
      const latestRemote=C.merge(C.empty(),...await store.readAll());
      checkAccount();
      const latestLocal=capture();
      const final=C.merge(latestRemote,latestLocal);
      commit(final);
      if(C.stable(final)!==C.stable(latestRemote)) {
        message('有新修改尚未同步','目前收藏已保留，將繼續同步最新變更。');schedule();
      } else {
        const time=new Date().toISOString();
        localStorage.setItem(KEYS.last,JSON.stringify({account:account.sub,time}));
        message('本次同步完成',`${account.email} · ${new Date(time).toLocaleString()}\n${describe(doc)}`);
      }
    } catch(e){message('同步未完成・本機收藏仍保留',e.message);}
    finally{setBusy(false);}
  }
  async function receiveToken(response) {
    if(response.error||!response.access_token){message('Google 登入未完成','可以繼續使用本機收藏或備份。');return;}
    if(!google.accounts.oauth2.hasGrantedAllScopes(response,'https://www.googleapis.com/auth/drive.appdata')) {message('未取得同步授權','請允許閱讀高手儲存自己的 APP 資料。');return;}
    token=response.access_token;expires=Date.now()+(Number(response.expires_in)||3600)*1000-60000;
    setBusy(true);
    try {
      const store=new window.ReaderDriveStore(token);
      const user=await store.request('https://www.googleapis.com/oauth2/v3/userinfo');
      if(!user.sub||!user.email)throw new Error('無法確認 Google 帳號；尚未上傳任何資料。');
      const bound=localStorage.getItem(KEYS.binding);
      if(bound===user.sub){account=user;message('已連線',user.email);}
      else {
        pendingAccount=user;account=null;
        $('readerAccountChoice').hidden=false;
        $('readerAccountNotice').textContent=bound ? `目前本機收藏屬於另一個帳號。切換到 ${user.email} 前，會先下載原收藏備份，再載入新帳號的資料；不會把原收藏上傳到新帳號。` : `即將使用 ${user.email}。按下確認後，此裝置現有的 ${describe(capture())} 會與該帳號的雲端收藏合併。共用電腦請確認這些都是你的收藏。`;
        $('readerAcceptAccount').textContent=bound?'備份原收藏並切換帳號':'確認使用此帳號同步';
        message('請確認同步帳號',user.email+'；確認前不會上傳收藏。');
      }
    }catch(e){token='';expires=0;message('Google 帳號確認失敗',e.message);}
    finally{setBusy(false);}
    if(account)await sync();
  }
  $('readerAcceptAccount').addEventListener('click',async()=>{
    if(!pendingAccount||busy)return;
    try {
      const bound=localStorage.getItem(KEYS.binding);
      if(bound&&bound!==pendingAccount.sub){download(capture(),'切換帳號前備份');commit(C.empty());}
      localStorage.setItem(KEYS.binding,pendingAccount.sub);
      account=pendingAccount;pendingAccount=null;$('readerAccountChoice').hidden=true;await sync();
    }catch(e){message('帳號切換未完成',e.message);}
  });
  $('readerDisconnect').addEventListener('click',()=>{
    token='';expires=0;account=null;pendingAccount=null;clearTimeout(timer);$('readerAccountChoice').hidden=true;
    message('已中斷雲端連線','本機仍保留收藏。共用電腦使用完畢，請先確認已同步，再清除網站資料。');
  });
  $('readerSyncNow').addEventListener('click',sync);
  $('readerExport').addEventListener('click',()=>{
    try{download(capture());message('完整備份已下載', '請將 JSON 檔存到 Google Drive 或其他安全位置；手機可用「匯入備份」還原。');}
    catch(e){try{download({...C.empty(),records:C.capture(C.empty(),readData(),actor).records});message('已下載收藏備份','本機同步紀錄仍需修復：'+e.message);}catch(err){message('備份失敗',err.message);}}
  });
  $('readerExportRecovery').addEventListener('click',()=>{
    try{const old=readJSON(KEYS.recovery,null);if(!old)throw new Error('目前沒有上一次合併前的復原備份');download(C.validate(old),'合併前復原備份');}catch(e){message('復原備份',e.message);}
  });
  $('readerImport').addEventListener('click',()=>$('readerBackupFile').click());
  $('readerBackupFile').addEventListener('change',async event=>{
    const file=event.target.files[0];event.target.value='';if(!file)return;
    try {
      if(file.size>10000000)throw new Error('備份超過 10 MB，請先分批整理收藏。');
      pendingImport=C.validate(JSON.parse(await file.text()));
      $('readerImportSummary').textContent=`備份內有 ${describe(pendingImport)}。匯入會新增缺少的收藏；相同 ID 保留此裝置版本，不會用舊備份刪除現有收藏。`;
      $('readerImportChoice').hidden=false;
    }catch(e){pendingImport=null;message('無法匯入此檔案',e.message+'；现有收藏未變更。');}
  });
  $('readerCancelImport').addEventListener('click',()=>{pendingImport=null;$('readerImportChoice').hidden=true;});
  $('readerConfirmImport').addEventListener('click',()=>{
    if(!pendingImport||busy)return;
    try{capture();commit(C.importBackup(doc,pendingImport,actor));pendingImport=null;$('readerImportChoice').hidden=true;message('備份已合併至此裝置',describe(doc)+'；連線後會同步到你的帳號。');schedule();}
    catch(e){message('匯入未完成',e.message);}
  });
  document.querySelectorAll('[data-open-reader-sync]').forEach(button=>button.addEventListener('click',()=>{
    try{$('readerLibraryCounts').textContent=describe(capture());}catch(e){message('無法讀取收藏',e.message);}
    $('readerSyncDialog').showModal();
  }));
  $('readerSyncClose').addEventListener('click',()=>$('readerSyncDialog').close());
  window.addEventListener('storage',event=>{
    if(event.key===KEYS.binding||event.key===null){token='';expires=0;account=null;pendingAccount=null;clearTimeout(timer);$('readerAccountChoice').hidden=true;message('帳號或網站資料已在另一分頁變更','請重新登入 Google；目前分頁已停止雲端同步。');}
    if(event.key===KEYS.ledger&&event.newValue){try{doc=C.validate(JSON.parse(event.newValue));window.ReaderLibrary.apply(C.data(doc));$('readerLibraryCounts').textContent=describe(doc);}catch(e){message('另一分頁的收藏更新失敗',e.message);}}
  });
  window.addEventListener('online',schedule);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')schedule();});
  function init(){try{doc=C.validate(readJSON(KEYS.ledger,C.empty()));capture();message('收藏保存在此裝置','登入 Google 以跨裝置同步；清除網站資料前，請先同步或下載完整備份。');}catch(e){message('收藏需要檢查',e.message);}}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
  const clientId=window.READER_GOOGLE_CLIENT_ID;
  if(clientId&&/^[a-zA-Z0-9._-]+\.apps\.googleusercontent\.com$/.test(clientId)) {
    $('readerSetupNotice').hidden=true;
    const script=document.createElement('script');script.src='https://accounts.google.com/gsi/client';script.async=true;
    script.onload=()=>{
      const client=google.accounts.oauth2.initTokenClient({client_id:clientId,scope:'openid email https://www.googleapis.com/auth/drive.appdata',include_granted_scopes:false,callback:receiveToken,error_callback:()=>message('Google 登入視窗已關閉或被阻擋','請再按一次登入；若使用手機主畫面 APP，可先在 Safari 或 Chrome 中登入。')});
      $('readerConnect').disabled=false;
      $('readerConnect').addEventListener('click',()=>client.requestAccessToken({prompt:'select_account'}));
    };
    script.onerror=()=>message('Google 登入服務尚未載入','請檢查網路後重新整理；完整備份仍可使用。');
    document.head.append(script);
  }
})();
