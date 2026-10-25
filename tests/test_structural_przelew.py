import pytest
from zespol_G import przelew


@pytest.mark.pelny
def test_przelew_na_zablokowanego_odbiorce(konto_nadawcy, konto_zablokowane):
    przelew(konto_nadawcy, konto_zablokowane, 100)
    assert konto_nadawcy.saldo == -100
