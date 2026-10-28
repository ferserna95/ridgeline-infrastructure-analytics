"""
Generador de datos sintéticos para Ridgeline Infrastructure Co. (empresa ficticia).
Produce 38 proyectos viales y de puentes (2020-2026) con patrones ocultos
que un análisis de datos puede descubrir. Todo es ficticio.
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
OUT = Path(__file__).resolve().parent.parent / "data"
OUT.mkdir(exist_ok=True)
CUT = pd.Timestamp("2026-10-19")  # "hoy" para los proyectos activos

# ---------------------------------------------------------------- catálogos
TYPES = {
    #                      valor contrato (USD)  meses    riesgo base
    "Road resurfacing":     ((2e6, 9e6),        (4, 9),   0.04),
    "Bridge rehabilitation": ((5e6, 22e6),      (9, 18),  0.13),
    "New bridge":           ((15e6, 60e6),      (16, 30), 0.18),
    "Drainage & culverts":  ((1.5e6, 7e6),      (4, 10),  0.07),
    "Intersection upgrade": ((3e6, 14e6),       (6, 14),  0.09),
}
# partida: (unidad, precio base 2020 USD, peso por tipo de proyecto)
ITEMS = {
    "Hot mix asphalt":    ("ton", 95,   {"Road resurfacing": .45, "Intersection upgrade": .25}),
    "Concrete Class S":   ("m3",  620,  {"New bridge": .30, "Bridge rehabilitation": .22, "Drainage & culverts": .18, "Intersection upgrade": .12}),
    "Reinforcing steel":  ("kg",  2.1,  {"New bridge": .18, "Bridge rehabilitation": .14, "Drainage & culverts": .08}),
    "Structural steel":   ("kg",  4.8,  {"New bridge": .20, "Bridge rehabilitation": .16}),
    "Excavation":         ("m3",  18,   {"New bridge": .06, "Drainage & culverts": .20, "Intersection upgrade": .08, "Road resurfacing": .05}),
    "Aggregate base":     ("ton", 34,   {"Road resurfacing": .15, "Intersection upgrade": .15, "Drainage & culverts": .10}),
    "Pipe culvert RCP":   ("m",   310,  {"Drainage & culverts": .30}),
    "Traffic control":    ("day", 1800, {t: .08 for t in TYPES}),
    "Guardrail":          ("m",   85,   {"Road resurfacing": .05, "Intersection upgrade": .08, "Bridge rehabilitation": .04}),
    "Pavement markings":  ("m",   3.2,  {"Road resurfacing": .06, "Intersection upgrade": .05}),
}
PRICE_INDEX = {2019: .97, 2020: 1.00, 2021: 1.08, 2022: 1.22, 2023: 1.28, 2024: 1.31, 2025: 1.34, 2026: 1.37}
# Hallazgo oculto #1: acero y asfalto muy subestimados en ofertas 2021-2022
VOLATILE = {"Structural steel": 1.5, "Reinforcing steel": 1.4, "Hot mix asphalt": 1.2}

STATES = {"TX": 1.0, "LA": 1.5, "OK": .8, "AR": 1.1}   # factor de lluvia
CLIENTS = ["State DOT", "County", "City", "Port Authority"]
# Hallazgo oculto #2: PM-04 retrasa más; PM-02 gasta más
PMS = {"PM-01": (0.00, 0.00), "PM-02": (0.05, 0.03), "PM-03": (-0.01, -0.02), "PM-04": (0.09, 0.02)}  # (retraso, costo)


def smooth(x):
    x = np.clip(x, 0, 1)
    return 3 * x**2 - 2 * x**3


# ---------------------------------------------------------------- proyectos
projects, bid_rows, weekly_rows, co_rows = [], [], [], []
type_names = list(TYPES)
type_probs = [.26, .18, .10, .24, .22]

for i in range(1, 39):
    pid = f"P{i:03d}"
    ptype = rng.choice(type_names, p=type_probs)
    (vmin, vmax), (mmin, mmax), risk = TYPES[ptype]
    value = float(rng.uniform(vmin, vmax))
    months = rng.uniform(mmin, mmax)
    planned_weeks = int(round(months * 4.345))
    start = pd.Timestamp("2020-01-06") + pd.Timedelta(days=int(rng.integers(0, 2300)))
    state = rng.choice(list(STATES))
    pm = rng.choice(list(PMS), p=[.3, .25, .3, .15])
    client = rng.choice(CLIENTS, p=[.45, .3, .2, .05])
    bac = value * 0.90  # presupuesto de costo (10% margen)

    # --- partidas de oferta vs. real
    weights = {k: v[2].get(ptype, 0) for k, v in ITEMS.items()}
    tot_w = sum(weights.values())
    bid_total = act_total = 0.0
    bid_year = start.year
    for name, (unit, base, _) in ITEMS.items():
        w = weights[name]
        if w == 0:
            continue
        share = w / tot_w
        bid_idx = PRICE_INDEX[max(bid_year - 1, 2019)]  # se oferta con el índice del año anterior
        bias = rng.normal(0, 0.02)
        if name in VOLATILE and bid_year in (2021, 2022):
            bias -= 0.06 * VOLATILE[name]
        bid_price = base * bid_idx * (1 + bias)
        mid = min((start + pd.Timedelta(weeks=planned_weeks // 2)).year, 2026)
        act_price = base * PRICE_INDEX[mid] * rng.normal(1.0, 0.03)
        if name in VOLATILE and bid_year in (2021, 2022):
            act_price *= 1 + 0.03 * VOLATILE[name]
        qty = bac * share / bid_price
        act_qty = qty * rng.normal(1.02, 0.04)
        bid_total += qty * bid_price
        act_total += act_qty * act_price
        bid_rows.append(dict(project_id=pid, item=name, unit=unit, bid_qty=round(qty, 1),
                             bid_unit_price=round(bid_price, 2), actual_qty=round(act_qty, 1),
                             actual_unit_price=round(act_price, 2)))
    item_ratio = act_total / bid_total

    # --- clima: lluvia semanal estacional
    max_w = int(planned_weeks * 2)
    weeks_idx = np.arange(1, max_w + 1)
    doy = (start + pd.to_timedelta(weeks_idx * 7, unit="D")).dayofyear.values
    lam = STATES[state] * (1.0 + 0.9 * np.sin((doy - 60) / 365 * 2 * np.pi) + 0.4)
    rain = rng.poisson(np.clip(lam, 0.2, None))
    expected = np.clip(lam, 0.2, None)[:planned_weeks].sum()
    excess_rain = max(rain[:planned_weeks].sum() - expected, 0)

    # --- órdenes de cambio
    n_co = rng.poisson(risk * 28 * (1 + PMS[pm][1] * 4))
    co_total = 0.0
    for k in range(n_co):
        d = start + pd.Timedelta(days=int(rng.integers(14, planned_weeks * 7)))
        if d > CUT:
            continue
        amt = float(bac * rng.gamma(2.0, 0.006))
        co_total += amt
        co_rows.append(dict(project_id=pid, co_id=f"{pid}-CO{k+1:02d}", date=d.date(), amount=round(amt, 2),
                            reason=rng.choice(["Design change", "Differing site condition", "Owner request", "Utility conflict", "Quantity adjustment"],
                                              p=[.25, .3, .2, .15, .1])))
    co_pct = co_total / bac

    # --- sobrecosto y retraso finales
    over = item_ratio * (1 + 0.7 * co_pct) * (1 + PMS[pm][1]) * rng.normal(1.0, 0.02)
    over = float(np.clip(over, 0.95, 1.65))
    delay = 1 + risk * rng.normal(1.0, 0.45) + 0.0045 * excess_rain + PMS[pm][0] + 0.8 * co_pct
    delay = float(np.clip(delay, 0.97, 1.8))
    n_actual = int(round(planned_weeks * delay))

    # --- serie semanal EVM
    pct_prev = 0.0
    last_w = 0
    for w in range(1, n_actual + 1):
        d = start + pd.Timedelta(weeks=w)
        if d > CUT:
            break
        pv = bac * smooth(w / planned_weeks)
        pct = smooth(w / n_actual) * (1 + rng.normal(0, 0.006))
        pct = float(np.clip(max(pct, pct_prev), 0, 1))
        pct_prev = pct
        ev = bac * pct
        ac = ev * (1 + (over - 1) * pct**0.8) * (1 + rng.normal(0, 0.012))
        weekly_rows.append(dict(project_id=pid, week=w, week_ending=d.date(), planned_value=round(pv, 2),
                                earned_value=round(ev, 2), actual_cost=round(ac, 2),
                                rain_days=int(rain[w - 1])))
        last_w = w
    completed = last_w == n_actual
    end = start + pd.Timedelta(weeks=n_actual)
    projects.append(dict(project_id=pid, name=f"{ptype} #{i}", type=ptype, state=state, client=client,
                         project_manager=pm, contract_value=round(value, 2), budget_at_completion=round(bac, 2),
                         start_date=start.date(), planned_end=(start + pd.Timedelta(weeks=planned_weeks)).date(),
                         actual_end=end.date() if completed else None,
                         status="Completed" if completed else "Active",
                         final_cost=round(bac * over, 2) if completed else None,
                         change_order_total=round(co_total, 2)))

proj = pd.DataFrame(projects)
weekly = pd.DataFrame(weekly_rows)
bids = pd.DataFrame(bid_rows)
cos = pd.DataFrame(co_rows)

# ---------------------------------------------------------------- telemetría de equipos
# Hallazgo oculto #3: 3 equipos con ralentí excesivo; 5 fallas precedidas por 3 semanas de degradación
FLEET = []
for kind, n in [("Excavator", 5), ("Dozer", 3), ("Paver", 3), ("Roller", 4), ("Crane", 3), ("Dump truck", 6)]:
    for j in range(n):
        FLEET.append((f"{kind[:3].upper()}-{j+1:02d}", kind))
dates = pd.date_range("2025-01-01", CUT, freq="D")
high_idle = {"EXC-02", "DOZ-01", "DUM-04"}
failing = {"EXC-03": "2025-09-12", "PAV-02": "2026-01-20", "CRA-01": "2026-04-08",
           "DUM-02": "2026-07-15", "ROL-03": "2026-09-02"}
tele_rows, fail_rows = [], []
active_by_date = proj.assign(s=pd.to_datetime(proj.start_date),
                             e=pd.to_datetime(proj.actual_end).fillna(CUT))
for eid, kind in FLEET:
    fail_day = pd.Timestamp(failing[eid]) if eid in failing else None
    base_fuel = {"Excavator": 18, "Dozer": 22, "Paver": 25, "Roller": 11, "Crane": 14, "Dump truck": 16}[kind]
    if fail_day is not None:
        fail_rows.append(dict(equipment_id=eid, failure_date=fail_day.date(), type="Unplanned breakdown",
                              downtime_days=int(rng.integers(5, 21))))
    for d in dates:
        if d.dayofweek == 6:
            continue
        act = active_by_date[(active_by_date.s <= d) & (active_by_date.e >= d)]
        pid = rng.choice(act.project_id) if len(act) else "YARD"
        if fail_day is not None and fail_day <= d < fail_day + pd.Timedelta(days=7):
            continue
        hrs = float(np.clip(rng.normal(7.2, 1.2), 0, 11)) if pid != "YARD" else 0.0
        idle_share = rng.normal(0.52 if eid in high_idle else 0.22, 0.05)
        idle = hrs * float(np.clip(idle_share, 0.05, 0.8))
        ramp = 0.0
        if fail_day is not None:
            days_to = (fail_day - d).days
            if 0 < days_to <= 21:
                ramp = (21 - days_to) / 21
        fuel = (hrs - idle) * base_fuel * rng.normal(1, 0.05) + idle * base_fuel * 0.35
        fuel *= 1 + 0.18 * ramp
        tele_rows.append(dict(date=d.date(), equipment_id=eid, equipment_type=kind, project_id=pid,
                              engine_hours=round(hrs, 2), idle_hours=round(idle, 2), fuel_liters=round(fuel, 1),
                              coolant_temp_max_c=round(rng.normal(88, 2) + 9 * ramp, 1),
                              vibration_rms=round(abs(rng.normal(2.1, 0.25)) * (1 + 0.9 * ramp), 3),
                              fault_code="E-" + str(int(rng.integers(100, 999))) if rng.random() < 0.02 + 0.25 * ramp else None))
tele = pd.DataFrame(tele_rows)
fails = pd.DataFrame(fail_rows)

# ---------------------------------------------------------------- guardar
proj.to_csv(OUT / "projects.csv", index=False)
bids.to_csv(OUT / "bid_items.csv", index=False)
weekly.to_csv(OUT / "weekly_evm.csv", index=False)
cos.to_csv(OUT / "change_orders.csv", index=False)
tele.to_csv(OUT / "equipment_telemetry.csv", index=False)
fails.to_csv(OUT / "equipment_failures.csv", index=False)
print({f: len(d) for f, d in [("projects", proj), ("bid_items", bids), ("weekly_evm", weekly),
                              ("change_orders", cos), ("telemetry", tele), ("failures", fails)]})
