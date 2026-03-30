"""
utils/pdf_generator.py
======================
Générateur PDF centralisé pour les rapports ESM.

Architecture :
  PdfBuilder        – briques génériques réutilisables
  DocumentGenerator – façade publique : une méthode par type de rapport

Rapports disponibles :
  generate_rapport_ventes(data, debut, fin, taux)
  generate_rapport_resultat(data, debut, fin, taux)
  generate_rapport_articles(data, taux)
  generate_rapport_caisse(data, debut, fin, taux)
  generate_bon_commande(data)
  generate_excel(data)
"""

import logging
import math
import mimetypes
import os
import datetime
from decimal import Decimal
from functools import cached_property
from io import BytesIO
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.http import HttpResponse
from django.template.defaultfilters import date as django_date_filter

from openpyxl import Workbook
from openpyxl.styles import Font

from num2words import num2words

import reportlab.rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A5, LETTER, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from parametres.models import Parametre

logger = logging.getLogger(__name__)

# ── Fonts ──────────────────────────────────────────────────────────────────────
_font_dir = os.path.join(settings.STATIC_ROOT, 'fonts', 'roboto')
reportlab.rl_config.warnOnMissingFontGlyphs = 0

for _alias, _file in [
    ('Roboto',      'Roboto-Regular.ttf'),
    ('RobotoBd',    'Roboto-Bold.ttf'),
    ('RobotoBdIt',  'Roboto-BoldItalic.ttf'),
    ('RobotoBl',    'Roboto-Black.ttf'),
    ('RobotoBlIt',  'Roboto-BlackItalic.ttf'),
    ('RobotoIt',    'Roboto-Italic.ttf'),
    ('RobotoLg',    'Roboto-Light.ttf'),
    ('RobotoLgIt',  'Roboto-LightItalic.ttf'),
    ('RobotoTh',    'Roboto-Thin.ttf'),
    ('RobotoThIt',  'Roboto-ThinItalic.ttf'),
    ('RobotoMd',    'Roboto-Medium.ttf'),
    ('RobotoMdIt',  'Roboto-MediumItalic.ttf'),
]:
    pdfmetrics.registerFont(TTFont(_alias, os.path.join(_font_dir, _file)))

pdfmetrics.registerFontFamily(
    'Roboto',
    normal='Roboto', bold='RobotoBd',
    italic='RobotoIt', boldItalic='RobotoBdIt',
)

# ── Styles de paragraphe ───────────────────────────────────────────────────────
_styles = getSampleStyleSheet()
for _name, _align, _font, _size in [
    ('Droite',        TA_RIGHT,  'Roboto',   10),
    ('Gauche',        TA_LEFT,   'Roboto',   10),
    ('Centre',        TA_CENTER, 'Roboto',   12),
    ('Centre_footer', TA_CENTER, 'Roboto',    8),
    ('Titre',         TA_CENTER, 'RobotoBd', 14),
    ('Titre_gauche',  TA_LEFT,   'RobotoBd', 13),
    ('Sous_titre',    TA_LEFT,   'RobotoIt', 10),
    ('Elements',      TA_LEFT,   'Roboto',    7),
    ('Total',         TA_RIGHT,  'RobotoBd', 12),
    ('Total_lettre',  TA_CENTER, 'RobotoBd', 11),
    ('KPI_label',     TA_LEFT,   'RobotoBd',  8),
    ('KPI_value',     TA_RIGHT,  'RobotoBd', 11),
]:
    _styles.add(ParagraphStyle(name=_name, alignment=_align,
                               fontName=_font, fontSize=_size))


# ══════════════════════════════════════════════════════════════════════════════
# Helpers ReportLab
# ══════════════════════════════════════════════════════════════════════════════

class LineFlowable(Flowable):
    """Ligne horizontale servant de séparateur."""

    def __init__(self, x_start, x_end, height=0, color=colors.black, thickness=0.5):
        Flowable.__init__(self)
        self.x_start = x_start
        self.x_end = x_end
        self.height = height
        self.color = color
        self.thickness = thickness
        self.width = x_end - x_start

    def __repr__(self):
        return f'Line({self.x_start}→{self.x_end})'

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(self.x_start, self.height, self.x_end, self.height)


