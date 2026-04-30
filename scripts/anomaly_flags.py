# -*- coding: utf-8 -*-

import numpy as np
import logging
from typing import Dict, List, Union
from dataclasses import dataclass, asdict

# ============================================
# Safari-Safe-AI | Physics-First Anomaly Flags
# Author: Ben Ogega | BRIDGE Framework
# Refined for Production & Forensic Safety
# ============================================

# Configure logging to capture safety events to a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='safari_safe_audit.log'
)

@dataclass(frozen=True)
class SafetyFlag:
    """Standardized output for all driving anomaly detectors.
    
    Attributes:
        flag: True if a safety violation was detected.
        type: The category of the flag (e.g., FLAG_OVERSPEED).
        severity: NONE, WARNING, DANGER, or CRITICAL.
        message: Human-readable explanation of the event.
        meta_data: Raw physics values for telemetry logging.
    """
    flag: bool
    type: str
    severity: str
    message: str
    meta_data: Dict[str, Union[float, int, bool, str]]

# Thresholds grounded in Kenyan Traffic Act
THRESHOLDS = {
    'speed_highway_kmh':     110.0,
    'speed_urban_kmh':        50.0,
    'speed_school_zone_kmh':  30.0,
    'brake_spike':             7.0,
    'steering_still':          0.3,
    'steering_overcorrect':   25.0,
    'decel_harsh':             3.5,
}

# ============================================
# SAFETY ENGINE FUNCTIONS
# ============================================

def flag_overspeed(speed_kmh: float, zone: str = 'highway') -> Dict:
    """Detects vehicle overspeeding relative to Kenyan traffic zones.
    
    Safety Theory:
        Based on kinetic energy (E = 1/2mv²). Higher speeds exponentially 
        increase braking distance and impact force.

    Args:
        speed_kmh: The current instantaneous speed of the vehicle.
        zone: The operational environment ('highway', 'urban', 'school').

    Returns:
        A dictionary representation of the SafetyFlag object.
        
    Raises:
        ValueError: If speed_kmh is a negative value.
    """
    if speed_kmh < 0:
        raise ValueError(f"Invalid speed: {speed_kmh}. Speed cannot be negative.")

    zone_limits = {
        'highway': THRESHOLDS['speed_highway_kmh'],
        'urban':   THRESHOLDS['speed_urban_kmh'],
        'school':  THRESHOLDS['speed_school_zone_kmh'],
    }

    limit = zone_limits.get(zone.lower(), THRESHOLDS['speed_highway_kmh'])
    excess = speed_kmh - limit

    if excess <= 0:
        severity, flagged = 'NONE', False
    elif excess <= 20:
        severity, flagged = 'WARNING', True
    elif excess <= 40:
        severity, flagged = 'DANGER', True
    else:
        severity, flagged = 'CRITICAL', True

    msg = (f'OVERSPEED: {speed_kmh} km/h in {zone} zone — {excess:.1f} km/h over limit' 
           if flagged else f'Normal speed: {speed_kmh} km/h')

    result = SafetyFlag(
        flag=flagged,
        type='FLAG_OVERSPEED',
        severity=severity,
        message=msg,
        meta_data={'excess_kmh': round(max(0, excess), 1), 'limit': limit}
    )
    
    if flagged:
        logging.warning(f"OVERSPEED EVENT: {msg}")
        
    return asdict(result)


