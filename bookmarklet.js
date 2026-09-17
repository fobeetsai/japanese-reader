// Trancy Dual - 沉浸翻譯書籤小工具 (Bookmarklet)
// 用法：將下方代碼複製為瀏覽器書籤網址，在任何日文網頁點擊即可啟動中日雙語對照與雙向遮蔽！
javascript:(function(){
  if(document.getElementById('trancy-ext-toolbar')){
    alert('Trancy 雙語遮蔽工具列已在運行中！');
    return;
  }
  const s=document.createElement('script');
  s.src='https://fobeetsai.github.io/japanese-reader/trancy_extension/content.js';
  const c=document.createElement('link');
  c.rel='stylesheet';
  c.href='https://fobeetsai.github.io/japanese-reader/trancy_extension/content.css';
  document.head.appendChild(c);
  document.head.appendChild(s);
})();
