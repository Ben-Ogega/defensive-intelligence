#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import matplotlib.pyplot as plt



# # ============================================
# # Safari-Safe-AI | Phase 3
# # F=ma to Self-Attention Bridge
# # Author: Ben Ogega | BRIDGE Framework
# # ============================================
# 
# # Your driving sequence — 10 timesteps
# # Nairobi — Mombasa Road — dangerous event at t=7
# 

# In[2]:


speeds_kmh = np.array([
    88.0,   # t=0 normal highway
    89.0,   # t=1 slight acceleration
    91.0,   # t=2 still accelerating
    92.0,   # t=3 cruising
    91.5,   # t=4 slight variation
    92.0,   # t=5 normal
    93.0,   # t=6 still normal
    60.0,   # t=7 HARSH BRAKING — dangerous event
    45.0,   # t=8 still braking
    44.0,   # t=9 nearly stopped
])

# Convert to m/s — Newton's laws work in SI units
speeds_ms = speeds_kmh / 3.6

print("Speeds (m/s):", speeds_ms)


# In[5]:


# Simple moving average to filter sensor jitter
window_size = 3
smoothed_speeds = np.convolve(speeds_ms, np.ones(window_size)/window_size, mode='valid')
print("Smoothed Speeds (m/s):", smoothed_speeds)


# In[6]:


dt = 1.0  # 1 second between readings
accelerations = np.diff(speeds_ms) / dt


# In[7]:


print("="*55)
print("STEP 1 — F=ma: Acceleration at each timestep")
print("="*55)
for i, a in enumerate(accelerations):
    flag = " ← DANGEROUS" if abs(a) > 3.5 else ""
    print(f"  t={i}→{i+1}: {a:+.3f} m/s²{flag}")

print(f"\nMost dangerous moment: t={np.argmin(accelerations)}→{np.argmin(accelerations)+1}")
print(f"Peak deceleration: {accelerations.min():.3f} m/s²")


# In[ ]:


# Or Create a boolean mask of dangerous events
dangerous_indices = np.where(np.abs(accelerations) > 3.5)[0]
print(f"Dangerous Timesteps detected at: {dangerous_indices}")


# In[9]:


# Adding a simple subplot  showing the Speed profile vs. the Acceleration profile will make the "Dangerous" event at t=7 visually undeniable.


# In[ ]:


# Data from user
timestamps = np.arange(0, 10, 1.0)
speeds_kmh = np.array([88.0, 89.0, 91.0, 92.0, 91.5, 92.0, 93.0, 60.0, 45.0, 44.0])
speeds_ms = speeds_kmh / 3.6
dt = 1.0
accelerations = np.diff(speeds_ms) / dt

# Time midpoints for acceleration plot
accel_times = timestamps[:-1] + 0.5

# Create plots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Plot 1: Speed
ax1.plot(timestamps, speeds_kmh, marker='o', color='b', linestyle='-', label='Vehicle Speed')
ax1.axvspan(6.5, 7.5, color='red', alpha=0.2, label='Harsh Braking Zone')
ax1.set_ylabel('Speed ($km/h$)')
ax1.set_title('Safari-Safe-AI Phase 3: Telematics Analysis (Mombasa Road)')
ax1.grid(True, linestyle='--', alpha=0.7)
ax1.legend()

# Plot 2: Acceleration
ax2.plot(accel_times, accelerations, marker='s', color='r', linestyle='--', label='Acceleration')
ax2.axhline(0, color='black', linewidth=1)
ax2.axhline(-3.5, color='orange', linestyle=':', label='Safety Threshold (-3.5 $m/s^2$)')
ax2.set_ylabel('Acceleration ($m/s^2$)')
ax2.set_xlabel('Time ($s$)')
ax2.grid(True, linestyle='--', alpha=0.7)
ax2.legend()

plt.tight_layout()
plt.savefig('../figures/safari_safe_telematics.png')

print("Calculated Accelerations (m/s^2):", accelerations)


# In[12]:


# Parameters
g = 9.81              # m/s^2
mu_asphalt = 0.7      # Dry asphalt (standard)
mu_gravel = 0.35      # Loose surface/Wet (dangerous)
reaction_time = 1.5   # Nairobi traffic "distracted" estimate (seconds)

# 1. Calculate Maximum Braking Capacity
max_a_asphalt = -mu_asphalt * g
max_a_gravel = -mu_gravel * g

# 2. Identify Skidding Events
skidding_on_asphalt = accelerations < max_a_asphalt
skidding_on_gravel = accelerations < max_a_gravel

# 3. Calculate "Perception-Reaction Distance"
# Distance traveled before the driver even hits the brakes
reaction_distance = speeds_ms[6] * reaction_time 

print(f"Max Deceleration (Asphalt): {max_a_asphalt:.2f} m/s²")
print(f"Max Deceleration (Gravel):  {max_a_gravel:.2f} m/s²")
print("-" * 40)

# Check our t=6->7 event (-9.17 m/s²)
if accelerations[6] < max_a_asphalt:
    print(f"CRITICAL: At t=7, vehicle is SKIDDING even on dry asphalt!")

print(f"Distance covered during reaction time: {reaction_distance:.2f} meters")


# In[13]:


# Lead vehicle speed (constant 70 km/h)
lead_speed_ms = 70 / 3.6 

# Initial gap at t=0 (meters)
initial_gap = 50 

# 1. Calculate Relative Speed at each timestep
# If positive, you are gaining on the lead vehicle
rel_speeds = speeds_ms - lead_speed_ms

# 2. Track the Gap over time (Numerical Integration)
# gap_t = gap_{t-1} - (rel_speed * dt)
gaps = [initial_gap]
for rs in rel_speeds:
    new_gap = gaps[-1] - (rs * dt)
    gaps.append(max(0, new_gap)) # Gap can't be less than 0 (collision)

gaps = np.array(gaps[:-1]) # Align with timestamps

# 3. Time-to-Collision (TTC) 
# TTC = Gap / Relative Speed (only when closing the gap)
ttc = np.where(rel_speeds > 0, gaps / rel_speeds, np.inf)

print("="*55)
print("PHASE 3 REFINEMENT: Collision Awareness")
print("="*55)
for i, t in enumerate(ttc):
    status = "⚠️ WARNING" if t < 3.0 else "Safe"
    print(f"t={i}: Gap={gaps[i]:.1f}m | TTC={t:.2f}s | {status}")

