"""M9.4 figure redraws: each figure is written as an editable draw.io file and a PNG drawn with matplotlib.

    python figures.py OUTDIR [NAME ...]      # all figures, or only the named ones

Layout is in draw.io pixels (y grows downward); the PNG uses the same numbers, so both files match.
Open a .drawio at app.diagrams.net or in draw.io desktop to edit and re-export.
"""
import sys, os, html
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse, Polygon, Rectangle, Arc

FONT = "Arial"


class Fig:
    def __init__(self, w, h):
        self.w, self.h, self.cells, self.n = w, h, [], 2

    def _id(self):
        self.n += 1
        return f"c{self.n}"

    def box(self, x, y, w, h, text, fill="#ffffff", stroke="#000000", color="#000000", bold=False, size=11,
            rounded=True, valign="middle", shape="rect"):
        """shape: rect | ellipse | rhombus | para (input/output) | cylinder (database) | actor (UML stick figure)."""
        cid = self._id()
        self.cells.append(dict(kind="box", id=cid, x=x, y=y, w=w, h=h, text=text, fill=fill, stroke=stroke,
                               color=color, bold=bold, size=size, rounded=rounded, valign=valign, shape=shape))
        return cid

    def node(self, cx, y, w, h, text, shape="rect", size=10):
        """A flowchart or use-case node placed by its centre x and top y."""
        self.box(cx - w / 2, y, w, h, text, shape=shape, size=size)

    def arrow(self, x1, y1, x2, y2, color="#000000", width=1.5):
        self.cells.append(dict(kind="arrow", id=self._id(), x1=x1, y1=y1, x2=x2, y2=y2, color=color, width=width))

    def text(self, x, y, text, size=10, bold=False, w=40, h=16):
        """Free text centred on (x, y), no border."""
        self.box(x - w / 2, y - h / 2, w, h, text, fill="none", stroke="none", size=size, bold=bold, rounded=False)

    def line(self, pts, start="none", end="none", dashed=False, width=1.5):
        """Polyline through pts. start/end: none | arrow | one | many (crow's foot)."""
        self.cells.append(dict(kind="line", id=self._id(), pts=pts, start=start, end=end, dashed=dashed,
                               width=width))

    def table(self, x, y, w, title, rows, methods=None, keys=None, row_h=22):
        """An ERD entity (keys: PK/FK column) or a UML class (methods section). Returns (x, y, w, h)."""
        h = 26 + row_h * len(rows) + (8 + row_h * len(methods) + 6 if methods is not None else 6)
        self.box(x, y, w, h, "", rounded=False)
        self.box(x, y, w, 26, title, bold=True, rounded=False)
        kw = 30 if keys else 0
        for i, r in enumerate(rows):
            ry = y + 26 + i * row_h
            if keys:
                self.box(x, ry, kw, row_h, keys[i], fill="none", stroke="none", bold=bool(keys[i]), rounded=False)
            self.box(x + kw + 6, ry, w - kw - 6, row_h, r, fill="none", stroke="none", rounded=False,
                     bold=bool(keys and keys[i]), size=10)
            self.cells[-1]["align"] = "left"
        if methods is not None:
            my = y + 26 + row_h * len(rows) + 4
            self.line([(x, my), (x + w, my)], width=1)
            for i, m in enumerate(methods):
                self.box(x + 6, my + 4 + i * row_h, w - 6, row_h, m, fill="none", stroke="none", rounded=False,
                         size=10)
                self.cells[-1]["align"] = "left"
        return (x, y, w, h)

    # ---------------------------------------------------------------- draw.io
    def drawio(self, path, name):
        out = ['<mxfile host="TheraQuest M9.4"><diagram name="%s"><mxGraphModel dx="0" dy="0" grid="1" gridSize="10" '
               'page="1" pageWidth="%d" pageHeight="%d"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
               % (html.escape(name), self.w, self.h)]
        for c in self.cells:
            if c["kind"] == "box":
                style = ("rounded=%d;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;fontColor=%s;fontSize=%d;"
                         "fontFamily=%s;verticalAlign=%s;%s" % (1 if c["rounded"] else 0, c["fill"], c["stroke"],
                         c["color"], c["size"], FONT, "top" if c["valign"] == "top" else "middle",
                         "fontStyle=1;" if c["bold"] else ""))
                style += {"rect": "", "ellipse": "ellipse;", "rhombus": "rhombus;",
                          "para": "shape=parallelogram;perimeter=parallelogramPerimeter;size=0.12;",
                          "cylinder": "shape=cylinder3;boundedLbl=1;size=10;",
                          "actor": "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;"}[c["shape"]]
                if c.get("align") == "left":
                    style += "align=left;spacingLeft=2;"
                val = html.escape(c["text"]).replace("\n", "&lt;br&gt;")
                out.append('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1"><mxGeometry x="%g" y="%g" '
                           'width="%g" height="%g" as="geometry"/></mxCell>' % (c["id"], val, style, c["x"], c["y"],
                                                                                c["w"], c["h"]))
            elif c["kind"] == "line":
                mark = {"none": "none", "arrow": "classic", "one": "ERmandOne", "many": "ERmany"}
                style = ("html=1;rounded=0;endArrow=%s;startArrow=%s;endFill=1;startFill=1;strokeWidth=%g;"
                         "strokeColor=#000000;%s" % (mark[c["end"]], mark[c["start"]], c["width"],
                                                     "dashed=1;" if c["dashed"] else ""))
                (x1, y1), (x2, y2) = c["pts"][0], c["pts"][-1]
                mid = "".join('<mxPoint x="%g" y="%g"/>' % p for p in c["pts"][1:-1])
                out.append('<mxCell id="%s" style="%s" edge="1" parent="1"><mxGeometry relative="1" as="geometry">'
                           '<mxPoint x="%g" y="%g" as="sourcePoint"/><mxPoint x="%g" y="%g" as="targetPoint"/>'
                           '%s</mxGeometry></mxCell>' % (c["id"], style, x1, y1, x2, y2,
                                                       '<Array as="points">%s</Array>' % mid if mid else ""))
            else:
                style = "endArrow=classic;html=1;strokeWidth=%g;strokeColor=%s;" % (c["width"], c["color"])
                out.append('<mxCell id="%s" style="%s" edge="1" parent="1"><mxGeometry relative="1" as="geometry">'
                           '<mxPoint x="%g" y="%g" as="sourcePoint"/><mxPoint x="%g" y="%g" as="targetPoint"/>'
                           '</mxGeometry></mxCell>' % (c["id"], style, c["x1"], c["y1"], c["x2"], c["y2"]))
        out.append("</root></mxGraphModel></diagram></mxfile>")
        open(path, "w", encoding="utf8").write("".join(out))

    # ---------------------------------------------------------------- PNG
    def png(self, path, dpi=200):
        fig = plt.figure(figsize=(self.w / 100, self.h / 100), dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, self.w); ax.set_ylim(self.h, 0); ax.axis("off")
        for c in self.cells:
            if c["kind"] == "box":
                x, y, w, h, s = c["x"], c["y"], c["w"], c["h"], c["shape"]
                kw = dict(fc=c["fill"], ec=c["stroke"], lw=1.2)
                if s == "rect":
                    pad = min(8, w / 8, h / 8) if c["rounded"] else 0
                    ax.add_patch(FancyBboxPatch((x + pad, y + pad), w - 2 * pad, h - 2 * pad,
                                                boxstyle="round,pad=%g" % pad if pad else "square,pad=0", **kw))
                elif s == "ellipse":
                    ax.add_patch(Ellipse((x + w / 2, y + h / 2), w, h, **kw))
                elif s == "rhombus":
                    ax.add_patch(Polygon([(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)], **kw))
                elif s == "para":
                    k = w * 0.12
                    ax.add_patch(Polygon([(x + k, y), (x + w, y), (x + w - k, y + h), (x, y + h)], **kw))
                elif s == "cylinder":
                    ax.add_patch(Rectangle((x, y + 8), w, h - 16, fc=c["fill"], ec="none"))
                    ax.plot([x, x], [y + 8, y + h - 8], color="black", lw=1.2)
                    ax.plot([x + w, x + w], [y + 8, y + h - 8], color="black", lw=1.2)
                    ax.add_patch(Arc((x + w / 2, y + h - 8), w, 16, theta1=180, theta2=360, color="black", lw=1.2))
                    ax.add_patch(Ellipse((x + w / 2, y + 8), w, 16, **kw))
                elif s == "actor":
                    cx = x + w / 2
                    ax.add_patch(Ellipse((cx, y + h * 0.12), h * 0.22, h * 0.22, fc="white", ec="black", lw=1.2))
                    for a, b in (((cx, y + h * 0.23), (cx, y + h * 0.62)), ((x, y + h * 0.36), (x + w, y + h * 0.36)),
                                 ((cx, y + h * 0.62), (x, y + h)), ((cx, y + h * 0.62), (x + w, y + h))):
                        ax.plot([a[0], b[0]], [a[1], b[1]], color="black", lw=1.2)
                    ax.text(cx, y + h + 6 + 8 * (c["text"].count(chr(10)) + 1), c["text"], ha="center", va="center", fontsize=c["size"] * 0.72, family=FONT)
                    continue
                ty = c["y"] + (14 + c["size"]) if c["valign"] == "top" else c["y"] + c["h"] / 2
                left = c.get("align") == "left"
                ax.text(c["x"] + 2 if left else c["x"] + c["w"] / 2, ty, c["text"], ha="left" if left else "center",
                        va="center", color=c["color"],
                        fontsize=c["size"] * 0.72, fontweight="bold" if c["bold"] else "normal", family=FONT,
                        linespacing=1.25)
            elif c["kind"] == "line":
                xs, ys = zip(*c["pts"])
                ax.plot(xs, ys, color="black", lw=c["width"], ls=(0, (5, 4)) if c["dashed"] else "-",
                        solid_capstyle="butt")
                for kind, tip, prev in ((c["end"], c["pts"][-1], c["pts"][-2]), (c["start"], c["pts"][0], c["pts"][1])):
                    _mark(ax, kind, tip, prev, c["width"])
            else:
                ax.add_patch(FancyArrowPatch((c["x1"], c["y1"]), (c["x2"], c["y2"]), arrowstyle="-|>",
                                             mutation_scale=12, color=c["color"], lw=c["width"]))
        fig.savefig(path, dpi=dpi, facecolor="white")
        plt.close(fig)


