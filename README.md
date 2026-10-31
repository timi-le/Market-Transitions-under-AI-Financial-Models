# CMTF market transitions: public research package

Author: Timilehin Olapade. Release: 31 October 2026.

Public research edition. Synthetic diagnostics are fully specified; production CMTF performance is not established by them.

Upload this ZIP as a new Overleaf project. Set Settings > Compiler > Main document to `main.tex` at the project root, and use pdfLaTeX. Only the root main file declares the document class and opens/closes the paper; `manuscript/preamble.tex` contains packages and definitions. The included figures and tables allow compilation without rerunning experiments. From the package root, run `make pdf`. Use Python 3.12, install requirements.txt, then run `make reproduce` to regenerate numerical outputs. Run `make validate` after compilation.

The full grid, adverse results, code, tests, and bibliographic link audit are retained. No DOI or remote research-repository URL has been invented. The package is ready for creation of a dedicated repository; it has not been published remotely.

The manuscript is a working paper and has not received independent peer review. The public study uses toy models, not a calibrated exchange. See the manuscript for claim boundaries and exact algorithm explanations.
