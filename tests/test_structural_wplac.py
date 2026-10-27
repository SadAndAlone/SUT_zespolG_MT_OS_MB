"""P2: pokrycie instrukcji i gałęzi metody BankSystem.wplac.

Testy oznaczone jako 'pelny' są dodane w fazie 2. Zachowania błędne z P1
są celowo dokumentowane, a kod SUT nie jest zmieniany.
"""

from decimal import Decimal

import pytest

from zespol_G import KontoNieIstnieje
from conftest import NUMER_NADAWCY


def test_wplac_poprawna(bank):
    assert bank.wplac(NUMER_NADAWCY, 100) == Decimal("10100")
    assert bank.konta[NUMER_NADAWCY].saldo == Decimal("10100")


@pytest.mark.pelny
def test_wplac_konto_nie_istnieje(bank):
    with pytest.raises(KontoNieIstnieje):
        bank.wplac("9999999991", 100)


@pytest.mark.pelny
def test_wplac_niepoprawny_typ(bank):
    with pytest.raises(TypeError, match="Kwota musi byc liczba"):
        bank.wplac(NUMER_NADAWCY, "100")


@pytest.mark.pelny
@pytest.mark.parametrize("kwota", [0, -50])
def test_wplac_kwota_niedodatnia(bank, kwota):
    with pytest.raises(ValueError, match="musi byc dodatnia"):
        bank.wplac(NUMER_NADAWCY, kwota)
    assert bank.konta[NUMER_NADAWCY].saldo == Decimal("10000")


@pytest.mark.pelny
@pytest.mark.parametrize("konto_zablokowane", [False, True], ids=["historia", "zablokowane"])
def test_wplac_dokumentacja_usterek_p1(bank, konto_zablokowane):
    """P1: historia jest podwójna; wpłata na konto zablokowane przechodzi."""
    if konto_zablokowane:
        bank.zablokuj_konto(NUMER_NADAWCY)
        assert bank.konta[NUMER_NADAWCY].status == "zablokowane"

    assert bank.wplac(NUMER_NADAWCY, 100) == Decimal("10100")
    konto = bank.konta[NUMER_NADAWCY]
    assert len(konto.historia) == 2  # udokumentowana usterka P1
    assert all(wpis[1] == "wplata" for wpis in konto.historia)
    assert konto.saldo == Decimal("10100")
    if konto_zablokowane:
        assert konto.status == "zablokowane"  # blokada nie zatrzymuje wpłaty
