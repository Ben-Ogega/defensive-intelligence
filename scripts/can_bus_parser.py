"""
CAN is the language the car will speak,
Bus is the highway where the packets fly,
Parser translates as the bits go by,
This script is the tool for the data you seek.

CAN FD arrives as the next generation,
With payloads larger and speeds more intense,
Following principles that still make sense,
The script handles both with ease and rotation.

J1939 serves the heavy-duty frame,
With rules and messages built for the fleet,
Parsing the data to make it complete,
A versatile tool for the analysis game.

The PGN identifies the message in line,
Signals (SGN) are the values inside,
Precision ensures that no data can hide,
An asset for engineers by design.

The building blocks are the bits and the bytes,
Shifting and masking extract what is concealed,
Until the true info is finally revealed,
A powerful tool for these analytical heights.
"""

# J1939 PGN — Parameter Group Number
# 18-bit identifier within a 29-bit CAN ID
# Labels a group of related signals broadcast
# on the CAN Bus every 100ms
# PGN 65265 — Vehicle Speed + Brake signals
# This is the source of Safari-Safe-AI sensor vector

# -*- coding: utf-8 -*-

import struct
import json
import os
from datetime import datetime

# ============================================
# Safari-Safe-AI | J1939 CAN Bus Parser
# Author: Ben Ogega | BRIDGE Framework
# Phase 1 — CAN Bus signal extraction
# ============================================

# J1939 PGN — Parameter Group Number
# 18-bit identifier within a 29-bit CAN ID
# Labels a group of related signals broadcast
# on the CAN Bus every 100ms
# PGN 65265 — Vehicle Speed + Brake signals
# This is the source of Safari-Safe-AI sensor vector

# ============================================
# PGN DEFINITIONS
# Our sensor vector lives here:
# [speed, acceleration, brake_pressure, steering_angle]
# ============================================

PGN_DEFINITIONS = {
    65265: {
        "name": "Cruise Control/Vehicle Speed",
        "signals": {
            "wheel_speed": {
                "start_byte": 1,
                "length_bytes": 2,
                "scale": 0.00390625,
                "offset": 0,
                "unit": "km/h",
                "sensor_vector": "speed"
            },
            "brake_switch": {
                "start_byte": 0,
                "length_bytes": 1,
                "scale": 1,
                "offset": 0,
                "unit": "binary",
                "sensor_vector": "brake_pressure"
            }
        }
    },
    61441: {
        "name": "Electronic Brake Controller",
        "signals": {
            "brake_demand": {
                "start_byte": 0,
                "length_bytes": 1,
                "scale": 0.4,
                "offset": 0,
                "unit": "percent",
                "sensor_vector": "brake_pressure"
            }
        }
    },
    61449: {
        "name": "Vehicle Dynamic Stability Control",
        "signals": {
            "steering_angle": {
                "start_byte": 0,
                "length_bytes": 2,
                "scale": 0.0078125,
                "offset": -250,
                "unit": "degrees",
                "sensor_vector": "steering_angle"
            }
        }
    }
}

# ============================================
# CAN BUS PARSER CLASS

# ============================================
# STEP 1 — Decode a single CAN message
# ============================================

def decode_message(pgn, data_bytes):
    """
    Decodes a J1939 CAN message into engineering units.
    
    pgn        — Parameter Group Number (int)
    data_bytes — 8 bytes of raw CAN data (bytes or list)
    
    Returns dictionary of decoded signals.
    """
    # Check if we know this PGN
    if pgn not in PGN_DEFINITIONS:
        return {"error": f"PGN {pgn} not defined"}

    pgn_def = PGN_DEFINITIONS[pgn]
    decoded = {
        "pgn": pgn,
        "name": pgn_def["name"],
        "signals": {}
    }

    # Extract each signal
    for signal_name, signal_def in pgn_def["signals"].items():

        start = signal_def["start_byte"]
        length = signal_def["length_bytes"]

        # Combine bytes — little endian (LSB first)
        if length == 1:
            raw_value = data_bytes[start]
        elif length == 2:
            raw_value = (data_bytes[start + 1] << 8) | data_bytes[start]
        else:
            raw_value = 0

        # Apply scale and offset
        # Same as sensor calibration — y = mx + c
        engineering_value = (raw_value * signal_def["scale"]) + signal_def["offset"]

        decoded["signals"][signal_name] = {
            "raw": raw_value,
            "value": round(engineering_value, 3),
            "unit": signal_def["unit"],
            "sensor_vector": signal_def["sensor_vector"]
        }

    return decoded