def _mark(ax, kind, tip, prev, lw):
    """Line end markers in the PNG: arrow head, crow's foot (many) or double bar (one)."""
    if kind == "none":
        return
    (tx, ty), (px, py) = tip, prev
    d = ((px - tx) ** 2 + (py - ty) ** 2) ** 0.5 or 1
    ux, uy = (px - tx) / d, (py - ty) / d          # from the tip back along the line
    vx, vy = -uy, ux
    seg = lambda a, b: ax.plot([a[0], b[0]], [a[1], b[1]], color="black", lw=lw)
    if kind == "arrow":
        ax.add_patch(FancyArrowPatch((tx + ux * 14, ty + uy * 14), (tx, ty), arrowstyle="-|>", mutation_scale=12,
                                     color="black", lw=lw))
    elif kind == "many":
        b = (tx + ux * 12, ty + uy * 12)
        for s in (-7, 0, 7):
            seg(b, (tx + vx * s, ty + vy * s))
        c = (tx + ux * 16, ty + uy * 16)
        seg((c[0] + vx * 7, c[1] + vy * 7), (c[0] - vx * 7, c[1] - vy * 7))
    elif kind == "one":
        for k in (8, 14):
            c = (tx + ux * k, ty + uy * k)
            seg((c[0] + vx * 7, c[1] + vy * 7), (c[0] - vx * 7, c[1] - vy * 7))


