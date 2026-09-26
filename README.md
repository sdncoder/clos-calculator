# Clos Spine-Leaf Calculator

Terminal tool for sizing a leaf-spine Clos fabric: given leaf count, server ports per leaf,
and port speeds, it reports the oversubscription ratio for a given spine count and sweeps
a set of target ratios to show how many spines each one requires.

No external dependencies -- stdlib only.

## Usage

Interactive (no flags -- prompts for each value):

```
python3 clos_calculator.py
```

Scripted:

```
python3 clos_calculator.py \
  --leaves 32 --spines 4 \
  --server-ports 48 --downlink-speed 25 --uplink-speed 100 \
  --spine-ports 32 \
  --leaf-cost 15000 --spine-cost 25000 --optic-cost 300 \
  --ratios 1,2,3,4 \
  --csv sweep.csv
```

Any flag you omit on the command line is prompted for interactively, so partial flags + prompts also works.

## What it computes

- **Achieved oversubscription** for the spine count you entered: `(server_ports * downlink_speed) / (spines * uplink_speed)`
- **Sweep table** across target ratios (default 1:1, 2:1, 3:1, 4:1): spines needed for each, whether the
  resulting leaf count fits within a single spine's port radix, total transceiver count, and estimated cost
  (if `--leaf-cost` / `--spine-cost` / `--optic-cost` are supplied)
- **Warnings**: leaf count exceeding spine port radix (needs higher-radix spines or a super-spine tier),
  and fewer than 3 spines (no maintenance window without an outage)

## Assumptions

- One physical link per leaf-to-spine pair (no parallel uplinks to the same spine)
- Transceiver count on spine-leaf links counts both ends; leaf-server transceiver count is leaf-side only
- Single spine tier / single plane -- does not model super-spine or multi-plane fabrics
- Cost estimate is switches + optics only (no cabling, power, rack, or licensing)
