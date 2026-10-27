"""Powtarzalne dane testowe dla SUT z zespołu G."""

from decimal import Decimal

import pytest

from zespol_G import BankSystem


NUMER_NADAWCY = "1234567895"
NUMER_ODBIORCY = "0000000011"
SALDO_NADAWCY = Decimal("10000")
SALDO_ODBIORCY = Decimal("2000")


@pytest.fixture
def bank():
    system = BankSystem()
    system.utworz_konto(NUMER_NADAWCY, "Nadawca", SALDO_NADAWCY)
    system.utworz_konto(NUMER_ODBIORCY, "Odbiorca", SALDO_ODBIORCY)
    return system
