import re
from collections import defaultdict
from matplotlib import cm


def build_mka_color_map(ma_groups, mas_list):
    """
    Color map compatible with ma_indicators_2 column naming.

    Supported keys:
        %>VWMA5
        $>V5
        $>V5>V12
        $>V40>V50>V60
        $>V80>V100>V200 (long)

    Color logic:
        - Hue by group (short / medium / long)
        - Intensity by ladder depth
    """

    # --------------------------------------------------
    # 1. Define base colormaps per group
    # --------------------------------------------------
    group_cmaps = {
        "short": cm.Blues,
        "medium": cm.Oranges,
        "long": cm.Reds,
    }

    # --------------------------------------------------
    # 2. Map VWMA period → group
    # --------------------------------------------------
    period_to_group = {}
    for group, data in ma_groups.items():
        for p in data["periods"]:
            period_to_group[p] = group

    color_map = {}

    # --------------------------------------------------
    # 3. %>VWMAp (single breadth series)
    # --------------------------------------------------
    for p in mas_list:
        group = period_to_group[p]
        cmap = group_cmaps[group]

        # fixed mid-tone for single VWMA
        color_map[f"%>VWMA{p}"] = cmap(0.55)

    # --------------------------------------------------
    # 4. $>V... true ladders
    # --------------------------------------------------
    ladder_by_group = defaultdict(list)

    for p in mas_list:
        group = period_to_group[p]
        ladder_by_group[group].append(p)

    for group, periods in ladder_by_group.items():
        cmap = group_cmaps[group]

        for i in range(len(periods)):
            rung = periods[: i + 1]
            depth = len(rung)

            # normalize depth → color intensity
            intensity = 0.35 + 0.6 * (depth / len(periods))

            label = "$>" + ">".join(f"V{p}" for p in rung)
            color_map[label] = cmap(intensity)

    return color_map