class FooterCanvas(canvas.Canvas):
    """Canvas avec en-tête société et pied de page (numéro de page, contacts)."""

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
        self._page_size = kwargs.get('pagesize', LETTER)

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self._draw_footer(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _draw_footer(self, page_count):
        try:
            params = Parametre.objects.get(code='Params')
        except Parametre.DoesNotExist:
            return

        width = self._page_size[0]

        pr = Paragraph(
            f'{params.telephone}<br/>{params.email}<br/>'
            f'{params.adresse}<br/>{params.ville} - {params.pays}',
            style=_styles['Droite'],
        )
        pl = Paragraph(
            f'RCCM: {params.rccm}<br/>Id.Nat.: {params.idnat}<br/>'
            f'N° impôt: {params.impot}<br/>TVA: {params.tva}',
            style=_styles['Gauche'],
        )

        self.saveState()
        self.setStrokeColorRGB(0, 0, 0)
        self.setLineWidth(0.5)
        self.line(25, 60, width - 25, 60)

        col_w = (width - 50) / 2
        pl.wrapOn(self, col_w, 50)
        pl.drawOn(self, 25, 10)
        pr.wrapOn(self, col_w, 50)
        pr.drawOn(self, 25 + col_w, 10)

        self.setFont('Roboto', 8)
        self.drawRightString(
            width - 25, 63,
            f'Page {self._pageNumber} / {page_count}',
        )
        self.restoreState()


def _fc_to_usd_equiv(valeur_fc, taux) -> Decimal | None:
    """
    Contre-valeur USD : valeur_fc (FC) / taux.
    Accepte Decimal, int ou float pour valeur_fc ; évite Decimal / float (TypeError).
    """
    if taux is None:
        return None
    tx = taux if isinstance(taux, Decimal) else Decimal(str(taux))
    if tx <= 0:
        return None
    v = valeur_fc if isinstance(valeur_fc, Decimal) else Decimal(str(valeur_fc))
    return v / tx


# ══════════════════════════════════════════════════════════════════════════════
# PdfBuilder — briques génériques
# ══════════════════════════════════════════════════════════════════════════════

class PdfBuilder:
    """Fournit les briques génériques communes à tous les rapports."""

    # Palette
    DARK_BLUE  = colors.Color(42 / 255,  63 / 255,  84 / 255)   # #2A3F54
    TEAL       = colors.Color(38 / 255, 185 / 255, 154 / 255)   # #26B99A
    LIGHT_GREY = colors.Color(0.96, 0.97, 0.98)
    MID_GREY   = colors.Color(0.88, 0.88, 0.88)

    def __init__(self, filename: str, title: str):
        self.filename = filename
        self.title = title

    @cached_property
    def params(self) -> Parametre:
        return Parametre.objects.get(code='Params')

    # ── Logo ──────────────────────────────────────────────────────────────────

    def _logo(self, width_in=1.5, height_in=1.5) -> Image:
        return Image(self.params.logo.path, width_in * inch, height_in * inch)

    # ── En-tête ───────────────────────────────────────────────────────────────

    def _header_flowable(self, page_width: float) -> Table:
        """
        Retourne une Table 3 colonnes :
          [Logo]  [Nom société + infos]  [Ville + date]
        """
        p = self.params
        im = self._logo(1.4, 1.4)

        societe_para = Paragraph(
            f'<b>{p.societe}</b><br/>{p.adresse}<br/>'
            f'Tél : {p.telephone}<br/>Email : {p.email}',
            style=_styles['Gauche'],
        )
        date_para = Paragraph(
            f'{p.ville}, le <b>{datetime.datetime.now().strftime("%d/%m/%Y")}</b>',
            style=_styles['Droite'],
        )

        margins = 30
        inner = page_width - margins
        col1 = 1.5 * inch
        col3 = 1.8 * inch
        col2 = inner - col1 - col3

        tbl = Table([[im, societe_para, date_para]],
                    colWidths=[col1, col2, col3])
        tbl.setStyle(TableStyle([
            ('VALIGN',  (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME',(0, 0), (-1, -1), 'Roboto'),
            ('FONTSIZE',(0, 0), (-1, -1), 9),
        ]))
        return tbl

    # ── Séparateur ────────────────────────────────────────────────────────────

    def _separator(self, page_width: float, margins: int = 30) -> LineFlowable:
        return LineFlowable(0, page_width - margins, color=self.DARK_BLUE, thickness=1)

    def _thin_separator(self, page_width: float, margins: int = 30) -> LineFlowable:
        return LineFlowable(0, page_width - margins, color=self.MID_GREY, thickness=0.4)

    # ── Titre + sous-titre ────────────────────────────────────────────────────

    def _title_block(self, page_width: float, subtitle: str = '') -> list:
        flowables = [
            Spacer(1, 8),
            Paragraph(self.title, style=_styles['Titre_gauche']),
        ]
        if subtitle:
            flowables.append(Paragraph(subtitle, style=_styles['Sous_titre']))
        flowables += [
            Spacer(1, 4),
            self._separator(page_width),
            Spacer(1, 10),
        ]
        return flowables

    # ── Table de données générique ────────────────────────────────────────────

    def _data_table(
        self,
        headers: list,
        rows: list,
        col_widths: list,
        stripe: bool = True,
        align_right_cols: list = None,
        align_center_cols: list = None,
    ) -> list:
        """
        Construit une table avec en-tête colorée et lignes zébrées.
        align_right_cols / align_center_cols : indices 0-based des colonnes à aligner.
        """
        align_right_cols = align_right_cols or []
        align_center_cols = align_center_cols or []

        # En-tête
        hdr_tbl = Table([headers], colWidths=col_widths)
        hdr_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.DARK_BLUE),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'RobotoBd'),
            ('FONTSIZE',   (0, 0), (-1, 0), 8),
            ('ALIGN',      (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN',     (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ]))

        if not rows:
            return [hdr_tbl]

        # Corps
        body_style = [
            ('FONTNAME',  (0, 0), (-1, -1), 'Roboto'),
            ('FONTSIZE',  (0, 0), (-1, -1), 8),
            ('VALIGN',    (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID',      (0, 0), (-1, -1), 0.3, self.MID_GREY),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN',     (0, 0), (-1, -1), 'LEFT'),
        ]
        if stripe:
            body_style.append(
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, self.LIGHT_GREY])
            )
        for col in align_right_cols:
            body_style.append(('ALIGN', (col, 0), (col, -1), 'RIGHT'))
        for col in align_center_cols:
            body_style.append(('ALIGN', (col, 0), (col, -1), 'CENTER'))

        body_tbl = Table(rows, colWidths=col_widths)
        body_tbl.setStyle(TableStyle(body_style))

        return [hdr_tbl, body_tbl]

    # ── Bloc de totaux ────────────────────────────────────────────────────────

    def _totals_block(self, lines: list, taux: float | Decimal | None = None) -> list:
        """
        lines = [(label, valeur_fc), ...]
        Si taux fourni, affiche la contre-valeur USD entre parenthèses.
        Dernier élément = total principal (police plus grande).
        """
        flowables = [Spacer(1, 10)]
        for i, (label, valeur_fc) in enumerate(lines):
            is_last = (i == len(lines) - 1)
            cv = ''
            cv_usd = _fc_to_usd_equiv(valeur_fc, taux)
            if cv_usd is not None:
                cv = f' <font size=8 color=grey>(≈ {cv_usd:,.2f} USD)</font>'

            fc_str = f'{valeur_fc:,.0f} FC'
            if is_last:
                text = f'<b><font size=13>{label} : {fc_str}</font></b>{cv}'
                flowables.append(Paragraph(text, style=_styles['Total']))
            else:
                text = f'{label} : <b>{fc_str}</b>{cv}'
                flowables.append(Paragraph(text, style=_styles['Droite']))
            flowables.append(Spacer(1, 4))
        return flowables

    @staticmethod
    def _montant_en_lettres(valeur_fc: float) -> str:
        """Retourne la représentation littérale du montant en FC."""
        try:
            frac, whole = math.modf(round(float(valeur_fc), 0))
            fc_txt = num2words(int(whole), lang='fr')
            if round(frac * 100) > 0:
                cents_txt = num2words(int(round(frac * 100)), lang='fr')
                return f'Nous disons {fc_txt} francs congolais et {cents_txt} centimes'
            return f'Nous disons {fc_txt} francs congolais'
        except Exception:
            return ''

    # ── Bloc KPI synthèse (section colorée) ───────────────────────────────────

    def _kpi_table(self, kpis: list, taux: float | Decimal | None = None) -> Table:
        """
        kpis = [(label, valeur_fc), ...]
        Retourne une Table une ligne, cellules colorées alternées.
        """
        cells = []
        for label, val in kpis:
            cv = ''
            cv_usd = _fc_to_usd_equiv(val, taux)
            if cv_usd is not None:
                cv = f'\n≈ {cv_usd:,.2f} USD'
            cells.append(
                Paragraph(
                    f'<font size=7 color=grey>{label}</font>\n'
                    f'<b><font size=11>{val:,.0f} FC</font></b>{cv}',
                    style=_styles['Centre'],
                )
            )
        col_w = (LETTER[0] - 30) / len(cells) if cells else 100
        tbl = Table([cells], colWidths=[col_w] * len(cells))
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_GREY),
            ('BOX',        (0, 0), (-1, -1), 0.5, self.MID_GREY),
            ('INNERGRID',  (0, 0), (-1, -1), 0.5, self.MID_GREY),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        return tbl

    # ── Réponse HTTP ──────────────────────────────────────────────────────────

    def _http_response(self, buffer: BytesIO) -> HttpResponse:
        data = buffer.getvalue()
        buffer.close()
        mimetype, encoding = mimetypes.guess_type(self.filename)
        if not mimetype:
            mimetype = 'application/pdf'
        if encoding:
            mimetype = f'{mimetype}; charset={encoding}'
        return HttpResponse(
            data,
            content_type=mimetype,
            headers={'Content-Disposition': f'attachment;filename={self.filename}'},
        )

    def _build(self, flowables: list, orientation: str = 'portrait') -> HttpResponse:
        """Assemble les flowables, appelle multiBuild et retourne la réponse."""
        buffer = BytesIO()
        page_size = LETTER if orientation == 'portrait' else landscape(LETTER)
        doc = SimpleDocTemplate(
            buffer, pagesize=page_size,
            rightMargin=15, leftMargin=15,
            topMargin=10, bottomMargin=65,
        )
        doc.multiBuild(flowables, canvasmaker=FooterCanvas)
        return self._http_response(buffer)


# ══════════════════════════════════════════════════════════════════════════════
# DocumentGenerator — façade publique
# ══════════════════════════════════════════════════════════════════════════════

class DocumentGenerator(PdfBuilder):
    """
    Une méthode par type de rapport.
    Toutes les méthodes acceptent `taux` (float, FC/USD) pour la contre-valeur.
    """

    # ── 1. Rapport des Ventes ─────────────────────────────────────────────────

    def generate_rapport_ventes(
        self,
        data: list,
        debut: datetime.date,
        fin: datetime.date,
        taux: float = 0,
    ) -> HttpResponse:
        """
        data = [{'numero', 'date_facture', 'client', 'devise',
                 'taux', 'remise', 'total'}, ...]
        """
        page_w = LETTER[0]
        subtitle = f'Période : du {debut.strftime("%d/%m/%Y")} au {fin.strftime("%d/%m/%Y")}'

        flowables = [self._header_flowable(page_w), Spacer(1, 6)]
        flowables += self._title_block(page_w, subtitle)

        headers = ['#', 'Date', 'Client', 'Dev.', 'Taux', 'Remise (FC)', 'Total (FC)']
        col_widths = [30, 80, 170, 35, 50, 75, 90]

        rows = [
            [
                str(i + 1),
                str(item.get('date_facture', '')),
                str(item.get('client') or '—'),
                str(item.get('devise', 'FC')),
                str(item.get('taux', '—')),
                f"{float(item.get('remise') or 0):,.0f}",
                f"{float(item.get('total') or 0):,.0f}",
            ]
            for i, item in enumerate(data)
        ]

        flowables += self._data_table(
            headers, rows, col_widths,
            align_right_cols=[4, 5, 6],
            align_center_cols=[0, 3],
        )

        # Totaux
        total_fc = sum(float(item.get('total') or 0) for item in data)
        nb = len(data)
        flowables += [Spacer(1, 6), self._thin_separator(page_w)]
        flowables += self._totals_block([
            (f'Nombre de factures', nb),
            ('Total ventes', total_fc),
        ], taux=taux)

        if total_fc > 0:
            flowables.append(Spacer(1, 8))
            flowables.append(Paragraph(
                self._montant_en_lettres(total_fc),
                style=_styles['Total_lettre'],
            ))

        if taux > 0:
            flowables.append(Spacer(1, 4))
            flowables.append(Paragraph(
                f'<font size=8 color=grey>Taux de référence : 1 USD = {taux:,.0f} FC</font>',
                style=_styles['Droite'],
            ))

        return self._build(flowables, orientation='portrait')

    # ── 2. Rapport des Résultats ──────────────────────────────────────────────

    def generate_rapport_resultat(
        self,
        total_ventes: float,
        total_appros: float,
        articles: list,
        debut: datetime.date,
        fin: datetime.date,
        taux: float = 0,
    ) -> HttpResponse:
        """
        articles = [{'designation', 'resultat', 'pourcentage'}, ...]
        """
        page_w = LETTER[0]
        total_global = total_appros
        subtitle = f'Période : du {debut.strftime("%d/%m/%Y")} au {fin.strftime("%d/%m/%Y")}'

        flowables = [self._header_flowable(page_w), Spacer(1, 6)]
        flowables += self._title_block(page_w, subtitle)

        # KPI synthèse
        flowables.append(self._kpi_table([
            ('Résultat ventes',   total_ventes),
            ('Résultat appros',   total_appros),
            ('Résultat de référence', total_global),
        ], taux=taux))
        flowables.append(Spacer(1, 12))

        # Tableau par article
        flowables.append(Paragraph('Détail par article', style=_styles['Titre_gauche']))
        flowables.append(Spacer(1, 4))

        headers = ['Article', 'Résultat (FC)', '% du résultat appros']
        col_widths = [320, 120, 80]
        rows = [
            [
                str(a.get('designation', '')),
                f"{float(a.get('resultat') or 0):+,.0f}",
                f"{float(a.get('pourcentage') or 0):.1f} %",
            ]
            for a in articles
        ]
        flowables += self._data_table(
            headers, rows, col_widths,
            align_right_cols=[1, 2],
        )

        flowables += [Spacer(1, 6), self._thin_separator(page_w)]
        flowables += self._totals_block(
            [('Résultat de référence', total_global)],
            taux=taux,
        )

        if total_global != 0:
            flowables.append(Spacer(1, 8))
            flowables.append(Paragraph(
                self._montant_en_lettres(abs(total_global)),
                style=_styles['Total_lettre'],
            ))

        if taux > 0:
            flowables.append(Spacer(1, 4))
            flowables.append(Paragraph(
                f'<font size=8 color=grey>Taux de référence : 1 USD = {taux:,.0f} FC</font>',
                style=_styles['Droite'],
            ))

        return self._build(flowables, orientation='portrait')

    # ── 3. Rapport des Articles (stock) ───────────────────────────────────────

    def generate_rapport_articles(
        self,
        rows: list,
        total_valeur_stock: float,
        ca_total_30j: float,
        resultat_total_30j: float,
        taux: float = 0,
    ) -> HttpResponse:
        """
        rows = [{'designation', 'valeur_stock', 'ca_30j', 'resultat_30j',
                 'moy_stock_30j', 'pct_stock', 'pct_ca'}, ...]
        Orientation : Landscape Letter.
        """
        page_w = landscape(LETTER)[0]
        today = datetime.date.today()
        subtitle = f'Situation au {today.strftime("%d/%m/%Y")} — 30 derniers jours'

        flowables = [self._header_flowable(page_w), Spacer(1, 6)]
        flowables += self._title_block(page_w, subtitle)

        # KPIs
        flowables.append(self._kpi_table([
            ('Valeur totale stock',  total_valeur_stock),
            ('CA 30 jours',          ca_total_30j),
            ('Résultat 30 jours',    resultat_total_30j),
        ], taux=taux))
        flowables.append(Spacer(1, 10))

        # Tableau
        headers = ['#', 'Article', 'Stock\nactuel', 'Valeur stock\n(FC)', '% stk',
                   'CA 30j\n(FC)', '% CA', 'Résultat 30j\n(FC)', 'Moy. stock\n30j (FC)']
        col_widths = [22, 190, 48, 80, 38, 72, 38, 82, 82]

        tbl_rows = [
            [
                str(i + 1),
                str(r.get('designation', '')),
                str(r.get('stock_actuel', 0)) if 'stock_actuel' in r else '—',
                f"{float(r.get('valeur_stock') or 0):,.0f}",
                f"{float(r.get('pct_stock') or 0):.1f}%",
                f"{float(r.get('ca_30j') or 0):,.0f}",
                f"{float(r.get('pct_ca') or 0):.1f}%",
                f"{float(r.get('resultat_30j') or 0):+,.0f}",
                f"{float(r.get('moy_stock_30j') or 0):,.0f}",
            ]
            for i, r in enumerate(rows)
        ]
        flowables += self._data_table(
            headers, tbl_rows, col_widths,
            align_right_cols=[2, 3, 4, 5, 6, 7, 8],
            align_center_cols=[0],
        )

        flowables += [Spacer(1, 6), self._thin_separator(page_w)]
        flowables += self._totals_block([
            ('Valeur totale stock', total_valeur_stock),
            ('CA 30 jours',         ca_total_30j),
            ('Résultat 30 jours',   resultat_total_30j),
        ], taux=taux)

        if taux > 0:
            flowables.append(Spacer(1, 4))
            flowables.append(Paragraph(
                f'<font size=8 color=grey>Taux de référence : 1 USD = {taux:,.0f} FC</font>',
                style=_styles['Droite'],
            ))

        return self._build(flowables, orientation='landscape')

    # ── 4. Rapport des Caisses ────────────────────────────────────────────────

    def generate_rapport_caisse(
        self,
        solde_par_caisse: list,
        mouvements: list,
        total_entrees: float,
        total_sorties: float,
        solde_total: float,
        net_periode: float,
        debut: datetime.date,
        fin: datetime.date,
        taux: float = 0,
    ) -> HttpResponse:
        """
        solde_par_caisse = [{'nom', 'entrees', 'sorties', 'solde'}, ...]
        mouvements = [{'date', 'caisse', 'type', 'rubrique',
                       'montant', 'effectue_par'}, ...]
        """
        page_w = LETTER[0]
        subtitle = f'Période : du {debut.strftime("%d/%m/%Y")} au {fin.strftime("%d/%m/%Y")}'

        flowables = [self._header_flowable(page_w), Spacer(1, 6)]
        flowables += self._title_block(page_w, subtitle)

        # ── Synthèse par caisse ──────────────────────────────────────────────
        flowables.append(Paragraph('Synthèse par caisse', style=_styles['Titre_gauche']))
        flowables.append(Spacer(1, 4))

        synth_headers = ['Caisse', 'Entrées (FC)', 'Sorties (FC)', 'Solde (FC)']
        synth_col_widths = [200, 120, 120, 100]
        synth_rows = [
            [
                str(c.get('nom', '')),
                f"{float(c.get('entrees') or 0):,.0f}",
                f"{float(c.get('sorties') or 0):,.0f}",
                f"{float(c.get('solde') or 0):,.0f}",
            ]
            for c in solde_par_caisse
        ]
        flowables += self._data_table(
            synth_headers, synth_rows, synth_col_widths,
            align_right_cols=[1, 2, 3],
        )

        flowables += [Spacer(1, 6), self._thin_separator(page_w)]
        flowables += self._totals_block([
            ('Total entrées', total_entrees),
            ('Total sorties', total_sorties),
            ('Net période',   net_periode),
            ('Solde réel',    solde_total),
        ], taux=taux)

        if total_entrees > 0:
            flowables.append(Spacer(1, 8))
            flowables.append(Paragraph(
                self._montant_en_lettres(total_entrees),
                style=_styles['Total_lettre'],
            ))

        # ── Détail des mouvements ────────────────────────────────────────────
        if mouvements:
            flowables += [Spacer(1, 14), self._separator(page_w)]
            flowables.append(Spacer(1, 8))
            flowables.append(Paragraph('Détail des mouvements', style=_styles['Titre_gauche']))
            flowables.append(Spacer(1, 4))

            mvt_headers = ['Date', 'Caisse', 'Type', 'Rubrique', 'Montant (FC)', 'Effectué par']
            mvt_col_widths = [70, 100, 50, 140, 90, 90]
            mvt_rows = [
                [
                    str(m.get('date', '')),
                    str(m.get('caisse', '')),
                    str(m.get('type', '')),
                    str(m.get('rubrique', '')),
                    f"{float(m.get('montant') or 0):,.0f}",
                    str(m.get('effectue_par', '')),
                ]
                for m in mouvements
            ]
            flowables += self._data_table(
                mvt_headers, mvt_rows, mvt_col_widths,
                align_right_cols=[4],
                align_center_cols=[2],
            )

        if taux > 0:
            flowables.append(Spacer(1, 6))
            flowables.append(Paragraph(
                f'<font size=8 color=grey>Taux de référence : 1 USD = {taux:,.0f} FC</font>',
                style=_styles['Droite'],
            ))

        return self._build(flowables, orientation='portrait')

    # ── 5. Bon de commande ────────────────────────────────────────────────────

    def generate_bon_commande(self, data: list) -> HttpResponse:
        """
        data = [{'designation', 'fournisseur', 'unite', 'stock_actuel',
                 'qte_suggere', 'prix_achat', 'total_estime'}, ...]
        """
        page_w = LETTER[0]
        today = datetime.date.today()

        flowables = [self._header_flowable(page_w), Spacer(1, 10)]
        flowables.append(self._separator(page_w))
        flowables += self._title_block(page_w)

        if not data:
            flowables.append(Paragraph('Aucun article à commander.', style=_styles['Centre']))
        else:
            headers = ['#', 'Article', 'Fournisseur', 'Unité',
                       'Stock\nactuel', 'Qté à\ncommander',
                       'Prix achat\n(FC)', 'Total estimé\n(FC)']
            col_widths = [20, 155, 95, 50, 50, 55, 65, 70]

            rows = []
            total_global = 0.0
            for i, item in enumerate(data, 1):
                rows.append([
                    str(i),
                    str(item.get('designation', '')),
                    str(item.get('fournisseur', '—')),
                    str(item.get('unite', '—')),
                    str(item.get('stock_actuel', 0)),
                    str(item.get('qte_suggere', 0)),
                    f"{float(item.get('prix_achat') or 0):,.0f}",
                    f"{float(item.get('total_estime') or 0):,.0f}",
                ])
                total_global += float(item.get('total_estime') or 0)

            flowables += self._data_table(
                headers, rows, col_widths,
                align_right_cols=[4, 5, 6, 7],
                align_center_cols=[0],
            )

            flowables += [Spacer(1, 8), self._thin_separator(page_w)]
            flowables += self._totals_block([('Total estimé', total_global)])
            flowables.append(Spacer(1, 8))
            flowables.append(Paragraph(
                self._montant_en_lettres(total_global),
                style=_styles['Total_lettre'],
            ))

        flowables.append(Spacer(1, 30))
        flowables.append(Paragraph('Signature & Cachet', style=_styles['Droite']))

        return self._build(flowables, orientation='portrait')

    # ── 6. Facture ────────────────────────────────────────────────────────────

    def generate_facture(self, facture, details) -> HttpResponse:
        """
        facture : instance Facture
        details : queryset DetailsFacture (select_related('article') recommandé)
        Design B&W-friendly : pas de fond coloré massif, typographie forte.
        """
        ZEBRA    = colors.Color(0.95, 0.95, 0.95)
        LIGHT    = colors.Color(0.88, 0.88, 0.88)   # header tableau
        BORDER   = colors.Color(0.70, 0.70, 0.70)

        page_w = LETTER[0]
        inner_w = page_w - 30   # marges latérales doc (15+15)

        # ── Client ────────────────────────────────────────────────────────
        try:
            client_nom = str(facture.facture_client.client)
        except Exception:
            client_nom = facture.client_comptoir or '—'

        livreur_nom = str(facture.livreur) if facture.livreur else '—'
        statut_txt  = 'VALIDÉE' if facture.valide else 'BROUILLON'

        # ── Flowables ─────────────────────────────────────────────────────
        flowables = [self._header_flowable(page_w), Spacer(1, 6)]
        flowables.append(self._separator(page_w))
        flowables.append(Spacer(1, 10))

        # Bandeau BROUILLON
        if not facture.valide:
            draft_tbl = Table(
                [['⚠  DOCUMENT NON VALIDÉ — BROUILLON']],
                colWidths=[inner_w],
            )
            draft_tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, -1), LIGHT),
                ('FONTNAME',      (0, 0), (-1, -1), 'RobotoBd'),
                ('FONTSIZE',      (0, 0), (-1, -1), 8),
                ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING',    (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('BOX',           (0, 0), (-1, -1), 0.5, BORDER),
            ]))
            flowables += [draft_tbl, Spacer(1, 8)]

        # ── Titre facture ─────────────────────────────────────────────────
        titre_cell  = Paragraph(f'FACTURE N° {facture.numero}', style=_styles['Titre_gauche'])
        date_cell   = Paragraph(
            f'Date : <b>{facture.date_facture.strftime("%d/%m/%Y")}</b><br/>'
            f'Statut : {statut_txt}',
            style=_styles['Droite'],
        )
        titre_tbl = Table([[titre_cell, date_cell]], colWidths=[inner_w * 0.60, inner_w * 0.40])
        titre_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        flowables += [titre_tbl, Spacer(1, 8)]

        # ── Bloc info client / métadonnées ────────────────────────────────
        half = inner_w / 2
        client_para = Paragraph(
            f'<font size=7 color=grey>CLIENT</font><br/>'
            f'<b>{client_nom}</b><br/>'
            f'<font size=8>Livreur : {livreur_nom}</font>',
            style=_styles['Gauche'],
        )
        meta_para = Paragraph(
            f'<font size=7 color=grey>INFORMATIONS</font><br/>'
            f'<b>Devise : {facture.devise}</b>  ·  Taux : {facture.taux} FC/USD<br/>'
            f'<font size=8>Émis par : {facture.cree_par}</font>',
            style=_styles['Droite'],
        )
        info_tbl = Table([[client_para, meta_para]], colWidths=[half, half])
        info_tbl.setStyle(TableStyle([
            ('BOX',           (0, 0), (-1, -1), 0.5, BORDER),
            ('LINEBEFORE',    (1, 0), (1, -1),  0.5, BORDER),
            ('BACKGROUND',    (0, 0), (-1, -1), ZEBRA),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING',   (0, 0), (-1, -1), 10),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ]))
        flowables += [info_tbl, Spacer(1, 14)]

        # ── Tableau des lignes ────────────────────────────────────────────
        devise = facture.devise
        headers = ['#', 'Désignation', 'Qté', f'P.U. ({devise})', f'Total ({devise})']
        col_widths = [22, 265, 40, 78, 80]

        hdr_row = Table([headers], colWidths=col_widths)
        hdr_row.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), LIGHT),
            ('FONTNAME',      (0, 0), (-1, -1), 'RobotoBd'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('ALIGN',         (0, 0), (0, -1),  'CENTER'),
            ('ALIGN',         (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW',     (0, 0), (-1, -1), 0.8, BORDER),
        ]))
        flowables.append(hdr_row)

        rows = [
            [
                str(i + 1),
                str(d.article.designation if d.article else '—'),
                str(d.qte),
                f'{float(d.prix):,.2f}',
                f'{float(d.total):,.2f}',
            ]
            for i, d in enumerate(details)
        ]

        if rows:
            body_tbl = Table(rows, colWidths=col_widths)
            body_tbl.setStyle(TableStyle([
                ('FONTNAME',      (0, 0), (-1, -1), 'Roboto'),
                ('FONTSIZE',      (0, 0), (-1, -1), 8),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN',         (0, 0), (0, -1),  'CENTER'),
                ('ALIGN',         (2, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING',    (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID',          (0, 0), (-1, -1), 0.25, BORDER),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, ZEBRA]),
            ]))
            flowables.append(body_tbl)
        else:
            flowables.append(Paragraph(
                'Aucune ligne enregistrée.', style=_styles['Centre'],
            ))

        # ── Totaux ────────────────────────────────────────────────────────
        flowables.append(Spacer(1, 10))
        flowables.append(self._thin_separator(page_w))
        flowables.append(Spacer(1, 6))

        sous_total = float(facture.sous_total)
        remise     = float(facture.remise)
        total_fc   = float(facture.total)

        totals_data = [(f'Sous-total ({devise})', f'{sous_total:,.2f}')]
        if remise > 0:
            totals_data.append((f'Remise ({devise})', f'- {remise:,.2f}'))
        totals_data.append((f'TOTAL ({devise})', f'{total_fc:,.2f}'))

        # Contre-valeur si pertinente
        try:
            taux = float(facture.taux)
            if taux > 0 and devise == '$':
                totals_data.append(('Équivalent FC', f'{total_fc * taux:,.0f} FC'))
            elif taux > 0 and devise == 'FC':
                totals_data.append(('Équivalent USD', f'{total_fc / taux:,.2f} $'))
        except (ValueError, ZeroDivisionError):
            pass

        for i, (label, valeur) in enumerate(totals_data):
            is_last = (i == len(totals_data) - 1)
            font = 'RobotoBd' if is_last else 'Roboto'
            size = 11 if is_last else 9
            flowables.append(Paragraph(
                f'<font name="{font}" size="{size}">{label} : {valeur}</font>',
                style=_styles['Droite'],
            ))
            flowables.append(Spacer(1, 3))

        # Montant en lettres
        flowables += [Spacer(1, 6), self._thin_separator(page_w), Spacer(1, 6)]
        flowables.append(Paragraph(
            self._montant_en_lettres(total_fc),
            style=_styles['Total_lettre'],
        ))

        # ── Zone signature ────────────────────────────────────────────────
        flowables.append(Spacer(1, 28))
        sig_right = Paragraph('Signature & Sceau', style=_styles['Droite'])
        sig_tbl = Table([[sig_right]], colWidths=[inner_w])
        sig_tbl.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'RobotoIt'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LINEABOVE', (0, 0), (-1, -1), 0.5, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ]))
        flowables.append(sig_tbl)

        return self._build(flowables, orientation='portrait')

    # ── Relevé de Compte Tiers ────────────────────────────────────────────────

    def generate_releve_compte(
        self,
        tiers_info: dict,
        debit_label: str,
        credit_label: str,
        debit_headers: list,
        debit_rows: list,
        credit_rows: list,
        total_debit: float,
        total_credit: float,
    ) -> HttpResponse:
        """
        Génère un relevé de compte pour n'importe quel tiers.

        tiers_info : {nom, code, type, telephone, email, adresse, ville}
        debit_rows / credit_rows : listes de listes (valeurs en str).
        credit_rows a toujours 3 colonnes : [N°, Date, Montant].
        """
        ZEBRA  = colors.Color(0.95, 0.95, 0.95)
        LIGHT  = colors.Color(0.88, 0.88, 0.88)
        BORDER = colors.Color(0.70, 0.70, 0.70)
        RED    = colors.Color(0.83, 0.19, 0.19)
        GREEN  = colors.Color(0.10, 0.68, 0.46)

        page_w  = LETTER[0]
        inner_w = page_w - 30
        solde   = total_debit - total_credit

        flowables = [self._header_flowable(page_w), Spacer(1, 6)]
        flowables.append(self._separator(page_w))
        flowables.append(Spacer(1, 10))

        # ── Titre ─────────────────────────────────────────────────────────
        titre_cell = Paragraph(self.title, style=_styles['Titre_gauche'])
        date_cell  = Paragraph(
            f'Édité le : <b>{datetime.datetime.now().strftime("%d/%m/%Y")}</b>',
            style=_styles['Droite'],
        )
        titre_tbl = Table(
            [[titre_cell, date_cell]],
            colWidths=[inner_w * 0.65, inner_w * 0.35],
        )
        titre_tbl.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        flowables += [titre_tbl, Spacer(1, 8)]

        # ── Fiche identité tiers ───────────────────────────────────────────
        contact_parts = []
        if tiers_info.get('telephone'):
            contact_parts.append(f'Tél : {tiers_info["telephone"]}')
        if tiers_info.get('email'):
            contact_parts.append(f'Email : {tiers_info["email"]}')
        if tiers_info.get('adresse'):
            loc = tiers_info['adresse']
            if tiers_info.get('ville'):
                loc += f', {tiers_info["ville"]}'
            contact_parts.append(f'Adresse : {loc}')

        id_para = Paragraph(
            f'<font size=7 color=grey>TYPE</font><br/>'
            f'<b>{tiers_info.get("type", "")}</b><br/>'
            f'<font size=8>Code : #{tiers_info.get("code", "")}</font>',
            style=_styles['Gauche'],
        )
        contact_para = Paragraph(
            '<font size=7 color=grey>CONTACT</font><br/>'
            + '<br/>'.join(contact_parts) if contact_parts
            else '<font size=7 color=grey>CONTACT</font><br/>—',
            style=_styles['Droite'],
        )
        id_tbl = Table([[id_para, contact_para]], colWidths=[inner_w / 2, inner_w / 2])
        id_tbl.setStyle(TableStyle([
            ('BOX',           (0, 0), (-1, -1), 0.5, BORDER),
            ('LINEBEFORE',    (1, 0), (1, -1),  0.5, BORDER),
            ('BACKGROUND',    (0, 0), (-1, -1), ZEBRA),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING',   (0, 0), (-1, -1), 10),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME',      (0, 0), (-1, -1), 'Roboto'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ]))
        flowables += [id_tbl, Spacer(1, 14)]

        # ── KPI : Total débit / crédit / solde ────────────────────────────
        solde_color = RED if solde > 0 else GREEN
        kpi_data = [
            Paragraph(
                f'<font size=7 color=grey>{debit_label}</font>\n'
                f'<b><font size=11>{total_debit:,.0f} FC</font></b>',
                style=_styles['Centre'],
            ),
            Paragraph(
                f'<font size=7 color=grey>{credit_label}</font>\n'
                f'<b><font size=11>{total_credit:,.0f} FC</font></b>',
                style=_styles['Centre'],
            ),
            Paragraph(
                f'<font size=7 color=grey>SOLDE</font>\n'
                f'<b><font size=12>{solde:+,.0f} FC</font></b>',
                style=_styles['Centre'],
            ),
        ]
        col_w = inner_w / 3
        kpi_tbl = Table([kpi_data], colWidths=[col_w] * 3)
        kpi_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, -1), self.LIGHT_GREY),
            ('BACKGROUND', (2, 0), (2, -1), colors.Color(0.93, 0.93, 0.93)),
            ('BOX',        (0, 0), (-1, -1), 0.5, self.MID_GREY),
            ('INNERGRID',  (0, 0), (-1, -1), 0.5, self.MID_GREY),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR',  (2, 0), (2, -1), solde_color),
        ]))
        flowables += [kpi_tbl, Spacer(1, 16)]

        # ── Table mouvements débit ─────────────────────────────────────────
        flowables.append(Paragraph(debit_label, style=_styles['Titre_gauche']))
        flowables.append(Spacer(1, 4))

        n_cols_d  = len(debit_headers)
        first_w   = 22
        last_w    = 80
        mid_total = inner_w - first_w - last_w
        if n_cols_d > 2:
            mid_w  = mid_total / (n_cols_d - 2)
            dw = [first_w] + [mid_w] * (n_cols_d - 2) + [last_w]
        else:
            dw = [inner_w / n_cols_d] * n_cols_d

        right_cols_d = list(range(max(0, n_cols_d - 2), n_cols_d))
        flowables += self._data_table(
            debit_headers, debit_rows, dw,
            align_right_cols=right_cols_d,
            align_center_cols=[0],
        )

        # ── Sous-total débit ──────────────────────────────────────────────
        flowables.append(Spacer(1, 4))
        flowables.append(Paragraph(
            f'<b>Total {debit_label} : {total_debit:,.0f} FC</b>',
            style=_styles['Droite'],
        ))
        flowables.append(Spacer(1, 16))

        # ── Table paiements / crédit ───────────────────────────────────────
        flowables.append(self._thin_separator(page_w))
        flowables.append(Spacer(1, 10))
        flowables.append(Paragraph(credit_label, style=_styles['Titre_gauche']))
        flowables.append(Spacer(1, 4))

        credit_headers = ['N°', 'Date', 'Montant (FC)']
        cw = [22, inner_w - 22 - 100, 100]
        flowables += self._data_table(
            credit_headers, credit_rows, cw,
            align_right_cols=[2],
            align_center_cols=[0],
        )

        # ── Sous-total crédit ─────────────────────────────────────────────
        flowables.append(Spacer(1, 4))
        flowables.append(Paragraph(
            f'<b>Total {credit_label} : {total_credit:,.0f} FC</b>',
            style=_styles['Droite'],
        ))

        # ── Solde final ───────────────────────────────────────────────────
        flowables += [Spacer(1, 10), self._thin_separator(page_w), Spacer(1, 8)]
        sign_txt = 'SOLDE DÛ' if solde > 0 else 'SOLDE EN FAVEUR'
        flowables.append(Paragraph(
            f'<font name="RobotoBd" size="13">{sign_txt} : {solde:+,.0f} FC</font>',
            style=_styles['Total'],
        ))
        if abs(solde) > 0:
            flowables.append(Spacer(1, 6))
            flowables.append(Paragraph(
                self._montant_en_lettres(abs(solde)),
                style=_styles['Total_lettre'],
            ))

        # ── Zone signature ────────────────────────────────────────────────
        flowables.append(Spacer(1, 28))
        sig_tbl = Table(
            [['Lu et approuvé', '', 'Signature & Sceau']],
            colWidths=[inner_w * 0.35, inner_w * 0.30, inner_w * 0.35],
        )
        sig_tbl.setStyle(TableStyle([
            ('FONTNAME',   (0, 0), (-1, -1), 'RobotoIt'),
            ('FONTSIZE',   (0, 0), (-1, -1), 9),
            ('ALIGN',      (0, 0), (0, -1),  'LEFT'),
            ('ALIGN',      (2, 0), (2, -1),  'RIGHT'),
            ('LINEABOVE',  (0, 0), (0, -1),  0.5, BORDER),
            ('LINEABOVE',  (2, 0), (2, -1),  0.5, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        flowables.append(sig_tbl)

        return self._build(flowables, orientation='portrait')

    # ── Bon d'Approvisionnement ───────────────────────────────────────────────

    def generate_bon_appro(self, appro, details) -> HttpResponse:
        """
        appro   : instance Approvisionnement
        details : queryset DetailsApprovisionnement (select_related recommandé)
        """
        ZEBRA  = colors.Color(0.95, 0.95, 0.95)
        LIGHT  = colors.Color(0.88, 0.88, 0.88)
        BORDER = colors.Color(0.70, 0.70, 0.70)

        page_w  = landscape(LETTER)[0]
        inner_w = page_w - 30

        statut_txt = 'VALIDÉ' if appro.valide else 'BROUILLON'
        devise     = appro.devise

        # ── Flowables ─────────────────────────────────────────────────────
        flowables = [self._header_flowable(page_w), Spacer(1, 6)]
        flowables.append(self._separator(page_w))
        flowables.append(Spacer(1, 10))

        # Bandeau BROUILLON
        if not appro.valide:
            draft_tbl = Table(
                [['⚠  DOCUMENT NON VALIDÉ — BROUILLON']],
                colWidths=[inner_w],
            )
            draft_tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, -1), LIGHT),
                ('FONTNAME',      (0, 0), (-1, -1), 'RobotoBd'),
                ('FONTSIZE',      (0, 0), (-1, -1), 8),
                ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING',    (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('BOX',           (0, 0), (-1, -1), 0.5, BORDER),
            ]))
            flowables += [draft_tbl, Spacer(1, 8)]

        # ── Titre ─────────────────────────────────────────────────────────
        titre_cell = Paragraph(
            f'BON D\'APPROVISIONNEMENT N° {appro.numero}',
            style=_styles['Titre_gauche'],
        )
        date_cell = Paragraph(
            f'Date : <b>{appro.date_creation.strftime("%d/%m/%Y")}</b><br/>'
            f'Statut : {statut_txt}',
            style=_styles['Droite'],
        )
        titre_tbl = Table(
            [[titre_cell, date_cell]],
            colWidths=[inner_w * 0.60, inner_w * 0.40],
        )
        titre_tbl.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        flowables += [titre_tbl, Spacer(1, 8)]

        # ── Bloc méta : magasin / devise / émetteur ────────────────────────
        half = inner_w / 2
        magasin_para = Paragraph(
            f'<font size=7 color=grey>MAGASIN</font><br/>'
            f'<b>{appro.magasin}</b>',
            style=_styles['Gauche'],
        )
        meta_para = Paragraph(
            f'<font size=7 color=grey>INFORMATIONS</font><br/>'
            f'<b>Devise : {devise}</b>  ·  Taux : {appro.taux} FC/USD<br/>'
            f'<font size=8>Créé par : {appro.cree_par}</font>',
            style=_styles['Droite'],
        )
        info_tbl = Table([[magasin_para, meta_para]], colWidths=[half, half])
        info_tbl.setStyle(TableStyle([
            ('BOX',           (0, 0), (-1, -1), 0.5, BORDER),
            ('LINEBEFORE',    (1, 0), (1, -1),  0.5, BORDER),
            ('BACKGROUND',    (0, 0), (-1, -1), ZEBRA),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING',   (0, 0), (-1, -1), 10),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ]))
        flowables += [info_tbl, Spacer(1, 14)]

        # ── Tableau des lignes ────────────────────────────────────────────
        headers = [
            '#', 'Article', 'Fournisseur', 'N° Facture',
            'Qté', f'P.A.N. ({devise})', f'Frais ({devise})',
            f'P.V.D. ({devise})', 'Péremption',
        ]
        col_widths = [22, 185, 100, 70, 32, 70, 70, 70, 65]

        hdr_row = Table([headers], colWidths=col_widths)
        hdr_row.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), LIGHT),
            ('FONTNAME',      (0, 0), (-1, -1), 'RobotoBd'),
            ('FONTSIZE',      (0, 0), (-1, -1), 7),
            ('ALIGN',         (0, 0), (0, -1),  'CENTER'),
            ('ALIGN',         (4, 0), (-1, -1), 'RIGHT'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW',     (0, 0), (-1, -1), 0.8, BORDER),
        ]))
        flowables.append(hdr_row)

        det_list = list(details)
        rows = []
        for i, d in enumerate(det_list):
            peremption = d.date_peremption.strftime('%d/%m/%Y') if d.date_peremption else '—'
            rows.append([
                str(i + 1),
                str(d.article.designation if d.article else '—'),
                str(d.fournisseur),
                str(d.facture or '—'),
                str(d.qte),
                f'{float(d.prix):,.2f}',
                f'{float(d.frais_achat):,.2f}',
                f'{float(d.prix_vente):,.2f}',
                peremption,
            ])

        if rows:
            body_tbl = Table(rows, colWidths=col_widths)
            body_tbl.setStyle(TableStyle([
                ('FONTNAME',      (0, 0), (-1, -1), 'Roboto'),
                ('FONTSIZE',      (0, 0), (-1, -1), 7),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN',         (0, 0), (0, -1),  'CENTER'),
                ('ALIGN',         (4, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING',    (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID',          (0, 0), (-1, -1), 0.25, BORDER),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, ZEBRA]),
            ]))
            flowables.append(body_tbl)
        else:
            flowables.append(Paragraph(
                'Aucune ligne enregistrée.', style=_styles['Centre'],
            ))

        # ── Totaux ────────────────────────────────────────────────────────
        flowables += [Spacer(1, 10), self._thin_separator(page_w), Spacer(1, 6)]

        total_pan   = float(appro.total_approvisionnement)
        total_frais = float(appro.frais_achat_total)
        ca_potentiel = float(appro.chiffre_affaires)
        resultat    = float(appro.resultat_total)

        totals_data = [
            (f'Total P.A.N. ({devise})',        f'{total_pan:,.2f}'),
            (f'Total Frais ({devise})',          f'{total_frais:,.2f}'),
            (f'CA potentiel ({devise})',          f'{ca_potentiel:,.2f}'),
            (f'RÉSULTAT ESTIMÉ ({devise})',       f'{resultat:+,.2f}'),
        ]
        for i, (label, valeur) in enumerate(totals_data):
            is_last = (i == len(totals_data) - 1)
            font = 'RobotoBd' if is_last else 'Roboto'
            size = 11 if is_last else 9
            flowables.append(Paragraph(
                f'<font name="{font}" size="{size}">{label} : {valeur}</font>',
                style=_styles['Droite'],
            ))
            flowables.append(Spacer(1, 3))

        # ── Zone signature ────────────────────────────────────────────────
        flowables.append(Spacer(1, 24))
        sig_tbl = Table(
            [['Responsable approvisionnements', '', 'Direction']],
            colWidths=[inner_w * 0.35, inner_w * 0.30, inner_w * 0.35],
        )
        sig_tbl.setStyle(TableStyle([
            ('FONTNAME',    (0, 0), (-1, -1), 'RobotoIt'),
            ('FONTSIZE',    (0, 0), (-1, -1), 9),
            ('ALIGN',       (0, 0), (0, -1),  'LEFT'),
            ('ALIGN',       (2, 0), (2, -1),  'RIGHT'),
            ('LINEABOVE',   (0, 0), (0, -1),  0.5, BORDER),
            ('LINEABOVE',   (2, 0), (2, -1),  0.5, BORDER),
            ('TOPPADDING',  (0, 0), (-1, -1), 5),
        ]))
        flowables.append(sig_tbl)

        return self._build(flowables, orientation='landscape')

    # ── Bon de Commande / Demande de Proforma ─────────────────────────────────

    def generate_bon_commande_fournisseur(self, commande, details, avec_prix: bool = True) -> HttpResponse:
        """
        commande   : instance Commande (select_related fournisseur, devise)
        details    : queryset DetailsCommande (select_related article)
        avec_prix  : True → Bon de commande (avec prix), False → Demande de proforma
        """
        ZEBRA  = colors.Color(0.95, 0.95, 0.95)
        LIGHT  = colors.Color(0.88, 0.88, 0.88)
        BORDER = colors.Color(0.70, 0.70, 0.70)
        TEAL   = self.TEAL
        WHITE  = colors.white

        page_w  = LETTER[0]
        inner_w = page_w - 50

        devise_str = commande.devise.symbole if commande.devise else ''
        titre_doc  = 'BON DE COMMANDE' if avec_prix else 'DEMANDE DE PROFORMA'

        flowables = [self._header_flowable(page_w), Spacer(1, 6)]
        flowables.append(self._separator(page_w))
        flowables.append(Spacer(1, 10))

        # ── Titre + date ──────────────────────────────────────────────────
        titre_cell = Paragraph(
            f'{titre_doc} N° {commande.numero}',
            style=_styles['Titre_gauche'],
        )
        date_cell = Paragraph(
            f'Date : <b>{commande.date_commande.strftime("%d/%m/%Y")}</b>',
            style=_styles['Droite'],
        )
        titre_tbl = Table(
            [[titre_cell, date_cell]],
            colWidths=[inner_w * 0.60, inner_w * 0.40],
        )
        titre_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        flowables += [titre_tbl, Spacer(1, 8)]

        # ── Bloc méta : fournisseur / devise / taux ───────────────────────
        half = inner_w / 2
        fourn_para = Paragraph(
            f'<font size=7 color=grey>FOURNISSEUR</font><br/>'
            f'<b>{commande.fournisseur}</b>',
            style=_styles['Gauche'],
        )
        devise_info = ''
        if commande.devise:
            devise_info = f'<b>Devise : {commande.devise.code}</b>  ·  Taux : {commande.taux}'
        meta_para = Paragraph(
            f'<font size=7 color=grey>INFORMATIONS</font><br/>'
            f'{devise_info}<br/>'
            f'<font size=8>Créé par : {commande.cree_par}</font>',
            style=_styles['Droite'],
        )
        info_tbl = Table([[fourn_para, meta_para]], colWidths=[half, half])
        info_tbl.setStyle(TableStyle([
            ('BOX',           (0, 0), (-1, -1), 0.5, BORDER),
            ('LINEBEFORE',    (1, 0), (1, -1),  0.5, BORDER),
            ('BACKGROUND',    (0, 0), (-1, -1), ZEBRA),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING',   (0, 0), (-1, -1), 10),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        flowables += [info_tbl, Spacer(1, 12)]

        # ── Tableau articles ───────────────────────────────────────────────
        if avec_prix:
            headers = ['N°', 'Code', 'Désignation', 'Qté', 'Unité', 'Prix unit.', 'Total']
            col_widths = [
                inner_w * 0.05, inner_w * 0.12, inner_w * 0.35,
                inner_w * 0.08, inner_w * 0.10, inner_w * 0.15, inner_w * 0.15,
            ]
        else:
            headers = ['N°', 'Code', 'Désignation', 'Qté', 'Unité']
            col_widths = [
                inner_w * 0.07, inner_w * 0.15, inner_w * 0.50,
                inner_w * 0.13, inner_w * 0.15,
            ]

        head_row = [Paragraph(f'<b>{h}</b>', _styles['Gauche']) for h in headers]
        rows = [head_row]

        detail_list = list(details)
        total = 0
        for idx, d in enumerate(detail_list):
            if avec_prix:
                row = [
                    str(idx + 1),
                    d.article.code,
                    d.article.designation,
                    str(d.qte),
                    d.article.unite if hasattr(d.article, 'unite') else '',
                    f'{d.prix:,.2f} {devise_str}',
                    f'{d.prix_total:,.2f} {devise_str}',
                ]
                total += float(d.prix_total)
            else:
                row = [
                    str(idx + 1),
                    d.article.code,
                    d.article.designation,
                    str(d.qte),
                    d.article.unite if hasattr(d.article, 'unite') else '',
                ]
            rows.append(row)

        if not detail_list:
            colspan = len(headers)
            rows.append(['Aucun article enregistré.'] + ['' for _ in range(colspan - 1)])

        art_tbl = Table(rows, colWidths=col_widths, repeatRows=1)
        n = len(rows)
        tbl_style = [
            ('BACKGROUND',    (0, 0), (-1, 0),  TEAL),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  WHITE),
            ('FONTNAME',      (0, 0), (-1, 0),  'RobotoBd'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING',   (0, 0), (-1, -1), 6),
            ('GRID',          (0, 0), (-1, -1), 0.3, BORDER),
            ('ALIGN',         (3, 0), (3, -1),  'RIGHT'),  # Qté
        ]
        if avec_prix:
            tbl_style += [
                ('ALIGN',  (5, 0), (6, -1), 'RIGHT'),  # Prix, Total
            ]
        for i in range(1, n):
            if i % 2 == 0:
                tbl_style.append(('BACKGROUND', (0, i), (-1, i), ZEBRA))
        art_tbl.setStyle(TableStyle(tbl_style))
        flowables += [art_tbl, Spacer(1, 10)]

        # ── Total (uniquement pour bon de commande) ────────────────────────
        if avec_prix and detail_list:
            total_para = Paragraph(
                f'<b>TOTAL : {total:,.2f} {devise_str}</b>',
                style=_styles['Droite'],
            )
            flowables.append(total_para)
            flowables.append(Spacer(1, 12))

        # ── Zone signature ─────────────────────────────────────────────────
        third = inner_w / 3
        sig_data = [[
            Paragraph('<font size=8 color=grey>Le Gestionnaire</font><br/><br/><br/>_______________', _styles['Centre']),
            Paragraph('<font size=8 color=grey>Le Responsable des achats</font><br/><br/><br/>_______________', _styles['Centre']),
            Paragraph('<font size=8 color=grey>Le Directeur Général</font><br/><br/><br/>_______________', _styles['Centre']),
        ]]
        sig_tbl = Table(sig_data, colWidths=[third, third, third])
        sig_tbl.setStyle(TableStyle([
            ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOX',        (0, 0), (0, -1),  0.4, BORDER),
            ('BOX',        (1, 0), (1, -1),  0.4, BORDER),
            ('BOX',        (2, 0), (2, -1),  0.4, BORDER),
        ]))
        flowables.append(sig_tbl)

        return self._build(flowables, orientation='portrait')

    # ── Excel ─────────────────────────────────────────────────────────────────

    # ── Bulletin de Paie ──────────────────────────────────────────────────────

    def generate_bulletin_paie(self, paie, lignes) -> HttpResponse:
        """
        paie   : instance Paie (select_related agent recommandé)
        lignes : queryset ou liste LignePaie, pré-chargé
        """
        ZEBRA       = colors.Color(0.95, 0.95, 0.95)
        LIGHT       = colors.Color(0.88, 0.88, 0.88)
        BORDER      = colors.Color(0.70, 0.70, 0.70)
        GREEN_PALE  = colors.Color(0.92, 0.99, 0.96)
        RED_PALE    = colors.Color(1.00, 0.95, 0.95)
        GREEN_HDR   = colors.Color(0.15, 0.73, 0.60)
        RED_HDR     = colors.Color(0.91, 0.30, 0.24)

        page_w  = LETTER[0]
        inner_w = page_w - 30

        agent      = paie.agent
        statut_txt = 'VALIDÉ' if paie.valide else 'BROUILLON'

        # ── Flowables ─────────────────────────────────────────────────────
        flowables = [self._header_flowable(page_w), Spacer(1, 6)]
        flowables.append(self._separator(page_w))
        flowables.append(Spacer(1, 10))

        # Bandeau BROUILLON
        if not paie.valide:
            draft_tbl = Table(
                [['⚠  DOCUMENT NON VALIDÉ — BROUILLON']],
                colWidths=[inner_w],
            )
            draft_tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, -1), LIGHT),
                ('FONTNAME',      (0, 0), (-1, -1), 'RobotoBd'),
                ('FONTSIZE',      (0, 0), (-1, -1), 8),
                ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING',    (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('BOX',           (0, 0), (-1, -1), 0.5, BORDER),
            ]))
            flowables += [draft_tbl, Spacer(1, 8)]

        # ── Titre ─────────────────────────────────────────────────────────
        titre_cell = Paragraph(
            f'BULLETIN DE PAIE — {django_date_filter(paie.mois, "F Y").upper()}',
            style=_styles['Titre_gauche'],
        )
        date_cell = Paragraph(
            f'Date d\'émission : <b>{datetime.datetime.now().strftime("%d/%m/%Y")}</b><br/>'
            f'Statut : {statut_txt}',
            style=_styles['Droite'],
        )
        titre_tbl = Table(
            [[titre_cell, date_cell]],
            colWidths=[inner_w * 0.60, inner_w * 0.40],
        )
        titre_tbl.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        flowables += [titre_tbl, Spacer(1, 8)]

        # ── Bloc agent ────────────────────────────────────────────────────
        half = inner_w / 2
        agent_para = Paragraph(
            f'<font size=7 color=grey>AGENT</font><br/>'
            f'<b>{agent.nom}</b><br/>'
            f'<font size=8>Matricule : {agent.matricule}</font>',
            style=_styles['Gauche'],
        )
        contrat_lines = (
            f'<font size=7 color=grey>CONTRAT</font><br/>'
            f'<b>{agent.get_type_contrat_display()}</b><br/>'
        )
        if agent.poste:
            contrat_lines += f'<font size=8>Poste : {agent.poste}</font><br/>'
        if agent.departement:
            contrat_lines += f'<font size=8>Département : {agent.departement}</font><br/>'
        if agent.date_engagement:
            contrat_lines += (
                f'<font size=8>Engagé le : {agent.date_engagement.strftime("%d/%m/%Y")}</font>'
            )
        contrat_para = Paragraph(contrat_lines, style=_styles['Droite'])
        info_tbl = Table([[agent_para, contrat_para]], colWidths=[half, half])
        info_tbl.setStyle(TableStyle([
            ('BOX',           (0, 0), (-1, -1), 0.5, BORDER),
            ('LINEBEFORE',    (1, 0), (1, -1),  0.5, BORDER),
            ('BACKGROUND',    (0, 0), (-1, -1), ZEBRA),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING',   (0, 0), (-1, -1), 10),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ]))
        flowables += [info_tbl, Spacer(1, 14)]

        # ── Tableau GAINS / RETENUES côte à côte ─────────────────────────
        lignes_list  = list(lignes)
        gains    = [l for l in lignes_list if l.type_ligne == 'GAIN']
        retenues = [l for l in lignes_list if l.type_ligne == 'RETENUE']

        col_w = (inner_w - 8) / 2   # 4 pt de gutter entre les deux moitiés

        def _side_table(rows_data, hdr_label, hdr_color, bg_color):
            hdr = Table(
                [[Paragraph(f'<b>{hdr_label}</b>', style=_styles['Gauche'])]],
                colWidths=[col_w],
            )
            hdr.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, -1), hdr_color),
                ('FONTNAME',      (0, 0), (-1, -1), 'RobotoBd'),
                ('FONTSIZE',      (0, 0), (-1, -1), 8),
                ('TOPPADDING',    (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING',   (0, 0), (-1, -1), 8),
                ('TEXTCOLOR',     (0, 0), (-1, -1), colors.white),
            ]))
            if not rows_data:
                body = Table(
                    [['—', '—']],
                    colWidths=[col_w * 0.65, col_w * 0.35],
                )
                body.setStyle(TableStyle([
                    ('FONTNAME',   (0, 0), (-1, -1), 'RobotoIt'),
                    ('FONTSIZE',   (0, 0), (-1, -1), 8),
                    ('TEXTCOLOR',  (0, 0), (-1, -1), BORDER),
                    ('TOPPADDING',    (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING',   (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                ]))
            else:
                body = Table(
                    rows_data,
                    colWidths=[col_w * 0.65, col_w * 0.35],
                )
                body.setStyle(TableStyle([
                    ('FONTNAME',      (0, 0), (-1, -1), 'Roboto'),
                    ('FONTSIZE',      (0, 0), (-1, -1), 8),
                    ('ALIGN',         (1, 0), (1, -1),  'RIGHT'),
                    ('TOPPADDING',    (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING',   (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
                    ('BACKGROUND',    (0, 0), (-1, -1), bg_color),
                    ('LINEBELOW',     (0, 0), (-1, -2), 0.3, BORDER),
                    ('FONTNAME',      (0, 0), (1, 0),   'RobotoBd'),  # 1re ligne en gras
                ]))
            return [hdr, body]

        gains_rows = [
            [l.libelle, f'{float(l.montant):,.0f} FC']
            for l in gains
        ]
        retenues_rows = [
            [l.libelle, f'− {float(l.montant):,.0f} FC']
            for l in retenues
        ]

        gains_flowables   = _side_table(gains_rows,    'GAINS',    GREEN_HDR, GREEN_PALE)
        retenues_flowables = _side_table(retenues_rows, 'RETENUES', RED_HDR,   RED_PALE)

        # Assemblage en 2 colonnes avec une Table enveloppante
        max_rows = max(len(gains_flowables), len(retenues_flowables))
        side_tbl = Table(
            [[gains_flowables[0],    retenues_flowables[0]],
             [gains_flowables[1],    retenues_flowables[1]]],
            colWidths=[col_w, col_w],
            spaceBefore=0,
            spaceAfter=0,
        )
        side_tbl.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('COLPADDING',    (0, 0), (-1, -1), 4),
        ]))
        flowables += [side_tbl, Spacer(1, 14)]

        # ── Récapitulatif ─────────────────────────────────────────────────
        flowables.append(self._thin_separator(page_w))
        flowables.append(Spacer(1, 8))

        recap_rows = [
            ('Salaire brut',    f'{float(paie.salaire_brut):,.0f} FC'),
            ('Total retenues',  f'− {float(paie.total_retenues):,.0f} FC'),
        ]
        for label, valeur in recap_rows:
            flowables.append(Paragraph(
                f'<font name="Roboto" size="9">{label} : {valeur}</font>',
                style=_styles['Droite'],
            ))
            flowables.append(Spacer(1, 3))

        flowables.append(Spacer(1, 4))
        flowables.append(self._thin_separator(page_w))
        flowables.append(Spacer(1, 6))
        flowables.append(Paragraph(
            f'<font name="RobotoBd" size="12">NET À PAYER : '
            f'{float(paie.net_a_payer):,.0f} FC</font>',
            style=_styles['Total'],
        ))

        # ── Période de paie ───────────────────────────────────────────────
        flowables.append(Spacer(1, 8))
        jours_txt = f'{paie.jp} jour{"s" if paie.jp > 1 else ""} prestés sur {paie.jap}'
        if paie.absence:
            jours_txt += f' ({paie.absence} jour{"s" if paie.absence > 1 else ""} d\'absence)'
        flowables.append(Paragraph(
            f'<font name="RobotoIt" size="8" color="grey">{jours_txt}</font>',
            style=_styles['Droite'],
        ))

        # ── Zone signature ────────────────────────────────────────────────
        flowables.append(Spacer(1, 32))
        sig_tbl = Table(
            [['Responsable paie', '', "Signature de l'agent"]],
            colWidths=[inner_w * 0.35, inner_w * 0.30, inner_w * 0.35],
        )
        sig_tbl.setStyle(TableStyle([
            ('FONTNAME',    (0, 0), (-1, -1), 'RobotoIt'),
            ('FONTSIZE',    (0, 0), (-1, -1), 9),
            ('ALIGN',       (0, 0), (0, -1),  'LEFT'),
            ('ALIGN',       (2, 0), (2, -1),  'RIGHT'),
            ('LINEABOVE',   (0, 0), (0, -1),  0.5, BORDER),
            ('LINEABOVE',   (2, 0), (2, -1),  0.5, BORDER),
            ('TOPPADDING',  (0, 0), (-1, -1), 5),
        ]))
        flowables.append(sig_tbl)

        return self._build(flowables, orientation='portrait')

    def generate_excel(self, data: list, header: list = None) -> HttpResponse:
        """Export Excel générique."""
        wb = Workbook()
        ws = wb.active
        ws.title = self.title
        _header = header or (list(data[0].keys()) if data else [])

        # En-tête en gras
        for col_idx, col_name in enumerate(_header, 1):
            cell = ws.cell(column=col_idx, row=1, value=col_name)
            cell.font = Font(bold=True)

        # Données
        for row_idx, item in enumerate(data, 2):
            for col_idx, key in enumerate(_header, 1):
                ws.cell(column=col_idx, row=row_idx,
                        value=item.get(key) if isinstance(item, dict) else item)

        with NamedTemporaryFile() as tmp:
            wb.save(tmp.name)
            tmp.seek(0)
            content = tmp.read()

        filename = f'export_{self.filename}'
        mimetype, encoding = mimetypes.guess_type(filename)
        if not mimetype:
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return HttpResponse(
            content,
            content_type=mimetype,
            headers={'Content-Disposition': f'attachment;filename={filename}'},
        )
