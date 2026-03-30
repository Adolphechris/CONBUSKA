"""Tests pour le générateur PDF (helpers sans dépendance ReportLab lourde)."""

from decimal import Decimal

from utils.pdf_generator import _fc_to_usd_equiv


def test_fc_to_usd_equiv_decimal_divided_by_float_taux() -> None:
    """Régression : Decimal / float levait TypeError dans _totals_block."""
    out = _fc_to_usd_equiv(Decimal("5600000"), 2800.0)
    assert out == Decimal("2000")


def test_fc_to_usd_equiv_none_or_zero_taux() -> None:
    assert _fc_to_usd_equiv(Decimal("100"), None) is None
    assert _fc_to_usd_equiv(Decimal("100"), 0) is None
    assert _fc_to_usd_equiv(Decimal("100"), Decimal("0")) is None


def test_fc_to_usd_equiv_decimal_taux() -> None:
    out = _fc_to_usd_equiv(Decimal("2800"), Decimal("2800"))
    assert out == Decimal("1")
