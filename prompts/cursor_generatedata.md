# Informations about fake data generation

## unstructured data (PDFs)

1- Some PDFs related to coupans and discounts. It can have information This is unstructured data

## Structured data

1) Retailers, stores, and geospatial context

* Structured

    * retailers(retailer_id, name, tier, region, partner_since, vertical)
stores(store_id, retailer_id, address, city, state_prov, postal_code, lat, lon, hours, services)
trade_areas(store_id, geo_hash, dma, census_block_group, population, median_income)

    * Use postal_code/geo_hash for “near me” queries and catchment analysis.
Size: ~20 retailers; ~500–2,000 stores total.


2) Product catalog and taxonomy

* Structured

    * products(product_id, upc_gtin, brand, title, size, unit, category_id, attributes MAP<string,string>)
categories(category_id, path, depth, synonyms ARRAY<string>)
product_retailer_map(product_id, retailer_id, retailer_sku)


    * Include common household categories (grocery, household, health/beauty).
Size: 50k–150k products; category tree depth 3–5.


3) User profiles and event telemetry (anonymized)

* Structured

    * users(user_id_hash, cohort, home_postal, device_type, signup_date, marketing_opt_in BOOLEAN)
sessions(session_id, user_id_hash, ts_start, ts_end, source, ab_group)
events(event_id, ts, session_id, user_id_hash, event_type, offer_id, product_id, query, referrer, position, dwell_ms, geo_hash)
event_type ∈ {search, view_offer, add_to_list, clip_coupon, share, open_circular, store_select}

    * Geo is rounded; user_id is salted hash; insert light noise for k‑anonymity.
Size: “lite” 2–5M events; “full” 20–50M events across 8–12 weeks.


4) Store visits and conversion proxies

* Structured (aggregated for privacy)
    * store_visits(store_id, ts_day, visitors, repeat_visitors, avg_dwell_min)
conversion_proxies(user_id_hash, ts, store_id, action ∈ {add_to_list, coupon_clip, redemption})


    * Visits are at store/day; no raw device pings.
