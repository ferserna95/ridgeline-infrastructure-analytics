# Data dictionary

All data is synthetic. Monetary values are in USD.

## projects.csv
| Column | Description |
|---|---|
| project_id | Unique ID (P001…P038) |
| name | Project label |
| type | Road resurfacing, Bridge rehabilitation, New bridge, Drainage & culverts, Intersection upgrade |
| state | TX, LA, OK, AR |
| client | State DOT, County, City, Port Authority |
| project_manager | PM-01 … PM-04 |
| contract_value | Contract price |
| budget_at_completion | Cost budget (BAC), 90% of contract value |
| start_date / planned_end / actual_end | Dates (`actual_end` empty if active) |
| status | Completed or Active |
| final_cost | Actual total cost (completed projects only) |
| change_order_total | Sum of change orders to date |

## bid_items.csv
| Column | Description |
|---|---|
| project_id, item, unit | Project, line item and unit of measure |
| bid_qty, bid_unit_price | Quantity and unit price at bid |
| actual_qty, actual_unit_price | Quantity and unit price actually incurred |

## weekly_evm.csv
| Column | Description |
|---|---|
| project_id, week, week_ending | Project and week number since start |
| planned_value (PV) | Cumulative budgeted cost of planned work |
| earned_value (EV) | Cumulative budgeted cost of work performed |
| actual_cost (AC) | Cumulative actual cost |
| rain_days | Rain days that week |

Derived metrics: CPI = EV / AC, SPI = EV / PV, EAC = BAC / CPI.

## change_orders.csv
| Column | Description |
|---|---|
| project_id, co_id, date, amount | Change order identifier, date and value |
| reason | Design change, Differing site condition, Owner request, Utility conflict, Quantity adjustment |

## equipment_telemetry.csv
| Column | Description |
|---|---|
| date, equipment_id, equipment_type | Day, machine and category |
| project_id | Project where it worked (YARD if idle in the yard) |
| engine_hours, idle_hours | Hours running and hours idling |
| fuel_liters | Fuel consumed |
| coolant_temp_max_c | Peak coolant temperature |
| vibration_rms | Vibration level |
| fault_code | Diagnostic code, empty if none |

## equipment_failures.csv
| Column | Description |
|---|---|
| equipment_id, failure_date | Machine and date of breakdown |
| type | Failure type |
| downtime_days | Days out of service |
