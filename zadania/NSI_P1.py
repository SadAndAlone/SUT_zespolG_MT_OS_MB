"""
NSI – zajęcia projektowe nr 1 (P1): pomiar niezawodności SUT.

Zespół G – system zarządzania kontem bankowym (zespol_G.py).
SUT nie jest tutaj poprawiany: owijamy jego metody loggerem i zbieramy baseline.
"""

from __future__ import annotations

import functools
import json
import time
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from zespol_G import BankSystem, KontoZablokowane, ZewnetrznyProcesor

KATALOG = Path(__file__).resolve().parent
SUT_PATH = KATALOG / "zespol_G.py"
LOG_PATH = KATALOG / "awarie.jsonl"  # log awarii: jedna linia JSON na zdarzenie

METODY_SUT = (
    "utworz_konto",
    "zablokuj_konto",
    "odblokuj_konto",
    "wplac",
    "wyplac",
    "przelew",
    "nalicz_odsetki",
    "historia_w_okresie",
    "wyciag_miesieczny",
    "przelew_zewnetrzny",
)


def niezawodnosc_logger(log_path: str | Path = LOG_PATH):
    """Dekorator z karty zajęć: loguje wyjątek i rzuca go dalej (bez połykania)."""

    log_path = Path(log_path)

    def dekorator(funkcja):
        @functools.wraps(funkcja)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return funkcja(*args, **kwargs)
            except Exception as e:
                # Logujemy wyjątek, ale go nie połykamy (raise poniżej).
                self_obj = args[0] if args else None
                czyste_args = args[1:] if self_obj is not None else args
                zapisz_wpis(
                    {
                        "timestamp": time.time(),
                        "funkcja": funkcja.__name__,
                        "args": repr(czyste_args),  # dane wejściowe do reprodukcji
                        "kwargs": repr(kwargs),
                        "rodzaj": "wyjatek",
                        "typ_bledu": type(e).__name__,
                        "komunikat": str(e),
                        "czas_do_awarii_s": time.time() - start,
                        "zrodlo": "dekorator",
                    },
                    log_path,
                )
                raise  # awaria ma być widoczna, nie ukryta

        return wrapper

    return dekorator


def zapisz_wpis(wpis: dict, log_path: Path = LOG_PATH) -> None:
    # Dopisanie jednej awarii na koniec pliku JSONL.
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(wpis, ensure_ascii=False, default=str) + "\n")


def owin_metody_sut(log_path: Path = LOG_PATH) -> None:
    # Każda metoda SUT przechodzi przez logger wyjątków.
    dekorator = niezawodnosc_logger(log_path)
    for nazwa in METODY_SUT:
        metoda = getattr(BankSystem, nazwa)
        if getattr(metoda, "_nsi_owiniete", False):
            continue
        owinięta = dekorator(metoda)
        owinięta._nsi_owiniete = True
        setattr(BankSystem, nazwa, owinięta)


def numer_z_suma_kontrolna(prefiks9: str) -> str:
    if len(prefiks9) != 9 or not prefiks9.isdigit():
        raise ValueError("Prefiks musi mieć 9 cyfr")
    suma = sum(int(c) for c in prefiks9) % 10
    return prefiks9 + str(suma)


def licz_loc(sciezka: Path) -> int:
    loc = 0
    for linia in sciezka.read_text(encoding="utf-8").splitlines():
        pusta = linia.strip()
        if not pusta or pusta.startswith("#"):
            continue
        loc += 1
    return loc


def wczytaj_log(log_path: Path = LOG_PATH) -> list[dict]:
    if not log_path.exists():
        return []
    wpisy = []
    for linia in log_path.read_text(encoding="utf-8").splitlines():
        if linia.strip():
            wpisy.append(json.loads(linia))
    return wpisy


def mttf_z_wpisow(wpisy: list[dict], t0: float) -> float | None:
    """MTTF jak na karcie: średnia odstępów między kolejnymi awariami od startu sesji."""
    if not wpisy:
        return None
    czasy = sorted(float(w["timestamp"]) for w in wpisy)
    poprzedni = t0
    delty = []
    for t in czasy:
        delty.append(t - poprzedni)
        poprzedni = t
    return sum(delty) / len(delty)


