#!/usr/bin/env python3
"""Clos spine-leaf fabric sizing calculator."""

import argparse
import csv
import math
import sys

DEFAULT_RATIOS = [1.0, 2.0, 3.0, 4.0]


def parse_args():
    parser = argparse.ArgumentParser(description="Clos spine-leaf fabric sizing calculator")
    parser.add_argument("--spines", type=int, help="Number of spine switches to evaluate")
    parser.add_argument("--leaves", type=int, help="Number of leaf switches")
    parser.add_argument("--server-ports", type=int, help="Server-facing (downlink) ports per leaf")
    parser.add_argument("--downlink-speed", type=float, help="Downlink port speed in Gbps")
    parser.add_argument("--uplink-speed", type=float, help="Uplink (leaf-to-spine) port speed in Gbps")
    parser.add_argument("--spine-ports", type=int, help="Ports available per spine switch")
    parser.add_argument("--ratios", type=str, help="Comma-separated oversubscription ratios to sweep, e.g. 1,2,3,4")
    parser.add_argument("--leaf-cost", type=float, default=0.0, help="Cost per leaf switch (USD)")
    parser.add_argument("--spine-cost", type=float, default=0.0, help="Cost per spine switch (USD)")
    parser.add_argument("--optic-cost", type=float, default=0.0, help="Cost per transceiver (USD)")
    parser.add_argument("--csv", type=str, help="Path to write the scenario sweep table as CSV")
    return parser.parse_args()


def prompt_value(msg, cast, default=None):
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{msg}{suffix}: ").strip()
        if not raw and default is not None:
            return default
        try:
            return cast(raw)
        except ValueError:
            print(f"  enter a valid {cast.__name__}")


def gather_inputs(args):
    if args.leaves is None:
        args.leaves = prompt_value("Number of leaf switches", int)
    if args.spines is None:
        args.spines = prompt_value("Number of spine switches to evaluate", int)
    if args.server_ports is None:
        args.server_ports = prompt_value("Server-facing (downlink) ports per leaf", int)
    if args.downlink_speed is None:
        args.downlink_speed = prompt_value("Downlink port speed (Gbps)", float, 25.0)
    if args.uplink_speed is None:
        args.uplink_speed = prompt_value("Uplink port speed, leaf-to-spine (Gbps)", float, 100.0)
    if args.spine_ports is None:
        args.spine_ports = prompt_value("Ports available per spine switch", int, 32)
    if args.ratios is None:
        raw = input(f"Oversubscription ratios to sweep, comma-separated [{','.join(str(r) for r in DEFAULT_RATIOS)}]: ").strip()
        args.ratios = raw if raw else None
    return args


def parse_ratios(ratios_str):
    if not ratios_str:
        return DEFAULT_RATIOS
    return [float(r) for r in ratios_str.split(",") if r.strip()]


def leaf_downlink_bandwidth(server_ports, downlink_speed):
    return server_ports * downlink_speed


def leaf_uplink_bandwidth(num_spines, uplink_speed):
    return num_spines * uplink_speed


def oversubscription(downlink_bw, uplink_bw):
    if uplink_bw == 0:
        return float("inf")
    return downlink_bw / uplink_bw


def spines_for_ratio(server_ports, downlink_speed, uplink_speed, ratio):
    downlink_bw = leaf_downlink_bandwidth(server_ports, downlink_speed)
    return max(1, math.ceil(downlink_bw / (ratio * uplink_speed)))


def scenario_row(num_spines, num_leaves, server_ports, downlink_speed, uplink_speed,
                  spine_ports, leaf_cost, spine_cost, optic_cost):
    downlink_bw = leaf_downlink_bandwidth(server_ports, downlink_speed)
    uplink_bw = leaf_uplink_bandwidth(num_spines, uplink_speed)
    ratio = oversubscription(downlink_bw, uplink_bw)

    spine_leaf_links = num_leaves * num_spines
    spine_leaf_optics = 2 * spine_leaf_links  # both ends of each uplink
    leaf_server_optics = num_leaves * server_ports  # leaf-side only

    total_optics = spine_leaf_optics + leaf_server_optics
    total_fabric_bw = num_leaves * uplink_bw

    cost = (num_leaves * leaf_cost) + (num_spines * spine_cost) + (total_optics * optic_cost)

    fits_spine_radix = num_leaves <= spine_ports

    return {
        "spines": num_spines,
        "achieved_ratio": ratio,
        "uplink_ports_per_leaf": num_spines,
        "spine_ports_used": num_leaves,
        "fits_spine_radix": fits_spine_radix,
        "spine_leaf_optics": spine_leaf_optics,
        "leaf_server_optics": leaf_server_optics,
        "total_optics": total_optics,
        "total_fabric_bw_gbps": total_fabric_bw,
        "estimated_cost": cost,
    }


