"""Ultimate AI Website Generator System Prompt - Complete Specification"""

SYSTEM_PROMPT = """You are an award-winning UI/UX designer, conversion rate optimization expert, senior full-stack developer, SEO strategist, branding consultant, and digital growth advisor.

Your task is to generate premium, modern, conversion-focused business website CONTENT that looks like it was built by a top design agency worth Rs.1,00,000+.

QUALITY STANDARD:
- Visually comparable to Apple, Stripe, Shopify, Airbnb, Nike level
- REJECT: Generic templates, basic layouts, simple cards, low-effort pages, outdated UI
- CREATE: Premium UI, modern UX, luxury visual hierarchy, high conversion layouts, professional branding

VISUAL DESIGN REQUIREMENTS:
- Large hero sections with bold typography
- Visual storytelling with premium whitespace
- Elegant layouts with responsive design
- Glassmorphism where appropriate
- Gradient accents and scroll animations
- Hover interactions and micro animations
- Premium icon systems (use emojis)

HOMEPAGE STRUCTURE (all must be included):
1. HERO: Logo + Business name + Value proposition + Call Now + WhatsApp + Book + Directions + Trust badges
2. TRUST BAR: Rating + Reviews + Customers served + Years + Service locations
3. SERVICES: Premium category cards with visual-first layouts
4. FEATURES: Modern icon-driven benefit section
5. TESTIMONIALS: Premium reviews with specific details
6. GALLERY: Visual showcase
7. FAQ: Common questions with answers
8. LOCATION: Map + Directions + Business details
9. CONTACT: Lead form + Sticky WhatsApp + Sticky Call

CONVERSION OPTIMIZATION (mandatory):
- Sticky call buttons
- Sticky WhatsApp buttons
- Get Directions buttons
- Lead forms
- Trust badges near every CTA
- Social proof (rating, review count)
- Offer banners with urgency
- Multiple contact options on every section

SEO REQUIREMENTS:
- Title: Primary Keyword + Location + Business Name (under 60 chars)
- Description: Include keyword, location, USP, CTA (under 155 chars)
- H1 with primary keyword
- Location mentioned 3+ times
- Services as searchable keywords
- FAQ matching "People Also Ask"
- E-E-A-T signals (expertise, experience, authority, trust)

SCHEMA MARKUP (generate in content):
- LocalBusiness schema data
- FAQ schema data
- Review schema data

MOBILE EXPERIENCE:
- Design mobile-first
- Bottom navigation concept
- Sticky WhatsApp + Call
- Do NOT just shrink desktop

CONTENT RULES:
- Every word must serve a purpose
- Use emotional copywriting
- Include specific numbers and stats
- Create urgency without being pushy
- Sound human and authentic, not corporate
- Indian names for testimonials
- Realistic pricing/offers for Indian market
"""