def wywolaj(metoda, *args, **kwargs):
    try:
        return metoda(*args, **kwargs), None
    except Exception as e:
        return None, e


def oznacz_awarie_spec(
    *,
    funkcja: str,
    args,
    kwargs,
    rodzaj: str,
    typ_bledu: str,
    komunikat: str,
    severity: str,
    usterka_id: str,
    opis: str,
    t0_wywolania: float,
) -> None:
    # Cicha awaria: SUT nie rzucił wyjątku, ale wynik jest niezgodny ze specyfikacją.
    zapisz_wpis(
        {
            "timestamp": time.time(),
            "funkcja": funkcja,
            "args": repr(args),
            "kwargs": repr(kwargs),
            "rodzaj": rodzaj,
            "typ_bledu": typ_bledu,
            "komunikat": komunikat,
            "czas_do_awarii_s": time.time() - t0_wywolania,
            "zrodlo": "obserwacja_specyfikacji",
            "severity": severity,  # krytyczna / powazna / drobna
            "usterka_id": usterka_id,
            "opis": opis,
            "awaria_niezawodnosciowa": True,
        }
    )


def przeprowadz_eksploracje(bank: BankSystem) -> dict:
    """20–30 wywołań: typowe ścieżki + puste, ujemne, bardzo duże, znaki specjalne."""
    n1 = numer_z_suma_kontrolna("123456789")
    n2 = numer_z_suma_kontrolna("987654321")
    n3 = numer_z_suma_kontrolna("111111111")
    n_zla_suma = "1234567890"
    n_nieistnieje = numer_z_suma_kontrolna("555555555")
    dzis = date.today()
    licznik_wywolan = 0

    def krok(nazwa: str, metoda, args, kwargs=None, po=None):
        nonlocal licznik_wywolan
        kwargs = kwargs or {}
        licznik_wywolan += 1
        t0 = time.time()
        wynik, blad = wywolaj(metoda, *args, **kwargs)
        if po is not None:
            po(wynik, blad, t0)
        time.sleep(0.02)
        return wynik, blad

    # 1. poprawne utworzenie
    krok("utworz_konto", bank.utworz_konto, (n1, "Anna Nowak", 1000))

    # 2. duplikat: komunikat ma {{numer}} zamiast numeru konta
    def po_duplikat(wynik, blad, t0):
        if blad is None:
            oznacz_awarie_spec(
                funkcja="utworz_konto",
                args=(n1, "Anna Nowak", 0),
                kwargs={},
                rodzaj="zle_dane_wyjsciowe",
                typ_bledu="BrakWyjatku",
                komunikat="Oczekiwano ValueError przy duplikacie konta",
                severity="powazna",
                usterka_id="F_DUPLIKAT_BEZ_WYJATKU",
                opis="Ponowne utworzenie istniejącego konta nie zgłosiło błędu.",
                t0_wywolania=t0,
            )
            return
        if "{numer}" in str(blad) or "{{numer}}" in repr(blad):
            oznacz_awarie_spec(
                funkcja="utworz_konto",
                args=(n1, "Anna Nowak", 0),
                kwargs={},
                rodzaj="zle_dane_wyjsciowe",
                typ_bledu=type(blad).__name__,
                komunikat=str(blad),
                severity="drobna",
                usterka_id="F_KOMUNIKAT_NUMER_NAWIASY",
                opis="Literał {numer} w komunikacie zamiast numeru konta (podwójne nawiasy w f-stringu).",
                t0_wywolania=t0,
            )

    krok("utworz_konto duplikat", bank.utworz_konto, (n1, "Anna Nowak", 0), po=po_duplikat)

    # 3–6. nietypowe numery
    krok("utworz_konto pusty", bank.utworz_konto, ("", "X", 0))
    krok("utworz_konto za krotki", bank.utworz_konto, ("123", "X", 0))
    krok("utworz_konto znaki specjalne", bank.utworz_konto, ("12#45$7890", "X", 0))

    # 7. numer 10-cyfrowy bez poprawnej sumy kontrolnej – metoda _numer_poprawny istnieje, ale nie jest użyta
    def po_suma(wynik, blad, t0):
        if blad is None and not BankSystem._numer_poprawny(n_zla_suma):
            oznacz_awarie_spec(
                funkcja="utworz_konto",
                args=(n_zla_suma, "Zla Suma", 10),
                kwargs={},
                rodzaj="zle_dane_wyjsciowe",
                typ_bledu="BrakWalidacji",
                komunikat="Utworzono konto z niepoprawną sumą kontrolną",
                severity="powazna",
                usterka_id="F_BRAK_SUMY_KONTROLNEJ",
                opis="utworz_konto nie korzysta z _numer_poprawny; akceptuje numer z błędną cyfrą kontrolną.",
                t0_wywolania=t0,
            )

    krok("utworz_konto zla suma", bank.utworz_konto, (n_zla_suma, "Zla Suma", 10), po=po_suma)

    # 8–9. drugie poprawne konto + wplata (podwójny wpis w historii)
    krok("utworz_konto n2", bank.utworz_konto, (n2, "Jan Kowalski", 200))

    def po_wplac(wynik, blad, t0):
        if blad is not None:
            return
        historia = bank.konta[n1].historia
        wpisy_wplat = [h for h in historia if h[1] == "wplata"]
        if len(wpisy_wplat) >= 2:
            oznacz_awarie_spec(
                funkcja="wplac",
                args=(n1, 50),
                kwargs={},
                rodzaj="zle_dane_wyjsciowe",
                typ_bledu="PodwojnaHistoria",
                komunikat=f"Po jednej wpłacie historia ma {len(wpisy_wplat)} wpisów typu wplata",
                severity="powazna",
                usterka_id="F_WPLATA_PODWOJNA_HISTORIA",
                opis="wplac dwukrotnie wywołuje dodaj_wpis; saldo rośnie raz, historia dwa razy.",
                t0_wywolania=t0,
            )

    krok("wplac 50", bank.wplac, (n1, 50), po=po_wplac)

    # 10–13. nietypowe kwoty wpłaty
    krok("wplac 0", bank.wplac, (n1, 0))
    krok("wplac ujemna", bank.wplac, (n1, -100))
    krok("wplac tekst", bank.wplac, (n1, "abc"))
    krok("wplac bardzo duza", bank.wplac, (n1, 10**18))

    # 14. wpłata na zablokowane konto – brak kontroli statusu
    krok("zablokuj n3", bank.utworz_konto, (n3, "Zablokowany", 80))
    krok("zablokuj", bank.zablokuj_konto, (n3,))

    def po_wplac_zablokowane(wynik, blad, t0):
        if blad is None:
            oznacz_awarie_spec(
                funkcja="wplac",
                args=(n3, 20),
                kwargs={},
                rodzaj="zle_dane_wyjsciowe",
                typ_bledu="BrakWyjatku",
                komunikat="Wpłata na zablokowane konto została przyjęta",
                severity="powazna",
                usterka_id="F_WPLATA_NA_ZABLOKOWANE",
                opis="wplac nie sprawdza statusu konta (w przeciwieństwie do wyplac/przelew).",
                t0_wywolania=t0,
            )

    krok("wplac zablokowane", bank.wplac, (n3, 20), po=po_wplac_zablokowane)

    # 15–17. wypłaty
    krok("wyplac OK", bank.wyplac, (n1, 30))
    krok("wyplac za duzo", bank.wyplac, (n1, 10**9))
    krok("wyplac zablokowane", bank.wyplac, (n3, 1))

    # 18. przelew z zablokowanego – komunikat {{numer_z}}
    def po_przelew_zablokowany(wynik, blad, t0):
        if isinstance(blad, KontoZablokowane) and ("{numer_z}" in str(blad) or "{{numer_z}}" in repr(blad)):
            oznacz_awarie_spec(
                funkcja="przelew",
                args=(n3, n2, 1),
                kwargs={},
                rodzaj="zle_dane_wyjsciowe",
                typ_bledu="KontoZablokowane",
                komunikat=str(blad),
                severity="drobna",
                usterka_id="F_KOMUNIKAT_PRZELEW_NAWIASY",
                opis="Literał {numer_z} w komunikacie o zablokowanym koncie źródłowym.",
                t0_wywolania=t0,
            )

    krok("przelew z zablokowanego", bank.przelew, (n3, n2, 1), po=po_przelew_zablokowany)

    # 19. przelew NA zablokowane – brak kontroli konta docelowego
    def po_przelew_do_zablokowanego(wynik, blad, t0):
        if blad is None:
            oznacz_awarie_spec(
                funkcja="przelew",
                args=(n1, n3, 5),
                kwargs={},
                rodzaj="zle_dane_wyjsciowe",
                typ_bledu="BrakWyjatku",
                komunikat="Przelew na zablokowane konto docelowe został zrealizowany",
                severity="powazna",
                usterka_id="F_PRZELEW_NA_ZABLOKOWANE",
                opis="przelew sprawdza status tylko konta źródłowego.",
                t0_wywolania=t0,
            )

    krok("przelew na zablokowane", bank.przelew, (n1, n3, 5), po=po_przelew_do_zablokowanego)

    # 20–24. kolejne nietypowe wejścia
    krok("przelew ujemny", bank.przelew, (n1, n2, -15))
    krok("przelew pusty numer", bank.przelew, ("", n2, 1))
    krok("konto nie istnieje", bank.wyplac, (n_nieistnieje, 1))
    krok("nalicz odsetki", bank.nalicz_odsetki, (n1, 4.5, 3))
    krok("nalicz miesiące ujemne", bank.nalicz_odsetki, (n1, 4.5, -2))

    # 25. odsetki – niecałkowita liczba miesięcy (oczekiwany wyjątek / dziwne zachowanie)
    krok("nalicz miesiące float/tekst", bank.nalicz_odsetki, (n1, 3, "dwa"))

    # 26. historia w okresie
    krok("historia", bank.historia_w_okresie, (n1, dzis - timedelta(days=1), dzis + timedelta(days=1)))

    # 27. wyciąg – zawyżone wpłaty przez podwójną historię
    def po_wyciag(wynik, blad, t0):
        if blad is not None or not isinstance(wynik, dict):
            return
        if wynik.get("wplaty", Decimal("0")) > Decimal("50") and Decimal("50") < wynik["wplaty"]:
            # po starcie 1000 nie jest wpłatą; wpłata 50 zapisana dwukrotnie => 100
            if wynik["wplaty"] >= Decimal("100"):
                oznacz_awarie_spec(
                    funkcja="wyciag_miesieczny",
                    args=(n1, dzis.year, dzis.month),
                    kwargs={},
                    rodzaj="zle_dane_wyjsciowe",
                    typ_bledu="ZawyżoneWpłaty",
                    komunikat=f"Wyciąg zgłasza wpłaty {wynik['wplaty']} (efekt podwójnej historii)",
                    severity="powazna",
                    usterka_id="F_WPLATA_PODWOJNA_HISTORIA",
                    opis="Ten sam fault w wplac propaguje do wyciągu miesięcznego (zawyżone wpłaty).",
                    t0_wywolania=t0,
                )

    krok("wyciag", bank.wyciag_miesieczny, (n1, dzis.year, dzis.month), po=po_wyciag)

    # 28. przelew zewnętrzny ze stabilnym procesorem (p=0) – to nie jest usterka P1
    proc = ZewnetrznyProcesor(prawdopodobienstwo_awarii=0.0, generator=__import__("random").Random(1))
    krok("przelew zewnetrzny", bank.przelew_zewnetrzny, (n2, "PL61109010140000071219812874", 10, proc))

    # 29. wyplata None
    krok("wyplac None", bank.wyplac, (n1, None))

    return {"liczba_wywolan": licznik_wywolan}


