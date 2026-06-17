# Requirements Document

## Introduction

The Ad Manager & Monetization System enables the City Maps platform to generate revenue from its network of 131+ business websites hosted on slug.city-maps.online. The system provides an ad management portal within the admin dashboard where the platform operator can create, target, and track advertising campaigns. It supports both Google AdSense integration and custom local ad campaigns, allowing businesses to advertise on other business websites within the network. Ad slots are embedded in business websites but remain hidden until activated by the ad manager, ensuring a clean user experience until monetization is engaged.

## Glossary

- **Ad_Manager**: The administrative portal within the City Maps admin dashboard used to create, manage, and track ad campaigns
- **Ad_Slot**: A predefined placement area on a business website where an advertisement can be rendered; hidden by default until activated
- **Ad_Creative**: The visual content of an advertisement including images, text, and call-to-action elements
- **Campaign**: A configured advertising effort with targeting rules, budget, schedule, and one or more ad creatives
- **Advertiser**: A business or individual who creates and pays for advertising campaigns on the City Maps network
- **Publisher_Site**: A business website within the City Maps network that displays ads in its ad slots
- **Impression**: A single instance of an ad being rendered and visible in a user's browser viewport
- **Click**: A user interaction where the visitor taps or clicks on a displayed advertisement
- **CPM**: Cost Per Mille; the price an advertiser pays per 1000 impressions of their ad
- **CPC**: Cost Per Click; the price an advertiser pays each time a user clicks their ad
- **Targeting_Rule**: A set of conditions that determines which publisher sites display a given campaign's ads
- **Ad_Format**: The visual type and position of an ad including banner, popup, sticky_footer, and in_content
- **Revenue_Dashboard**: A reporting interface that displays earnings, impressions, clicks, and financial metrics
- **Budget**: The maximum amount an advertiser allocates to spend on a campaign
- **Schedule**: The time-based configuration defining when a campaign's ads are active (date range, time of day, days of week)
- **A_B_Test**: A split test where multiple ad creatives are shown to different audience segments to measure performance differences

## Requirements

### Requirement 1: Ad Slot Embedding

**User Story:** As the platform operator, I want hidden ad slots embedded in every business website, so that I can activate advertising without modifying the website code later.

#### Acceptance Criteria

1. THE Ad_Slot rendering system SHALL embed ad slot containers in every business website HTML at predefined positions (header_banner, in_content, sticky_footer, popup)
2. WHILE an Ad_Slot has no active Campaign assigned, THE Ad_Slot rendering system SHALL keep the ad slot container hidden with zero visual footprint on the page
3. WHEN the Ad_Manager activates a Campaign targeting a Publisher_Site, THE Ad_Slot rendering system SHALL render the assigned Ad_Creative in the corresponding Ad_Slot position
4. THE Ad_Slot rendering system SHALL support four Ad_Format types: banner (728x90 or responsive), popup (centered overlay), sticky_footer (fixed bottom bar), and in_content (inline between sections)
5. WHEN a visitor's browser viewport intersects an active Ad_Slot, THE Ad_Slot rendering system SHALL fire an Impression tracking event

### Requirement 2: Campaign Management

**User Story:** As the platform operator, I want to create and manage advertising campaigns with targeting rules, so that I can serve relevant ads to the right audience on the right websites.

#### Acceptance Criteria

1. WHEN the Ad_Manager creates a new Campaign, THE Campaign management system SHALL require a campaign name, at least one Ad_Creative, at least one Targeting_Rule, a pricing model (CPM or CPC), and a Budget
2. THE Campaign management system SHALL support three Targeting_Rule types: area-based (city, region, pincode), business-based (specific website IDs), and category-based (business category matching)
3. WHEN multiple Campaigns target the same Ad_Slot on a Publisher_Site, THE Campaign management system SHALL select the campaign with the highest bid price for display
4. WHEN a Campaign Budget is fully consumed, THE Campaign management system SHALL pause the Campaign and stop serving its ads
5. WHEN the Ad_Manager updates a Campaign's Targeting_Rule or Ad_Creative, THE Campaign management system SHALL apply the changes within 60 seconds across all affected Publisher_Sites

