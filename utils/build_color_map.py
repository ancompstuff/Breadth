from __future__ import annotations

from itertools import combinations
from colorsys import hsv_to_rgb


ma_groups = {
    "short":  {"periods": [5, 12, 25],    "color": "red",         "port": "curtas"},
    "medium": {"periods": [40, 60, 80],   "color": "springgreen", "port": "médias"},
    "long":   {"periods": [50, 100, 200], "color": "darkblue",    "port": "longas"},
}

mas_list = sorted({ma for g in ma_groups.values() for ma in g["periods"]})
# [5, 12, 25, 40, 50, 60, 80, 100, 200]


def _rgb_hex(r: float, g: float, b: float) -> str:
    return f"#{int(round(r*255)):02x}{int(round(g*255)):02x}{int(round(b*255)):02x}"


def _hsv_palette(n: int, h0: float, h1: float, s: float, v: float) -> list[str]:
    """
    Create n distinct-ish colors by spacing hues between [h0,h1] (inclusive-ish),
    returning hex strings.
    """
    if n <= 0:
        return []
    if n == 1:
        r, g, b = hsv_to_rgb((h0 + h1) / 2, s, v)
        return [_rgb_hex(r, g, b)]
    out = []
    for i in range(n):
        h = h0 + (h1 - h0) * (i / (n - 1))
        r, g, b = hsv_to_rgb(h % 1.0, s, v)
        out.append(_rgb_hex(r, g, b))
    return out


