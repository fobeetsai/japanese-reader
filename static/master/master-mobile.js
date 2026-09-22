(() => {
  'use strict';
  const mobile = matchMedia('(max-width: 900px)');
  const body = document.body;
  const byId = id => document.getElementById(id);
  body.dataset.masterView = 'deep';
  const settings = byId('btnMobileSettings');
  settings.addEventListener('click', () => {
    const open = body.classList.toggle('mobile-settings-open');
    settings.setAttribute('aria-expanded', String(open));
  });
  byId('btnMobileApps').addEventListener('click', event => {
    const open = body.classList.toggle('mobile-apps-open');
    event.currentTarget.setAttribute('aria-expanded', String(open));
    if (open) document.querySelector('.cross-app-nav-bar').scrollIntoView({block: 'start'});
  });
  // Keep the existing view controller and all learning data intact.
  const originalSwitch = window.switchMasterView;
  window.switchMasterView = function(view) {
    originalSwitch(view);
    body.dataset.masterView = view;
    settings.hidden = view !== 'deep';
    document.querySelectorAll('.master-tab-btn').forEach(button => {
      button.setAttribute('aria-selected', String(button.dataset.view === view));
    });
    if (mobile.matches) window.scrollTo({top: 0, behavior: 'auto'});
  };
  const reader = byId('readerDeck');
  const syncReader = () => body.classList.toggle('mobile-has-article', reader.style.display !== 'none');
  new MutationObserver(syncReader).observe(reader, {attributes: true, attributeFilter: ['style']});
  syncReader();
  // Expose the sentence inspector without requiring a long scroll on a phone.
  byId('articleContentBox').addEventListener('click', event => {
    if (!mobile.matches || !event.target.closest('.sentence-row')) return;
    byId('btnMobileAnalyze').hidden = false;
  });
  byId('btnMobileAnalyze').addEventListener('click', () => byId('analyzerCard').scrollIntoView({behavior: 'smooth', block: 'start'}));

  const audio = byId('masterAudioBar');
  const expand = byId('btnMobileAudio');
  expand.addEventListener('click', () => {
    const open = audio.classList.toggle('expanded');
    expand.setAttribute('aria-expanded', String(open));
    expand.setAttribute('aria-label', open ? '收合播放設定' : '展開播放設定');
    expand.textContent = open ? '⌄' : '⌃';
  });
  const updateAudioHeight = () => document.documentElement.style.setProperty('--mobile-player-height', `${audio.getBoundingClientRect().height + 8}px`);
  new ResizeObserver(updateAudioHeight).observe(audio);
  if (window.visualViewport) {
    const updateKeyboard = () => {
      const editing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
      body.classList.toggle('mobile-keyboard-open', mobile.matches && editing && window.innerHeight - visualViewport.height > 120);
    };
    visualViewport.addEventListener('resize', updateKeyboard);
    document.addEventListener('focusout', () => body.classList.remove('mobile-keyboard-open'));
  }
  const help = byId('mobileInstallHelp');
  const installButton = byId('btnMobileInstall');
  const confirm = byId('btnConfirmInstall');
  let installPrompt = null;
  const standalone = matchMedia('(display-mode: standalone)');
  const updateInstalled = () => { installButton.hidden = standalone.matches || navigator.standalone === true; };
  updateInstalled();
  standalone.addEventListener('change', updateInstalled);
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    installPrompt = event;
    confirm.hidden = false;
  });
  window.addEventListener('appinstalled', () => { installButton.hidden = true; help.close(); installPrompt = null; });
  installButton.addEventListener('click', () => help.showModal());
  byId('btnCloseInstall').addEventListener('click', () => help.close());
  confirm.addEventListener('click', async () => {
    if (!installPrompt) return;
    await installPrompt.prompt();
    await installPrompt.userChoice;
    installPrompt = null;
    confirm.hidden = true;
    help.close();
  });
  document.querySelectorAll('button[title], select[title]').forEach(element => {
    if (!element.textContent.trim() || element.querySelector('i') && element.textContent.trim().length === 0) element.setAttribute('aria-label', element.title);
  });
  if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    navigator.serviceWorker.register('./sw.js').catch(error => console.warn('離線快取尚未啟用', error));
  }
})();
