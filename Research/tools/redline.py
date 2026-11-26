"""Apply manuscript edits to a .docx as Word tracked changes (M9, DEC-031).

    python redline.py apply IN.docx EDITS.json OUT.docx [--author Claude] [--date 2026-11-22T00:00:00Z]
    python redline.py text DOCX [--view accept|reject]      # one line per paragraph (body + table cells)
    python redline.py guard DOCX                            # hashes that must never change

EDITS.json is a list of objects, each with "op", "source" and:
  replace       match, old, new   word-level diff of old -> new inside the one paragraph containing match
  insert_after  match, text[, like]   new paragraph after match, formatted like `like` (default: match)
  insert_before match, text[, like]
  delete_para   match
  delete_row    match              the whole table row whose cell paragraph contains match
`match` must hit exactly one paragraph (TOC excluded). `text`/`new` may mark bold with **.
Paragraphs with equations, images or fields, and everything in Section 3.9, are refused.
"""
import argparse, copy, difflib, hashlib, json, re, sys, zipfile
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W, 'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
q = lambda tag: '{%s}%s' % (W, tag)
QUOTES = str.maketrans({'’': "'", '‘': "'", '“': '"', '”': '"', ' ': ' ', '–': '-', '—': '-'})
TOKEN = re.compile(r'\*\*|\s+|\w+|[^\w\s]')


def paragraphs(root):
    """Body and table-cell paragraphs in document order, TOC (sdt) excluded."""
    return [p for p in root.iter(q('p')) if not p.xpath('ancestor::w:sdt', namespaces=NS)]


def ptext(p, view=None):
    out = []
    for el in p.iter(q('t'), q('delText'), q('tab'), q('br')):
        if el.getparent().tag != q('r'): continue  # tab stops in pPr are not text
        if view == 'accept' and el.xpath('ancestor::w:del', namespaces=NS): continue
        if view == 'reject' and el.xpath('ancestor::w:ins', namespaces=NS): continue
        if view is None and el.tag == q('delText'): continue
        out.append({q('tab'): '\t', q('br'): '\n'}.get(el.tag, el.text or ''))
    return ''.join(out)


def norm_map(s):
    """Normalised text (quotes unified, whitespace collapsed, lower case) and index map back to s."""
    out, idx, prev_space = [], [], False
    for i, ch in enumerate(s.translate(QUOTES)):
        if ch.isspace():
            if prev_space: continue
            ch, prev_space = ' ', True
        else:
            prev_space = False
        out.append(ch.lower()); idx.append(i)
    return ''.join(out), idx


norm = lambda s: norm_map(s)[0].strip()


def section_39(paras):
    """Ids of paragraphs from the 3.9 Data Analysis heading up to the 3.10 heading."""
    inside, ids = False, set()
    for p in paras:
        t = norm(ptext(p))
        if re.match(r'^3\.9 +data analysis', t): inside = True
        elif re.match(r'^3\.10 +ethical', t): inside = False
        if inside: ids.add(id(p))
    return ids


