# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from collections import defaultdict
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from anomaly_flags import (
        flag_overspeed,
        flag_harsh_braking,
        flag_distraction,
        flag_aggressive_cornering,
        flag_grip_violation,
        flag_lateral_force,
        flag_friction_circle,
        SEVERITY_SCORE
    )
except ImportError:
    # Defensive fallback for severity scores if not found in anomaly_flags
    SEVERITY_SCORE = {'NONE': 0, 'WARNING': 1, 'DANGER': 2, 'CRITICAL': 3}
# ============================================
# Safari-Safe-AI | Unified Safety Report
# Author: Ben Ogega | BRIDGE Framework
# Phase 2 — Fleet anomaly reporting system
# ============================================

"""
This module answers three questions for fleet managers:
1. Which vehicle has the most anomalies?
2. Which road has the most dangerous events?
3. Which anomaly type is most frequent?
"""

# Severity scoring — for ranking and aggregation
SEVERITY_SCORE = {
    'NONE':     0,
    'WARNING':  1,
    'DANGER':   2,
    'CRITICAL': 3,
}

# ============================================
# LAYER 1 — SINGLE EVENT REPORT
# One function. One job.
# Runs all 7 flags on one driving event.
# ============================================

def generate_safety_report(event):
    """
    Runs all 7 safety flags on a single driving event.

    event — dictionary containing all sensor readings
            for one moment in time.

    Returns a complete safety report for that event.
    """
    reports = []

    # Flag 1 — Overspeed
    reports.append(flag_overspeed(
        event['speed_kmh'],
        event.get('zone', 'highway')
    ))

    # Flag 2 — Harsh Braking
    reports.append(flag_harsh_braking(
        event['speed_prev_kmh'],
        event['speed_kmh'],
        event['brake_pressure'],
        event.get('time_delta_s', 1.0)
    ))

    # Flag 3 — Distraction
    reports.append(flag_distraction(
        event['steering_seq']
    ))

    # Flag 4 — Aggressive Cornering
    reports.append(flag_aggressive_cornering(
        event['speed_kmh'],
        event.get('turn_radius_m', 100.0)
    ))

    # Flag 5 — Grip Violation
    reports.append(flag_grip_violation(
        event.get('lat_accel_ms2', 0.0),
        event.get('long_accel_ms2', 0.0)
    ))

    # Flag 6 — Lateral Force
    reports.append(flag_lateral_force(
        event['speed_kmh'],
        event['steering_angle'],
        event.get('vehicle_model', 'TOYOTA_HIACE')
    ))

    # Flag 7 — Friction Circle
    reports.append(flag_friction_circle(
        event['speed_kmh'],
        event['steering_angle'],
        event.get('long_accel_ms2', 0.0),
        event.get('vehicle_model', 'TOYOTA_HIACE')
    ))

    # Collect only triggered flags
    triggered = [r for r in reports if r['flag']]

    # Calculate overall severity — worst flag wins
    max_severity = 'NONE'
    for r in triggered:
        if SEVERITY_SCORE[r['severity']] > SEVERITY_SCORE[max_severity]:
            max_severity = r['severity']

    return {
        'vehicle_id':    event['vehicle_id'],
        'timestamp':     event['timestamp'],
        'location':      event['location'],
        'overall_severity': max_severity,
        'flags_triggered':  len(triggered),
        'flags':         triggered,
        'all_reports':   reports,
    }


# ============================================
# LAYER 2 — FLEET SUMMARY
# Aggregates across all events.
# Answers the three fleet manager questions.
# ============================================

def generate_fleet_summary(events):
    """
    Processes a list of driving events and generates
    a fleet-wide safety summary.

    Answers:
    1. Which vehicle has most anomalies?
    2. Which road is most dangerous?
    3. Which anomaly type is most frequent?
    """
    vehicle_scores  = defaultdict(int)
    location_scores = defaultdict(int)
    flag_counts     = defaultdict(int)
    all_reports     = []

    for event in events:
        report = generate_safety_report(event)
        all_reports.append(report)

        score = SEVERITY_SCORE[report['overall_severity']]
        vehicle_scores[event['vehicle_id']]  += score
        location_scores[event['location']]   += score

        for flag in report['flags']:
            flag_counts[flag['type']] += 1

    # Sort results — highest risk first
    top_vehicles  = sorted(vehicle_scores.items(),
                           key=lambda x: x[1], reverse=True)
    top_locations = sorted(location_scores.items(),
                           key=lambda x: x[1], reverse=True)
    top_flags     = sorted(flag_counts.items(),
                           key=lambda x: x[1], reverse=True)

    return {
        'total_events':    len(events),
        'total_triggered': sum(1 for r in all_reports
                               if r['flags_triggered'] > 0),
        'top_vehicles':    top_vehicles[:5],
        'top_locations':   top_locations[:5],
        'top_flags':       top_flags,
        'all_reports':     all_reports,
    }


    # ============================================
    # TEST FLEET — Synthetic Nairobi driving data
    # 10 vehicles. Real Kenyan roads. Real plates.
    # ============================================

