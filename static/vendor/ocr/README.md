# Bundled browser OCR

Tesseract.js and tesseract.js-core: **5.1.1**, obtained from official npm packages.
Only the LSTM core variants are included (SIMD and non-SIMD); their `.wasm.js`
files embed WebAssembly. `NovelOCR` explicitly uses OEM 1.

Japanese, Japanese vertical and Traditional Chinese models are the same
`4.0.0_best_int` models distributed by `@tesseract.js-data` on jsDelivr:

- https://cdn.jsdelivr.net/npm/@tesseract.js-data/jpn/4.0.0_best_int/jpn.traineddata.gz
- https://cdn.jsdelivr.net/npm/@tesseract.js-data/jpn_vert/4.0.0_best_int/jpn_vert.traineddata.gz
- https://cdn.jsdelivr.net/npm/@tesseract.js-data/chi_tra/4.0.0_best_int/chi_tra.traineddata.gz

All resources are served from this website's own origin. Photos are processed in
the browser. Engine, core and traineddata license files are included alongside
the distribution. Japanese models were deterministically recompressed with gzip
from the exact downloaded training data; this does not change model contents.

Model details: https://github.com/naptha/tessdata
Engine: https://github.com/naptha/tesseract.js
Core: https://github.com/naptha/tesseract.js-core
Training data: https://github.com/tesseract-ocr/tessdata_best
