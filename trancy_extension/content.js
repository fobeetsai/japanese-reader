(function() {
  'use strict';

  // Prevent multiple injections
  if (window.__TRANCY_EXT_INJECTED__) return;
  window.__TRANCY_EXT_INJECTED__ = true;

  // Japanese detection regex
  const JP_REGEX = /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/;

  // State Management
  const state = {
    maskMode: 'all', // 'all', 'mask-jp', 'mask-zh', 'mask-both'
    isPinned: localStorage.getItem('trancy_toolbar_pinned') === 'true',
    voice: localStorage.getItem('trancy_speech_voice') || 'nanami',
    speed: parseFloat(localStorage.getItem('trancy_speech_rate') || '1.0'),
    isTranslating: false,
    translatedCount: 0
  };

  const processedElements = new WeakSet();
  let currentAudio = null;

  // --------------------------------------------------------------------------
  // TTS Engine (Microsoft Edge Neural Voices + Google Cloud HD + Stepless Speed)
  // --------------------------------------------------------------------------
  function speakJapanese(text) {
    if (!text) return;
    const cleanText = text.trim();
    if (!cleanText) return;

    // Stop ongoing audio
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    // Priority 1: Direct Edge Neural Audio synthesis from background service worker
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
      chrome.runtime.sendMessage({
        action: 'synthesize_speech',
        text: cleanText,
        voice: state.voice,
        speed: state.speed
      }, (res) => {
        if (chrome.runtime.lastError) {
          fallbackSpeech(cleanText);
          return;
        }
        if (res && res.success && res.audioUrl) {
          currentAudio = new Audio(res.audioUrl);
          currentAudio.playbackRate = state.speed;
          currentAudio.play().catch(() => fallbackSpeech(cleanText));
        } else {
          fallbackSpeech(cleanText);
        }
      });
      return;
    }

    fallbackSpeech(cleanText);
  }

  function fallbackSpeech(cleanText) {
    // Mode A: Google Cloud HD Audio
    const url = `https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=ja&q=${encodeURIComponent(cleanText.slice(0, 180))}`;
    currentAudio = new Audio(url);
    currentAudio.playbackRate = state.speed;
    currentAudio.play().catch(() => {
      // Mode B: Web Speech API ONLY if it is a real Natural/Online voice (STRICTLY NO ROBOT HARUKA)
      if (!('speechSynthesis' in window)) return;
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = 'ja-JP';
      utterance.rate = state.speed;

      const voices = window.speechSynthesis.getVoices();
      // Match Nanami / Keita / Natural / Online
      let matchedVoice = voices.find(v => 
        (v.name.includes('Nanami') || v.name.includes('Keita') || v.name.includes('Natural') || v.name.includes('Online')) &&
        (v.lang.startsWith('ja') || v.lang.includes('JP'))
      );

      // STRICT CHECK: If only robotic Haruka Desktop exists, DO NOT USE IT!
      if (!matchedVoice) {
        matchedVoice = voices.find(v => (v.lang.startsWith('ja') || v.lang.includes('JP')) && !v.name.includes('Desktop') && !v.name.includes('Haruka'));
      }

      if (matchedVoice) {
        utterance.voice = matchedVoice;
        window.speechSynthesis.speak(utterance);
      }
    });
  }

  // Preload browser voices
  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
      window.speechSynthesis.getVoices();
    };
  }

  // --------------------------------------------------------------------------
  // Floating Toolbar with Drag & Pin/Lock Support
  // --------------------------------------------------------------------------
  function injectToolbar() {
    if (document.getElementById('trancy-ext-toolbar')) return;

    const bar = document.createElement('div');
    bar.id = 'trancy-ext-toolbar';
    if (state.isPinned) bar.classList.add('trancy-ext-toolbar-locked');

    bar.innerHTML = `
      <div class="trancy-drag-handle" id="trancy-drag-handle" title="按住拖曳移動工具列">⠿</div>
      <span class="trancy-brand-tag">🌐 Trancy</span>
      <button class="trancy-btn-pill active" data-action="all">全顯</button>
      <button class="trancy-btn-pill" data-action="mask-jp" title="遮蔽日文原文（懸停或點擊解開）">遮日</button>
      <button class="trancy-btn-pill" data-action="mask-zh" title="遮蔽中文譯文（懸停或點擊解開）">遮中</button>
      <button class="trancy-btn-pill" data-action="mask-both" title="日中雙向遮蔽">雙遮</button>
      <button class="trancy-btn-pill primary" id="trancy-btn-translate">✨ 翻譯本頁</button>
      
      <!-- Settings Button -->
      <button class="trancy-btn-icon" id="trancy-btn-settings" title="語音與無段語速設定">⚙️</button>
      
      <!-- Pin / Lock Button -->
      <button class="trancy-btn-icon ${state.isPinned ? 'active' : ''}" id="trancy-btn-pin" title="${state.isPinned ? '已固定位置（點擊解鎖）' : '釘選固定位置'}">
        ${state.isPinned ? '📌' : '🔓'}
      </button>

      <!-- Close Button -->
      <button class="trancy-btn-icon" id="trancy-btn-close" title="關閉工具列">✕</button>

      <!-- Settings Popover -->
      <div id="trancy-settings-popover">
        <div class="trancy-setting-row">
          <div class="trancy-setting-label">
            <span>🗣️ 日語語音引擎</span>
          </div>
          <select class="trancy-select" id="trancy-select-voice">
            <option value="nanami">🌸 微軟 Nanami (七海・自然女聲)</option>
            <option value="keita">👦 微軟 Keita (圭太・自然男聲)</option>
            <option value="google-hd">☁️ Google 真人高音質 (Cloud HD)</option>
            <option value="default">🌐 瀏覽器日語 (系統預設)</option>
          </select>
        </div>

        <div class="trancy-setting-row">
          <div class="trancy-setting-label">
            <span>⚡ 無段數語速調節</span>
            <span class="trancy-setting-val" id="trancy-speed-val">${state.speed.toFixed(2)}x</span>
          </div>
          <input type="range" class="trancy-range-slider" id="trancy-speed-slider" min="0.5" max="2.0" step="0.05" value="${state.speed}">
          <div class="trancy-speed-presets">
            <button class="trancy-speed-preset-btn" data-val="0.8">0.8x 慢速</button>
            <button class="trancy-speed-preset-btn" data-val="1.0">1.0x 標準</button>
            <button class="trancy-speed-preset-btn" data-val="1.2">1.2x 快速</button>
          </div>
        </div>

        <div style="display: flex; gap: 8px; margin-top: 4px;">
          <button class="trancy-btn-pill" id="trancy-btn-test-speech" style="flex: 1; justify-content: center;">
            ▶️ 試聽當前發音
          </button>
          <button class="trancy-btn-pill" id="trancy-btn-reset-pos" style="padding: 4px 8px;" title="復位到右上角">
            📍 復位位置
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(bar);

    // Restore saved position
    const savedPos = localStorage.getItem('trancy_toolbar_pos');
    if (savedPos) {
      try {
        const { left, top } = JSON.parse(savedPos);
        const maxLeft = window.innerWidth - 350;
        const maxTop = window.innerHeight - 80;
        bar.style.left = `${Math.min(Math.max(10, left), maxLeft)}px`;
        bar.style.top = `${Math.min(Math.max(10, top), maxTop)}px`;
        bar.style.right = 'auto';
      } catch (e) {}
    }

    // Set initial voice dropdown value
    const voiceSelect = document.getElementById('trancy-select-voice');
    if (voiceSelect) voiceSelect.value = state.voice;

    // --- Drag & Drop Functionality ---
    setupDraggable(bar);

    // --- Toolbar Event Listeners ---
    bar.querySelectorAll('button[data-action]').forEach(btn => {
      btn.addEventListener('click', () => {
        bar.querySelectorAll('button[data-action]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        setMaskMode(btn.dataset.action);
      });
    });

    document.getElementById('trancy-btn-translate').addEventListener('click', translatePage);

    // Settings Toggle
    const settingsBtn = document.getElementById('trancy-btn-settings');
    const settingsPopover = document.getElementById('trancy-settings-popover');
    settingsBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      settingsPopover.classList.toggle('show');
    });

    // Close settings when clicking outside
    document.addEventListener('click', (e) => {
      if (!bar.contains(e.target)) {
        settingsPopover.classList.remove('show');
      }
    });

    // Voice Selection change
    voiceSelect.addEventListener('change', (e) => {
      state.voice = e.target.value;
      localStorage.setItem('trancy_speech_voice', state.voice);
    });

    // Stepless Speed Slider change
    const speedSlider = document.getElementById('trancy-speed-slider');
    const speedVal = document.getElementById('trancy-speed-val');
    speedSlider.addEventListener('input', (e) => {
      state.speed = parseFloat(e.target.value);
      speedVal.textContent = state.speed.toFixed(2) + 'x';
      localStorage.setItem('trancy_speech_rate', state.speed.toString());
    });

    // Speed Preset buttons
    bar.querySelectorAll('.trancy-speed-preset-btn').forEach(b => {
      b.addEventListener('click', () => {
        const val = parseFloat(b.dataset.val);
        state.speed = val;
        speedSlider.value = val;
        speedVal.textContent = val.toFixed(2) + 'x';
        localStorage.setItem('trancy_speech_rate', val.toString());
      });
    });

    // Test Speech button
    document.getElementById('trancy-btn-test-speech').addEventListener('click', () => {
      speakJapanese('こんにちは！Trancyの自然な音声へようこそ。');
    });

    // Reset Position button
    document.getElementById('trancy-btn-reset-pos').addEventListener('click', () => {
      bar.style.top = '18px';
      bar.style.right = '24px';
      bar.style.left = 'auto';
      localStorage.removeItem('trancy_toolbar_pos');
    });

    // Pin / Lock Toggle
    const pinBtn = document.getElementById('trancy-btn-pin');
    pinBtn.addEventListener('click', () => {
      state.isPinned = !state.isPinned;
      localStorage.setItem('trancy_toolbar_pinned', state.isPinned);
      if (state.isPinned) {
        bar.classList.add('trancy-ext-toolbar-locked');
        pinBtn.classList.add('active');
        pinBtn.textContent = '📌';
        pinBtn.title = '已固定位置（點擊解鎖）';
      } else {
        bar.classList.remove('trancy-ext-toolbar-locked');
        pinBtn.classList.remove('active');
        pinBtn.textContent = '🔓';
        pinBtn.title = '釘選固定位置';
      }
    });

    // Close button
    document.getElementById('trancy-btn-close').addEventListener('click', () => {
      bar.remove();
      document.body.classList.remove('trancy-ext-mask-jp-active', 'trancy-ext-mask-zh-active');
    });
  }

  // Draggable Implementation
  function setupDraggable(bar) {
    const handle = document.getElementById('trancy-drag-handle');
    let isDragging = false;
    let startX, startY, origLeft, origTop;

    const startDrag = (e) => {
      if (state.isPinned) return; // Locked: do not allow drag
      // Don't drag if clicking buttons, select, or inside settings popover
      if (e.target.closest('button, select, input, #trancy-settings-popover')) return;

      isDragging = true;
      bar.classList.add('trancy-dragging');

      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);

      startX = clientX;
      startY = clientY;

      const rect = bar.getBoundingClientRect();
      origLeft = rect.left;
      origTop = rect.top;

      document.addEventListener('mousemove', onDrag);
      document.addEventListener('mouseup', stopDrag);
      document.addEventListener('touchmove', onDrag, { passive: false });
      document.addEventListener('touchend', stopDrag);
      e.preventDefault();
    };

    const onDrag = (e) => {
      if (!isDragging) return;
      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);

      const dx = clientX - startX;
      const dy = clientY - startY;

      let newLeft = origLeft + dx;
      let newTop = origTop + dy;

      // Clamping to screen boundaries
      const maxLeft = window.innerWidth - bar.offsetWidth - 8;
      const maxTop = window.innerHeight - bar.offsetHeight - 8;
      newLeft = Math.max(8, Math.min(newLeft, maxLeft));
      newTop = Math.max(8, Math.min(newTop, maxTop));

      bar.style.left = `${newLeft}px`;
      bar.style.top = `${newTop}px`;
      bar.style.right = 'auto';

      if (e.cancelable) e.preventDefault();
    };

    const stopDrag = () => {
      if (!isDragging) return;
      isDragging = false;
      bar.classList.remove('trancy-dragging');

      document.removeEventListener('mousemove', onDrag);
      document.removeEventListener('mouseup', stopDrag);
      document.removeEventListener('touchmove', onDrag);
      document.removeEventListener('touchend', stopDrag);

      // Save position to localStorage
      localStorage.setItem('trancy_toolbar_pos', JSON.stringify({
        left: bar.offsetLeft,
        top: bar.offsetTop
      }));
    };

    handle.addEventListener('mousedown', startDrag);
    handle.addEventListener('touchstart', startDrag, { passive: false });
  }

  // --------------------------------------------------------------------------
  // Mask Mode Management (Fixing "遮日 居然變成全遮")
  // --------------------------------------------------------------------------
  function setMaskMode(mode) {
    state.maskMode = mode;
    document.body.classList.remove('trancy-ext-mask-jp-active', 'trancy-ext-mask-zh-active');

    if (mode === 'mask-jp') {
      document.body.classList.add('trancy-ext-mask-jp-active');
      // If user chooses mask-jp and page hasn't been translated, auto-translate so Chinese appears!
      if (state.translatedCount === 0) {
        translatePage();
      }
    } else if (mode === 'mask-zh') {
      document.body.classList.add('trancy-ext-mask-zh-active');
      if (state.translatedCount === 0) {
        translatePage();
      }
    } else if (mode === 'mask-both') {
      document.body.classList.add('trancy-ext-mask-jp-active', 'trancy-ext-mask-zh-active');
      if (state.translatedCount === 0) {
        translatePage();
      }
    }
  }

  // --------------------------------------------------------------------------
  // Pure Leaf Block Selection & Immersive Translation
  // --------------------------------------------------------------------------
  // Checks if element is a pure leaf text block without nested block children
  function isPureLeafTextBlock(el) {
    if (!el || el.nodeType !== 1) return false;
    // Disallow containers that contain other paragraphs or structural containers
    const nestedBlocks = el.querySelector('p, h1, h2, h3, h4, h5, h6, blockquote, dt, dd, li, table, pre, article, section, header, footer, nav');
    return !nestedBlocks;
  }

  async function translatePage() {
    if (state.isTranslating) return;
    state.isTranslating = true;

    const btn = document.getElementById('trancy-btn-translate');
    if (btn) btn.textContent = '⏳ 翻譯中...';

    // Only query specific leaf text blocks, NEVER large containers like article or div
    const candidates = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, blockquote, dt, dd, li');
    const targetNodes = [];

    candidates.forEach(el => {
      if (processedElements.has(el)) return;
      if (el.closest('#trancy-ext-toolbar')) return;
      if (!isPureLeafTextBlock(el)) return;

      const text = (el.innerText || el.textContent || '').trim();
      // Must have at least 4 characters, contain Japanese, and not already have injected translation
      if (text.length >= 4 && JP_REGEX.test(text)) {
        targetNodes.push({ el, text });
      }
    });

    // Translate up to 50 leaf blocks per batch
    const batch = targetNodes.slice(0, 50);

    for (let item of batch) {
      const { el, text } = item;
      processedElements.add(el);

      // Mark the Japanese leaf element specifically
      el.classList.add('trancy-orig-jp');
      el.title = '日文原文（懸停或點擊解開遮蔽）';

      // Click on Japanese to reveal if masked
      el.addEventListener('click', (e) => {
        if (state.maskMode === 'mask-jp' || state.maskMode === 'mask-both') {
          el.classList.toggle('trancy-revealed');
        }
      });

      try {
        const zh = await fetchTranslation(text);
        if (zh) {
          const zhDiv = document.createElement('div');
          zhDiv.className = 'trancy-injected-zh';

          // TTS Button
          const ttsBtn = document.createElement('button');
          ttsBtn.className = 'trancy-speak-btn';
          ttsBtn.title = '真人自然語音朗讀';
          ttsBtn.innerHTML = '🔊';
          ttsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            speakJapanese(text);
          });
          zhDiv.appendChild(ttsBtn);

          // Translation Text Node
          const textSpan = document.createElement('span');
          textSpan.textContent = zh;
          zhDiv.appendChild(textSpan);

          // Click on Chinese to reveal if masked
          zhDiv.addEventListener('click', () => {
            if (state.maskMode === 'mask-zh' || state.maskMode === 'mask-both') {
              zhDiv.classList.toggle('trancy-revealed');
            }
          });

          // Insert translation directly as the NEXT sibling of the Japanese element
          el.parentNode.insertBefore(zhDiv, el.nextSibling);
          state.translatedCount++;
        }
      } catch (err) {
        console.warn('Trancy translation error:', err);
      }
    }

    state.isTranslating = false;
    if (btn) {
      btn.textContent = `✨ 已譯 (${state.translatedCount}段)`;
      setTimeout(() => {
        btn.textContent = '✨ 繼續翻譯';
      }, 3000);
    }
  }

  // Google Translate API with fallback
  async function fetchTranslation(text) {
    if (!text) return '';
    try {
      const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=zh-TW&dt=t&q=${encodeURIComponent(text)}`;
      const res = await fetch(url);
      const data = await res.json();
      if (data && data[0]) {
        return data[0].map(item => item[0]).join('');
      }
    } catch (e) {
      console.warn('Fetch translation error:', e);
    }
    return '';
  }

  function toggleToolbar() {
    const existing = document.getElementById('trancy-ext-toolbar');
    if (existing) {
      if (existing.style.display === 'none') {
        existing.style.display = 'flex';
      } else {
        existing.style.display = 'none';
      }
    } else {
      injectToolbar();
    }
  }

  // NOTE: The toolbar will NEVER automatically appear when loading a webpage.
  // It will ONLY appear when the user explicitly clicks the extension APP icon!

  // Extension runtime messaging listener
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
      if (req.action === 'toggle-toolbar') {
        toggleToolbar();
        const existing = document.getElementById('trancy-ext-toolbar');
        const isVisible = existing && existing.style.display !== 'none';
        sendResponse({ status: 'ok', visible: isVisible });
      }
    });
  }
})();
