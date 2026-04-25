# -*- coding: utf-8 -*-

import numpy as np

# ============================================
# Safari-Safe-AI | Physics-First Anomaly Flags
# Author: Ben Ogega | BRIDGE Framework
# Phase 2 — Encoding defensive driving knowledge
# AA Kenya | FIA Affiliate | 15+ years experience
# ============================================

"""
Every flag in this file represents a dangerous
driving behaviour observed and taught by the author
during 2 years of defensive driving instruction
at the Automobile Association of Kenya.

This is not guesswork. This is domain knowledge
encoded into mathematics.
"""

# ============================================
# THRESHOLDS — Physics-based limits
# Grounded in Kenyan road speed limits and
# defensive driving standards
# ============================================

THRESHOLDS = {
    'speed_highway_kmh':     110.0,   # Kenya highway limit
    'speed_urban_kmh':        50.0,   # Kenya urban limit
    'speed_school_zone_kmh':  30.0,   # School zone limit
    'brake_spike':             7.0,   # Brake pressure danger threshold
    'steering_still':          0.3,   # Max variance for distraction flag
    'steering_overcorrect':   25.0,   # Sudden steering angle degrees
    'decel_harsh':             3.5,   # m/s^2 — harsh braking threshold
    'tailgate_cycles':         3,     # Brake cycles in short window
    'distraction_time_s':      5.0,   # Seconds of eyes off road
}


# ============================================
# FLAG 1 — OVERSPEED
# One function. One job.
# Detects vehicle exceeding safe speed limits
# Source: Kenya Traffic Act + AA Kenya training
# ============================================

def flag_overspeed(speed_kmh, zone='highway'):
    """
    Detects overspeeding based on zone type.
    
    speed_kmh — current vehicle speed in km/h
    zone      — 'highway', 'urban', 'school'
    
    Returns dict with flag status and severity.
    
    One function. One job:
    Check if speed exceeds zone threshold.
    """
    # Select correct threshold for zone
    zone_limits = {
        'highway': THRESHOLDS['speed_highway_kmh'],
        'urban':   THRESHOLDS['speed_urban_kmh'],
        'school':  THRESHOLDS['speed_school_zone_kmh'],
    }

    # Default to highway if zone unknown
    limit = zone_limits.get(zone, THRESHOLDS['speed_highway_kmh'])

    # How far over the limit?
    excess = speed_kmh - limit

    if excess <= 0:
        return {
            'flag':     False,
            'type':     'FLAG_OVERSPEED',
            'severity': 'NONE',
            'message':  f'Speed {speed_kmh} km/h within {zone} limit of {limit} km/h',
            'excess_kmh': 0
        }
    elif excess <= 20:
        severity = 'WARNING'
    elif excess <= 40:
        severity = 'DANGER'
    else:
        severity = 'CRITICAL'

    return {
        'flag':       True,
        'type':       'FLAG_OVERSPEED',
        'severity':   severity,
        'message':    f'OVERSPEED: {speed_kmh} km/h in {zone} zone — '
                      f'{excess:.1f} km/h over limit',
        'excess_kmh': round(excess, 1)
    }

# ============================================
# FLAG 2 — HARSH BRAKING
# One function. One job.
# Detects dangerous braking events
# Source: AA Kenya defensive driving standards
# Physics: deceleration = delta_v / delta_t
# Skid marks appear above 0.5g deceleration
# ============================================

