# OCR quality regression

Open `tests/ocr-quality.html` through the local HTTP server or GitHub Pages and
press the run button. It uses the shipped v5.1.1 browser worker and local models.
The old baseline uses the previous whole-image/default-layout recognition;
the new implementation uses image preparation and explicit layout recognition.

Three synthetic fixtures use Windows BIZ UD Gothic, with Japanese engineering
text, a regular quantity table and a three-box flow diagram. These are controlled
regressions, not a claim about every photograph or complex chart.

Acceptance gates:

- Vertical: character error rate below 10%, ignoring whitespace.
- Table: all 12 cells exactly match, including quantities and units.
- Diagram in the default auto layout: all six expected labels/sentences appear as complete lines.

Run `node tests/novel-ocr.cjs` for grid structure/merged-cell rejection regressions.
The optional Node quality runner requires `tesseract.js@5.1.1` and `@napi-rs/canvas`.
Set `OCR_ENGINE_MODULE` and `OCR_CANVAS_MODULE` to package locations and
`OCR_CACHE_PATH` to a writable traineddata cache; then run
`node tests/ocr-quality.cjs results.json`. Browser rendering of resized pixels may
produce slightly different confidence values from the Node canvas backend.

UI check: choose fixture in the OCR modal, select table, recognize, import, and
start reading. Check original image, reconstructed table, sentence analysis,
and grammar markers are visible. Original image is retained for this import;
books are held in the reader's current session.
