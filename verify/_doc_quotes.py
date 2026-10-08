"""Check every quote on docs/how-a-run-works.md against the file it cites. Used by check_docs.py.

The page marks each quoted text with a label and a source line, followed by a fenced block or a
block quote:

  **Q7.** Exact text: `lab/gne_c3/run.py:33-35`. Sent as message 0 of `S1`.
  **Q9.** Exact code: `lab/gne_c3/run.py:149-160`.
  **Q3.** Assembled at run time (`lab/gne_c3/run.py:176` ...). As sent: message 1 of `S1`.
  **Q50.** Assembled at run time (...). As sent: inside the prompt of `S28`.   (or: the whole prompt of)
  **Q1.** Request fields: everything in `S1` except `messages`, `tools` and `prompt`.
  **Q18.** From a saved reply: `lab/runs/.../response-01.json`.

and each table of quoted texts with a label and a source line:

  **T1.** Exact texts from `FILE`; the Lines column gives the lines. [Sent as the numbered messages of `S1`.]
  **T7.** Exact texts from `FILE`; the Lines column gives the lines, the last column a saved request and message.
  **T5.** Tools as offered in `S1`.
  **T6.** Texts as sent; the last column names the saved request and the message.
  **T9.** Side by side: left `S1`, right `S2`; the # column is the message position.

What is checked:

- Exact text: the quote equals one Python string constant that lies inside the cited lines. The file is
  parsed with `ast`, which joins adjacent string literals, so a text written over several literals is
  compared as one. If the label also names a saved request, the quote must be that message, or occur in
  that prompt.
- Exact code: the quote equals the cited source lines (common indentation removed).
- Assembled at run time: no single literal holds the text, so the quote is compared with the saved
  request named in the label: the message with that number, or the prompt.
- Request fields: the JSON in the quote equals the saved request without messages, tools and prompt.
- From a saved reply: the quote occurs in the text of that saved reply.
- Tables: every row is checked in the same ways. A side-by-side table must list every message of both
  requests, so that no difference can be left out.

Also checked: every `lab/...` path named on the page exists, every `file:lines` reference lies inside
its file, and every short quotation from a plan that is followed by its file and line occurs there.

Quote boxes (lines starting with ">") are joined with single spaces before comparing; an empty ">" line
separates paragraphs. Reads the page and lab/ only. Writes nothing.
"""
import ast
import json
import re
import sys
import textwrap
from pathlib import Path

# How the page names who speaks, and the role that the saved request gives that message.
ROLE_WORD = {"system": "system", "authorized principal": "user", "user": "user", "agent": "assistant", "assistant": "assistant"}


def role_of(cell):
    """The role named in a table cell such as "Authorized Principal (user)" or "Agent"."""
    return ROLE_WORD[re.sub(r"\s*\(.*\)\s*$", "", cell).strip().lower()]


