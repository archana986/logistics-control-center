from __future__ import annotations

import random
from typing import Any

SUBREGION_BANDS: dict[str, dict[str, Any]] = {
    "RhineRuhr": {
        "label": "Rhine-Ruhr Corridor",
        "facilities": [
            ("Leuna", 51.3167, 12.0167),
            ("Dormagen", 51.0964, 6.8317),
            ("Sluiskil", 51.2750, 3.8417),
        ],
        "customers": [
            ("Ludwigshafen", 49.4774, 8.4452),
            ("Cologne", 50.9375, 6.9603),
            ("Rotterdam", 51.9225, 4.4792),
        ],
    },
    "WesternEurope": {
        "label": "Western Europe",
        "facilities": [
            ("Chalampé", 47.8167, 7.5667),
            ("Krakow", 50.0647, 19.9450),
            ("Fos-sur-Mer", 43.4377, 4.9444),
        ],
        "customers": [
            ("Lyon", 45.7640, 4.8357),
            ("Versailles", 48.8046, 2.1206),
            ("Dunkirk", 51.0343, 2.3768),
        ],
    },
    "CentralEurope": {
        "label": "Alpine & Iberia Corridor",
        "facilities": [
            ("Zurich", 47.3769, 8.5417),
            ("Linz", 48.3069, 14.2858),
            ("Antwerp", 51.2213, 4.4051),
        ],
        "customers": [
            ("Barcelona", 41.3874, 2.1686),
            ("Eindhoven", 51.4416, 5.4697),
            ("Saint-Denis", 48.9333, 2.3583),
        ],
    },
}

INDUSTRIES = [
    "Semiconductor",
    "Healthcare",
    "Refining",
    "Chemicals",
    "Aerospace",
    "Food & Beverage",
    "Steel",
    "Mining",
]
TIERS = ["Strategic", "Enterprise", "Merchant"]
PRODUCTS = ["LIN", "LOX", "LAR"]
CUSTOMERS_BY_INDUSTRY: dict[str, list[str]] = {
    "Semiconductor": [
        "ASML Lithography",
        "Infineon Technologies",
        "STMicroelectronics",
    ],
    "Healthcare": [
        "Hospital Clínic de Barcelona",
        "Charité Universitätsmedizin Berlin",
        "Assistance Publique-Hôpitaux de Paris",
        "Szpital Kliniczny Kraków",
    ],
    "Refining": [
        "TotalEnergies Refining",
        "Shell Pernis Refinery",
        "OMV Downstream",
    ],
    "Chemicals": [
        "BASF",
        "Evonik Industries",
        "Solvay",
    ],
    "Aerospace": [
        "Airbus Operations",
        "Safran Propulsion",
        "ESA Launch Services",
    ],
    "Food & Beverage": [
        "Nestlé Europe",
        "Danone Dairy",
        "Carlsberg Brewing",
        "Unilever Foods",
    ],
    "Steel": [
        "H2 Green Steel",
        "ThyssenKrupp Steel",
        "ArcelorMittal Europe",
    ],
    "Mining": [
        "KGHM Polska Miedź",
        "Tauron Mining",
        "K+S Potash",
    ],
}


def _jittered_point(rng: random.Random, lat: float, lng: float, lat_spread: float, lng_spread: float) -> tuple[float, float]:
    return round(lat + rng.uniform(-lat_spread, lat_spread), 4), round(lng + rng.uniform(-lng_spread, lng_spread), 4)