def flag_harsh_braking(speed_before_kmh: float, 
                       speed_after_kmh: float,
                       brake_pressure: float, 
                       time_delta_s: float = 1.0) -> Dict:
    """Analyzes deceleration rates to identify emergency or aggressive braking.

    Safety Theory:
        AA Kenya Standards: Skid marks typically appear when deceleration 
        exceeds 0.5g (~4.9 m/s²). Values above 7.0 m/s² indicate imminent 
        collision-avoidance maneuvers.

    Args:
        speed_before_kmh: Speed at the start of the measurement window.
        speed_after_kmh: Speed at the end of the measurement window.
        brake_pressure: Normalized brake sensor input (Scale 0.0 - 10.0).
        time_delta_s: The duration of the event in seconds.

    Returns:
        A dictionary including deceleration (m/s²) and skid_risk (bool).
    """
    if time_delta_s <= 0:
        logging.error("Harsh Braking calculation failed: time_delta_s must be > 0")
        return asdict(SafetyFlag(False, 'ERROR', 'NONE', "Invalid time delta", {}))

    v1, v2 = speed_before_kmh / 3.6, speed_after_kmh / 3.6
    deceleration = (v1 - v2) / time_delta_s

    if deceleration < THRESHOLDS['decel_harsh']:
        severity, flagged = 'NONE', False
    elif deceleration < 5.0:
        severity, flagged = 'WARNING', True
    elif deceleration < 7.0:
        severity, flagged = 'DANGER', True
    else:
        severity, flagged = 'CRITICAL', True

    skid_risk = bool(brake_pressure >= THRESHOLDS['brake_spike'] and deceleration >= 5.0)

    result = SafetyFlag(
        flag=flagged,
        type='FLAG_HARSH_BRAKING',
        severity=severity,
        message=f'Decel: {deceleration:.2f} m/s² | Skid Risk: {skid_risk}',
        meta_data={'decel_ms2': round(deceleration, 2), 'skid_risk': skid_risk}
    )
    
    if flagged:
        logging.warning(f"BRAKING EVENT: {result.message}")
        
    return asdict(result)


def flag_distraction(steering_sequence: List[float], 
                     time_window_s: float = 2.0) -> Dict:
    """Detects cognitive distraction through erratic steering patterns.

    Safety Theory:
        Focused drivers perform micro-corrections (entropy). Phone distraction 
        results in "clamping" (low variance) followed by an over-correction 
        "snap" when attention returns to the road.

    Args:
        steering_sequence: Time-series of steering angles in degrees.
        time_window_s: The duration of the window analyzed.

    Returns:
        Analysis of steering variance and corrective snap behavior.
    """
    if len(steering_sequence) < 4:
        return asdict(SafetyFlag(False, 'FLAG_DISTRACTION', 'NONE', 'Insufficient data', {}))

    seq = np.array(steering_sequence)
    mid = len(seq) // 2
    
    early_std = np.std(seq[:mid])
    late_change = np.max(np.abs(np.diff(seq[mid:])))
    total_variance = np.std(seq)


    is_still = early_std < THRESHOLDS['steering_still']
    is_snap = late_change > THRESHOLDS['steering_overcorrect']

    if is_still and is_snap:
        severity, flagged = 'CRITICAL', True
        msg = "DISTRACTION: Steering frozen then snapped back."
    elif is_still:
        severity, flagged = 'WARNING', True
        msg = "DISTRACTION: Steering unnaturally still (likely phone use)."
    elif is_snap:
        severity, flagged = 'WARNING', True
        msg = "OVERCORRECTION: Sudden steering adjustment detected."
    else:
        severity, flagged = 'NONE', False
        msg = "Normal steering activity."

    result = SafetyFlag(
        flag=flagged,
        type='FLAG_DISTRACTION',
        severity=severity,
        message=msg,
        meta_data={'std_dev': round(total_variance, 3), 'max_snap': round(late_change, 1)}
    )
    
    if flagged:
        logging.warning(f"DISTRACTION EVENT: {msg}")

    return asdict(result)



# Phase 3 — Lateral Dynamics & Grip Management

# Add Phase 3 specific thresholds
PHASE_3_THRESHOLDS = {
    'lat_accel_warning': 3.0,   # m/s^2 - Passengers start to lean
    'lat_accel_danger':  5.0,   # m/s^2 - Limit for high-center vehicles (SUVs)
    'friction_limit_g':  0.8,   # Standard asphalt grip limit (~7.8 m/s^2)
}

