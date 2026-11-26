"""Put one figure on its own landscape page, as Word tracked changes (M9.4, DEC-031).

    python landfig.py IN.docx OUT.docx MEDIA NEW.png [--max-h-in 5.3] [--author Claude] [--date ...]

MEDIA is the file name under word/media of a picture that an earlier swapfig.py run inserted (a tracked w:ins run in
the figure's caption paragraph). The script:
  * replaces that picture with NEW.png, as an inline picture in a new tracked paragraph just above the caption;
  * adds a tracked empty paragraph before that (ends the portrait section, copy of the governing sectPr);
  * adds a tracked empty paragraph after the caption carrying a landscape sectPr (top margin 1.5 in for binding,
    vertically centred, no first-page footer switch);
  * drops titlePg from the governing sectPr as a tracked section change, since its section now starts after the
    landscape page;
  * marks deleted the spacer lines above the caption (all but the first) and the empty paragraph right after it, so
    no blank page appears and the next page does not start with a blank line.
Rejecting all changes gives the input document back.
"""
import argparse, copy, re, struct, zipfile
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
WP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'w': W, 'wp': WP, 'a': A, 'r': R}
q = lambda t: '{%s}%s' % (W, t)
EMU_IN = 914400


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input'); ap.add_argument('output'); ap.add_argument('media'); ap.add_argument('png')
    ap.add_argument('--max-h-in', type=float, default=5.3)
    ap.add_argument('--author', default='Claude'); ap.add_argument('--date', default='2026-11-26T00:00:00Z')
    a = ap.parse_args()

    zin = zipfile.ZipFile(a.input)
    files = {n: zin.read(n) for n in zin.namelist()}
    doc = etree.fromstring(files['word/document.xml'])
    rels = etree.fromstring(files['word/_rels/document.xml.rels'])
    body = doc.find('w:body', NS)
    rid = [r.get('Id') for r in rels if r.get('Target') == 'media/' + a.media][0]
    data = open(a.png, 'rb').read()
    pw, ph = struct.unpack('>II', data[16:24])
    files['word/media/' + a.media] = data

    rev = [max(int(x) for x in doc.xpath('//w:ins/@w:id|//w:del/@w:id', namespaces=NS)) + 1000]

    def tag(kind):
        rev[0] += 1
        return etree.Element(q(kind), {q('id'): str(rev[0]), q('author'): a.author, q('date'): a.date})

    blip = [b for b in doc.iter('{%s}blip' % A) if b.get('{%s}embed' % R) == rid][0]
    ins_run_wrap = blip
    while ins_run_wrap.tag != q('ins'):
        ins_run_wrap = ins_run_wrap.getparent()
    cap = ins_run_wrap.getparent()
    assert cap.getparent() is body, 'caption paragraph not at body level'
    run = ins_run_wrap.find('w:r', NS)
    anchor = run.find('w:drawing/wp:anchor', NS)

    # inline picture sized to the landscape text area
    cy = int(a.max_h_in * EMU_IN)
    cx = int(cy * pw / ph)
    if cx > 9 * EMU_IN:
        cx, cy = 9 * EMU_IN, int(9 * EMU_IN * ph / pw)
    inline = etree.Element('{%s}inline' % WP, distT='0', distB='0', distL='0', distR='0')
    for name in ('extent', 'effectExtent', 'docPr', 'cNvGraphicFramePr'):
        el = anchor.find('wp:' + name, NS)
        if el is not None:
            inline.append(copy.deepcopy(el))
    inline.append(copy.deepcopy(anchor.find('a:graphic', NS)))
    for ext in inline.iter('{%s}extent' % WP):
        ext.set('cx', str(cx)); ext.set('cy', str(cy))
    for ext in inline.iter('{%s}ext' % A):
        if ext.get('cx') is not None:
            ext.set('cx', str(cx)); ext.set('cy', str(cy))
    new_run = etree.Element(q('r'))
    etree.SubElement(etree.SubElement(new_run, q('rPr')), q('noProof'))
    etree.SubElement(new_run, q('drawing')).append(inline)
    cap.remove(ins_run_wrap)             # the 2.13 anchored insert goes; the tracked deletion of the original stays

    def new_para(jc=None, sect=None, child=None):
        p = etree.Element(q('p'))
        ppr = etree.SubElement(p, q('pPr'))
        if jc:
            etree.SubElement(ppr, q('spacing'), {q('after'): '120', q('line'): '240', q('lineRule'): 'auto'})
            etree.SubElement(ppr, q('jc'), {q('val'): jc})
        rpr = etree.SubElement(ppr, q('rPr'))
        rpr.append(tag('ins'))
        if sect is not None:
            ppr.append(sect)
        if child is not None:
            w = tag('ins'); w.append(child); p.append(w)
        return p

    # governing sectPr = the next one after the caption
    gov = None
    for e in body[body.index(cap):]:
        gov = e.find('w:pPr/w:sectPr', NS) if e.tag == q('p') else (e if e.tag == q('sectPr') else None)
        if gov is not None:
            break
    portrait = copy.deepcopy(gov)
    for x in portrait.findall('w:sectPrChange', NS):
        portrait.remove(x)
    land = copy.deepcopy(portrait)
    for x in land.findall('w:titlePg', NS) + land.findall('w:type', NS) + land.findall('w:vAlign', NS):
        land.remove(x)
    land.find('w:pgSz', NS).attrib.update({q('w'): '15840', q('h'): '12240', q('orient'): 'landscape'})
    land.find('w:pgMar', NS).attrib.update({q('top'): '2160', q('right'): '1440', q('bottom'): '1440', q('left'): '1440'})
    land.insert(list(land).index(land.find('w:cols', NS)) + 1, etree.Element(q('vAlign'), {q('val'): 'center'}))

    def mark_deleted(p):
        ppr = p.find('w:pPr', NS)
        if ppr is None:
            ppr = etree.Element(q('pPr')); p.insert(0, ppr)
        rpr = ppr.find('w:rPr', NS)
        if rpr is None:
            rpr = etree.SubElement(ppr, q('rPr'))
        rpr.insert(0, tag('del'))

    def blank(p):
        return (p.tag == q('p') and not ''.join(p.itertext()).strip() and p.find('.//w:drawing', NS) is None
                and p.find('.//w:sectPr', NS) is None)

    # empty spacer lines above the caption held room for the floating picture; keep the first, delete the rest
    i = body.index(cap)
    k = i
    while k > 0 and blank(body[k - 1]):
        k -= 1
    for p in list(body[k + 1:i]):
        mark_deleted(p)

    body.insert(i, new_para(jc='center', child=new_run))           # picture above the caption
    body.insert(i, new_para(sect=portrait))                          # ends the portrait section
    i = body.index(cap)
    body.insert(i + 1, new_para(sect=land))                          # ends the landscape section
    nxt = body[i + 2]
    if blank(nxt):
        mark_deleted(nxt)

    if gov.find('w:titlePg', NS) is not None:
        old = copy.deepcopy(gov)
        for x in old.findall('w:sectPrChange', NS):
            old.remove(x)
        old.attrib.clear()
        gov.remove(gov.find('w:titlePg', NS))
        ch = tag('sectPrChange'); ch.append(old); gov.append(ch)

    print('landscape figure: %.2f x %.2f in' % (cx / EMU_IN, cy / EMU_IN))
    files['word/document.xml'] = etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)
    with zipfile.ZipFile(a.output, 'w', zipfile.ZIP_DEFLATED) as zout:
        for n in zin.namelist():
            zout.writestr(zin.getinfo(n), files[n])


if __name__ == '__main__':
    main()