# -------------------------------------------------------------------- ERD (3.5.2.1)
def erd():
    f = Fig(1090, 610)
    Y = 40
    f.table(0, Y + 150, 180, "Physical Therapist", ["therapist_id", "name", "license_no"], keys=["PK", "", ""])
    f.table(270, Y, 190, "Patient", ["patient_id", "therapist_id", "program_id", "code (e.g. P-001)", "name",
                                     "condition"], keys=["PK", "FK", "FK", "", "", ""])
    f.table(270, Y + 230, 190, "Rehabilitation Program", ["program_id", "therapist_id", "name", "description"],
            keys=["PK", "FK", "", ""])
    f.table(560, Y, 190, "Session", ["session_id", "patient_id", "program_id", "started_at", "ended_at", "status",
                                     "points", "stars"], keys=["PK", "FK", "FK", "", "", "", "", ""])
    f.table(560, Y + 300, 190, "Exercise", ["exercise_id", "program_id", "code", "name", "joint", "target_angle",
                                           "tolerance", "safety_max", "sets", "reps"],
            keys=["PK", "FK", "", "", "", "", "", "", "", ""])
    f.table(850, Y, 230, "Adherence Record", ["adherence_id", "patient_id", "session_id", "session_date",
                                             "status (complete, partial, missed)"], keys=["PK", "FK", "FK", "", ""])
    f.table(850, Y + 240, 230, "Performance Record", ["record_id", "session_id", "exercise_id", "valid_reps",
                                                     "avg_accuracy", "mean_angle_error", "feedback_log"],
            keys=["PK", "FK", "FK", "", "", "", ""])
    L = lambda pts, a="one", b="many": f.line([(x, y + Y) for x, y in pts], start=a, end=b)
    L([(180, 200), (215, 200), (215, 50), (270, 50)])                 # therapist 1 - n patients
    L([(180, 250), (235, 250), (235, 290), (270, 290)])               # therapist 1 - n programs
    L([(460, 60), (560, 60)])                                         # patient 1 - n sessions
    L([(460, 280), (510, 280), (510, 110), (560, 110)])               # program 1 - n sessions
    L([(460, 320), (530, 320), (530, 380), (560, 380)])               # program 1 - n exercises
    L([(750, 60), (850, 60)], "one", "one")                           # session 1 - 1 adherence record
    L([(365, 0), (365, -25), (965, -25), (965, 0)])                   # patient 1 - n adherence records (missed days too)
    L([(750, 200), (800, 200), (800, 300), (850, 300)])               # session 1 - n performance records
    L([(750, 450), (820, 450), (820, 350), (850, 350)])               # exercise 1 - n performance records
    return f


# -------------------------------------------------------------------- class diagram (3.7.2.1)
def classes():
    f = Fig(1040, 680)
    T = f.table
    T(760, 0, 170, "VRSystem", ["- system_name: string"],
      ["+ trackMotion()", "+ evaluateRep()", "+ giveFeedback()", "+ pauseSession()", "+ storeData()"])
    T(280, 110, 170, "Patient", ["- patient_id: int", "- code: string", "- name: string", "- condition: string",
                                 "- xp: int"], ["+ startSession()", "+ performExercise()", "+ viewProgress()"])
    T(0, 250, 170, "PhysicalTherapist", ["- therapist_id: int", "- name: string", "- license_no: string"],
      ["+ assignProgram()", "+ monitorProgress()", "+ viewReports()"])
    T(560, 200, 170, "Session", ["- session_id: int", "- started_at: datetime", "- ended_at: datetime",
                                 "- status: string", "- points: int", "- stars: int"],
      ["+ start()", "+ end()", "+ calculateCompletion()"])
    T(850, 220, 180, "PerformanceRecord", ["- record_id: int", "- valid_reps: int", "- avg_accuracy: float",
                                           "- mean_angle_error: float", "- feedback_log: string"],
      ["+ generateScore()", "+ storeFeedback()"])
    T(850, 450, 180, "AdherenceRecord", ["- adherence_id: int", "- session_date: date", "- status: string"],
      ["+ evaluateCompletion()"])
    T(280, 440, 170, "RehabilitationProgram", ["- program_id: int", "- name: string", "- description: string",
                                               "- schedule_days: string"], ["+ addExercise()", "+ removeExercise()"])
    T(560, 470, 170, "Exercise", ["- exercise_id: int", "- name: string", "- joint: string",
                                  "- target_angle: float", "- tolerance: float", "- safety_max: float"],
      ["+ validateMovement()"])
    def A(pts, m1, m2):
        f.line(pts)
        (x1, y1), (x2, y2) = pts[0], pts[-1]
        f.text(x1 + (12 if pts[1][0] > x1 else -12 if pts[1][0] < x1 else 12), y1 + (-9 if pts[1][1] == y1 else 10), m1)
        f.text(x2 + (-16 if pts[-2][0] < x2 else 16 if pts[-2][0] > x2 else 14), y2 + (-9 if pts[-2][1] == y2 else -10), m2)
    A([(170, 330), (220, 330), (220, 180), (280, 180)], "1", "1..*")
    A([(170, 400), (220, 400), (220, 520), (280, 520)], "1", "1..*")
    A([(450, 180), (500, 180), (500, 260), (560, 260)], "1", "1..*")
    A([(365, 326), (365, 440)], "1", "1")
    A([(450, 560), (560, 560)], "1", "1..*")
    f.line([(645, 438), (645, 470)])
    f.text(625, 450, "1..*")
    f.text(667, 458, "1..*")
    A([(730, 280), (790, 280), (790, 300), (850, 300)], "1", "1..*")
    A([(730, 400), (800, 400), (800, 500), (850, 500)], "1", "1")
    f.line([(760, 60), (645, 60), (645, 200)], end="arrow", dashed=True)
    f.line([(900, 172), (900, 220)], end="arrow", dashed=True)
    return f


