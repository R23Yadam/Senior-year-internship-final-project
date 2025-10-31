#!/usr/bin/env python3
"""
Glaze Dry Time Estimator — plain Python, functions only.
- Glaze types: normal / medium / fast
- Environments: basement / upstairs / outside
- Shapes: plate / mug / bowl / cylinder / vase / sculpture / unknown
- All dimensions in inches; temperature in °F
- Final estimate is rounded UP to the next whole hour
"""

import math

# -----------------------------
# Small input helpers
# -----------------------------
def prompt_choice(prompt, choices):
    menu = "/".join(choices)
    while True:
        val = input(f"{prompt} [{menu}]: ").strip().lower()
        if val in choices:
            return val
        print(f"Please enter one of: {menu}")

def prompt_int(prompt, min_val=None, max_val=None):
    # Whole-number input with basic range checks.
    while True:
        raw = input(f"{prompt}: ").strip()
        if raw.lstrip("-").isdigit():
            val = int(raw)
            if min_val is not None and val < min_val:
                print(f"Value must be ≥ {min_val}."); continue
            if max_val is not None and val > max_val:
                print(f"Value must be ≤ {max_val}."); continue
            return val
        print("Please enter a whole number.")

def prompt_float_pos(prompt, min_val=0.0, allow_zero=False):
    # Positive float input (optionally allowing zero). Friendly errors.
    while True:
        raw = input(f"{prompt}: ").strip()
        try:
            x = float(raw)
            if allow_zero:
                if x < min_val:
                    print(f"Value must be ≥ {min_val}."); continue
            else:
                if x <= min_val:
                    print(f"Value must be > {min_val}."); continue
            return x
        except ValueError:
            print("Please enter a number (e.g., 7 or 7.5).")

# -----------------------------
# Shape → area proxy (in²)
# -----------------------------
def area_proxy_square_inches(shape):
    """
    Super simple surface-area proxies to scale time.
    These are intentionally rough so the model stays transparent and easy to tweak.
    """
    if shape == "plate":
        d = prompt_float_pos("Plate diameter (inches)")
        return math.pi * (d / 2) ** 2  # top area as proxy

    if shape == "mug":
        h = prompt_float_pos("Mug height (inches)")
        d = prompt_float_pos("Mug outer diameter (inches)")
        # Side area approx + tiny base/lip allowance
        return math.pi * d * h * 0.9 + (math.pi * (d / 2) ** 2) * 0.1

    if shape == "bowl":
        d = prompt_float_pos("Bowl rim diameter (inches)")
        r = d / 2
        return 2 * math.pi * r * r  # hemisphere-ish

    if shape == "cylinder":
        h = prompt_float_pos("Cylinder height (inches)")
        d = prompt_float_pos("Cylinder diameter (inches)")
        return math.pi * d * h + (math.pi * (d / 2) ** 2)

    if shape == "vase":
        # Quick-and-clean frustum (tapered cylinder) proxy
        h  = prompt_float_pos("Vase height (inches)")
        d1 = prompt_float_pos("Top diameter (inches)")
        d2 = prompt_float_pos("Bottom diameter (inches)")
        r1, r2 = d1 / 2.0, d2 / 2.0
        s = math.sqrt((r2 - r1) ** 2 + h ** 2)    # slant height
        lateral = math.pi * (r1 + r2) * s         # lateral area
        bases   = math.pi * r2 * r2 * 0.4         # small base allowance
        return lateral + bases

    if shape == "sculpture":
        # Bounding-box surface area: easy to measure, conservative enough.
        L = prompt_float_pos("Sculpture length (inches)")
        W = prompt_float_pos("Sculpture width  (inches)")
        H = prompt_float_pos("Sculpture height (inches)")
        sa_box = 2 * (L*W + L*H + W*H)
        return sa_box * 0.9  # slight reduction for curved/organic shapes

    # Unknown/weird shape → longest dimension square-ish proxy
    L = prompt_float_pos("Longest outer dimension (inches)")
    return (L ** 2) * 0.8

# -----------------------------
# Core model
# -----------------------------
def estimate_hours(glaze_type, coats, environment, temp_f, shape):
    """
    time = k * area_proxy * coat_mult * glaze_mult * env_mult * temp_mult
    then +10% safety, min floor, and round UP to the next hour.
    """
    area_in2 = area_proxy_square_inches(shape)

    # Base constant (hours per square inch). Tuned to feel right in a studio.
    k = 0.11

    # Coats: first is baseline; each extra adds ~25% time.
    coat_mult = 1.0 + 0.25 * max(coats - 1, 0)

    # Glaze speed: small nudges (you said differences are minor).
    glaze_mult = {
        "fast":   0.93,
        "medium": 1.00,
        "normal": 1.05,
    }[glaze_type]

    # Environment: airflow + general drying vibe.
    env_mult = {
        "basement": 1.25,  # slow/stagnant air
        "upstairs": 1.00,  # baseline
        "outside":  0.85,  # breezy, faster
    }[environment]

    # Temperature (°F): relative to 72°F, ~0.5% per °F. Clamped to keep it sane.
    temp_mult = 1.0 - 0.005 * (temp_f - 72.0)
    temp_mult = max(0.75, min(1.25, temp_mult))

    base_hours = k * area_in2
    hours = base_hours * coat_mult * glaze_mult * env_mult * temp_mult

    # Safety buffer and minimum floor so tiny pieces don’t go to zero.
    hours *= 1.10
    hours = max(0.5, hours)

    # You asked to always round UP to the next whole hour.
    rounded_up = math.ceil(hours)

    breakdown = {
        "area_in2": round(area_in2, 1),
        "base_hours": round(base_hours, 2),
        "coat_mult": round(coat_mult, 2),
        "glaze_mult": round(glaze_mult, 2),
        "env_mult": round(env_mult, 2),
        "temp_mult": round(temp_mult, 2),
        "pre_round_hours": round(hours, 2),
        "final_hours": int(rounded_up),
    }
    return rounded_up, breakdown

# -----------------------------
# CLI flow (one Q at a time)
# -----------------------------
def main():
    print("Glaze Dry Time Estimator\n")

    # Ask the non-geometry stuff first (per your request).
    glaze = prompt_choice("Glaze drying type", ["normal", "medium", "fast"])
    coats = prompt_int("Number of coats (whole number)", min_val=1)
    env   = prompt_choice("Environment", ["basement", "upstairs", "outside"])
    tempf = prompt_float_pos("Temperature (°F)", min_val=-50, allow_zero=True)

    # Now pick the piece likely to be the slowest and grab its dims.
    shape = prompt_choice(
        "Shape (pick the piece likely to take the longest)",
        ["plate", "mug", "bowl", "cylinder", "vase", "sculpture", "unknown"],
    )

    final_hours, info = estimate_hours(glaze, coats, env, tempf, shape)

    print("\n=== Estimate ===")
    print(f"Estimated drying time: {final_hours} hours (rounded up)")
    print("\nBreakdown")
    for k, v in info.items():
        label = k.replace("_", " ")
        print(f"  {label:16s}: {v}")
    print("\nNote: Simple proxy model. Tweak constants if your studio runs hotter/colder or your coats are heavier.")

if __name__ == "__main__":
    main()