# ============================================
# FLAG 4 — AGGRESSIVE CORNERING
# ============================================

def flag_aggressive_cornering(speed_kmh: float, radius_m: float) -> Dict:
    """Detects dangerous lateral forces during cornering.
    
    Safety Theory:
        Centripetal force increases with the square of speed ($a_c = v^2 / r$). 
        In Kenya, many rural roads have inconsistent camber (slopes), 
        reducing the effective grip available for cornering.

    Args:
        speed_kmh: Current vehicle speed.
        radius_m: The radius of the turn in meters (from GPS or Steering Map).

    Returns:
        A dictionary containing lateral acceleration and rollover risk.
    """
    if radius_m <= 0:
        return asdict(SafetyFlag(False, 'FLAG_LATERAL', 'NONE', "Straight path", {}))

    # Convert speed to m/s
    v = speed_kmh / 3.6
    
    # Calculate Centripetal Acceleration: a = v^2 / r
    lat_accel = (v**2) / radius_m

    flagged = lat_accel > PHASE_3_THRESHOLDS['lat_accel_warning']
    
    if lat_accel < PHASE_3_THRESHOLDS['lat_accel_warning']:
        severity = 'NONE'
    elif lat_accel < PHASE_3_THRESHOLDS['lat_accel_danger']:
        severity = 'WARNING'
    else:
        severity = 'DANGER'

    msg = f"Lateral Force: {lat_accel:.2f} m/s² | "
    msg += "High rollover risk for Matatus/SUVs" if lat_accel > 4.0 else "Stable"

    result = SafetyFlag(
        flag=flagged,
        type='FLAG_AGGRESSIVE_CORNERING',
        severity=severity,
        message=msg,
        meta_data={'lat_accel_ms2': round(lat_accel, 2), 'turn_radius_m': radius_m}
    )

    if flagged:
        logging.warning(f"LATERAL EVENT: {msg}")

    return asdict(result)

# ============================================
# FLAG 5 — FRICTION CIRCLE VIOLATION
# ============================================

def flag_grip_violation(lat_accel_ms2: float, long_accel_ms2: float) -> Dict:
    """Detects if combined steering and braking exceeds physics limits.
    
    Safety Theory:
        The Circle of Friction (Kamm's Circle) states that total grip 
        is the vector sum of longitudinal (braking) and lateral (turning) 
        forces. If $Total > Limit$, a skid is mathematically certain.

    Args:
        lat_accel_ms2: Measured lateral acceleration.
        long_accel_ms2: Measured longitudinal acceleration (braking).

    Returns:
        Analysis of total grip utilization percentage.
    """
    # Total Vector Magnitude: sqrt(a_lat^2 + a_long^2)
    total_grip_used = np.sqrt(lat_accel_ms2**2 + long_accel_ms2**2)
    
    # Convert friction limit g to m/s^2
    limit = PHASE_3_THRESHOLDS['friction_limit_g'] * 9.81
    utilization_pct = (total_grip_used / limit) * 100

    flagged = utilization_pct > 80.0 # 80% is the safety buffer
    
    if utilization_pct < 80.0:
        severity = 'NONE'
    elif utilization_pct < 95.0:
        severity = 'WARNING'
    else:
        severity = 'CRITICAL'

    msg = f"Grip Utilization: {utilization_pct:.1f}% of available friction."

    result = SafetyFlag(
        flag=flagged,
        type='FLAG_GRIP_VIOLATION',
        severity=severity,
        message=msg,
        meta_data={'total_accel': round(total_grip_used, 2), 'utilization_pct': round(utilization_pct, 1)}
    )

    if flagged:
        logging.error(f"FRICTION CIRCLE VIOLATION: {msg}")

    return asdict(result)

# ============================================
# BRIDGE Framework Phase 3 — Lateral Dynamics
# ============================================

