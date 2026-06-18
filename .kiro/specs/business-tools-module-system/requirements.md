# Requirements Document

## Introduction

The Business Tools Module System transforms the City Maps platform from a simple website-with-dashboard offering into a full **Multi-Tenant Business Operating System**. Instead of building industry-specific features, the platform provides universal capability modules (CRM, Billing, Booking, Inventory, etc.) that can be mixed and matched for any business type. The admin portal controls which modules are available to which website/business, and the business owner's existing dashboard dynamically displays only their enabled tools.

The architectural principle is: **Build capabilities, not business types.** A Salon gets CRM + Booking + Membership. A PG gets Property + Billing + CRM. A Solar company gets CRM + Project + Asset. Same modules, different combinations.

## Glossary

- **Module**: A self-contained business capability (e.g., CRM, Billing, Booking) that provides specific functionality to a business owner
- **Module_Registry**: The database-driven catalog of all available modules in the platform
- **Website_Module**: An assignment record linking a specific module to a specific website/business, controlling access
- **Industry_Template**: A pre-configured combination of modules suited for a particular business category
- **Owner_Dashboard**: The business owner's dashboard at `/api/panel/{website_id}` where they access their enabled tools
- **Admin_Module_Panel**: The admin interface for assigning/removing modules to/from websites
- **Module_Page**: The functional page for a module, accessible at `/api/panel/{website_id}/{module_slug}`
- **Tenant_Isolation**: The security principle ensuring each business can only access its own module data
- **Module_Category**: A grouping label for organizing modules (e.g., Operations, Marketing, Management)

## Requirements

### Requirement 1: Module Registry Database

**User Story:** As the platform operator, I want a centralized registry of all available modules stored in the database, so that I can manage the platform's capabilities without code changes.

**Acceptance Criteria:**
- A `modules` table exists with columns: id (UUID), slug (unique text), name (text), icon (text/emoji), description (text), category (text), is_premium (boolean), sort_order (integer), is_active (boolean), created_at
- A `website_modules` table exists with columns: id (UUID), website_id (UUID FK), module_id (UUID FK), enabled (boolean), enabled_at (timestamptz), config (JSONB), created_at
- Seed data populates at least 15 core modules covering: CRM, Billing, Booking, Inventory, Membership, Property, Asset, Project, Documents, WhatsApp Automation, AI Employee, Analytics, Customer Portal, Website Editor, Marketing Tools
- Each module has a unique slug used for URL routing (e.g., crm, billing, booking)
- Modules can be marked as premium (requires paid plan) or free (available to all)
- An `industry_templates` table exists with columns: id, category (text), template_name (text), module_slugs (JSONB array), is_default (boolean)

### Requirement 2: Admin Module Assignment Panel

**User Story:** As the platform admin, I want to control which modules each business website has access to, so that I can offer different tiers and customize the experience per client.

**Acceptance Criteria:**
- A new admin page exists at `/api/admin/modules` showing all websites in a searchable list
- Clicking a website opens a module toggle grid displaying all available modules with on/off switches
- Toggling a module immediately enables/disables it for that website (saves to website_modules)
- A Bulk Assign feature allows selecting a business category and enabling a set of modules for all websites in that category
- A Templates section shows industry templates; admin can apply a template to a website with one click
- Admin can create/edit industry templates (select modules to include, name the template, assign to a category)
- The page is protected by admin authentication (existing /api/admin/login)

### Requirement 3: Dynamic Owner Dashboard

**User Story:** As a business owner, I want my dashboard to show only the tools that are enabled for my business, organized clearly by category, so that I can find and use my business tools easily.

**Acceptance Criteria:**
- The owner panel (/api/panel/{website_id}) queries website_modules to determine which modules to display
- Modules are grouped by category with section headers (e.g., Business Operations, Marketing and Growth, Management)
- Each enabled module appears as a clickable card with icon, name, and short description
- Cards link to /api/panel/{website_id}/{module_slug} for the module functional page
- Modules not enabled for this website are NOT visible to the owner
- Existing tools (Social Post, QR Code, Logo, Analytics, etc.) are preserved as part of the Marketing Tools module
- The dashboard maintains the current dark-theme mobile-first design
- A stats section at the top (Views, Calls, WhatsApp clicks) is preserved from the current design
- Loading is fast (under 2 seconds) with no layout shifts

### Requirement 4: CRM Module Page

**User Story:** As a business owner with CRM enabled, I want to manage my leads and customers from my dashboard, so that I can track prospects and follow up effectively.

**Acceptance Criteria:**
- CRM page at /api/panel/{website_id}/crm shows a list of contacts (leads/customers)
- Business owner can add a new contact (name, phone, email, notes, status)
- Contacts can be filtered by status: New, Contacted, Interested, Converted, Lost
- Each contact shows last activity and can be edited
- A crm_contacts table stores: id, website_id, name, phone, email, status, notes, tags (JSONB), custom_fields (JSONB), created_at, updated_at
- Data is isolated by website_id (tenant isolation)
- Simple pipeline view showing count per status

### Requirement 5: Billing Module Page

**User Story:** As a business owner with Billing enabled, I want to create invoices and quotations, so that I can manage my business finances professionally.

**Acceptance Criteria:**
- Billing page at /api/panel/{website_id}/billing shows list of invoices/quotations
- Business owner can create a new invoice with: customer name, items (name, qty, rate), tax (GST percent), notes
- Invoice auto-calculates subtotal, tax amount, and total
- Invoice gets a sequential number (INV-001, INV-002, etc.) per website
- A Share on WhatsApp button generates a formatted message with invoice summary
- A billing_invoices table stores: id, website_id, invoice_number, customer_name, customer_phone, items (JSONB), subtotal, tax_percent, tax_amount, total, status (draft/sent/paid), notes, created_at
- Invoices can be marked as paid
- Data is isolated by website_id

### Requirement 6: Booking Module Page

**User Story:** As a business owner with Booking enabled, I want to manage appointments and bookings, so that my customers can schedule services efficiently.

**Acceptance Criteria:**
- Booking page at /api/panel/{website_id}/booking shows upcoming appointments
- Business owner can create a booking: customer name, phone, service, date, time, notes
- Bookings can be filtered by: Today, This Week, All
- Bookings have statuses: Pending, Confirmed, Completed, Cancelled
- A module_bookings table stores: id, website_id, customer_name, customer_phone, service, date, time, status, notes, created_at
- Owner can change booking status with one tap
- Data is isolated by website_id

### Requirement 7: Inventory Module Page

**User Story:** As a business owner with Inventory enabled, I want to track my products and stock levels, so that I never run out of essential items.

**Acceptance Criteria:**
- Inventory page at /api/panel/{website_id}/inventory shows product list with stock levels
- Business owner can add a product: name, category, price, stock quantity, minimum stock level
- Products with stock below minimum level are highlighted in red
- Stock can be updated (add/subtract) with one action
- A module_inventory table stores: id, website_id, name, category, price, stock_qty, min_stock, unit, created_at, updated_at
- Data is isolated by website_id
