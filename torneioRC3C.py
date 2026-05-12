"""
═══════════════════════════════════════════════════════════════════════
EXPERIMENTO COMPLETO — RC3C vs Estratégias Clássicas
Retaliação Caótica de Três Corpos no Dilema dos Prisioneiros Iterado

Fabio da Costa Sereno
Independent Researcher, Nova Friburgo, RJ, Brazil
fcsereno@gmail.com
https://orcid.org/0009-0002-0175-3963
Script : torneioRC3C.py

Saídas geradas:
  results/resultados_brutos.csv   — todas as repetições por par
  results/ranking_final.csv       — média ± dp por estratégia
  results/confrontos_matriz.csv   — matriz de pontos par a par
  figures/fig1_curva_pk.png       — Figura 1: curva p(k) por λ
  figures/fig2_ranking.png        — Figura 2: ranking do torneio
  figures/fig3_heatmap.png        — Figura 3: heatmap de confrontos
  results/tabela2_pk.csv          — Tabela 2: valores p(k) formatados

Parâmetros do experimento:
  N_RODADAS    = 200   (rodadas por confronto — padrão Axelrod 1984)
  N_REPETICOES = 50    (repetições por par — controle de variância)
  SEMENTE_BASE = 42    (reprodutibilidade das estratégias estocásticas)
═══════════════════════════════════════════════════════════════════════
"""

import csv
import math
import time
import hashlib
import random
import os
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from itertools import combinations
from collections import defaultdict

# ── Diretório de saída ──────────────────────────────────────────────
os.makedirs("results", exist_ok=True)
os.makedirs("figures", exist_ok=True)

# ── Semente global para reprodutibilidade ──────────────────────────
SEMENTE_BASE = 42
N_RODADAS = 200
N_REPETICOES = 50

# ── Estilo visual (publicação) ──────────────────────────────────────
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.dpi": 300,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    }
)

CORES = {
    "Sempre Coopera": "#6b7280",
    "Sempre Trai": "#ef4444",
    "Tit-for-Tat": "#3b82f6",
    "Tit-for-Two-Tats": "#8b5cf6",
    "Grudger": "#f59e0b",
    "Pavlov": "#06b6d4",
    "TFT Generoso": "#10b981",
    "RC3C-Suave": "#f97316",
    "RC3C-Padrão": "#ec4899",
    "RC3C-Agressiva": "#dc2626",
}

# ══════════════════════════════════════════════════════════════════════
# BLOCO 1 — PAYOFFS
# ══════════════════════════════════════════════════════════════════════

PAYOFFS = {
    ("C", "C"): (3, 3),
    ("C", "D"): (0, 5),
    ("D", "C"): (5, 0),
    ("D", "D"): (1, 1),
}

# ══════════════════════════════════════════════════════════════════════
# BLOCO 2 — GERADOR CAÓTICO DE TRÊS CORPOS
# ══════════════════════════════════════════════════════════════════════


def _tres_corpos_passo(pos, vel, G=6.674e-11, dt=0.01):
    """
    Um passo de integração gravitacional (Euler simplético).
    Massas: m1=1.0, m2=φ≈1.618, m3=e≈2.718
    """
    massas = [1.0, 1.6180339887, 2.7182818284]
    n = 3
    acels = [(0.0, 0.0)] * n

    for i in range(n):
        ax, ay = 0.0, 0.0
        for j in range(n):
            if i == j:
                continue
            dx = pos[j][0] - pos[i][0]
            dy = pos[j][1] - pos[i][1]
            dist = math.sqrt(dx**2 + dy**2) + 1e-9
            forca = G * massas[i] * massas[j] / dist**2
            ax += forca * dx / dist / massas[i]
            ay += forca * dy / dist / massas[i]
        acels[i] = (ax, ay)

    pos_novo, vel_novo = [], []
    for i in range(n):
        vx = vel[i][0] + acels[i][0] * dt
        vy = vel[i][1] + acels[i][1] * dt
        pos_novo.append((pos[i][0] + vx * dt, pos[i][1] + vy * dt))
        vel_novo.append((vx, vy))

    return pos_novo, vel_novo


