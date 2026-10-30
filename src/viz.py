"""Shared visual language for the Ridgeline charts.

Design rules (see docs/figures for the result):
  * One accent hue against neutral grays - colour is used to point at the story, not to decorate.
  * Titles state the finding; the subtitle says what is measured and in which unit.
  * Thin marks, rounded data-ends, hairline recessive grid, direct labels instead of legends.
  * Text always wears ink tokens, never the series colour.
Palette values come from a validated set (adjacent CVD / normal-vision / contrast checks pass).
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# ----------------------------------------------------------------------------- tokens
SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e6e5de", "#c3c2b7"
ACCENT, ACCENT_DARK = "#2a78d6", "#184f95"        # series slot 1 (blue)
SECOND = "#eb6834"                                  # series slot 2 (orange), used sparingly
DEEMPH = "#c9c8c0"                                  # de-emphasised context marks
STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SEQ_CMAP = LinearSegmentedColormap.from_list("ridgeline_blue", BLUE_RAMP)

SOURCE = "Source: synthetic data, Ridgeline Infrastructure Co. (fictional company)  ·  github.com/ferserna95/ridgeline-infrastructure-analytics"
FIG_DIR = Path(__file__).resolve().parent.parent / "docs" / "figures"


def _fonts() -> list[str]:
    """First installed family of the preferred UI sans stack."""
    from matplotlib import font_manager
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for fam in ["Inter", "Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"]:
        if fam in installed:
            return [fam]
    return ["sans-serif"]


def setup() -> None:
    plt.rcParams.update({
        "font.family": _fonts(),
        "font.size": 9.5,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "text.color": INK, "axes.labelcolor": INK2,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "xtick.major.size": 0, "ytick.major.size": 0, "xtick.major.pad": 6, "ytick.major.pad": 6,
        "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.7,
        "legend.frameon": False, "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
    })


# ----------------------------------------------------------------------------- figure frame
def new_fig(w, h, title, subtitle=None, nrows=1, ncols=1, *, left=0.55, right=0.3, bottom=0.62,
            wspace=0.28, hspace=0.4, width_ratios=None, height_ratios=None, source=SOURCE):
    """Create a figure with a headline, optional subtitle and source footer; return (fig, gridspec)."""
    fig = plt.figure(figsize=(w, h))
    title = title.replace(" %", "\u00a0%")
    tw = textwrap.fill(title, width=max(20, int(8.4 * (w - 0.6))))
    n_t = tw.count("\n") + 1
    y = 1 - 0.20 / h
    fig.text(0.3 / w, y, tw, fontsize=15, fontweight="semibold", color=INK, va="top", ha="left", linespacing=1.18)
    header = 0.20 + 0.27 * n_t
    if subtitle:
        sw = textwrap.fill(subtitle.replace(" %", "\u00a0%"), width=max(20, int(12.2 * (w - 0.6))))
        n_s = sw.count("\n") + 1
        fig.text(0.3 / w, 1 - (header + 0.05) / h, sw, fontsize=10, color=INK2, va="top", ha="left", linespacing=1.3)
        header += 0.05 + 0.19 * n_s
    header += 0.46
    if source:
        fig.text(0.3 / w, 0.17 / h, source, fontsize=7.3, color=MUTED, va="bottom", ha="left")
    gs = fig.add_gridspec(nrows, ncols, left=left / w, right=1 - right / w, top=1 - header / h,
                          bottom=bottom / h, wspace=wspace, hspace=hspace,
                          width_ratios=width_ratios, height_ratios=height_ratios)
    return fig, gs


def style_axes(ax, *, grid="y", baseline="bottom", panel_title=None):
    """Recessive chrome: hairline grid on one axis, a single baseline, no tick marks."""
    for s in ax.spines.values():
        s.set_visible(False)
    if baseline in ("bottom", "left"):
        ax.spines[baseline].set_visible(True)
        ax.spines[baseline].set_color(AXIS)
        ax.spines[baseline].set_linewidth(0.9)
    ax.grid(False)
    if grid:
        ax.grid(True, axis=grid, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    if panel_title:
        ax.set_title(panel_title, loc="left", fontsize=10, fontweight="semibold", color=INK2, pad=10)
    return ax


# ----------------------------------------------------------------------------- marks
def _px_per_unit(ax, axis):
    bb = ax.get_window_extent()
    lo, hi = (ax.get_xlim() if axis == "x" else ax.get_ylim())
    return (bb.width if axis == "x" else bb.height) / abs(hi - lo)


def bars(ax, pos, values, colors, *, orient="v", thick=18, base=0.0, radius=3.5):
    """Thin bars: small rounded corners at the data end, square at the baseline.

    Geometry is built in pixel space (so corners stay circular whatever the axis scales) and mapped back to data."""
    from matplotlib.patches import Polygon
    fig = ax.figure
    colors = [colors] * len(values) if isinstance(colors, str) else list(colors)
    n = len(values)
    bb = ax.get_window_extent()
    slot_pt = (bb.width if orient == "v" else bb.height) / max(n, 1) * 72 / fig.dpi
    thick_px = min(thick, 0.62 * slot_pt) * fig.dpi / 72
    half = thick_px / 2
    r = min(radius * fig.dpi / 72, half)
    T, Ti = ax.transData, ax.transData.inverted()
    ang = np.linspace(0, np.pi / 2, 10)
    for p, v, c in zip(pos, values, colors):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            continue
        if orient == "v":
            cx, yb = T.transform((p, base)); _, ye = T.transform((p, v))
            sgn = 1 if ye >= yb else -1
            r_ = min(r, abs(ye - yb))
            pts = [(cx - half, yb), (cx - half, ye - sgn * r_)]
            pts += [(cx - half + r_ - r_ * np.cos(a), ye - sgn * r_ + sgn * r_ * np.sin(a)) for a in ang]
            pts += [(cx + half - r_ + r_ * np.sin(a), ye - sgn * r_ + sgn * r_ * np.cos(a)) for a in ang]
            pts += [(cx + half, yb)]
        else:
            xb, cy = T.transform((base, p)); xe, _ = T.transform((v, p))
            sgn = 1 if xe >= xb else -1
            r_ = min(r, abs(xe - xb))
            pts = [(xb, cy + half), (xe - sgn * r_, cy + half)]
            pts += [(xe - sgn * r_ + sgn * r_ * np.sin(a), cy + half - r_ + r_ * np.cos(a)) for a in ang]
            pts += [(xe - sgn * r_ + sgn * r_ * np.cos(a), cy - half + r_ - r_ * np.sin(a)) for a in ang]
            pts += [(xb, cy - half)]
        ax.add_patch(Polygon(Ti.transform(np.array(pts)), closed=True, fc=c, ec="none", zorder=3))
    return thick_px * 72 / fig.dpi


def dot(ax, x, y, color=ACCENT, size=7.5, zorder=6):
    """End-marker with a surface-coloured ring so it stays legible on top of lines."""
    ax.plot([x], [y], marker="o", ms=size, mfc=color, mec=SURFACE, mew=2, ls="none", zorder=zorder, clip_on=False)


def label(ax, x, y, text, *, ha="left", va="center", color=INK, size=9.5, weight="regular", dx=0, dy=0, **kw):
    return ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                       color=color, fontsize=size, fontweight=weight, annotation_clip=False, **kw)


def callout(ax, xy, xytext, text, *, color=INK2, size=9, ha="left", va="center", weight="regular"):
    """Annotation with a thin leader line."""
    return ax.annotate(text, xy=xy, xytext=xytext, ha=ha, va=va, fontsize=size, color=color, fontweight=weight,
                       arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=2, shrinkB=3),
                       annotation_clip=False)


def hline(ax, y, text=None, *, color=INK, lw=1.0, ls="-", x_text=None, ha="left", size=8.8, dy=6, zorder=2):
    ax.axhline(y, color=color, lw=lw, ls=ls, zorder=zorder)
    if text:
        xl = ax.get_xlim()
        ax.annotate(text, (x_text if x_text is not None else xl[0], y), xytext=(0, dy), textcoords="offset points",
                    ha=ha, va="bottom", fontsize=size, color=INK2, annotation_clip=False,
                    bbox=dict(boxstyle="round,pad=0.18", fc=SURFACE, ec="none"), zorder=zorder + 3)


def legend_keys(ax, items, *, loc=(0.0, 1.0), dy=0.0, gap=0.0, size=9):
    """Compact swatch legend placed above the plot (items: [(label, color)])."""
    x = loc[0]
    fig = ax.figure
    for text, color in items:
        ax.plot([x], [loc[1] + dy], marker="s", ms=7, mfc=color, mec=color, ls="none", transform=ax.transAxes, clip_on=False)
        t = ax.text(x + 0.015, loc[1] + dy, text, transform=ax.transAxes, va="center", fontsize=size, color=INK2)
        fig.canvas.draw()
        bb = t.get_window_extent().transformed(ax.transAxes.inverted())
        x = bb.x1 + 0.04 + gap


def save(fig, name, dpi=200):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"{name}.png", dpi=dpi, facecolor=SURFACE)
