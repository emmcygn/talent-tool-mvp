"""
Master seed data generation script.

Usage (from backend/ directory):
    python -m seed.generate

Generates all seed data and outputs supabase/seed.sql.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from uuid import uuid4

from seed.candidates import generate_all_candidates
from seed.organisations import ORGANISATIONS
from seed.roles import generate_roles
from seed.users import get_demo_users


async def generate_seed_data():
    """Generate all seed data and output SQL."""
    print("=== RecruitTech Seed Data Generator ===\n")

    # 1. Organisations
    print(f"Generating {len(ORGANISATIONS)} organisations...")
    org_ids = {org["name"]: org["id"] for org in ORGANISATIONS}

    # 2. Users
    users = get_demo_users(org_ids)
    print(f"Generating {len(users)} demo users...")
    partner_ids = [u["id"] for u in users if u["role"] == "talent_partner"]
    client_ids = [u["id"] for u in users if u["role"] == "client"]

    # 3. Candidates
    candidates = generate_all_candidates(partner_ids)
    print(f"Generating {len(candidates)} candidates...")

    # 4. Roles
    roles = generate_roles(org_ids, client_ids)
    print(f"Generating {len(roles)} roles...")

    # 5. Collections
    collections = _generate_collections(candidates, partner_ids)
    print(f"Generating {len(collections)} collections...")

    # 6. Handoffs
    handoffs = _generate_handoffs(candidates, partner_ids, roles)
    print(f"Generating {len(handoffs)} handoffs...")

    # 7. Quotes
    quotes = _generate_quotes(candidates, roles, client_ids)
    print(f"Generating {len(quotes)} quotes...")

    # 8. Signals
    signals = _generate_signal_history(users, candidates, roles)
    print(f"Generating {len(signals)} signals...")

    # 9. Dedup queue items
    dedup_items = _generate_dedup_queue(candidates)
    print(f"Generating {len(dedup_items)} dedup queue items...")

    # 10. Write SQL
    _write_seed_sql(
        organisations=ORGANISATIONS,
        users=users,
        candidates=candidates,
        roles=roles,
        collections=collections,
        handoffs=handoffs,
        quotes=quotes,
        signals=signals,
        dedup_items=dedup_items,
    )

    print("\n=== Seed data written to supabase/seed.sql ===")
    print(f"  Organisations: {len(ORGANISATIONS)}")
    print(f"  Users: {len(users)}")
    print(f"  Candidates: {len(candidates)}")
    print(f"  Roles: {len(roles)}")
    print(f"  Collections: {len(collections)}")
    print(f"  Handoffs: {len(handoffs)}")
    print(f"  Quotes: {len(quotes)}")
    print(f"  Signals: {len(signals)}")
    print(f"  Dedup queue items: {len(dedup_items)}")


def _generate_collections(candidates, partner_ids):
    """Generate themed collections."""
    collections = []
    themes = [
        ("Senior Backend — London", ["backend", "london", "senior"], "senior", "London"),
        ("ML Engineers — Remote OK", ["ml", "ai", "remote"], None, "Remote"),
        ("Fintech Specialists", ["fintech", "finance"], None, None),
        ("Available Now", ["immediate", "available"], None, None),
        ("React Frontend Experts", ["react", "frontend", "typescript"], None, None),
        ("Data Engineering Talent", ["data", "sql", "spark"], None, None),
    ]

    for name, tags, seniority_filter, location_filter in themes:
        cid_pool = []
        for c in candidates:
            if seniority_filter and c.get("seniority") != seniority_filter:
                continue
            if location_filter and location_filter.lower() not in (c.get("location") or "").lower():
                continue
            cid_pool.append(c["id"])

        if not cid_pool:
            cid_pool = [c["id"] for c in candidates]

        selected = random.sample(cid_pool, k=min(random.randint(5, 12), len(cid_pool)))

        collection_id = str(uuid4())
        collections.append({
            "id": collection_id,
            "name": name,
            "description": f"Curated collection: {name}",
            "owner_id": random.choice(partner_ids),
            "visibility": random.choice(["private", "shared_all", "shared_specific"]),
            "shared_with": (
                random.sample(partner_ids, k=random.randint(1, min(2, len(partner_ids))))
                if random.random() > 0.5
                else None
            ),
            "tags": tags,
            "candidate_ids": selected,
            "candidate_count": len(selected),
            "avg_match_score": round(random.uniform(0.5, 0.85), 2),
            "available_now_count": random.randint(1, min(5, len(selected))),
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 20))).isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })

    return collections


def _generate_handoffs(candidates, partner_ids, roles):
    """Generate 12 handoffs between partners."""
    handoffs = []
    statuses = ["pending", "accepted", "declined", "pending", "accepted"]

    for i in range(12):
        from_id = random.choice(partner_ids)
        to_candidates = [p for p in partner_ids if p != from_id]
        to_id = random.choice(to_candidates) if to_candidates else from_id
        selected_candidates = random.sample(
            [c["id"] for c in candidates],
            k=random.randint(1, 4),
        )
        status = statuses[i % len(statuses)]
        created = datetime.utcnow() - timedelta(days=random.randint(1, 14))

        handoffs.append({
            "id": str(uuid4()),
            "from_partner_id": from_id,
            "to_partner_id": to_id,
            "candidate_ids": selected_candidates,
            "context_notes": random.choice([
                "Strong Python candidates for your fintech roles",
                "These ML engineers might be a good fit",
                "Recommended for the backend position",
                "Experienced candidates looking for new opportunities",
                "Great cultural fit for your team",
            ]),
            "target_role_id": (
                random.choice([r["id"] for r in roles])
                if random.random() > 0.3
                else None
            ),
            "status": status,
            "response_notes": (
                "Looks great, thanks!" if status == "accepted"
                else ("Not quite the right fit" if status == "declined" else None)
            ),
            "attribution_id": str(uuid4()),
            "created_at": created.isoformat(),
            "responded_at": (
                (created + timedelta(hours=random.randint(1, 48))).isoformat()
                if status != "pending"
                else None
            ),
        })

    return handoffs


def _generate_quotes(candidates, roles, client_ids):
    """Generate 18 quotes with various statuses."""
    quotes = []
    fee_map = {"junior": 8000, "mid": 12000, "senior": 18000, "lead": 25000, "principal": 35000}

    for i in range(18):
        role = random.choice(roles)
        candidate = random.choice(candidates)
        seniority = role.get("seniority", "mid")
        base_fee = fee_map.get(seniority, 12000)
        is_pool = random.random() > 0.5
        discount = int(base_fee * 0.20) if is_pool else 0
        final_fee = base_fee - discount
        status = random.choice(["generated", "sent", "accepted", "declined", "expired"])
        created = datetime.utcnow() - timedelta(days=random.randint(1, 30))

        quotes.append({
            "id": str(uuid4()),
            "client_id": random.choice(client_ids),
            "candidate_id": candidate["id"],
            "role_id": role["id"],
            "is_pool_candidate": is_pool,
            "base_fee": str(base_fee),
            "pool_discount": str(discount) if is_pool else None,
            "final_fee": str(final_fee),
            "fee_breakdown": {
                "summary": f"Placement fee for {role['title']}",
                "seniority_level": seniority,
                "base_fee": {"amount": str(base_fee), "currency": "GBP"},
                "final_fee": {"amount": str(final_fee), "currency": "GBP"},
            },
            "status": status,
            "created_at": created.isoformat(),
            "expires_at": (created + timedelta(days=14)).isoformat(),
        })

    return quotes


def _generate_signal_history(users, candidates, roles):
    """Generate signal history for populated analytics dashboards."""
    signals = []
    now = datetime.utcnow()

    partner_users = [u for u in users if u["role"] == "talent_partner"]
    client_users = [u for u in users if u["role"] == "client"]

    # Spread signals over 30 days
    for day_offset in range(30):
        day = now - timedelta(days=day_offset)
        daily_count = random.randint(15, 40)

        for _ in range(daily_count):
            hour = random.randint(8, 18)
            minute = random.randint(0, 59)
            timestamp = day.replace(hour=hour, minute=minute)

            event_type = random.choice([
                "candidate_ingested", "candidate_viewed", "candidate_viewed",
                "candidate_shortlisted", "candidate_dismissed",
                "match_generated", "match_generated", "match_generated",
                "intro_requested", "handoff_sent", "handoff_accepted",
                "quote_generated", "copilot_query",
            ])

            if event_type in (
                "candidate_ingested", "candidate_viewed", "candidate_shortlisted",
                "candidate_dismissed", "handoff_sent", "handoff_accepted", "copilot_query",
            ):
                actor = random.choice(partner_users)
            else:
                actor = random.choice(client_users + partner_users)

            if "candidate" in event_type:
                entity_type = "candidate"
            elif "match" in event_type:
                entity_type = "match"
            elif "handoff" in event_type:
                entity_type = "handoff"
            elif "quote" in event_type:
                entity_type = "quote"
            else:
                entity_type = "copilot"

            signals.append({
                "id": str(uuid4()),
                "event_type": event_type,
                "actor_id": actor["id"],
                "actor_role": actor["role"],
                "entity_type": entity_type,
                "entity_id": random.choice(candidates)["id"],
                "metadata": {},
                "created_at": timestamp.isoformat(),
            })

    # Add a few placements
    for _ in range(5):
        signals.append({
            "id": str(uuid4()),
            "event_type": "placement_made",
            "actor_id": users[-1]["id"],  # admin
            "actor_role": "admin",
            "entity_type": "candidate",
            "entity_id": random.choice(candidates)["id"],
            "metadata": {"final_fee": str(random.randint(12000, 35000))},
            "created_at": (now - timedelta(days=random.randint(1, 30))).isoformat(),
        })

    return signals


def _generate_dedup_queue(candidates):
    """Generate dedup queue items for admin review."""
    items = []
    for i in range(8):
        a, b = random.sample(candidates, 2)
        items.append({
            "id": str(uuid4()),
            "candidate_a_id": a["id"],
            "candidate_b_id": b["id"],
            "match_type": random.choice(["fuzzy_name", "semantic", "fuzzy_name"]),
            "confidence": round(random.uniform(0.6, 0.89), 2),
            "status": "pending",
            "resolved_by": None,
            "resolved_at": None,
            "resolution_notes": None,
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat(),
        })
    return items


def _write_seed_sql(
    organisations, users, candidates, roles,
    collections, handoffs, quotes, signals, dedup_items,
):
    """Write all seed data as a SQL file."""
    lines = [
        "-- RecruitTech Seed Data",
        "-- Generated by backend/seed/generate.py",
        f"-- Generated at: {datetime.utcnow().isoformat()}",
        "",
        "BEGIN;",
        "",
    ]

    # Organisations
    lines.append("-- Organisations")
    for org in organisations:
        lines.append(
            f"INSERT INTO organisations (id, name, industry, location, description, size) "
            f"VALUES ('{org['id']}', {_sql_str(org['name'])}, {_sql_str(org['industry'])}, "
            f"{_sql_str(org['location'])}, {_sql_str(org['description'])}, {_sql_str(org['size'])}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Users
    lines.append("-- Users")
    for u in users:
        lines.append(
            f"INSERT INTO users (id, email, first_name, last_name, role, organisation_id, is_active, created_at) "
            f"VALUES ('{u['id']}', {_sql_str(u['email'])}, {_sql_str(u['first_name'])}, "
            f"{_sql_str(u['last_name'])}, {_sql_str(u['role'])}, "
            f"{'NULL' if not u.get('organisation_id') else _sql_str(u['organisation_id'])}, "
            f"{u['is_active']}, now()) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Candidates
    lines.append("-- Candidates")
    for c in candidates:
        lines.append(
            f"INSERT INTO candidates (id, first_name, last_name, email, phone, location, linkedin_url, "
            f"skills, experience, seniority, salary_expectation, availability, industries, "
            f"cv_text, sources, extraction_confidence, extraction_flags, created_at, updated_at, created_by) "
            f"VALUES ('{c['id']}', {_sql_str(c['first_name'])}, {_sql_str(c['last_name'])}, "
            f"{_sql_str(c.get('email'))}, {_sql_str(c.get('phone'))}, {_sql_str(c.get('location'))}, "
            f"{_sql_str(c.get('linkedin_url'))}, "
            f"{_sql_json(c.get('skills', []))}, {_sql_json(c.get('experience', []))}, "
            f"{_sql_str(c.get('seniority'))}, {_sql_json(c.get('salary_expectation'))}, "
            f"{_sql_str(c.get('availability'))}, {_sql_array(c.get('industries', []))}, "
            f"{_sql_str(c.get('cv_text'))}, {_sql_json(c.get('sources', []))}, "
            f"{c.get('extraction_confidence', 0.8)}, {_sql_array(c.get('extraction_flags', []))}, "
            f"{_sql_str(c['created_at'])}, {_sql_str(c['updated_at'])}, '{c['created_by']}') "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Roles
    lines.append("-- Roles")
    for r in roles:
        lines.append(
            f"INSERT INTO roles (id, title, description, organisation_id, required_skills, preferred_skills, "
            f"seniority, salary_band, location, remote_policy, industry, extraction_confidence, status, "
            f"created_at, created_by) "
            f"VALUES ('{r['id']}', {_sql_str(r['title'])}, {_sql_str(r['description'])}, "
            f"{_sql_str(r.get('organisation_id'))}, {_sql_json(r.get('required_skills', []))}, "
            f"{_sql_json(r.get('preferred_skills', []))}, {_sql_str(r.get('seniority'))}, "
            f"{_sql_json(r.get('salary_band'))}, {_sql_str(r.get('location'))}, "
            f"{_sql_str(r.get('remote_policy'))}, {_sql_str(r.get('industry'))}, "
            f"{r.get('extraction_confidence', 0.9)}, {_sql_str(r.get('status', 'active'))}, "
            f"{_sql_str(r['created_at'])}, '{r['created_by']}') "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Collections
    lines.append("-- Collections")
    for c in collections:
        lines.append(
            f"INSERT INTO collections (id, name, description, owner_id, visibility, shared_with, tags, "
            f"candidate_count, avg_match_score, available_now_count, created_at, updated_at) "
            f"VALUES ('{c['id']}', {_sql_str(c['name'])}, {_sql_str(c.get('description'))}, "
            f"'{c['owner_id']}', {_sql_str(c['visibility'])}, "
            f"{_sql_array(c.get('shared_with')) if c.get('shared_with') else 'NULL'}, "
            f"{_sql_array(c['tags'])}, {c['candidate_count']}, "
            f"{c.get('avg_match_score') or 'NULL'}, {c['available_now_count']}, "
            f"{_sql_str(c['created_at'])}, {_sql_str(c['updated_at'])}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
        # Junction table entries
        for cid in c.get("candidate_ids", []):
            lines.append(
                f"INSERT INTO collection_candidates (collection_id, candidate_id) "
                f"VALUES ('{c['id']}', '{cid}') ON CONFLICT DO NOTHING;"
            )
    lines.append("")

    # Handoffs
    lines.append("-- Handoffs")
    for h in handoffs:
        lines.append(
            f"INSERT INTO handoffs (id, from_partner_id, to_partner_id, candidate_ids, context_notes, "
            f"target_role_id, status, response_notes, attribution_id, created_at, responded_at) "
            f"VALUES ('{h['id']}', '{h['from_partner_id']}', '{h['to_partner_id']}', "
            f"{_sql_array(h['candidate_ids'])}, {_sql_str(h['context_notes'])}, "
            f"{_sql_str(h.get('target_role_id'))}, {_sql_str(h['status'])}, "
            f"{_sql_str(h.get('response_notes'))}, '{h['attribution_id']}', "
            f"{_sql_str(h['created_at'])}, {_sql_str(h.get('responded_at'))}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Quotes
    lines.append("-- Quotes")
    for q in quotes:
        lines.append(
            f"INSERT INTO quotes (id, client_id, candidate_id, role_id, is_pool_candidate, "
            f"base_fee, pool_discount, final_fee, fee_breakdown, status, created_at, expires_at) "
            f"VALUES ('{q['id']}', '{q['client_id']}', '{q['candidate_id']}', '{q['role_id']}', "
            f"{q['is_pool_candidate']}, {q['base_fee']}, "
            f"{q.get('pool_discount') or 'NULL'}, {q['final_fee']}, "
            f"{_sql_json(q['fee_breakdown'])}, {_sql_str(q['status'])}, "
            f"{_sql_str(q['created_at'])}, {_sql_str(q['expires_at'])}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Signals
    lines.append("-- Signals")
    for s in signals:
        lines.append(
            f"INSERT INTO signals (id, event_type, actor_id, actor_role, entity_type, entity_id, "
            f"metadata, created_at) "
            f"VALUES ('{s['id']}', {_sql_str(s['event_type'])}, '{s['actor_id']}', "
            f"{_sql_str(s['actor_role'])}, {_sql_str(s['entity_type'])}, '{s['entity_id']}', "
            f"{_sql_json(s.get('metadata', {}))}, {_sql_str(s['created_at'])}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append("")

    # Dedup queue
    lines.append("-- Dedup Queue")
    for d in dedup_items:
        lines.append(
            f"INSERT INTO dedup_queue (id, candidate_a_id, candidate_b_id, match_type, confidence, "
            f"status, created_at) "
            f"VALUES ('{d['id']}', '{d['candidate_a_id']}', '{d['candidate_b_id']}', "
            f"{_sql_str(d['match_type'])}, {d['confidence']}, {_sql_str(d['status'])}, "
            f"{_sql_str(d['created_at'])}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )

    lines.extend(["", "COMMIT;", ""])

    import os
    # Write relative to project root (two levels up from backend/seed/)
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "supabase", "seed.sql"
    )
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f"  Written to: {output_path}")


def _sql_str(value) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def _sql_json(value) -> str:
    if value is None:
        return "NULL"
    return "'" + json.dumps(value).replace("'", "''") + "'::jsonb"


def _sql_array(value) -> str:
    if value is None or len(value) == 0:
        return "ARRAY[]::text[]"
    items = ", ".join(f"'{str(v).replace(chr(39), chr(39)+chr(39))}'" for v in value)
    return f"ARRAY[{items}]"


if __name__ == "__main__":
    asyncio.run(generate_seed_data())
