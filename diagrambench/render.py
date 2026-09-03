"""SVG renderer: display list -> standalone SVG string."""

from html import escape

from . import theme
from .layout import layout_scene


def _attr_str(attrs):
    parts = []
    for k, v in attrs.items():
        if isinstance(v, float):
            v = f"{v:.2f}".rstrip("0").rstrip(".")
        parts.append(f'{k}="{escape(str(v), quote=True)}"')
    return " ".join(parts)


def items_to_svg(items, width=None, height=None, background=True):
    W = width or theme.CANVAS_W
    H = height or theme.CANVAS_H
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}" font-family="{theme.FONT}">']
    if background:
        out.append(f'<rect x="0" y="0" width="{W}" height="{H}" '
                   f'fill="{theme.PAPER}"/>')
    for it in items:
        tag = it["tag"]
        attrs = dict(it["attrs"])
        attrs["id"] = it["id"]
        if tag == "text":
            body = escape(it.get("text", ""))
            out.append(f"<text {_attr_str(attrs)}>{body}</text>")
        else:
            out.append(f"<{tag} {_attr_str(attrs)}/>")
    out.append("</svg>")
    return "\n".join(out)


def render_scene(scene, ledgers):
    items, warnings = layout_scene(scene, ledgers)
    return items_to_svg(items), warnings


def render_env(env):
    return render_scene(env.scene, env.ledgers)