# -------------------------------------------------------------------- system flowchart (3.6.1.1)
def flowchart():
    f = Fig(760, 1400)
    N, A, T = f.node, (lambda pts: f.line(pts, end="arrow")), f.text
    P, Q = 220, 580                                   # patient and therapist columns
    N(400, 10, 110, 46, "Start", "ellipse")
    N(400, 86, 160, 100, "Who is using\nthe system?", "rhombus")
    A([(400, 56), (400, 86)])
    A([(320, 136), (P, 136), (P, 200)]); T(280, 126, "Patient", w=60)
    A([(480, 136), (Q, 136), (Q, 200)]); T(530, 126, "Therapist", w=70)
    # Patient: the game opens the program by patient code (no password)
    N(P, 200, 180, 40, "Open VR Application")
    N(P, 270, 180, 46, "Load Assigned Program\nby Patient Code")
    N(P, 346, 180, 46, "Start VR Rehabilitation\nSession")
    N(P, 422, 180, 36, "Perform Exercise")
    N(P, 488, 190, 44, "Capture Body Movement", "para")
    N(P, 562, 150, 96, "Is the Locked\nPatient in View?", "rhombus")
    N(400, 590, 120, 40, "Pause Session")
    N(P, 690, 180, 44, "Analyze Motion\n(Computer Vision)")
    N(P, 764, 150, 96, "Is Movement\nCorrect?", "rhombus")
    N(400, 792, 120, 40, "Show Corrective\nPrompt")
    N(P, 890, 180, 36, "Update Score")
    N(P, 950, 150, 96, "All Exercises\nCompleted?", "rhombus")
    N(400, 978, 140, 40, "Session Completed")
    N(400, 1050, 180, 44, "Generate Performance\nData")
    N(400, 1124, 180, 44, "Record Adherence\nStatus")
    N(400, 1198, 180, 44, "Store Performance\nData")
    N(590, 1188, 100, 64, "TheraQuest\nDatabase", "cylinder")
    N(400, 1272, 180, 40, "Display Results")
    N(400, 1342, 110, 46, "End", "ellipse")
    for y1, y2 in ((240, 270), (316, 346), (392, 422), (458, 488), (532, 562), (734, 764), (926, 950)):
        A([(P, y1), (P, y2)])
    A([(P, 658), (P, 690)]); T(P + 14, 672, "Yes", w=30)
    A([(295, 610), (340, 610)]); T(318, 600, "No", w=24)
    A([(400, 590), (400, 516), (308, 516)])           # resumes when the patient is tracked again
    A([(P, 860), (P, 890)]); T(P + 14, 874, "Yes", w=30)
    A([(295, 812), (340, 812)]); T(318, 802, "No", w=24)
    A([(460, 812), (470, 812), (470, 498), (312, 498)])
    A([(145, 998), (40, 998), (40, 440), (130, 440)]); T(92, 988, "No", w=24)
    A([(295, 998), (330, 998)]); T(312, 988, "Yes", w=30)
    for y1, y2 in ((1018, 1050), (1094, 1124), (1168, 1198), (1242, 1272), (1312, 1342)):
        A([(400, y1), (400, y2)])
    A([(490, 1220), (540, 1220)])
    # Therapist: password sign-in on the dashboard
    N(Q, 200, 180, 40, "Sign In with Password")
    N(Q, 266, 180, 40, "Validate Credentials")
    N(Q, 332, 120, 80, "Valid?", "rhombus")
    N(Q, 440, 180, 40, "Display Dashboard")
    N(Q, 506, 130, 90, "Select Action?", "rhombus")
    N(535, 640, 100, 46, "Retrieve Data\nfrom Database")
    N(665, 640, 100, 46, "Retrieve Data\nfrom Database")
    N(535, 712, 100, 44, "Display\nPrograms")
    N(665, 712, 100, 44, "Display\nReports")
    N(600, 790, 110, 44, "End", "ellipse")
    A([(Q, 240), (Q, 266)]); A([(Q, 306), (Q, 332)])
    A([(Q, 412), (Q, 440)]); T(Q + 16, 426, "Yes", w=30)
    A([(640, 372), (700, 372), (700, 220), (670, 220)]); T(670, 362, "No", w=24)
    A([(Q, 480), (Q, 506)])
    f.line([(Q, 596), (Q, 612)])
    A([(Q, 612), (535, 612), (535, 640)]); T(530, 600, "Assign program", w=100, size=9)
    A([(Q, 612), (665, 612), (665, 640)]); T(672, 600, "View reports", w=90, size=9)
    A([(535, 686), (535, 712)]); A([(665, 686), (665, 712)])
    A([(535, 756), (535, 812), (545, 812)]); A([(665, 756), (665, 812), (655, 812)])
    return f