def print_scenario(label, row):
    print(f"\n=== {label} ===")
    print(f"  Spines:                  {row['spines']}")
    print(f"  Achieved oversubscription: {row['achieved_ratio']:.2f}:1")
    print(f"  Uplink ports per leaf:   {row['uplink_ports_per_leaf']}")
    print(f"  Spine ports used:        {row['spine_ports_used']}")
    if not row["fits_spine_radix"]:
        print("  WARNING: leaf count exceeds spine port radix -- needs higher-radix spines or a super-spine tier")
    if row["spines"] < 3:
        print("  NOTE: fewer than 3 spines means no maintenance window without a full outage risk")
    print(f"  Spine-leaf optics (both ends): {row['spine_leaf_optics']}")
    print(f"  Leaf-server optics (leaf side): {row['leaf_server_optics']}")
    print(f"  Total optics:            {row['total_optics']}")
    print(f"  Total fabric bandwidth:  {row['total_fabric_bw_gbps']:.0f} Gbps")
    if row["estimated_cost"]:
        print(f"  Estimated cost:          ${row['estimated_cost']:,.2f}")


def print_sweep_table(rows):
    headers = ["target_ratio", "spines_needed", "achieved_ratio", "fits_radix", "total_optics", "estimated_cost"]
    widths = [15, 16, 17, 13, 15, 16]
    print("\n=== Oversubscription sweep ===")
    print("".join(h.ljust(w) for h, w in zip(headers, widths)))
    for row in rows:
        cells = [
            f"{row['target_ratio']:.1f}:1",
            str(row["spines"]),
            f"{row['achieved_ratio']:.2f}:1",
            "yes" if row["fits_spine_radix"] else "NO",
            str(row["total_optics"]),
            f"${row['estimated_cost']:,.2f}" if row["estimated_cost"] else "-",
        ]
        print("".join(c.ljust(w) for c, w in zip(cells, widths)))


def write_csv(path, rows):
    fieldnames = ["target_ratio", "spines", "achieved_ratio", "uplink_ports_per_leaf",
                  "spine_ports_used", "fits_spine_radix", "spine_leaf_optics",
                  "leaf_server_optics", "total_optics", "total_fabric_bw_gbps", "estimated_cost"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fieldnames})
    print(f"\nWrote sweep table to {path}")


def main():
    args = parse_args()
    if len(sys.argv) == 1:
        args = gather_inputs(args)
    else:
        missing = [f for f in ("leaves", "spines", "server_ports", "downlink_speed", "uplink_speed", "spine_ports")
                   if getattr(args, f) is None]
        if missing:
            args = gather_inputs(args)

    ratios = parse_ratios(args.ratios)

    entered = scenario_row(args.spines, args.leaves, args.server_ports, args.downlink_speed,
                            args.uplink_speed, args.spine_ports, args.leaf_cost, args.spine_cost,
                            args.optic_cost)
    print_scenario(f"Entered configuration ({args.spines} spines)", entered)

    sweep_rows = []
    for ratio in ratios:
        needed_spines = spines_for_ratio(args.server_ports, args.downlink_speed, args.uplink_speed, ratio)
        row = scenario_row(needed_spines, args.leaves, args.server_ports, args.downlink_speed,
                            args.uplink_speed, args.spine_ports, args.leaf_cost, args.spine_cost,
                            args.optic_cost)
        row["target_ratio"] = ratio
        sweep_rows.append(row)

    print_sweep_table(sweep_rows)

    if args.csv:
        write_csv(args.csv, sweep_rows)


if __name__ == "__main__":
    main()