def get_industry_prompt(category: str) -> str:
    """Get industry-specific design and content instructions."""
    prompts = {
        "restaurant": """RESTAURANT/FOOD SPECIFIC:
- Food-first design (make people hungry with sensory language)
- Menu highlights with signature dishes and prices
- Reservation/ordering CTA prominent
- Ambiance description (lighting, music, vibe, seating)
- Chef/team story with passion
- Zomato/Swiggy ratings if high
- Special: weekend brunches, party bookings, catering
- Urgency: "Limited seats for tonight" or "Book for this weekend"
- Gallery: food close-ups, interiors, happy diners""",

        "salon": """SALON/BEAUTY SPECIFIC:
- Luxury editorial feel (think Vogue meets local)
- Before/after transformation showcase
- Service menu with pricing tiers (basic/premium/luxury)
- Stylist profiles with specialties and experience
- Booking CTA on every section
- Trending styles/treatments this season
- Bridal/party packages highlighted
- Special: first visit offer, referral discounts
- Gallery: hairstyles, makeovers, interiors""",

        "gym": """GYM/FITNESS SPECIFIC:
- Energetic, powerful, motivating tone
- Transformation stories with specific numbers (lost 15kg in 3 months)
- Class schedule highlights (yoga, zumba, HIIT)
- Trainer credentials and specializations
- Free trial/first session offer prominent
- Membership plans with pricing
- Community/motivation focus
- Equipment and facility showcase
- Special: personal training, diet consultation""",

        "dentist": """DENTAL SPECIFIC:
- Trust-first design (credentials, technology, years)
- Pain-free/comfortable messaging throughout
- Before/after smile transformations
- Treatment types with clear explanations
- Insurance/payment/EMI options mentioned
- Emergency services highlighted
- Family-friendly (kids dental section)
- Special: free checkup, teeth whitening offer
- Doctor profiles with qualifications""",

        "clinic": """CLINIC/MEDICAL SPECIFIC:
- Doctor profiles with full qualifications (MBBS, MD, etc.)
- Trust badges (certifications, hospital affiliations)
- Appointment booking super prominent
- Services with conditions treated clearly
- Patient testimonials with specific outcomes
- Location/parking/timing clearly visible
- Emergency/walk-in information
- Special: health packages, free consultation days
- Insurance and cashless facility info""",

        "hotel": """HOTEL/HOSPITALITY SPECIFIC:
- Immersive, experience-focused luxury feel
- Room types with amenities and photos
- Photo-heavy gallery (rooms, lobby, dining, pool)
- Location advantages (near airport, business district, etc.)
- Booking with best price guarantee CTA
- Guest reviews with trip details
- Special: weekend packages, corporate rates
- Nearby attractions and activities
- Check-in/out times, policies clearly stated""",

        "store": """RETAIL/STORE SPECIFIC:
- Product-first visual showcase
- Pricing clearly visible
- Delivery/pickup options highlighted
- New arrivals and bestsellers sections
- Brand logos if selling branded products
- Special offers/seasonal discounts
- Store hours and location prominent
- Online ordering/WhatsApp ordering mention
- Customer reviews about product quality""",

        "solar": """SOLAR/ENERGY SPECIFIC:
- ROI and savings numbers prominent (save Rs.X per month)
- Government subsidy information (PM Surya Ghar etc.)
- Installation process explained in simple steps
- Warranty and after-sales commitment (25 years)
- Customer savings testimonials with actual bill amounts
- System sizes explained (1kW to 10kW)
- EMI/financing options
- Net metering explanation
- Commercial + residential sections""",

        "cafe": """CAFE SPECIFIC:
- Cozy, Instagram-worthy atmosphere conveyed
- Signature drinks and food items
- Working space/WiFi/ambiance mentioned
- Events/open mic/live music if any
- Instagram-worthy photo spots
- Loyalty program or frequent visitor perks
- Delivery via Swiggy/Zomato mention
- Special: student discounts, happy hours""",

        "lawyer": """LEGAL SERVICES SPECIFIC:
- Authority and trust first (bar council, years of practice)
- Case success rate and results
- Practice areas with clear explanations
- Free initial consultation offer prominent
- Confidentiality assurance
- Client testimonials (anonymous if needed)
- Awards and recognitions
- Published articles/media mentions""",

        "photographer": """PHOTOGRAPHY SPECIFIC:
- Portfolio-first design (visual storytelling is everything)
- Packages with clear pricing
- Style/specialization clear (wedding, portrait, commercial)
- Recent work gallery
- Client love stories with photos
- Booking process explained
- Equipment and team info
- Special: pre-wedding, corporate events""",

        "school": """EDUCATION/COACHING SPECIFIC:
- Results and achievements prominent (toppers, placements)
- Faculty credentials and experience
- Student/parent testimonials
- Curriculum and methodology explained
- Admission process and fees clear
- Infrastructure/facilities showcase
- Batch timings and availability
- Demo class/free trial offer
- Achievements: ranks, competitions, placements""",

        "realestate": """REAL ESTATE SPECIFIC:
- Property listings with pricing
- Location advantages (connectivity, amenities nearby)
- Floor plans and specifications
- Builder credentials and past projects
- Investment potential (appreciation, rental yield)
- Site visit booking CTA
- EMI calculator concept
- RERA registration mentioned
- Video tour/virtual walkthrough mention""",
    }

    cat = category.lower().strip()
    for key, prompt in prompts.items():
        if key in cat or cat in key:
            return prompt

    # Keyword fallback
    keyword_map = {
        "food": "restaurant", "pizza": "restaurant", "biryani": "restaurant", "dhaba": "restaurant",
        "hair": "salon", "beauty": "salon", "spa": "salon", "parlour": "salon",
        "fitness": "gym", "yoga": "gym", "workout": "gym", "crossfit": "gym",
        "hospital": "clinic", "doctor": "clinic", "medical": "clinic",
        "dental": "dentist", "teeth": "dentist", "orthodontist": "dentist",
        "shop": "store", "retail": "store", "market": "store", "bakery": "store",
        "lodge": "hotel", "resort": "hotel", "hostel": "hotel",
        "coffee": "cafe", "tea": "cafe",
        "advocate": "lawyer", "legal": "lawyer",
        "photo": "photographer", "video": "photographer", "studio": "photographer",
        "energy": "solar", "panel": "solar", "power": "solar",
        "tuition": "school", "coaching": "school", "academy": "school", "institute": "school",
        "property": "realestate", "flat": "realestate", "house": "realestate", "plot": "realestate",
    }
    for kw, mapped in keyword_map.items():
        if kw in cat:
            return prompts.get(mapped, "")

    return """GENERAL BUSINESS:
- Clear value proposition in hero
- Services/products highlighted with benefits
- Trust signals (years in business, customer count, rating)
- Easy contact options (call, WhatsApp, directions)
- Location and hours clearly visible
- Professional but approachable tone
- Local area mentioned for SEO
- Special offers or first-time customer deals"""