def flowchart_h():
    """The same flowchart laid out left to right (human request 2026-11-26): patient path on top, therapist below."""
    f = Fig(1860, 720)
    N, T = f.node, f.text
    A = lambda pts: f.line(pts, end="arrow")
    R = lambda x, cy, w, t, s="rect", h=56: N(x + w / 2, cy - h / 2, w, h, t, s)   # placed by left edge and centre y
    R(20, 360, 90, "Start", "ellipse", 46)
    R(140, 360, 140, "Who is using\nthe system?", "rhombus", 110)
    A([(110, 360), (140, 360)])
    A([(210, 305), (210, 110), (250, 110)]); T(180, 200, "Patient", w=60)
    A([(210, 415), (210, 600), (250, 600)]); T(176, 510, "Therapist", w=70)
    # Patient path, row 1 (left to right)
    y = 110
    R(250, y, 130, "Open VR\nApplication")
    R(410, y, 130, "Load Assigned\nProgram by\nPatient Code", h=60)
    R(570, y, 130, "Start VR\nRehabilitation\nSession", h=60)
    R(730, y, 130, "Perform Exercise")
    R(890, y, 150, "Capture Body\nMovement", "para")
    R(1070, y, 130, "Is the Locked\nPatient in\nView?", "rhombus", 100)
    R(1230, y, 130, "Analyze Motion\n(Computer\nVision)", h=60)
    R(1390, y, 130, "Is Movement\nCorrect?", "rhombus", 100)
    R(1550, y, 120, "Update Score")
    R(1700, y, 130, "All Exercises\nCompleted?", "rhombus", 100)
    for x1, x2 in ((380, 410), (540, 570), (700, 730), (860, 893), (1040, 1070), (1520, 1550), (1670, 1700)):
        A([(x1, y), (x2, y)])
    A([(1200, y), (1230, y)]); T(1215, y - 10, "Yes", w=30)
    A([(1360, y), (1390, y)])
    R(1070, 220, 130, "Pause Session", h=40)
    A([(1135, 160), (1135, 200)]); T(1150, 180, "No", w=24)
    A([(1070, 220), (965, 220), (965, 138)])                 # resumes when the patient is tracked again
    R(1390, 220, 130, "Show Corrective\nPrompt", h=40)
    A([(1455, 160), (1455, 200)]); T(1470, 180, "No", w=24)
    T(1535, y - 10, "Yes", w=30)
    A([(1455, 240), (1455, 265), (920, 265), (920, 138)])
    A([(1765, 60), (1765, 30), (795, 30), (795, 82)]); T(1785, 45, "No", w=24)
    A([(1765, 160), (1765, 335)]); T(1785, 250, "Yes", w=30)
    # Patient path, row 2 (right to left)
    y = 360
    R(1700, y, 130, "Session\nCompleted", h=50)
    R(1520, y, 140, "Generate\nPerformance Data", h=50)
    R(1340, y, 140, "Record Adherence\nStatus", h=50)
    R(1160, y, 140, "Store Performance\nData", h=50)
    R(980, y, 140, "Display Results", h=50)
    R(860, y, 90, "End", "ellipse", 46)
    for x1, x2 in ((1700, 1660), (1520, 1480), (1340, 1300), (1160, 1120), (980, 950)):
        A([(x1, y), (x2, y)])
    R(1180, 452, 100, "TheraQuest\nDatabase", "cylinder", 64)
    A([(1230, 385), (1230, 420)])
    # Therapist path (left to right)
    y = 600
    R(250, y, 130, "Sign In with\nPassword")
    R(410, y, 130, "Validate\nCredentials")
    R(570, y, 120, "Valid?", "rhombus", 90)
    R(720, y, 130, "Display\nDashboard")
    R(880, y, 130, "Select\nAction?", "rhombus", 100)
    for x1, x2 in ((380, 410), (540, 570), (850, 880)):
        A([(x1, y), (x2, y)])
    A([(690, y), (720, y)]); T(705, y - 10, "Yes", w=30)
    A([(630, 555), (630, 530), (315, 530), (315, 572)]); T(648, 542, "No", w=24)
    for cy, lab, show in ((520, "Assign program", "Display\nPrograms"), (680, "View reports", "Display\nReports")):
        R(1040, cy, 120, "Retrieve Data\nfrom Database", h=50)
        R(1190, cy, 120, show, h=50)
        A([(1160, cy), (1190, cy)])
        A([(945, 550 if cy < y else 650), (945, cy), (1040, cy)]); T(990, cy - 10, lab, w=90, size=9)
        A([(1310, cy), (1385, cy), (1385, y - 23 if cy < y else y + 23)])
    R(1340, y, 90, "End", "ellipse", 46)
    return f


def flowchart_l():
    """Left-to-right flowchart shaped for its own landscape page (9 x 6 in text area): large labels, rows that snake
    so the figure is about 1.5 times as wide as it is high (human choice 2026-11-26)."""
    f = Fig(1460, 950)
    S = 17                                            # label size: about 7.5 pt once scaled to the 9 in text width
    T = lambda x, y, t, w=50: f.text(x, y, t, w=w, size=15)
    A = lambda pts: f.line(pts, end="arrow")
    def R(x, cy, w, t, s="rect", h=70):
        f.node(x + w / 2, cy - h / 2, w, h, t, s, size=S)
    R(165, 30, 90, "Start", "ellipse", 46)
    R(140, 130, 150, "Who is using\nthe system?", "rhombus", 120)
    A([(210, 53), (210, 70)])
    # Row 1, patient (left to right)
    y = 130
    R(320, y, 150, "Open VR\nApplication")
    R(500, y, 150, "Load Program\nby Patient\nCode", h=80)
    R(680, y, 150, "Start VR\nSession")
    R(860, y, 150, "Perform\nExercise")
    R(1040, y, 170, "Capture Body\nMovement", "para")
    A([(290, y), (320, y)]); f.text(303, y + 22, "Patient", w=46, size=13)
    for x1, x2 in ((470, 500), (650, 680), (830, 860), (1010, 1044)):
        A([(x1, y), (x2, y)])
    # Row 2, patient (right to left)
    y = 330
    R(1025, y, 200, "Is the Locked\nPatient in\nView?", "rhombus", 130)
    A([(1125, 165), (1125, 265)])
    R(1260, y, 150, "Pause\nSession")
    A([(1225, y), (1260, y)]); T(1242, y - 14, "No", 30)
    A([(1335, y - 35), (1335, 145), (1206, 145)])     # resumes when the patient is tracked again
    R(850, y, 150, "Analyze Motion\n(Computer\nVision)", h=80)
    A([(1025, y), (1000, y)]); T(1012, y - 14, "Yes", 30)
    R(630, y, 160, "Is Movement\nCorrect?", "rhombus", 120)
    A([(850, y), (790, y)])
    R(630, 450, 160, "Show Corrective\nPrompt", h=60)
    A([(710, 390), (710, 420)]); T(728, 405, "No", 30)
    A([(790, 450), (1440, 450), (1440, 115), (1220, 115)])
    R(420, y, 150, "Update\nScore")
    A([(630, y), (570, y)]); T(600, y - 14, "Yes", 36)
    R(200, y, 160, "All Exercises\nCompleted?", "rhombus", 120)
    A([(420, y), (360, y)])
    A([(280, 270), (280, 225), (935, 225), (935, 165)]); T(298, 248, "No", 30)
    # Row 3, end of the session (left to right)
    y = 560
    A([(280, 390), (280, y - 35)]); T(300, 480, "Yes", 36)
    R(205, y, 150, "Session\nCompleted")
    R(390, y, 150, "Generate\nPerformance\nData", h=80)
    R(570, y, 150, "Record\nAdherence\nStatus", h=80)
    R(750, y, 150, "Store\nPerformance\nData", h=80)
    R(930, y, 150, "Display\nResults")
    R(1110, y, 90, "End", "ellipse", 50)
    for x1, x2 in ((355, 390), (540, 570), (720, 750), (900, 930), (1080, 1110)):
        A([(x1, y), (x2, y)])
    R(775, 650, 100, "TheraQuest\nDatabase", "cylinder", 70)
    A([(825, 600), (825, 615)])
    # Row 4, therapist (left to right)
    y = 820
    A([(140, 130), (50, 130), (50, y), (80, y)]); T(84, 118, "Therapist", 90)
    R(80, y, 150, "Sign In with\nPassword")
    R(260, y, 150, "Validate\nCredentials")
    R(440, y, 130, "Valid?", "rhombus", 100)
    R(610, y, 150, "Display\nDashboard")
    R(790, y, 150, "Select\nAction?", "rhombus", 120)
    for x1, x2 in ((230, 260), (410, 440), (760, 790)):
        A([(x1, y), (x2, y)])
    A([(570, y), (610, y)]); T(590, y - 14, "Yes", 36)
    A([(505, y - 50), (505, y - 75), (155, y - 75), (155, y - 35)]); T(522, y - 62, "No", 30)
    for cy, lab, show in ((730, "Assign program", "Display\nPrograms"), (910, "View reports", "Display\nReports")):
        R(990, cy, 150, "Retrieve Data\nfrom Database")
        R(1170, cy, 140, show)
        A([(1140, cy), (1170, cy)])
        A([(865, y - 60 if cy < y else y + 60), (865, cy), (990, cy)]); T(925, cy - 14, lab, 120)
        A([(1310, cy), (1395, cy), (1395, y - 25 if cy < y else y + 25)])
    R(1350, y, 90, "End", "ellipse", 50)
    return f


