"""
Step 1: Create data for Flipp Deal-Finder Agent.

Generates structured data per prompts/cursor_generatedata.md:
1. Retailers, stores, trade_areas (geospatial / "near me")
2. Categories, products, product_retailer_map (catalog & taxonomy)
3. Users, sessions, events (anonymized telemetry)
4. Store_visits, conversion_proxies (aggregated / conversion)
5. Deals (synthetic deals catalog)
6. Flyer PDFs + JSON examples are produced by generate_flyer_pdfs.py (data/flyers/);
   they are uploaded in Step 2.

All structured data is written as parquet under Unity Catalog Volume raw_data.
Run on a Databricks cluster (Spark available). Config: conf/catalog_config.py.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

# Add project root for config (Databricks notebook-safe)
SCRIPT_DIR = Path.cwd()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
PROJECT_ROOT = SCRIPT_DIR.parent

from conf.catalog_config import CATALOG, SCHEMA, VOLUME_RAW, VOLUME_PATH_RAW

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.types import ArrayType, MapType, StringType, StructType, StructField, IntegerType

SEED = 42
np.random.seed(SEED)

# Deal catalog (existing)
N_DEALS = 5000
N_RETAILERS = 20

# cursor_generatedata.md: ~20 retailers; ~500–2,000 stores
N_STORES = 800
N_TRADE_AREAS_PER_STORE = 2  # ~1600 trade_areas

# Product catalog: 50k–150k products → demo 12k; category tree depth 3–5
N_CATEGORIES = 200
N_PRODUCTS = 12000
N_PRODUCT_RETAILER_MAP = 25000

# Users and telemetry: "lite" 2–5M events → demo ~100k events
N_USERS = 4000
N_SESSIONS = 15000
N_EVENTS = 100000

# Store visits: one row per store per day over date range; conversion_proxies subset
DAYS_STORE_VISITS = 60
N_CONVERSION_PROXIES = 8000

# Date ranges
END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=180)
DEAL_START = END_DATE
DEAL_END = END_DATE + timedelta(days=14)

# Synthetic retailers (Flipp-style)
RETAILER_NAMES = [
    "Metro Plus", "FreshCo Weekly", "No Frills", "Walmart", "Kroger", "Lowe's", "Home Depot",
    "Loblaws", "Sobeys", "Food Basics", "Giant Tiger", "Canadian Tire", "Costco", "Real Canadian Superstore",
    "Shoppers Drug Mart", "Rexall", "Dollarama", "Target", "Whole Foods", "Save-On-Foods",
]

VERTICALS = ["grocery", "grocery", "grocery", "general_merch", "grocery", "home", "home", "grocery", "grocery", "grocery", "general_merch", "general_merch", "warehouse", "grocery", "pharmacy", "pharmacy", "general_merch", "general_merch", "grocery", "grocery"]
TIERS = ["premium", "standard", "value", "premium", "premium", "premium", "premium", "premium", "standard", "value", "value", "standard", "premium", "standard", "standard", "standard", "value", "standard", "premium", "standard"]

# Product categories for deals and taxonomy
CATEGORIES_NAMES = [
    "Meat & Poultry", "Frozen", "Bakery", "Deli", "Pantry", "Snacks", "Dairy & Deli",
    "Beverages", "Produce", "Dairy", "Household", "Personal Care", "Baby", "Pet",
]

PRODUCT_NAMES = [
    "Chicken Wings", "Ground Beef", "Pork Chops", "Marinated Chicken", "Beef Burger",
    "French Fries", "Ice Cream", "Pizza", "Appetizers", "Frozen Vegetables",
    "Sliced Bread", "Buns", "Bagels", "Croissants", "Muffins",
    "Frankfurters", "Deli Ham", "Cheese Slices", "Hummus", "Dips",
    "Pasta", "Rice", "Cereal", "Condiments", "Canned Soup", "Olive Oil",
    "Chips", "Crackers", "Cookies", "Nuts", "Granola Bars",
    "Milk", "Yogurt", "Butter", "Eggs", "Cream Cheese",
    "Soft Drinks", "Juice", "Water", "Coffee", "Tea",
    "Apples", "Bananas", "Salad Kit", "Tomatoes", "Potatoes", "Onions",
    "Laundry Detergent", "Paper Towels", "Dish Soap", "Trash Bags",
    "Shampoo", "Soap", "Toothpaste", "Deodorant", "Sunscreen",
]

EVENT_TYPES = ["search", "view_offer", "add_to_list", "clip_coupon", "share", "open_circular", "store_select"]
CONVERSION_ACTIONS = ["add_to_list", "coupon_clip", "redemption"]

# Canadian-style cities and provinces for stores
CITIES = ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Edmonton", "Mississauga", "Winnipeg", "Brampton", "Hamilton", "Quebec City", "Surrey", "Laval", "Halifax", "London"]
STATE_PROV = ["ON", "BC", "QC", "AB", "ON", "AB", "ON", "MB", "ON", "ON", "QC", "BC", "QC", "NS", "ON"]


def get_spark() -> SparkSession:
    return SparkSession.builder.getOrCreate()


def create_infrastructure(spark: SparkSession) -> None:
    catalogs = [row.catalog for row in spark.sql("SHOW CATALOGS").collect()]
    if CATALOG not in catalogs:
        raise ValueError(
            f"Catalog '{CATALOG}' does not exist. Create it first (e.g. CREATE CATALOG {CATALOG};)"
        )
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME_RAW}")


def _hash_id(s: str, salt: str = "flipp") -> str:
    return hashlib.sha256(f"{salt}{s}".encode()).hexdigest()[:16]


# -----------------------------------------------------------------------------
# 1. RETAILERS (retailer_id, name, tier, region, partner_since, vertical)
# -----------------------------------------------------------------------------
def generate_retailers(spark: SparkSession) -> pd.DataFrame:
    rows = []
    for i in range(N_RETAILERS):
        name = RETAILER_NAMES[i] if i < len(RETAILER_NAMES) else f"Retailer_{i+1}"
        rows.append({
            "retailer_id": f"R{i+1:04d}",
            "name": name,
            "tier": TIERS[i] if i < len(TIERS) else np.random.choice(["premium", "standard", "value"]),
            "region": np.random.choice(["North", "South", "East", "West"], p=[0.3, 0.25, 0.25, 0.2]),
            "partner_since": (START_DATE + timedelta(days=np.random.randint(0, 1600))).strftime("%Y-%m-%d"),
            "vertical": VERTICALS[i] if i < len(VERTICALS) else "grocery",
        })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# 2. STORES (store_id, retailer_id, address, city, state_prov, postal_code, lat, lon, hours, services)
# -----------------------------------------------------------------------------
def generate_stores(spark: SparkSession, retailers_pdf: pd.DataFrame) -> pd.DataFrame:
    retailer_ids = retailers_pdf["retailer_id"].tolist()
    rows = []
    for i in range(N_STORES):
        rid = np.random.choice(retailer_ids)
        ci = np.random.randint(0, len(CITIES))
        city = CITIES[ci]
        state = STATE_PROV[ci]
        postal = f"{np.random.randint(1, 9)}{np.random.randint(0, 9)}{np.random.randint(0, 9)} {np.random.randint(0, 9)}{np.random.randint(0, 9)}{np.random.randint(0, 9)}"
        lat = 43 + np.random.uniform(-5, 5)
        lon = -79 + np.random.uniform(-8, 8)
        rows.append({
            "store_id": f"S{i+1:06d}",
            "retailer_id": rid,
            "address": f"{100 + np.random.randint(0, 9900)} {city} St",
            "city": city,
            "state_prov": state,
            "postal_code": postal,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "hours": "07:00-22:00",
            "services": "pharmacy, pickup" if np.random.random() > 0.5 else "pickup",
        })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# 3. TRADE_AREAS (store_id, geo_hash, dma, census_block_group, population, median_income)
# -----------------------------------------------------------------------------
def generate_trade_areas(spark: SparkSession, stores_pdf: pd.DataFrame) -> pd.DataFrame:
    store_ids = stores_pdf["store_id"].tolist()
    rows = []
    for sid in store_ids:
        for _ in range(N_TRADE_AREAS_PER_STORE):
            rows.append({
                "store_id": sid,
                "geo_hash": _hash_id(sid + str(np.random.randint(0, 10))),
                "dma": f"DMA_{np.random.randint(1, 50):03d}",
                "census_block_group": f"CBG_{np.random.randint(10000, 99999)}",
                "population": int(np.random.lognormal(9, 0.5)),
                "median_income": int(np.random.lognormal(10.5, 0.3)),
            })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# 4. CATEGORIES (category_id, path, depth, synonyms ARRAY<string>)
# -----------------------------------------------------------------------------
def generate_categories(spark: SparkSession) -> pd.DataFrame:
    paths = []
    depth_map = {}
    for i in range(N_CATEGORIES):
        depth = min(5, 1 + (i % 5))
        parent = f"cat_{(i // 20):04d}" if depth > 1 else "root"
        path = f"{parent}/{CATEGORIES_NAMES[i % len(CATEGORIES_NAMES)].replace(' ', '_').lower()}_{i}"
        paths.append((f"cat_{i:05d}", path, depth))
        depth_map[f"cat_{i:05d}"] = depth
    rows = []
    for cid, path, depth in paths:
        synonyms = [path.split("/")[-1].replace("_", " "), path.split("/")[-1][:8]]
        rows.append({
            "category_id": cid,
            "path": path,
            "depth": depth,
            "synonyms": synonyms,
        })
    pdf = pd.DataFrame(rows)
    # Spark needs ArrayType; write as list column
    return pdf


# -----------------------------------------------------------------------------
# 5. PRODUCTS (product_id, upc_gtin, brand, title, size, unit, category_id, attributes MAP)
# -----------------------------------------------------------------------------
def generate_products(spark: SparkSession, categories_pdf: pd.DataFrame) -> pd.DataFrame:
    cat_ids = categories_pdf["category_id"].tolist()
    brands = ["Store Brand", "Name Brand", "Premium", "Selection", "No Name", "Irresistible"]
    units = ["each", "per lb", "per kg", "bunch", "bag", "box", "bottle"]
    rows = []
    for i in range(N_PRODUCTS):
        title = np.random.choice(PRODUCT_NAMES) + (" " + str(np.random.randint(1, 5)) if np.random.random() > 0.6 else "")
        rows.append({
            "product_id": f"P{i+1:07d}",
            "upc_gtin": str(100000000000 + i),
            "brand": np.random.choice(brands, p=[0.35, 0.25, 0.15, 0.1, 0.1, 0.05]),
            "title": title,
            "size": f"{np.random.choice([250, 500, 750, 1, 2])} {np.random.choice(['g', 'ml', 'L', 'kg'])}",
            "unit": np.random.choice(units, p=[0.4, 0.15, 0.1, 0.1, 0.1, 0.1, 0.05]),
            "category_id": np.random.choice(cat_ids),
            "attributes": {"organic": "false", "format": np.random.choice(["frozen", "fresh", "shelf"])},
        })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# 6. PRODUCT_RETAILER_MAP (product_id, retailer_id, retailer_sku)
# -----------------------------------------------------------------------------
def generate_product_retailer_map(
    spark: SparkSession, products_pdf: pd.DataFrame, retailers_pdf: pd.DataFrame
) -> pd.DataFrame:
    product_ids = products_pdf["product_id"].tolist()
    retailer_ids = retailers_pdf["retailer_id"].tolist()
    rows = []
    seen = set()
    for _ in range(N_PRODUCT_RETAILER_MAP):
        pid = np.random.choice(product_ids)
        rid = np.random.choice(retailer_ids)
        key = (pid, rid)
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "product_id": pid,
            "retailer_id": rid,
            "retailer_sku": f"SKU-{pid}-{rid}-{np.random.randint(1, 999)}",
        })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# 7. USERS (user_id_hash, cohort, home_postal, device_type, signup_date, marketing_opt_in)
# -----------------------------------------------------------------------------
def generate_users(spark: SparkSession) -> pd.DataFrame:
    rows = []
    for i in range(N_USERS):
        uid = f"user_{i:06d}"
        rows.append({
            "user_id_hash": _hash_id(uid),
            "cohort": np.random.choice(["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"], p=[0.2, 0.25, 0.3, 0.25]),
            "home_postal": f"{np.random.randint(1, 9)}{np.random.randint(0, 9)}{np.random.randint(0, 9)} {np.random.randint(0, 9)}{np.random.randint(0, 9)}{np.random.randint(0, 9)}",
            "device_type": np.random.choice(["ios", "android", "web"], p=[0.45, 0.45, 0.1]),
            "signup_date": (START_DATE + timedelta(days=np.random.randint(0, 150))).strftime("%Y-%m-%d"),
            "marketing_opt_in": bool(np.random.random() > 0.4),
        })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# 8. SESSIONS (session_id, user_id_hash, ts_start, ts_end, source, ab_group)
# -----------------------------------------------------------------------------
def generate_sessions(spark: SparkSession, users_pdf: pd.DataFrame) -> pd.DataFrame:
    user_hashes = users_pdf["user_id_hash"].tolist()
    rows = []
    for i in range(N_SESSIONS):
        uh = np.random.choice(user_hashes)
        ts_start = START_DATE + timedelta(
            days=np.random.randint(0, 170),
            seconds=np.random.randint(0, 86400),
        )
        ts_end = ts_start + timedelta(seconds=np.random.randint(60, 3600))
        rows.append({
            "session_id": f"sess_{i:08d}",
            "user_id_hash": uh,
            "ts_start": ts_start.strftime("%Y-%m-%d %H:%M:%S"),
            "ts_end": ts_end.strftime("%Y-%m-%d %H:%M:%S"),
            "source": np.random.choice(["app", "web", "widget"], p=[0.7, 0.2, 0.1]),
            "ab_group": np.random.choice(["control", "treatment"], p=[0.5, 0.5]),
        })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# 9. EVENTS (event_id, ts, session_id, user_id_hash, event_type, offer_id, product_id, query, referrer, position, dwell_ms, geo_hash)
# -----------------------------------------------------------------------------
def generate_events(
    spark: SparkSession,
    sessions_pdf: pd.DataFrame,
    users_pdf: pd.DataFrame,
    products_pdf: pd.DataFrame,
) -> pd.DataFrame:
    sessions_list = sessions_pdf.to_dict("records")
    product_ids = products_pdf["product_id"].tolist()
    rows = []
    for i in range(N_EVENTS):
        s = np.random.choice(sessions_list)
        ts = datetime.strptime(s["ts_start"], "%Y-%m-%d %H:%M:%S") + timedelta(seconds=np.random.randint(0, 1800))
        event_type = np.random.choice(EVENT_TYPES, p=[0.25, 0.3, 0.15, 0.1, 0.05, 0.05, 0.1])
        rows.append({
            "event_id": f"evt_{i:010d}",
            "ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": s["session_id"],
            "user_id_hash": s["user_id_hash"],
            "event_type": event_type,
            "offer_id": f"OFF-{np.random.randint(1, 5000):05d}" if np.random.random() > 0.3 else None,
            "product_id": np.random.choice(product_ids) if event_type in ("view_offer", "add_to_list", "clip_coupon") and np.random.random() > 0.5 else None,
            "query": np.random.choice(["chicken", "milk", "bread", "deals", "coupons", ""], p=[0.2, 0.15, 0.15, 0.2, 0.2, 0.1]) or None,
            "referrer": np.random.choice(["search", "flyer", "home", None], p=[0.3, 0.4, 0.2, 0.1]),
            "position": np.random.randint(1, 50) if np.random.random() > 0.5 else None,
            "dwell_ms": int(np.random.exponential(2000)) if np.random.random() > 0.3 else None,
            "geo_hash": _hash_id(s["user_id_hash"] + str(i))[:12],
        })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# 10. STORE_VISITS (store_id, ts_day, visitors, repeat_visitors, avg_dwell_min)
# -----------------------------------------------------------------------------
def generate_store_visits(spark: SparkSession, stores_pdf: pd.DataFrame) -> pd.DataFrame:
    store_ids = stores_pdf["store_id"].tolist()
    rows = []
    for day_offset in range(DAYS_STORE_VISITS):
        ts_day = (END_DATE - timedelta(days=DAYS_STORE_VISITS - 1 - day_offset)).strftime("%Y-%m-%d")
        for sid in store_ids:
            if np.random.random() > 0.3:  # not every store every day
                visitors = int(np.random.lognormal(6, 0.8))
                repeat = int(visitors * np.random.uniform(0.1, 0.4))
                rows.append({
                    "store_id": sid,
                    "ts_day": ts_day,
                    "visitors": visitors,
                    "repeat_visitors": repeat,
                    "avg_dwell_min": round(np.random.uniform(5, 45), 1),
                })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# 11. CONVERSION_PROXIES (user_id_hash, ts, store_id, action)
# -----------------------------------------------------------------------------
def generate_conversion_proxies(
    spark: SparkSession, users_pdf: pd.DataFrame, stores_pdf: pd.DataFrame
) -> pd.DataFrame:
    user_hashes = users_pdf["user_id_hash"].tolist()
    store_ids = stores_pdf["store_id"].tolist()
    rows = []
    for i in range(N_CONVERSION_PROXIES):
        ts = START_DATE + timedelta(days=np.random.randint(0, 170), seconds=np.random.randint(0, 86400))
        rows.append({
            "user_id_hash": np.random.choice(user_hashes),
            "ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "store_id": np.random.choice(store_ids),
            "action": np.random.choice(CONVERSION_ACTIONS, p=[0.4, 0.4, 0.2]),
        })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# 12. DEALS (existing: deal_id, retailer_id, retailer_name, product_name, brand, category, prices, unit, valid_from, valid_to)
# -----------------------------------------------------------------------------
def generate_deals(spark: SparkSession, retailers_pdf: pd.DataFrame) -> pd.DataFrame:
    retailer_ids = retailers_pdf["retailer_id"].tolist()
    retailer_names = retailers_pdf.set_index("retailer_id")["name"].to_dict()
    deals = []
    for i in range(N_DEALS):
        rid = np.random.choice(retailer_ids)
        rname = retailer_names[rid]
        category = np.random.choice(CATEGORIES_NAMES)
        product = np.random.choice(PRODUCT_NAMES)
        brand = np.random.choice(["Store Brand", "Name Brand", "Premium", "Selection", "No Name"], p=[0.35, 0.25, 0.2, 0.1, 0.1])
        was_price = round(float(np.random.lognormal(2.5, 0.8)), 2)
        discount_pct = np.random.choice([5, 10, 15, 20, 25, 30, 40, 50], p=[0.15, 0.2, 0.2, 0.15, 0.12, 0.1, 0.05, 0.03])
        current_price = round(was_price * (1 - discount_pct / 100), 2)
        valid_days = np.random.randint(0, 13)
        valid_from = (DEAL_START + timedelta(days=valid_days)).strftime("%Y-%m-%d")
        valid_to = (DEAL_START + timedelta(days=valid_days + 6)).strftime("%Y-%m-%d")
        unit = np.random.choice(["each", "per lb", "per kg", "2/$", "4/$", "bunch", "bag"], p=[0.4, 0.15, 0.1, 0.15, 0.05, 0.1, 0.05])
        deals.append({
            "deal_id": f"D{i+1:06d}",
            "retailer_id": rid,
            "retailer_name": rname,
            "product_name": product,
            "brand": brand,
            "category": category,
            "current_price": current_price,
            "was_price": was_price,
            "discount_pct": discount_pct,
            "unit": unit,
            "valid_from": valid_from,
            "valid_to": valid_to,
        })
    return pd.DataFrame(deals)


def main() -> None:
    spark = get_spark()
    print(f"Step 1: Create data → catalog={CATALOG}, schema={SCHEMA}, volume={VOLUME_RAW}")

    create_infrastructure(spark)
    print("  Created schema / volume (if not exists).")

    # Generate in dependency order
    retailers_pdf = generate_retailers(spark)
    stores_pdf = generate_stores(spark, retailers_pdf)
    trade_areas_pdf = generate_trade_areas(spark, stores_pdf)
    categories_pdf = generate_categories(spark)
    products_pdf = generate_products(spark, categories_pdf)
    product_retailer_map_pdf = generate_product_retailer_map(spark, products_pdf, retailers_pdf)
    users_pdf = generate_users(spark)
    sessions_pdf = generate_sessions(spark, users_pdf)
    events_pdf = generate_events(spark, sessions_pdf, users_pdf, products_pdf)
    store_visits_pdf = generate_store_visits(spark, stores_pdf)
    conversion_proxies_pdf = generate_conversion_proxies(spark, users_pdf, stores_pdf)
    deals_pdf = generate_deals(spark, retailers_pdf)

    # Write parquet to volume
    spark.createDataFrame(retailers_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/retailers")
    spark.createDataFrame(stores_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/stores")
    spark.createDataFrame(trade_areas_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/trade_areas")

    # Categories: synonyms as array<string>
    from pyspark.sql import Row as R
    cat_schema = StructType([
        StructField("category_id", StringType()),
        StructField("path", StringType()),
        StructField("depth", IntegerType()),
        StructField("synonyms", ArrayType(StringType())),
    ])
    cat_rows = [R(category_id=r["category_id"], path=r["path"], depth=int(r["depth"]), synonyms=r["synonyms"]) for _, r in categories_pdf.iterrows()]
    spark.createDataFrame(cat_rows, cat_schema).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/categories")

    # Products: attributes as map<string,string>
    prod_schema = StructType([
        StructField("product_id", StringType()),
        StructField("upc_gtin", StringType()),
        StructField("brand", StringType()),
        StructField("title", StringType()),
        StructField("size", StringType()),
        StructField("unit", StringType()),
        StructField("category_id", StringType()),
        StructField("attributes", MapType(StringType(), StringType())),
    ])
    prod_rows = [R(product_id=r["product_id"], upc_gtin=r["upc_gtin"], brand=r["brand"], title=r["title"], size=r["size"], unit=r["unit"], category_id=r["category_id"], attributes=r["attributes"]) for _, r in products_pdf.iterrows()]
    spark.createDataFrame(prod_rows, prod_schema).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/products")

    spark.createDataFrame(product_retailer_map_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/product_retailer_map")
    spark.createDataFrame(users_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/users")
    spark.createDataFrame(sessions_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/sessions")
    spark.createDataFrame(events_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/events")
    spark.createDataFrame(store_visits_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/store_visits")
    spark.createDataFrame(conversion_proxies_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/conversion_proxies")
    spark.createDataFrame(deals_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/deals")

    print(f"  Wrote: retailers({len(retailers_pdf)}), stores({len(stores_pdf)}), trade_areas({len(trade_areas_pdf)}), categories({len(categories_pdf)}), products({len(products_pdf)}), product_retailer_map({len(product_retailer_map_pdf)}), users({len(users_pdf)}), sessions({len(sessions_pdf)}), events({len(events_pdf)}), store_visits({len(store_visits_pdf)}), conversion_proxies({len(conversion_proxies_pdf)}), deals({len(deals_pdf)})")
    print(f"  Parquet paths: {VOLUME_PATH_RAW}/<table_name>")

    print("\nStep 1 done. Next: run generate_flyer_pdfs.py (local) for PDFs + JSON, then Step 2 (enrich + upload).")


if __name__ == "__main__":
    main()
