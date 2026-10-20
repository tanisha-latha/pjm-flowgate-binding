from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
CHARTS = ROOT / "charts"

# train on everything before this, score on everything after
SPLIT = "2025-09-01"

# a congested hour = the congestion spread across the area is above this ($/MWh)
THRESHOLD = 10.0
THRESHOLDS = [5.0, 10.0, 20.0]

# each area is a pair of pricing nodes on either side of the congestion.
# spread = congestion price at `rich` minus `cheap`, so a positive spread means
# power wants to flow from the cheap side to the rich side and can't.
AREAS = {
    "baltimore": {"rich": "BGE_RESID_AGG", "cheap": "PECO_RESID_AGG", "label": "Baltimore (BGE over PECO)"},
    "richmond": {"rich": "DOM_RESID_AGG", "cheap": "SOUTH", "label": "Richmond (Dominion over SOUTH)"},
    "chicago": {"rich": "WESTERN HUB", "cheap": "COMED_RESID_AGG", "label": "Chicago (Western Hub over ComEd)"},
}

# load zones as named in PJM's hrl_load_metered feed
ZONES = {
    "BC Zone": "bge", "PE Zone": "peco", "ME Zone": "meted", "AE Zone": "aeco",
    "DOM Zone": "dom", "COMED Zone": "comed", "AEP Zone": "aep", "APS Zone": "aps",
    "PJM RTO Total": "rto", "Mid-Atlantic Region": "midatl_region",
    "Southern Region": "south_region", "Western Region": "west_region",
}

# rough centres for the EIA retirement check
CITIES = {"baltimore": (39.29, -76.61), "richmond": (37.54, -77.44), "chicago": (41.88, -87.63)}
RADIUS_MILES = 60

# chart colours
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
AREA_COLOURS = {"baltimore": BLUE, "richmond": ORANGE, "chicago": AQUA}
YEAR_COLOURS = {2024: "#86b6ef", 2025: "#2a78d6", 2026: "#104281"}
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