def gerar_numero_caotico(semente_extra: int = 0) -> float:
    """
    Gera ξ ∈ [0,1) usando entropia externa como condições iniciais
    do sistema de três corpos.
    """
    N_STEPS = 8

    t_ns = time.time_ns()
    t_perf = time.perf_counter()
    h_bytes = hashlib.sha256(f"{t_ns}{t_perf}{semente_extra}".encode()).digest()

    h1 = int.from_bytes(h_bytes[0:4], "big") / 0xFFFFFFFF
    h2 = int.from_bytes(h_bytes[4:8], "big") / 0xFFFFFFFF

    escala = 1e-3
    pos = [
        ((t_ns % 1_000_000) * escala, (t_ns % 999_983) * escala),
        ((h1 * 500) * escala, (h2 * 500) * escala),
        ((t_perf % 1000) * escala, (semente_extra % 997) * escala),
    ]
    vel = [
        (h1 * 0.1, h2 * 0.1),
        (t_perf % 1 * 0.05, h1 * 0.05),
        (h2 * 0.08, (t_ns % 100) * 1e-5),
    ]

    for _ in range(N_STEPS):
        pos, vel = _tres_corpos_passo(pos, vel)

    valor = pos[0][0] + pos[1][1] - pos[2][0]
    return abs(math.sin(valor * 1e6)) % 1.0


# ══════════════════════════════════════════════════════════════════════
# BLOCO 3 — ESTRATÉGIAS
# ══════════════════════════════════════════════════════════════════════


class Estrategia:
    def __init__(self, nome):
        self.nome = nome

    def jogada(self, hp, ha, rodada):
        raise NotImplementedError

    def reset(self):
        pass


class SempreCoopera(Estrategia):
    def __init__(self):
        super().__init__("Sempre Coopera")

    def jogada(self, hp, ha, r):
        return "C"


class SempreTrai(Estrategia):
    def __init__(self):
        super().__init__("Sempre Trai")

    def jogada(self, hp, ha, r):
        return "D"


class TitForTat(Estrategia):
    def __init__(self):
        super().__init__("Tit-for-Tat")

    def jogada(self, hp, ha, r):
        return "C" if r == 0 else ha[r - 1]


class TitForTwoTats(Estrategia):
    def __init__(self):
        super().__init__("Tit-for-Two-Tats")

    def jogada(self, hp, ha, r):
        if r < 2:
            return "C"
        return "D" if ha[r - 1] == "D" and ha[r - 2] == "D" else "C"


class Grudger(Estrategia):
    def __init__(self):
        super().__init__("Grudger")

    def jogada(self, hp, ha, r):
        return "D" if "D" in ha else "C"


class Pavlov(Estrategia):
    def __init__(self):
        super().__init__("Pavlov")

    def jogada(self, hp, ha, r):
        if r == 0:
            return "C"
        g, _ = PAYOFFS[(hp[r - 1], ha[r - 1])]
        if g >= 3:
            return hp[r - 1]
        return "D" if hp[r - 1] == "C" else "C"


class TFTGeneroso(Estrategia):
    def __init__(self, rng):
        super().__init__("TFT Generoso")
        self.rng = rng

    def jogada(self, hp, ha, r):
        if r == 0:
            return "C"
        if ha[r - 1] == "D" and self.rng.random() < 0.1:
            return "C"
        return ha[r - 1]


class RC3C(Estrategia):
    """
    Retaliação Caótica de Três Corpos.
    lambda_ controla a velocidade de sensibilização.
    """

    def __init__(self, lambda_: float, nome: str):
        super().__init__(nome)
        self.lambda_ = lambda_
        self._traicoes = 0

    def reset(self):
        self._traicoes = 0

    def jogada(self, hp, ha, r):
        if r > 0 and ha[r - 1] == "D":
            self._traicoes += 1

        k = self._traicoes
        if k == 0:
            return "C"

        p = 1.0 - math.exp(-self.lambda_ * k)
        xi = gerar_numero_caotico(semente_extra=r * k + k)
        return "D" if xi < p else "C"