# -------------------------------------------------------------------- use case diagram (3.5.1.1)
def usecase():
    f = Fig(1540, 780)
    f.box(210, 10, 1170, 760, "TheraQuest VR System", fill="#ffffff", bold=True, size=16, rounded=False, valign="top")
    for x, y, w, h, t in ((260, 70, 265, 560, "Patient Functions"), (600, 70, 420, 670, "System Internal Functions"),
                          (1090, 120, 265, 550, "Therapist Functions")):
        f.box(x, y, w, h, "", rounded=False)
        f.box(x, y, 150, 26, t, bold=True, size=10, rounded=False)
    U = lambda cx, cy, t, w=150, h=76: f.node(cx, cy, w, h, t, "ellipse")
    for cy, t in ((120, "Start VR Rehabilitation\nSession"), (230, "Perform Prescribed\nExercises"),
                  (340, "Receive Real-Time\nFeedback"), (450, "View Scores / Progress")):
        U(393, cy, t, 220, 86)
        f.line([(60, 375), (283, cy + 43)], end="arrow")
    for cy, t in ((170, "Sign In with Password"), (270, "Assign Rehabilitation\nProgram"),
                  (370, "Monitor Session\nCompletion"), (470, "View Patient\nPerformance Reports"),
                  (570, "Approve Next Phase")):
        U(1222, cy, t, 220, 76)
        f.line([(1440, 375), (1332, cy + 38)], end="arrow")
    for cy, t in ((100, "Load Program by\nPatient Code"), (200, "Track Body\nMovements"),
                  (300, "Keep Tracking the\nPatient (Patient Lock)"), (400, "Evaluate Exercise\nAccuracy"),
                  (520, "Generate\nPerformance Data"), (640, "Corrective Prompts")):
        U(690, cy, t)
    for cy, t in ((200, "Validate Session\nCompletion"), (360, "Store Patient\nRecords"),
                  (520, "Recommend Next\nPhase")):
        U(920, cy, t)
    f.box(20, 335, 40, 80, "Patient", shape="actor")
    f.box(1440, 335, 40, 80, "Physical Therapist", shape="actor")
    inc = lambda pts, lab, at: (f.line(pts, end="arrow", dashed=True), f.text(at[0], at[1], lab, w=80, size=9))
    inc([(503, 163), (615, 138)], "<<include>>", (560, 140))
    inc([(503, 273), (615, 238)], "<<include>>", (560, 244))
    inc([(690, 276), (690, 300)], "<<include>>", (735, 288))
    inc([(503, 273), (615, 438)], "<<include>>", (548, 330))
    inc([(503, 383), (615, 438)], "<<include>>", (566, 420))
    inc([(615, 678), (560, 678), (560, 400), (500, 400)], "<<extend>>", (590, 560))
    inc([(765, 130), (1060, 130), (1060, 308), (1112, 308)], "assigned program", (912, 120))
    A = lambda pts: f.line(pts, end="arrow")
    A([(690, 476), (690, 520)])                        # evaluate -> generate data
    A([(765, 558), (845, 398)])                        # generate -> store
    A([(615, 558), (503, 493)])                        # generate -> patient scores
    A([(765, 438), (845, 238)])                        # evaluate -> validate completion
    A([(920, 436), (920, 520)])                        # store -> recommend next phase
    A([(995, 238), (1112, 408)])                       # validate -> monitor
    A([(995, 398), (1112, 508)])                       # store -> reports
    A([(995, 558), (1112, 608)])                       # recommend -> therapist approves
    return f