class Editor:
    def __init__(self, root, author, date):
        self.root, self.author, self.date, self.nid = root, author, date, 90000
        self.paras = paragraphs(root)
        self.locked = section_39(self.paras)

    def mark(self, tag):
        self.nid += 1
        return etree.Element(q(tag), {q('id'): str(self.nid), q('author'): self.author, q('date'): self.date})

    def find(self, match, exact=False):
        key = norm(match)
        hits = [p for p in self.paras if (key == norm(ptext(p)) if exact else key in norm(ptext(p)))]
        if len(hits) != 1: raise ValueError('match hits %d paragraphs: %r' % (len(hits), match[:60]))
        p = hits[0]
        if id(p) in self.locked: raise ValueError('inside Section 3.9')
        if p.xpath('.//m:oMath | .//w:fldChar | .//w:instrText', namespaces=NS):
            raise ValueError('paragraph holds an equation or field')
        return p

    # --- runs -------------------------------------------------------------
    def atoms(self, p):
        """(start, end, run, element) for each text-bearing element, offsets into ptext(p)."""
        res, pos = [], 0
        for el in p.iter(q('t'), q('tab'), q('br')):
            if el.getparent().tag != q('r'): continue
            n = len(el.text or '') if el.tag == q('t') else 1
            res.append((pos, pos + n, el.getparent(), el)); pos += n
        return res

    def split(self, p, off):
        """Make `off` a run boundary; return nothing."""
        for s, e, run, el in self.atoms(p):
            if s < off < e:
                if el.tag != q('t') or run.tag != q('r'): raise ValueError('cannot split here')
                k = off - s
                second = copy.deepcopy(run)
                kids = list(run)
                i = kids.index(el)
                for c in kids[i + 1:]: run.remove(c)
                skids = list(second)
                for c in skids[1 if skids[0].tag == q('rPr') else 0:skids.index(skids[i])]: second.remove(c)
                second_t = [c for c in second if c.tag == q('t')][0]
                el.text, second_t.text = el.text[:k], el.text[k:]
                for t in (el, second_t): t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                run.addnext(second)
                return

    def runs_between(self, p, s, e):
        """Runs whose every atom lies inside [s, e)."""
        spans = {}
        for a, b, run, _ in self.atoms(p):
            if b > a: spans.setdefault(run, []).append((a, b))
        inside = [r for r, sp in spans.items() if all(a >= s and b <= e for a, b in sp)]
        if any(r for r, sp in spans.items() if r not in inside and any(a < e and b > s for a, b in sp)):
            raise ValueError('change cuts through a run with a break or tab')
        return inside

    def new_run(self, rpr_src, text, bold=None):
        r = etree.Element(q('r'))
        rpr = rpr_src.find(q('rPr')) if rpr_src is not None else None
        rpr = copy.deepcopy(rpr) if rpr is not None else etree.Element(q('rPr'))
        for tag in ('b', 'bCs'):
            old = rpr.find(q(tag))
            if old is not None: rpr.remove(old)
        if bold:
            rpr.insert(1 if rpr.find(q('rFonts')) is not None else 0, etree.Element(q('b')))
            rpr.find(q('b')).addnext(etree.Element(q('bCs')))
        elif rpr_src is not None and bold is None:
            src = rpr_src.find(q('rPr'))
            for tag in ('b', 'bCs'):
                if src is not None and src.find(q(tag)) is not None: rpr.append(copy.deepcopy(src.find(q(tag))))
        r.append(rpr)
        for k, line in enumerate(text.split('\n')):
            if k: etree.SubElement(r, q('br'))
            if line:
                t = etree.SubElement(r, q('t')); t.text = line
                t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        return r

    def styled_runs(self, rpr_src, text, inherit_bold):
        """Runs for text; ** toggles bold. Without ** markers, bold follows rpr_src when inherit_bold."""
        if '**' not in text: return [self.new_run(rpr_src, text, None if inherit_bold else False)]
        runs, bold = [], False
        for piece in text.split('**'):
            if piece: runs.append(self.new_run(rpr_src, piece, bold))
            bold = not bold
        return runs

    # --- operations -------------------------------------------------------
    def replace(self, p, old, new):
        full = ptext(p)
        nfull, fmap = norm_map(full)
        nold = norm(old)
        at = nfull.find(nold)
        if at < 0 or nfull.find(nold, at + 1) >= 0: raise ValueError('old text not found once: %r' % old[:60])
        base = fmap[at]
        seg = full[base:fmap[at + len(nold) - 1] + 1]
        a_tok = [(m.start() + base, m.group()) for m in TOKEN.finditer(seg)]
        b_tok = [m.group() for m in TOKEN.finditer(new)]
        key = lambda t: '' if t.isspace() else t.translate(QUOTES)
        ops = difflib.SequenceMatcher(None, [key(t) for _, t in a_tok], [key(t) for t in b_tok], autojunk=False).get_opcodes()
        done = 0
        for tag, i1, i2, j1, j2 in reversed(ops):
            if tag == 'equal': continue
            s = a_tok[i1][0] if i1 < len(a_tok) else base + len(seg)
            e = a_tok[i2 - 1][0] + len(a_tok[i2 - 1][1]) if i2 > i1 else s
            ins = ''.join(b_tok[j1:j2])
            self.change(p, s, e, ins); done += 1
        return done

    def change(self, p, s, e, ins):
        self.split(p, s); self.split(p, e)
        dead = self.runs_between(p, s, e) if e > s else []
        if dead:
            parent = dead[0].getparent()
            if any(r.getparent() is not parent for r in dead): raise ValueError('change crosses an element boundary')
            if any(r.find('.//' + q('drawing')) is not None for r in dead): raise ValueError('change would delete an image')
            d = self.mark('del'); dead[0].addprevious(d)
            for r in dead:
                d.append(r)
                for t in r.iter(q('t')): t.tag = q('delText')
            anchor, src = d, dead[0]
        else:
            before = [run for (a, b, run, _) in self.atoms(p) if b <= s and b > a]
            after = [run for (a, b, run, _) in self.atoms(p) if a >= s and b > a]
            src = before[-1] if before else (after[0] if after else None)
            bold = lambda r: r is not None and r.find('w:rPr/w:b', NS) is not None
            if before and after and bold(before[-1]) and not bold(after[0]): src = after[0]
            anchor = before[-1] if before else None
        if ins.replace('**', ''):
            w = self.mark('ins')
            for r in self.styled_runs(src, ins, True): w.append(r)
            if anchor is not None: anchor.addnext(w)
            elif src is not None: src.addprevious(w)
            else: p.append(w)

    def new_para(self, ref, text, like, before):
        tmpl = like if like is not None else ref
        np = etree.Element(q('p'))
        ppr = tmpl.find(q('pPr'))
        ppr = copy.deepcopy(ppr) if ppr is not None else etree.Element(q('pPr'))
        prpr = ppr.find(q('rPr'))
        if prpr is None: prpr = etree.SubElement(ppr, q('rPr'))
        prpr.insert(0, self.mark('ins'))
        np.append(ppr)
        src = next((r for r in tmpl.iter(q('r')) if r.find(q('t')) is not None and (r.find(q('rPr')) is None or r.find('w:rPr/w:b', NS) is None)), None)
        src = src if src is not None else next(tmpl.iter(q('r')), None)
        w = self.mark('ins')
        for r in self.styled_runs(src, text, False): w.append(r)
        np.append(w)
        (ref.addprevious if before else ref.addnext)(np)
        self.paras = paragraphs(self.root)

    def delete_para(self, p):
        ppr = p.find(q('pPr'))
        if ppr is None: ppr = etree.Element(q('pPr')); p.insert(0, ppr)
        prpr = ppr.find(q('rPr'))
        if prpr is None: prpr = etree.SubElement(ppr, q('rPr'))
        prpr.insert(0, self.mark('del'))
        self.wrap_all_runs(p)

    def wrap_all_runs(self, p):
        for r in [r for r in p.iter(q('r')) if r.getparent().tag != q('del')]:
            d = self.mark('del'); r.addprevious(d); d.append(r)
            for t in r.iter(q('t')): t.tag = q('delText')

    def delete_row(self, p):
        tr = p.xpath('ancestor::w:tr[1]', namespaces=NS)
        if not tr: raise ValueError('not in a table')
        tr = tr[0]
        trpr = tr.find(q('trPr'))
        if trpr is None:
            trpr = etree.Element(q('trPr')); tr.insert(1 if tr[0].tag == q('tblPrEx') else 0, trpr)
        trpr.append(self.mark('del'))
        for cp in tr.iter(q('p')):
            ppr = cp.find(q('pPr'))
            if ppr is None: ppr = etree.Element(q('pPr')); cp.insert(0, ppr)
            prpr = ppr.find(q('rPr'))
            if prpr is None: prpr = etree.SubElement(ppr, q('rPr'))
            prpr.insert(0, self.mark('del'))
            self.wrap_all_runs(cp)

    def mark_para(self, p, tag):
        ppr = p.find(q('pPr'))
        if ppr is None: ppr = etree.Element(q('pPr')); p.insert(0, ppr)
        prpr = ppr.find(q('rPr'))
        if prpr is None: prpr = etree.SubElement(ppr, q('rPr'))
        prpr.insert(0, self.mark(tag))

    def delete_empty_after(self, p, count):
        """Delete exactly `count` empty paragraphs that directly follow p."""
        nxt = []
        sib = p.getnext()
        while sib is not None and len(nxt) < count:
            if sib.tag != q('p') or ptext(sib).strip() or sib.find('.//' + q('drawing')) is not None:
                raise ValueError('paragraph %d after the match is not empty' % (len(nxt) + 1))
            nxt.append(sib); sib = sib.getnext()
        if len(nxt) != count: raise ValueError('not enough empty paragraphs after the match')
        for e in nxt: self.mark_para(e, 'del')
        return count


    # --- tables (added 2026-11-25, M9.3 Chapter 1 Table 1.5.1) ---------------
    def fill_cell(self, tc, text, bold=None):
        """Replace a cell's content with one tracked-inserted run, keeping its first paragraph's formatting."""
        paras = tc.findall(q('p'))
        keep = paras[0]
        for extra in paras[1:]: tc.remove(extra)
        src = next((r for r in keep.iter(q('r')) if r.find(q('t')) is not None), None)
        if src is None: src = next(keep.iter(q('r')), None)
        for child in list(keep):
            if child.tag != q('pPr'): keep.remove(child)
        w = self.mark('ins')
        w.append(self.new_run(src, text, bold))
        keep.append(w)
        self.mark_para(keep, 'ins')

    def mark_row(self, tr):
        trpr = tr.find(q('trPr'))
        if trpr is None:
            trpr = etree.Element(q('trPr')); tr.insert(1 if tr[0].tag == q('tblPrEx') else 0, trpr)
        trpr.append(self.mark('ins'))

    def table_of(self, text):
        for t in self.root.iter(q('tbl')):
            if text in ''.join(t.itertext()) and not t.xpath('ancestor::w:sdt', namespaces=NS): return t
        raise ValueError('template table not found: %r' % text)

    def insert_table_after(self, p, edit):
        """Caption paragraph + a table cloned from a template table (all tracked as inserted)."""
        tmpl = self.table_of(edit['template'])
        rows_t = tmpl.findall(q('tr'))
        head_t, body_t = rows_t[0], rows_t[1]
        like = self.find(edit['like'])
        self.new_para(p, edit['caption'], like, False)
        cap = p.getnext()
        tbl = etree.Element(q('tbl'))
        for tag in ('tblPr', 'tblGrid'): tbl.append(copy.deepcopy(tmpl.find(q(tag))))
        for k, vals in enumerate([edit['header']] + edit['rows']):
            tr = copy.deepcopy(head_t if k == 0 else body_t)
            for tag in ('trPr',):
                old = tr.find(q(tag))
                if old is not None: tr.remove(old)
            cells = tr.findall(q('tc'))
            if len(cells) != len(vals): raise ValueError('template has %d columns, row has %d' % (len(cells), len(vals)))
            for tc, v in zip(cells, vals): self.fill_cell(tc, v, True if k == 0 else None)
            self.mark_row(tr); tbl.append(tr)
        cap.addnext(tbl)
        self.paras = paragraphs(self.root)
        return 1

    def insert_row_before(self, p, edit):
        tr = p.xpath('ancestor::w:tr[1]', namespaces=NS)
        if not tr: raise ValueError('not in a table')
        tr = tr[0]
        new = copy.deepcopy(tr)
        old = new.find(q('trPr'))
        if old is not None: new.remove(old)
        cells = new.findall(q('tc'))
        if len(cells) != len(edit['cells']): raise ValueError('row has %d cells' % len(cells))
        for tc, v in zip(cells, edit['cells']): self.fill_cell(tc, v)
        self.mark_row(new)
        tr.addprevious(new)
        self.paras = paragraphs(self.root)
        return 1

    def split_para(self, p, at):
        """Tracked paragraph break before the text `at`."""
        full = ptext(p)
        n, fmap = norm_map(full)
        k = n.find(norm(at))
        if k < 0 or n.find(norm(at), k + 1) >= 0: raise ValueError('split point not found once')
        off = fmap[k]
        self.split(p, off)
        first = etree.Element(q('p'))
        ppr = p.find(q('pPr'))
        first.append(copy.deepcopy(ppr) if ppr is not None else etree.Element(q('pPr')))
        for a, b, run, _ in self.atoms(p):
            if b <= off and run.getparent() is p: first.append(run)
        p.addprevious(first)
        self.mark_para(first, 'ins')
        self.paras = paragraphs(self.root)
        return 1

    def apply(self, edit):
        op = edit['op']
        p = self.find(edit['match'], edit.get('exact', False))
        if op == 'replace': return self.replace(p, edit['old'], edit['new'])
        if op == 'delete_empty_after': return self.delete_empty_after(p, edit.get('count', 1))
        if op == 'split_para': return self.split_para(p, edit['at'])
        if op in ('insert_after', 'insert_before'):
            like = self.find(edit['like']) if edit.get('like') else None
            self.new_para(p, edit['text'], like, op == 'insert_before'); return 1
        if op == 'insert_table_after': return self.insert_table_after(p, edit)
        if op == 'insert_row_before': return self.insert_row_before(p, edit)
        if op == 'delete_para': self.delete_para(p); return 1
        if op == 'delete_row': self.delete_row(p); return 1
        raise ValueError('unknown op ' + op)


