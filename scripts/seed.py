"""Deterministic and Idempotent Database Seed Script for TripBuddy.

Seeds:
- 3 demo users (fixed fictional credentials and distinct verified_id_numbers)
- 9 hosts (some Superhosts)
- 22 realistic listings across 5 cities (Goa, Manali, Jaipur, Pondicherry, Munnar)
- 3 to 8 reviews per listing with natural voices and varied ratings
- Safe truncate-and-reseed logic
"""

import sys
import os
import hashlib
import json

# Ensure core package is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "tripbuddy_core")))

from tripbuddy_core.db import SessionLocal, engine
from tripbuddy_core.models import (
    User,
    Listing,
    Review,
    Booking,
    Message,
    ConciergeSession,
    ConciergeToolCall,
)
from sqlalchemy import text


# Deterministic demo users
DEMO_USERS = [
    {
        "id": "usr-demo-001",
        "name": "Alex Mercer",
        "email": "alex.mercer@tripbuddy.test",
        # Fictional bcrypt/mock hash placeholder for demo
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-7F3A91-DEMO",
        "is_host": False,
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80",
        "superhost": False,
        "joined_date": "March 2022",
    },
    {
        "id": "usr-demo-002",
        "name": "Samantha Chen",
        "email": "samantha.chen@tripbuddy.test",
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-4B8C12-DEMO",
        "is_host": False,
        "avatar": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=200&auto=format&fit=crop&q=80",
        "superhost": False,
        "joined_date": "August 2023",
    },
    {
        "id": "usr-demo-003",
        "name": "Rohan Deshmukh",
        "email": "rohan.deshmukh@tripbuddy.test",
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-9E2D55-DEMO",
        "is_host": False,
        "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80",
        "superhost": False,
        "joined_date": "January 2024",
    },
]

# 9 Hosts
HOSTS = [
    {
        "id": "host-001",
        "name": "Meera Joshi",
        "email": "meera.joshi@hosts.tripbuddy.test",
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-HOST-01-VERIFIED",
        "is_host": True,
        "avatar": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=200&auto=format&fit=crop&q=80",
        "superhost": True,
        "joined_date": "May 2020",
    },
    {
        "id": "host-002",
        "name": "Vikram Sethi",
        "email": "vikram.sethi@hosts.tripbuddy.test",
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-HOST-02-VERIFIED",
        "is_host": True,
        "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&auto=format&fit=crop&q=80",
        "superhost": True,
        "joined_date": "October 2019",
    },
    {
        "id": "host-003",
        "name": "Ananya Roy",
        "email": "ananya.roy@hosts.tripbuddy.test",
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-HOST-03-VERIFIED",
        "is_host": True,
        "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=200&auto=format&fit=crop&q=80",
        "superhost": False,
        "joined_date": "March 2021",
    },
    {
        "id": "host-004",
        "name": "Kabir Mehta",
        "email": "kabir.mehta@hosts.tripbuddy.test",
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-HOST-04-VERIFIED",
        "is_host": True,
        "avatar": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=200&auto=format&fit=crop&q=80",
        "superhost": True,
        "joined_date": "July 2021",
    },
    {
        "id": "host-005",
        "name": "Pooja Hegde",
        "email": "pooja.hegde@hosts.tripbuddy.test",
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-HOST-05-VERIFIED",
        "is_host": True,
        "avatar": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=200&auto=format&fit=crop&q=80",
        "superhost": False,
        "joined_date": "February 2022",
    },
    {
        "id": "host-006",
        "name": "David Fernandes",
        "email": "david.fernandes@hosts.tripbuddy.test",
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-HOST-06-VERIFIED",
        "is_host": True,
        "avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&auto=format&fit=crop&q=80",
        "superhost": True,
        "joined_date": "November 2020",
    },
    {
        "id": "host-007",
        "name": "Siddharth Rao",
        "email": "siddharth.rao@hosts.tripbuddy.test",
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-HOST-07-VERIFIED",
        "is_host": True,
        "avatar": "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=200&auto=format&fit=crop&q=80",
        "superhost": False,
        "joined_date": "April 2023",
    },
    {
        "id": "host-008",
        "name": "Fatima Begum",
        "email": "fatima.begum@hosts.tripbuddy.test",
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-HOST-08-VERIFIED",
        "is_host": True,
        "avatar": "https://images.unsplash.com/photo-1567532939604-b6b5b0db2604?w=200&auto=format&fit=crop&q=80",
        "superhost": True,
        "joined_date": "September 2021",
    },
    {
        "id": "host-009",
        "name": "Arjun Nair",
        "email": "arjun.nair@hosts.tripbuddy.test",
        "password_hash": "$2b$12$e80bY7p0oQh1y9Z4bJ9Hee0gU4nS6z.yJ6uE8cQf9XbQpY9rKj2iW",
        "verified_id_number": "ID-HOST-09-VERIFIED",
        "is_host": True,
        "avatar": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=200&auto=format&fit=crop&q=80",
        "superhost": False,
        "joined_date": "December 2022",
    },
]

