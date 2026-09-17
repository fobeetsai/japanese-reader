(function() {
  'use strict';

  // State
  let maskMode = 'all'; // 'all', 'mask-jp', 'mask-zh', 'mask-both'
  let translatedElements = new Set();
  let isTranslating = false;

  // Japanese detection regex
  const JP_REGEX = /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/;

  // Create & Inject Floating Toolbar
  function injectToolbar() {
    if (document.getElementById('trancy-ext-toolbar')) return;

    const bar = document.createElement('div');
    bar.id = 'trancy-ext-toolbar';
    bar.innerHTML = `
      <span style="font-weight: 800; color: #818cf8; display: flex; align-items: center; gap: 4px;">
        🌐 Trancy
      </span>
      <button class="trancy-btn-pill active" data-action="all">全顯</button>
      <button class="trancy-btn-pill" data-action="mask-jp" title="遮蔽日文！懸停或點擊解開">遮日</button>
      <button class="trancy-btn-pill" data-action="mask-zh" title="遮蔽中文！懸停或點擊解開">遮中</button>
      <button class="trancy-btn-pill" data-action="mask-both" title="雙向全遮">雙遮</button>
      <button class="trancy-btn-pill" id="trancy-btn-translate" style="background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff;">
        ✨ 翻譯本頁
      </button>
      <button class="trancy-btn-pill" id="trancy-btn-close" style="padding: 4px 6px;">✕</button>
    `;

    document.body.appendChild(bar);

    // Event listeners
    bar.querySelectorAll('button[data-action]').forEach(btn => {
      btn.addEventListener('click', () => {
        bar.querySelectorAll('button[data-action]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        setMaskMode(btn.dataset.action);
      });
    });

    document.getElementById('trancy-btn-translate').addEventListener('click', translatePage);
    document.getElementById('trancy-btn-close').addEventListener('click', () => {
      bar.remove();
      document.body.classList.remove('trancy-ext-mask-jp-active', 'trancy-ext-mask-zh-active');
    });
  }

  function setMaskMode(mode) {
    maskMode = mode;
    document.body.classList.remove('trancy-ext-mask-jp-active', 'trancy-ext-mask-zh-active');

    if (mode === 'mask-jp' || mode === 'mask-both') {
      document.body.classList.add('trancy-ext-mask-jp-active');
    }
    if (mode === 'mask-zh' || mode === 'mask-both') {
      document.body.classList.add('trancy-ext-mask-zh-active');
    }
  }

  // Edge Natural Voice TTS
  function speakJapanese(text) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ja-JP';

    const voices = window.speechSynthesis.getVoices();
    // Prioritize Microsoft Edge Natural Voices (Nanami / Keita)
    const naturalVoice = voices.find(v => 
      (v.name.includes('Nanami') || v.name.includes('Keita') || v.name.includes('Natural') || v.name.includes('Online')) &&
      (v.lang.startsWith('ja') || v.lang.includes('JP'))
    );

    if (naturalVoice) {
      utterance.voice = naturalVoice;
    }

    window.speechSynthesis.speak(utterance);
  }

  // Translate page paragraphs
  async function translatePage() {
    if (isTranslating) return;
    isTranslating = true;
    const btn = document.getElementById('trancy-btn-translate');
    if (btn) btn.textContent = '⏳ 翻譯中...';

    // Find readable elements containing Japanese
    const candidates = document.querySelectorAll('p, h1, h2, h3, h4, h5, article, li, blockquote');
    const targetNodes = [];

    candidates.forEach(el => {
      if (translatedElements.has(el)) return;
      if (el.closest('#trancy-ext-toolbar')) return;
      const text = el.innerText ? el.innerText.trim() : '';
      if (text.length >= 6 && JP_REGEX.test(text) && !el.querySelector('.trancy-injected-zh')) {
        targetNodes.push(el);
      }
    });

    for (let el of targetNodes.slice(0, 40)) { // batch first 40 blocks
      const origText = el.innerText.trim();
      el.classList.add('trancy-orig-jp');

      try {
        const zh = await fetchTranslation(origText);
        if (zh) {
          const zhDiv = document.createElement('div');
          zhDiv.className = 'trancy-injected-zh';
          zhDiv.textContent = zh;

          // TTS button
          const ttsBtn = document.createElement('button');
          ttsBtn.className = 'trancy-speak-btn';
          ttsBtn.title = '微軟 Edge 自然語音朗讀';
          ttsBtn.innerHTML = '🔊';
          ttsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            speakJapanese(origText);
          });
          zhDiv.prepend(ttsBtn);

          // Click on translation to reveal when masked
          zhDiv.addEventListener('click', () => {
            zhDiv.classList.toggle('trancy-revealed');
          });

          el.parentNode.insertBefore(zhDiv, el.nextSibling);
          translatedElements.add(el);
        }
      } catch (err) {
        console.warn('Trancy translation error:', err);
      }
    }

    isTranslating = false;
    if (btn) btn.textContent = '✨ 已完成翻譯';
  }

  // Free Google Translate API
  async function fetchTranslation(text) {
    if (!text) return '';
    const url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=zh-TW&dt=t&q=' + encodeURIComponent(text);
    const res = await fetch(url);
    const data = await res.json();
    if (data && data[0]) {
      return data[0].map(item => item[0]).join('');
    }
    return '';
  }

  // Auto-init toolbar when Japanese is detected
  if (JP_REGEX.test(document.body.innerText)) {
    injectToolbar();
  }

  // Listen to messages from popup
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
      if (req.action === 'toggle-toolbar') {
        injectToolbar();
        sendResponse({ status: 'ok' });
      }
    });
  }
})();