class Repo:
    def __init__(self, root):
        self.root = Path(root)
        self._text, self._json, self._consts = {}, {}, {}

    def text(self, rel):
        if rel not in self._text:
            self._text[rel] = (self.root / rel).read_text(encoding="utf-8")
        return self._text[rel]

    def lines(self, rel):
        return self.text(rel).split("\n")

    def json(self, rel):
        if rel not in self._json:
            self._json[rel] = json.loads(self.text(rel))
        return self._json[rel]

    def string_constants(self, rel):
        """(first line, last line, value) of every string constant; adjacent literals arrive joined."""
        if rel not in self._consts:
            tree = ast.parse(self.text(rel))
            self._consts[rel] = [(n.lineno, n.end_lineno, n.value) for n in ast.walk(tree)
                                 if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        return self._consts[rel]

    def has_constant(self, rel, a, b, value):
        return any(x >= a and y <= b and v == value for x, y, v in self.string_constants(rel))


def split_ref(ref):
    """'lab/x/run.py:33-35' -> ('lab/x/run.py', 33, 35)"""
    m = re.fullmatch(r"(.+?):(\d+)(?:-(\d+))?", ref)
    if not m:
        raise ValueError("not a file:line reference: %r" % ref)
    a = int(m.group(2))
    return m.group(1), a, int(m.group(3) or a)


def split_row(line):
    cells = re.split(r"(?<!\\)\|", line.strip())
    return [c.strip().replace("\\|", "|") for c in cells[1:-1]]


def uncode(cell):
    """Remove one pair of backticks around a code cell."""
    return cell[1:-1] if len(cell) >= 2 and cell[0] == "`" and cell[-1] == "`" else cell


def read_blocks(lines):
    """Yield (label, caption text, block kind, block content, line number) for every labelled quote or table."""
    i, n = 0, len(lines)
    while i < n:
        m = re.match(r"\*\*([QT]\d+)\.\*\* ", lines[i])
        if not m:
            i += 1
            continue
        start = i
        cap = []
        while i < n and lines[i].strip():
            cap.append(lines[i].strip())
            i += 1
        caption = " ".join(cap)[m.end():]
        while i < n and not lines[i].strip():
            i += 1
        if i >= n:
            yield m.group(1), caption, "none", None, start + 1
            break
        fence = re.match(r"(`{3,})(\w*)\s*$", lines[i])
        if fence:
            i += 1
            body = []
            while i < n and lines[i] != fence.group(1):
                body.append(lines[i])
                i += 1
            i += 1
            yield m.group(1), caption, "fence", "\n".join(body), start + 1
        elif lines[i].startswith(">"):
            paragraphs, cur = [], []
            while i < n and lines[i].startswith(">"):
                piece = lines[i][1:].strip()
                if piece:
                    cur.append(piece)
                else:
                    paragraphs.append(" ".join(cur))
                    cur = []
                i += 1
            paragraphs.append(" ".join(cur))
            yield m.group(1), caption, "quote", "\n\n".join(paragraphs), start + 1
        elif lines[i].startswith("|"):
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            yield m.group(1), caption, "table", rows, start + 1
        else:
            yield m.group(1), caption, "none", None, start + 1


def saved_requests(lines):
    """Label -> path, from the table of Appendix A (columns Label and Saved request)."""
    out = {}
    for line in lines:
        if line.startswith("| `S"):
            cells = split_row(line)
            label, path = uncode(cells[0]), next(uncode(c) for c in cells if uncode(c).startswith("lab/"))
            out[label] = path
    return out


def check_quote(repo, saved, caption, kind, body):
    """Return (kind of quote, detail of what was compared). Raises AssertionError on a mismatch."""
    assert kind in ("fence", "quote"), "no quoted block follows the label"
    m = re.match(r"Exact text: `([^`]+)`\.(.*)$", caption)
    if m:
        rel, a, b = split_ref(m.group(1))
        assert rel.endswith(".py"), "exact texts are checked in Python files only"
        assert repo.has_constant(rel, a, b, body), "no string constant inside %s:%d-%d equals the quote" % (rel, a, b)
        detail = "one string constant in %s:%d-%d" % (rel, a, b)
        rest = m.group(2)
        s = re.search(r"Sent as message (\d+) of `(S\d+)`", rest)
        if s:
            msg = repo.json(saved[s.group(2)])["messages"][int(s.group(1))]
            assert msg["content"] == body, "message %s of %s differs from the quote" % (s.group(1), s.group(2))
            detail += "; equals message %s of %s" % (s.group(1), s.group(2))
        s = re.search(r"Sent inside the prompt of `(S\d+)`", rest)
        if s:
            assert body in repo.json(saved[s.group(1)])["prompt"], "the prompt of %s does not contain the quote" % s.group(1)
            detail += "; occurs in the prompt of %s" % s.group(1)
        assert rest.strip() == "" or s or "Sent as message" in rest, "unreadable end of label: %r" % rest
        return "exact text", detail
    m = re.match(r"Exact code: `([^`]+)`\.$", caption)
    if m:
        rel, a, b = split_ref(m.group(1))
        want = textwrap.dedent("\n".join(repo.lines(rel)[a - 1:b]))
        assert want == body, "the cited lines differ from the quote"
        return "exact code", "lines %d-%d of %s" % (a, b, rel)
    m = re.match(r"Assembled at run time \((.*)\)\. As sent: (.*)\.$", caption)
    if m:
        for ref in re.findall(r"`([^`]+)`", m.group(1)):
            rel, a, b = split_ref(ref)
            assert 1 <= a <= b <= len(repo.lines(rel)), "reference outside the file: %s" % ref
        how = m.group(2)
        s = re.fullmatch(r"message (\d+) of `(S\d+)`", how)
        if s:
            msg = repo.json(saved[s.group(2)])["messages"][int(s.group(1))]
            assert msg["content"] == body, "message %s of %s differs from the quote" % (s.group(1), s.group(2))
            return "assembled at run time", "equals message %s of %s (%s)" % (s.group(1), s.group(2), saved[s.group(2)])
        s = re.fullmatch(r"inside the prompt of `(S\d+)`", how)
        if s:
            assert body in repo.json(saved[s.group(1)])["prompt"], "the prompt of %s does not contain the quote" % s.group(1)
            return "assembled at run time", "occurs in the prompt of %s (%s)" % (s.group(1), saved[s.group(1)])
        s = re.fullmatch(r"the whole prompt of `(S\d+)`", how)
        if s:
            assert body == repo.json(saved[s.group(1)])["prompt"], "the prompt of %s differs from the quote" % s.group(1)
            return "assembled at run time", "equals the whole prompt of %s (%s)" % (s.group(1), saved[s.group(1)])
        raise AssertionError("unreadable label: %r" % how)
    m = re.match(r"Request fields: everything in `(S\d+)` except", caption)
    if m:
        req = repo.json(saved[m.group(1)])
        want = {k: v for k, v in req.items() if k not in ("messages", "tools", "prompt")}
        assert json.loads(body) == want, "the fields of %s differ from the quote" % m.group(1)
        return "request fields", "equals the fields of %s (%s)" % (m.group(1), saved[m.group(1)])
    m = re.match(r"From a saved reply: `([^`]+)`\.$", caption)
    if m:
        content = repo.json(m.group(1))["message"]["content"]
        assert body in content, "the saved reply does not contain the quote"
        return "from a saved reply", "occurs in the reply text of %s" % m.group(1)
    raise AssertionError("label not understood: %r" % caption)


def check_table(repo, saved, caption, rows):
    """Return (kind, number of rows checked, detail). Raises AssertionError on a mismatch."""
    header, body = rows[0], rows[2:]
    col = {name: i for i, name in enumerate(header)}
    assert body, "empty table"
    m = re.match(r"Exact texts from `([^`]+)`; the Lines column gives the lines", caption)
    if m:
        rel = m.group(1)
        sent = re.search(r"Sent as the numbered messages of `(S\d+)`", caption)
        for r in body:
            text = uncode(r[col["Text"]])
            ref = r[col["Lines"]]
            a, b = (int(x) for x in (ref.split("-") + ref.split("-"))[:2])
            assert repo.has_constant(rel, a, b, text), "no string constant inside %s:%s equals %r" % (rel, ref, text[:50])
            if sent:
                msg = repo.json(saved[sent.group(1)])["messages"][int(r[col["#"]])]
                assert msg["content"] == text, "message %s of %s differs" % (r[col["#"]], sent.group(1))
                assert msg["role"] == role_of(r[col["Who speaks"]]), "role of message %s differs" % r[col["#"]]
            if "Seen in" in col:
                s = re.fullmatch(r"`(S\d+)` #(\d+)", r[col["Seen in"]])
                msg = repo.json(saved[s.group(1)])["messages"][int(s.group(2))]
                assert msg["content"] == text, "message %s of %s differs" % (s.group(2), s.group(1))
        how = "string constants of %s" % rel
        if sent:
            how += "; messages of %s with their roles" % sent.group(1)
        if "Seen in" in col:
            how += "; the message named in each row"
        return "exact texts", len(body), how
    m = re.match(r"Tools as offered in `(S\d+)`\.$", caption)
    if m:
        tools = repo.json(saved[m.group(1)])["tools"]
        assert len(tools) == len(body), "the request offers %d tools, the table has %d rows" % (len(tools), len(body))
        for r, t in zip(body, tools):
            f = t["function"]
            props = f["parameters"]["properties"]
            assert uncode(r[col["Tool"]]) == f["name"], "tool name %r" % r[col["Tool"]]
            assert r[col["Description"]] == f["description"], "description of %s" % f["name"]
            assert [uncode(x.strip()) for x in r[col["Arguments"]].split(",")] == list(props) == f["parameters"]["required"], \
                "arguments of %s" % f["name"]
            assert all(p["type"] == "string" for p in props.values()), "argument types of %s" % f["name"]
            enums = {k: p["enum"] for k, p in props.items() if "enum" in p}
            cell = r[col["Allowed values"]]
            if not enums:
                assert cell == "any text", "allowed values of %s" % f["name"]
            else:
                got = {}
                for part in cell.split(";"):
                    k, v = part.split(":")
                    got[uncode(k.strip())] = [uncode(x.strip()) for x in v.split(" or ")]
                assert got == enums, "allowed values of %s" % f["name"]
        return "tools", len(body), "names, descriptions, arguments and allowed values in the tools of %s" % m.group(1)
    if caption.startswith("Texts as sent;"):
        for r in body:
            s = re.fullmatch(r"`(S\d+)` #(\d+)", r[col["Seen in"]])
            msg = repo.json(saved[s.group(1)])["messages"][int(s.group(2))]
            assert msg["content"] == uncode(r[col["Text sent"]]), "message %s of %s differs" % (s.group(2), s.group(1))
        return "texts as sent", len(body), "the message named in each row"
    m = re.match(r"Side by side: left `(S\d+)`, right `(S\d+)`", caption)
    if m:
        left, right = (repo.json(saved[x])["messages"] for x in m.groups())
        assert len(left) == len(right) == len(body), "the table must list every message of both requests"
        ndiff = 0
        for r in body:
            i = int(r[col["#"]])
            a = uncode(r[2]).replace("\\n", "\n") if r[2].startswith("`") else r[2]
            b = a if r[3] == "same as left" else (uncode(r[3]).replace("\\n", "\n") if r[3].startswith("`") else r[3])
            assert left[i]["content"] == a, "left message %d differs" % i
            assert right[i]["content"] == b, "right message %d differs" % i
            assert left[i]["role"] == right[i]["role"] == role_of(r[col["Role"]]), "role of message %d" % i
            differs = left[i] != right[i]
            assert (r[col["Differs"]] == "**yes**") == differs and (r[3] == "same as left") == (not differs), "Differs column, message %d" % i
            ndiff += differs
        return "side by side", len(body), "every message of %s and %s; %d of %d differ" % (m.group(1), m.group(2), ndiff, len(body))
    raise AssertionError("label not understood: %r" % caption)


def check_references(repo, page):
    """Every `lab/...` path exists; every file:lines reference lies inside its file. Returns (checked, problems)."""
    checked, problems = 0, []
    for ref in sorted(set(re.findall(r"`(lab/[^`\s]*)`", page))):
        if "<" in ref:
            continue
        checked += 1
        m = re.fullmatch(r"(.+?):(\d+)(?:-(\d+))?", ref)
        rel = m.group(1) if m else ref
        target = repo.root / rel
        if not target.exists():
            problems.append("missing path: %s" % ref)
        elif m:
            a, b, n = int(m.group(2)), int(m.group(3) or m.group(2)), len(repo.lines(rel))
            if not 1 <= a <= b <= n:
                problems.append("lines outside the file (%d lines): %s" % (n, ref))
    return checked, problems


def check_plan_quotes(repo, page):
    """Short quotations followed by their file and line: "..." (`lab/x/FILE.md:N`). Returns (checked, problems)."""
    checked, problems = 0, []
    flat_page = re.sub(r"\s+", " ", page)
    for text, rel, line in re.findall(r'"([^"]+)" \(`(lab/[^`:]+\.md):(\d+)`\)', flat_page):
        checked += 1
        lines = repo.lines(rel)
        window = re.sub(r"\s+", " ", " ".join(lines[int(line) - 1:int(line) + 8]))
        if text not in window:
            problems.append("not found from line %s of %s: %r" % (line, rel, text))
    return checked, problems


def run(repo_root, page_path, verbose=False):
    """Check one page. Returns (number of problems, list of summary lines)."""
    repo = Repo(repo_root)
    page = Path(page_path).read_text(encoding="utf-8")
    lines = page.split("\n")
    saved = saved_requests(lines)
    missing = [k for k, v in saved.items() if not (repo.root / v).exists()]
    results, by_kind = [], {}
    q_total = q_ok = t_total = t_ok = rows_ok = 0
    for label, caption, kind, body, lineno in read_blocks(lines):
        try:
            if label.startswith("Q"):
                q_total += 1
                what, detail = check_quote(repo, saved, caption, kind, body)
                q_ok += 1
                results.append((label, what, "verified", detail, lineno))
                by_kind.setdefault(what, [0, 0])[0] += 1
            else:
                t_total += 1
                assert kind == "table", "no table follows the label"
                what, nrows, detail = check_table(repo, saved, caption, body)
                t_ok += 1
                rows_ok += nrows
                results.append((label, what + " (table, %d rows)" % nrows, "verified", detail, lineno))
        except (AssertionError, KeyError, ValueError, IndexError, FileNotFoundError, StopIteration) as e:
            results.append((label, "?", "NOT VERIFIED", "%s: %s" % (type(e).__name__, e), lineno))
    labels = [r[0] for r in results]
    dup = sorted({x for x in labels if labels.count(x) > 1})
    n_q_labels = len(re.findall(r"^\*\*Q\d+\.\*\* ", page, flags=re.M))
    refs_checked, ref_problems = check_references(repo, page)
    plan_checked, plan_problems = check_plan_quotes(repo, page)
    out = []
    for label, what, status, detail, lineno in results:
        if verbose or status != "verified":
            out.append("%-4s line %-5d %-13s %-34s %s" % (label, lineno, status, what, detail))
    out.append("saved requests named in Appendix A: %d (missing files: %d)" % (len(saved), len(missing)))
    out.append("quotes: %d labelled, %d verified (%s)" % (
        q_total, q_ok, "; ".join("%s %d" % (what, n) for what, (n, _) in sorted(by_kind.items()))))
    out.append("tables of quoted texts: %d labelled, %d verified (%d rows)" % (t_total, t_ok, rows_ok))
    out.append("references to lab/ files and lines: %d checked, %d problems" % (refs_checked, len(ref_problems)))
    out.extend("    " + p for p in ref_problems)
    out.append("short quotations from plans, with file and line: %d checked, %d problems" % (plan_checked, len(plan_problems)))
    out.extend("    " + p for p in plan_problems)
    if dup:
        out.append("duplicate labels: %s" % dup)
    failed = (q_total - q_ok) + (t_total - t_ok) + len(ref_problems) + len(plan_problems) + len(missing) + len(dup)
    failed += q_total != n_q_labels
    return failed, out, {"quotes": q_total, "tables": t_total, "rows": rows_ok, "references": refs_checked, "plan_quotes": plan_checked}