def flag_harsh_braking(speed_before_kmh, speed_after_kmh,
                        brake_pressure, time_delta_s=1.0):
    """
    Detects harsh braking using physics.

    speed_before_kmh — speed at start of braking (km/h)
    speed_after_kmh  — speed after time_delta_s (km/h)
    brake_pressure   — brake sensor reading (0-10 scale)
    time_delta_s     — time between readings (seconds)

    One function. One job:
    Check if deceleration exceeds safe threshold.

    Physics: deceleration = (v_before - v_after) / time
    Unit conversion: km/h to m/s = divide by 3.6
    """
    # Convert speeds to m/s — Newton's laws work in SI units
    v_before = speed_before_kmh / 3.6
    v_after  = speed_after_kmh  / 3.6

    # Calculate deceleration — delta_v / delta_t
    # Your F=ma from B.Tech — a = (v2-v1)/t
    deceleration = (v_before - v_after) / time_delta_s

    # Negative deceleration = acceleration — not braking
    if deceleration <= 0:
        return {
            'flag':          False,
            'type':          'FLAG_HARSH_BRAKING',
            'severity':      'NONE',
            'decel_ms2':     round(deceleration, 2),
            'message':       'No braking detected'
        }

    # Determine severity
    # 0-3.5 m/s²  — normal braking — passengers comfortable
    # 3.5-5.0     — harsh — passengers feel it — WARNING
    # 5.0-7.0     — dangerous — skid risk — DANGER
    # 7.0+        — critical — skid marks — CRITICAL
    if deceleration < THRESHOLDS['decel_harsh']:
        severity = 'NONE'
        flagged  = False
    elif deceleration < 5.0:
        severity = 'WARNING'
        flagged  = True
    elif deceleration < 7.0:
        severity = 'DANGER'
        flagged  = True
    else:
        severity = 'CRITICAL'
        flagged  = True

    # Skid mark indicator — brake pressure + high deceleration
    skid_risk = brake_pressure >= THRESHOLDS['brake_spike'] \
                and deceleration >= 5.0

    return {
        'flag':          flagged,
        'type':          'FLAG_HARSH_BRAKING',
        'severity':      severity,
        'decel_ms2':     round(deceleration, 2),
        'brake_pressure': brake_pressure,
        'skid_risk':     skid_risk,
        'message':       f'Deceleration: {deceleration:.2f} m/s² '
                         f'({deceleration/9.81*100:.1f}% of g) — '
                         f'Brake: {brake_pressure}/10 — '
                         f'Skid risk: {skid_risk}'
    }



# ============================================
# FLAG 3 — DRIVER DISTRACTION
# One function. One job.
# Detects distraction via steering inactivity
# followed by sudden overcorrection
#
# Research basis:
# NHTSA: 5 seconds eyes off road = danger
# AAA: 2 seconds doubles crash risk
# AA Kenya: phone unlock ~6 seconds
#
# Physics: Focused drivers make constant
# micro-corrections — std dev > 0.3 degrees
# Distracted drivers go unnaturally still
# then overcorrect suddenly
# ============================================

def flag_distraction(steering_sequence, time_window_s=2.0):
    """
    Detects driver distraction from steering pattern.
    One function. One job.
    """
    if len(steering_sequence) < 3:
        return {
            'flag':     False,
            'type':     'FLAG_DISTRACTION',
            'severity': 'NONE',
            'message':  'Insufficient data points'
        }

    seq = np.array(steering_sequence)

    # Split into early and late halves
    mid = len(seq) // 2
    early_std    = np.std(seq[:mid])
    late_change  = np.max(np.abs(np.diff(seq[mid:])))

    # Overall measures
    variance     = np.std(seq)
    max_change   = np.max(np.abs(np.diff(seq)))
    steering_range = np.max(seq) - np.min(seq)

    # Distraction signatures
    still           = variance < THRESHOLDS['steering_still']
    overcorrect     = max_change > THRESHOLDS['steering_overcorrect']
    still_then_snap = (early_std < THRESHOLDS['steering_still'] and
                       late_change > THRESHOLDS['steering_overcorrect'])

    # Classify — most severe first
    if still_then_snap:
        severity = 'CRITICAL'
        flagged  = True
        message  = (f'DISTRACTION CRITICAL: Still first half '
                    f'(std={early_std:.3f}) then snapped '
                    f'{late_change:.1f} degrees — phone use confirmed')
    elif still and overcorrect:
        severity = 'CRITICAL'
        flagged  = True
        message  = (f'DISTRACTION DETECTED: Still '
                    f'(std={variance:.3f}) then overcorrected '
                    f'({max_change:.1f} degrees)')
    elif still:
        severity = 'WARNING'
        flagged  = True
        message  = (f'DISTRACTION WARNING: Steering unnaturally '
                    f'still (std={variance:.3f}) — possible phone use')
    elif overcorrect:
        severity = 'WARNING'
        flagged  = True
        message  = (f'OVERCORRECTION WARNING: Sudden steering '
                    f'change of {max_change:.1f} degrees')
    else:
        severity = 'NONE'
        flagged  = False
        message  = (f'Normal steering — '
                    f'std={variance:.3f}, '
                    f'max change={max_change:.1f} degrees')

    return {
        'flag':           flagged,
        'type':           'FLAG_DISTRACTION',
        'severity':       severity,
        'steering_std':   round(variance, 3),
        'early_std':      round(early_std, 3),
        'late_change':    round(late_change, 1),
        'max_change_deg': round(max_change, 1),
        'steering_range': round(steering_range, 1),
        'time_window_s':  time_window_s,
        'message':        message
    }




