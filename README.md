# rc3c-prisoners-dilemma
Chaotic Three-Body Retaliation strategy for the Iterated Prisoner's Dilemma
# Chaotic Three-Body Retaliation in the Iterated Prisoner's Dilemma

**A Strategy Grounded in Deterministic Chaos and Dual-Process Cognition**

[![SSRN](https://img.shields.io/badge/SSRN-6752538-blue)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6752538)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-yellow)](https://www.python.org/)

---

## Overview

This repository contains the complete simulation code, experimental results, and publication figures for the paper:

> **Sereno, F.C. (2026).** *Chaotic Three-Body Retaliation in the Iterated Prisoner's Dilemma: A Strategy Grounded in Deterministic Chaos and Dual-Process Cognition.* SSRN Preprint. https://doi.org/10.2139/ssrn.6752538

The paper proposes and analyzes **RC3C** (*Retaliação Caótica de Três Corpos* / Chaotic Three-Body Retaliation), a novel strategy for the Iterated Prisoner's Dilemma (IPD) that models the dynamic transition between deliberative and automatic cognition described by Kahneman (2011), mediated by the neuro-behavioral sensitization documented by Sapolsky (2017), and implemented through the structural unpredictability identified by Lorenz (1963) and Poincaré (1890) in deterministic non-linear systems.

---

## The RC3C Strategy

RC3C operates across three temporal layers:

| Layer | Mechanism | Cognitive analog |
|---|---|---|
| 1 — Initial posture | Unconditional cooperation until first defection | System 2 (deliberative) |
| 2 — Structured memory | Retaliation probability p(k) = 1 − e^(−λk) | System 1/2 transition |
| 3 — Chaotic realization | Three-body gravitational system with external entropy | System 1 (automatic) |

The parameter **λ** controls the speed of sensitization — the rate at which accumulated defections transfer behavioral control from deliberative to automatic processing.

```
p(k) = 1 − e^(−λ·k)

k = number of defections suffered
λ = sensitization coefficient (0.5 = mild · 1.0 = standard · 2.0 = aggressive)
```

---

## Tournament Results

Round-robin tournament · 50 repetitions · 200 rounds per match · seed = 42

| Rank | Strategy | Mean/round | ±SD | 95% CI |
|---|---|---|---|---|
| 1 | Tit-for-Tat | 2.7772 | 0.0000 | [2.7772, 2.7772] |
| 2 | Grudger | 2.7772 | 0.0000 | [2.7772, 2.7772] |
| **3** | **RC3C-Aggressive (λ=2.0)** | **2.7769** | **0.0004** | **[2.7768, 2.7770]** |
| 4 | Tit-for-Two-Tats | 2.7767 | 0.0000 | [2.7767, 2.7767] |
| **5** | **RC3C-Standard (λ=1.0)** | **2.7765** | **0.0005** | **[2.7763, 2.7766]** |
| **6** | **RC3C-Mild (λ=0.5)** | **2.7753** | **0.0007** | **[2.7751, 2.7756]** |
| 7 | Generous TFT | 2.7663 | 0.0022 | [2.7657, 2.7669] |
| 8 | Pavlov | 2.7222 | 0.0000 | [2.7222, 2.7222] |
| 9 | Always Cooperate | 2.6667 | 0.0000 | [2.6667, 2.6667] |
| 10 | Always Defect | 1.7402 | 0.0096 | [1.7375, 1.7428] |

---

## Repository Structure

```
rc3c-prisoners-dilemma/
│
├── torneioRC3C.py          # Full simulation script (Python)
│
├── results/
│   ├── ranking_final.csv           # Mean ± SD and 95% CI per strategy
│   ├── resultados_brutos.csv       # Raw scores across all 50 repetitions
│   ├── confrontos_matriz.csv       # Head-to-head match results
│   └── tabela2_pk.csv              # p(k) values for λ ∈ {0.3, 0.5, 1.0, 1.5, 2.0}
│
└── figures/
    ├── fig1_curva_pk.png           # Figure 1: exponential escalation curves
    ├── fig2_ranking.png            # Figure 2: tournament ranking with 95% CI
    └── fig3_heatmap.png            # Figure 3: head-to-head match matrix
```

---

## Reproducing the Experiment

### Requirements

```bash
pip install matplotlib numpy scipy
```

### Run

```bash
python torneioRC3C.py
```

This will reproduce all results, figures, and CSV files in `results/` and `figures/`. The simulation uses `seed = 42` for reproducibility of stochastic strategies. RC3C's chaotic generator uses real-time system entropy (`time.time_ns()`, `time.perf_counter()`, SHA-256) — minor numerical variations across machines and runs are expected and intentional, as they reflect the strategy's structural unpredictability.

### Expected runtime

Approximately 2–5 minutes on a standard desktop (10 strategies × 45 pairs × 50 repetitions × 200 rounds).

---

## Theoretical Background

RC3C draws from three scientific traditions:

**Kahneman (2011) — Dual-process cognition**
The strategy models the transition between System 2 (slow, deliberative) and System 1 (fast, automatic) as defections accumulate. The parameter λ is the formal coefficient of this transfer.

**Sapolsky (2017, 2023) — Behavioral neurobiology**
Repeated social stressors produce progressive sensitization of stress-response circuits — a non-linear escalation that p(k) = 1 − e^(−λk) captures mathematically.

**Lorenz (1963) / Poincaré (1890) — Deterministic chaos**
The Three-Body Problem is non-integrable: deterministic but operationally unpredictable. RC3C's chaotic generator uses this structure to produce responses that are causally determined but inaccessible to adversarial prediction.

---

## Citation

If you use this code or build on this work, please cite:

```bibtex
@techreport{sereno2026rc3c,
  author      = {Sereno, Fabio da Costa},
  title       = {Chaotic Three-Body Retaliation in the Iterated Prisoner's Dilemma:
                 A Strategy Grounded in Deterministic Chaos and Dual-Process Cognition},
  institution = {SSRN},
  year        = {2026},
  type        = {Preprint},
  number      = {6752538},
  url         = {https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6752538}
}
```

---

## Author

**Fábio da Costa Sereno**
Independent Researcher, Nova Friburgo, RJ, Brazil
fcsereno@gmail.com
ORCID: [0009-0002-0175-3963](https://orcid.org/0009-0002-0175-3963)

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## AI Disclosure

The author used Claude (Anthropic), accessed via claude.ai, to assist with the following tasks: development and validation of the Python simulation code and JavaScript interactive interface; structuring and drafting of the academic manuscript; and final document formatting. The original idea for the RC3C strategy, the intellectual motivation, the experimental design, all content decisions, and the final review of the manuscript are solely the author's responsibility.
