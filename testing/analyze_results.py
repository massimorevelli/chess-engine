import os
import pandas as pd
import matplotlib.pyplot as plt


TESTING_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(TESTING_DIR, "results")
FIGURES_DIR = os.path.join(TESTING_DIR, "figures")

os.makedirs(FIGURES_DIR, exist_ok=True)

df = pd.read_csv(os.path.join(RESULTS_DIR, "max_move_stats.csv"))


# ------------------------------------------------------------
# Figure 1: completed-depth distribution
# ------------------------------------------------------------

depth_counts = df["depth"].value_counts().sort_index()
depth_pct = 100 * depth_counts / depth_counts.sum()

fig, ax = plt.subplots(figsize=(7.2, 4.3))

bars = ax.barh(
    depth_counts.index,
    depth_counts.values,
    height=0.62,
    color="black"
)

for bar, count, pct in zip(bars, depth_counts.values, depth_pct.values):
    ax.text(
        bar.get_width() + 5,
        bar.get_y() + bar.get_height() / 2,
        f"{count}  ({pct:.1f}%)",
        va="center",
        ha="left",
        fontsize=9.5
    )


ax.set_xlabel("Number of engine moves")
ax.set_ylabel("Completed search depth")

ax.set_yticks(depth_counts.index)

ax.set_xlim(0, depth_counts.max() * 1.28)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

ax.tick_params(axis="y", length=0)

ax.xaxis.grid(
    True,
    linestyle="--",
    linewidth=0.5,
    alpha=0.25
)
ax.set_axisbelow(True)

fig.tight_layout()

fig.savefig(
    os.path.join(FIGURES_DIR, "depth_distribution.pdf"),
    bbox_inches="tight"
)

fig.savefig(
    os.path.join(FIGURES_DIR, "depth_distribution.png"),
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)


# ------------------------------------------------------------
# Figure 2: average completed depth by pieces remaining
# ------------------------------------------------------------

def count_pieces(fen):
    board_part = fen.split()[0]
    return sum(1 for char in board_part if char.isalpha())

df["pieces_remaining"] = df["fen_before"].apply(count_pieces)

bins = [0, 10, 16, 24, 32]
labels = ["≤ 10", "11–16", "17–24", "25–32"]

df["piece_group"] = pd.cut(
    df["pieces_remaining"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

depth_by_material = (
    df.groupby("piece_group", observed=True)["depth"]
      .agg(["mean", "count"])
      .reindex(labels)
)

fig, ax = plt.subplots(figsize=(7.2, 3.2))

bars = ax.barh(
    depth_by_material.index,
    depth_by_material["mean"],
    height=0.42,
    color="black"
)

for bar, mean_depth, count in zip(
    bars,
    depth_by_material["mean"],
    depth_by_material["count"]
):
    ax.text(
        bar.get_width() + 0.08,
        bar.get_y() + bar.get_height() / 2,
        f"{mean_depth:.2f}   (n={count})",
        va="center",
        ha="left",
        fontsize=9.5
    )

ax.set_xlabel("Average completed search depth")
ax.set_ylabel("Pieces remaining")

ax.set_xlim(0, depth_by_material["mean"].max() * 1.28)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

ax.tick_params(axis="y", length=0)

ax.xaxis.grid(
    True,
    linestyle="--",
    linewidth=0.5,
    alpha=0.25
)
ax.set_axisbelow(True)

fig.tight_layout()

fig.savefig(
    os.path.join(FIGURES_DIR, "depth_by_material.pdf"),
    bbox_inches="tight"
)

fig.savefig(
    os.path.join(FIGURES_DIR, "depth_by_material.png"),
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)