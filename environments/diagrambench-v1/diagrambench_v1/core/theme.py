"""Visual language: editorial, restrained, beautiful by default."""

CANVAS_W = 960
CANVAS_H = 600
MARGIN = 26

FONT = "Inter, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

PAPER = "#FCFCFA"
INK = "#1F2430"
TITLE = "#171C26"
LABEL = "#3B4252"
MUTED = "#6B7280"
FAINT = "#9AA1AE"
GRID = "#ECEDF1"
AXIS = "#D6D9E0"
PANEL_EDGE = "#E4E6EB"
CORRAL_FILL = "#F2F4F8"
CORRAL_EDGE = "#D8DCE5"

HUE_HEX = {
    "tide": "#3E6DE0",
    "ember": "#E8590C",
    "moss": "#2F9E64",
    "plum": "#8D6FD1",
    "sand": "#D9A62E",
    "teal": "#0CA678",
    "rose": "#E64980",
    "slate": "#64748B",
    "ink": "#1F2430",
    "mist": "#C7CDD9",
}

PALETTES = {
    "quill": ["tide", "ember", "moss", "plum", "sand", "teal", "rose", "slate"],
    "dusk": ["#5B6EE8", "#8B7CF0", "#4C9BE8", "#3D53C6", "#A9A2F2", "#6FB6E8",
             "#7C5CD6", "#9DB2F0"],
    "field": ["#3E9A5F", "#8AB65C", "#2E7D6B", "#C9A54A", "#5B8A72", "#A3C98A",
              "#77A85B", "#4E6E58"],
    "emberline": ["#E8590C", "#F2A33C", "#C93C2C", "#B2503F", "#E87F4F", "#D9822B",
                  "#A8543A", "#F0B873"],
}

NODE_FILL = "#F6F7FA"
NODE_EDGE = "#C9CFDA"
NODE_TEXT = "#232936"
CORD = "#8B93A3"
CORD_KINDLED = "#E8590C"
PIPE = "#B9C3D8"

FS_TITLE = 17
FS_SUBTITLE = 12
FS_LABEL = 11
FS_TICK = 10.5
FS_BADGE = 10.5
FS_NODE = 11.5
FS_NOTE = 11
FS_ANNOT = 11.5


def palette_colors(name):
    pal = PALETTES.get(name or "quill", PALETTES["quill"])
    return [HUE_HEX.get(c, c) for c in pal]


def hue_hex(token):
    return HUE_HEX.get(token, token)


def mix(hex_a, hex_b, t):
    a = [int(hex_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def soften(hex_c, t=0.12):
    """Blend toward paper for fills."""
    return mix(hex_c, "#FFFFFF", t)


def ramp(t, base="#3E6DE0"):
    """Counted tint ramp: pale mist -> saturated base."""
    return mix("#E3E8F2", base, 0.15 + 0.85 * max(0.0, min(1.0, t)))


def text_w(s, fs):
    return len(str(s)) * fs * 0.58


def fmt_num(v):
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9:
            v = int(round(v))
        else:
            return f"{v:,.2f}".rstrip("0").rstrip(".")
    if isinstance(v, int) and abs(v) >= 10000:
        return f"{v:,}"
    return str(v)
