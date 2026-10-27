# Zespół G — zadanie P2 (bez usuwania materiałów P1)

Ten folder jest kontynuacją **oryginalnego** projektu `SUT_zespolG_MT_OS_MB-main`.
Zachowano wszystkie pliki przesłane w pierwotnym archiwum, włącznie z materiałami P1
(`zadania/`, `raporty/raport_P1.pdf`, `awarie.jsonl`, `raporty.txt`, `zespol_G.py`, `.vs/`).
Plik `zespol_G.py` nie został zmieniony.

## Co dodano / uzupełniono dla zajęć nr 2 (P2)

- `tests/test_structural_wplac.py`, `tests/test_structural_wyplac.py`, `tests/test_structural_przelew.py` — uruchamialne testy strukturalne (26 przypadków); trzy istniejące niekompletne testy zostały **zachowane oddzielnie** w `tests/oryginalne_testy_przed_P2/`.
- `tests/conftest.py` — dane i fixture testów.
- `pytest.ini`, `requirements-dev.txt` — ustawienia i zależności.
- `wyniki_pokrycia/faza1.txt`, `faza2.txt`, `porownanie_pokrycia.md` — wyniki pomiarów.
- `zadania/NSI_P2-1.pdf`, `raporty/Raport_P2-1.pdf` — karta zajęć P2 i raport P2.

Plik `README.md` i `.gitignore` pozostawiono bez zmian.

## Jak uruchomić w Windows (PowerShell / terminal w katalogu projektu)

Zainstaluj Python i uruchom:

```powershell
py -m pip install -r requirements-dev.txt
```

**Faza 1:**

```powershell
py -m pytest -m "not pelny" --cov=zespol_G --cov-report=term-missing --cov-branch
```

**Faza 2:**

```powershell
py -m pytest --cov=zespol_G --cov-report=term-missing --cov-branch --cov-report=html
```

Zobacz szczegółowy raport: `htmlcov/index.html` (powstaje po fazie 2).

W raporcie P2: 5 testów / 50% (faza 1), 26 testów / 61% (faza 2),
65% statement coverage, 50% branch coverage dla całego pliku.
Wybrane metody: `wplac`, `wyplac`, `przelew` — 100% obu miar w fazie 2.

## Uwaga

Dokument `NSI_P2-1.pdf` dotyczy **zajęć projektowych nr 2**, a nie nr 3.
Do przygotowania bloku zajęć nr 3 będzie potrzebna właściwa karta zadania nr 3.

Folder `.vs/` to pliki środowiska Visual Studio zachowane z oryginału.
Do repozytorium GitHub najlepiej nie commitować plików lokalnego cache IDE.
