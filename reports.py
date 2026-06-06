"""Monthly sales report generator: CSV + PDF for director."""

import io
import csv
from datetime import datetime
from typing import List, Dict, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _filter_in_month(items: List[Dict], year: int, month: int, key: str = "created_at") -> List[Dict]:
    prefix = f"{year:04d}-{month:02d}"
    return [i for i in items if isinstance(i.get(key), str) and i[key].startswith(prefix)]


def _fmt(n) -> str:
    try:
        return f"{int(round(float(n))):,}".replace(",", " ")
    except Exception:
        return "0"


def build_csv(year: int, month: int, sales: List[Dict], orders: List[Dict]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Maison Glow - Oylik hisobot"])
    w.writerow(["Davr", f"{year}-{month:02d}"])
    w.writerow([])

    w.writerow(["DO'KON SOTUVLARI"])
    w.writerow(["Sana", "Sotuvchi", "Mijoz", "Telefon", "Mahsulot", "Soni",
                "Asl narx", "Chegirma %", "Sotilgan narx", "Xarid narxi",
                "Chegirma jami", "Foyda", "Jami (so'm)", "Sabab"])
    sales_rev = sales_cost = sales_profit = sales_disc = 0
    for s in sales:
        sales_rev += s.get("total", 0)
        sales_cost += s.get("cost_total", 0)
        sales_profit += s.get("profit", 0)
        sales_disc += s.get("discount_total", 0)
        w.writerow([
            s.get("created_at", "")[:10],
            s.get("worker_name", ""),
            f"{s.get('customer_name','')} {s.get('customer_surname','')}".strip(),
            s.get("customer_phone", ""),
            s.get("product_name", ""),
            s.get("quantity", 0),
            s.get("original_price", s.get("product_price", 0)),
            s.get("discount_percent", 0),
            s.get("product_price", 0),
            s.get("cost_price", 0),
            s.get("discount_total", 0),
            s.get("profit", 0),
            s.get("total", 0),
            s.get("reason", ""),
        ])
    w.writerow([])
    w.writerow(["Jami sotuvlar:", len(sales), "", "", "", "", "", "", "", "",
                sales_disc, sales_profit, sales_rev])
    w.writerow([])

    w.writerow(["ONLAYN BUYURTMALAR"])
    w.writerow(["Sana", "Mijoz", "Telefon", "Email", "Mahsulot", "Soni",
                "Sotilgan narx", "Chegirma jami", "Foyda", "Jami (so'm)", "Lat", "Lng"])
    orders_rev = orders_cost = orders_profit = orders_disc = 0
    for o in orders:
        orders_rev += o.get("total", 0)
        orders_cost += o.get("cost_total", 0)
        orders_profit += o.get("profit", 0)
        orders_disc += o.get("discount_total", 0)
        loc = o.get("location") or {}
        w.writerow([
            o.get("created_at", "")[:10],
            f"{o.get('customer_name','')} {o.get('customer_surname','')}".strip(),
            o.get("customer_phone", ""),
            o.get("customer_email", ""),
            o.get("product_name", ""),
            o.get("quantity", 0),
            o.get("product_price", 0),
            o.get("discount_total", 0),
            o.get("profit", 0),
            o.get("total", 0),
            loc.get("lat", ""),
            loc.get("lng", ""),
        ])
    w.writerow([])
    w.writerow(["Jami buyurtmalar:", len(orders), "", "", "", "", "",
                orders_disc, orders_profit, orders_rev])
    w.writerow([])
    w.writerow(["UMUMIY DAROMAD:", "", "", "", "", "", "", "", "", sales_rev + orders_rev])
    w.writerow(["XARID NARXI:", "", "", "", "", "", "", "", "", sales_cost + orders_cost])
    w.writerow(["SOF FOYDA:", "", "", "", "", "", "", "", "", sales_profit + orders_profit])
    w.writerow(["JAMI CHEGIRMA:", "", "", "", "", "", "", "", "", sales_disc + orders_disc])

    return buf.getvalue().encode("utf-8-sig")


def build_pdf(year: int, month: int, sales: List[Dict], orders: List[Dict]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=1.4 * cm, leftMargin=1.4 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title=f"Maison Glow - {year}-{month:02d}",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Heading1"],
        textColor=colors.HexColor("#2A1114"), fontSize=22, leading=26, spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "sub", parent=styles["Normal"],
        textColor=colors.HexColor("#9C433E"), fontSize=10, leading=14, spaceAfter=18,
    )
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=colors.HexColor("#2A1114"), fontSize=14, spaceAfter=8, spaceBefore=12)
    body = ParagraphStyle("body", parent=styles["Normal"], textColor=colors.HexColor("#1A1919"), fontSize=10, leading=13)

    story = []
    story.append(Paragraph("Doctor·VITA", title_style))
    story.append(Paragraph(f"OYLIK HISOBOT  ·  {year} - {month:02d}", sub_style))

    sales_rev = sum(s.get("total", 0) for s in sales)
    sales_cost = sum(s.get("cost_total", 0) for s in sales)
    sales_profit = sum(s.get("profit", 0) for s in sales)
    sales_disc = sum(s.get("discount_total", 0) for s in sales)

    orders_rev = sum(o.get("total", 0) for o in orders)
    orders_cost = sum(o.get("cost_total", 0) for o in orders)
    orders_profit = sum(o.get("profit", 0) for o in orders)
    orders_disc = sum(o.get("discount_total", 0) for o in orders)

    total_rev = sales_rev + orders_rev
    total_cost = sales_cost + orders_cost
    total_profit = sales_profit + orders_profit
    total_disc = sales_disc + orders_disc

    summary_data = [
        ["Ko'rsatkich", "Soni", "Daromad", "Xarid", "Foyda", "Chegirma"],
        ["Do'kon sotuvlari", str(len(sales)), _fmt(sales_rev), _fmt(sales_cost), _fmt(sales_profit), _fmt(sales_disc)],
        ["Onlayn buyurtmalar", str(len(orders)), _fmt(orders_rev), _fmt(orders_cost), _fmt(orders_profit), _fmt(orders_disc)],
        ["UMUMIY", str(len(sales) + len(orders)), _fmt(total_rev), _fmt(total_cost), _fmt(total_profit), _fmt(total_disc)],
    ]
    t = Table(summary_data, colWidths=[4.5 * cm, 1.6 * cm, 3.0 * cm, 2.7 * cm, 2.7 * cm, 2.8 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2A1114")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#FAFAF7")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F2EFE9")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E1D8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#FAFAF7")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # Per-worker summary
    worker_totals: Dict[str, Tuple[int, int, int]] = {}
    for s in sales:
        wname = s.get("worker_name", "—")
        cnt, rev, prof = worker_totals.get(wname, (0, 0, 0))
        worker_totals[wname] = (cnt + s.get("quantity", 0), rev + s.get("total", 0), prof + s.get("profit", 0))
    if worker_totals:
        story.append(Paragraph("Sotuvchilar reytingi", h2))
        wdata = [["Sotuvchi", "Mahsulot soni", "Daromad", "Foyda"]]
        for name, (c, r, pr) in sorted(worker_totals.items(), key=lambda kv: -kv[1][1]):
            wdata.append([name, str(c), _fmt(r), _fmt(pr)])
        wt = Table(wdata, colWidths=[6 * cm, 3 * cm, 4 * cm, 4 * cm])
        wt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#9C433E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#FAFAF7")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E1D8")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAF7")]),
        ]))
        story.append(wt)
        story.append(Spacer(1, 0.5 * cm))

    # Sales table
    story.append(Paragraph("Do'kon sotuvlari", h2))
    if sales:
        data = [["Sana", "Sotuvchi", "Mijoz", "Mahsulot", "Soni", "Chegirma", "Foyda", "Jami"]]
        for s in sales:
            data.append([
                (s.get("created_at", "") or "")[:10],
                (s.get("worker_name", "") or "")[:14],
                f"{s.get('customer_name','')} {s.get('customer_surname','')}"[:18],
                (s.get("product_name", "") or "")[:18],
                str(s.get("quantity", 0)),
                _fmt(s.get("discount_total", 0)),
                _fmt(s.get("profit", 0)),
                _fmt(s.get("total", 0)),
            ])
        st = Table(data, colWidths=[1.9 * cm, 2.4 * cm, 2.8 * cm, 3.0 * cm, 1.0 * cm, 2.2 * cm, 2.2 * cm, 2.3 * cm], repeatRows=1)
        st.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2A1114")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#FAFAF7")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("ALIGN", (-3, 1), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E1D8")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAF7")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(st)
    else:
        story.append(Paragraph("Bu davrda sotuvlar yo'q.", body))
    story.append(Spacer(1, 0.5 * cm))

    # Orders table
    story.append(Paragraph("Onlayn buyurtmalar", h2))
    if orders:
        odata = [["Sana", "Mijoz", "Telefon", "Mahsulot", "Chegirma", "Foyda", "Jami"]]
        for o in orders:
            odata.append([
                (o.get("created_at", "") or "")[:10],
                f"{o.get('customer_name','')} {o.get('customer_surname','')}"[:18],
                (o.get("customer_phone", "") or "")[:14],
                (o.get("product_name", "") or "")[:18],
                _fmt(o.get("discount_total", 0)),
                _fmt(o.get("profit", 0)),
                _fmt(o.get("total", 0)),
            ])
        ot = Table(odata, colWidths=[2.0 * cm, 3.4 * cm, 2.8 * cm, 3.4 * cm, 2.3 * cm, 2.3 * cm, 2.6 * cm], repeatRows=1)
        ot.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#9C433E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#FAFAF7")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (-3, 1), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E1D8")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAF7")]),
        ]))
        story.append(ot)
    else:
        story.append(Paragraph("Bu davrda onlayn buyurtmalar yo'q.", body))

    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(f"Tayyorlangan: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body))

    doc.build(story)
    return buf.getvalue()
