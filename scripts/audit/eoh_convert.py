"""Convert the EoH (UKDS SN 9050) 2-min cleansed property files to 30-min parquet.

Reads each ``clean/Property_ID=EOH*.csv`` straight from the four zips in ``data/``
(nothing is extracted; the zips are opened read-only) and writes

- ``data/_paperb/pools_raw/eoh/eoh_30min_set{k}.parquet``: property, ts (bin start),
  mean power per 30 min in kW for every cumulative energy channel (from 2-min diffs),
  the number of valid 2-min diffs behind it (``n_<chan>``, max 15), and the 30-min
  mean of every temperature channel;
- ``data/_paperb/pools_raw/eoh/eoh_sites.parquet``: one row per property with the
  channels present, first/last timestamp, duplicate and negative-diff counts, the
  99.9th percentile of the whole-system power at 15 and 30 min, and the share of
  whole-system energy used by the immersion and back-up heaters.

Cumulative counters: a 2-min diff < 0 or above ``MAX_KW`` (kW) is treated as missing
(counter reset or spike); diffs spanning more than one 2-min step are dropped.
Usage: python scripts/audit/eoh_convert.py [--limit N]
"""
import argparse
import glob
import os
import time
import zipfile

import numpy as np
import pandas as pd

ZIPS = sorted(glob.glob('data/9050csv_cleansed_data_set*.zip'))
OUT = 'data/_paperb/pools_raw/eoh'
ENERGY = ['Whole_System_Energy_Consumed', 'Heat_Pump_Energy_Output', 'Immersion_Heater_Energy_Consumed',
          'Back-up_Heater_Energy_Consumed', 'Circulation_Pump_Energy_Consumed', 'Boiler_Energy_Output']
TEMPS = ['External_Air_Temperature', 'Internal_Air_Temperature', 'Heat_Pump_Heating_Flow_Temperature',
         'Heat_Pump_Return_Temperature', 'Hot_Water_Flow_Temperature', 'Brine_Flow_Temperature',
         'Brine_Return_Temperature']
MAX_KW = {'Whole_System_Energy_Consumed': 30.0, 'Heat_Pump_Energy_Output': 60.0,
          'Immersion_Heater_Energy_Consumed': 15.0, 'Back-up_Heater_Energy_Consumed': 15.0,
          'Circulation_Pump_Energy_Consumed': 5.0, 'Boiler_Energy_Output': 60.0}
SHORT = {'Whole_System_Energy_Consumed': 'P_ws', 'Heat_Pump_Energy_Output': 'Q_hp',
         'Immersion_Heater_Energy_Consumed': 'P_ih', 'Back-up_Heater_Energy_Consumed': 'P_buh',
         'Circulation_Pump_Energy_Consumed': 'P_cp', 'Boiler_Energy_Output': 'Q_boiler',
         'External_Air_Temperature': 'T_ext', 'Internal_Air_Temperature': 'T_int',
         'Heat_Pump_Heating_Flow_Temperature': 'T_flow_sh', 'Heat_Pump_Return_Temperature': 'T_ret',
         'Hot_Water_Flow_Temperature': 'T_flow_dhw', 'Brine_Flow_Temperature': 'T_brine_f',
         'Brine_Return_Temperature': 'T_brine_r'}


def convert_one(d):
    """2-min frame -> (30-min frame, site stats)."""
    t = pd.to_datetime(d['Timestamp'])
    d = d.assign(Timestamp=t).sort_values('Timestamp')
    n_dup = int(d['Timestamp'].duplicated().sum())
    d = d.drop_duplicates('Timestamp').set_index('Timestamp')
    step_ok = d.index.to_series().diff().dt.total_seconds().eq(120).to_numpy()
    out, st = {}, dict(n_rows=len(d), n_dup=n_dup, start=d.index.min(), end=d.index.max())
    p15 = None
    for c in ENERGY:
        if c not in d:
            continue
        dx = d[c].diff().to_numpy()
        bad = (dx < 0) | (dx * 30 > MAX_KW[c])
        st[f'neg_{SHORT[c]}'] = int(np.nansum(dx < 0))
        dx = np.where(step_ok & ~bad, dx, np.nan)
        s = pd.Series(dx, index=d.index - pd.Timedelta(minutes=2))      # diff belongs to the previous slot
        g = s.resample('30min')
        out[SHORT[c]] = (g.sum(min_count=1) * 2.0).astype('float32')    # kWh per 30 min -> kW
        out['n_' + SHORT[c]] = g.count().astype('int8')
        st[f'E_{SHORT[c]}_kWh'] = float(np.nansum(dx))
        if c == 'Whole_System_Energy_Consumed':
            g15 = s.resample('15min')
            p15 = (g15.sum(min_count=1) * 4.0).where(g15.count() >= 6)
    for c in TEMPS:
        if c in d:
            out[SHORT[c]] = d[c].resample('30min').mean().astype('float32')
    H = pd.DataFrame(out)
    if 'P_ws' in H:
        full = H['P_ws'].where(H['n_P_ws'] >= 12)
        st['peak30_ws_kW'] = float(full.quantile(0.999)) if full.notna().any() else np.nan
        st['peak15_ws_kW'] = float(p15.quantile(0.999)) if p15 is not None and p15.notna().any() else np.nan
    st['channels'] = ';'.join(SHORT[c] for c in ENERGY + TEMPS if c in d)
    return H, st


def main(limit=None):
    os.makedirs(OUT, exist_ok=True)
    sites, t0 = [], time.time()
    for k, zp in enumerate(ZIPS, start=1):
        frames = []
        with zipfile.ZipFile(zp) as z:
            names = sorted(n for n in z.namelist() if n.startswith('clean/Property_ID='))
            for i, n in enumerate(names[:limit]):
                pid = n.split('=')[1].split('.')[0]
                if z.getinfo(n).file_size < 100:                      # empty file (listed, not converted)
                    sites.append(dict(property=pid, zip_set=k, n_rows=0, channels='EMPTY FILE'))
                    continue
                H, st = convert_one(pd.read_csv(z.open(n)))
                H.insert(0, 'property', pid)
                frames.append(H.reset_index().rename(columns={'Timestamp': 'ts'}))
                sites.append(dict(property=pid, zip_set=k, **st))
                if (i + 1) % 25 == 0:
                    print(f'set {k}: {i + 1}/{len(names)} ({time.time() - t0:.0f} s)', flush=True)
        F = pd.concat(frames, ignore_index=True)
        F['property'] = F['property'].astype('category')
        F.to_parquet(f'{OUT}/eoh_30min_set{k}.parquet', index=False)
        print(f'wrote set {k}: {F.property.nunique()} properties, {len(F):,} rows', flush=True)
    S = pd.DataFrame(sites)
    S.to_parquet(f'{OUT}/eoh_sites.parquet', index=False)
    print(f'wrote {len(S)} sites in {time.time() - t0:.0f} s', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=None, help='properties per zip (smoke test)')
    main(ap.parse_args().limit)