# ══════════════════════════════════════════════════════════════════════
# BLOCO 4 — MOTOR DO TORNEIO
# ══════════════════════════════════════════════════════════════════════


def confronto(est_a, est_b, n_rodadas):
    """Executa um confronto completo entre duas estratégias."""
    est_a.reset()
    est_b.reset()
    hp_a, hp_b = [], []
    pts_a = pts_b = 0

    for r in range(n_rodadas):
        ja = est_a.jogada(hp_a[:], hp_b[:], r)
        jb = est_b.jogada(hp_b[:], hp_a[:], r)
        pa, pb = PAYOFFS[(ja, jb)]
        pts_a += pa
        pts_b += pb
        hp_a.append(ja)
        hp_b.append(jb)

    return pts_a, pts_b


def criar_estrategias(semente):
    """Cria instâncias frescas com RNG controlado."""
    rng = random.Random(semente)
    return [
        SempreCoopera(),
        SempreTrai(),
        TitForTat(),
        TitForTwoTats(),
        Grudger(),
        Pavlov(),
        TFTGeneroso(rng),
        RC3C(lambda_=0.5, nome="RC3C-Suave"),
        RC3C(lambda_=1.0, nome="RC3C-Padrão"),
        RC3C(lambda_=2.0, nome="RC3C-Agressiva"),
    ]


def executar_experimento():
    """
    Executa N_REPETICOES torneios completos.
    Retorna dicionários com pontuações brutas e matriz de confrontos.
    """
    nomes = [e.nome for e in criar_estrategias(0)]
    n = len(nomes)
    pares = list(combinations(range(n), 2))

    # Armazena pontos por repetição: {nome: [rep0, rep1, ...]}
    pontos_por_rep = {nome: [] for nome in nomes}

    # Matriz de confrontos: {(nome_a, nome_b): [pts_a_rep0, ...]}
    confronto_pts = {(nomes[i], nomes[j]): [] for i, j in pares}

    print(
        f"Executando {N_REPETICOES} repetições × "
        f"{len(pares)} pares × {N_RODADAS} rodadas"
    )
    print(f"Total de confrontos: {N_REPETICOES * len(pares)}\n")

    for rep in range(N_REPETICOES):
        estrategias = criar_estrategias(SEMENTE_BASE + rep)
        placar_rep = {e.nome: 0 for e in estrategias}

        for i, j in pares:
            ea = estrategias[i]
            eb = estrategias[j]
            pa, pb = confronto(ea, eb, N_RODADAS)
            placar_rep[ea.nome] += pa
            placar_rep[eb.nome] += pb
            confronto_pts[(ea.nome, eb.nome)].append((pa, pb))

        for nome in nomes:
            pontos_por_rep[nome].append(placar_rep[nome])

        if (rep + 1) % 10 == 0:
            print(f"  Repetição {rep+1:>3}/{N_REPETICOES} concluída")

    return nomes, pontos_por_rep, confronto_pts, pares


# ══════════════════════════════════════════════════════════════════════
# BLOCO 5 — EXPORTAÇÃO DE DADOS
# ══════════════════════════════════════════════════════════════════════


def exportar_resultados_brutos(nomes, pontos_por_rep):
    """Exporta CSV com pontos por repetição."""
    path = "results/resultados_brutos.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["repeticao"] + nomes)
        for rep in range(N_REPETICOES):
            w.writerow([rep + 1] + [pontos_por_rep[n][rep] for n in nomes])
    print(f"[CSV] {path}")


