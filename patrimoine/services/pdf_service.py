import datetime
from io import BytesIO
from decimal import Decimal

from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# ---------- Styles ----------
_styles = getSampleStyleSheet()
_styles.add(ParagraphStyle(name='PDFTitre', alignment=TA_LEFT, fontName='Helvetica-Bold', fontSize=14))
_styles.add(ParagraphStyle(name='PDFSousTitre', alignment=TA_LEFT, fontName='Helvetica-Bold', fontSize=11))
_styles.add(ParagraphStyle(name='PDFCentre', alignment=TA_CENTER, fontName='Helvetica', fontSize=9))
_styles.add(ParagraphStyle(name='PDFDroite', alignment=TA_RIGHT, fontName='Helvetica', fontSize=9))

_VERT = colors.Color(red=26/255, green=187/255, blue=156/255)
_ROUGE = colors.Color(red=231/255, green=76/255, blue=60/255)
_BLEU = colors.Color(red=42/255, green=63/255, blue=84/255)
_GRIS = colors.Color(red=245/255, green=247/255, blue=250/255)


def _fmt(value, usd_value=None, taux=None):
    """Formate un Decimal ou float en entier avec séparateur milliers.
    Si usd_value est fourni, retourne un format dual currency."""
    try:
        fc_str = f"{int(round(float(value))):,}".replace(",", " ") + " FC"
        if usd_value is not None and taux:
            usd_str = f"{float(usd_value):,.2f} $".replace(",", " ")
            return f"{usd_str}\n{fc_str}"
        return fc_str
    except (TypeError, ValueError):
        return "0 FC"


