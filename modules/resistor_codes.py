"""Pure four-band resistor decoding; camera recognition remains experimental."""
DIGITS = dict(zip(["black", "brown", "red", "orange", "yellow", "green", "blue", "violet", "gray", "white"], range(10)))
MULTIPLIERS = {**{k: 10**v for k, v in DIGITS.items()}, "gold": 0.1, "silver": 0.01}
TOLERANCE = {"brown": 1, "red": 2, "green": 0.5, "blue": 0.25, "violet": 0.1, "gray": 0.05, "gold": 5, "silver": 10}

def decode_bands(bands):
    if len(bands) != 4:
        return None
    first, second, multiplier, tolerance = bands
    if first not in DIGITS or first == "black" or second not in DIGITS:
        return None
    if multiplier not in MULTIPLIERS or tolerance not in TOLERANCE:
        return None
    return (10*DIGITS[first] + DIGITS[second])*MULTIPLIERS[multiplier], TOLERANCE[tolerance]

def format_ohms(value):
    if value >= 1_000_000:
        return f"{value / 1_000_000:g} mega-ohm"
    if value >= 1_000:
        return f"{value / 1_000:g} kilo-ohm"
    return f"{value:g} ohm"