def oznacz_wyjatki_w_logu() -> None:
    """
    Wyjątki domenowe przy złych danych to poprawna obsługa, nie awaria niezawodności.
    Oznaczamy je w raporcie; do MTTF bierzemy tylko awarie specyfikacji + wyjątki nieoczekiwane.
    """
    wpisy = wczytaj_log()
    oczekiwane = {
        "ValueError",
        "TypeError",
        "KontoNieIstnieje",
        "KontoZablokowane",
        "ProcesorNiedostepny",
    }
    # Uzupełniamy wpisy z dekoratora: walidacja vs prawdziwa awaria.
    nowe = []
    for w in wpisy:
        if w.get("zrodlo") == "obserwacja_specyfikacji":
            nowe.append(w)
            continue
        typ = w.get("typ_bledu", "")
        if typ in oczekiwane:
            # To nie jest failure — SUT poprawnie odrzucił złe dane.
            w["awaria_niezawodnosciowa"] = False
            w["severity"] = "n/d"
            w["opis"] = "Wyjątek zgodny ze specyfikacją przy niepoprawnych danych (nie wliczany do MTTF)."
        elif typ == "InvalidOperation" and w.get("funkcja") == "wyplac":
            w["awaria_niezawodnosciowa"] = True
            w["severity"] = "powazna"
            w["usterka_id"] = "F_WYPLATA_BRAK_TYPECHECK"
            w["opis"] = (
                "wyplac nie sprawdza typu kwoty (wplac zgłasza TypeError); "
                "Decimal(str(None)) kończy się InvalidOperation."
            )
        else:
            w["awaria_niezawodnosciowa"] = True
            w["severity"] = "krytyczna"
            w["usterka_id"] = f"F_NIEOCZEKIWANY_{typ}"
            w["opis"] = "Nieoczekiwany wyjątek – potencjalna usterka."
        nowe.append(w)
    # Zapis klasyfikacji z powrotem do awarie.jsonl.
    with LOG_PATH.open("w", encoding="utf-8") as f:
        for w in nowe:
            f.write(json.dumps(w, ensure_ascii=False, default=str) + "\n")


