"""
Design systems inspired by awesome-claude-design repository.
Each system defines visual rules the AI uses when generating websites.
"""

DESIGN_SYSTEMS = {
    "glass": {
        "name": "Glass / Soft-Futurism",
        "best_for": ["spa", "salon", "yoga", "wellness", "beauty", "luxury", "hotel"],
        "css_vars": """
            --bg: #fafaff;
            --surface: rgba(255,255,255,0.6);
            --text: #0f0f14;
            --text-muted: #5a5a68;
            --border: rgba(255,255,255,0.5);
            --radius: 16px;
        """,
        "rules": "Use backdrop-filter blur on surfaces. Pastel radial gradients on body. Frosted white cards. Soft shadows. Generous radii (16-24px). Inner highlights for glass quality. No hard edges.",
    },
    "editorial": {
        "name": "Editorial Minimalism",
        "best_for": ["lawyer", "consultant", "accountant", "architect", "agency", "tech"],
        "css_vars": """
            --bg: #ffffff;
            --surface: #f4f4f5;
            --text: #0f0f14;
            --text-muted: #6b6b76;
            --border: #e4e4e7;
            --radius: 8px;
        """,
        "rules": "Flat design. Border-based depth only. High information density. One accent color used sparingly. Max 8px radius. No shadows on cards. Clean typography with Inter font.",
    },
    "warm": {
        "name": "Warm Editorial",
        "best_for": ["restaurant", "cafe", "bakery", "food", "home", "interior", "craft"],
        "css_vars": """
            --bg: #fffbf5;
            --surface: #fff8f0;
            --text: #1a1a1a;
            --text-muted: #6b5e50;
            --border: #f0e6d8;
            --radius: 12px;
        """,
        "rules": "Warm cream/beige backgrounds. Serif headings (Playfair Display). Earthy accent colors. Soft rounded corners. Cozy and inviting feel. Natural textures.",
    },
    "bold": {
        "name": "Bold & Energetic",
        "best_for": ["gym", "fitness", "sports", "adventure", "automotive", "construction"],
        "css_vars": """
            --bg: #0a0a0a;
            --surface: #1a1a1a;
            --text: #ffffff;
            --text-muted: #a0a0a0;
            --border: #2a2a2a;
            --radius: 8px;
        """,
        "rules": "Dark backgrounds. Bold typography. High contrast. Strong accent colors (red, orange, electric blue). Uppercase headings. Angular shapes. Energetic and powerful feel.",
    },
    "clinical": {
        "name": "Clean Clinical",
        "best_for": ["clinic", "dentist", "doctor", "hospital", "medical", "pharmacy", "health"],
        "css_vars": """
            --bg: #ffffff;
            --surface: #f0f9ff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --radius: 12px;
        """,
        "rules": "Clean white with light blue accents. Trust-building design. Professional and calming. Rounded but not playful. Clear hierarchy. Lots of whitespace. Blue/teal accent colors.",
    },
    "vibrant": {
        "name": "Vibrant & Playful",
        "best_for": ["school", "kids", "toys", "party", "event", "photography", "creative"],
        "css_vars": """
            --bg: #ffffff;
            --surface: #fef3c7;
            --text: #1f2937;
            --text-muted: #6b7280;
            --border: #fde68a;
            --radius: 16px;
        """,
        "rules": "Colorful gradients. Playful rounded shapes. Fun typography. Multiple accent colors. Bouncy animations. Friendly and approachable. Large radii (16-24px).",
    },
    "professional": {
        "name": "Professional Default",
        "best_for": ["store", "retail", "service", "plumber", "electrician", "solar", "general"],
        "css_vars": """
            --bg: #ffffff;
            --surface: #f8fafc;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --radius: 12px;
        """,
        "rules": "Clean and professional. Good contrast. Clear CTAs. Balanced whitespace. Standard 12px radius. Subtle shadows. Works for any business type.",
    },
}


def get_design_system(category: str) -> dict:
    """Pick the best design system for a business category."""
    cat = category.lower().strip()
    for system_key, system in DESIGN_SYSTEMS.items():
        for keyword in system["best_for"]:
            if keyword in cat or cat in keyword:
                return system
    return DESIGN_SYSTEMS["professional"]
