"""The semantic scene: the canonical internal representation of a VELD artifact.

Everything the verifier scores lives here. The layout engine and renderer are
pure functions of (scene, ledgerspace).
"""

import copy

from .errors import VeldError

FORMS = ["slab", "disc", "wisp", "ring", "capsule", "rhomb", "drum", "plaque"]
TRAITS = ["stature", "girth", "stance", "perch", "tint", "bulk", "veil", "heft"]
LAWS = ["abreast", "heap", "strew", "wheel", "current"]
HEADINGS = ["east", "west", "north", "south"]
SIDES = ["south", "west", "north", "east"]
AIMS = ["auto", "north", "south", "east", "west", "center", "rim"]
HUES = ["ember", "tide", "moss", "plum", "sand", "slate", "rose", "teal", "ink", "mist"]
PALETTES = ["quill", "dusk", "field", "emberline"]


class Parcel:
    def __init__(self, pid, parent=None, cell_key=None, kind="root"):
        self.id = pid
        self.parent = parent
        self.cell_key = cell_key
        self.kind = kind  # root | cell | split | nest
        self.carve = None  # {along, ledger, by, gap, cells:{key: pid}, order:[keys]}
        self.split = None  # {along, count, gap, cells:[pids]}
        self.hooped = None  # {inner: float}
        self.settle = None  # {law, heading} or None -> default
        self.breathe = None
        self.inverted = []
        self.host_glyph = None
        self.nest_aim = None
        self.nest_breadth = None
        self.nest_depth = None
        self.entitle = None
        self.note = None
        self.palette = None
        self.gauge_overrides = {}  # trait -> (floor, ceil)
        self.rims = []  # sides
        self.wefts = []  # alongs


class Glyph:
    def __init__(self, gid, parcel, form, brood=None, name=None, row=None):
        self.id = gid
        self.parcel = parcel  # cell parcel the glyph lives in
        self.form = form
        self.brood = brood
        self.name = name
        self.row = row  # data record (dict) for sown glyphs
        self.fixed = {}  # tint/veil/outline overrides
        self.badge = None  # {text?, vein?, aim}
        self.badge2 = None  # secondary label (e.g. a value under a named node)
        self.kindled = False
        self.hushed = False
        self.layer = 0


class Brood:
    def __init__(self, bid, parcel, ledger_ref, form, key_vein=None):
        self.id = bid
        self.parcel = parcel
        self.ledger_ref = ledger_ref
        self.form = form
        self.key_vein = key_vein
        self.meterings = {}  # trait -> vein
        self.glyphs = []
        self.loose_traits = []
        self.strand = None
        self.badge = None  # brood-level badge spec applied to all glyphs
        self.fixed = {}
        self.kindled = False
        self.hushed = False


class Strand:
    def __init__(self, sid, brood, by):
        self.id = sid
        self.brood = brood
        self.by = by
        self.flooded = False
        self.heft = None
        self.tint = None
        self.kindled = False


class Cord:
    def __init__(self, cid, tail, head, sense="forth"):
        self.id = cid
        self.tail = tail
        self.head = head
        self.sense = sense
        self.barb = "head"
        self.sweep = 0.0
        self.crook = "auto"  # straight | bend | arc | auto
        self.heft = None
        self.pipe_width = None
        self.kindled = False
        self.hushed = False
        self.tint = None
        self.badge = None


class Flock:
    def __init__(self, fid, members, name=None):
        self.id = fid
        self.members = members
        self.name = name


class Corral:
    def __init__(self, kid, members, label=None):
        self.id = kid
        self.members = members
        self.label = label
        self.tint = None


class Annotation:
    def __init__(self, aid, kind, text, near=None, aim="auto"):
        self.id = aid
        self.kind = kind  # inscribe | flag
        self.text = text
        self.near = near  # ref of glyph/parcel/cord or None
        self.aim = aim


class Key:
    def __init__(self, parcel, brood, trait):
        self.parcel = parcel
        self.brood = brood
        self.trait = trait