# -------------------------------------------------------------------- Level 1 DFD (3.5.3.2)
def dfd1():
    f = Fig(860, 410)
    Y = "#f6eaa0"
    def proc(x, y, w, n, t):
        f.box(x, y, w, 80, "", fill=Y)
        f.line([(x, y + 22), (x + w, y + 22)], width=1)
        f.line([(x + 24, y), (x + 24, y + 22)], width=1)
        f.text(x + 12, y + 11, str(n), bold=True, w=20)
        f.box(x, y + 22, w, 58, t, fill="none", stroke="none", rounded=False)
    def ext(x, y, w, h, t):
        f.box(x, y, w, h, t, fill=Y, rounded=False, bold=True)
    ext(20, 25, 120, 40, "Patient")
    ext(600, 110, 110, 45, "Physical Therapist")
    f.box(620, 183, 120, 40, "Database", fill=Y, rounded=False)
    f.box(620, 183, 30, 40, "D", fill="#cccccc", rounded=False)
    proc(0, 165, 130, 1, "Motion Tracking")
    proc(300, 165, 170, 2, "Exercise Evaluation")
    proc(275, 0, 140, 3, "Feedback Generation")
    proc(310, 315, 155, 4, "Adherence Monitoring")
    A, T = (lambda pts: f.line(pts, end="arrow", width=1)), (lambda x, y, t, w=150: f.text(x, y, t, w=w, size=9))
    A([(80, 65), (80, 165)]); T(118, 120, "Movement Data\n(webcam)", 90)
    A([(130, 205), (300, 205)]); T(215, 192, "Processed Motion Data")
    A([(385, 165), (385, 80)]); T(340, 125, "Evaluation Results", 100)
    A([(275, 40), (140, 40)]); T(208, 30, "Real-Time Feedback", 110)
    A([(600, 132), (430, 132), (430, 165)]); T(515, 122, "Rehabilitation Parameters")
    A([(470, 200), (620, 200)]); T(545, 190, "Performance Metrics", 120)
    A([(385, 245), (385, 315)]); T(435, 280, "Performance Data", 100)
    A([(465, 355), (680, 355), (680, 223)]); T(570, 345, "Adherence Records", 110)
    A([(740, 203), (765, 203), (765, 132), (710, 132)]); T(812, 170, "Performance &\nAdherence\nReports", 80)
    return f


# -------------------------------------------------------------------- four-layer architecture (3.6.2.1)
def architecture():
    f = Fig(1000, 800)
    f.box(140, 5, 720, 40, "TheraQuest VR System Architecture", fill="none", stroke="none", bold=True, size=16,
          rounded=False)
    layers = [
        ("Presentation Layer", "#5b3fa0", 60, [
            ("VR Environment", "Headset or laptop view,\nguided exercises,\ncoach and HUD"),
            ("Gamification", "Points, stars, badges,\nlevels, combo streaks"),
            ("Therapist Dashboard", "Caseload, 14-day calendar,\nreports, attention flags")]),
        ("Application Layer", "#1f7a4d", 240, [
            ("Therapist Sign-In", "Password on the dashboard;\nthe game opens a program\nby patient code"),
            ("Session Management", "Start, pause and end\nsessions; upload results"),
            ("Program Management", "Assign exercises, protocols\nand phases; approve the\nnext phase")]),
        ("Processing Layer", "#c25f00", 420, [
            ("Motion Tracking", "Webcam, MediaPipe Pose,\nPatient Lock,\njoint angles"),
            ("Exercise Evaluation", "Angle vs therapist target,\nrep counting,\nsafe-limit stop"),
            ("Feedback Generation", "Visual cues, sounds,\nsubtitles"),
            ("Adherence Monitoring", "Complete, partial or\nmissed per day")]),
        ("Data Layer", "#2a5db0", 600, [
            ("Patient & Session", "Patient code; name on\nthe therapist's\ncomputer only"),
            ("Performance", "Per exercise and per\nrepetition records"),
            ("Adherence", "Daily status and\nadherence records"),
            ("Programs & Exercises", "Programs, protocols,\n29-exercise library"),
            ("Storage", "SQLite on the clinic\ncomputer, encrypted\nbackup")]),
    ]
    for name, col, y, comps in layers:
        h = 150
        f.box(140, y, 720, h, "", fill="#ffffff", stroke=col)
        f.box(140, y, 720, 30, name, fill=col, stroke=col, color="#ffffff", bold=True, size=12, rounded=False)
        n = len(comps)
        cw = (720 - 20 - 10 * (n - 1)) / n
        for i, (t, d) in enumerate(comps):
            x = 150 + i * (cw + 10)
            f.box(x, y + 40, cw, 100, "", stroke=col)
            f.box(x, y + 44, cw, 20, t, fill="none", stroke="none", bold=True, size=10, color=col, rounded=False)
            f.box(x, y + 66, cw, 70, d, fill="none", stroke="none", size=9, rounded=False)
        if y < 600:
            f.line([(500, y + h), (500, y + 180)], end="arrow", width=2)
    f.box(40, 300, 40, 80, "Patient", shape="actor")
    f.box(920, 300, 40, 80, "Physical\nTherapist", shape="actor")
    f.line([(60, 290), (60, 135), (140, 135)], end="arrow")                 # patient uses the VR environment
    f.line([(60, 405), (60, 495), (140, 495)], end="arrow", dashed=True)     # webcam sees the patient
    f.text(95, 482, "webcam", w=60, size=9)
    f.line([(940, 290), (940, 135), (860, 135)], end="arrow")               # therapist uses the dashboard
    return f


