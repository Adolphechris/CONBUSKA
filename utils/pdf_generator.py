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
from functools import cached_property
from io import BytesIO
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.http import HttpResponse

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

    def _totals_block(self, lines: list, taux: float = None) -> list:
        """
        lines = [(label, valeur_fc), ...]
        Si taux fourni, affiche la contre-valeur USD entre parenthèses.
        Dernier élément = total principal (police plus grande).
        """
        flowables = [Spacer(1, 10)]
        for i, (label, valeur_fc) in enumerate(lines):
            is_last = (i == len(lines) - 1)
            cv = ''
            if taux and taux > 0:
                cv_usd = valeur_fc / taux
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
                return f'Arrêté à la somme de {fc_txt} francs congolais et {cents_txt} centimes'
            return f'Arrêté à la somme de {fc_txt} francs congolais'
        except Exception:
            return ''

    # ── Bloc KPI synthèse (section colorée) ───────────────────────────────────

    def _kpi_table(self, kpis: list, taux: float = None) -> Table:
        """
        kpis = [(label, valeur_fc), ...]
        Retourne une Table une ligne, cellules colorées alternées.
        """
        cells = []
        for label, val in kpis:
            cv = ''
            if taux and taux > 0:
                cv = f'\n≈ {val / taux:,.2f} USD'
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
        total_global = total_ventes + total_appros
        subtitle = f'Période : du {debut.strftime("%d/%m/%Y")} au {fin.strftime("%d/%m/%Y")}'

        flowables = [self._header_flowable(page_w), Spacer(1, 6)]
        flowables += self._title_block(page_w, subtitle)

        # KPI synthèse
        flowables.append(self._kpi_table([
            ('Résultat ventes',   total_ventes),
            ('Résultat appros',   total_appros),
            ('Résultat net total', total_global),
        ], taux=taux))
        flowables.append(Spacer(1, 12))

        # Tableau par article
        flowables.append(Paragraph('Détail par article', style=_styles['Titre_gauche']))
        flowables.append(Spacer(1, 4))

        headers = ['Article', 'Résultat (FC)', '% du total']
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
        flowables += self._totals_block([('Résultat net total', total_global)], taux=taux)

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
        solde_net = total_entrees - total_sorties
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
            ('Solde net',     solde_net),
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

    # ── Excel ─────────────────────────────────────────────────────────────────

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
