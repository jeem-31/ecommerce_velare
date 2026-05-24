"""Shipping fee calculation based on Buyer Province vs Seller Province tier matrix.

Tier 1 — Same City                         → ₱49
Tier 2 — Same Province (different cities)  → ₱79
Tier 3 — Same Region/Island (diff province)→ ₱109
Tier 4 — Different Region (same island grp)→ ₱149
Tier 5 — Cross-Island                      → ₱199
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple


# ----------------------------------------------------------------------------
# Tier fees
# ----------------------------------------------------------------------------
TIER_FEES = {
    1: 49.00,
    2: 79.00,
    3: 109.00,
    4: 149.00,
    5: 199.00,
}

# Default fallback used when the seller has no usable address yet.
DEFAULT_SHIPPING_FEE = TIER_FEES[1]


# ----------------------------------------------------------------------------
# Region → Major Island Group mapping
# Based on the Philippine Statistics Authority groupings.
# ----------------------------------------------------------------------------
LUZON_REGIONS = {
    'ilocos region', 'region i', 'region 1',
    'cagayan valley', 'region ii', 'region 2',
    'central luzon', 'region iii', 'region 3',
    'calabarzon', 'region iv-a', 'region iva', 'region 4-a', 'region 4a',
    'mimaropa', 'mimaropa region', 'region iv-b', 'region ivb', 'region 4-b', 'region 4b',
    'bicol region', 'region v', 'region 5',
    'cordillera administrative region', 'car',
    'national capital region', 'ncr', 'metro manila',
}

VISAYAS_REGIONS = {
    'western visayas', 'region vi', 'region 6',
    'central visayas', 'region vii', 'region 7',
    'eastern visayas', 'region viii', 'region 8',
    'negros island region', 'nir',
}

MINDANAO_REGIONS = {
    'zamboanga peninsula', 'region ix', 'region 9',
    'northern mindanao', 'region x', 'region 10',
    'davao region', 'region xi', 'region 11',
    'soccsksargen', 'region xii', 'region 12',
    'caraga', 'region xiii', 'region 13',
    'bangsamoro autonomous region in muslim mindanao',
    'bangsamoro', 'barmm', 'armm',
}


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _norm(value: Optional[str]) -> str:
    """Normalize a place name for comparison: lowercase, no punctuation,
    no common qualifiers like 'city of', 'municipality of', 'province of'."""
    if not value:
        return ''
    s = str(value).strip().lower()
    # Remove common prefixes/suffixes
    s = re.sub(r'^(city of|municipality of|province of|barangay)\s+', '', s)
    s = re.sub(r'\s+(city|municipality|province)$', '', s)
    # Strip non-alphanumeric (keep spaces)
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _island_group(region: Optional[str]) -> Optional[str]:
    """Return 'luzon', 'visayas', 'mindanao' or None for an unknown region."""
    r = _norm(region)
    if not r:
        return None
    if r in LUZON_REGIONS:
        return 'luzon'
    if r in VISAYAS_REGIONS:
        return 'visayas'
    if r in MINDANAO_REGIONS:
        return 'mindanao'
    # Loose contains-match for variants like "Region IV-A (CALABARZON)"
    for token, group in (
        (LUZON_REGIONS, 'luzon'),
        (VISAYAS_REGIONS, 'visayas'),
        (MINDANAO_REGIONS, 'mindanao'),
    ):
        for known in token:
            if known and known in r:
                return group
    return None


def _effective_province(address: Dict) -> str:
    """NCR addresses don't have a province — treat the region as the province
    so 'same province' / 'same region' tiers behave correctly within NCR."""
    province = _norm(address.get('province'))
    region = _norm(address.get('region'))
    if province:
        return province
    # NCR has no provinces
    if region in {'national capital region', 'ncr', 'metro manila'}:
        return 'metro manila'
    return ''


# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------
def determine_tier(buyer_address: Dict, seller_address: Dict) -> int:
    """Return tier 1..5 comparing buyer and seller addresses."""
    if not buyer_address or not seller_address:
        return 1  # fall back to base fee

    buyer_city = _norm(buyer_address.get('city'))
    seller_city = _norm(seller_address.get('city'))
    buyer_province = _effective_province(buyer_address)
    seller_province = _effective_province(seller_address)
    buyer_region = _norm(buyer_address.get('region'))
    seller_region = _norm(seller_address.get('region'))
    buyer_island = _island_group(buyer_address.get('region'))
    seller_island = _island_group(seller_address.get('region'))

    # Tier 1: Same City (must also be in the same province to avoid false
    # matches between cities sharing a name in different provinces).
    if (
        buyer_city
        and seller_city
        and buyer_city == seller_city
        and (not buyer_province or not seller_province or buyer_province == seller_province)
    ):
        return 1

    # Tier 2: Same Province, different city
    if buyer_province and seller_province and buyer_province == seller_province:
        return 2

    # Tier 3: Same Region/Island (different province)
    if buyer_region and seller_region and buyer_region == seller_region:
        return 3

    # Tier 4: Different Region but same major island group
    if buyer_island and seller_island and buyer_island == seller_island:
        return 4

    # Tier 5: Cross-Island (Luzon ↔ Visayas / Mindanao)
    if buyer_island and seller_island and buyer_island != seller_island:
        return 5

    # Unknown — be conservative, charge the base fee
    return 1


def calculate_fee(buyer_address: Dict, seller_address: Dict) -> Tuple[float, int]:
    """Return (fee, tier) for the given buyer and seller addresses."""
    tier = determine_tier(buyer_address, seller_address)
    return TIER_FEES.get(tier, DEFAULT_SHIPPING_FEE), tier


def get_seller_default_address(supabase, seller_id: int) -> Optional[Dict]:
    """Fetch a seller's default address (region/province/city)."""
    if not seller_id:
        return None
    try:
        resp = (
            supabase.table('addresses')
            .select('region, province, city, barangay, is_default, created_at')
            .eq('user_type', 'seller')
            .eq('user_ref_id', seller_id)
            .order('is_default', desc=True)
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0]
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"⚠️ get_seller_default_address failed for seller {seller_id}: {exc}")
    return None


def get_address_by_id(supabase, address_id) -> Optional[Dict]:
    """Fetch a single address row by id."""
    if not address_id:
        return None
    try:
        resp = (
            supabase.table('addresses')
            .select('region, province, city, barangay')
            .eq('address_id', address_id)
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0]
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"⚠️ get_address_by_id failed for {address_id}: {exc}")
    return None