### Requirement 3: Ad Scheduling

**User Story:** As the platform operator, I want to schedule campaigns by date range, time of day, and day of week, so that ads appear at the most effective times.

#### Acceptance Criteria

1. WHEN the Ad_Manager configures a Schedule for a Campaign, THE Scheduling system SHALL accept a start date, end date, active hours (start time and end time in IST), and active days of the week
2. WHILE the current time falls outside a Campaign's configured Schedule, THE Scheduling system SHALL suppress ad delivery for that Campaign
3. WHEN a Campaign's Schedule start date is reached, THE Scheduling system SHALL automatically activate ad delivery without manual intervention
4. WHEN a Campaign's Schedule end date passes, THE Scheduling system SHALL automatically pause the Campaign

### Requirement 4: Click and Impression Tracking

**User Story:** As the platform operator, I want accurate tracking of ad impressions and clicks, so that I can bill advertisers correctly and report performance.

#### Acceptance Criteria

1. WHEN a visitor's browser renders an Ad_Creative in the viewport for at least 1 second, THE Tracking system SHALL record one Impression event with the campaign ID, website ID, timestamp, and visitor IP hash
2. WHEN a visitor clicks on an Ad_Creative, THE Tracking system SHALL record one Click event with the campaign ID, website ID, timestamp, visitor IP hash, and redirect the visitor to the ad's destination URL
3. THE Tracking system SHALL deduplicate Impressions from the same visitor IP hash for the same Campaign within a 30-minute window
4. IF the Tracking system receives a request with an invalid or missing campaign ID, THEN THE Tracking system SHALL discard the event and return an error response
5. THE Tracking system SHALL store all tracking events in the Supabase analytics_events table with event_type values of ad_impression and ad_click

### Requirement 5: Revenue Tracking and Dashboard

**User Story:** As the platform operator, I want a revenue dashboard showing earnings from all campaigns, so that I can monitor monetization performance and financial health.

#### Acceptance Criteria

1. THE Revenue_Dashboard SHALL display total revenue, total impressions, total clicks, average CPM, average CPC, and click-through rate for a selected date range
2. WHEN the Ad_Manager selects a specific Campaign in the Revenue_Dashboard, THE Revenue_Dashboard SHALL display that Campaign's individual performance metrics including spend, impressions, clicks, CTR, and remaining budget
3. THE Revenue_Dashboard SHALL provide revenue breakdowns by Targeting_Rule type (area, business, category) and by Ad_Format
4. WHEN new Impression or Click events are recorded, THE Revenue_Dashboard SHALL reflect updated metrics within 5 minutes
5. THE Revenue_Dashboard SHALL display a daily revenue chart for the selected date range

### Requirement 6: Google AdSense Integration

**User Story:** As the platform operator, I want to integrate Google AdSense on business websites, so that I can earn revenue from Google's ad network alongside custom campaigns.

#### Acceptance Criteria

1. WHEN the Ad_Manager enables Google AdSense for a Publisher_Site, THE AdSense integration system SHALL inject the AdSense script tag and ad unit code into the designated Ad_Slot
2. THE AdSense integration system SHALL allow the Ad_Manager to configure the AdSense publisher ID and ad unit IDs per Ad_Slot position
3. WHILE a custom Campaign is assigned to an Ad_Slot, THE AdSense integration system SHALL prioritize the custom Campaign over Google AdSense in that slot
4. IF Google AdSense script fails to load within 5 seconds, THEN THE AdSense integration system SHALL hide the Ad_Slot and log a warning event

### Requirement 7: Advertiser Self-Service Portal

**User Story:** As a local business owner (advertiser), I want a self-service portal to create and manage my ad campaigns, so that I can promote my business on other City Maps websites without contacting the platform operator.

#### Acceptance Criteria