def exportar_ranking(nomes, pontos_por_rep):
    """Exporta CSV com média ± dp e ranking."""
    rodadas_totais = (len(nomes) - 1) * N_RODADAS

    stats = {}
    for nome in nomes:
        arr = np.array(pontos_por_rep[nome])
        media_pts = arr.mean()
        dp_pts = arr.std(ddof=1)
        media_rod = media_pts / rodadas_totais
        dp_rod = dp_pts / rodadas_totais
        stats[nome] = {
            "media_pts": media_pts,
            "dp_pts": dp_pts,
            "media_rod": media_rod,
            "dp_rod": dp_rod,
            "ic95_low": media_rod - 1.96 * dp_rod / math.sqrt(N_REPETICOES),
            "ic95_high": media_rod + 1.96 * dp_rod / math.sqrt(N_REPETICOES),
        }

    ranking = sorted(stats.items(), key=lambda x: x[1]["media_pts"], reverse=True)

    path = "results/ranking_final.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "posicao",
                "estrategia",
                "media_pontos",
                "dp_pontos",
                "media_por_rodada",
                "dp_por_rodada",
                "ic95_low",
                "ic95_high",
            ]
        )
        for pos, (nome, s) in enumerate(ranking, 1):
            w.writerow(
                [
                    pos,
                    nome,
                    f"{s['media_pts']:.2f}",
                    f"{s['dp_pts']:.2f}",
                    f"{s['media_rod']:.4f}",
                    f"{s['dp_rod']:.4f}",
                    f"{s['ic95_low']:.4f}",
                    f"{s['ic95_high']:.4f}",
                ]
            )

    print(f"[CSV] {path}")
    return ranking, stats


def exportar_matriz_confrontos(nomes, confronto_pts, pares):
    """Exporta CSV com média de pontos em cada par de confronto."""
    path = "results/confrontos_matriz.csv"
    medias = {}
    for (na, nb), lista in confronto_pts.items():
        pts_a = np.mean([x[0] for x in lista])
        pts_b = np.mean([x[1] for x in lista])
        medias[(na, nb)] = (pts_a, pts_b)

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            ["estrategia_a", "estrategia_b", "media_pts_a", "media_pts_b", "resultado"]
        )
        for (na, nb), (pa, pb) in sorted(medias.items()):
            if pa > pb:
                res = f"{na} vence"
            elif pa < pb:
                res = f"{nb} vence"
            else:
                res = "empate"
            w.writerow([na, nb, f"{pa:.1f}", f"{pb:.1f}", res])
    print(f"[CSV] {path}")
    return medias


def exportar_tabela_pk():
    """Exporta Tabela 2: p(k) para diferentes λ e k."""
    lambdas = [0.3, 0.5, 1.0, 1.5, 2.0]
    path = "results/tabela2_pk.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["k"] + [f"lambda={l}" for l in lambdas])
        for k in range(1, 9):
            w.writerow([k] + [f"{1 - math.exp(-l*k):.4f}" for l in lambdas])
    print(f"[CSV] {path}")


# ══════════════════════════════════════════════════════════════════════
# BLOCO 6 — FIGURAS
# ══════════════════════════════════════════════════════════════════════


def figura1_curva_pk():
    """
    Figura 1 — Curva p(k) = 1 − e^(−λ·k) para λ = 0.5, 1.0, 2.0.
    Mostra a escalada exponencial da probabilidade de retaliação.
    """
    fig, ax = plt.subplots(figsize=(5.5, 3.8))

    k_vals = np.linspace(0, 7, 300)
    configs = [
        (0.5, "#f97316", "λ = 0.5 (RC3C-Suave)", "--"),
        (1.0, "#ec4899", "λ = 1.0 (RC3C-Padrão)", "-"),
        (2.0, "#dc2626", "λ = 2.0 (RC3C-Agressiva)", "-."),
    ]

    for lam, cor, label, ls in configs:
        y = 1 - np.exp(-lam * k_vals)
        ax.plot(k_vals, y, color=cor, lw=2, linestyle=ls, label=label)

    # Marca os pontos inteiros
    for lam, cor, _, _ in configs:
        for k in range(1, 8):
            p = 1 - math.exp(-lam * k)
            ax.scatter(k, p, color=cor, s=30, zorder=5)

    # Linhas de referência
    ax.axhline(0.5, color="gray", lw=0.8, ls=":", alpha=0.6, label="p = 0.5")
    ax.axhline(0.95, color="gray", lw=0.8, ls=":", alpha=0.4, label="p = 0.95")

    ax.set_xlabel("k  (número acumulado de traições sofridas)")
    ax.set_ylabel("p(k)  (probabilidade de retaliar)")
    ax.set_title(
        "Figura 1 — Escalada exponencial da probabilidade de retaliação\n"
        r"$p(k) = 1 - e^{-\lambda k}$",
        pad=10,
    )
    ax.set_xlim(0, 7.2)
    ax.set_ylim(0, 1.05)
    ax.set_xticks(range(0, 8))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
    ax.legend(framealpha=0.9, loc="lower right")

    fig.tight_layout()
    path = "figures/fig1_curva_pk.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] {path}")


