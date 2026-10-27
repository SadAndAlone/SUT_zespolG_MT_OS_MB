"""P2: testy jednostkowe metody BankSystem.wyplac."""

from decimal import Decimal, InvalidOperation

import pytest

from zespol_G import KontoNieIstnieje, KontoZablokowane
from conftest import NUMER_NADAWCY


def test_wyplac_poprawna(bank):
    assert bank.wyplac(NUMER_NADAWCY, 100) == Decimal("9900")
    assert bank.konta[NUMER_NADAWCY].historia[0][1:] == ("wyplata", Decimal("100"))


def test_wyplac_zablokowany_nadawca(bank):
    bank.zablokuj_konto(NUMER_NADAWCY)
    with pytest.raises(KontoZablokowane):
        bank.wyplac(NUMER_NADAWCY, 100)
    assert bank.konta[NUMER_NADAWCY].saldo == Decimal("10000")


@pytest.mark.pelny
def test_wyplac_konto_nie_istnieje(bank):
    with pytest.raises(KontoNieIstnieje):
        bank.wyplac("9999999991", 100)


@pytest.mark.pelny
@pytest.mark.parametrize("kwota", [0, -50])
def test_wyplac_kwota_niedodatnia(bank, kwota):
    with pytest.raises(ValueError, match="musi byc dodatnia"):
        bank.wyplac(NUMER_NADAWCY, kwota)


@pytest.mark.pelny
def test_wyplac_niewystarczajace_srodki(bank):
    with pytest.raises(ValueError, match="Niewystarczajace srodki"):
        bank.wyplac(NUMER_NADAWCY, 10001)
    assert bank.konta[NUMER_NADAWCY].saldo == Decimal("10000")


@pytest.mark.pelny
def test_wyplac_przekroczony_limit_jednorazowo(bank):
    with pytest.raises(ValueError, match="dzienny limit"):
        bank.wyplac(NUMER_NADAWCY, 5001)


@pytest.mark.pelny
def test_wyplac_przekroczony_limit_sumy(bank):
    # Wplata w historii nie jest wypłata; codzienny limit ma ją pominąć.
    assert bank.wplac(NUMER_NADAWCY, 100) == Decimal("10100")
    assert bank.wyplac(NUMER_NADAWCY, 3000) == Decimal("7100")
    with pytest.raises(ValueError, match="dzienny limit"):
        bank.wyplac(NUMER_NADAWCY, 2001)
    assert bank.konta[NUMER_NADAWCY].saldo == Decimal("7100")


@pytest.mark.pelny
def test_wyplac_dokladnie_limit_jest_dozwolony(bank):
    """Granica wynosi > 5000, a nie >= 5000."""
    assert bank.wyplac(NUMER_NADAWCY, 5000) == Decimal("5000")
    assert bank.konta[NUMER_NADAWCY].historia[-1][2] == Decimal("5000")


@pytest.mark.pelny
def test_wyplac_none_powoduje_invalidoperation(bank):
    """Udokumentowana usterka P1: brak TypeError dla None."""
    with pytest.raises(InvalidOperation):
        bank.wyplac(NUMER_NADAWCY, None)
    assert bank.konta[NUMER_NADAWCY].saldo == Decimal("10000")