def _distance_score(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    # Fast planar score is sufficient for relative ordering.
    return (lat1 - lat2) ** 2 + (lng1 - lng2) ** 2


def generate_dim_assets_rows(cfg) -> list[dict[str, Any]]:
    rng = random.Random(cfg.seed + 11)
    rows: list[dict[str, Any]] = []
    band_keys = list(SUBREGION_BANDS.keys())
    band_counts: dict[str, int] = {k: 0 for k in band_keys}
    for idx in range(1, cfg.num_assets + 1):
        band_key = band_keys[(idx - 1) % len(band_keys)]
        band = SUBREGION_BANDS[band_key]
        local_idx = band_counts[band_key]
        band_counts[band_key] += 1
        anchor_name, base_lat, base_lng = band["facilities"][local_idx % len(band["facilities"])]
        lat, lng = _jittered_point(rng, base_lat, base_lng, lat_spread=0.22, lng_spread=0.28)
        max_capacity = rng.randint(500, 2000)
        min_run_rate = min(rng.randint(100, 400), max_capacity - 30)
        is_primary_hub = (idx - 1) % len(band_keys) == 0
        asset_commission_year = rng.randint(1998, 2024)
        depreciation_years = rng.choice([15, 18, 20])
        overbuild_ratio = round(rng.uniform(1.08, 1.38), 3)
        capex_usd = round(max_capacity * rng.uniform(25_000.0, 90_000.0), 2)
        rows.append(
            {
                "asset_id": f"ASU-{idx:03d}",
                "asset_name": f"{anchor_name} ASU {idx:03d}",
                "region": band["label"],
                "subregion": band_key,
                "is_primary_hub": is_primary_hub,
                "lat": lat,
                "lng": lng,
                "max_capacity_tpd": max_capacity,
                "min_run_rate_tpd": min_run_rate,
                "base_specific_energy_kwh": rng.randint(200, 300),
                "asset_commission_year": asset_commission_year,
                "depreciation_years": depreciation_years,
                "overbuild_ratio": overbuild_ratio,
                "capex_usd": capex_usd,
            }
        )
    return rows


def generate_dim_customers_rows(cfg) -> list[dict[str, Any]]:
    rng = random.Random(cfg.seed + 23)
    rows: list[dict[str, Any]] = []
    band_keys = list(SUBREGION_BANDS.keys())
    band_counts: dict[str, int] = {k: 0 for k in band_keys}
    industry_counts: dict[str, int] = {k: 0 for k in INDUSTRIES}
    for idx in range(1, cfg.num_customers + 1):
        band_key = band_keys[(idx - 1) % len(band_keys)]
        band = SUBREGION_BANDS[band_key]
        industry = INDUSTRIES[(idx - 1) % len(INDUSTRIES)]
        customer_pool = CUSTOMERS_BY_INDUSTRY.get(industry, ["Industrial Customer"])
        industry_local_idx = industry_counts[industry]
        industry_counts[industry] += 1
        account_name = customer_pool[industry_local_idx % len(customer_pool)]
        tier_roll = rng.random()
        tier = "Strategic" if tier_roll < 0.1 else ("Enterprise" if tier_roll < 0.4 else "Merchant")
        local_idx = band_counts[band_key]
        band_counts[band_key] += 1
        anchor_name, base_lat, base_lng = band["customers"][local_idx % len(band["customers"])]
        lat, lng = _jittered_point(rng, base_lat, base_lng, lat_spread=0.20, lng_spread=0.26)
        rows.append(
            {
                "customer_id": f"CUST-{idx:04d}",
                "customer_name": f"{account_name} - {anchor_name} Site",
                "contact_email": f"ops+{idx:04d}@example.com",
                "industry": industry,
                "tier": tier,
                "region": band["label"],
                "subregion": band_key,
                "lat": lat,
                "lng": lng,
            }
        )
    return rows


TECHNICIAN_NAMES = [
    "Hans Müller", "Ingrid Bauer", "Stefan Kovacs", "Marie Dupont", "Klaus Richter",
    "Eva Novak", "Thomas Schmidt", "Anna Bergström", "Peter Jansen", "Liesel Hoff",
    "Henrik Olsen", "Marta Wiśniewska", "Franz Keller", "Sophie Laurent", "Erik Lindqvist",
    "Renata Horváth", "Dieter Braun", "Claudia Rossi", "Jan de Vries", "Helena Petrova",
    "Wilhelm Stark", "Brigitte Lemaire", "Karel Novotný", "Astrid Holm", "Luca Ferri",
    "Katarina Szabó", "Rolf Andersen", "Nadia Popescu", "Friedrich Weber", "Elise Moreau",
    "Gustav Persson", "Zuzana Králová", "Marco Bianchi", "Petra Engel", "Miloš Jovanović",
    "Dorothea Klein", "Tomáš Havel", "Isabella Conti", "Lars Thorsen", "Monika Stein",
    "Alois Gruber", "Françoise Girard", "Jiří Malý", "Carmen Vega", "Piotr Kowalski",
]

TECHNICIAN_ROLES = [
    "Compressor Specialist",
    "Instrument Technician",
    "Reliability Engineer",
    "Vibration Analyst",
    "Field Technician",
    "Electrical Technician",
]

PART_TYPES = [
    ("COMP-BRG", "Compressor Bearing Assembly", "Rotating Equipment"),
    ("COMP-VLV", "Compressor Intake Valve", "Rotating Equipment"),
    ("INST-PRS", "Pressure Transmitter", "Instrumentation"),
    ("INST-TMP", "Thermocouple Assembly", "Instrumentation"),
    ("ELEC-VFD", "Variable Frequency Drive Module", "Electrical"),
    ("ELEC-CTR", "Motor Control Contactor", "Electrical"),
    ("PIPING-GK", "Cryogenic Gasket Set", "Piping"),
    ("PIPING-VLV", "Cryogenic Globe Valve", "Piping"),
]

VENDOR_LOCATIONS = [
    ("AirLiquide Zurich", 47.3769, 8.5417),
    ("Messer Lyon", 45.7640, 4.8357),
    ("Nippon Gases Antwerp", 51.2213, 4.4051),
    ("SOL Group Barcelona", 41.3874, 2.1686),
    ("SIAD Milano", 45.4642, 9.1900),
    ("Westfalen Düsseldorf", 51.2277, 6.7735),
    ("Linde Gas Praha", 50.0755, 14.4378),
    ("Air Products Münster", 51.9607, 7.6261),
]

VENDOR_PRODUCTS = [
    ["LIN", "LOX"],
    ["LIN", "LOX", "LAR"],
    ["LIN", "LAR"],
    ["LOX", "LAR"],
    ["LIN", "LOX"],
    ["LIN", "LOX", "LAR"],
    ["LOX"],
    ["LIN", "LOX"],
]


def generate_dim_technicians_rows(cfg, asset_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(cfg.seed + 51)
    rows: list[dict[str, Any]] = []
    name_pool = list(TECHNICIAN_NAMES)
    rng.shuffle(name_pool)
    name_idx = 0
    for asset in asset_rows:
        for t_idx in range(cfg.num_technicians_per_asset):
            name = name_pool[name_idx % len(name_pool)]
            name_idx += 1
            role = TECHNICIAN_ROLES[(t_idx + hash(asset["asset_id"])) % len(TECHNICIAN_ROLES)]
            cert_level = rng.choice(["Level I", "Level II", "Level III"])
            available = rng.random() < 0.70
            rows.append({
                "tech_id": f"TECH-{asset['asset_id'][-3:]}-{t_idx + 1:02d}",
                "name": name,
                "role": role,
                "asset_id": asset["asset_id"],
                "region": asset["region"],
                "available": available,
                "certification_level": cert_level,
            })
    return rows


def generate_dim_parts_inventory_rows(cfg, asset_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(cfg.seed + 63)
    rows: list[dict[str, Any]] = []
    for asset in asset_rows:
        asset_num = int(asset["asset_id"].split("-")[1])
        stock_modifier = 0.5 if asset_num <= 4 else 1.0
        for p_idx, (sku_prefix, part_name, category) in enumerate(PART_TYPES):
            qty_on_hand = max(0, int(rng.randint(0, 8) * stock_modifier))
            rows.append({
                "part_id": f"PART-{asset['asset_id'][-3:]}-{p_idx + 1:02d}",
                "sku": f"{sku_prefix}-{asset['asset_id'][-3:]}",
                "name": part_name,
                "category": category,
                "asset_id": asset["asset_id"],
                "qty_on_hand": qty_on_hand,
                "qty_needed": rng.choice([1, 1, 1, 2]),
                "lead_time_days": rng.randint(0, 14),
            })
    return rows


def generate_dim_vendors_rows(cfg) -> list[dict[str, Any]]:
    rng = random.Random(cfg.seed + 77)
    rows: list[dict[str, Any]] = []
    for v_idx in range(min(cfg.num_vendors, len(VENDOR_LOCATIONS))):
        name, lat, lng = VENDOR_LOCATIONS[v_idx]
        products = VENDOR_PRODUCTS[v_idx]
        rows.append({
            "vendor_id": f"VEND-{v_idx + 1:03d}",
            "name": name,
            "lat": lat,
            "lng": lng,
            "products": ",".join(products),
            "capacity_tpd": rng.randint(30, 80),
            "price_premium_pct": round(rng.uniform(5.0, 25.0), 1),
            "eta_hours": round(rng.uniform(4.0, 18.0), 1),
        })
    return rows


def generate_dim_contracts_rows(cfg, asset_rows: list[dict[str, Any]], customer_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(cfg.seed + 37)
    priority_rng = random.Random(cfg.seed + 73)
    assets_by_subregion: dict[str, list[dict[str, Any]]] = {}
    for asset in asset_rows:
        assets_by_subregion.setdefault(asset["subregion"], []).append(asset)
    contract_indices = list(range(1, cfg.num_contracts + 1))
    priority_rng.shuffle(contract_indices)
    critical_count = min(2, cfg.num_contracts)
    remaining_after_critical = max(0, cfg.num_contracts - critical_count)
    watch_count = min(max(5, cfg.num_contracts // 6), remaining_after_critical)
    critical_indices = set(contract_indices[:critical_count])
    watch_indices = set(contract_indices[critical_count : critical_count + watch_count])

    def choose_asset_for_customer(customer: dict[str, Any], contract_idx: int) -> dict[str, Any]:
        subregion_assets = assets_by_subregion.get(customer["subregion"]) or asset_rows
        primary_hubs = [a for a in subregion_assets if a.get("is_primary_hub")]
        primary_hub = primary_hubs[0] if primary_hubs else subregion_assets[0]
        nearest_asset = min(
            subregion_assets,
            key=lambda a: _distance_score(
                float(a["lat"]),
                float(a["lng"]),
                float(customer["lat"]),
                float(customer["lng"]),
            ),
        )
        # Backbone contracts originate from hub; branch contracts use nearest asset.
        if contract_idx % 3 == 0:
            return primary_hub
        return nearest_asset

    rows: list[dict[str, Any]] = []
    for idx in range(1, cfg.num_contracts + 1):
        customer = customer_rows[(idx - 1) % len(customer_rows)]
        selected_asset = choose_asset_for_customer(customer, idx)
        asset_id = selected_asset["asset_id"]
        industry = customer["industry"]
        dist_score = _distance_score(
            float(selected_asset["lat"]),
            float(selected_asset["lng"]),
            float(customer["lat"]),
            float(customer["lng"]),
        )
        pipeline_industries = {"Refining", "Chemicals", "Steel", "Mining"}
        PIPELINE_DIST_THRESHOLD = 1.5  # low dist_score = short distance
        mode = "pipeline" if industry in pipeline_industries and dist_score < PIPELINE_DIST_THRESHOLD else "truck"
        product = PRODUCTS[(idx - 1) % len(PRODUCTS)]
        story_chain = (idx - 1) % 9
        if idx in critical_indices:
            lane_priority = "critical"
        elif idx in watch_indices:
            lane_priority = "watch"
        else:
            lane_priority = "stable"
        lane_id = f"{asset_id}-{customer['customer_id']}-{product}"
        is_anchor_pipeline = mode == "pipeline" and (lane_priority == "critical" or rng.random() < 0.45)
        contract_type = "anchor_pipeline" if is_anchor_pipeline else "merchant_bulk"
        if contract_type == "anchor_pipeline":
            take_or_pay_min_tpd = rng.randint(35, 140)
            price_per_ton_usd = round(rng.uniform(95.0, 165.0), 2)
            energy_pass_through_pct = round(rng.uniform(0.75, 0.95), 3)
            overage_price_multiplier = round(rng.uniform(1.02, 1.08), 3)
            contract_term_years = rng.choice([15, 18, 20])
        else:
            take_or_pay_min_tpd = rng.randint(8, 70)
            price_per_ton_usd = round(rng.uniform(130.0, 285.0), 2)
            energy_pass_through_pct = round(rng.uniform(0.15, 0.50), 3)
            overage_price_multiplier = round(rng.uniform(1.12, 1.35), 3)
            contract_term_years = rng.choice([3, 5, 7, 10])
        rows.append(
            {
                "contract_id": f"CTR-{idx:04d}",
                "lane_id": lane_id,
                "customer_id": customer["customer_id"],
                "asset_id": asset_id,
                "product": product,
                "mode": mode,
                "contract_type": contract_type,
                "contract_term_years": contract_term_years,
                "take_or_pay_min_tpd": take_or_pay_min_tpd,
                "price_per_ton_usd": price_per_ton_usd,
                "energy_pass_through_pct": energy_pass_through_pct,
                "overage_price_multiplier": overage_price_multiplier,
                "ld_penalty_rate_usd": rng.choice([10000, 50000, 100000]),
                "story_chain_id": f"CHAIN-{story_chain:02d}",
                "lane_priority": lane_priority,
            }
        )

    # Capacity-aware scaling: total contracted demand per asset ~85-105% of expected supply
    asset_to_capacity = {a["asset_id"]: a["max_capacity_tpd"] for a in asset_rows}
    by_asset: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_asset.setdefault(row["asset_id"], []).append(row)
    for asset_id, contract_rows in by_asset.items():
        current_sum = sum(r["take_or_pay_min_tpd"] for r in contract_rows)
        if current_sum <= 0:
            continue
        capacity = asset_to_capacity.get(asset_id, 1000)
        expected_supply = capacity * 0.6  # typical utilization
        target_total = expected_supply * rng.uniform(0.85, 1.05)
        scale = target_total / current_sum
        for r in contract_rows:
            raw = max(5, round(r["take_or_pay_min_tpd"] * scale))
            r["take_or_pay_min_tpd"] = raw

    return rows

