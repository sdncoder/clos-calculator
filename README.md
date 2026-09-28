# Clos Spine-Leaf Visualizer

Interactive, single-file tool for sizing a leaf-spine Clos fabric. Set your leaf-facing host
profile and target oversubscription, and it draws the resulting spine-leaf topology live,
alongside the same sizing and cost math as before.

No build step, no server, no external dependencies -- just open `index.html` in a browser.

## Usage

```
open index.html
```

or double-click the file in Finder.

## Inputs

- **End devices per leaf switch** -- number of hosts/servers hanging off each leaf
- **NIC speed per device (Gbps)** -- downlink port speed to each end device
- **Target oversubscription (X:1)** -- the downlink:uplink bandwidth ratio the fabric should not exceed
- **Fabric topology** -- uplink (leaf-to-spine) speed, number of leaf switches, and ports per spine
  switch (radix), used to draw the topology and check feasibility
- **Cost estimate** (optional) -- per-switch and per-transceiver costs

## What it shows

- A live spine-leaf diagram: spines on top, leaves on bottom, full mesh between them, with each
  leaf's end-device count and NIC speed labeled underneath. Large fabrics are abbreviated
  (first/last few switches with `...`) to stay legible -- the full mesh still applies underneath.
- **Spines needed** for your target ratio, and the **achieved ratio** with that spine count
- Warnings for leaf count exceeding spine port radix (needs higher-radix spines or a super-spine
  tier), and fewer than 3 spines (no maintenance window without an outage)
- Total transceiver count, total fabric bandwidth, and estimated cost (if switch/optic costs are set)
- A sweep table showing spines needed across a range of target ratios (1:1 through 6:1) for the
  same topology

## Assumptions

- One physical link per leaf-to-spine pair (no parallel uplinks to the same spine)
- Transceiver count on spine-leaf links counts both ends; leaf-server transceiver count is leaf-side only
- Single spine tier / single plane -- does not model super-spine or multi-plane fabrics
- Cost estimate is switches + optics only (no cabling, power, rack, or licensing)
