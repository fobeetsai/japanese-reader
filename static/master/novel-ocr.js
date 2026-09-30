/* Browser OCR: explicit page layout, image preparation, ruled-table cells and source retention. */
(function (root) {
    'use strict';
    const scriptUrl = typeof document !== 'undefined' && document.currentScript?.src;
    const assets = scriptUrl ? new URL('../vendor/ocr/', scriptUrl).href : null;
    const CJK = '\\p{Script=Han}\\p{Script=Hiragana}\\p{Script=Katakana}';
    function cleanText(text) {
        return String(text || '').replace(/\r\n?/g, '\n')
            .replace(new RegExp(`([${CJK}])[ \\u3000]+(?=[${CJK}、。！？「」『』（）])`, 'gu'), '$1')
            .replace(/[ \u3000]+([、。！？])/g, '$1').trim();
    }
    function layoutOptions(mode, language) {
        return { languages: mode === 'vertical' ? 'jpn_vert' : (language === 'mixed' ? 'jpn+chi_tra' : 'jpn'),
            psm: ({ vertical: '5', horizontal: '6', figure: '11', table: '11', auto: '3' })[mode] || '3' };
    }
    // Find a regular ruled grid. Partial/merged grids are left as a source image, never invented as cells.
    function detectGrid(pixels, width, height) {
        const dark = (x, y) => {
            const i = (y * width + x) * 4;
            return pixels[i] * .299 + pixels[i + 1] * .587 + pixels[i + 2] * .114 < 145;
        };
        function scan(horizontal) {
            const outer = horizontal ? height : width, inner = horizontal ? width : height;
            const hits = [];
            for (let a = 0; a < outer; a++) {
                let run = 0, longest = 0, ink = 0;
                for (let b = 0; b < inner; b += 2) {
                    const hit = dark(horizontal ? b : a, horizontal ? a : b);
                    run = hit ? run + 2 : 0; if (hit) ink += 2;
                    longest = Math.max(longest, run);
                }
                if (longest >= Math.max(50, inner * .14) && ink >= inner * .28) hits.push(a);
            }
            const groups = [];
            for (const n of hits) {
                const g = groups[groups.length - 1];
                if (g && n - g[g.length - 1] <= 3) g.push(n); else groups.push([n]);
            }
            return groups.filter(g => g.length < 25).map(g => ({ at: Math.round((g[0] + g[g.length - 1]) / 2), start: g[0], end: g[g.length - 1] }));
        }
        const xs = scan(false), ys = scan(true);
        if (xs.length < 2 || ys.length < 2 || (xs.length - 1) * (ys.length - 1) > 80) return null;
        const coverage = (a, b, fixed, horizontal) => {
            let found = 0, total = 0;
            for (let n = a; n <= b; n += 2) { total++; if (dark(horizontal ? n : fixed, horizontal ? fixed : n)) found++; }
            return found / total;
        };
        if (xs.some(x => coverage(ys[0].at, ys[ys.length - 1].at, x.at, false) < .85) ||
            ys.some(y => coverage(xs[0].at, xs[xs.length - 1].at, y.at, true) < .85)) return null;
        const cells = [];
        for (let r = 0; r < ys.length - 1; r++) for (let c = 0; c < xs.length - 1; c++) {
            const left = xs[c].end + 3, top = ys[r].end + 3;
            const w = xs[c + 1].start - 3 - left, h = ys[r + 1].start - 3 - top;
            if (w < 15 || h < 15) return null;
            cells.push({ row: r, col: c, left, top, width: w, height: h });
        }
        return { cells, rows: ys.length - 1, cols: xs.length - 1,
            left: xs[0].start, top: ys[0].start, right: xs[xs.length - 1].end, bottom: ys[ys.length - 1].end };
    }
    function canvas(w, h) {
        const c = document.createElement('canvas'); c.width = w; c.height = h;
        const ctx = c.getContext('2d', { willReadFrequently: true }); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, w, h);
        return c;
    }
    function decode(url) {
        return new Promise((resolve, reject) => {
            const img = new Image(); img.onload = () => resolve(img);
            img.onerror = () => reject(new Error('圖片無法開啟，請先轉存為 JPG 或 PNG。')); img.src = url;
        });
    }
    async function prepareImage(url, options = {}) {
        const img = await decode(url);
        const angle = Number(options.rotation || 0), sideways = angle === 90 || angle === 270;
        const rotated = canvas(sideways ? img.naturalHeight : img.naturalWidth, sideways ? img.naturalWidth : img.naturalHeight);
        const rc = rotated.getContext('2d'); rc.translate(rotated.width / 2, rotated.height / 2); rc.rotate(angle * Math.PI / 180);
        rc.drawImage(img, -img.naturalWidth / 2, -img.naturalHeight / 2);
        let sx = 0, sw = rotated.width;
        if (options.region === 'left' || options.region === 'right') { sw = Math.floor(sw / 2); if (options.region === 'right') sx = sw; }
        const scale = Math.min(2.5, Math.max(1, 2200 / Math.max(sw, rotated.height)), 3400 / Math.max(sw, rotated.height));
        const out = canvas(Math.round(sw * scale) + 32, Math.round(rotated.height * scale) + 32);
        const ctx = out.getContext('2d', { willReadFrequently: true });
        ctx.drawImage(rotated, sx, 0, sw, rotated.height, 16, 16, out.width - 32, out.height - 32);
        if (options.enhance !== false) {
            const data = ctx.getImageData(0, 0, out.width, out.height), histogram = new Uint32Array(256);
            for (let i = 0; i < data.data.length; i += 4) histogram[Math.round(data.data[i] * .299 + data.data[i + 1] * .587 + data.data[i + 2] * .114)]++;
            let count = 0, low = 0, high = 255, total = out.width * out.height;
            for (let i = 0; i < 256; i++) { count += histogram[i]; if (count < total * .005) low = i; if (count < total * .995) high = i; }
            const range = Math.max(80, high - low);
            for (let i = 0; i < data.data.length; i += 4) {
                const grey = data.data[i] * .299 + data.data[i + 1] * .587 + data.data[i + 2] * .114;
                const value = Math.max(0, Math.min(255, (grey - low) * 255 / range));
                data.data[i] = data.data[i + 1] = data.data[i + 2] = value;
            }
            ctx.putImageData(data, 0, 0);
        }
        return out;
    }
    function crop(source, rect) {
        const c = canvas(rect.width + 24, rect.height + 24);
        c.getContext('2d').drawImage(source, rect.left, rect.top, rect.width, rect.height, 12, 12, rect.width, rect.height);
        return c;
    }
    function textLineMode(c) {
        const { data } = c.getContext('2d').getImageData(0, 0, c.width, c.height);
        let lines = 0, last = -100;
        for (let y = 0; y < c.height; y++) {
            let ink = 0;
            for (let x = 0; x < c.width; x++) if (data[(y * c.width + x) * 4] < 150) ink++;
            if (ink > 3) { if (y - last > 12) lines++; last = y; }
        }
        return lines === 1 ? '7' : '6';
    }
    // Remove cell whitespace and normalize single-line glyph height. Large isolated glyphs
    // can be misread even when whole-page scaling helps small body text.
    function trimText(source, targetHeight) {
        const { data } = source.getContext('2d').getImageData(0, 0, source.width, source.height);
        let left = source.width, top = source.height, right = -1, bottom = -1;
        for (let y = 0; y < source.height; y++) for (let x = 0; x < source.width; x++) {
            if (data[(y * source.width + x) * 4] < 150) {
                left = Math.min(left, x); right = Math.max(right, x); top = Math.min(top, y); bottom = Math.max(bottom, y);
            }
        }
        if (right < left) return null;
        const width = right - left + 1, height = bottom - top + 1;
        const scale = targetHeight ? Math.min(2, targetHeight / height) : 1;
        const c = canvas(Math.round(width * scale) + 40, Math.round(height * scale) + 40);
        c.getContext('2d').drawImage(source, left, top, width, height, 20, 20, c.width - 40, c.height - 40);
        return c;
    }
    function detectBoxes(source) {
        const w = source.width, h = source.height;
        const { data } = source.getContext('2d').getImageData(0, 0, w, h);
        const dark = (x, y) => data[(y * w + x) * 4] < 145;
        const segments = [];
        for (let y = 0; y < h; y++) {
            let start = -1;
            for (let x = 0; x <= w; x++) {
                if (x < w && dark(x, y)) { if (start < 0) start = x; }
                else if (start >= 0) {
                    if (x - start >= Math.max(80, w * .05)) {
                        const group = segments.find(s => y - s.bottom <= 3 && Math.abs(s.left - start) < 5 && Math.abs(s.right - (x - 1)) < 5);
                        if (group) group.bottom = y; else segments.push({ left: start, right: x - 1, top: y, bottom: y });
                    }
                    start = -1;
                }
            }
        }
        const boxes = [];
        for (const top of segments) {
            const bottom = segments.find(b => b.top > top.bottom + 30 && Math.abs(b.left - top.left) < 5 && Math.abs(b.right - top.right) < 5);
            if (!bottom || boxes.length >= 40) continue;
            const edge = x => {
                let count = 0;
                for (let y = top.bottom; y <= bottom.top; y++) if (dark(x, y) || dark(Math.min(w - 1, x + 2), y) || dark(Math.max(0, x - 2), y)) count++;
                return count / (bottom.top - top.bottom + 1);
            };
            if (edge(top.left + 1) < .85 || edge(top.right - 1) < .85) continue;
            if (boxes.some(b => top.top < b.bottom && bottom.bottom > b.top && top.left < b.right && top.right > b.left)) continue;
            boxes.push({ left: top.left, right: top.right, top: top.top, bottom: bottom.bottom });
        }
        return boxes.sort((a, b) => a.top - b.top || a.left - b.left);
    }
    async function recognize(source, options, hooks = {}) {
        const settings = layoutOptions(options.mode, options.language);
        const progress = hooks.progress || (() => {});
        let worker, timer, fail, stopped = false;
        const failure = new Promise((_, reject) => { fail = reject; });
        // Attach immediately: worker error callbacks can run before the first await settles.
        failure.catch(() => {});
        const bounded = async promise => {
            clearTimeout(timer);
            timer = setTimeout(() => fail(new Error('辨識等待逾時。請縮小辨識範圍，或確認網路後再試。')), 120000);
            return Promise.race([promise, failure]);
        };
        hooks.cancel && hooks.cancel(() => fail(new Error('已取消辨識。')));
        try {
            progress('準備日文辨識模型…');
            const creating = Tesseract.createWorker(settings.languages, 1, {
                ...(assets ? { workerPath: assets + 'worker.min.js', corePath: assets + 'core', langPath: assets + 'lang', workerBlobURL: false } : {}),
                logger: m => { if (!stopped && m.status === 'loading language traineddata') progress(`載入語言模型 ${Math.round(m.progress * 100)}%`); },
                errorHandler: err => fail(new Error(typeof err === 'string' ? err : err.message || '辨識引擎錯誤'))
            });
            creating.then(w => { if (stopped) w.terminate(); }, () => {});
            worker = await bounded(creating);
            const imageData = source.getContext('2d').getImageData(0, 0, source.width, source.height);
            const grid = ['auto', 'table'].includes(options.mode) ? detectGrid(imageData.data, source.width, source.height) : null;
            const boxes = !grid && ['auto', 'figure'].includes(options.mode) ? detectBoxes(source) : [];
            let texts = [], rows = [], confidences = [], warnings = [];
            async function readResult(c, psm, label) {
                progress(label);
                await bounded(worker.setParameters({ tessedit_pageseg_mode: psm, user_defined_dpi: '300', preserve_interword_spaces: '1' }));
                const ret = await bounded(worker.recognize(c));
                const text = cleanText(ret.data.text);
                return { text, confidence: Number(ret.data.confidence) || 0 };
            }
            async function read(c, psm, label) {
                const ret = await readResult(c, psm, label);
                if (ret.text) confidences.push(ret.confidence);
                return ret.text;
            }
            async function readCell(image, label) {
                const tight = trimText(image);
                if (!tight) return '';
                const singleLine = textLineMode(tight) === '7';
                const candidates = [await readResult(tight, singleLine ? '7' : '6', label)];
                if (singleLine) {
                    candidates.push(await readResult(trimText(image, 32), '7', label));
                    if (Math.max(...candidates.map(r => r.confidence)) < 85) candidates.push(await readResult(tight, '13', label));
                }
                const best = candidates.sort((a, b) => b.confidence - a.confidence)[0];
                confidences.push(best.confidence);
                if (best.confidence < 65) warnings.push(`${label.replace(/…$/, '')}：文字信心偏低，請校對。`);
                return best.text;
            }
            if (grid) {
                rows = Array.from({ length: grid.rows }, () => Array(grid.cols).fill(''));
                for (let i = 0; i < grid.cells.length; i++) {
                    const cell = grid.cells[i];
                    const image = crop(source, cell);
                    rows[cell.row][cell.col] = (await readCell(image, `辨識表格第 ${i + 1} / ${grid.cells.length} 格…`)).replace(/\n+/g, ' ');
                }
                const surrounding = [
                    { left: 0, top: 0, width: source.width, height: Math.max(0, grid.top - 4) },
                    { left: 0, top: grid.bottom + 4, width: source.width, height: source.height - grid.bottom - 4 },
                    { left: 0, top: grid.top, width: Math.max(0, grid.left - 4), height: grid.bottom - grid.top },
                    { left: grid.right + 4, top: grid.top, width: source.width - grid.right - 4, height: grid.bottom - grid.top }
                ];
                for (const rect of surrounding) if (rect.width > 40 && rect.height > 40) {
                    const t = await read(crop(source, rect), '11', '辨識表格周圍的標題與說明…'); if (t) texts.push(t);
                }
            } else if (options.mode === 'figure' || boxes.length) {
                const remainder = canvas(source.width, source.height);
                const ctx = remainder.getContext('2d'); ctx.drawImage(source, 0, 0);
                for (let i = 0; i < boxes.length; i++) {
                    const b = boxes[i], image = crop(source, { left: b.left + 8, top: b.top + 8, width: b.right - b.left - 16, height: b.bottom - b.top - 16 });
                    const t = await read(image, textLineMode(image), `辨識圖解框內文字 ${i + 1} / ${boxes.length}…`);
                    if (t) texts.push(t);
                    ctx.fillStyle = '#fff'; ctx.fillRect(b.left - 3, b.top - 3, b.right - b.left + 6, b.bottom - b.top + 6);
                }
                texts.push(await read(remainder, '11', '辨識圖解標題與其他文字…'));
            } else {
                texts.push(await read(source, settings.psm, options.mode === 'vertical' ? '依直排欄位辨識日文…' : '辨識頁面文字…'));
                if (options.mode === 'table') warnings.push('未找到完整規則框線，已擷取文字；請對照原圖核對欄位。');
            }
            const confidence = confidences.length ? confidences.reduce((a, b) => a + b, 0) / confidences.length : 0;
            if (confidence < 65) warnings.push('引擎對部分文字信心偏低，請對照原圖校對；可改選直排、半頁或旋轉後重試。');
            if (options.mode === 'figure' || boxes.length) warnings.push('已擷取圖中文字；圖形、箭頭與位置關係請查看保留的原圖。');
            if (options.mode === 'vertical' && options.language === 'mixed') warnings.push('直排模式使用日文直排模型；繁體中文請另選橫排或圖解模式校對。');
            return { text: texts.filter(Boolean).join('\n\n'), rows, confidence, warnings };
        } finally {
            stopped = true; clearTimeout(timer); hooks.cancel && hooks.cancel(null);
            if (worker) await worker.terminate().catch(() => {});
        }
    }
    function renderReference(book) {
        const panel = document.getElementById('novelOcrReference');
        if (!panel) return;
        panel.replaceChildren(); panel.hidden = !book?.ocrSource;
        if (!book?.ocrSource) return;
        const details = document.createElement('details'); details.open = true;
        const summary = document.createElement('summary'); summary.textContent = '原圖與圖表對照（本次匯入的完整圖片）'; details.append(summary);
        const link = document.createElement('a'); link.href = book.ocrSource.url; link.target = '_blank'; link.rel = 'noopener';
        const img = document.createElement('img'); img.src = book.ocrSource.url; img.alt = 'OCR 原始書頁，點擊放大';
        img.style.cssText = 'display:block;max-width:100%;max-height:65vh;object-fit:contain;margin:12px auto'; link.append(img); details.append(link);
        if (book.ocrSource.rows.length) {
            const table = document.createElement('table'); table.style.cssText = 'border-collapse:collapse;width:100%;margin:12px 0';
            const caption = table.createCaption(); caption.textContent = '校對後的表格';
            for (const row of book.ocrSource.rows) {
                const tr = table.insertRow();
                for (const value of row) { const td = tr.insertCell(); td.textContent = value; td.style.cssText = 'border:1px solid #888;padding:8px;white-space:pre-wrap'; }
            }
            details.append(table);
        }
        panel.append(details);
    }
    function install(importText, toast) {
        const el = id => document.getElementById(id);
        let sourceUrl = '', result = null, busy = false, cancel = null, generation = 0;
        const status = text => { el('ocrStatusText').textContent = text; };
        function setBusy(value) {
            busy = value;
            document.querySelectorAll('#ocrModal input, #ocrModal select, #btnStartOcrRecognize, #btnImportOcrText').forEach(n => { n.disabled = value; });
        }
        function resetResult() {
            result = null; el('ocrRecognizedText').value = ''; el('ocrTableText').value = '';
            el('ocrResultArea').style.display = 'none'; el('ocrTableArea').hidden = true; el('btnImportOcrText').style.display = 'none';
        }
        root.openOcrModal = () => { el('ocrModal').style.display = 'flex'; el('ocrModal').querySelector('button').focus(); };
        root.closeOcrModal = () => { generation++; cancel?.(); el('ocrModal').style.display = 'none'; };
        async function select(file) {
            if (busy || !file) return;
            const id = ++generation; resetResult(); sourceUrl = '';
            el('btnStartOcrRecognize').style.display = 'none'; el('ocrPreviewArea').style.display = 'none'; status('正在開啟圖片…');
            try {
                if (!file.type.startsWith('image/')) throw new Error('請選擇 JPG、PNG 或其他圖片檔案。');
                const url = await new Promise((resolve, reject) => { const r = new FileReader(); r.onload = () => resolve(r.result); r.onerror = () => reject(new Error('圖片讀取失敗。')); r.readAsDataURL(file); });
                const img = await decode(url); if (id !== generation) return;
                sourceUrl = url; el('ocrImagePreview').src = url; el('ocrPreviewArea').style.display = 'block';
                el('btnStartOcrRecognize').style.display = 'inline-flex';
                status(`圖片 ${img.naturalWidth} × ${img.naturalHeight}。${Math.max(img.naturalWidth, img.naturalHeight) < 1200 ? '文字偏小時建議使用原始照片或只辨識半頁。' : '請選擇符合圖片的版面。'}`);
            } catch (e) { if (id === generation) status(e.message); }
        }
        root.handleImageFileSelect = e => { const file = e.target.files?.[0]; e.target.value = ''; return select(file); };
        root.addEventListener('paste', e => {
            if (busy) return;
            const item = Array.from(e.clipboardData?.items || []).find(i => i.kind === 'file' && i.type.startsWith('image/'));
            if (item) { e.preventDefault(); root.openOcrModal(); select(item.getAsFile()); }
        });
        root.runOcrRecognition = async () => {
            if (busy) return;
            if (!sourceUrl) { status('請先選擇圖片或拍照。'); return; }
            const id = ++generation; setBusy(true); resetResult();
            try {
                if (!root.Tesseract) throw new Error('辨識引擎尚未載入，請確認網路後重新整理。');
                const options = { mode: el('ocrLayout').value, language: el('ocrLanguage').value, rotation: el('ocrRotation').value,
                    region: el('ocrRegion').value, enhance: el('ocrEnhance').checked };
                status('調整圖片大小、背景與對比…');
                const prepared = await prepareImage(sourceUrl, options); if (id !== generation) return;
                result = await recognize(prepared, options, { progress: t => { if (id === generation) status(t); }, cancel: fn => { cancel = fn; } });
                if (id !== generation) return;
                el('ocrRecognizedText').value = result.text;
                el('ocrTableText').value = result.rows.map(r => r.join('\t')).join('\n');
                el('ocrTableArea').hidden = !result.rows.length;
                el('ocrResultArea').style.display = 'block'; el('btnImportOcrText').style.display = 'inline-flex';
                const hasText = result.text || result.rows.some(r => r.some(Boolean));
                status(`${hasText ? '辨識完成，請對照原圖校對。' : '未辨識到文字，請調整版面或辨識範圍；仍可保留原圖。'} ${result.warnings.join(' ')}`);
            } catch (e) { if (id === generation) status(`辨識失敗：${e.message || String(e)}。可重新選圖或調整版面後重試。`); }
            finally { setBusy(false); }
        };
        root.importOcrText = () => {
            if (busy || !result) return;
            const text = el('ocrRecognizedText').value.trim(), tableText = el('ocrTableText').value.trim();
            const rows = tableText ? tableText.split(/\r?\n/).map(r => r.split('\t')) : [];
            const combined = [text, tableText].filter(Boolean).join('\n\n') || '（本頁未辨識到文字，請查看原圖。）';
            importText('📸 圖片書頁', combined, 'ocr');
            root.novelState.currentBook.ocrSource = { url: sourceUrl, rows };
            renderReference(root.novelState.currentBook);
            root.closeOcrModal(); toast('已匯入文字，原圖與表格將保留在閱讀頁。');
        };
    }
    const api = { cleanText, layoutOptions, detectGrid, prepareImage, recognize, renderReference, install };
    root.NovelOCR = api;
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