# 2024 Kenyan Road Dominator Library (Wheelbase in Meters)
WHEELBASE_LIBRARY = {
    'ISUZU_DMAX': 3.125,
    'TOYOTA_HILUX': 3.085,
    'TOYOTA_HIACE': 3.860,
    'TOYOTA_LC300': 2.850,
    'ISUZU_FRR': 4.800,
    'TOYOTA_PROBOX': 2.550,
    'TOYOTA_FIELDER': 2.600,
    'MAZDA_DEMIO': 2.570,
    'MITSUBISHI_FUSO': 4.800,
    'TOYOTA_VITZ': 2.510,
}

@dataclass(frozen=True)
class SafetyFlag:
    """Immutable record for safety anomalies."""
    flag: bool
    type: str
    severity: str
    message: str
    meta_data: Dict[str, Union[float, int, bool, str]]

# ============================================
# UTILITY: RADIUS CALCULATION
# ============================================

def get_turning_radius(steering_angle: float, vehicle_model: str) -> float:
    r"""Calculates the geometric turning radius of a specific Kenyan vehicle.
    
    This function uses the Ackerman Steering model. It converts steering wheel 
    input into a physical radius ($R = L / \sin(\delta)$).

    Args:
        steering_angle: Input from steering column in degrees.
        vehicle_model: Key from WHEELBASE_LIBRARY.

    Returns:
        float: Radius in meters. Returns float('inf') for straight travel.
    """
    wheelbase = WHEELBASE_LIBRARY.get(vehicle_model.upper(), 2.8) # Default to 2.8m
    # steering_ratio = 16.5  # Standard for most modern power steering systems
    steering_ratio = 16.0  # Adjusted for Kenyan vehicles with less assist

    # Defensive check for straight-line travel (prevent division by zero)
    if abs(steering_angle) < 1.0:
        return float('inf')

    # Convert steering wheel degrees to wheel-at-road radians
    tire_angle_rad = np.radians(steering_angle / steering_ratio)
    
    # Physics: R = L / sin(theta)
    radius = wheelbase / np.sin(tire_angle_rad)
    return abs(radius)

# ============================================
# FLAG 6 — LATERAL G-FORCE (ROLLOVER RISK)
# ============================================

def flag_lateral_force(speed_kmh: float, 
                       steering_angle: float, 
                       vehicle_model: str = 'TOYOTA_HIACE') -> Dict:
    """Evaluates the risk of sliding or rolling over in a turn.
    
    Safety Theory:
        Centripetal acceleration ($a_c = v^2/r$) is the primary cause of 
        matatu/truck rollovers on highway bends. 
        Critical threshold for high-roof vehicles is ~0.45g (4.4 m/s²).

    Args:
        speed_kmh: Instantaneous speed.
        steering_angle: Steering wheel input in degrees.
        vehicle_model: The specific vehicle type to pull wheelbase data.

    Returns:
        Dict: Safety flag status with lateral acceleration in m/s².
    """
    # 1. Input Validation (Defensive Programming)
    if speed_kmh < 0:
        return asdict(SafetyFlag(False, 'ERROR', 'NONE', "Speed cannot be negative", {}))

    # 2. Derive Physics Properties
    radius = get_turning_radius(steering_angle, vehicle_model)
    v_ms = speed_kmh / 3.6
    
    # 3. Calculate Centripetal Acceleration
    if radius == float('inf') or v_ms == 0:
        lat_accel = 0.0
    else:
        lat_accel = (v_ms**2) / radius

    # 4. Severity Mapping (Grounded in AA Kenya defensive standards)
    # 0.0-3.0: Normal; 3.0-4.5: Warning (Leaning); 4.5+: Danger (Slide/Roll)
    if lat_accel < 3.0:
        severity, flagged = 'NONE', False
    elif lat_accel < 4.5:
        severity, flagged = 'WARNING', True
    else:
        severity, flagged = 'DANGER', True

    msg = f"Lat Accel: {lat_accel:.2f} m/s² ({vehicle_model})"
    if lat_accel > 4.5:
        msg += " — CRITICAL ROLLOVER RISK"

    return asdict(SafetyFlag(
        flag=flagged,
        type='FLAG_LATERAL_FORCE',
        severity=severity,
        message=msg,
        meta_data={'lat_accel': round(lat_accel, 2), 'radius': round(radius, 1)}
    ))

