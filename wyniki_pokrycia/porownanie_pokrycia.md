# Porównanie pokrycia kodu — P2

| Metryka | Faza 1 | Faza 2 |
|---|---:|---:|
| Liczba zaliczonych testów | 5 | 26 |
| Pokrycie instrukcji pliku zespol_G.py | 57% (89/155) | 65% (100/155) |
| Pokrycie gałęzi pliku zespol_G.py | 29% (17/58) | 50% (29/58) |
| Pokrycie łączne według coverage.py | 50% | 61% |
| Metoda wplac: instrukcje / gałęzie | 80% / 50% | 100% / 100% |
| Metoda wyplac: instrukcje / gałęzie | 77% / 62% | 100% / 100% |
| Metoda przelew: instrukcje / gałęzie | 82% / 62% | 100% / 100% |

Brakujące linie w fazie 2 dotyczą m.in. procesora zewnętrznego,
naliczania odsetek, historii operacji i wyciągu miesięcznego,
ponieważ P2 obejmuje metody `wplac`, `wyplac`, `przelew`.
Stwierdzone wcześniej błędy w SUT zachowano i opisano w testach.

Szczegółowe logi komend znajdują się w `faza1.txt` i `faza2.txt`.
