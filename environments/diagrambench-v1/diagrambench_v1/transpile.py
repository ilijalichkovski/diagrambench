"""Transpile reference op programs into SIGIL multi-unit projects.

Simulates the ops against the live engine while walking them, so parcel/cell
refs resolve exactly as the original programs did. Output is a dict of unit
sources that `compile_project` must accept and whose execution must verify.
"""

import re

from .core.datasets import DATASETS, RANKED_ORDERS, vein_kind
from .core.sdk import TaskEnv

REL_INV = {"is": "==", "is_not": "!=", "above": ">", "below": "<",
           "at_least": ">=", "at_most": "<="}
AGG_OF = {"sum": "sum", "mean": "mean", "median": "median", "min": "min",
          "max": "max", "count": "count"}


def _lit(v):
    if isinstance(v, str):
        return '"' + v.replace('"', '\\"') + '"'
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v)


def _schema_of(dataset):
    rows = DATASETS[dataset]
    cols = list(rows[0].keys())
    parts = []
    for c in cols:
        vals = [r[c] for r in rows]
        kind = vein_kind(c, vals)
        if kind == "counted":
            parts.append(f"{c}: counted")
        elif kind == "ranked":
            present = []
            for v in RANKED_ORDERS[c]:
                if v in set(vals):
                    present.append(v)
            order = ", ".join(_lit(v) for v in present)
            parts.append(f"{c}: rank[{order}]")
        else:
            parts.append(f"{c}: told")
    return "(" + ", ".join(parts) + ")"


def _var(label, taken):
    base = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or "n"
    if base[0].isdigit():
        base = "n_" + base
    v = base
    i = 2
    while v in taken:
        v = f"{base}{i}"
        i += 1
    taken.add(v)
    return v