def build_mka_color_map(
    ma_groups: dict,
    mas_list: list[int],
    *,
    include_all_pairwise_and_triplets: bool = True,
) -> dict[str, str]:
    """
    Builds a color map with:
      - Single MA/VWMA metrics (12 * len(mas_list) keys)
      - Composite MA/VWMA group metrics:
          If include_all_pairwise_and_triplets=True:
            For each group periods:
              all 2-combos and 3-combo (if exists) for MA and VWMA
              for each combo: Nº> , Nº< , %> , %<  => 4 metrics
              total composites = sum_over_groups((C(n,2)+C(n,3)) * 2 * 4)
              with n=3 per group => (3+1)*2*4=32 per group => 96 total
          If False:
            only the user-listed composites (pair and full-triplet) for MA+VWMA and Nº/% and >/<
            total composites = 48.

    Note on counts:
      - Your “108 single MA + 48 composites = 156” doesn’t match the 12 categories
        you listed for singles (that’s 12*9=108) BUT your composites list includes
        some extra %<VWMA-only items and misses the symmetrical ones. This function can
        generate a complete, consistent set.
    """
    # ---- 1) Period -> group + index (to map each MA to the right family palette)
    period_to_group = {}
    for group_name, gd in ma_groups.items():
        for p in gd["periods"]:
            period_to_group[p] = group_name

    # ---- 2) Define palettes per group so colors don't repeat in "similar groups"
    # We create distinct hue ranges per group, then within each group vary the hue slightly
    # across its periods.
    group_hue_ranges = {
        "short":  (0.98, 0.05),   # wraps around red-ish
        "medium": (0.28, 0.40),   # green-ish
        "long":   (0.58, 0.70),   # blue-ish
    }

    # Build per-period base colors
    period_base_color: dict[int, str] = {}
    for group_name, gd in ma_groups.items():
        periods = sorted(gd["periods"])
        h0, h1 = group_hue_ranges.get(group_name, (0.0, 0.9))
        # handle wrap-around for short reds: if h1 < h0, spread across boundary
        if h1 < h0:
            # make hues go from h0..1 then 0..h1
            # approximate by mapping evenly then mod 1.0
            hues = [((h0 + (i / max(1, len(periods) - 1)) * ((1 - h0) + h1)) % 1.0)
                    for i in range(len(periods))]
            cols = []
            for h in hues:
                r, g, b = hsv_to_rgb(h, 0.80, 0.85)
                cols.append(_rgb_hex(r, g, b))
        else:
            cols = _hsv_palette(len(periods), h0, h1, s=0.80, v=0.85)

        for p, c in zip(periods, cols, strict=True):
            period_base_color[p] = c

    # ---- 3) For each single MA period, derive multiple related but distinct colors
    # We keep MA vs VWMA, >/</±, and Nº/% visually different via V and S changes.
    def variant(hex_color: str, *, sat_mul=1.0, val_mul=1.0) -> str:
        r = int(hex_color[1:3], 16) / 255.0
        g = int(hex_color[3:5], 16) / 255.0
        b = int(hex_color[5:7], 16) / 255.0

        # convert RGB->HSV
        import colorsys
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        s = max(0.0, min(1.0, s * sat_mul))
        v = max(0.0, min(1.0, v * val_mul))
        rr, gg, bb = colorsys.hsv_to_rgb(h, s, v)
        return _rgb_hex(rr, gg, bb)

    m = {}

    # Singles: 12 variants per period (your items 1..12)
    for n in mas_list:
        base = period_base_color[n]

        # MA line vs VWMA line (VWMA a bit darker)
        m[f"MA{n}"] = variant(base, sat_mul=0.95, val_mul=0.95)
        m[f"VWMA{n}"] = variant(base, sat_mul=1.05, val_mul=0.75)

        # Counts (Nº) vs Percent (%) and >/< /±
        m[f"Nº>MA{n}"] = variant(base, sat_mul=1.10, val_mul=0.90)
        m[f"%>MA{n}"]  = variant(base, sat_mul=0.85, val_mul=1.00)

        m[f"Nº<MA{n}"] = variant(base, sat_mul=1.10, val_mul=0.65)
        m[f"%<MA{n}"]  = variant(base, sat_mul=0.85, val_mul=0.80)

        m[f"%±MA{n}"]  = variant(base, sat_mul=0.55, val_mul=0.95)

        m[f"Nº>VWMA{n}"] = variant(base, sat_mul=1.15, val_mul=0.70)
        m[f"%>VWMA{n}"]  = variant(base, sat_mul=0.90, val_mul=0.85)

        m[f"Nº<VWMA{n}"] = variant(base, sat_mul=1.15, val_mul=0.50)
        m[f"%<VWMA{n}"]  = variant(base, sat_mul=0.90, val_mul=0.65)

        m[f"%±VWMA{n}"]  = variant(base, sat_mul=0.55, val_mul=0.75)

    # ---- 4) Composite keys
    def combo_key(prefix: str, combo: tuple[int, ...]) -> str:
        return f"{prefix}{'&'.join(map(str, combo))}"

    # If you want EXACTLY the user-stated 48 “composites”, set include_all_pairwise_and_triplets=False
    for group_name, gd in ma_groups.items():
        periods = tuple(sorted(gd["periods"]))

        if include_all_pairwise_and_triplets:
            combos = list(combinations(periods, 2))
            if len(periods) >= 3:
                combos += [periods]  # the full triplet
        else:
            # match the “pair” and “full list” pattern: [a_b] and [a_b_c] for each group
            combos = [(periods[0], periods[1]), periods]

        for combo in combos:
            # choose composite base color as the average idea: use the first period’s hue,
            # but make composites lighter so they differ from singles.
            cbase = variant(period_base_color[combo[0]], sat_mul=0.70, val_mul=1.10)

            for ma_prefix in ("MA", "VWMA"):
                # VWMA composites: darker
                c = cbase if ma_prefix == "MA" else variant(cbase, sat_mul=1.00, val_mul=0.78)

                # Nº and % plus >/<
                m[f"Nº>{combo_key(ma_prefix, combo)}"] = variant(c, sat_mul=1.10, val_mul=0.90)
                m[f"Nº<{combo_key(ma_prefix, combo)}"] = variant(c, sat_mul=1.10, val_mul=0.65)
                m[f"%>{combo_key(ma_prefix, combo)}"]  = variant(c, sat_mul=0.85, val_mul=1.00)
                m[f"%<{combo_key(ma_prefix, combo)}"]  = variant(c, sat_mul=0.85, val_mul=0.80)

    return m


mka_color_map = build_mka_color_map(ma_groups, mas_list, include_all_pairwise_and_triplets=False)

# Sanity checks
print("mas_list:", mas_list)
print("keys:", len(mka_color_map))
print("sample:", list(mka_color_map.items())[:156])

# If you want the “full, consistent composites” (pairs + triplets across all groups):
# mka_color_map = build_mka_color_map(ma_groups, mas_list, include_all_pairwise_and_triplets=True)
# print("keys (full composites):", len(mka_color_map))

"""
#-----------------
HOW TO USE
#-----------------

import matplotlib.pyplot as plt

fig, ax = plt.subplots()

ax.plot(df.index, df["MA5"],    color=mka_color_map["MA5"],    label="MA5")
ax.plot(df.index, df["VWMA5"],  color=mka_color_map["VWMA5"],  label="VWMA5")
ax.plot(df.index, df["MA12"],   color=mka_color_map["MA12"],   label="MA12")

ax.legend()
plt.show()"""

"""import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df.index, y=df["MA5"],
    mode="lines",
    name="MA5",
    line=dict(color=mka_color_map["MA5"], width=2),
))
fig.show()"""