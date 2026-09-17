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
    rubyMode: localStorage.getItem('trancy_ruby_mode') || 'show', // 'show', 'mask', 'hide'
    isPinned: localStorage.getItem('trancy_toolbar_pinned') === 'true',
    voice: localStorage.getItem('trancy_speech_voice') || 'nanami',
    speed: parseFloat(localStorage.getItem('trancy_speech_rate') || '1.0'),
    isTranslating: false,
    translatedCount: 0,
    isPickMode: false,
    currentSelection: null
  };

  // Set initial ruby mode on body
  document.body.setAttribute('data-trancy-ruby', state.rubyMode);

  const processedElements = new WeakSet();
  let currentAudio = null;
  let activeKaraokeInterval = null;
  let currentKaraokeTokens = null;

  // UI Component Singletons
  let hoverMarkerEl = null;
  let selectionTriggerEl = null;
  let selectionCardEl = null;
  let lastHoveredBlock = null;
  let hoverTimer = null;
  let currentPickHoverEl = null;

  // --------------------------------------------------------------------------
  // Karaoke Highlighting Engine (隨著顏色朗讀)
  // --------------------------------------------------------------------------
  function clearActiveKaraoke() {
    if (activeKaraokeInterval) {
      clearInterval(activeKaraokeInterval);
      activeKaraokeInterval = null;
    }
    if (currentKaraokeTokens) {
      currentKaraokeTokens.forEach(token => {
        token.classList.remove('trancy-karaoke-active', 'trancy-karaoke-passed');
      });
      currentKaraokeTokens = null;
    }
    document.querySelectorAll('.trancy-karaoke-active').forEach(el => el.classList.remove('trancy-karaoke-active'));
    document.querySelectorAll('.trancy-karaoke-passed').forEach(el => el.classList.remove('trancy-karaoke-passed'));
  }

  function setupKaraokeTokens(targetEl, text) {
    if (!targetEl) return null;
    if (!window.TrancyFurigana) return null;

    let words = targetEl.querySelectorAll('.trancy-karaoke-word');
    if (!words || words.length === 0) {
      targetEl.innerHTML = window.TrancyFurigana.toKaraokeHtml(text);
      words = targetEl.querySelectorAll('.trancy-karaoke-word');
    }

    // Attach click-to-speak on individual words
    words.forEach(wordSpan => {
      wordSpan.onclick = (e) => {
        e.stopPropagation();
        const wordText = decodeURIComponent(wordSpan.dataset.surface || '');
        if (wordText) {
          speakJapanese(wordText, wordSpan);
        }
      };
    });

    return words;
  }

  function bindAudioKaraoke(audio, tokens, text) {
    if (!audio || !tokens || tokens.length === 0) return;

    const tokenList = Array.from(tokens);
    currentKaraokeTokens = tokenList;

    const lengths = tokenList.map(t => Math.max(1, decodeURIComponent(t.dataset.surface || '').length));
    const totalLen = lengths.reduce((a, b) => a + b, 0);

    // Compute cumulative ratios for word boundary progression
    const cumulativeRatios = [];
    let running = 0;
    for (let i = 0; i < lengths.length; i++) {
      running += lengths[i];
      cumulativeRatios.push(running / totalLen);
    }

    let lastIdx = -1;

    const updateHighlight = () => {
      if (!audio || audio.paused || audio.ended) return;
      const duration = (audio.duration && !isNaN(audio.duration) && isFinite(audio.duration)) 
        ? audio.duration 
        : (totalLen * 0.28 / (state.speed || 1));
      const currentTime = audio.currentTime || 0;
      const currentRatio = Math.min(0.999, currentTime / duration);

      let activeIdx = 0;
      for (let i = 0; i < cumulativeRatios.length; i++) {
        if (currentRatio <= cumulativeRatios[i]) {
          activeIdx = i;
          break;
        }
      }

      if (activeIdx !== lastIdx) {
        lastIdx = activeIdx;
        tokenList.forEach((token, idx) => {
          if (idx === activeIdx) {
            token.classList.add('trancy-karaoke-active');
            token.classList.remove('trancy-karaoke-passed');
          } else if (idx < activeIdx) {
            token.classList.remove('trancy-karaoke-active');
            token.classList.add('trancy-karaoke-passed');
          } else {
            token.classList.remove('trancy-karaoke-active', 'trancy-karaoke-passed');
          }
        });
      }
    };

    if (activeKaraokeInterval) clearInterval(activeKaraokeInterval);
    activeKaraokeInterval = setInterval(updateHighlight, 35);

    const onAudioEnd = () => {
      if (activeKaraokeInterval) {
        clearInterval(activeKaraokeInterval);
        activeKaraokeInterval = null;
      }
      setTimeout(() => {
        tokenList.forEach(t => t.classList.remove('trancy-karaoke-active', 'trancy-karaoke-passed'));
        if (currentKaraokeTokens === tokenList) currentKaraokeTokens = null;
      }, 400);
    };

    audio.addEventListener('ended', onAudioEnd, { once: true });
    audio.addEventListener('pause', () => {
      if (audio.currentTime >= (audio.duration - 0.15)) onAudioEnd();
    }, { once: true });
  }

  // --------------------------------------------------------------------------
  // TTS Engine (Microsoft Edge Neural Voices + Google Cloud HD + Stepless Speed)
  // --------------------------------------------------------------------------
  function speakJapanese(text, targetEl = null) {
    if (!text) return;
    const cleanText = text.trim();
    if (!cleanText) return;

    // Stop ongoing audio & reset previous highlights
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    clearActiveKaraoke();

    // Prepare Karaoke tokens if target element provided
    let tokens = null;
    if (targetEl) {
      tokens = setupKaraokeTokens(targetEl, cleanText);
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
          fallbackSpeech(cleanText, tokens);
          return;
        }
        if (res && res.success && res.audioUrl) {
          currentAudio = new Audio(res.audioUrl);
          currentAudio.playbackRate = state.speed;
          bindAudioKaraoke(currentAudio, tokens, cleanText);
          currentAudio.play().catch(() => fallbackSpeech(cleanText, tokens));
        } else {
          fallbackSpeech(cleanText, tokens);
        }
      });
      return;
    }

    fallbackSpeech(cleanText, tokens);
  }

  function fallbackSpeech(cleanText, tokens = null) {
    // Mode A: Google Cloud HD Audio
    const url = `https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=ja&q=${encodeURIComponent(cleanText.slice(0, 180))}`;
    currentAudio = new Audio(url);
    currentAudio.playbackRate = state.speed;
    bindAudioKaraoke(currentAudio, tokens, cleanText);
    currentAudio.play().catch(() => {
      // Mode B: Web Speech API ONLY if it is a real Natural/Online voice (STRICTLY NO ROBOT HARUKA)
      if (!('speechSynthesis' in window)) return;
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = 'ja-JP';
      utterance.rate = state.speed;

      const voices = window.speechSynthesis.getVoices();
      let matchedVoice = voices.find(v => 
        (v.name.includes('Nanami') || v.name.includes('Keita') || v.name.includes('Natural') || v.name.includes('Online')) &&
        (v.lang.startsWith('ja') || v.lang.includes('JP'))
      );

      if (!matchedVoice) {
        matchedVoice = voices.find(v => (v.lang.startsWith('ja') || v.lang.includes('JP')) && !v.name.includes('Desktop') && !v.name.includes('Haruka'));
      }

      if (matchedVoice) {
        utterance.voice = matchedVoice;

        if (tokens && tokens.length > 0) {
          const tokenList = Array.from(tokens);
          currentKaraokeTokens = tokenList;

          utterance.onboundary = (event) => {
            const charIdx = event.charIndex || 0;
            let acc = 0;
            let activeIdx = 0;
            for (let i = 0; i < tokenList.length; i++) {
              const w = decodeURIComponent(tokenList[i].dataset.surface || '');
              acc += Math.max(1, w.length);
              if (acc > charIdx) {
                activeIdx = i;
                break;
              }
            }
            tokenList.forEach((token, idx) => {
              if (idx === activeIdx) {
                token.classList.add('trancy-karaoke-active');
                token.classList.remove('trancy-karaoke-passed');
              } else if (idx < activeIdx) {
                token.classList.remove('trancy-karaoke-active');
                token.classList.add('trancy-karaoke-passed');
              } else {
                token.classList.remove('trancy-karaoke-active', 'trancy-karaoke-passed');
              }
            });
          };

          utterance.onend = () => {
            setTimeout(() => {
              tokenList.forEach(t => t.classList.remove('trancy-karaoke-active', 'trancy-karaoke-passed'));
              if (currentKaraokeTokens === tokenList) currentKaraokeTokens = null;
            }, 400);
          };
        }

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
      <button class="trancy-btn-pill ${state.rubyMode !== 'hide' ? 'active' : ''}" id="trancy-btn-ruby" title="假名標註：點擊循環切換 [全顯假名] / [遮蔽自測] / [隱藏假名]">🌸 標註假名</button>
      <button class="trancy-btn-pill" id="trancy-btn-pick" title="切換點選模式：點選網頁任意段落直接翻譯">🎯 點選段落</button>
      <button class="trancy-btn-pill primary" id="trancy-btn-translate">✨ 翻譯本頁</button>
      
      <!-- Settings Button -->
      <button class="trancy-btn-icon" id="trancy-btn-settings" title="語音、假名與無段語速設定">⚙️</button>
      
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
            <span>🌸 漢字假名標註</span>
          </div>
          <select class="trancy-select" id="trancy-select-ruby">
            <option value="show">🌸 顯示假名 (小字平假名)</option>
            <option value="mask">👁️ 假名遮蔽 (懸停揭示自測)</option>
            <option value="hide">🚫 隱藏假名 (直讀訓練)</option>
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

    // --- Furigana Ruby Mode Controller ---
    const rubyBtn = document.getElementById('trancy-btn-ruby');
    const rubySelect = document.getElementById('trancy-select-ruby');
    if (rubySelect) rubySelect.value = state.rubyMode;

    function applyRubyMode(mode) {
      state.rubyMode = mode;
      localStorage.setItem('trancy_ruby_mode', mode);
      document.body.setAttribute('data-trancy-ruby', mode);
      if (rubySelect) rubySelect.value = mode;
      if (mode !== 'hide') {
        annotateJapaneseParagraphs();
      }
      if (rubyBtn) {
        if (mode === 'show') {
          rubyBtn.textContent = '🌸 假名:開';
          rubyBtn.classList.add('active');
          rubyBtn.title = '目前模式：全顯假名（點擊切換為遮蔽自測）';
        } else if (mode === 'mask') {
          rubyBtn.textContent = '🌸 假名:遮蔽';
          rubyBtn.classList.add('active');
          rubyBtn.title = '目前模式：遮蔽自測（滑鼠懸停顯示，點擊切換為隱藏）';
        } else {
          rubyBtn.textContent = '🌸 假名:關';
          rubyBtn.classList.remove('active');
          rubyBtn.title = '目前模式：隱藏假名（點擊切換為全顯假名）';
        }
      }
    }

    function annotateJapaneseParagraphs() {
      if (!window.TrancyFurigana) return;
      const candidates = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, blockquote, dt, dd, li, div');
      candidates.forEach(el => {
        if (el.closest('#trancy-ext-toolbar, #trancy-selection-card, #trancy-hover-marker, .trancy-injected-zh')) return;
        if (!isLeafLikeTextBlock(el)) return;
        if (el.querySelector('.trancy-ruby, .trancy-karaoke-word')) return;

        const text = (el.innerText || el.textContent || '').trim();
        if (text.length >= 2 && JP_REGEX.test(text) && window.TrancyFurigana.hasKanji(text)) {
          el.innerHTML = window.TrancyFurigana.toKaraokeHtml(text);
          el.querySelectorAll('.trancy-karaoke-word').forEach(wordSpan => {
            wordSpan.onclick = (e) => {
              e.stopPropagation();
              const w = decodeURIComponent(wordSpan.dataset.surface || '');
              if (w) speakJapanese(w, wordSpan);
            };
          });
        }
      });
    }

    if (rubyBtn) {
      applyRubyMode(state.rubyMode);
      rubyBtn.addEventListener('click', () => {
        if (state.rubyMode === 'show') {
          applyRubyMode('mask');
        } else if (state.rubyMode === 'mask') {
          applyRubyMode('hide');
        } else {
          applyRubyMode('show');
        }
      });
    }

    if (rubySelect) {
      rubySelect.addEventListener('change', (e) => {
        applyRubyMode(e.target.value);
      });
    }

    // --- Toolbar Event Listeners ---
    bar.querySelectorAll('button[data-action]').forEach(btn => {
      btn.addEventListener('click', () => {
        bar.querySelectorAll('button[data-action]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        setMaskMode(btn.dataset.action);
      });
    });

    // Pick-to-Translate Button
    const pickBtn = document.getElementById('trancy-btn-pick');
    pickBtn.addEventListener('click', () => {
      state.isPickMode = !state.isPickMode;
      if (state.isPickMode) {
        pickBtn.classList.add('active');
        document.body.classList.add('trancy-pick-mode-active');
        pickBtn.textContent = '🎯 點選中(點段落)';
      } else {
        pickBtn.classList.remove('active');
        document.body.classList.remove('trancy-pick-mode-active');
        pickBtn.textContent = '🎯 點選段落';
        clearPickHover();
      }
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
      document.body.classList.remove('trancy-ext-mask-jp-active', 'trancy-ext-mask-zh-active', 'trancy-pick-mode-active');
      state.isPickMode = false;
      clearPickHover();
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

  function updateTranslateBtnCount() {
    const btn = document.getElementById('trancy-btn-translate');
    if (btn && !state.isTranslating) {
      btn.textContent = `✨ 已譯 (${state.translatedCount}段)`;
    }
  }

  // --------------------------------------------------------------------------
  // Robust Multi-Fallback Translation Engine
  // --------------------------------------------------------------------------
  async function fetchTranslation(text) {
    if (!text) return '';
    const trimmed = text.trim();
    if (!trimmed) return '';

    // Route 1: Google GTX Client (ja -> zh-TW)
    try {
      const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=zh-TW&dt=t&q=${encodeURIComponent(trimmed)}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (data && data[0]) {
          const translated = data[0].map(item => item[0]).filter(Boolean).join('');
          if (translated) return translated;
        }
      }
    } catch (e) {
      console.warn('Google GTX sl=ja error:', e);
    }

    // Route 2: Google GTX Client Fallback (auto -> zh-TW)
    try {
      const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-TW&dt=t&q=${encodeURIComponent(trimmed)}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (data && data[0]) {
          const translated = data[0].map(item => item[0]).filter(Boolean).join('');
          if (translated) return translated;
        }
      }
    } catch (e) {
      console.warn('Google GTX sl=auto error:', e);
    }

    // Route 3: MyMemory Free Translation Mirror (Backup)
    try {
      const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(trimmed)}&langpair=ja|zh-TW`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (data && data.responseData && data.responseData.translatedText) {
          return data.responseData.translatedText;
        }
      }
    } catch (e) {
      console.warn('MyMemory fallback error:', e);
    }

    return '';
  }

  // --------------------------------------------------------------------------
  // Intelligent Leaf Text Block Detection
  // --------------------------------------------------------------------------
  function isLeafLikeTextBlock(el) {
    if (!el || el.nodeType !== 1) return false;
    if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEXTAREA', 'INPUT', 'SELECT', 'BUTTON', 'SVG'].includes(el.tagName)) return false;
    if (el.closest('#trancy-ext-toolbar, #trancy-selection-card, #trancy-hover-marker, .trancy-injected-zh')) return false;

    // Disallow parent containers that have nested paragraphs or headings
    const hasNestedMajorBlocks = el.querySelector('p, h1, h2, h3, h4, h5, h6, blockquote, dt, dd, li, article, section');
    if (hasNestedMajorBlocks) return false;

    const text = (el.innerText || el.textContent || '').trim();
    return text.length >= 3 && JP_REGEX.test(text);
  }

  function findTargetParagraph(el) {
    let curr = el;
    while (curr && curr !== document.body) {
      if (['P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'BLOCKQUOTE', 'DT', 'DD', 'LI'].includes(curr.tagName)) {
        const text = (curr.innerText || curr.textContent || '').trim();
        if (text.length >= 2 && JP_REGEX.test(text)) return curr;
      }
      if (curr.tagName === 'DIV' && isLeafLikeTextBlock(curr)) {
        return curr;
      }
      curr = curr.parentElement;
    }
    return null;
  }

  // --------------------------------------------------------------------------
  // Single Paragraph Translation Engine
  // --------------------------------------------------------------------------
  async function translateSingleElement(el, customText = null) {
    if (!el || el.nodeType !== 1) return null;
    if (el.closest('#trancy-ext-toolbar, #trancy-selection-card, #trancy-hover-marker')) return null;

    // Check if already translated
    if (processedElements.has(el)) {
      const next = el.nextElementSibling;
      if (next && next.classList.contains('trancy-injected-zh')) {
        next.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        return next;
      }
    }

    const text = customText || (el.innerText || el.textContent || '').trim();
    if (!text || text.length < 2 || !JP_REGEX.test(text)) return null;

    processedElements.add(el);
    el.classList.add('trancy-orig-jp');
    el.title = '日文原文（懸停或點擊解開遮蔽）';

    // Annotate Japanese paragraph with Furigana and Karaoke tokens
    if (window.TrancyFurigana) {
      el.innerHTML = window.TrancyFurigana.toKaraokeHtml(text);
      el.querySelectorAll('.trancy-karaoke-word').forEach(wordSpan => {
        wordSpan.onclick = (e) => {
          e.stopPropagation();
          const w = decodeURIComponent(wordSpan.dataset.surface || '');
          if (w) speakJapanese(w, wordSpan);
        };
      });
    }

    // Click on Japanese to reveal if masked
    el.addEventListener('click', (e) => {
      if (e.target.closest('.trancy-karaoke-word')) return;
      if (state.maskMode === 'mask-jp' || state.maskMode === 'mask-both') {
        el.classList.toggle('trancy-revealed');
      }
    });

    // Temporary loading placeholder
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'trancy-injected-zh trancy-translating-pulse';
    loadingDiv.innerHTML = '<span style="font-size:12px;opacity:0.75;">⏳ 正在翻譯此段...</span>';
    el.parentNode.insertBefore(loadingDiv, el.nextSibling);

    try {
      const zh = await fetchTranslation(text);
      if (!zh) {
        loadingDiv.remove();
        processedElements.delete(el);
        return null;
      }

      const zhDiv = document.createElement('div');
      zhDiv.className = 'trancy-injected-zh';

      // TTS Button with synchronized Karaoke color reading
      const ttsBtn = document.createElement('button');
      ttsBtn.className = 'trancy-speak-btn';
      ttsBtn.title = '真人自然語音朗讀（伴隨顏色同步高亮）';
      ttsBtn.innerHTML = '🔊';
      ttsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        speakJapanese(text, el);
      });
      zhDiv.appendChild(ttsBtn);

      // Translation Text
      const textSpan = document.createElement('span');
      textSpan.textContent = zh;
      zhDiv.appendChild(textSpan);

      // Copy Button
      const copyBtn = document.createElement('button');
      copyBtn.className = 'trancy-zh-copy-btn';
      copyBtn.title = '複製譯文';
      copyBtn.innerHTML = '📋';
      copyBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(zh).then(() => {
          copyBtn.innerHTML = '✅';
          setTimeout(() => { copyBtn.innerHTML = '📋'; }, 1500);
        });
      });
      zhDiv.appendChild(copyBtn);

      // Click on Chinese to reveal if masked
      zhDiv.addEventListener('click', () => {
        if (state.maskMode === 'mask-zh' || state.maskMode === 'mask-both') {
          zhDiv.classList.toggle('trancy-revealed');
        }
      });

      loadingDiv.replaceWith(zhDiv);
      state.translatedCount++;
      updateTranslateBtnCount();
      return zhDiv;
    } catch (err) {
      console.warn('translateSingleElement failed:', err);
      loadingDiv.remove();
      processedElements.delete(el);
      return null;
    }
  }

  // --------------------------------------------------------------------------
  // Hover Quick-Translate Marker ([🌐 譯此段])
  // --------------------------------------------------------------------------
  function setupHoverMarker() {
    hoverMarkerEl = document.createElement('div');
    hoverMarkerEl.id = 'trancy-hover-marker';
    hoverMarkerEl.innerHTML = '<span>🌐</span> 譯此段';
    document.body.appendChild(hoverMarkerEl);

    hoverMarkerEl.addEventListener('click', (e) => {
      e.stopPropagation();
      if (lastHoveredBlock) {
        translateSingleElement(lastHoveredBlock);
        hoverMarkerEl.style.display = 'none';
      }
    });

    document.addEventListener('mousemove', (e) => {
      if (state.isPickMode) return;
      if (hoverMarkerEl.contains(e.target)) return;

      const target = findTargetParagraph(e.target);
      if (target && !processedElements.has(target)) {
        lastHoveredBlock = target;
        clearTimeout(hoverTimer);
        const rect = target.getBoundingClientRect();
        if (rect.width > 30 && rect.height > 12) {
          const top = rect.top + window.scrollY + 2;
          const left = Math.min(window.innerWidth - 85, rect.right + window.scrollX - 75);
          hoverMarkerEl.style.top = `${top}px`;
          hoverMarkerEl.style.left = `${left}px`;
          hoverMarkerEl.style.display = 'inline-flex';
        }
      } else {
        hoverTimer = setTimeout(() => {
          if (!hoverMarkerEl.matches(':hover')) {
            hoverMarkerEl.style.display = 'none';
          }
        }, 350);
      }
    });
  }

  // --------------------------------------------------------------------------
  // Point-and-Click Translation Mode (🎯 點選翻譯)
  // --------------------------------------------------------------------------
  function clearPickHover() {
    if (currentPickHoverEl) {
      currentPickHoverEl.classList.remove('trancy-pick-target-hover');
      currentPickHoverEl = null;
    }
  }

  function setupPickModeListener() {
    document.addEventListener('mousemove', (e) => {
      if (!state.isPickMode) return;
      if (e.target.closest('#trancy-ext-toolbar')) {
        clearPickHover();
        return;
      }
      const target = findTargetParagraph(e.target);
      if (target && target !== currentPickHoverEl) {
        clearPickHover();
        currentPickHoverEl = target;
        currentPickHoverEl.classList.add('trancy-pick-target-hover');
      } else if (!target) {
        clearPickHover();
      }
    });

    document.addEventListener('click', (e) => {
      if (!state.isPickMode) return;
      if (e.target.closest('#trancy-ext-toolbar')) return;

      const target = findTargetParagraph(e.target);
      if (target) {
        e.preventDefault();
        e.stopPropagation();
        translateSingleElement(target);
      }
    }, true);
  }

  // --------------------------------------------------------------------------
  // Mouse Text Selection Quick Translation Bubble & Card
  // --------------------------------------------------------------------------
  function setupSelectionFeature() {
    // 1. Floating Bubble Trigger
    selectionTriggerEl = document.createElement('div');
    selectionTriggerEl.id = 'trancy-selection-trigger';
    selectionTriggerEl.innerHTML = '<span>🌐</span> 翻譯選段';
    document.body.appendChild(selectionTriggerEl);

    // 2. Floating Translation Card
    selectionCardEl = document.createElement('div');
    selectionCardEl.id = 'trancy-selection-card';
    selectionCardEl.innerHTML = `
      <div class="trancy-card-header">
        <span class="trancy-card-title">🌐 Trancy 選段翻譯</span>
        <button class="trancy-card-close" id="trancy-card-close-btn" title="關閉">✕</button>
      </div>
      <div class="trancy-card-orig" id="trancy-card-orig-box"></div>
      <div class="trancy-card-trans" id="trancy-card-trans-box"></div>
      <div class="trancy-card-actions">
        <button class="trancy-card-btn" id="trancy-card-speak-btn">🔊 朗讀</button>
        <button class="trancy-card-btn" id="trancy-card-copy-btn">📋 複製</button>
        <button class="trancy-card-btn primary" id="trancy-card-insert-btn" title="將翻譯插入該段落下方，支援中日雙向遮蔽">📌 插入段落</button>
      </div>
    `;
    document.body.appendChild(selectionCardEl);

    const closeBtn = document.getElementById('trancy-card-close-btn');
    closeBtn.addEventListener('click', () => {
      selectionCardEl.style.display = 'none';
    });

    // Trigger Click Handler
    selectionTriggerEl.addEventListener('click', async (e) => {
      e.stopPropagation();
      selectionTriggerEl.style.display = 'none';
      if (!state.currentSelection || !state.currentSelection.text) return;

      const { text, rect, anchorNode } = state.currentSelection;
      const origBox = document.getElementById('trancy-card-orig-box');
      const transBox = document.getElementById('trancy-card-trans-box');
      const speakBtn = document.getElementById('trancy-card-speak-btn');
      const copyBtn = document.getElementById('trancy-card-copy-btn');
      const insertBtn = document.getElementById('trancy-card-insert-btn');

      if (window.TrancyFurigana) {
        origBox.innerHTML = window.TrancyFurigana.toKaraokeHtml(text);
        origBox.querySelectorAll('.trancy-karaoke-word').forEach(wordSpan => {
          wordSpan.onclick = (e) => {
            e.stopPropagation();
            const w = decodeURIComponent(wordSpan.dataset.surface || '');
            if (w) speakJapanese(w, wordSpan);
          };
        });
      } else {
        origBox.textContent = text;
      }
      transBox.innerHTML = '<span class="trancy-translating-pulse" style="opacity:0.8;">⏳ 正在翻譯選取內容...</span>';

      // Position Card
      const cardTop = rect.bottom + window.scrollY + 8;
      const cardLeft = Math.min(window.innerWidth - 390, Math.max(12, rect.left + window.scrollX));
      selectionCardEl.style.top = `${cardTop}px`;
      selectionCardEl.style.left = `${cardLeft}px`;
      selectionCardEl.style.display = 'flex';

      // Fetch Translation
      const zh = await fetchTranslation(text);
      transBox.textContent = zh || '(無法取得翻譯，請重試)';

      // Action Handlers
      speakBtn.onclick = () => speakJapanese(text, origBox);
      copyBtn.onclick = () => {
        if (zh) {
          navigator.clipboard.writeText(zh).then(() => {
            copyBtn.textContent = '✅ 已複製';
            setTimeout(() => { copyBtn.textContent = '📋 複製'; }, 1500);
          });
        }
      };

      insertBtn.onclick = () => {
        let parentBlock = anchorNode && (anchorNode.nodeType === 1 ? anchorNode : anchorNode.parentElement);
        parentBlock = findTargetParagraph(parentBlock) || parentBlock;

        if (parentBlock && zh) {
          const zhDiv = document.createElement('div');
          zhDiv.className = 'trancy-injected-zh';

          const ttsBtn = document.createElement('button');
          ttsBtn.className = 'trancy-speak-btn';
          ttsBtn.title = '真人自然語音朗讀（伴隨顏色同步高亮）';
          ttsBtn.innerHTML = '🔊';
          ttsBtn.onclick = (ev) => {
            ev.stopPropagation();
            speakJapanese(text, parentBlock);
          };
          zhDiv.appendChild(ttsBtn);

          const tSpan = document.createElement('span');
          tSpan.textContent = zh;
          zhDiv.appendChild(tSpan);

          zhDiv.onclick = () => {
            if (state.maskMode === 'mask-zh' || state.maskMode === 'mask-both') {
              zhDiv.classList.toggle('trancy-revealed');
            }
          };

          parentBlock.parentNode.insertBefore(zhDiv, parentBlock.nextSibling);
          state.translatedCount++;
          updateTranslateBtnCount();

          insertBtn.textContent = '✅ 已插入';
          setTimeout(() => {
            selectionCardEl.style.display = 'none';
            insertBtn.textContent = '📌 插入段落';
          }, 800);
        }
      };
    });

    // Selection on MouseUp
    document.addEventListener('mouseup', (e) => {
      if (e.target.closest('#trancy-selection-trigger, #trancy-selection-card, #trancy-ext-toolbar')) return;

      setTimeout(() => {
        const sel = window.getSelection();
        if (!sel || sel.isCollapsed) {
          selectionTriggerEl.style.display = 'none';
          return;
        }

        const selectedText = sel.toString().trim();
        if (selectedText.length >= 2 && JP_REGEX.test(selectedText)) {
          const range = sel.getRangeAt(0);
          const rect = range.getBoundingClientRect();

          if (rect.width > 0 && rect.height > 0) {
            state.currentSelection = {
              text: selectedText,
              rect: rect,
              anchorNode: sel.anchorNode
            };

            const triggerTop = rect.bottom + window.scrollY + 6;
            const triggerLeft = Math.min(window.innerWidth - 120, Math.max(10, rect.left + window.scrollX));
            selectionTriggerEl.style.top = `${triggerTop}px`;
            selectionTriggerEl.style.left = `${triggerLeft}px`;
            selectionTriggerEl.style.display = 'inline-flex';
          }
        } else {
          selectionTriggerEl.style.display = 'none';
        }
      }, 30);
    });

    // Dismiss selection card on clicking outside
    document.addEventListener('mousedown', (e) => {
      if (!selectionCardEl.contains(e.target) && !selectionTriggerEl.contains(e.target)) {
        selectionCardEl.style.display = 'none';
      }
    });
  }

  // --------------------------------------------------------------------------
  // Full Page Translation (Broadened & Batching)
  // --------------------------------------------------------------------------
  async function translatePage() {
    if (state.isTranslating) return;
    state.isTranslating = true;

    const btn = document.getElementById('trancy-btn-translate');
    if (btn) btn.textContent = '⏳ 翻譯中...';

    // Broaden candidate selectors so articles inside div/sections are captured!
    const candidates = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, blockquote, dt, dd, li, div');
    const targetNodes = [];

    candidates.forEach(el => {
      if (processedElements.has(el)) return;
      if (el.closest('#trancy-ext-toolbar, #trancy-selection-card, #trancy-hover-marker, .trancy-injected-zh')) return;
      if (!isLeafLikeTextBlock(el)) return;

      const text = (el.innerText || el.textContent || '').trim();
      if (text.length >= 3 && JP_REGEX.test(text)) {
        targetNodes.push({ el, text });
      }
    });

    // Translate in parallel batches of 5 to avoid slow serial delays or timeouts
    const BATCH_SIZE = 5;
    for (let i = 0; i < targetNodes.length; i += BATCH_SIZE) {
      const chunk = targetNodes.slice(i, i + BATCH_SIZE);
      await Promise.all(chunk.map(item => translateSingleElement(item.el, item.text)));
      if (btn) {
        btn.textContent = `⏳ 翻譯中 (${Math.min(i + BATCH_SIZE, targetNodes.length)}/${targetNodes.length})`;
      }
      await new Promise(r => setTimeout(r, 60));
    }

    state.isTranslating = false;
    if (btn) {
      btn.textContent = `✨ 已譯 (${state.translatedCount}段)`;
      setTimeout(() => {
        btn.textContent = '✨ 繼續翻譯';
      }, 3000);
    }
  }

  // --------------------------------------------------------------------------
  // Toolbar Visibility Control
  // --------------------------------------------------------------------------
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

  // --------------------------------------------------------------------------
  // Initialization & Runtime Message Dispatcher
  // --------------------------------------------------------------------------
  function init() {
    setupHoverMarker();
    setupPickModeListener();
    setupSelectionFeature();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

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
