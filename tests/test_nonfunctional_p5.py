"""P5: odtwarzalne pomiary bez zmiany kodu SUT. Uruchom: python test_nonfunctional_p5.py"""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from time import perf_counter
from pathlib import Path
from statistics import median, mean
import hashlib, json, platform, os, sys
from zespol_G import BankSystem

A, B = '1234567895', '9876543215'
WORKERS = 8

def scenario(method, count, workers):
    bank = BankSystem()
    bank.utworz_konto(A, 'Zrodlo', count if method == 'przelew' else 0)
    bank.utworz_konto(B, 'Cel', 0)
    barrier = Barrier(workers) if workers > 1 else None
    def worker(n):
        done = 0; errors = []
        if barrier: barrier.wait(timeout=30)
        for _ in range(n):
            try:
                if method == 'przelew': bank.przelew(A, B, Decimal('1'))
                else: bank.wplac(A, Decimal('1'))
                done += 1
            except Exception as exc:
                errors.append(type(exc).__name__ + ': ' + str(exc))
        return done, errors
    start = perf_counter()
    if workers == 1:
        results = [worker(count)]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(worker, count//workers + (i < count%workers)) for i in range(workers)]
            results = [f.result(timeout=60) for f in futures]
    elapsed = perf_counter() - start
    done = sum(r[0] for r in results)
    errors = [e for r in results for e in r[1]]
    balances = [str(bank.konta[x].saldo) for x in (A,B)]
    expected = ['0',str(count)] if method == 'przelew' else [str(count),'0']
    histories = [len(bank.konta[x].historia) for x in (A,B)]
    expected_histories = [count,count] if method == 'przelew' else [count,0]
    return dict(method=method, count=count, workers=workers, seconds=elapsed,
                throughput=done/elapsed, completed=done, errors=errors,
                balances=balances, expected_balances=expected,
                balance_ok=balances==expected and done==count and not errors,
                history_lengths=histories, history_ok=histories==expected_histories)

def main():
    # Rozgrzewka, poza raportowanymi seriami.
    scenario('wplac',1000,1); scenario('wplac',1000,WORKERS)
    concurrency=[]
    for method in ('przelew','wplac'):
        for repeat in range(1,21):
            row=scenario(method,1000,WORKERS);row['repeat']=repeat;concurrency.append(row)
    load=[]
    # Naprzemienna kolejność zmniejsza wpływ kolejności wariantów.
    for repeat in range(1,6):
        for workers in ((1,WORKERS) if repeat%2 else (WORKERS,1)):
            row=scenario('wplac',10000,workers);row['repeat']=repeat;load.append(row)
    metadata=dict(python=sys.version, platform=platform.platform(),cpu_logical=os.cpu_count(),
                  switch_interval=sys.getswitchinterval(),workers=WORKERS,
                  sut_sha256=hashlib.sha256(Path(__file__).with_name('zespol_G.py').read_bytes()).hexdigest())
    summary={}
    for workers in (1,WORKERS):
        rows=[r for r in load if r['workers']==workers]
        summary[str(workers)]={'median_seconds':median(r['seconds'] for r in rows),
                              'median_throughput':median(r['throughput'] for r in rows),
                              'min_seconds':min(r['seconds'] for r in rows),
                              'max_seconds':max(r['seconds'] for r in rows),
                              'balance_passed':sum(r['balance_ok'] for r in rows)}
    data=dict(metadata=metadata,concurrency=concurrency,load=load,summary=summary)
    Path('wyniki_P5.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    for method in ('przelew','wplac'):
        rows=[r for r in concurrency if r['method']==method]
        print(method, 'saldo:',sum(r['balance_ok'] for r in rows),'/20;',
              'historia:',sum(r['history_ok'] for r in rows),'/20')
    print(json.dumps(summary,indent=2))
    # Kod 1 także dla znanej rozbieżności historii wpłat; pełny pomiar już zapisano.
    return 0 if all(r['balance_ok'] and r['history_ok'] for r in concurrency+load) else 1

if __name__ == '__main__':sys.exit(main())
