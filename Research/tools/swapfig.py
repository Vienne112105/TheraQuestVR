"""Replace figures in a .docx as Word tracked changes (M9.4, DEC-031).

    python swapfig.py IN.docx MAP.json OUT.docx [--author Claude] [--date 2026-11-26T00:00:00Z]

MAP.json: {"<n>": "path/to/new.png", ...} where n is the figure's position among the document's drawings (1-based,
document order). For each, the run holding the old drawing is marked deleted and a copy pointing at the new image is
inserted right after it, so rejecting all changes gives the old figure back. The new image keeps the old drawing's
layout (inline or floating) and is sized to the text width, height from its own aspect
ratio, at most MAX_H. Nothing else in the document is touched.
"""
import argparse, copy, json, re, struct, zipfile
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W, 'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture'}
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
q = lambda t: '{%s}%s' % (W, t)
EMU_CM = 360000
MAX_W = int(15.24 * EMU_CM)       # text width: 8.5 in page, 1.5 in left and 1 in right margins
MAX_H = int(20.5 * EMU_CM)        # leaves room for the caption on a 9 in high text area


def png_size(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'PNG files only'
    return struct.unpack('>II', data[16:24])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input'); ap.add_argument('map'); ap.add_argument('output')
    ap.add_argument('--author', default='Claude'); ap.add_argument('--date', default='2026-11-26T00:00:00Z')
    a = ap.parse_args()
    mapping = {int(k): v for k, v in json.load(open(a.map, encoding='utf8')).items()}

    zin = zipfile.ZipFile(a.input)
    files = {n: zin.read(n) for n in zin.namelist()}
    doc = etree.fromstring(files['word/document.xml'])
    rels = etree.fromstring(files['word/_rels/document.xml.rels'])
    ct = files['[Content_Types].xml'].decode('utf8')
    if 'Extension="png"' not in ct:
        ct = ct.replace('<Default ', '<Default Extension="png" ContentType="image/png"/><Default ', 1)

    rid_n = max(int(re.sub(r'\D', '', r.get('Id')) or 0) for r in rels) + 1
    ids = [int(x) for x in doc.xpath('//w:ins/@w:id|//w:del/@w:id', namespaces=NS)] + [0]
    rev = max(ids) + 1000
    docpr = max(int(x) for x in doc.xpath('//wp:docPr/@id', namespaces=NS)) + 100

    drawings = list(doc.iter(q('drawing')))
    for n, path in sorted(mapping.items()):
        d = drawings[n - 1]
        run = d.getparent()
        assert run.tag == q('r'), 'drawing %d is not directly in a run' % n
        assert not run.xpath('ancestor::w:ins|ancestor::w:del', namespaces=NS), 'figure %d already tracked' % n
        data = open(path, 'rb').read()
        pw, ph = png_size(data)
        media = 'media/m94_fig%02d.png' % n
        files['word/' + media] = data
        rid = 'rId%d' % rid_n; rid_n += 1
        etree.SubElement(rels, '{%s}Relationship' % REL, Id=rid, Target=media,
                         Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/image')

        new_run = copy.deepcopy(run)
        nd = new_run.find('w:drawing', NS)
        kid = nd[0]
        old_cx = int(kid.find('wp:extent', NS).get('cx'))
        cx = MAX_W
        cy = int(cx * ph / pw)
        if cy > MAX_H:
            cy, cx = MAX_H, int(MAX_H * pw / ph)
        for ext in kid.iter('{%s}extent' % NS['wp']):
            ext.set('cx', str(cx)); ext.set('cy', str(cy))
        for ext in kid.iter('{%s}ext' % NS['a']):
            if ext.get('cx') is not None:
                ext.set('cx', str(cx)); ext.set('cy', str(cy))
        for blip in kid.iter('{%s}blip' % NS['a']):
            blip.set('{%s}embed' % NS['r'], rid)
            for sub in list(blip):
                blip.remove(sub)          # drop image effects and links of the old picture
        for pr in kid.iter('{%s}docPr' % NS['wp']):
            pr.set('id', str(docpr)); pr.set('name', 'M9.4 Figure %d' % n); docpr += 1
        for pr in kid.iter('{%s}cNvPr' % NS['pic']):
            pr.set('name', 'm94_fig%02d.png' % n)

        parent = run.getparent()
        i = parent.index(run)
        dl = etree.Element(q('del'), {q('id'): str(rev), q('author'): a.author, q('date'): a.date}); rev += 1
        ins = etree.Element(q('ins'), {q('id'): str(rev), q('author'): a.author, q('date'): a.date}); rev += 1
        parent.remove(run)
        dl.append(run)
        ins.append(new_run)
        parent.insert(i, dl)
        parent.insert(i + 1, ins)
        print('figure %d: %s, %.2f x %.2f cm' % (n, path.split('/')[-1].split('\\')[-1], cx / EMU_CM, cy / EMU_CM))

    files['word/document.xml'] = etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)
    files['word/_rels/document.xml.rels'] = etree.tostring(rels, xml_declaration=True, encoding='UTF-8',
                                                           standalone=True)
    files['[Content_Types].xml'] = ct.encode('utf8')
    with zipfile.ZipFile(a.output, 'w', zipfile.ZIP_DEFLATED) as zout:
        for n in zin.namelist():
            zout.writestr(zin.getinfo(n), files[n])
        for n in files:
            if n not in zin.namelist():
                zout.writestr(n, files[n])


if __name__ == '__main__':
    main()
