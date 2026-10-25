import pytest
from zespol_G import wplac


@pytest.mark.pelny
def test_wplac_zly_typ(konto):
    with pytest.raises(TypeError):
        wplac(konto, "100")

@pytest.mark.pelny
def test_wplac_kwota_niedodatnia(konto):
    with pytest.raises(ValueError):
        wplac(konto, -50)
    with pytest.raises(ValueError):
        wplac(konto, 0)

@pytest.mark.pelny
def test_wplac_podwojna_historia(konto):
    wplac(konto, 100)
    assert len(konto.historia) == 2