class Scene:
    def __init__(self):
        self.parcels = {}
        self.glyphs = {}
        self.broods = {}
        self.strands = {}
        self.cords = {}
        self.flocks = {}
        self.corrals = {}
        self.annotations = []
        self.keys = []
        self.shared = []  # (parcel_a, parcel_b, trait)
        self._counters = {}
        root = Parcel("p0")
        self.parcels["p0"] = root
        self.root = "p0"

    # -- ids -------------------------------------------------------------
    def next_id(self, prefix):
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f"{prefix}{self._counters[prefix]}"

    # -- lookup ----------------------------------------------------------
    def parcel(self, ref):
        p = self.parcels.get(ref)
        if not p:
            raise VeldError(f"unknown parcel '{ref}'. Parcels: {', '.join(self.parcels)}.")
        return p

    def brood(self, ref):
        b = self.broods.get(ref)
        if not b:
            raise VeldError(f"unknown brood '{ref}'.")
        return b

    def glyph(self, ref):
        if ref in self.glyphs:
            return self.glyphs[ref]
        for g in self.glyphs.values():
            if g.name == ref:
                return g
        raise VeldError(f"unknown glyph '{ref}' (no such ref or name).")

    def cord(self, ref):
        c = self.cords.get(ref)
        if not c:
            raise VeldError(f"unknown cord '{ref}'.")
        return c

    def strand_of(self, ref):
        s = self.strands.get(ref)
        if not s:
            raise VeldError(f"unknown strand '{ref}'.")
        return s

    def resolve_target(self, ref):
        """Resolve a ref/name to (kind, object) across glyphs, broods, flocks,
        cords, strands, parcels, corrals."""
        for table, kind in (
            (self.broods, "brood"), (self.cords, "cord"), (self.strands, "strand"),
            (self.flocks, "flock"), (self.corrals, "corral"), (self.parcels, "parcel"),
        ):
            if ref in table:
                return kind, table[ref]
        if ref in self.glyphs:
            return "glyph", self.glyphs[ref]
        for g in self.glyphs.values():
            if g.name == ref:
                return "glyph", g
        raise VeldError(f"unknown target '{ref}'.")

    def target_glyphs(self, ref):
        """Expand a target ref to a list of glyphs (for emphasis/patina/badge)."""
        kind, obj = self.resolve_target(ref)
        if kind == "glyph":
            return [obj]
        if kind == "brood":
            return [self.glyphs[g] for g in obj.glyphs]
        if kind == "flock" or kind == "corral":
            return [self.glyphs[g] for g in obj.members]
        raise VeldError(f"target '{ref}' is a {kind}; expected glyphs, a brood, or a flock.")

    # -- structure helpers ------------------------------------------------
    def chart_root(self, pid):
        """Nearest ancestor that is not a carve cell — the gauge owner."""
        p = self.parcel(pid)
        while p.kind == "cell" and p.parent:
            p = self.parcel(p.parent)
        return p

    def descendants(self, pid):
        out = [pid]
        p = self.parcel(pid)
        if p.carve:
            for c in p.carve["cells"].values():
                out.extend(self.descendants(c))
        if p.split:
            for c in p.split["cells"]:
                out.extend(self.descendants(c))
        for q in self.parcels.values():
            if q.kind == "nest" and q.parent == pid:
                out.extend(self.descendants(q.id))
        return out

    def glyphs_in(self, pid, recursive=True):
        pids = set(self.descendants(pid)) if recursive else {pid}
        return [g for g in self.glyphs.values() if g.parcel in pids]

    def broods_in(self, pid):
        pids = set(self.descendants(pid))
        return [b for b in self.broods.values()
                if b.parcel in pids or (b.glyphs and self.glyphs[b.glyphs[0]].parcel in pids)]

    def effective_settle(self, parcel):
        """Settle law for a parcel's cells, inheriting from the chart root."""
        p = parcel
        while True:
            if p.settle:
                return p.settle
            if p.parent is None:
                break
            p = self.parcel(p.parent)
        root = self.chart_root(parcel.id)
        if root.hooped or parcel.hooped:
            return {"law": "wheel", "heading": None}
        return {"law": "abreast", "heading": None}

    def snapshot(self):
        return copy.deepcopy(self)