# ============================================
# QUICK TEST — remove before production
# ============================================
if __name__ == "__main__":
    
    # Test cases — Kenyan road scenarios
    tests = [
        (90,  'highway'),   # Normal highway
        (115, 'highway'),   # Slightly over
        (145, 'highway'),   # Danger
        (170, 'highway'),   # Critical
        (60,  'urban'),     # Over urban limit
        (35,  'school'),    # Over school limit
    ]

    print("="*55)
    print("   Safari-Safe-AI | Overspeed Flag Tests")
    print("="*55)

    for speed, zone in tests:
        result = flag_overspeed(speed, zone)
        status = "🚨" if result['flag'] else "✅"
        print(f"\n{status} {result['severity']:<8} "
              f"{speed} km/h in {zone} zone")
        print(f"   {result['message']}")


    print("\n" + "="*55)
    print("   Safari-Safe-AI | Harsh Braking Flag Tests")
    print("="*55)

    brake_tests = [
        # (speed_before, speed_after, brake_pressure, scenario)
        (60,  55,  2.0, "Normal city braking"),
        (80,  60,  5.0, "Progressive highway braking"),
        (90,  60,  7.5, "Harsh — Mlolongo junction"),
        (110, 60,  9.0, "Dangerous — Mombasa Road"),
        (120, 40,  9.5, "Critical — near accident"),
    ]

    for v1, v2, bp, scenario in brake_tests:
        result = flag_harsh_braking(v1, v2, bp)
        status = "🚨" if result['flag'] else "✅"
        print(f"\n{status} {result['severity']:<8} {scenario}")
        print(f"   {result['message']}")

    
    print("\n" + "="*55)
    print("   Safari-Safe-AI | Distraction Flag Tests")
    print("="*55)

    distraction_tests = [
        # Focused driver — constant micro corrections/More realistic corrections:
        ([5.1, 6.8, 4.2, 7.1, 3.9, 6.5, 4.8, 7.2],
        "Focused driver — highway"),
        # Distracted — unnaturally still
        ([5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
         "Distracted — phone unlock"),

        # Distracted — still then overcorrect
        ([5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 32.0, 28.0],
         "Distracted — snap back overcorrection"),

        # Fatigue drift — slow wandering
        ([5.0, 6.2, 7.8, 9.1, 10.5, 11.2, 12.0, 13.1],
         "Fatigue drift — Mombasa Road night"),

        # Urban normal — more steering activity
        ([8.1, 12.3, 6.2, 15.1, 4.8, 9.3, 11.2, 7.4],
         "Normal urban — Nairobi CBD"),

    ]


    for sequence, scenario in distraction_tests:
        result = flag_distraction(sequence)
        status = "🚨" if result['flag'] else "✅"
        print(f"\n{status} {result['severity']:<8} {scenario}")
        print(f"   {result['message']}")