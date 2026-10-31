# Market Transitions under AI Financial Models

### Alpha Decay, Instability, and Evidence-Gated Neuro-Symbolic Adaptation

**Timilehin Olapade** · Independent researcher  
[ORCID: 0009-0001-4211-3105](https://orcid.org/0009-0001-4211-3105) · Public research edition · 31 October 2026

[![CMTF market transitions: gyroscopic animated explainer](./cmtf-market-transitions.gif)](./cmtf-market-transitions.mp4)

[Watch or download the 30-second video](./cmtf-market-transitions.mp4)

**Models act. Markets respond. The feedback changes the next decision.**

Financial models operate inside the markets they seek to predict. Their orders can change prices, liquidity, execution costs, and the relationships behind future forecasts. This research studies that interaction: how model similarity, adaptation speed, leverage, and evidence requirements shape individual outcomes and collective market behavior.

Building on the **Causal Macro Transmission Framework (CMTF)**, the paper connects neural proposals, explicit evidence requirements, regime-conditioned routing, and constrained decisions. The accompanying code provides reproducible experiments for examining those ideas and their failure cases.

[Read the manuscript source](./main.tex) · [Explore the code](./code/) · [Inspect the results](./results/) · [Citation metadata](./CITATION.cff)

## Research questions

- How does model activity change the market conditions on which subsequent decisions depend?
- When do correlated behavior, rapid adjustment, leverage, and liquidity interact to amplify instability?
- Can lower losses reflect reduced exposure rather than more accurate inference?
- How should forecasting quality, individual protection, and collective recovery be evaluated together?

## Experiments and findings

The release contains **two separate synthetic diagnostics**:

| Study | Design | What it examines |
|---|---|---|
| Structural estimation | 200 replications per scenario and estimator | Confounding, regime uncertainty, misspecified observation mappings, and coefficient-estimation error |
| Interactive market feedback | 24 modeled participants; 256 configurations; 64 replications per configuration | Order impact, liquidity, adjustment speed, leverage, evidence eligibility, and recovery |

Regime averaging improves coefficient MSE under nominal assumptions, but a misspecified regime mapping can reverse that advantage. Regime confidence alone does not establish causal identification.

The market study also shows why return and forecast quality must be inspected together:

| Policy | Mean net return | Forecast MSE |
|---|---:|---:|
| Ungated | −8.00% | 0.425 |
| Liquidity cap only | −7.28% | 0.425 |
| Evidence gate | −6.81% | 0.425 |
| Wrong evidence | −2.80% | 2.962 |

These are descriptive averages across equally weighted simulation settings. All mean net returns shown are negative; lower MSE is better. The wrong-evidence policy trades less and has the smallest average loss despite worse forecasts. Smaller losses alone therefore do not establish better inference. Scenario detail, paired comparisons, and uncertainty estimates are retained in the manuscript and results.

## Repository guide

| Path | Contents |
|---|---|
| [`main.tex`](./main.tex) | Main LaTeX document; compile this file |
| [`manuscript/`](./manuscript/) | Shared setup, paper sections, tables, and figures |
| [`code/`](./code/) | Evidence router, structural study, market study, sensitivity analysis, and figure generation |
| [`results/`](./results/) | Replication-level outputs, summaries, paired comparisons, manifests, and validation records |
| [`tests/`](./tests/) | Router and market-contract checks |
| [`requirements.txt`](./requirements.txt) | Python dependencies |
| [`Makefile`](./Makefile) | Test, reproduction, PDF, and validation commands |
| [`CITATION.cff`](./CITATION.cff) | Machine-readable citation metadata |

## Reproduce the experiments

Use **Python 3.12** in a fresh virtual environment. From the repository root, install the dependencies:

```bash
python -m pip install -r requirements.txt
```

With Make installed:

```bash
make test
make reproduce
```

`make reproduce` runs the tests, both primary studies, the sensitivity analysis, and figure generation. To run the same sequence without Make, including on Windows:

```bash
python -m unittest discover -s tests -v
python code/synthetic_study.py
python code/market_study.py
python code/sensitivity.py
python code/build_figures.py
```

Generated outputs are written to `results/`; manuscript tables and figures are refreshed by the figure builder. Reproduction uses generated data and does not require a broker connection, private records, or a paid inference service.

## Compile the paper

The included tables and figures allow compilation without rerunning the experiments.

**Overleaf:** download the repository as a ZIP and upload it as a new project. Select **`main.tex` at the repository root** as the main document and **pdfLaTeX** as the compiler. `manuscript/preamble.tex` contains shared setup and is not a standalone document.

**Locally:** with Make, `latexmk`, and a LaTeX distribution installed:

```bash
make pdf
make validate
```

The build creates `manuscript.pdf` at the repository root. Without Make, use:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -jobname=manuscript main.tex
python code/validate_release.py
```

Validation checks result structure, summary arithmetic, and PDF identity. The computational checks are distinct from independent scientific peer review.

## Research scope

This public preprint reports controlled simulation experiments and a validation framework. Its numerical findings are conditional on the specified environments and assumptions. It distinguishes forecasting quality, exposure reduction, and market recovery; the manuscript documents the limits of attribution and the further validation required for deployment claims.

The animation includes an attributed EUR/USD market-context panel. That panel is separate from the simulation results. Gyroscope and Fourier-style graphics are illustrative.

## Cite this work

Please cite the manuscript when using the research or accompanying code. See [`CITATION.cff`](./CITATION.cff).

```bibtex
@misc{olapade2026markettransitions,
  author = {Olapade, Timilehin},
  title = {Market Transitions under AI Financial Models: Alpha Decay, Instability, and Evidence-Gated Neuro-Symbolic Adaptation},
  year = {2026},
  note = {Public research edition},
  url = {https://github.com/timi-le/Market-Transitions-under-AI-Financial-Models}
}
```

## License

See the repository's [MIT License](./LICENSE) for terms.