# -------------------------------------------------------------------- module figures (3.6.3.x)
def module(title, fill, inputs, stages, outputs, stage_h=58):
    """Inputs on the left, the module block with its stages in the middle, outputs on the right (old layout)."""
    n = max(len(inputs), len(outputs))
    gap = 16
    top = 100
    body_h = len(stages) * stage_h + (len(stages) - 1) * 30
    row = max(90, (body_h + 20) // max(n, 1))
    h = max(top + body_h + 50, 80 + n * row + 40)
    f = Fig(720, h)
    bx, bw = 220, 280
    f.box(bx, 0, bw, h - 2, title, fill=fill, stroke="#000000", color="#ffffff", bold=True, size=11, valign="top")
    f.box(20, 30, 70, 30, "Inputs", rounded=False)
    f.box(630, 30, 70, 30, "Outputs", rounded=False)
    sx, sw = bx + 80, 120
    for i, s in enumerate(stages):
        y = top + i * (stage_h + 30)
        f.box(sx, y, sw, stage_h, s, fill=fill, stroke="#ffffff", color="#ffffff", bold=True, size=10)
        if i:
            f.arrow(sx + sw / 2, y - 30, sx + sw / 2, y, color="#ffffff", width=1.5)
    for i, t in enumerate(inputs):
        y = 100 + i * row
        f.box(0, y, 120, 58, t, size=10)
        f.arrow(120, y + 29, bx, y + 29)
    for i, t in enumerate(outputs):
        y = 100 + i * row
        f.box(610, y, 120, 58, t, size=10)
        f.arrow(bx + bw, y + 29, 610, y + 29)
    f.w = 735
    return f


FIGS = {"3.5.2.1 Entity Relationship Diagram": erd, "3.7.2.1 Class Diagram": classes,
        "3.6.1.1 System Flowchart": flowchart_l, "3.5.1.1 Use Case Diagram": usecase,
        "3.5.3.2 Data Flow Diagram": dfd1, "3.6.2.1 System Architecture": architecture}

FIGS["3.6.3.1 VR Environment Module"] = lambda: module(
    "VR Environment Module\nUnity Game Engine (C#)", "#2b2d31",
    ["VR Headset\nMeta Quest: head pose\nand controllers",
     "Body Movement\nJoint angles from the\nmotion tracking module",
     "Exercise Data\nFrom rehabilitation\nprogram",
     "Feedback Signals\nFrom processing\nmodules"],
    ["Scene Renderer\nDisplays 3D\nrehabilitation room",
     "Interaction Controller\nHead orientation,\ncontroller menus,\nre-centering",
     "Exercise Prompt\nDisplay\nShows instructions\nand task cues",
     "Feedback Overlay\nDisplays visual and\naudio feedback"],
    ["Immersive Scene\nRendered VR\nenvironment",
     "Exercise Prompts\nDisplayed to patient",
     "Real-time Feedback\nAudio and visual cues"])

FIGS["3.6.3.2 Motion Tracking Module"] = lambda: module(
    "Motion Tracking Module\nOpenCV / MediaPipe Pose, Python", "#c25f00",
    ["External Webcam\nRaw video frames,\nreal-time stream"],
    ["Frame Preprocessor\nResizes a copy of\nthe frame",
     "Pose Estimator\nDetects body\nlandmarks",
     "Patient Lock\nKeeps the first body;\npauses if replaced",
     "Landmark Smoother\nSteadies landmarks,\nbridges short gaps",
     "Joint Angle\nCalculator\nLimb angles and range",
     "Motion Data\nPackager"],
    ["Keypoint Coordinates\nBody landmark\npositions",
     "Joint Angle Data\nRange of motion\nvalues",
     "Patient Status\nPause when another\nperson takes over",
     "Processed Motion\nData\nSent to evaluation\nmodule"], stage_h=54)

FIGS["3.6.3.4 Feedback Generation Module"] = lambda: module(
    "Feedback Generation Module\nReal-time Response Engine", "#123e3f",
    ["Evaluation Results\nAccuracy scores,\nerror flags",
     "Movement Error Data\nSpecific joint\ndeviations",
     "Session Context\nCurrent exercise,\nprogress"],
    ["Feedback Decision\nEngine\nDetermines feedback\ntype",
     "Visual Cue Generator\nIn-VR overlays and\nhighlights",
     "Audio Prompt\nGenerator\nSound responses\nand subtitles",
     "Corrective Instruction\nEngine\nMovement correction\nguidance"],
    ["Visual Overlays\nDisplayed in VR\nenvironment",
     "Audio Prompts\nSounds via headset,\nwith subtitles",
     "Posture Fault\nPer repetition, logged\nto performance\ndatabase"])

FIGS["3.6.3.5 Gamification Module"] = lambda: module(
    "Gamification Module\nC# - Unity Game Engine", "#3e7d17",
    ["Accuracy Scores\nFrom evaluation\nmodule",
     "Repetition Count\nCompleted repetitions",
     "Session Progress\nExercise completion\nstatus"],
    ["Score Calculator\nCalculates points\nbased on accuracy",
     "Reward Engine\nBadges, stars,\ncombo streaks",
     "Progression\nController\nXP, level, next-phase\nrecommendation",
     "HUD Display\nManager\nDisplays scores in VR\ninterface"],
    ["Session Score\nDisplayed in VR HUD",
     "Rewards Unlocked\nShown to patient\nin VR",
     "Next-Phase\nRecommendation\nTherapist approves",
     "Progress Summary\nStored in session\ndatabase"])

FIGS["3.6.3.6 Adherence Monitoring Module"] = lambda: module(
    "Adherence Monitoring Module\nSession Compliance Tracker", "#2a7de1",
    ["Session Data\nStart time, end time",
     "Exercise Completion\nRepetition counts,\ncompletion status",
     "Prescribed Program\nRequired exercises\nfor the day"],
    ["Completion Checker\nVerifies the day's\nexercises are done",
     "Status Classifier\nComplete, partial,\nor missed",
     "Adherence Record\nWriter\nStores adherence\nresults in database",
     "Report Generator\n14-day calendar and\nattention flags"],
    ["Completion Flag\nPass or fail per\nsession",
     "Day Status\nComplete, partial,\nor missed",
     "Adherence Record\nSaved to adherence\ndatabase",
     "Therapist Report\nCalendar, adherence %,\nattention flags"])


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    want = sys.argv[2:]
    for name, make in FIGS.items():
        if want and not any(w in name for w in want):
            continue
        f = make()
        base = os.path.join(out, "Figure " + name)
        f.drawio(base + ".drawio", name)
        f.png(base + ".png")
        print("wrote", base + ".png")


if __name__ == "__main__":
    main()