def figura2_ranking(ranking, stats):
    """
    Figura 2 — Ranking do torneio com média e IC 95%.
    Barras horizontais ordenadas por pontuação.
    """
    nomes_ord = [n for n, _ in ranking]
    medias = [stats[n]["media_rod"] for n in nomes_ord]
    erros = [1.96 * stats[n]["dp_rod"] / math.sqrt(N_REPETICOES) for n in nomes_ord]
    cores = [CORES.get(n, "#94a3b8") for n in nomes_ord]

    fig, ax = plt.subplots(figsize=(7, 5))

    y_pos = range(len(nomes_ord))
    bars = ax.barh(
        y_pos,
        medias,
        xerr=erros,
        color=cores,
        edgecolor="white",
        linewidth=0.5,
        error_kw=dict(ecolor="#374151", capsize=3, elinewidth=1),
        height=0.65,
    )

    # Valores no final de cada barra
    for i, (m, e) in enumerate(zip(medias, erros)):
        ax.text(
            m + e + 0.005,
            i,
            f"{m:.4f}",
            va="center",
            ha="left",
            fontsize=8,
            color="#374151",
        )

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(nomes_ord)
    ax.invert_yaxis()
    ax.set_xlabel("Pontuação média por rodada  (± IC 95%)")
    ax.set_title(
        f"Figura 2 — Ranking do torneio\n"
        f"({N_REPETICOES} repetições × {N_RODADAS} rodadas por confronto, "
        f"round-robin completo)",
        pad=10,
    )
    ax.set_xlim(left=min(medias) * 0.97, right=max(medias) + max(erros) * 6)

    # Destaque RC3C
    for i, nome in enumerate(nomes_ord):
        if "RC3C" in nome:
            ax.get_yticklabels()[i].set_fontweight("bold")
            ax.get_yticklabels()[i].set_color("#dc2626")

    fig.tight_layout()
    path = "figures/fig2_ranking.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] {path}")


