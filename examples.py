"""Preset problems used by the solver pages, the home page and the Learn lessons.

Every value here has been checked against OTTools 0.1.3.
"""

# rows: [coefficients..., type, rhs] with type one of "≤", "≥", "="
LP_EXAMPLES = {
    "Glass factory · max, 2 variables": {
        "sense": "Maximize",
        "c": [3, 5],
        "rows": [[1, 0, "≤", 4], [0, 2, "≤", 12], [3, 2, "≤", 18]],
        "method": "Graphical",
        "answer": "Z = 36 at x₁ = 2, x₂ = 6",
    },
    "Mixed constraints · min, ≥ and =": {
        "sense": "Minimize",
        "c": [4, 1],
        "rows": [[3, 1, "=", 3], [4, 3, "≥", 6], [1, 2, "≤", 4]],
        "method": "Big M",
        "answer": "Z = 3.4 at x₁ = 0.4, x₂ = 1.8",
    },
    "Whole units only · max, integer": {
        "sense": "Maximize",
        "c": [5, 4],
        "rows": [[6, 4, "≤", 24], [1, 2, "≤", 6]],
        "method": "Integer",
        "answer": "Z = 20 at x₁ = 4, x₂ = 0 (the LP relaxation gives 21)",
    },
    "Three products · max, 3 variables": {
        "sense": "Maximize",
        "c": [3, 2, 5],
        "rows": [[1, 2, 1, "≤", 430], [3, 0, 2, "≤", 460], [1, 4, 0, "≤", 420]],
        "method": "Simplex",
        "answer": "Z = 1350 at x = (0, 100, 230)",
    },
}

TP_EXAMPLES = {
    "Classic 3×4 · balanced": {
        "cost": [[19, 30, 50, 10], [70, 30, 40, 60], [40, 8, 70, 20]],
        "supply": [7, 9, 18],
        "demand": [5, 8, 7, 14],
        "method": "VAM",
    },
    "Warehouses · extra supply (dummy destination)": {
        "cost": [[4, 8, 8], [16, 24, 16], [8, 16, 24]],
        "supply": [76, 82, 77],
        "demand": [72, 102, 41],
        "method": "MODI",
    },
    "Factories · extra demand (dummy source)": {
        "cost": [[2, 3, 11, 7], [1, 0, 6, 1], [5, 8, 15, 9]],
        "supply": [6, 1, 10],
        "demand": [7, 5, 3, 4],
        "method": "VAM",
    },
}

DEFAULT_LP = "Glass factory · max, 2 variables"
DEFAULT_TP = "Classic 3×4 · balanced"
