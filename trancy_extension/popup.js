document.getElementById('btn-activate').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.id) {
    chrome.tabs.sendMessage(tab.id, { action: 'toggle-toolbar' }, () => {
      window.close();
    });
  }
});