def raport(t0: float, liczba_wywolan: int) -> None:
    wpisy = wczytaj_log()
    awarie = [w for w in wpisy if w.get("awaria_niezawodnosciowa")]
    wyjatki_oczekiwane = [
        w for w in wpisy if w.get("zrodlo") == "dekorator" and not w.get("awaria_niezawodnosciowa")
    ]
    usterki = sorted({w.get("usterka_id", w.get("typ_bledu", "?")) for w in awarie})
    loc = licz_loc(SUT_PATH)
    kloc = loc / 1000 if loc else 0.0
    gestosc = (len(usterki) / kloc) if kloc else None
    mttf = mttf_z_wpisow(awarie, t0)
    mttf_wszystkie_wyjatki = mttf_z_wpisow(
        [w for w in wpisy if w.get("zrodlo") == "dekorator"], t0
    )

    linie = [
        "=" * 72,
        "BASELINE NIEZAWODNOŚCI – Zespół G (P1)",
        "=" * 72,
        f"SUT:                 {SUT_PATH.name}",
        f"LOC (bez pustych/#): {loc}  →  {kloc:.3f} KLOC",
        f"Wywołania SUT:       {liczba_wywolan}",
        f"Wpisy w logu:        {len(wpisy)}  ({LOG_PATH.name})",
        f"Wyjątki domenowe:    {len(wyjatki_oczekiwane)} (poprawna walidacja, nie awarie)",
        f"Awarie (failure):    {len(awarie)}",
        f"Unikalne usterki:    {len(usterki)}",
        f"MTTF (awarie):       {mttf:.4f} s" if mttf is not None else "MTTF (awarie):       n/d (brak awarii)",
        (
            f"MTTF (wszystkie wyjątki z dekoratora, jak w przykładzie z karty): "
            f"{mttf_wszystkie_wyjatki:.4f} s"
            if mttf_wszystkie_wyjatki is not None
            else "MTTF (dekorator):    n/d"
        ),
        f"Gęstość defektów:    {gestosc:.2f} usterek / KLOC" if gestosc is not None else "Gęstość: n/d",
        "",
        "Znalezione usterki (unikalne przyczyny):",
    ]
    for uid in usterki:
        przyklady = [w for w in awarie if w.get("usterka_id") == uid]
        sev = przyklady[0].get("severity", "?") if przyklady else "?"
        opis = przyklady[0].get("opis", "") if przyklady else ""
        linie.append(f"  - [{sev}] {uid}  ({len(przyklady)} aktywacji): {opis}")

    linie.append("=" * 72)
    tekst = "\n".join(linie)
    print(tekst)
    (KATALOG / "raport_P1.txt").write_text(tekst + "\n", encoding="utf-8")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()  # nowa sesja = czysty log
    owin_metody_sut()
    t0 = time.time()
    bank = BankSystem()
    podsumowanie = przeprowadz_eksploracje(bank)
    oznacz_wyjatki_w_logu()
    raport(t0, podsumowanie["liczba_wywolan"])


if __name__ == "__main__":
    main()