class PatrimoinePDFService:

    @staticmethod
    def generate(date_debut: datetime.date, date_fin: datetime.date) -> HttpResponse:
        from patrimoine.models import FondsRoulementSnapshot
        from caisse.models import MouvementCaisse
        from django.db.models import Sum
        from parametres.models import Parametre

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(LETTER),
            rightMargin=20, leftMargin=20,
            topMargin=20, bottomMargin=40,
        )
        flowables = []

        params = Parametre.objects.get(code='Params')

        # ── En-tête ──────────────────────────────────────────────────
        flowables.append(Paragraph(params.societe, _styles['PDFTitre']))
        flowables.append(Paragraph(
            f"Rapport Financier — du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}",
            _styles['PDFSousTitre']
        ))
        flowables.append(Paragraph(
            f"Édité le {datetime.date.today().strftime('%d/%m/%Y')}",
            _styles['PDFCentre']
        ))
        flowables.append(Spacer(1, 12))

        # ── Section 1 : Historique du Fonds de Roulement ─────────────
        flowables.append(Paragraph("1. Historique du Fonds de Roulement", _styles['PDFSousTitre']))
        flowables.append(Spacer(1, 6))

        snapshots = list(
            FondsRoulementSnapshot.objects
            .filter(date__range=(date_debut, date_fin))
            .order_by("-date")
        )

        # Dual currency: récupérer le taux pour l'affichage USD
        from parametres.models import get_taux_usd_cdf
        taux = get_taux_usd_cdf()

        fr_header = [['Date', 'FR Initial', 'Entrées (EJ)', 'Sorties (SJ)', 'FR Final', 'Contre-vérif.', 'Écart']]
        fr_data = [
            [
                s.date.strftime('%d/%m/%Y'),
                _fmt(s.fr_initial, s.fr_initial_usd, taux),
                _fmt(s.ej, s.ej_usd, taux),
                _fmt(s.sj, s.sj_usd, taux),
                _fmt(s.fr_final, s.fr_final_usd, taux),
                _fmt(s.fr_calcule, None, None),  # Contre-vérif FC uniquement (historique)
                _fmt(s.ecart, None, None),  # Écart FC uniquement
            ]
            for s in snapshots
        ]

        if not fr_data:
            fr_data = [['Aucune donnée pour cette période', '', '', '', '', '', '']]

        tbl_fr = Table(
            fr_header + fr_data,
            colWidths=[70, 90, 90, 90, 90, 95, 80],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), _BLEU),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, _GRIS]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ])
        )
        flowables.append(tbl_fr)
        flowables.append(Spacer(1, 20))

        # ── Section 2 : Analyse Structurelle ─────────────────────────
        flowables.append(Paragraph("2. Analyse Structurelle des Flux", _styles['PDFSousTitre']))
        flowables.append(Spacer(1, 6))

        base_qs = MouvementCaisse.objects.filter(
            date_mouvement__date__range=(date_debut, date_fin)
        ).exclude(rubrique__nom__in={"clients", "fournisseurs"})

        total_entrees = (
            base_qs.filter(type_mouvement="ENTREE")
            .aggregate(t=Sum("montant"))["t"] or Decimal("0")
        )
        total_sorties = (
            base_qs.filter(type_mouvement="SORTIE")
            .aggregate(t=Sum("montant"))["t"] or Decimal("0")
        )

        def repartition(type_mvt, total, total_usd):
            qs = (
                base_qs.filter(type_mouvement=type_mvt)
                .values("rubrique__nom")
                .annotate(montant=Sum("montant"))
                .order_by("-montant")
            )
            rows = []
            for r in qs:
                pct = round(float(r["montant"]) / float(total) * 100, 1) if total else 0
                montant_usd = (Decimal(str(r["montant"])) / taux) if taux else None
                rows.append([r["rubrique__nom"] or "—", _fmt(r["montant"], montant_usd, taux), f"{pct} %"])
            return rows

        rep_e = repartition("ENTREE", total_entrees, total_entrees_usd) or [["Aucune donnée", "", ""]]
        rep_s = repartition("SORTIE", total_sorties, total_sorties_usd) or [["Aucune donnée", "", ""]]

        entrees_header = [['ENTRÉES — Catégorie', 'Montant', '%']]
        sorties_header = [['SORTIES — Catégorie', 'Montant', '%']]

        def _style_rep(header_color):
            return TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), header_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, _GRIS]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ])

        tbl_e = Table(
            entrees_header + rep_e + [['TOTAL', _fmt(total_entrees), '100 %']],
            colWidths=[180, 120, 60],
            style=_style_rep(_VERT)
        )
        tbl_s = Table(
            sorties_header + rep_s + [['TOTAL', _fmt(total_sorties), '100 %']],
            colWidths=[180, 120, 60],
            style=_style_rep(_ROUGE)
        )

        # Côte-à-côte
        deux_colonnes = Table(
            [[tbl_e, Spacer(20, 1), tbl_s]],
            colWidths=[370, 20, 370]
        )
        flowables.append(deux_colonnes)
        flowables.append(Spacer(1, 20))

        # ── Solde final ───────────────────────────────────────────────
        solde = total_entrees - total_sorties
        solde_usd = (Decimal(str(solde)) / taux) if taux else None
        flowables.append(Paragraph(
            f"<b>Solde de la période : {_fmt(solde, solde_usd, taux)}</b>",
            _styles['PDFDroite']
        ))
        flowables.append(Spacer(1, 20))

        # ── Section 3 : Récapitulatif des Justificatifs Sources ───────
        flowables.append(Paragraph("3. Récapitulatif des Justificatifs Sources", _styles['PDFSousTitre']))
        flowables.append(Spacer(1, 6))

        # 3a — Fiches d'Approvisionnement
        from patrimoine.models import ResultatApprovisionnementSnapshot
        appros = list(
            ResultatApprovisionnementSnapshot.objects
            .filter(date__range=(date_debut, date_fin))
            .select_related("approvisionnement")
            .order_by("-date")
        )

        flowables.append(Paragraph("a) Fiches d'Approvisionnement", _styles['Normal']))
        flowables.append(Spacer(1, 4))

        appro_header = [['Réf.', 'Date', 'Chiffre d\'Affaires', 'Coût d\'Achat', 'Frais', 'Résultat Brut']]
        appro_data = [
            [
                f"#{a.approvisionnement.numero}",
                a.date.strftime('%d/%m/%Y'),
                _fmt(a.chiffre_affaires, a.chiffre_affaires_usd, taux),
                _fmt(a.cout_achat, a.cout_achat_usd, taux),
                _fmt(a.frais_achat, a.frais_achat_usd, taux),
                _fmt(a.resultat_brut, a.resultat_brut_usd, taux),
            ]
            for a in appros
        ] or [['Aucun approvisionnement sur la période', '', '', '', '', '']]

        tbl_appro = Table(
            appro_header + appro_data,
            colWidths=[50, 65, 110, 100, 80, 105],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), _VERT),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (1, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, _GRIS]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ])
        )
        flowables.append(tbl_appro)
        flowables.append(Spacer(1, 14))

        # 3b — Mouvements de Caisse significatifs
        from caisse.models import MouvementCaisse as MC
        mvts = list(
            MC.objects
            .filter(date_mouvement__date__range=(date_debut, date_fin))
            .exclude(rubrique__nom__in={"clients", "fournisseurs"})
            .select_related("caisse", "rubrique")
            .order_by("-date_mouvement")[:100]
        )

        flowables.append(Paragraph("b) Mouvements de Caisse (100 derniers)", _styles['Normal']))
        flowables.append(Spacer(1, 4))

        mvt_header = [['Date', 'Caisse', 'Type', 'Rubrique', 'Motif', 'Montant']]
        mvt_data = [
            [
                m.date_mouvement.strftime('%d/%m/%Y'),
                str(m.caisse)[:20],
                m.type_mouvement,
                (m.rubrique.nom if m.rubrique else '—')[:18],
                (m.motif or '—')[:28],
                _fmt(m.montant),
            ]
            for m in mvts
        ] or [['Aucun mouvement sur la période', '', '', '', '', '']]

        _ORANGE = colors.Color(red=243/255, green=156/255, blue=18/255)
        tbl_mvt = Table(
            mvt_header + mvt_data,
            colWidths=[55, 90, 45, 85, 145, 90],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), _BLEU),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, _GRIS]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ])
        )
        flowables.append(tbl_mvt)
        flowables.append(Spacer(1, 10))

        # ── Build ─────────────────────────────────────────────────────
        doc.build(flowables)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        filename = f"rapport_patrimoine_{date_debut}_{date_fin}.pdf"
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
