document.addEventListener('DOMContentLoaded', async () => {
  const btnActivate = document.getElementById('btn-activate');
  if (!btnActivate) return;

  btnActivate.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.id) return;

    chrome.tabs.sendMessage(tab.id, { action: 'toggle-toolbar' }, (response) => {
      if (chrome.runtime.lastError) {
        // Content script not loaded yet, inject content.css and content.js
        chrome.scripting.insertCSS({
          target: { tabId: tab.id },
          files: ['content.css']
        }, () => {
          chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content.js']
          }, () => {
            setTimeout(() => {
              chrome.tabs.sendMessage(tab.id, { action: 'toggle-toolbar' });
              window.close();
            }, 120);
          });
        });
      } else {
        window.close();
      }
    });
  });
});