# ============================================
# STEP 2 — Generate synthetic CAN Bus data
# Simulates Nairobi road driving scenarios
# ============================================

def generate_synthetic_messages():
    """
    Generates synthetic J1939 messages representing
    real Nairobi driving scenarios.
    
    Returns list of (timestamp, pgn, data_bytes) tuples.
    """
    messages = []

    # Scenario 1 — Normal highway driving (Thika Road)
    # Speed ~90 km/h, no braking, straight steering
    messages.append((
        "2026-04-23 08:00:00.000",
        65265,
        [0x00, 0x00, 0x40, 0x23, 0x00, 0xFF, 0xFF, 0xFF]
    ))

    # Scenario 2 — Normal city driving (Moi Avenue)
    # Speed ~40 km/h, light braking, slight steering
    messages.append((
        "2026-04-23 08:00:00.100",
        65265,
        [0x00, 0x80, 0x1A, 0x10, 0x00, 0xFF, 0xFF, 0xFF]
    ))

    # Scenario 3 — Harsh braking (Mlolongo)
    # Speed drops, heavy brake demand
    messages.append((
        "2026-04-23 08:00:00.200",
        61441,
        [0xC8, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    ))

    # Scenario 4 — Panic swerve (Waiyaki Way)
    # Sharp steering angle
    messages.append((
        "2026-04-23 08:00:00.300",
        61449,
        [0x00, 0x50, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    ))

    # Scenario 5 — Fatigue drift (Mombasa Road)
    # Slow steering drift, no braking
    messages.append((
        "2026-04-23 08:00:00.400",
        61449,
        [0x00, 0x18, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    ))

    return messages


# ============================================
# STEP 3 — Process all messages and build
# Safari-Safe-AI sensor vector
# ============================================

def process_messages(messages):
    """
    Processes a list of CAN messages and builds
    the Safari-Safe-AI sensor vector for each event.
    
    Returns list of decoded sensor readings.
    """
    results = []

    for timestamp, pgn, data_bytes in messages:
        decoded = decode_message(pgn, data_bytes)

        print(f"\n{'='*55}")
        print(f"Timestamp: {timestamp}")
        print(f"PGN:       {pgn} — {decoded.get('name', 'Unknown')}")
        print(f"{'-'*55}")

        for signal_name, signal_data in decoded.get("signals", {}).items():
            print(f"  {signal_name:<20} "
                  f"{signal_data['value']:>10} "
                  f"{signal_data['unit']:<12} "
                  f"[{signal_data['sensor_vector']}]")

        results.append({
            "timestamp": timestamp,
            "pgn": pgn,
            "decoded": decoded
        })

    return results


def save_results(results, output_path):
    """
    Saves decoded CAN messages to JSON.
    This becomes your Safari-Safe-AI training data.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)

    print(f"\nResults saved to: {output_path}")


# ============================================
# MAIN — Entry point
# ============================================

if __name__ == "__main__":

    print("\n" + "="*55)
    print("   Safari-Safe-AI | J1939 CAN Bus Parser")
    print("   Nairobi Road Scenarios | Ben Ogega")
    print("   BRIDGE Framework | Phase 1")
    print("="*55)

    # Generate synthetic Nairobi driving data
    messages = generate_synthetic_messages()
    print(f"\nProcessing {len(messages)} CAN messages...")

    # Decode all messages
    results = process_messages(messages)

    # Save to processed data folder
    BASE_DIR = os.path.dirname(
                   os.path.dirname(
                       os.path.abspath(__file__)
                   )
               )
    output_path = os.path.join(
                      BASE_DIR,
                      'data', 'processed',
                      'can_bus_decoded.json'
                  )
    save_results(results, output_path)

    print("\n" + "="*55)
    print("   Sensor vector extraction complete.")
    print("   Data ready for Safari-Safe-AI pipeline.")
    print("="*55)

