'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');
const url = 'http://127.0.0.1:17863/index.html';
async function ready() {
    try {
        const res = await fetch('http://127.0.0.1:17863/health', { signal: AbortSignal.timeout(1500) });
        if (!res.ok) throw new Error('port');
        return (await res.json()).service === 'japanese-reader-speech-relay';
    } catch { return false; }
}
async function main() {
    if (!await ready()) {
        if (!fs.existsSync(path.join(__dirname, 'node_modules/ws/package.json'))) {
            console.log('首次啟動：安裝語音服務元件…');
            const install = spawnSync('cmd.exe', ['/d', '/c', 'npm ci --omit=dev --no-audit --no-fund'], { cwd: __dirname, windowsHide: true, stdio: 'inherit' });
            if (install.status !== 0) throw new Error('無法安裝語音元件，請確認已安裝 Node.js 並可連網。');
        }
        const helper = spawn(process.execPath, [path.join(__dirname, 'server.cjs')], { cwd: __dirname, detached: true, windowsHide: true, stdio: 'ignore' });
        helper.unref();
        for (let attempt = 0; attempt < 20; attempt++) {
            if (await ready()) break;
            await new Promise(resolve => setTimeout(resolve, 250));
        }
        if (!await ready()) throw new Error('語音服務未能啟動，17863 連接埠可能已被占用。');
    }
    const chrome = [process.env.PROGRAMFILES, process.env['PROGRAMFILES(X86)'], process.env.LOCALAPPDATA]
        .filter(Boolean).map(base => path.join(base, 'Google/Chrome/Application/chrome.exe')).find(file => fs.existsSync(file));
    if (!chrome) throw new Error('找不到 Chrome。請安裝後重試，或手動用 Chrome 開啟 ' + url);
    const browser = spawn(chrome, [url], { detached: true, windowsHide: false, stdio: 'ignore' }); browser.unref();
    console.log('Chrome 日文閱讀助手已開啟。語音服務運作至電腦關機。');
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