# ============================================
# FLAG 7 — KAMM'S CIRCLE (THE FRICTION LIMIT)
# ============================================

def flag_friction_circle(speed_kmh: float, 
                         steering_angle: float, 
                         long_accel_ms2: float,
                         vehicle_model: str) -> Dict:
    """Calculates the total load on the tires (Combined Loading).
    
    Safety Theory:
        Combines braking/acceleration and cornering. A driver might 
        safely brake at 4 m/s² or turn at 4 m/s², but doing both 
        simultaneously creates a vector of 5.6 m/s², which may exceed 
        road friction (Kamm's Circle).

    Args:
        speed_kmh: Speed in km/h.
        steering_angle: Steering angle in degrees.
        long_accel_ms2: Longitudinal acceleration from braking/gas.
        vehicle_model: Key from WHEELBASE_LIBRARY.

    Returns:
        Dict: Utilization of total available friction (%).
    """
    # Get lateral component
    lat_result = flag_lateral_force(speed_kmh, steering_angle, vehicle_model)
    a_lat = lat_result['meta_data'].get('lat_accel', 0.0)
    
    # Calculate Resultant Vector: sqrt(a_lat² + a_long²)
    total_accel = np.sqrt(a_lat**2 + long_accel_ms2**2)
    
    # 8.0 m/s² is a safe limit for typical Kenyan tarmac (0.8g)
    utilization_pct = (total_accel / 8.0) * 100
    
    flagged = utilization_pct > 85.0
    severity = 'CRITICAL' if utilization_pct > 100.0 else ('WARNING' if flagged else 'NONE')

    return asdict(SafetyFlag(
        flag=flagged,
        type='FLAG_FRICTION_CIRCLE',
        severity=severity,
        message=f"Total Grip Utilization: {utilization_pct:.1f}%",
        meta_data={'vector_sum': round(total_accel, 2), 'utilization_pct': round(utilization_pct, 1)}
    ))


# ============================================
# FLAG 8 — TAILGATING / TIME TO COLLISION
# One function. One job.
# Detects dangerous following distance
#
# Research basis:
# Highway Code: 2-second rule minimum
# AA Kenya: 3-second rule recommended
# Physics: TTC = gap / relative_speed
# ============================================

def flag_tailgating(speed_kmh, lead_speed_kmh,
                    gap_m, vehicle_model='TOYOTA_HIACE'):
    """
    Detects dangerous following distance using
    Time-to-Collision (TTC) physics.

    speed_kmh      — your vehicle speed
    lead_speed_kmh — lead vehicle speed
    gap_m          — current gap in metres

    One function. One job:
    Calculate TTC and flag if below safe threshold.

    Physics: TTC = gap / relative_speed
    AA Kenya standard: 3 seconds minimum
    """
    # Convert to m/s
    v_ego  = speed_kmh / 3.6
    v_lead = lead_speed_kmh / 3.6

    # Relative speed — positive means closing
    rel_speed = v_ego - v_lead

    # Not closing — no tailgating risk
    if rel_speed <= 0:
        return {
            'flag':     False,
            'type':     'FLAG_TAILGATING',
            'severity': 'NONE',
            'ttc_s':    float('inf'),
            'gap_m':    gap_m,
            'message':  f'Gap {gap_m:.1f}m — not closing on lead vehicle'
        }

    # Calculate TTC
    ttc = gap_m / rel_speed

    # Severity — AA Kenya 3-second rule
    # Default values — safety net
    severity = 'NONE'
    flagged  = False