1. WHEN an Advertiser accesses the self-service portal, THE Portal system SHALL require authentication via the existing client_auth system
2. THE Portal system SHALL allow the Advertiser to create a Campaign by uploading Ad_Creative assets, selecting Targeting_Rules, choosing a pricing model (CPM or CPC), setting a Budget, and configuring a Schedule
3. WHEN an Advertiser submits a new Campaign, THE Portal system SHALL set the Campaign status to pending_review until the Ad_Manager approves it
4. THE Portal system SHALL display the Advertiser's active campaigns with real-time metrics including impressions, clicks, spend, and remaining budget
5. WHEN an Advertiser's Campaign Budget reaches 80 percent consumption, THE Portal system SHALL send a notification to the Advertiser via the platform notification system

### Requirement 8: A/B Testing of Ad Creatives

**User Story:** As the platform operator, I want to run A/B tests on ad creatives within a campaign, so that I can identify the highest-performing creative and maximize click-through rates.

#### Acceptance Criteria

1. WHEN the Ad_Manager enables A_B_Test mode for a Campaign, THE A_B_Test system SHALL accept two or more Ad_Creative variants with an even traffic split by default
2. WHILE an A_B_Test is active, THE A_B_Test system SHALL randomly assign each Impression to one creative variant based on the configured traffic split percentage
3. THE A_B_Test system SHALL track Impressions, Clicks, and CTR independently for each Ad_Creative variant
4. WHEN an A_B_Test has accumulated at least 1000 Impressions per variant, THE A_B_Test system SHALL identify the statistically leading variant and display a recommendation to the Ad_Manager
5. WHEN the Ad_Manager selects a winning variant, THE A_B_Test system SHALL allocate 100 percent of traffic to that variant and archive the other variants

### Requirement 9: Budget Management

**User Story:** As the platform operator, I want campaign budgets to be enforced in real-time, so that advertisers are never overcharged and campaigns stop when their budget is exhausted.

#### Acceptance Criteria

1. THE Budget management system SHALL track cumulative spend for each Campaign by summing CPM charges (impressions divided by 1000 multiplied by CPM rate) and CPC charges (clicks multiplied by CPC rate)
2. WHEN a Campaign's cumulative spend reaches the configured Budget limit, THE Budget management system SHALL pause the Campaign within 10 seconds
3. THE Budget management system SHALL support daily budget caps in addition to total campaign budgets
4. WHEN a Campaign's daily budget cap is reached, THE Budget management system SHALL pause the Campaign until the next calendar day (IST midnight)
5. IF the Budget management system detects a billing discrepancy greater than 5 percent between tracked events and calculated spend, THEN THE Budget management system SHALL flag the Campaign for manual review

### Requirement 10: Area-Based Ad Targeting

**User Story:** As the platform operator, I want to target ads by geographic area, so that local advertisers can reach customers in their service region.

#### Acceptance Criteria

1. THE Targeting system SHALL allow Campaigns to be targeted by one or more of: city name, region name, or pincode
2. WHEN a Campaign has area-based Targeting_Rules, THE Targeting system SHALL match the Campaign to Publisher_Sites whose registered address contains the specified city, region, or pincode
3. WHEN a Publisher_Site's location matches multiple area-targeted Campaigns, THE Targeting system SHALL apply the bid priority ranking to select the displayed Campaign
4. THE Targeting system SHALL use the location data already stored in the websites table (city, area, pincode fields) for matching

### Requirement 11: Category-Based Ad Targeting

**User Story:** As the platform operator, I want to target ads by business category, so that relevant ads appear on related business websites (e.g., food delivery ads on restaurant sites).

#### Acceptance Criteria

1. THE Targeting system SHALL allow Campaigns to target one or more business categories (restaurant, salon, gym, clinic, hotel, retail, cafe, photographer, real_estate, school, solar, legal)
2. WHEN a Campaign has category-based Targeting_Rules, THE Targeting system SHALL serve that Campaign's ads only on Publisher_Sites whose registered category matches the targeting criteria
3. THE Targeting system SHALL use the category data already stored in the websites table for matching
