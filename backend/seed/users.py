def get_demo_users(org_ids: dict[str, str]) -> list[dict]:
    """
    Generate demo users. org_ids maps org name → org ID.

    Returns list of user dicts with pre-set UUIDs for stable references.
    """
    return [
        # Talent Partners (5)
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "email": "sarah.chen@recruittech.demo",
            "first_name": "Sarah",
            "last_name": "Chen",
            "role": "talent_partner",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-partner-1",
        },
        {
            "id": "11111111-1111-1111-1111-222222222222",
            "email": "james.oconnor@recruittech.demo",
            "first_name": "James",
            "last_name": "O'Connor",
            "role": "talent_partner",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-partner-2",
        },
        {
            "id": "11111111-1111-1111-1111-333333333333",
            "email": "priya.sharma@recruittech.demo",
            "first_name": "Priya",
            "last_name": "Sharma",
            "role": "talent_partner",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-partner-3",
        },
        {
            "id": "11111111-1111-1111-1111-444444444444",
            "email": "tom.wright@recruittech.demo",
            "first_name": "Tom",
            "last_name": "Wright",
            "role": "talent_partner",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-partner-4",
        },
        {
            "id": "11111111-1111-1111-1111-555555555555",
            "email": "elena.volkov@recruittech.demo",
            "first_name": "Elena",
            "last_name": "Volkov",
            "role": "talent_partner",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-partner-5",
        },
        # Clients (3)
        {
            "id": "22222222-2222-2222-2222-111111111111",
            "email": "alex.thompson@monzo.demo",
            "first_name": "Alex",
            "last_name": "Thompson",
            "role": "client",
            "organisation_id": org_ids.get("Monzo"),
            "is_active": True,
            "password": "demo-client-1",
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "email": "rachel.green@babylon.demo",
            "first_name": "Rachel",
            "last_name": "Green",
            "role": "client",
            "organisation_id": org_ids.get("Babylon Health"),
            "is_active": True,
            "password": "demo-client-2",
        },
        {
            "id": "22222222-2222-2222-2222-333333333333",
            "email": "david.kim@paddle.demo",
            "first_name": "David",
            "last_name": "Kim",
            "role": "client",
            "organisation_id": org_ids.get("Paddle"),
            "is_active": True,
            "password": "demo-client-3",
        },
        # Admin (1)
        {
            "id": "33333333-3333-3333-3333-111111111111",
            "email": "admin@recruittech.demo",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "organisation_id": None,
            "is_active": True,
            "password": "demo-admin-1",
        },
    ]
