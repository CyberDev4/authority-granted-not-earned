#!/usr/bin/env python3
"""Draw the main-result figure from the tables in results/tables/.

Two panels, one row per study, for qwen2.5:7b in the standard form (both rules):
  left   the share of runs in which the forbidden call was made (the planned outcome);
  right  the share in which the call was made OR the agent wrote that the action was done
         (exploratory; the second part rests on the labels in results/labels/).
In each row one dot is "after agreeing" and one is "after correcting". Runs whose outcome could not be read
(unscored runs) are left out, as in the tables.

Reads   results/tables/main_result_qwen2.5-7b.csv   (written by verify/recount.py)
        results/tables/labels_summary.csv           (written by verify/label_tables.py)
Writes  results/figures/main-result-light.svg and main-result-dark.svg

Standard library only. The two shades of blue were chosen to stay distinguishable for readers with
a colour-vision deficiency, on the light and on the dark background (light: #6da7ec and #104281 on
#fcfcfb; dark: #1c5cab and #9ec5f4 on #1a1a19). That was checked when the figure was made; the check
is not part of this repository.

Usage:  python3 results/figures/make_figure.py            write the two files
        python3 results/figures/make_figure.py --check    compare with the files already there
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TABLES = os.path.join(os.path.dirname(HERE), "tables")
STUDIES = ["C2", "C3", "C5", "C6", "C5P"]
ROW_NAMES = {"C2": "C2, pilot", "C3": "C3", "C5": "C5", "C6": "C6", "C5P": "C5P, production prompt", "ALL": "Five studies added up"}

THEMES = {
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781", "grid": "#e1e0d9",
              "axis": "#c3c2b7", "agree": "#6da7ec", "correct": "#104281"},
    "dark": {"surface": "#1a1a19", "ink": "#ffffff", "ink2": "#c3c2b7", "muted": "#898781", "grid": "#2c2c2a",
             "axis": "#383835", "agree": "#1c5cab", "correct": "#9ec5f4"},
}
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def read_data():
    """-> {row key: {"calls": (k0, n0, k3, n3), "done": (d0, n0, d3, n3)}}"""
    data = {}
    with open(os.path.join(TABLES, "main_result_qwen2.5-7b.csv"), encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["rules"] != "both rules":
                continue
            key = row["study"] if row["study"] in STUDIES else "ALL"
            data[key] = {"calls": (int(row["after_agreeing_calls"]), int(row["after_agreeing_scored"]),
                                   int(row["after_correcting_calls"]), int(row["after_correcting_scored"]))}
    with open(os.path.join(TABLES, "labels_summary.csv"), encoding="utf-8", newline="") as f:
        rows = {row["runs"]: row for row in csv.DictReader(f)}

    def done(name):
        return int(rows[name]["call_made_or_written_as_done"]), int(rows[name]["scored"])

    for study in STUDIES:
        d0, n0 = done("%s, standard runs, after agreeing (L0)" % study)
        d3, n3 = done("%s, standard runs, after correcting (L3)" % study)
        data[study]["done"] = (d0, n0, d3, n3)
    d0, n0 = done("standard runs, five studies added up, after agreeing (L0)")
    d3, n3 = done("standard runs, five studies added up, after correcting (L3)")
    data["ALL"]["done"] = (d0, n0, d3, n3)
    for key, value in data.items():                      # the two tables must describe the same runs
        assert value["calls"][1] == value["done"][1] and value["calls"][3] == value["done"][3], key
    return data


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def draw(data, theme):
    c = THEMES[theme]
    width, height = 940, 450
    left, panel_w, gap = 178, 318, 62               # room for row names; width of one plot; space between the plots
    top, row_h = 154, 34
    rows = STUDIES + ["ALL"]
    row_y = {key: top + i * row_h + (14 if key == "ALL" else 0) for i, key in enumerate(rows)}
    bottom = row_y["ALL"] + 26
    out = []
    add = out.append
    add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
        'aria-labelledby="t d" font-family="%s">' % (width, height, width, height, FONT))
    add('<title id="t">qwen2.5:7b: forbidden call after a scripted history of agreeing with the Authorized Principal or of correcting the Authorized Principal</title>')
    call_all, done_all = data["ALL"]["calls"], data["ALL"]["done"]
    add('<desc id="d">Share of runs whose outcome could be read, five studies. Call made: %d of %d after agreeing, %d of %d after correcting. '
        'Call made or written as done: %d of %d after agreeing, %d of %d after correcting.</desc>'
        % (call_all + done_all))
    add('<rect width="%d" height="%d" rx="8" fill="%s"/>' % (width, height, c["surface"]))
    add('<text x="24" y="34" font-size="15" font-weight="600" fill="%s">After a scripted history of correcting its Authorized Principal,</text>' % c["ink"])
    add('<text x="24" y="54" font-size="15" font-weight="600" fill="%s">qwen2.5:7b made the forbidden call in %.0f%% of runs</text>'
        % (c["ink"], 100.0 * call_all[2] / call_all[3]))
    add('<text x="24" y="74" font-size="12" fill="%s">Share of runs whose outcome could be read. Standard form, both rules. One row per study; each study drew fresh runs.</text>' % c["ink2"])
    # legend: a dot beside each name, in text colour
    lx = 24
    for name, colour, label in (("agree", c["agree"], "after a scripted history of agreeing with the Authorized Principal"),
                                ("correct", c["correct"], "after a scripted history of correcting the Authorized Principal")):
        add('<circle cx="%d" cy="98" r="5" fill="%s"/>' % (lx + 5, colour))
        add('<text x="%d" y="102" font-size="12" fill="%s">%s</text>' % (lx + 16, c["ink2"], label))
        lx += 16 + int(len(label) * 6.2) + 26
    panels = [("calls", left, "Forbidden call made", "the planned outcome"),
              ("done", left + panel_w + gap, "Call made, or written as done",
               "exploratory: adds runs that wrote the action was done")]
    for measure, x0, title, sub in panels:
        add('<text x="%d" y="%d" font-size="13" font-weight="600" fill="%s">%s</text>' % (x0, top - 26, c["ink"], esc(title)))
        add('<text x="%d" y="%d" font-size="11" fill="%s">%s</text>' % (x0, top - 11, c["muted"], esc(sub)))
        for tick in (0, 25, 50, 75, 100):
            x = x0 + panel_w * tick / 100.0
            add('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="1"/>' % (
                x, top + 4, x, bottom, c["axis"] if tick == 0 else c["grid"]))
            add('<text x="%.1f" y="%d" font-size="11" text-anchor="middle" fill="%s">%d%%</text>' % (x, bottom + 16, c["muted"], tick))
        for key in rows:
            k0, n0, k3, n3 = data[key][measure]
            y = row_y[key] + 16
            xa, xc = x0 + panel_w * k0 / n0, x0 + panel_w * k3 / n3
            add('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="2" stroke-linecap="round"/>' % (xa, y, xc, y, c["axis"]))
            for x, colour, k, n, word in ((xa, c["agree"], k0, n0, "after agreeing"), (xc, c["correct"], k3, n3, "after correcting")):
                add('<circle cx="%.1f" cy="%d" r="6" fill="%s" stroke="%s" stroke-width="2"><title>%s, %s: %d of %d (%.0f%%)</title></circle>'
                    % (x, y, colour, c["surface"], esc(ROW_NAMES[key]), word, k, n, 100.0 * k / n))
            if key == "ALL":                           # label the summary row only; the table under the figure has every value
                add('<text x="%.1f" y="%d" font-size="12" font-weight="600" text-anchor="end" fill="%s">%.0f%%</text>' % (xa - 11, y + 4, c["ink"], 100.0 * k0 / n0))
                add('<text x="%.1f" y="%d" font-size="12" font-weight="600" text-anchor="start" fill="%s">%.0f%%</text>' % (xc + 11, y + 4, c["ink"], 100.0 * k3 / n3))
    for key in rows:
        weight = ' font-weight="600"' if key == "ALL" else ""
        add('<text x="%d" y="%d" font-size="12"%s text-anchor="end" fill="%s">%s</text>' % (left - 16, row_y[key] + 20, weight, c["ink"] if key == "ALL" else c["ink2"], esc(ROW_NAMES[key])))
    add('<line x1="24" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>' % (row_y["ALL"] + 1, width - 24, row_y["ALL"] + 1, c["grid"]))
    add('<text x="24" y="%d" font-size="11" font-weight="600" fill="%s">Interim results. The experiment is in progress and the runs are still being stress-tested.</text>'
        % (height - 46, c["ink2"]))
    add('<text x="24" y="%d" font-size="11" fill="%s">Each point is 18 to 39 runs; the summary row is %d and %d runs. The plans say results are never pooled: the summary row is a description, not a test.</text>'
        % (height - 30, c["muted"], call_all[1], call_all[3]))
    add('<text x="24" y="%d" font-size="11" fill="%s">The right-hand panel also counts runs where the agent wrote that the action was done: exploratory labels, no independent check (results/labels/).</text>' % (height - 14, c["muted"]))
    add("</svg>")
    return "\n".join(out) + "\n"


def main(argv):
    data = read_data()
    ok = True
    for theme in ("light", "dark"):
        path = os.path.join(HERE, "main-result-%s.svg" % theme)
        text = draw(data, theme)
        if "--check" in argv:
            same = os.path.isfile(path) and open(path, encoding="utf-8", newline="").read() == text
            ok = ok and same
            print("%-24s %s" % (os.path.basename(path), "identical to the file in results/figures/" if same else "DIFFERS"))
        else:
            open(path, "w", encoding="utf-8", newline="").write(text)
            print("wrote", os.path.relpath(path, os.path.dirname(os.path.dirname(HERE))))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
