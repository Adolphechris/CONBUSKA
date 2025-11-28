import mimetypes
from django.conf import settings
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, LETTER, landscape, A5
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, Flowable, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import reportlab.rl_config
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from tempfile import NamedTemporaryFile
from io import BytesIO
import os
import math
from num2words import num2words
import datetime
from parametres.models import Parametre


font_dir = settings.STATIC_ROOT
font_path = os.path.join(font_dir, 'fonts/roboto/')

reportlab.rl_config.warnOnMissingFontGlyphs = 0
pdfmetrics.registerFont(TTFont('Roboto', os.path.join(font_dir, font_path) + 'Roboto-Regular.ttf'))
pdfmetrics.registerFont(TTFont('RobotoBd', os.path.join(font_dir, font_path) + 'Roboto-Bold.ttf'))
pdfmetrics.registerFont(TTFont('RobotoBdIt', os.path.join(font_dir, font_path) + 'Roboto-BoldItalic.ttf'))
pdfmetrics.registerFont(TTFont('RobotoBl', os.path.join(font_dir, font_path) + 'Roboto-Black.ttf'))
pdfmetrics.registerFont(TTFont('RobotoBlIt', os.path.join(font_dir, font_path) + 'Roboto-BlackItalic.ttf'))
pdfmetrics.registerFont(TTFont('RobotoIt', os.path.join(font_dir, font_path) + 'Roboto-Italic.ttf'))
pdfmetrics.registerFont(TTFont('RobotoLg', os.path.join(font_dir, font_path) + 'Roboto-Light.ttf'))
pdfmetrics.registerFont(TTFont('RobotoLgIt', os.path.join(font_dir, font_path) + 'Roboto-LightItalic.ttf'))
pdfmetrics.registerFont(TTFont('RobotoTh', os.path.join(font_dir, font_path) + 'Roboto-Thin.ttf'))
pdfmetrics.registerFont(TTFont('RobotoThIt', os.path.join(font_dir, font_path) + 'Roboto-ThinItalic.ttf'))
pdfmetrics.registerFont(TTFont('RobotoMd', os.path.join(font_dir, font_path) + 'Roboto-Medium.ttf'))
pdfmetrics.registerFont(TTFont('RobotoMdIt', os.path.join(font_dir, font_path) + 'Roboto-MediumItalic.ttf'))
pdfmetrics.registerFontFamily('Roboto', normal='Roboto', bold='RobotoBd', italic='RobotoIt', boldItalic='RobotoBdIt')

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Droite', alignment=TA_RIGHT, fontName='Roboto', fontSize=12))
styles.add(ParagraphStyle(name='Gauche', alignment=TA_LEFT, fontName='Roboto', fontSize=12))
styles.add(ParagraphStyle(name='Centre', alignment=TA_CENTER, fontName='Roboto', fontSize=14))
styles.add(ParagraphStyle(name='Centre_footer', alignment=TA_CENTER, fontName='Roboto', fontSize=8))
styles.add(ParagraphStyle(name='Titre', alignment=TA_CENTER, fontName='RobotoBd', fontSize=14))
styles.add(ParagraphStyle(name='Titre_gauche', alignment=TA_LEFT, fontName='RobotoBd', fontSize=12))
styles.add(ParagraphStyle(name='Elements', fontSize=7, leading=8))


class FooterCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
        self.mode = kwargs['pagesize']

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_canvas(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_canvas(self, page_count):
        get_parametres = Parametre.objects.get(code='Params')
        page = "Page %s sur %s" % (self._pageNumber, page_count)
        x = 128
        pr = Paragraph(f'{get_parametres.telephone}<br />{get_parametres.email}<br />{get_parametres.adresse}<br />'
                       f'{get_parametres.ville} - {get_parametres.pays}', style=styles['Droite'])

        pl = Paragraph(f'RCCM: {get_parametres.rccm}<br />Id.Nat.: {get_parametres.idnat}<br />'
                       f'Numéro impôt:{get_parametres.impot}<br /> TVA: {get_parametres.tva}')

        width = self.mode[0]
        print('THE WIDTH', width)
        self.saveState()
        self.setStrokeColorRGB(0, 0, 0)
        self.setLineWidth(0.5)
        self.line(25, 60, width - 25, 60)
        self.setFont('Roboto', 10)

        if width > 700:
            pl.wrapOn(self, width-410, 10)
            pl.drawOn(self, 25, 10)

            pr.wrapOn(self, width-410, 10)
            pr.drawOn(self, width-410, 10)

        else:
            pl.wrapOn(self, width - 318, 10)
            pl.drawOn(self, 25, 10)

            pr.wrapOn(self, width - 318, 10)
            pr.drawOn(self, width - 318, 10)
        self.restoreState()


class LineFlowable(Flowable):
    """Une custom line pour reportlab ligne horizontale servant de separateur"""
    def __init__(self, debut, width, height=0):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.debut = debut

    def __repr__(self):
        return "Line(w=%s)" % self.width

    def draw(self):
        self.canv.line(self.debut, self.height, self.width, self.height)


class DocumentGenerator:
    def __init__(self, filename, title, header=None):
        self.filename = filename
        self.title = title
        self.header = header if header is not None else []
        self.custom_color = colors.Color(red=(54.0/255), green=(139.0/255), blue=(193.0/255))

    def generate_rapport(self, data):
        title_bloc = [Paragraph('{}'.format(self.title), style=styles['Titre_gauche']), Spacer(1, 6)]

        get_params = Parametre.objects.get(code='Params')
        info_societe = [Paragraph('<b>{}</b><br />'.format(get_params.societe), style=styles['Gauche']), Spacer(1, 6)]

        info_date = [Paragraph('Lubumbashi, le : {}<br />'.format(datetime.datetime.now().strftime('%d/%m/%Y')),
                               style=styles['Gauche']), Spacer(1, 6)]

        # LOGO
        get_params = Parametre.objects.get(code='Params')
        print(get_params.logo)
        logo_dir = settings.MEDIA_ROOT
        logo = get_params.logo.path
        im = Image(os.path.join(logo_dir, logo), 1.8 * inch, 1.8 * inch)

        header_bloc = [[info_societe], [im, info_date]]

        return self.generate_rapport_pdf(title_bloc, header_bloc, data)

    def generate_rapport_pdf(self, title_bloc, header_bloc, data):
        filename = self.filename
        buffer = BytesIO()

        page_size = LETTER
        doc = SimpleDocTemplate(buffer, pagesize=page_size, rightMargin=15, leftMargin=15,
                                topMargin=10, bottomMargin=60)
        flowables = []

        tablestyle = TableStyle([('FONT', (0, 0), (-1, -1), 'RobotoBd', 10),
                                 ('VALIGN', (1, 1), (1, 1), 'MIDDLE')])
        table_header = Table(header_bloc, colWidths=[400, 180])
        table_header.setStyle(tablestyle)

        flowables.append(table_header)
        flowables.append(Spacer(1, 6))

        # TITLE
        try:
            flowables += title_bloc
        except TypeError:
            flowables.append(title_bloc)

        line = LineFlowable(1, LETTER[1] - 220)
        flowables.append(line)
        flowables.append(Spacer(1, 12))

        # DATA
        total_general = sum(i.get('total') for i in data)
        data_header = [['Numero', 'Date', 'Devise', 'Taux', 'Remise', 'Client', 'Livreur', 'Total', 'Cree par']]
        tbl_header = Table(data_header, colWidths=[50, 100, 60, 60, 60, 50, 50, 100, 50],
                           style=[('GRID', (0, 0), (-1, -1), 1, colors.grey),
                                  ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                  ('FONTSIZE', (0, 0), (-1, -1), 9),
                                  ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)])
        flowables.append(tbl_header)

        data_items = [[i.get('numero'), i.get('date_facture'), i.get('devise'), i.get('taux'), i.get('remise'),
                       i.get('client'), i.get('livreur'), i.get('total'), i.get('cree_par')] for i in data]
        tbl_items = Table(data_items, colWidths=[50, 100, 60, 60, 60, 50, 50, 100, 50],
                          style=[('GRID', (0, 0), (-1, -1), 1, colors.grey),
                                 ('FONTSIZE', (0, 0), (-1, -1), 8),
                                 ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                                 ('ALIGN', (1, 0), (-1, -1), 'CENTER')])
        flowables.append(tbl_items)

        flowables.append(Spacer(1, 24))

        flowables.append(Paragraph(f'<b><font size=14>Total: {total_general}$</font></b>',
                                   style=styles['Droite']))

        flowables.append(Spacer(1, 12))

        frac, whole = math.modf(round(total_general, 3))
        centimes = num2words(round(frac * 1000, 0), lang='fr')
        usd = num2words(whole, lang='fr')
        texte = "Nous disons {} USD et {} centimes".format(usd, centimes)
        flowables.append(Paragraph(texte, style=styles['Titre']))

        flowables.append(Spacer(1, 24))

        doc.multiBuild(flowables, canvasmaker=FooterCanvas)
        response_data = buffer.getvalue()
        buffer.close()

        disposition = 'attachment;filename=%s' % (filename,)

        mimetype, encoding = mimetypes.guess_type(filename)
        if not mimetype:
            mimetype = 'application/octet-stream'
        if encoding:
            mimetype = '%s; charset=%s' % (mimetype, encoding)

        return HttpResponse(
            response_data,
            headers={'Content-Disposition': disposition},
            content_type=mimetype,
        )

    def generate_recu_pdf(self, data):
        filename = self.filename
        buffer = BytesIO()

        page_size = A5
        doc = SimpleDocTemplate(buffer, pagesize=landscape(page_size), rightMargin=15, leftMargin=15,
                                topMargin=10, bottomMargin=60)
        flowables = []

        # LOGO
        get_params = Parametre.objects.get(code='Params')
        print(get_params.logo)
        logo_dir = settings.MEDIA_ROOT
        logo = get_params.logo.path
        im = Image(os.path.join(logo_dir, logo), 1 * inch, 1 * inch)

        # flowables.append(im)

        school_name = [Paragraph('<b>{}</b><br /><br />'.format(get_params.ecole), style=styles['Droite'])]
        school_infos = [Paragraph(f'{get_params.adresse} <br /><br /> {get_params.telephone} <br />',
                                  style=styles['Droite'])]

        school_bloc = [school_name, school_infos]

        header_bloc = [[im, school_bloc]]

        tablestyle = TableStyle([('FONT', (0, 0), (-1, -1), 'RobotoBd', 10),
                                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                 ('ALIGN', (0, 0), (-1, -1), 'LEFT')])
        table_header = Table(header_bloc, colWidths=None)
        table_header.setStyle(tablestyle)

        flowables.append(table_header)
        flowables.append(Spacer(1, 16))

        title = Paragraph(f'<b>{self.title} No.{data.get("recu")}</b><br />', style=styles['Centre'])
        date = Paragraph(f'<u>Date: {data.get("date")}</u>', style=styles['Droite'])
        description = Paragraph(f'<b>Description:</b> &nbsp; {data.get("description")}', style=styles['Gauche'])
        montant = Paragraph(f'<b>Montant:</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {data.get("montant")}',
                            style=styles['Gauche'])
        eleve = Paragraph(f'<b>Eleve</b>: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; '
                          f'{data.get("eleve")} de la {data.get("classe")}', style=styles['Gauche'])
        paye_par = Paragraph(f'<b>Paye par:</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {data.get("paye_par")}',
                             style=styles['Gauche'])
        signature = Paragraph('<u>La Direction</u>', style=styles['Droite'])

        line = LineFlowable(85, LETTER[1] - 230)

        flowables.append(title)
        flowables.append(Spacer(1, 16))
        flowables.append(date)
        flowables.append(Spacer(1, 16))
        flowables.append(description)
        flowables.append(Spacer(1, 12))
        flowables.append(line)
        flowables.append(Spacer(1, 12))
        flowables.append(montant)
        flowables.append(Spacer(1, 12))
        flowables.append(line)
        flowables.append(Spacer(1, 12))
        flowables.append(eleve)
        flowables.append(Spacer(1, 12))
        flowables.append(line)
        flowables.append(Spacer(1, 12))
        flowables.append(paye_par)
        flowables.append(Spacer(1, 12))
        flowables.append(line)
        flowables.append(Spacer(1, 16))
        flowables.append(signature)

        # print(data)

        # print(flowables)

        doc.multiBuild(flowables)
        response_data = buffer.getvalue()
        buffer.close()

        disposition = 'attachment;filename=%s' % (filename,)

        mimetype, encoding = mimetypes.guess_type(filename)
        if not mimetype:
            mimetype = 'application/octet-stream'
        if encoding:
            mimetype = '%s; charset=%s' % (mimetype, encoding)

        return HttpResponse(
            response_data,
            headers={'Content-Disposition': disposition},
            content_type=mimetype,
        )

    def generate_excel(self, data):
        wb = Workbook()
        filename = self.filename
        ws = wb.active
        ws.title = self.title
        header = self.header

        def style_bold(data_to_style):
            col_header = 1
            for c in data_to_style:
                c = ws.cell(column=col_header, row=1, value=c)
                c.font = Font(bold=True)
                col_header += 1
                yield c

        ws.append(style_bold(header))
        col = 1
        row = 2

        for i in data:
            for k, v in i.items():
                ws.cell(column=col, row=row, value=v)
                col += 1
            col = 1
            row += 1

        with NamedTemporaryFile() as tmp:
            wb.save(tmp.name)
            tmp.seek(0)
            virtual_workbook = tmp.read()

        disposition = 'attachment;filename=%s' % ('export_' + filename,)

        mimetype, encoding = mimetypes.guess_type(filename)
        if not mimetype:
            mimetype = 'application/octet-stream'
        if encoding:
            mimetype = '%s; charset=%s' % (mimetype, encoding)

        print('FINISHING')

        return HttpResponse(
            response=virtual_workbook,
            status=200,
            headers={'Content-Disposition': disposition},
            mimetype=mimetype,
        )