def load(path):
    z = zipfile.ZipFile(path)
    return z, etree.fromstring(z.read('word/document.xml'))


def cmd_apply(a):
    z, root = load(a.input)
    edits = json.load(open(a.edits, encoding='utf-8'))
    ed = Editor(root, a.author, a.date)
    report = []
    for n, e in enumerate(edits, 1):
        try:
            k = ed.apply(e)
            report.append('%3d applied (%d change%s) %s' % (n, k, '' if k == 1 else 's', e.get('source', '')))
            if k == 0: report[-1] = '%3d NO-OP %s' % (n, e.get('source', ''))
        except ValueError as err:
            report.append('%3d REFUSED %s: %s' % (n, e.get('source', ''), err))
    data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
    with zipfile.ZipFile(a.output, 'w', zipfile.ZIP_DEFLATED) as out:
        for item in z.infolist():
            out.writestr(item, data if item.filename == 'word/document.xml' else z.read(item.filename))
    print('\n'.join(report))
    print('applied %d, refused %d, no-op %d' % tuple(sum(t in r for r in report) for t in (' applied', 'REFUSED', 'NO-OP')))


def cmd_text(a):
    """Paragraph text as Word shows it with all changes accepted or rejected.
    A paragraph whose mark is removed in that view joins the next paragraph."""
    _, root = load(a.docx)
    gone = {'accept': 'del', 'reject': 'ins'}.get(a.view)
    carry = ''
    for p in paragraphs(root):
        if a.view == 'accept' and p.xpath('ancestor::w:tr[w:trPr/w:del]', namespaces=NS): continue
        t = carry + ptext(p, a.view)
        if gone and p.xpath('w:pPr/w:rPr/w:' + gone, namespaces=NS):
            carry = t; continue
        carry = ''
        sys.stdout.write(t.replace('\n', ' ') + '\n')