# 22 Listings across 5 cities: Goa, Manali, Jaipur, Pondicherry, Munnar
LISTINGS = [
    # Goa
    {
        "id": "lst-goa-001",
        "host_id": "host-001",
        "title": "Seaside Portuguese Villa with Private Pool",
        "city": "Goa",
        "type": "Beachfront",
        "price_per_night": 3200,
        "max_guests": 5,
        "description": "Sunlit 2BHK heritage villa, just 2 minutes walk from Candolim beach. Enjoy a pristine private plunge pool, manicured tropical garden, homemade Goan breakfast, and dedicated high-speed wifi.",
        "amenities": ["Wifi", "Private Pool", "Kitchen", "Free Breakfast", "Air conditioning", "Beach Access"],
        "images": [
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-goa-002",
        "host_id": "host-006",
        "title": "Palm Grove Sunset Cottage near Anjuna",
        "city": "Goa",
        "type": "Cottage",
        "price_per_night": 2650,
        "max_guests": 3,
        "description": "Charming eco-cottage tucked amidst lush coconut groves. Cozy outdoor patio, open-air shower, 10 min stroll to flea markets and beach cafes.",
        "amenities": ["Wifi", "Free Parking", "Patio", "Air conditioning", "Work Desk"],
        "images": [
            "https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?w=800&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-goa-003",
        "host_id": "host-001",
        "title": "Modern Sea-Facing Studio in Morjim",
        "city": "Goa",
        "type": "Apartment",
        "price_per_night": 2100,
        "max_guests": 2,
        "description": "Crisp and peaceful sea-facing loft overlooking Olive Ridley turtle beach. Balcony hammock, fast fiber optic internet, and modular kitchenette.",
        "amenities": ["Wifi", "Kitchenette", "Balcony", "Sea View", "Dedicated workspace"],
        "images": [
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-goa-004",
        "host_id": "host-006",
        "title": "Luxury 4BHK Infinity Villa in Vagator",
        "city": "Goa",
        "type": "Villa",
        "price_per_night": 7800,
        "max_guests": 8,
        "description": "Cliffside architectural marvel with panoramic Arabian Sea views, infinity pool, personal butler, and expansive sun deck.",
        "amenities": ["Infinity Pool", "Wifi", "Butler Service", "Chef on call", "Air conditioning", "Hot Tub"],
        "images": [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-goa-005",
        "host_id": "host-001",
        "title": "Cozy Mandovi Riverfront Haven",
        "city": "Goa",
        "type": "Apartment",
        "price_per_night": 1850,
        "max_guests": 2,
        "description": "Peaceful retreat watching fishing trawlers and river breeze. 5 min drive into old Latin Quarter of Fontainhas.",
        "amenities": ["Wifi", "Kitchen", "River View", "Washing machine"],
        "images": [
            "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&auto=format&fit=crop&q=80",
        ],
    },

    # Manali
    {
        "id": "lst-man-001",
        "host_id": "host-002",
        "title": "Snow Peak Cedar Chalet with Fireplace",
        "city": "Manali",
        "type": "Cabin",
        "price_per_night": 3400,
        "max_guests": 4,
        "description": "Traditional Himalayan wooden chalet nestled in pine forest. Features a wood-burning stone fireplace, apple orchard views, and mountain spring water on tap.",
        "amenities": ["Fireplace", "Mountain View", "Wifi", "Heater", "Free Breakfast", "Balcony"],
        "images": [
            "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1510798831971-661eb04b3739?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-man-002",
        "host_id": "host-004",
        "title": "Old Manali Riverside Backpackers Attic",
        "city": "Manali",
        "type": "Apartment",
        "price_per_night": 1250,
        "max_guests": 2,
        "description": "Warm wooden attic bedroom with glass ceiling right next to the gushing Manalsu stream. Bohemian cafes are just steps away.",
        "amenities": ["Wifi", "Hot Water", "Heater", "Cafe on premises"],
        "images": [
            "https://images.unsplash.com/photo-1505691938895-1758d7feb511?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-man-003",
        "host_id": "host-002",
        "title": "Solang Valley Alpine Glasshouse",
        "city": "Manali",
        "type": "Cabin",
        "price_per_night": 5500,
        "max_guests": 6,
        "description": "Contemporary all-glass facade offering 360-degree unobstructed views of snow-clad Pir Panjal range. Gourmet kitchen and private bonfire ring.",
        "amenities": ["Panoramic View", "Bonfire", "Radiant Floor Heating", "Wifi", "Chef available"],
        "images": [
            "https://images.unsplash.com/photo-1587061949409-02df41d5e562?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-man-004",
        "host_id": "host-004",
        "title": "Naggar Castle Vista Homestay",
        "city": "Manali",
        "type": "Cottage",
        "price_per_night": 2200,
        "max_guests": 3,
        "description": "Heritage Kathkuni architecture stay overlooking the Beas valley and ancient cedar forests. Quiet and peaceful, perfect for remote workers.",
        "amenities": ["Wifi", "Work Desk", "Mountain View", "Kitchenette", "Garden"],
        "images": [
            "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=800&auto=format&fit=crop&q=80",
        ],
    },

    # Jaipur
    {
        "id": "lst-jai-001",
        "host_id": "host-003",
        "title": "The Pink City Heritage Courtyard Haveli",
        "city": "Jaipur",
        "type": "Villa",
        "price_per_night": 4100,
        "max_guests": 5,
        "description": "Restored 120-year-old Rajput haveli featuring hand-painted fresco arches, open courtyard with water fountain, and rooftop views of Nahargarh Fort.",
        "amenities": ["Courtyard", "Wifi", "Breakfast Included", "Air conditioning", "Rooftop terrace"],
        "images": [
            "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-jai-002",
        "host_id": "host-007",
        "title": "Boho Chic Studio in C-Scheme",
        "city": "Jaipur",
        "type": "Apartment",
        "price_per_night": 1750,
        "max_guests": 2,
        "description": "Bright, sun-drenched studio right in the heart of Jaipur's prime dining and shopping district. Walkable to boutique cafes and galleries.",
        "amenities": ["Wifi", "Air conditioning", "Kitchenette", "Smart TV", "Elevator"],
        "images": [
            "https://images.unsplash.com/photo-1502005229762-ee1b2b8ab00f?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-jai-003",
        "host_id": "host-003",
        "title": "Amer Fort View Royal Suite",
        "city": "Jaipur",
        "type": "Villa",
        "price_per_night": 6200,
        "max_guests": 4,
        "description": "Opulent marble suite with private jharokha balcony directly overlooking illuminated Amer Fort at dusk. Includes traditional welcome tea.",
        "amenities": ["Fort View", "Air conditioning", "Wifi", "Bathtub", "Free Breakfast"],
        "images": [
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-jai-004",
        "host_id": "host-007",
        "title": "Artisan Block-Print Loft in Civil Lines",
        "city": "Jaipur",
        "type": "Apartment",
        "price_per_night": 2400,
        "max_guests": 3,
        "description": "Styled with indigo block prints and terracotta ceramics. Quiet residential neighborhood with leafy trees and private security.",
        "amenities": ["Wifi", "Kitchen", "Air conditioning", "Balcony", "Free parking"],
        "images": [
            "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800&auto=format&fit=crop&q=80",
        ],
    },

    # Pondicherry
    {
        "id": "lst-pon-001",
        "host_id": "host-005",
        "title": "French Quarter Yellow Villa near Promenade",
        "city": "Pondicherry",
        "type": "Villa",
        "price_per_night": 3800,
        "max_guests": 4,
        "description": "Classic French colonial townhouse on Rue Romain Rolland. High timber ceilings, arched louvred shutters, inner courtyard garden, 3 mins walk to the sea.",
        "amenities": ["Courtyard", "Wifi", "Bicycles Provided", "Air conditioning", "Kitchen"],
        "images": [
            "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-pon-002",
        "host_id": "host-008",
        "title": "Auroville Forest Earth Cottage",
        "city": "Pondicherry",
        "type": "Cottage",
        "price_per_night": 1600,
        "max_guests": 2,
        "description": "Serene rammed-earth eco-cottage immersed in cashew forest. Outdoor rain shower, organic garden access, quiet contemplative atmosphere.",
        "amenities": ["Organic Garden", "Wifi", "Outdoor Shower", "Breakfast available"],
        "images": [
            "https://images.unsplash.com/photo-1449844908441-8829872d2607?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-pon-003",
        "host_id": "host-005",
        "title": "Serenity Beach Surf Bungalow",
        "city": "Pondicherry",
        "type": "Beachfront",
        "price_per_night": 2900,
        "max_guests": 4,
        "description": "Step right onto golden sand. Roof terrace with ocean sunrise views, surfboards available for guests, and fresh fish market nearby.",
        "amenities": ["Beachfront", "Rooftop terrace", "Wifi", "Kitchen", "Surfboards"],
        "images": [
            "https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-pon-004",
        "host_id": "host-008",
        "title": "White Town Heritage Rooftop Loft",
        "city": "Pondicherry",
        "type": "Apartment",
        "price_per_night": 2350,
        "max_guests": 2,
        "description": "Private rooftop haven surrounded by bougainvillea flowers. Great coffee shops and bakeries right down the street.",
        "amenities": ["Air conditioning", "Wifi", "Terrace", "Kitchenette"],
        "images": [
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&auto=format&fit=crop&q=80",
        ],
    },

    # Munnar
    {
        "id": "lst-mun-001",
        "host_id": "host-009",
        "title": "Mist Valley Tea Plantation Estate House",
        "city": "Munnar",
        "type": "Villa",
        "price_per_night": 4600,
        "max_guests": 6,
        "description": "Colonial planter bungalow situated inside a functioning tea estate. Morning mist walks, freshly plucked tea tastings, and cozy log fireplace.",
        "amenities": ["Tea Estate View", "Fireplace", "Wifi", "Cook on premises", "Free Breakfast"],
        "images": [
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-mun-002",
        "host_id": "host-009",
        "title": "Anamudi Cloud Peak Wooden Chalet",
        "city": "Munnar",
        "type": "Cabin",
        "price_per_night": 3100,
        "max_guests": 3,
        "description": "Perched on a ridge high above the clouds. Glass windows with direct views of Western Ghat peaks and cardamom plantations.",
        "amenities": ["Mountain View", "Balcony", "Wifi", "Heater", "Free Parking"],
        "images": [
            "https://images.unsplash.com/photo-1448375240586-882707db888b?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-mun-003",
        "host_id": "host-007",
        "title": "Attukal Waterfalls View Cottage",
        "city": "Munnar",
        "type": "Cottage",
        "price_per_night": 2400,
        "max_guests": 4,
        "description": "Listen to the cascading sounds of Attukal waterfalls from your private veranda. Lush spice plantation gardens with pepper and cinnamon trees.",
        "amenities": ["Waterfall View", "Garden", "Wifi", "Kitchenette", "Hot Water"],
        "images": [
            "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-mun-004",
        "host_id": "host-009",
        "title": "Devikulam Lake Rustic Treehouse",
        "city": "Munnar",
        "type": "Cabin",
        "price_per_night": 2800,
        "max_guests": 2,
        "description": "Authentic wooden treehouse built on twin banyan trees. Overlooks mineral-rich lake waters. Pure nature immersion.",
        "amenities": ["Balcony", "Breakfast Included", "Hot Shower", "Lake View"],
        "images": [
            "https://images.unsplash.com/photo-1488441770602-aed21fc49bd5?w=800&auto=format&fit=crop&q=80",
        ],
    },
    {
        "id": "lst-mun-005",
        "host_id": "host-008",
        "title": "Cardamom County Budget Homestay",
        "city": "Munnar",
        "type": "Apartment",
        "price_per_night": 1400,
        "max_guests": 2,
        "description": "Comfortable room in a welcoming family home. Authentic Kerala meals cooked fresh on order. Clean, simple, and warm hospitality.",
        "amenities": ["Wifi", "Hot Water", "Home Cooked Meals", "Parking"],
        "images": [
            "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop&q=80",
        ],
    },
]

# Reviews: 3 to 8 reviews per listing in natural voices, not all 5 stars
REVIEW_TEMPLATES = [
    ("Aarav Sharma", 5, "Amazing stay! The place was spotless and the host was very attentive to our needs."),
    ("Priya Kumar", 4, "Great location and very comfortable beds. Wifi was a bit sluggish on one evening but overall a wonderful trip."),
    ("Nikhil Varma", 5, "Absolutely breathtaking views and great privacy. Would definitely return next season!"),
    ("Sneha Nair", 3, "Decent place for the price. The hot water took a while to kick in, but host resolved it quickly."),
    ("Carlos Mendoza", 5, "One of the best stays we have booked. Everything was as described in the photos."),
    ("Elena Rostova", 4, "Very cozy and well maintained. Loved having morning coffee out on the veranda."),
    ("Karan Malhotra", 5, "Host went above and beyond to arrange our local transit. Superhost status well deserved."),
    ("Ananya Patel", 2, "The property itself is pretty, but nearby construction made early mornings rather noisy."),
]


def seed_database():
    db = SessionLocal()
    try:
        print("Truncating tables...")
        # Idempotent cleanup: truncate in correct FK dependency order
        db.execute(text("TRUNCATE TABLE concierge_tool_calls, concierge_sessions, messages, bookings, reviews, listings, users CASCADE;"))
        db.commit()

        print("Seeding demo users...")
        for u in DEMO_USERS:
            user = User(
                id=u["id"],
                name=u["name"],
                email=u["email"],
                password_hash=u["password_hash"],
                verified_id_number=u["verified_id_number"],
                is_host=u["is_host"],
                avatar=u["avatar"],
                superhost=u["superhost"],
                joined_date=u["joined_date"],
            )
            db.add(user)

        print("Seeding hosts...")
        for h in HOSTS:
            host = User(
                id=h["id"],
                name=h["name"],
                email=h["email"],
                password_hash=h["password_hash"],
                verified_id_number=h["verified_id_number"],
                is_host=h["is_host"],
                avatar=h["avatar"],
                superhost=h["superhost"],
                joined_date=h["joined_date"],
            )
            db.add(host)
        db.commit()

        print("Seeding listings...")
        review_counter = 1
        for lst_data in LISTINGS:
            listing = Listing(
                id=lst_data["id"],
                host_id=lst_data["host_id"],
                title=lst_data["title"],
                city=lst_data["city"],
                type=lst_data["type"],
                price_per_night=lst_data["price_per_night"],
                max_guests=lst_data["max_guests"],
                description=lst_data["description"],
                amenities=lst_data["amenities"],
                images=lst_data["images"],
            )
            db.add(listing)

            # Assign 4 to 6 reviews deterministically
            hash_val = int(hashlib.md5(lst_data["id"].encode()).hexdigest(), 16)
            review_count = 3 + (hash_val % 5)  # 3 to 7 reviews per listing
            for i in range(review_count):
                author, rating, text_body = REVIEW_TEMPLATES[(hash_val + i) % len(REVIEW_TEMPLATES)]
                review = Review(
                    id=f"rev-{review_counter:04d}",
                    listing_id=lst_data["id"],
                    author_name=author,
                    rating=rating,
                    text=text_body,
                )
                db.add(review)
                review_counter += 1

        # Seed 1 confirmed booking for testing date overlap exclusion
        test_booking = Booking(
            id="bk-seed-test-01",
            reference="TB-CONF-001",
            user_id="usr-demo-001",
            listing_id="lst-goa-001",
            checkin="2026-12-12",
            checkout="2026-12-14",
            guests=2,
            total_price=6400,
            status="confirmed",
        )
        db.add(test_booking)

        db.commit()
        print("Database successfully seeded deterministically!")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


def compute_database_hash():
    """Compute a deterministic hash of database content to verify idempotency."""
    db = SessionLocal()
    try:
        u_count = db.query(User).count()
        l_count = db.query(Listing).count()
        r_count = db.query(Review).count()
        b_count = db.query(Booking).count()

        # Extract deterministic rows
        users = db.query(User.id, User.email, User.verified_id_number).order_by(User.id).all()
        listings = db.query(Listing.id, Listing.city, Listing.price_per_night).order_by(Listing.id).all()
        reviews = db.query(Review.id, Review.rating, Review.text).order_by(Review.id).all()

        payload = json.dumps({
            "counts": [u_count, l_count, r_count, b_count],
            "users": [(u[0], u[1], u[2]) for u in users],
            "listings": [(l[0], l[1], l[2]) for l in listings],
            "reviews": [(r[0], r[1], r[2]) for r in reviews],
        }, sort_keys=True)

        return hashlib.sha256(payload.encode()).hexdigest(), (u_count, l_count, r_count, b_count)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

