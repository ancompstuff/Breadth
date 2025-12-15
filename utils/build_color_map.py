from __future__ import annotations
from itertools import combinations
from colorsys import hsv_to_rgb
import colorsys


# --- Utility Functions (as defined previously) ---
def _rgb_hex(r: float, g: float, b: float) -> str:
    return f"#{int(round(r * 255)):02x}{int(round(g * 255)):02x}{int(round(b * 255)):02x}"


def _hsv_palette(n: int, h0: float, h1: float, s: float, v: float) -> list[str]:
    # ... (implementation as in the last response) ...
    if n <= 0:
        return []
    if n == 1 or h0 == h1:
        r, g, b = hsv_to_rgb(h0, s, v)
        return [_rgb_hex(r, g, b)] * n
    out = []
    for i in range(n):
        h = h0 + (h1 - h0) * (i / (n - 1))
        r, g, b = hsv_to_rgb(h % 1.0, s, v)
        out.append(_rgb_hex(r, g, b))
    return out


# --- Core Function with Saturation Dedicated to Combo Depth ---

def build_mka_color_map(
        ma_groups: dict,
        mas_list: list[int],
        *,
        include_all_pairwise_and_triplets: bool = False,
) -> dict[str, str]:

    # ---- 1) Define 3 distinct Hues (Primary Hues for Group)
    HUE_MAP = {
        "short": (0.00, 0.03),  # Red
        "medium": (0.33, 0.36),  # Green
        "long": (0.66, 0.69),  # Blue
    }

    # ---- S/V Map for Combo Depth (Saturation is the differentiator)
    SAT_MAP = {
        # S_base: Saturation level for the base color of the metric (e.g., MA or VWMA line)
        1: 0.95,  # Single (Highly Saturated)
        2: 0.65,  # Pair (Medium Saturation)
        3: 0.35,  # Triplet (Low Saturation - Pale/Translucent effect)
    }

    # ---- 2) Build per-period base colors (Depth 1/Single)
    period_base_color: dict[int, str] = {}
    for group_name, gd in ma_groups.items():
        periods = sorted(gd["periods"])
        h0, h1 = HUE_MAP[group_name]

        # Base V is high to give range for dark variants
        cols = _hsv_palette(len(periods), h0, h1, s=SAT_MAP[1], v=0.90)

        for p, c in zip(periods, cols, strict=True):
            period_base_color[p] = c

    # ---- 3) Variant function (re-tuning S/V shifts for max contrast)
    def variant(hex_color: str, *, sat_mul=1.0, val_mul=1.0, sat_add=0.0, val_add=0.0) -> str:
        r = int(hex_color[1:3], 16) / 255.0
        g = int(hex_color[3:5], 16) / 255.0
        b = int(hex_color[5:7], 16) / 255.0

        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        s = max(0.0, min(1.0, s * sat_mul + sat_add))
        v = max(0.0, min(1.0, v * val_mul + val_add))

        rr, gg, bb = colorsys.hsv_to_rgb(h, s, v)
        return _rgb_hex(rr, gg, bb)

    m = {}

    # Helper function to generate all 12 variants for a given base color
    def generate_variants(base: str, n: int, m: dict, prefix: str):
        # VWMA/MA distinction (V-shift for darker/lighter)
        m[f"MA{n}"] = variant(base, sat_mul=1.0, val_mul=1.0)
        m[f"VWMA{n}"] = variant(base, sat_mul=0.9, val_mul=0.70)

        # Metric distinctions (V-shift is main differentiator)
        # Nº > / % > : Bright
        m[f"Nº>{prefix}{n}"] = variant(base, sat_mul=1.05, val_mul=1.1, val_add=0.05)
        m[f"%>MA{n}"] = variant(base, sat_mul=0.70, val_mul=1.05)

        # Nº < / % < : Dark
        m[f"Nº<{prefix}{n}"] = variant(base, sat_mul=1.05, val_mul=0.60, val_add=-0.1)
        m[f"%<{prefix}{n}"] = variant(base, sat_mul=0.70, val_mul=0.75)

        # %± : Neutral/Gray (low S)
        m[f"%±{prefix}{n}"] = variant(base, sat_mul=0.30, val_mul=0.95)

        # VWMA Metric distinctions (applied to VWMA line S/V)
        vwma_base = m[f"VWMA{n}"]
        m[f"Nº>VWMA{n}"] = variant(vwma_base, sat_mul=1.1, val_mul=1.05)
        m[f"%>VWMA{n}"] = variant(vwma_base, sat_mul=0.85, val_mul=1.1)
        m[f"Nº<VWMA{n}"] = variant(vwma_base, sat_mul=1.1, val_mul=0.70)
        m[f"%<VWMA{n}"] = variant(vwma_base, sat_mul=0.85, val_mul=0.85)
        m[f"%±VWMA{n}"] = variant(vwma_base, sat_mul=0.30, val_mul=0.80)
        return m

    # Singles: 12 variants per period
    for n in mas_list:
        base = period_base_color[n]
        generate_variants(base, n, m, prefix="MA")

    # ---- 4) Composite keys (New Saturation based on Combo Depth)
    def combo_key(prefix: str, combo: tuple[int, ...]) -> str:
        return f"{prefix}{'&'.join(map(str, combo))}"

    for group_name, gd in ma_groups.items():
        periods = tuple(sorted(gd["periods"]))

        combo_map = {
            2: (periods[0], periods[1]),  # Pair
            3: periods,  # Triplet
        }

        for depth, combo in combo_map.items():
            h0, h1 = HUE_MAP[group_name]
            # Use the hue of the group, but the saturation of the depth
            s_depth = SAT_MAP[depth]

            # Base color for the composite: High V, Depth S, Group H
            cbase_hex = _hsv_palette(1, (h0 + h1) / 2, (h0 + h1) / 2, s_depth, v=0.95)[0]

            for ma_prefix in ("MA", "VWMA"):
                # Use the composite base color
                c = cbase_hex

                # Apply strong V-shifts for the metric types

                # Nº > / % > : Brightest/Highest V variant (Top Layer)
                m[f"Nº>{combo_key(ma_prefix, combo)}"] = variant(c, sat_mul=1.1, val_mul=1.0, val_add=0.05)
                m[f"%>{combo_key(ma_prefix, combo)}"] = variant(c, sat_mul=0.85, val_mul=1.0)

                # Nº < / % < : Darkest/Lowest V variant (Bottom Layer)
                m[f"Nº<{combo_key(ma_prefix, combo)}"] = variant(c, sat_mul=1.1, val_mul=0.6)
                m[f"%<{combo_key(ma_prefix, combo)}"] = variant(c, sat_mul=0.85, val_mul=0.75)

    return m

# Final Example of the Three Short Term Bar Segments:

# Short-term (RED Hue):
# Single (Highest Saturation): #f20d1c (Vivid Red)
# Pair (Medium Saturation):   #f24b4b (Softer Red)
# Triplet (Lowest Saturation): #f29c9c (Pale Pink/Top Layer)