def figura3_heatmap(nomes, confronto_pts):
    """
    Figura 3 — Heatmap de resultado por confronto.
    Cada célula mostra a diferença média de pontos (A − B).
    Verde = A vence, vermelho = A perde.
    """
    n = len(nomes)
    matriz = np.full((n, n), np.nan)

    for (na, nb), lista in confronto_pts.items():
        i = nomes.index(na)
        j = nomes.index(nb)
        diff = np.mean([x[0] - x[1] for x in lista])
        matriz[i, j] = diff
        matriz[j, i] = -diff

    fig, ax = plt.subplots(figsize=(8, 6.5))

    absmax = np.nanmax(np.abs(matriz))
    im = ax.imshow(matriz, cmap="RdYlGn", vmin=-absmax, vmax=absmax, aspect="auto")

    # Anotações
    for i in range(n):
        for j in range(n):
            if not np.isnan(matriz[i, j]):
                val = matriz[i, j]
                cor = "white" if abs(val) > absmax * 0.6 else "black"
                ax.text(
                    j,
                    i,
                    f"{val:+.0f}",
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    color=cor,
                    fontweight="bold",
                )

    nomes_curtos = [
        n.replace("Tit-for-", "TfT-")
        .replace("Sempre ", "S.")
        .replace("Generoso", "Gen.")
        for n in nomes
    ]

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(nomes_curtos, rotation=40, ha="right", fontsize=8)
    ax.set_yticklabels(nomes_curtos, fontsize=8)

    cbar = fig.colorbar(im, ax=ax, shrink=0.75)
    cbar.set_label("Diferença média de pontos (linha − coluna)", fontsize=9)

    ax.set_title(
        "Figura 3 — Matriz de confrontos\n"
        "Diferença média de pontos por par (positivo = linha vence)",
        pad=10,
    )

    # Destaque RC3C (linhas/colunas)
    for i, nome in enumerate(nomes):
        if "RC3C" in nome:
            for spine in ["bottom", "top", "left", "right"]:
                pass
            ax.add_patch(
                plt.Rectangle(
                    (-0.5, i - 0.5),
                    n,
                    1,
                    fill=False,
                    edgecolor="#dc2626",
                    linewidth=1.5,
                    clip_on=False,
                )
            )

    fig.tight_layout()
    path = "figures/fig3_heatmap.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] {path}")


# ══════════════════════════════════════════════════════════════════════
# BLOCO 7 — RELATÓRIO DE CONSOLE
# ══════════════════════════════════════════════════════════════════════


def imprimir_relatorio(ranking, stats):
    rodadas_totais = (len(stats) - 1) * N_RODADAS

    print("\n" + "═" * 72)
    print("  RESULTADO FINAL DO TORNEIO RC3C")
    print(
        f"  {N_REPETICOES} repetições · {N_RODADAS} rodadas/confronto · "
        f"round-robin completo"
    )
    print("═" * 72)
    print(
        f"  {'#':<4} {'Estratégia':<24} "
        f"{'Média/rod':>10} {'±DP':>8} {'IC95 low':>10} {'IC95 high':>10}"
    )
    print("─" * 72)

    for pos, (nome, s) in enumerate(ranking, 1):
        rc = " ◄" if "RC3C" in nome else ""
        print(
            f"  {pos:<4} {nome:<24} "
            f"{s['media_rod']:>10.4f} "
            f"{s['dp_rod']:>8.4f} "
            f"{s['ic95_low']:>10.4f} "
            f"{s['ic95_high']:>10.4f}{rc}"
        )

    print("═" * 72)


# ══════════════════════════════════════════════════════════════════════
# BLOCO 8 — EXECUÇÃO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  EXPERIMENTO RC3C — Dilema dos Prisioneiros Iterado      ║")
    print("║  Sereno (2026) · reprodutível · semente =", SEMENTE_BASE, "          ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # ── Figura 1 e Tabela 2 (independem do torneio) ────────────────
    figura1_curva_pk()
    exportar_tabela_pk()
    print()

    # ── Execução do torneio ────────────────────────────────────────
    nomes, pontos_por_rep, confronto_pts, pares = executar_experimento()

    # ── Exportação de dados ────────────────────────────────────────
    print()
    exportar_resultados_brutos(nomes, pontos_por_rep)
    ranking, stats = exportar_ranking(nomes, pontos_por_rep)
    exportar_matriz_confrontos(nomes, confronto_pts, pares)

    # ── Figuras 2 e 3 ─────────────────────────────────────────────
    figura2_ranking(ranking, stats)
    figura3_heatmap(nomes, confronto_pts)

    # ── Relatório de console ───────────────────────────────────────
    imprimir_relatorio(ranking, stats)

    print("\nSaídas salvas em ./results/ e ./figures/")
    print("Arquivos gerados:")
    for folder in ["results", "figures"]:
        for f in sorted(os.listdir(folder)):
            size = os.path.getsize(f"{folder}/{f}")
            print(f"  {folder}/{f:<36} {size:>8,} bytes")