if __name__ == "__main__":
    test_fleet = [
        # Vehicle 1 — Normal highway KBZ 001A
        {
            'vehicle_id':    'KBZ 001A',
            'vehicle_model': 'TOYOTA_HIACE',
            'timestamp':     '2026-04-25 08:00:00',
            'location':      'Thika Road',
            'zone':          'highway',
            'speed_kmh':     95.0,
            'speed_prev_kmh':94.0,
            'brake_pressure':0.5,
            'steering_seq':  [5.1, 6.8, 4.2, 7.1, 3.9],
            'steering_angle':10.0,
            'long_accel_ms2':0.2,
            'time_delta_s':  1.0,
        },
        # Vehicle 2 — Overspeeding KCA 202B
        {
            'vehicle_id':    'KCA 202B',
            'vehicle_model': 'ISUZU_DMAX',
            'timestamp':     '2026-04-25 08:05:00',
            'location':      'Mombasa Road',
            'zone':          'highway',
            'speed_kmh':     155.0,
            'speed_prev_kmh':150.0,
            'brake_pressure':0.2,
            'steering_seq':  [3.0, 3.1, 2.9, 3.0, 3.1],
            'steering_angle':5.0,
            'long_accel_ms2':0.5,
            'time_delta_s':  1.0,
        },
        # Vehicle 3 — Harsh braking KDD 303C
        {
            'vehicle_id':    'KDD 303C',
            'vehicle_model': 'TOYOTA_HILUX',
            'timestamp':     '2026-04-25 08:10:00',
            'location':      'Ngong Road',
            'zone':          'urban',
            'speed_kmh':     45.0,
            'speed_prev_kmh':90.0,
            'brake_pressure':9.0,
            'steering_seq':  [8.0, 8.1, 7.9, 8.0, 8.1],
            'steering_angle':8.0,
            'long_accel_ms2':5.5,
            'time_delta_s':  1.0,
        },
        # Vehicle 4 — Distracted driver KBX 404D
        {
            'vehicle_id':    'KBX 404D',
            'vehicle_model': 'TOYOTA_PROBOX',
            'timestamp':     '2026-04-25 08:15:00',
            'location':      'Waiyaki Way',
            'zone':          'urban',
            'speed_kmh':     55.0,
            'speed_prev_kmh':55.0,
            'brake_pressure':0.1,
            'steering_seq':  [5.0, 5.0, 5.0, 5.0, 32.0],
            'steering_angle':5.0,
            'long_accel_ms2':0.1,
            'time_delta_s':  1.0,
        },
        # Vehicle 5 — School zone speeding KCB 505E
        {
            'vehicle_id':    'KCB 505E',
            'vehicle_model': 'TOYOTA_VITZ',
            'timestamp':     '2026-04-25 08:20:00',
            'location':      'Langata Road School Zone',
            'zone':          'school',
            'speed_kmh':     55.0,
            'speed_prev_kmh':54.0,
            'brake_pressure':0.3,
            'steering_seq':  [2.0, 2.1, 1.9, 2.0, 2.1],
            'steering_angle':3.0,
            'long_accel_ms2':0.1,
            'time_delta_s':  1.0,
        },
        # Vehicle 6 — Matatu sharp bend KDA 606F
        {
            'vehicle_id':    'KDA 606F',
            'vehicle_model': 'TOYOTA_HIACE',
            'timestamp':     '2026-04-25 08:25:00',
            'location':      'Nakuru Highway',
            'zone':          'highway',
            'speed_kmh':     85.0,
            'speed_prev_kmh':85.0,
            'brake_pressure':1.0,
            'steering_seq':  [10.0, 15.0, 20.0, 25.0, 30.0],
            'steering_angle':65.0,
            'long_accel_ms2':1.0,
            'time_delta_s':  1.0,
        },
        # Vehicle 7 — Fatigue drift KCE 707G
        {
            'vehicle_id':    'KCE 707G',
            'vehicle_model': 'MITSUBISHI_FUSO',
            'timestamp':     '2026-04-25 08:30:00',
            'location':      'Mombasa Road',
            'zone':          'highway',
            'speed_kmh':     88.0,
            'speed_prev_kmh':88.0,
            'brake_pressure':0.1,
            'steering_seq':  [5.0, 6.2, 7.8, 9.1, 10.5],
            'steering_angle':12.0,
            'long_accel_ms2':0.2,
            'time_delta_s':  1.0,
        },
        # Vehicle 8 — Combined violations KBW 808H
        {
            'vehicle_id':    'KBW 808H',
            'vehicle_model': 'TOYOTA_HIACE',
            'timestamp':     '2026-04-25 08:35:00',
            'location':      'Mombasa Road',
            'zone':          'highway',
            'speed_kmh':     140.0,
            'speed_prev_kmh':140.0,
            'brake_pressure':8.5,
            'steering_seq':  [5.0, 5.0, 5.0, 5.0, 38.0],
            'steering_angle':70.0,
            'long_accel_ms2':6.0,
            'time_delta_s':  1.0,
        },
        # Vehicle 9 — Normal urban KCC 909I
        {
            'vehicle_id':    'KCC 909I',
            'vehicle_model': 'MAZDA_DEMIO',
            'timestamp':     '2026-04-25 08:40:00',
            'location':      'Moi Avenue',
            'zone':          'urban',
            'speed_kmh':     38.0,
            'speed_prev_kmh':37.0,
            'brake_pressure':1.0,
            'steering_seq':  [8.1, 12.3, 6.2, 9.4, 7.8],
            'steering_angle':15.0,
            'long_accel_ms2':0.3,
            'time_delta_s':  1.0,
        },
        # Vehicle 10 — Night truck fatigue KDB 010J
        {
            'vehicle_id':    'KDB 010J',
            'vehicle_model': 'MITSUBISHI_FUSO',
            'timestamp':     '2026-04-25 02:00:00',
            'location':      'Mombasa Road',
            'zone':          'highway',
            'speed_kmh':     95.0,
            'speed_prev_kmh':95.0,
            'brake_pressure':0.1,
            'steering_seq':  [5.0, 5.0, 5.0, 5.0, 5.0],
            'steering_angle':8.0,
            'long_accel_ms2':0.1,
            'time_delta_s':  1.0,
        },
    ]
    # Generate fleet summary
    summary = generate_fleet_summary(test_fleet)
    print("\n" + "="*60)
    print("   SAFARI-SAFE-AI | FLEET SAFETY REPORT")
    print("   Generated:", datetime.now().strftime('%Y-%m-%d %H:%M'))
    print("   BRIDGE Framework | Ben Ogega")
    print("="*60)

    print(f"\n📊 SUMMARY")
    print(f"   Total events monitored:  {summary['total_events']}")
    print(f"   Events with violations:  {summary['total_triggered']}")
    print(f"   Clean events:            "
            f"{summary['total_events'] - summary['total_triggered']}")

    print(f"\n🚗 TOP RISK VEHICLES:")
    print(f"   {'Vehicle':<12} {'Risk Score'}")
    print(f"   {'-'*25}")
    for vehicle, score in summary['top_vehicles']:
        bar = '█' * score
        print(f"   {vehicle:<12} {bar} ({score})")

    print(f"\n📍 MOST DANGEROUS ROADS:")
    print(f"   {'Location':<30} {'Risk Score'}")
    print(f"   {'-'*45}")
    for location, score in summary['top_locations']:
        print(f"   {location:<30} {score}")

    print(f"\n⚠️  MOST FREQUENT VIOLATIONS:")
    print(f"   {'Flag Type':<30} {'Count'}")
    print(f"   {'-'*40}")
    for flag_type, count in summary['top_flags']:
        print(f"   {flag_type:<30} {count}")

    print(f"\n📋 INDIVIDUAL VEHICLE REPORTS:")
    print("="*60)
    for report in summary['all_reports']:
        status = "🚨" if report['flags_triggered'] > 0 else "✅"
        print(f"\n{status} {report['vehicle_id']:<12} "
                f"{report['overall_severity']:<8} "
                f"{report['location']}")
        for flag in report['flags']:
            print(f"   → {flag['type']:<30} {flag['severity']}")
    print("="*60)


