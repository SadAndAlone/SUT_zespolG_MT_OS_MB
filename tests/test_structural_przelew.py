"""P2: testy jednostkowe metody BankSystem.przelew."""

from decimal import Decimal

import pytest

from zespol_G import KontoNieIstnieje, KontoZablokowane
from conftest import NUMER_NADAWCY, NUMER_ODBIORCY


def test_przelew_poprawny(bank):
    assert bank.przelew(NUMER_NADAWCY, NUMER_ODBIORCY, 100) == Decimal("9900")
    nadawca = bank.konta[NUMER_NADAWCY]
    odbiorca = bank.konta[NUMER_ODBIORCY]
    assert nadawca.saldo == Decimal("9900")
    assert odbiorca.saldo == Decimal("2100")
    assert nadawca.historia[-1][1:] == ("przelew_wychodzacy", Decimal("100"))
    assert odbiorca.historia[-1][1:] == ("przelew_przychodzacy", Decimal("100"))


def test_przelew_zablokowany_nadawca(bank):
    bank.zablokuj_konto(NUMER_NADAWCY)
    with pytest.raises(KontoZablokowane):
        bank.przelew(NUMER_NADAWCY, NUMER_ODBIORCY, 100)
    assert bank.konta[NUMER_NADAWCY].saldo == Decimal("10000")
    assert bank.konta[NUMER_ODBIORCY].saldo == Decimal("2000")


@pytest.mark.pelny
def test_przelew_nieistniejacy_nadawca(bank):
    with pytest.raises(KontoNieIstnieje):
        bank.przelew("9999999991", NUMER_ODBIORCY, 100)


@pytest.mark.pelny
def test_przelew_nieistniejacy_odbiorca(bank):
    with pytest.raises(KontoNieIstnieje):
        bank.przelew(NUMER_NADAWCY, "9999999991", 100)


@pytest.mark.pelny
@pytest.mark.parametrize("kwota", [0, -10])
def test_przelew_kwota_niedodatnia(bank, kwota):
    with pytest.raises(ValueError, match="musi byc dodatnia"):
        bank.przelew(NUMER_NADAWCY, NUMER_ODBIORCY, kwota)


@pytest.mark.pelny
def test_przelew_niewystarczajace_srodki(bank):
    with pytest.raises(ValueError, match="Niewystarczajace srodki"):
        bank.przelew(NUMER_NADAWCY, NUMER_ODBIORCY, 10001)


@pytest.mark.pelny
def test_przelew_limit_systemowy(bank):
    bank.konta[NUMER_NADAWCY].saldo = Decimal("2000000")
    with pytest.raises(ValueError, match="dzienny limit systemowy"):
        bank.przelew(NUMER_NADAWCY, NUMER_ODBIORCY, 1000001)
    assert bank.konta[NUMER_NADAWCY].saldo == Decimal("2000000")


@pytest.mark.pelny
def test_przelew_na_zablokowanego_odbiorce_dokumentacja_p1(bank):
    """P1: przelew trafia na zablokowane konto odbiorcy (błąd)."""
    bank.zablokuj_konto(NUMER_ODBIORCY)
    assert bank.przelew(NUMER_NADAWCY, NUMER_ODBIORCY, 100) == Decimal("9900")
    assert bank.konta[NUMER_NADAWCY].saldo == Decimal("9900")
    assert bank.konta[NUMER_ODBIORCY].saldo == Decimal("2100")
    assert bank.konta[NUMER_ODBIORCY].status == "zablokowane"