class Transpiler:
    def __init__(self, program):
        self.program = program
        self.env = TaskEnv()
        self.data, self.ground, self.marks, self.script = [], [], [], []
        self.taken = set()
        self.led = {}       # engine ref (name or L#) -> sigil var
        self.parcel = {"p0": "@root"}   # engine pid -> sigil parcel expr
        self.brood = {}     # b# -> var
        self.brood_led = {}
        self.brood_kernel = {}  # var -> {"form","binds":[],"badge":[],"ifs":[]}
        self.brood_route = {}   # b# -> (parcel_expr, key)
        self.gauges = {}    # (bvar, trait) -> gauge var
        self.gauge_decl = {}  # gauge var -> declaration line
        self.g_cal = {}     # gauge var -> "auto" | ", floor X..." | None
        self.spawn = {}     # glyph name/label -> var; also gid -> var
        self.cord = {}      # c# -> var
        self.strand = {}    # s# -> var
        self.pick = {}      # f# -> (brood_ref, [clauses])
        self.arena_n = 0
        self.lat_n = 0
        self.gauge_n = 0

    # ------------------------------------------------------------------
    def act(self, op, args):
        obs = self.env.act(op, args)
        if not obs.get("ok"):
            raise RuntimeError(f"transpile: engine refused {op}({args}): "
                               f"{obs.get('error')}")
        return obs

    def ledvar(self, ref):
        if ref not in self.led:
            if ref in DATASETS:
                v = _var(ref, self.taken)
                self.data.append(f'ledger {v} = open("data/{ref}.tsv") '
                                 f'schema {_schema_of(ref)};')
                self.led[ref] = v
            else:
                raise RuntimeError(f"unknown ledger ref {ref}")
        return self.led[ref]

    def stage(self, parent_ref, new_ref, stage_src):
        v = _var(new_ref.lower(), self.taken)
        self.data.append(f"ledger {v} = {self.ledvar(parent_ref)} | "
                         f"{stage_src};")
        self.led[new_ref] = v
        return v

    def pexpr(self, pid):
        if pid not in self.parcel:
            raise RuntimeError(f"unmapped parcel {pid}")
        return self.parcel[pid]

    def kernel(self, bvar):
        return self.brood_kernel.setdefault(
            bvar, {"form": None, "binds": [], "badges": [], "ifs": []})

    def gauge_for(self, bvar, trait, vein, ledref):
        key = (bvar, trait)
        if key in self.gauges:
            return self.gauges[key]
        self.gauge_n += 1
        gv = f"g{self.gauge_n}"
        led = self.env.ledgers.resolve(ledref)
        kind = led.kind_of(vein)
        if kind == "counted":
            self.gauge_decl[gv] = f"gauge {gv} = gauge counted;"
            self.g_cal[gv] = "auto"
        else:
            self.gauge_decl[gv] = (f"gauge {gv} = gauge banded("
                                   f"{self.ledvar(ledref)}.{vein});")
        self.gauges[key] = gv
        return gv

    def target_ref(self, ref):
        """engine target ref -> sigil var (brood/spawn/cord/strand/pick)."""
        if ref in self.brood:
            return self.brood[ref]
        if ref in self.spawn:
            return self.spawn[ref]
        if ref in self.cord:
            return self.cord[ref]
        if ref in self.strand:
            return self.strand[ref]
        return None

    # ------------------------------------------------------------------
    def emit_if(self, fref, actions):
        bref, clauses = self.pick[fref]
        bvar = self.brood[bref]
        pred = " && ".join(
            f".{v} {REL_INV[r]} {_lit(val)}" if r in REL_INV
            else f".{v} in [{', '.join(_lit(x) for x in val)}]"
            for v, r, val in clauses)
        self.kernel(bvar)["ifs"].append((pred, actions))

    # ------------------------------------------------------------------
    def walk(self):
        for op, args in self.program:
            self.step(op, dict(args))
        return self.assemble()

    def step(self, op, a):
        obs = self.act(op, a)
        ref = obs.get("ref")

        if op == "sift":
            rel = a["relation"]
            if rel == "among":
                vals = ", ".join(_lit(v) for v in a["value"])
                pred = f".{a['vein']} in [{vals}]"
            else:
                pred = f".{a['vein']} {REL_INV[rel]} {_lit(a['value'])}"
            self.stage(a["ledger"], ref, f"keep({pred})")
        elif op == "distill":
            by = a["by"] if isinstance(a["by"], list) else [a["by"]]
            bys = ", ".join(f".{b}" for b in by)
            if a["mode"] == "count":
                self.stage(a["ledger"], ref, f"fold({bys}; tally = count())")
            else:
                self.stage(a["ledger"], ref,
                           f"fold({bys}; {a['take']} = "
                           f"{AGG_OF[a['mode']]}(.{a['take']}))")
        elif op == "derive":
            m = a["mode"]
            if m == "total_share":
                expr = f"share(.{a['a']})"
            else:
                sym = "/" if m == "ratio" else "-"
                expr = f".{a['a']} {sym} .{a['b']}"
            self.stage(a["ledger"], ref, f"derive({a['name']} = {expr})")
        elif op == "bin":
            self.stage(a["ledger"], ref,
                       f"bins(.{a['vein']}, {a.get('bins', 8)})")
        elif op == "marshal":
            sense = "asc" if a["sense"] == "waxing" else "desc"
            self.stage(a["ledger"], ref, f"rank(.{a['vein']}, {sense})")
        elif op == "crop":
            self.stage(a["ledger"], ref, f"first({a['first']})")

        elif op == "carve":
            self.lat_n += 1
            lv = f"lat{self.lat_n}"
            self.ground.append(f"lattice {lv} = lattice("
                               f"{self.ledvar(a['ledger'])}.{a['by']});")
            gap = f", gap {a['gap']:g}" if "gap" in a else ""
            base = self.pexpr(a["parcel"])
            self.ground.append(f"cleave {base} : {a['along']} by {lv}{gap};")
            p = self.env.scene.parcel(a["parcel"])
            for key, cid in p.carve["cells"].items():
                self.parcel[cid] = f'{base}[{_lit(key)}]'
        elif op == "split":
            base = self.pexpr(a["parcel"])
            gap = f", gap {a['gap']:g}" if "gap" in a else ""
            self.ground.append(f"split {base} : {a['along']} into "
                               f"{a['count']}{gap};")
            p = self.env.scene.parcel(a["parcel"])
            for i, cid in enumerate(p.split["cells"]):
                self.parcel[cid] = f"{base}[{i + 1}]"
        elif op == "cell":
            pass  # addressing only; mappings created at carve/split
        elif op == "hoop":
            inner = f" inner {a['inner']:g}" if "inner" in a else ""
            self.ground.append(f"hoop {self.pexpr(a['parcel'])}{inner};")
        elif op == "settle":
            law = a["law"]
            if law == "current":
                law = f"current({a.get('heading', 'east')})"
            self.ground.append(f"law {self.pexpr(a['parcel'])} = {law};")
        elif op == "invert":
            self.ground.append(f"invert {self.pexpr(a['parcel'])} : "
                               f"{a['along']};")
        elif op == "breathe":
            self.ground.append(f"breathe {self.pexpr(a['parcel'])} "
                               f"{a['amount']:g};")
        elif op == "palette":
            self.ground.append(f"palette {self.pexpr(a['parcel'])} "
                               f"{a['name']};")
        elif op == "share":
            self.ground.append(f"align {self.pexpr(a['parcel_a'])} ~ "
                               f"{self.pexpr(a['parcel_b'])} : {a['trait']};")
        elif op == "abut":
            self.ground.append(f"abut {self.pexpr(a['parcel_a'])} ~ "
                               f"{self.pexpr(a['parcel_b'])} : {a['edge']};")
        elif op == "nest":
            self.arena_n += 1
            av = f"inset{self.arena_n}"
            self.taken.add(av)
            opts = "".join(
                [f" at {a['aim']}" if "aim" in a else ""] +
                [f", breadth {a['breadth']:g}" if "breadth" in a else ""] +
                [f", depth {a['depth']:g}" if "depth" in a else ""])
            if "host" in a:
                hv = self.spawn[a["host"]]
                self.marks.append(f"arena {av} = nest under {hv}{opts};")
            else:
                self.ground.append(f"arena {av} = nest "
                                   f"{self.pexpr(a['parcel'])}{opts};")
            self.parcel[ref] = f"@{av}"

        elif op == "sow":
            bv = _var(f"b_{self.ledvar(a['ledger'])}", self.taken)
            self.brood[ref] = bv
            self.brood_led[ref] = a["ledger"]
            self.marks.append(f"brood {bv} = alloc brood("
                              f"{self.ledvar(a['ledger'])});")
            by = f" by .{a['key']}" if a.get("key") else ""
            self.marks.append(f"route {bv} into "
                              f"{self.pexpr(a['parcel'])}{by};")
            self.marks.append(f"commit {bv};")
            self.kernel(bv)["form"] = a["form"]
        elif op == "place":
            v = _var(a.get("name") or a["form"], self.taken)
            label = a.get("name") or a["form"]
            self.spawn[label] = v
            self.spawn[ref] = v
            self.marks.append(f'spawn {v} = {a["form"]} {_lit(label)} in '
                              f'{self.pexpr(a["parcel"])};')
        elif op == "meter":
            bv = self.brood[a["brood"]]
            gv = self.gauge_for(bv, a["trait"], a["vein"],
                                self.brood_led[a["brood"]])
            self.kernel(bv)["binds"].append(
                (a["trait"], gv, a["vein"]))
        elif op == "rebase":
            # attach to the gauge of the matching (brood, trait)
            for (bv, trait), gv in self.gauges.items():
                if trait == a["trait"] and gv in self.g_cal:
                    parts = []
                    if a.get("floor") is not None:
                        parts.append(f"floor {a['floor']:g}")
                    if a.get("ceil") is not None:
                        parts.append(f"ceil {a['ceil']:g}")
                    self.g_cal[gv] = ", " + ", ".join(parts) if parts \
                        else "auto"
                    break
        elif op == "loosen":
            self.marks.append(f"loosen {self.brood[a['brood']]}."
                              f"{a['trait']};")
        elif op == "unmeter":
            pass

        elif op == "tether":
            cv = _var(f"c_{len(self.cord) + 1}", self.taken)
            self.cord[ref] = cv
            self.marks.append(f"cord {cv} = tether "
                              f"{self.spawn[a['tail']]} -> "
                              f"{self.spawn[a['head']]};")
        elif op == "pipe":
            cv = _var(f"c_{len(self.cord) + 1}", self.taken)
            self.cord[ref] = cv
            self.marks.append(f"pipe {self.spawn[a['tail']]} -> "
                              f"{self.spawn[a['head']]} width "
                              f"{a['width']:g} as {cv};")
        elif op in ("barb", "sweep", "crook"):
            cv = self.cord[a["cord"]]
            argname = {"barb": "at", "sweep": "amount", "crook": "style"}[op]
            val = a[argname]
            self.marks.append(f"{cv}.{op} = "
                              f"{val if not isinstance(val, str) else val};")
        elif op == "heft":
            tv = self.target_ref(a["target"])
            self.marks.append(f"{tv}.heft = {a['weight']:g};")
        elif op == "thread":
            sv = _var(f"s_{len(self.strand) + 1}", self.taken)
            self.strand[ref] = sv
            self.marks.append(f"thread {self.brood[a['brood']]} by "
                              f".{a['by']} as {sv};")
        elif op == "flood":
            self.marks.append(f"flood {self.strand[a['strand']]};")

        elif op == "pick":
            src = a["brood"]
            if src in self.pick:
                bref, clauses = self.pick[src]
                self.pick[ref] = (bref, clauses +
                                  [(a["vein"], a["relation"], a["value"])])
            else:
                self.pick[ref] = (src, [(a["vein"], a["relation"],
                                         a["value"])])
        elif op == "corral":
            members = ", ".join(self.spawn[m] for m in a["members"])
            self.marks.append(f'corral {_lit(a.get("label") or "")} '
                              f'{{ {members} }};')
        elif op in ("kindle", "hush"):
            t = a["target"]
            if t in self.pick:
                self.emit_if(t, [(op, None)])
            else:
                self.marks.append(f"{op} {self.target_ref(t)};")
        elif op in ("lift", "sink"):
            self.marks.append(f"{op} {self.target_ref(a['target'])};")
        elif op == "tint":
            t = a["target"]
            if t in self.pick:
                self.emit_if(t, [("paint", a["hue"])])
            else:
                self.marks.append(f"paint {self.target_ref(t)} {a['hue']};")
        elif op == "veil":
            self.marks.append(f"veil {self.target_ref(a['target'])} "
                              f"{a['amount']:g};")
        elif op == "outline":
            self.marks.append(f"outline {self.target_ref(a['target'])} "
                              f"{a['weight']:g};")

        elif op == "badge":
            t = a["target"]
            if t in self.brood:
                bv = self.brood[t]
                aim = f" at {a['aim']}" if a.get("aim") else ""
                if a.get("vein"):
                    self.kernel(bv)["badges"].append(
                        f"g.badge = text(.{a['vein']}){aim};")
                else:
                    self.kernel(bv)["badges"].append(
                        f"g.badge = {_lit(a['text'])}{aim};")
            elif t in self.cord:
                self.marks.append(f"{self.cord[t]}.badge = "
                                  f"{_lit(a['text'])};")
            else:
                aim = f" at {a['aim']}" if a.get("aim") else ""
                self.marks.append(f"label {self.spawn[t]} "
                                  f"{_lit(a['text'])}{aim};")
        elif op == "inscribe":
            near = a.get("near")
            if near in self.pick:
                aimtail = f' at {a["aim"]}' if a.get("aim") else ""
                self.emit_if(near, [("inscribe", (a["text"], a.get("aim")))])
            else:
                tail = ""
                if near is not None:
                    tail += f" near {self.target_ref(near)}"
                if a.get("aim"):
                    tail += f" at {a['aim']}"
                self.script.append(f"inscribe {_lit(a['text'])}{tail};")
        elif op == "flag":
            t = a["target"]
            if t in self.pick:
                self.emit_if(t, [("flag", a["text"])])
            else:
                self.script.append(f"flag {self.target_ref(t)} "
                                   f"{_lit(a['text'])};")

        elif op == "rim":
            self.script.append(f"raise rim {self.pexpr(a['parcel'])}:"
                               f"{a['side']};")
        elif op == "weft":
            self.script.append(f"raise weft {self.pexpr(a['parcel'])} : "
                               f"{a['along']};")
        elif op == "key":
            self.script.append(f"raise key {self.pexpr(a['parcel'])} from "
                               f"{self.brood[a['brood']]}.{a['trait']};")
        elif op == "entitle":
            self.script.append(f"entitle {self.pexpr(a['parcel'])} "
                               f"{_lit(a['text'])};")
        elif op == "note":
            self.script.append(f"note {self.pexpr(a['parcel'])} "
                               f"{_lit(a['text'])};")
        elif op == "flock":
            pass
        elif op == "disband":
            pass
        else:
            raise RuntimeError(f"transpiler: unhandled op {op}")

    # ------------------------------------------------------------------
    def assemble(self):
        marks = []
        emitted_kernel = set()
        for line in self.marks:
            marks.append(line)
            # right after commit of a brood, emit its kernel + calibrates
            m = re.match(r"commit (\w+);", line)
            if m and m.group(1) not in emitted_kernel:
                bv = m.group(1)
                emitted_kernel.add(bv)
                k = self.brood_kernel.get(bv)
                if not k:
                    continue
                for trait, gv, vein in k["binds"]:
                    if gv in self.gauge_decl:
                        marks.append(self.gauge_decl.pop(gv))
                body = []
                if k["form"]:
                    body.append(f"  g.form = {k['form']};")
                for trait, gv, vein in k["binds"]:
                    body.append(f"  g.{trait} = {gv}(.{vein});")
                body.extend("  " + b for b in k["badges"])
                for pred, actions in k["ifs"]:
                    acts = []
                    for act, val in actions:
                        if act in ("kindle", "hush"):
                            acts.append(f"{act} g;")
                        elif act == "paint":
                            acts.append(f"paint g {val};")
                        elif act == "flag":
                            acts.append(f"flag g {_lit(val)};")
                        elif act == "inscribe":
                            text, aim = val
                            t = f"inscribe g {_lit(text)}"
                            if aim:
                                t += f" at {aim}"
                            acts.append(t + ";")
                    body.append(f"  if ({pred}) {{ {' '.join(acts)} }}")
                marks.append(f"over {bv} as g {{")
                marks.extend(body)
                marks.append("}")
                for trait, gv, vein in k["binds"]:
                    cal = self.g_cal.get(gv)
                    if cal == "auto":
                        marks.append(f"calibrate {gv};")
                        self.g_cal[gv] = None
                    elif isinstance(cal, str) and cal.startswith(","):
                        marks.append(f"calibrate {gv}{cal};")
                        self.g_cal[gv] = None
        # kernels for broods whose kernel content arrived after commit
        # (meters always precede in reference programs, so none expected)

        units = {}
        if self.data:
            units["src/data.sgl"] = "unit data;\n\n" + "\n".join(self.data) \
                + "\n"
        if self.ground:
            units["src/ground.sgl"] = "unit ground;\n\n" + \
                "\n".join(self.ground) + "\n"
        if marks:
            units["src/marks.sgl"] = "unit marks;\n\n" + "\n".join(marks) \
                + "\n"
        if self.script:
            units["src/script.sgl"] = "unit script;\n\n" + \
                "\n".join(self.script) + "\n"
        units["src/main.sgl"] = "unit compose;\n\nsettle!;\n"
        return units


def transpile(program):
    return Transpiler(program).walk()
