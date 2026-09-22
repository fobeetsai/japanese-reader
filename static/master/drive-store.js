(function(root,factory) {
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api; else root.ReaderDriveStore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const NAME='reading-master-sync-v1.json';
  class DriveStore {
    constructor(token,fetcher=fetch){this.token=token;this.fetcher=fetcher;}
    async request(url,options={}) {
      const response=await this.fetcher(url,{...options,headers:{Authorization:`Bearer ${this.token}`,...options.headers},signal:AbortSignal.timeout(30000)});
      if(!response.ok) {
        if(response.status===401) throw new Error('Google 授權已到期，請重新登入後同步。');
        if(response.status===403) throw new Error('Google Drive 尚未授權、API 未啟用或儲存空間不足。');
        throw new Error(`Google Drive 連線失敗（${response.status}），本機收藏仍保留。`);
      }
      const raw=await response.text();
      if(raw.length>10000000) throw new Error('雲端備份超過可讀取大小，請先下載本機備份。');
      return raw ? JSON.parse(raw) : {};
    }
    async list() {
      const all=[]; let pageToken='';
      do {
        const params=new URLSearchParams({spaces:'appDataFolder',q:`name = '${NAME}' and trashed = false`,pageSize:'1000',fields:'nextPageToken,files(id,appProperties,size)'});
        if(pageToken) params.set('pageToken',pageToken);
        const result=await this.request('https://www.googleapis.com/drive/v3/files?'+params);
        all.push(...(result.files||[])); pageToken=result.nextPageToken||'';
        if(all.length>20000) throw new Error('雲端歷史版本較多，請聯絡管理者整理；本機資料未更動。');
      } while(pageToken);
      // Each browser session writes immutable snapshots. Never overwrite another device.
      const latest=new Map();
      for(const file of all) {
        const p=file.appProperties||{};
        if(!/^[a-zA-Z0-9_-]{1,150}$/.test(p.writer||'')||!/^\d+$/.test(p.sequence||'')) throw new Error('雲端版本資訊不完整，已停止同步以保護資料。');
        const previous=latest.get(p.writer);
        if(!previous||Number(p.sequence)>Number(previous.appProperties.sequence)) latest.set(p.writer,file);
        else if(Number(p.sequence)===Number(previous.appProperties.sequence)) latest.set(p.writer+'-'+file.id,file);
      }
      return [...latest.values()];
    }
    async readAll() {
      const files=await this.list(); const docs=[];
      for(let i=0;i<files.length;i+=5) docs.push(...await Promise.all(files.slice(i,i+5).map(f=>this.request('https://www.googleapis.com/drive/v3/files/'+encodeURIComponent(f.id)+'?alt=media'))));
      return docs;
    }
    async write(doc,writer,sequence) {
      const boundary='reader_'+crypto.randomUUID().replaceAll('-','');
      const metadata={name:NAME,parents:['appDataFolder'],mimeType:'application/json',appProperties:{writer,sequence:String(sequence)}};
      const body=`--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${JSON.stringify(metadata)}\r\n--${boundary}\r\nContent-Type: application/json\r\n\r\n${JSON.stringify(doc)}\r\n--${boundary}--`;
      const created=await this.request('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id',{method:'POST',headers:{'Content-Type':'multipart/related; boundary='+boundary},body});
      if(!created.id) throw new Error('Google Drive 未回傳儲存結果，請重新同步確認。');
      const readback=await this.request('https://www.googleapis.com/drive/v3/files/'+encodeURIComponent(created.id)+'?alt=media');
      if(JSON.stringify(readback)!==JSON.stringify(doc)) throw new Error('雲端回讀驗證不一致，尚未標示同步完成。');
      return created.id;
    }
  }
  return DriveStore;
});
