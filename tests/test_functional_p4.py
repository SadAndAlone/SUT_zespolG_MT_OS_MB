"""P4: wymagania robocze z P1 i przykładu P4; brak sut_dokumentacja.pdf."""
from decimal import Decimal as D
from datetime import date
import pytest
from zespol_G import BankSystem, KontoZablokowane, KontoNieIstnieje
N = '1234567895'

def setup(saldo='10000'):
    bank = BankSystem()
    konto = bank.utworz_konto(N, 'Test P4', D(saldo))
    return bank, konto

def state(konto):
    return konto.saldo, list(konto.historia), konto.status

@pytest.mark.parametrize('kwota', ['-0.01', '0'], ids=['W01','W02'])
def test_wplac_niedodatnia(kwota):
    bank, k = setup(); before = state(k)
    with pytest.raises(ValueError): bank.wplac(N, D(kwota))
    assert state(k) == before

@pytest.mark.parametrize('kwota', ['0.01','100'], ids=['W03','W04'])
def test_wplac_saldo(kwota):
    bank, k = setup()
    assert bank.wplac(N, D(kwota)) == D('10000') + D(kwota)
    assert k.saldo == D('10000') + D(kwota)

def test_W05_wplac_historia():
    bank, k = setup()
    bank.wplac(N, D('100'))
    assert k.historia == [(date.today(), 'wplata', D('100'))]

def test_W06_wplac_zablokowane():
    bank, k = setup(); bank.zablokuj_konto(N); before = state(k)
    with pytest.raises(KontoZablokowane): bank.wplac(N, D('100'))
    assert state(k) == before

def test_W07_wplac_brak_konta():
    bank, k = setup(); before = state(k)
    with pytest.raises(KontoNieIstnieje): bank.wplac('0000000000', D('100'))
    assert state(k) == before

@pytest.mark.parametrize('kwota', ['-0.01','0'], ids=['Y01','Y02'])
def test_wyplac_niedodatnia(kwota):
    bank, k = setup(); before = state(k)
    with pytest.raises(ValueError): bank.wyplac(N, D(kwota))
    assert state(k) == before

@pytest.mark.parametrize('saldo,kwota', [('100','0.01'),('100','99.99'),('100','100'),('10000','4999.99'),('10000','5000')], ids=['Y03','Y04','Y05','Y07','Y08'])
def test_wyplac_poprawna(saldo,kwota):
    bank, k = setup(saldo)
    assert bank.wyplac(N, D(kwota)) == D(saldo)-D(kwota)
    assert k.saldo == D(saldo)-D(kwota)
    assert k.historia == [(date.today(), 'wyplata', D(kwota))]

@pytest.mark.parametrize('saldo,kwota', [('100','100.01'),('10000','5000.01')], ids=['Y06','Y09'])
def test_wyplac_odmowa(saldo,kwota):
    bank, k = setup(saldo); before = state(k)
    with pytest.raises(ValueError): bank.wyplac(N, D(kwota))
    assert state(k) == before

@pytest.mark.parametrize('kwota,odmowa', [('999.99',False),('1000',False),('1000.01',True)], ids=['Y10','Y11','Y12'])
def test_wyplac_limit_laczny(kwota,odmowa):
    bank, k = setup(); bank.wyplac(N,D('4000')); before = state(k)
    if odmowa:
        with pytest.raises(ValueError): bank.wyplac(N,D(kwota))
        assert state(k) == before
    else:
        assert bank.wyplac(N,D(kwota)) == D('6000')-D(kwota)
        assert k.historia == [(date.today(),'wyplata',D('4000')),(date.today(),'wyplata',D(kwota))]

@pytest.mark.parametrize('kwota', ['100','0','6000'], ids=['Y13','Y14','Y15'])
def test_wyplac_blokada(kwota):
    bank, k = setup('100'); bank.zablokuj_konto(N); before = state(k)
    with pytest.raises(KontoZablokowane): bank.wyplac(N,D(kwota))
    assert state(k) == before

def test_Y16_wyplac_brak_konta():
    bank, k = setup(); before = state(k)
    with pytest.raises(KontoNieIstnieje): bank.wyplac('0000000000',D('100'))
    assert state(k) == before
