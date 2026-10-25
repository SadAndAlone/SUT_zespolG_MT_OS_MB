import pytest
from zespol_G import wyplac


from decimal import InvalidOperation

@pytest.mark.pelny
def test_wyplac_przekroczony_limit_jednorazowo(konto):
    with pytest.raises(ValueError):
        wyplac(konto, 5001)

@pytest.mark.pelny
def test_wyplac_przekroczony_limit_suma(konto):
    wyplac(konto, 3000)
    with pytest.raises(ValueError):
        wyplac(konto, 2001)

@pytest.mark.pelny
def test_wyplac_brak_srodkow(konto):
    with pytest.raises(ValueError):
        wyplac(konto, 999999)

@pytest.mark.pelny
def test_wyplac_none(konto):
    with pytest.raises(InvalidOperation):
        wyplac(konto, None)
