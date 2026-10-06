"""Product mark for the Review Copilot. Concept: three document versions fanned behind one another; the front sheet is the version in force
on the date of service, and it carries the verification check. The mark says what the product does: pick the right document, verify the evidence.
Writes public/logo.svg (used by the app and as favicon), docs/logo.png and public/logo.png (transparent, 512 px), docs/logo_wordmark.png.   python scripts/build_logo.py"""
import os
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import pypdfium2 as pdfium
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="Review Copilot">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#14B8A6"/><stop offset="1" stop-color="#0E7490"/></linearGradient></defs>
<rect width="64" height="64" rx="15" fill="url(#g)"/>
<rect x="27" y="11" width="21" height="27" rx="3" fill="#fff" fill-opacity=".26"/>
<rect x="21.5" y="15.5" width="21" height="27" rx="3" fill="#fff" fill-opacity=".48"/>
<rect x="16" y="20" width="23" height="29" rx="3.5" fill="#fff"/>
<rect x="20" y="26" width="11" height="2.4" rx="1.2" fill="#0F766E" fill-opacity=".55"/>
<rect x="20" y="31.6" width="15" height="2.4" rx="1.2" fill="#0F766E" fill-opacity=".55"/>
<rect x="20" y="37.2" width="9" height="2.4" rx="1.2" fill="#0F766E" fill-opacity=".55"/>
<circle cx="41" cy="46" r="9.5" fill="#0A1F2B"/>
<path d="M36.2 46.3l3.1 3.1 6.3-6.6" stroke="#2DD4BF" stroke-width="2.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''
open(os.path.join(ROOT, "public", "logo.svg"), "w").write(SVG)

def mark(c, x, y, s):
    """Same mark drawn with reportlab primitives, at size s with bottom-left corner (x, y)."""
    u = s / 64.0
    def R(px, py, w, h, r, col, a=1): c.setFillColor(col, alpha=a); c.roundRect(x + px * u, y + (64 - py - h) * u, w * u, h * u, r * u, stroke=0, fill=1)
    c.saveState()
    # gradient tile: approximate with a vertical band gradient clipped to a rounded rect
    p = c.beginPath(); p.roundRect(x, y, s, s, 15 * u); c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(x, y + s, x + s, y, (colors.HexColor("#14B8A6"), colors.HexColor("#0E7490")), extend=True)
    c.restoreState(); c.saveState()
    R(27, 11, 21, 27, 3, colors.white, .26); R(21.5, 15.5, 21, 27, 3, colors.white, .48); R(16, 20, 23, 29, 3.5, colors.white)
    t = colors.HexColor("#0F766E"); R(20, 26, 11, 2.4, 1.2, t, .55); R(20, 31.6, 15, 2.4, 1.2, t, .55); R(20, 37.2, 9, 2.4, 1.2, t, .55)
    c.setFillColor(colors.HexColor("#0A1F2B"), alpha=1); c.circle(x + 41 * u, y + (64 - 46) * u, 9.5 * u, stroke=0, fill=1)
    c.setStrokeColor(colors.HexColor("#2DD4BF")); c.setLineWidth(2.7 * u); c.setLineCap(1); c.setLineJoin(1)
    pth = c.beginPath(); pth.moveTo(x + 36.2 * u, y + (64 - 46.3) * u); pth.lineTo(x + 39.3 * u, y + (64 - 49.4) * u); pth.lineTo(x + 45.6 * u, y + (64 - 42.8) * u); c.drawPath(pth, stroke=1, fill=0)
    c.restoreState()

def render(pdf_path, png_path, scale):
    pg = pdfium.PdfDocument(pdf_path)[0]; pg.render(scale=scale, fill_color=(0, 0, 0, 0)).to_pil().save(png_path)

if __name__ == "__main__":
    tmp = os.path.join(ROOT, ".cache"); os.makedirs(tmp, exist_ok=True)
    p = os.path.join(tmp, "logo.pdf"); c = canvas.Canvas(p, pagesize=(64, 64)); mark(c, 0, 0, 64); c.save()
    for out, sc in ((os.path.join(ROOT, "docs", "logo.png"), 8), (os.path.join(ROOT, "public", "logo.png"), 8), (os.path.join(ROOT, "public", "logo-192.png"), 3)): render(p, out, sc)
    # wordmark: mark + product name, for README and documents
    from reportlab.pdfbase import pdfmetrics; from reportlab.pdfbase.ttfonts import TTFont
    F = os.path.join(ROOT, "docs", "fonts")
    pdfmetrics.registerFont(TTFont("IB", os.path.join(F, "Inter-700.ttf"))); pdfmetrics.registerFont(TTFont("IM", os.path.join(F, "Inter-500.ttf")))
    p2 = os.path.join(tmp, "wordmark.pdf"); c = canvas.Canvas(p2, pagesize=(300, 64)); mark(c, 0, 0, 64)
    c.setFillColor(colors.HexColor("#10232B")); c.setFont("IB", 24); c.drawString(78, 30, "Review Copilot"); c.setFillColor(colors.HexColor("#5B6B76")); c.setFont("IM", 10.5); c.drawString(79, 14, "Bellcourt Health Administrators"); c.save()
    render(p2, os.path.join(ROOT, "docs", "logo_wordmark.png"), 4)
    print("logo written: public/logo.svg public/logo.png public/logo-192.png docs/logo.png docs/logo_wordmark.png")