def cmd_guard(a):
    """Content hashes that survive a re-save by Word (which rewrites ids, rsids and media names):
    Section 3.9 text and equations, the set of image files, and the images in document order."""
    z, root = load(a.docx)
    paras = paragraphs(root)
    locked = section_39(paras)
    h = lambda b: hashlib.sha256(b).hexdigest()[:16]
    MT = '{%s}t' % NS['m']
    s39 = '\n'.join(ptext(p) + '|' + ''.join(t.text or '' for t in p.iter(MT)) for p in paras if id(p) in locked)
    rels = etree.fromstring(z.read('word/_rels/document.xml.rels'))
    target = {r.get('Id'): r.get('Target') for r in rels}
    blip = '{http://schemas.openxmlformats.org/drawingml/2006/main}blip'
    emb = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'
    order = [h(z.read('word/' + target[b.get(emb)])) for b in root.iter(blip) if b.get(emb) in target]
    med = sorted(h(z.read(n)) for n in z.namelist() if n.startswith('word/media/'))
    print('section3.9 %s (%d paras)  images-in-order %s (%d)  media-set %s (%d)' % (
        h(s39.encode()), len(locked), h(''.join(order).encode()), len(order), h(''.join(med).encode()), len(med)))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    p1 = sub.add_parser('apply'); p1.add_argument('input'); p1.add_argument('edits'); p1.add_argument('output')
    p1.add_argument('--author', default='Claude'); p1.add_argument('--date', default='2026-11-22T00:00:00Z')
    p2 = sub.add_parser('text'); p2.add_argument('docx'); p2.add_argument('--view', choices=['accept', 'reject'])
    p3 = sub.add_parser('guard'); p3.add_argument('docx')
    a = ap.parse_args()
    {'apply': cmd_apply, 'text': cmd_text, 'guard': cmd_guard}[a.cmd](a)