# Severity — AA Kenya 3-second rule
    if ttc > 3.5:
        return {
            'flag':         False,
            'type':         'FLAG_TAILGATING',
            'severity':     'NONE',
            'ttc_s':        round(ttc, 2),
            'gap_m':        round(gap_m, 1),
            'rel_speed_ms': round(rel_speed, 2),
            'message':      f'TTC: {ttc:.2f}s — Gap: {gap_m:.1f}m — '
                            f'Closing at {rel_speed*3.6:.1f} km/h'
        }
    elif ttc > 2.5:
        severity = 'WARNING'
    elif ttc > 1.0:
        severity = 'DANGER'
    else:
        severity = 'CRITICAL'

    return {
        'flag':         True,
        'type':         'FLAG_TAILGATING',
        'severity':     severity,
        'ttc_s':        round(ttc, 2),
        'gap_m':        round(gap_m, 1),
        'rel_speed_ms': round(rel_speed, 2),
        'message':      f'TTC: {ttc:.2f}s — Gap: {gap_m:.1f}m — '
                        f'Closing at {rel_speed*3.6:.1f} km/h'
    }

# ============================================
# QUICK TEST 
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
        # Focused driver — constant micro corrections
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


    print("="*55 + "\n BRIDGE Phase 3 — Lateral Dynamics Validation\n" + "="*55)
    
    # Scenario: Toyota Hiace Matatu taking a highway bend at 80km/h with 15deg steering
    print("\nScenario 1: Hiace Matatu Highway Bend")
    hiace_turn = flag_lateral_force(80, 15, 'TOYOTA_HIACE')
    print(f"Result: {hiace_turn['message']} (Severity: {hiace_turn['severity']})")

    # Scenario: Isuzu D-Max braking while cornering (Emergency Swerve)
    print("\nScenario 2: D-Max Emergency Swerve (Braking + Turning)")
    dmax_evasion = flag_friction_circle(60, 30, 4.5, 'ISUZU_DMAX')
    print(f"Result: {dmax_evasion['message']} (Severity: {dmax_evasion['severity']})")

    # More realistic highway bend scenario
    print("\nScenario 1b: Hiace Matatu Sharp Bend 90km/h")
    hiace_sharp = flag_lateral_force(90, 25, 'TOYOTA_HIACE')
    print(f"Result: {hiace_sharp['message']} (Severity: {hiace_sharp['severity']})")

    # Replace 15 degrees with realistic bend scenarios
    print("\nScenario 1: Hiace — gentle lane change (15 deg)")
    print(f"{flag_lateral_force(80, 15, 'TOYOTA_HIACE')['message']}")

    print("\nScenario 2: Hiace — rural sharp bend (60 deg)")
    print(f"{flag_lateral_force(80, 60, 'TOYOTA_HIACE')['message']}")

    print("\nScenario 3: Hiace — emergency swerve (90 deg)")
    print(f"{flag_lateral_force(80, 90, 'TOYOTA_HIACE')['message']}")

    print("\nScenario 4: Hiace — tight junction (120 deg)")
    print(f"{flag_lateral_force(60, 120, 'TOYOTA_HIACE')['message']}")


    print("\n" + "="*55)
    print("   Safari-Safe-AI | Tailgating Flag Tests")
    print("="*55)

    tailgate_tests = [
        # (your_speed, lead_speed, gap, scenario)
        (88, 70, 50.0, "Safe following — Thika Road"),
        (88, 70, 21.8, "Warning zone — t=5 from notebook"),
        (88, 70, 15.7, "Danger — t=6 from notebook"),
        (88, 70,  9.3, "Critical — near collision"),
        (60, 70, 15.0, "Safe — braking, not closing"),
    ]

    for ego, lead, gap, scenario in tailgate_tests:
        result = flag_tailgating(ego, lead, gap)
        status = "🚨" if result['flag'] else "✅"
        print(f"\n{status} {result['severity']:<8} {scenario}")
        print(f"   {result['message']}")

    

