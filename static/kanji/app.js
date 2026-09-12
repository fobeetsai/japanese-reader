'use strict';
const $=id=>document.getElementById(id);
function view(name){if(!['wk','books'].includes(name))throw Error('未知模式');for(const n of ['wk','books'])$(n).hidden=n!==name;document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.view===name));}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>view(b.dataset.view));
function say(text){if(!('speechSynthesis'in window)){alert('此瀏覽器不支援合成語音。');return;}const voices=speechSynthesis.getVoices();const voice=voices.find(v=>v.lang.toLowerCase().startsWith('ja'));if(!voice){alert('裝置目前沒有可用的日文語音，請先安裝或啟用日文語音。');return;}speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang='ja-JP';u.voice=voice;u.rate=.8;u.onerror=()=>{$('storageMessage').textContent='語音播放失敗，請確認裝置的日文語音設定。';};speechSynthesis.speak(u);}
if('speechSynthesis'in window)speechSynthesis.getVoices();

function nextSchedule(old,rating,now=Date.now()){if(!['again','hard','good'].includes(rating))throw Error('未知評分');const stage=old?.stage||0;if(rating==='again')return{stage:0,due:now+60000};if(rating==='hard')return{stage,due:now+600000};return{stage:Math.min(stage+1,5),due:now+[1,3,7,14,30][Math.min(stage,4)]*86400000};}
function download(name,text,type='text/plain;charset=utf-8'){const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),3000);}
