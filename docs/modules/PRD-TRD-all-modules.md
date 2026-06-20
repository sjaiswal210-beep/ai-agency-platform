# Module 1: Subscription Manager
## PRD (Product Requirements Document)

### Overview
Manages recurring deliveries and auto-billing for subscription-based businesses.

### Target Categories
Dairy/milk provider, tiffin service, water can supplier, newspaper distributor, chai pass, laundry subscription, gym monthly, meal plans

### Core Features

1. **Customer Subscriptions**
   - Customer name, phone, address, delivery location
   - Product subscribed (milk 500ml, tiffin lunch, water can 20L)
   - Frequency: daily, alternate days, specific weekdays, weekly, monthly
   - Quantity per delivery
   - Start date, pause/resume with dates
   - Price per unit, monthly total auto-calculated

2. **Delivery Calendar**
   - Daily view: which customers get delivery today
   - Mark delivered / not delivered / extra quantity
   - Delivery boy assignment per route/area
   - Route sequence (optimized delivery order)
   - Holiday/off-day management (no delivery on Sundays)

3. **Auto Billing**
   - Monthly bill generation (count deliveries x price)
   - Deduct paused/off days automatically
   - Extra orders added to bill
   - SMS/WhatsApp bill to customer
   - Payment tracking (paid/pending/partial)
   - Payment method (cash, UPI, bank transfer)
   - Payment reminder on due date

4. **Route Management**
   - Group customers by area/locality/society
   - Assign delivery boy per route
   - Sequence within route (building 1 -> 2 -> 3)
   - Route-wise daily delivery sheet (printable)
   - Route change history

5. **Product Management**
   - Products offered (Full cream milk, toned milk, paneer, curd)
   - Per-unit pricing
   - Availability (daily/on-demand)
   - Seasonal products

6. **Customer Communication**
   - Holiday announcement (no delivery tomorrow)
   - Price change notification
   - New product launch message
   - Payment reminder
   - Bill sharing via WhatsApp

7. **Reports**
   - Monthly revenue per route
   - Customer-wise delivery count
   - Pending payments report
   - Delivery boy performance
   - Product-wise demand

---

## TRD (Technical Requirements Document)

### Database Tables

**subscriptions**
- id, organization_id, customer_name, customer_phone, address
- product_id, quantity, frequency (daily/alternate/weekdays/weekly)
- weekdays TEXT[] (for specific day selection)
- price_per_unit, start_date, status (active/paused/cancelled)
- pause_from, pause_until, delivery_boy_id
- route_id, route_sequence, notes

**subscription_products**
- id, organization_id, name, unit (ltr/kg/pcs/can)
- price, is_available, category

**delivery_log**
- id, organization_id, subscription_id, date
- status (delivered/skipped/extra/holiday)
- quantity, delivery_boy_id, notes, delivered_at

**subscription_bills**
- id, organization_id, customer_phone, month, year
- total_deliveries, total_amount, extras_amount
- deductions, final_amount, status (generated/sent/paid/overdue)
- paid_amount, paid_date, payment_method

**delivery_routes**
- id, organization_id, name, area, delivery_boy_name
- delivery_boy_phone, sequence_order JSONB

### API Endpoints
- GET /api/org/{org_id}/subscriptions - list all
- POST /api/org/{org_id}/subscriptions - create
- PUT /api/org/{org_id}/subscriptions/{id} - update/pause/resume
- GET /api/org/{org_id}/subscriptions/today - today's delivery list
- POST /api/org/{org_id}/subscriptions/mark-delivery - mark delivered
- GET /api/org/{org_id}/subscriptions/bills - list bills
- POST /api/org/{org_id}/subscriptions/generate-bills - auto-generate monthly
- GET /api/org/{org_id}/subscriptions/routes - routes
- GET /api/org/{org_id}/subscriptions/dashboard - stats

### UI Components
- Subscription list with search/filter
- Today's delivery board (route-wise)
- Mark delivery checkboxes
- Bill generator + preview
- Route planner
- Customer detail with delivery history

---
---

# Module 2: Job Card / Service Ticket
## PRD

### Overview
Complete service management for repair/maintenance businesses.

### Target Categories
Garage (bike/car), electrician, plumber, AC repair, mobile repair, appliance repair, pest control, CCTV installation, computer repair

### Core Features

1. **Job Card Creation**
   - Customer details (name, phone, address)
   - Device/vehicle details (brand, model, registration no, IMEI)
   - Problem description (customer's words)
   - Diagnosis notes (technician findings)
   - Estimated cost + time
   - Priority (normal/urgent/emergency)
   - Assign technician/mechanic

2. **Job Status Pipeline**
   - Received -> Diagnosed -> Awaiting Parts -> In Progress -> Quality Check -> Ready -> Delivered
   - Status change timestamps
   - WhatsApp status update to customer on each change
   - Photo at each stage (before/during/after)

3. **Parts & Material Tracking**
   - Parts used per job (from inventory)
   - External parts ordered (vendor, cost, ETA)
   - Labor charges separate from parts cost
   - Final bill = parts + labor + GST

4. **Customer Vehicle/Device History**
   - All past jobs for same customer/vehicle
   - Service interval reminders (next service due)
   - Warranty on past repairs

5. **Technician Management**
   - Assign jobs to specific technician
   - Workload view (how many active jobs each)
   - Completion rate / performance
   - Specialization tags

6. **Service Reminders**
   - Auto-remind after X days/km (vehicle service)
   - AMC (Annual Maintenance Contract) tracking
   - Insurance/PUC expiry reminders
   - Next checkup due notification

7. **Quotation & Invoice**
   - Estimate before work starts
   - Final invoice after completion
   - Payment tracking (advance taken, balance due)
   - GST invoice generation

### Database Tables

**job_cards**
- id, organization_id, job_number (auto: JOB-0001)
- customer_name, customer_phone, customer_address
- device_type (vehicle/mobile/appliance/electrical/plumbing)
- device_brand, device_model, registration_no, serial_number
- problem_description, diagnosis_notes
- assigned_to, priority (normal/urgent/emergency)
- status (received/diagnosed/awaiting_parts/in_progress/quality_check/ready/delivered/cancelled)
- estimated_cost, estimated_time_hours
- actual_cost, parts_cost, labor_cost
- warranty_until, photos JSONB
- received_at, completed_at, delivered_at

**job_parts**
- id, job_card_id, organization_id
- part_name, quantity, unit_price, total_price
- source (stock/ordered), vendor, status (available/ordered/installed)

**job_status_history**
- id, job_card_id, from_status, to_status
- changed_by, notes, photo_url, created_at

**service_reminders**
- id, organization_id, customer_phone, customer_name
- device_info, reminder_type (service_due/amc/insurance/warranty)
- due_date, message, status (pending/sent/completed)

**technicians**
- id, organization_id, name, phone, specialization
- is_active, active_jobs_count

### API Endpoints
- CRUD for job_cards with status transitions
- GET /today's-jobs, /pending-parts, /ready-for-delivery
- POST /status-update (triggers WhatsApp notification)
- GET /customer/{phone}/history
- GET /reminders/due-today
- GET /dashboard (stats: total jobs, pending, revenue today)

---
---

# Module 3: Custom Order Tracker
## PRD

### Overview
Track custom/made-to-order items through production stages.

### Target Categories
Tailor, furniture maker, bakery (custom cakes/boxes), jewellery, printing press, gift shop, interior design fabrication

### Core Features

1. **Order Intake**
   - Customer details
   - Item description with specifications
   - Reference images (customer shows what they want)
   - Measurements/dimensions (tailor: chest, waist; furniture: L x W x H)
   - Material selection (fabric, wood type, gold karat)
   - Agreed price, advance taken
   - Promised delivery date

2. **Production Pipeline**
   - Order Received -> Design/Cutting -> Production/Stitching -> Finishing -> Quality Check -> Ready -> Delivered
   - Customizable stages per business type
   - Assign to craftsman/worker
   - Progress percentage

3. **Measurement Database**
   - Customer body measurements (tailor)
   - Room/space dimensions (furniture/interior)
   - Stored per customer - reuse for repeat orders

4. **Design Catalog**
   - Photo catalog of designs/styles offered
   - Customer can pick from catalog
   - Custom design upload

5. **Delivery Management**
   - Promised date tracking
   - Delay notification to customer
   - Fitting/trial appointment (tailor)
   - Installation scheduling (furniture)
   - Alteration/modification tracking post-delivery

6. **Billing**
   - Advance + balance tracking
   - Material cost + making charges breakdown
   - EMI option tracking

### Database Tables

**custom_orders**
- id, organization_id, order_number
- customer_name, customer_phone
- item_description, specifications JSONB
- reference_images JSONB, measurements JSONB
- material, material_cost, making_charges, total_price
- advance_paid, balance_due
- assigned_to, promised_date, actual_delivery_date
- status (received/design/production/finishing/quality_check/ready/delivered/alteration)
- progress_percent, notes

**customer_measurements**
- id, organization_id, customer_phone, customer_name
- measurement_type (body/room/custom)
- data JSONB (flexible key-value for any measurement)
- updated_at

**design_catalog**
- id, organization_id, name, category
- images JSONB, description, base_price
- is_active

**order_stages**
- id, organization_id, name, description
- sort_order, color

---
---

# Module 4: Delivery Route Manager
## PRD

### Overview
Manage delivery operations with routes, drivers, and proof of delivery.

### Target Categories
Dairy delivery, tiffin service, pharmacy home delivery, furniture delivery, water can, newspaper, grocery delivery, laundry pickup/drop

### Core Features

1. **Route Planning**
   - Define routes by area/locality
   - Sequence stops within route
   - Assign delivery person per route
   - Time estimates per stop

2. **Daily Delivery Board**
   - Today's deliveries grouped by route
   - Checkbox: delivered / not home / refused
   - Proof of delivery (photo/signature)
   - Notes per delivery

3. **Delivery Person Management**
   - Assign routes to delivery staff
   - Track active/completed deliveries
   - Fuel/travel allowance tracking
   - Performance (deliveries/day, on-time %)

4. **Customer Notifications**
   - Out for delivery notification
   - Delivered confirmation
   - Attempted delivery (not home)
   - Rescheduled delivery

5. **Pickup Management** (for laundry, return items)
   - Schedule pickups
   - Combine with delivery route
   - Container/item collection tracking

### Database Tables

**delivery_routes**
- id, organization_id, name, area
- assigned_to_name, assigned_to_phone
- stops JSONB (ordered array of customer stops)
- days_active TEXT[] (which weekdays)

**delivery_tasks**
- id, organization_id, route_id, date
- customer_name, customer_phone, customer_address
- items JSONB, status (pending/out/delivered/failed/rescheduled)
- delivery_person, delivered_at, proof_photo_url
- notes, attempt_count

**delivery_persons**
- id, organization_id, name, phone
- vehicle_type, vehicle_number
- is_active, routes_assigned TEXT[]

---
---

# Module 5: Catalog / Digital Menu
## PRD

### Overview
Visual product/service catalog shareable via WhatsApp link.

### Target Categories
Restaurant, sweet mart, fashion store, electrical shop, hardware store, nursery, stationery, juice shop, ice cream parlor, gift shop, furniture showroom

### Core Features

1. **Product/Menu Items**
   - Name, description, price, image
   - Category/section grouping
   - Variants (size: S/M/L, color: red/blue)
   - In stock / out of stock toggle
   - Vegetarian/non-veg tag (food)
   - Best seller / new arrival / featured tags

2. **Categories**
   - Organize items into sections
   - Custom sort order
   - Category images

3. **Shareable Link**
   - Public URL: /menu/{org_slug}
   - WhatsApp share button
   - QR code to menu
   - Mobile-optimized beautiful display

4. **Quick Actions for Customers**
   - Inquiry button (WhatsApp message with item name)
   - Call to order button
   - Add to cart (optional)

5. **Search & Filter**
   - Search within menu
   - Filter by category, price range, veg/non-veg

6. **Menu Customization**
   - Brand colors and logo
   - Cover image
   - Business hours display
   - Delivery/pickup info

### Database Tables

**catalog_categories**
- id, organization_id, name, image_url, sort_order, is_active

**catalog_items**
- id, organization_id, category_id
- name, description, price, compare_price (MRP for discount)
- images JSONB, variants JSONB
- tags TEXT[] (bestseller, new, featured, veg, nonveg)
- in_stock BOOLEAN, sort_order
- is_active

### Public Page
- GET /menu/{org_slug} - beautiful responsive catalog page
- Search, filter, WhatsApp inquiry button per item
- Shareable via link/QR

---
---

# Module 6: Student / Batch Manager
## PRD

### Overview
Manage students, batches, attendance, and fees for educational businesses.

### Target Categories
Coaching center, school tuition, music class, dance academy, yoga/gym classes, driving school, computer training, art class, sports academy

### Core Features

1. **Batch Management**
   - Batch name (e.g., "Class 10 Science Batch A")
   - Schedule (Mon/Wed/Fri, 4:00-5:30 PM)
   - Teacher/instructor assignment
   - Capacity, current strength
   - Start date, end date
   - Fee per month/quarter

2. **Student Enrollment**
   - Student name, phone (parent phone)
   - Batch assignment (can be in multiple batches)
   - Enrollment date
   - Fee structure (monthly/quarterly/yearly)
   - Emergency contact
   - Notes/special requirements

3. **Attendance**
   - Batch-wise daily attendance
   - Present/absent/late
   - Attendance percentage per student
   - Alert if attendance drops below threshold
   - Notify parent if absent

4. **Fee Management**
   - Monthly fee generation per student
   - Payment tracking (paid/due/overdue)
   - Fee reminder to parents (WhatsApp)
   - Discount/scholarship tracking
   - Receipt generation
   - Late fee calculation

5. **Progress / Performance**
   - Test scores entry per student
   - Progress report sharing with parents
   - Topic/chapter completion tracking
   - Homework/assignment tracking

6. **Communication**
   - Broadcast to all students/parents in batch
   - Holiday/off-day announcement
   - Exam schedule sharing
   - Class cancellation notification
   - Fee reminder

### Database Tables

**batches**
- id, organization_id, name, description
- schedule JSONB (weekdays + time)
- teacher_name, capacity, current_strength
- fee_amount, fee_frequency (monthly/quarterly)
- start_date, end_date, is_active

**students**
- id, organization_id, name, phone, parent_phone
- email, address, date_of_birth
- enrollment_date, status (active/completed/dropped)
- notes, emergency_contact

**student_batches**
- id, student_id, batch_id, joined_date, status

**student_attendance**
- id, organization_id, batch_id, student_id, date
- status (present/absent/late), marked_by

**student_fees**
- id, organization_id, student_id, month, year
- amount, discount, final_amount
- status (due/paid/overdue/partial)
- paid_date, payment_method, receipt_number

**student_scores**
- id, organization_id, student_id, batch_id
- test_name, subject, max_marks, obtained_marks
- date, remarks

---
---

# Module 7: Event / Venue Manager
## PRD

### Overview
Manage venue bookings, event coordination, and vendor management.

### Target Categories
Marriage hall, banquet hall, event planner, party decorator, tent house, resort events, DJ/sound rental, balloon decorator, catering service

### Core Features

1. **Venue/Date Booking**
   - Calendar showing available/booked dates
   - Morning/Evening/Full day slots
   - Multiple halls/venues within one property
   - Tentative vs confirmed bookings
   - Advance payment to confirm

2. **Event Details**
   - Event type (wedding, reception, birthday, corporate)
   - Guest count
   - Client details
   - Selected package/menu
   - Special requirements (no non-veg, live band, etc.)

3. **Package Builder**
   - Pre-defined packages (Silver, Gold, Platinum)
   - Add-on items (extra decoration, live band, valet)
   - Per-plate pricing with head count
   - Custom package creation

4. **Vendor Coordination**
   - Caterer, DJ, photographer, florist, decorator
   - Vendor contact + assignment per event
   - Vendor payment tracking
   - Vendor performance notes

5. **Event Checklist**
   - Pre-event setup tasks
   - Day-of coordination items
   - Post-event cleanup
   - Task assignment to team members

6. **Billing & Payments**
   - Quotation to client
   - Advance booking amount
   - Progressive payment milestones
   - Final settlement
   - Vendor payment schedule

### Database Tables

**venues**
- id, organization_id, name, capacity, type
- amenities JSONB, photos JSONB, is_active

**event_bookings**
- id, organization_id, venue_id
- client_name, client_phone, event_type
- event_date, slot (morning/evening/fullday)
- guest_count, package_id
- status (tentative/confirmed/completed/cancelled)
- total_amount, advance_paid, balance_due
- special_requirements, notes

**event_packages**
- id, organization_id, name, description
- price, per_plate_price, min_guests
- includes JSONB, add_ons JSONB

**event_vendors**
- id, organization_id, event_booking_id
- vendor_name, vendor_phone, service_type
- amount, payment_status, notes

**event_checklist**
- id, event_booking_id, task, assigned_to
- due_date, status (pending/done), sort_order

---
---

# Module 8: Renewal / Reminder Engine
## PRD

### Overview
Automated reminder system for expiry dates, renewals, and follow-ups.

### Target Categories
Insurance agent, optical shop, vehicle service, AMC providers, diagnostic lab, dental checkups, pest control, CCTV AMC, warranty tracking, subscription renewals

### Core Features

1. **Reminder Types**
   - Insurance renewal (health, vehicle, life, home)
   - Vehicle service due (every 5000km / 6 months)
   - AMC renewal (AC, elevator, generator, pest control)
   - Warranty expiry
   - Eye checkup (yearly)
   - Dental cleaning (6 monthly)
   - Document renewal (PUC, fitness, license)
   - Subscription renewal

2. **Reminder Setup**
   - Customer name, phone
   - Item/policy/device details
   - Due date / renewal date
   - Remind before: 30 days, 7 days, 1 day, on due date
   - Auto-send via WhatsApp/SMS
   - Recurrence (yearly, 6-monthly, quarterly)

3. **Notification Channels**
   - WhatsApp message (primary)
   - SMS fallback
   - Dashboard notification
   - Email (optional)

4. **Status Tracking**
   - Pending -> Reminded -> Renewed/Completed / Lapsed
   - Customer response tracking
   - Revenue from renewals

5. **Bulk Operations**
   - Import renewals from CSV
   - Bulk reminders for same-day expirations
   - Template messages per reminder type

6. **Reports**
   - Upcoming renewals (next 7/30/90 days)
   - Lapsed/missed renewals
   - Revenue from renewals
   - Customer-wise policy summary

### Database Tables

**reminders**
- id, organization_id
- customer_name, customer_phone, customer_email
- type (insurance/service/amc/warranty/checkup/document/subscription)
- item_description, reference_number
- due_date, remind_days_before TEXT[] (e.g., [30, 7, 1])
- recurrence (none/yearly/half_yearly/quarterly/monthly)
- message_template, status (active/reminded/renewed/lapsed)
- last_reminded_at, renewed_at
- amount (renewal cost), notes

**reminder_logs**
- id, reminder_id, sent_at, channel (whatsapp/sms/email)
- status (sent/delivered/failed), response

---
---

# Module 9: Client Project Board
## PRD

### Overview
Visual project management with client collaboration and approvals.

### Target Categories
Interior designer, architect, contractor, freelancer, digital agency, event planner, construction company

### Core Features

1. **Project Creation**
   - Project name, client details
   - Scope description
   - Budget (estimated + actual tracking)
   - Timeline (start, milestones, end)
   - Team members assigned

2. **Milestone Tracking**
   - Break project into phases/milestones
   - Each milestone: tasks, deliverables, deadline
   - Progress percentage auto-calculated
   - Payment linked to milestone completion

3. **Client Sharing**
   - Shareable project link (password protected)
   - Client can view progress, photos, updates
   - Approval requests (design approval, material approval)
   - Comments/feedback from client

4. **Document & Photo Management**
   - Upload designs, 3D renders, floor plans
   - Before/during/after photos
   - Material selections and approvals
   - Contracts and agreements

5. **Budget Tracking**
   - Category-wise budget (material, labor, transport)
   - Actual spend vs estimate
   - Invoice/receipt attachment
   - Vendor payment tracking

6. **Updates & Communication**
   - Daily/weekly progress updates
   - Photo updates to client via WhatsApp
   - Status changes notification
   - Meeting notes

### Database Tables

**client_projects**
- id, organization_id, name, client_name, client_phone
- description, budget_estimated, budget_actual
- start_date, end_date, status (planning/active/on_hold/completed)
- progress_percent, access_code (for client view)

**project_milestones**
- id, project_id, name, description
- deadline, status (pending/in_progress/completed)
- payment_amount, payment_status
- sort_order

**project_tasks**
- id, milestone_id, project_id, title
- assigned_to, status (todo/doing/done)
- due_date, notes

**project_updates**
- id, project_id, title, description
- photos JSONB, type (progress/approval_request/note)
- client_visible BOOLEAN, client_approved BOOLEAN
- created_at

**project_expenses**
- id, project_id, category, description
- amount, vendor, receipt_url, date

---
---

# Module 10: Fleet / Vehicle Manager
## PRD

### Overview
Manage vehicles, drivers, trips, and maintenance for transport businesses.

### Target Categories
Cab/taxi service, transport company, packers & movers, delivery fleet, school bus, ambulance, car rental, logistics

### Core Features

1. **Vehicle Registry**
   - Vehicle number, type (car/bike/truck/van)
   - Make, model, year, color
   - Insurance expiry, PUC expiry, fitness certificate
   - Current odometer reading
   - Status (available/on_trip/maintenance)

2. **Driver Management**
   - Name, phone, license number, license expiry
   - Assigned vehicle
   - Documents (license, Aadhar, police verification)
   - Performance/rating
   - Availability schedule

3. **Trip/Booking Management**
   - Customer booking (pickup, drop, time)
   - Driver + vehicle assignment
   - Trip status (booked/dispatched/in_progress/completed)
   - Distance, fare calculation
   - OTP-based start/end

4. **Maintenance Log**
   - Service history per vehicle
   - Oil change, tire, brake, battery tracking
   - Next service due reminder
   - Repair cost tracking
   - Vendor/garage details

5. **Fuel Tracking**
   - Fuel fill entries (date, liters, amount)
   - Mileage calculation (km/liter)
   - Monthly fuel expense per vehicle
   - Anomaly detection (sudden mileage drop)

6. **Expense Tracking**
   - Toll, parking, challan tracking
   - Insurance premium payments
   - EMI tracking per vehicle
   - Monthly P&L per vehicle

7. **Compliance & Documents**
   - Insurance renewal alerts
   - PUC renewal alerts
   - Fitness certificate renewal
   - Driver license expiry
   - Dashboard showing all upcoming expirations

### Database Tables

**fleet_vehicles**
- id, organization_id, vehicle_number, type
- make, model, year, color, fuel_type
- insurance_expiry, puc_expiry, fitness_expiry
- odometer, status (available/on_trip/maintenance/inactive)
- assigned_driver_id, notes

**fleet_drivers**
- id, organization_id, name, phone
- license_number, license_expiry, documents JSONB
- assigned_vehicle_id, status (available/on_trip/off_duty)
- rating, total_trips

**fleet_trips**
- id, organization_id, vehicle_id, driver_id
- customer_name, customer_phone
- pickup_location, drop_location
- scheduled_at, started_at, completed_at
- distance_km, fare, payment_status
- status (booked/dispatched/in_progress/completed/cancelled)

**fleet_maintenance**
- id, vehicle_id, organization_id
- type (service/repair/tire/oil/battery)
- description, cost, vendor, date
- odometer_at_service, next_service_due_km, next_service_due_date

**fleet_fuel**
- id, vehicle_id, organization_id
- date, liters, amount, odometer, fuel_station
- mileage_calculated

---
---

# Module 11: Patient / Clinic Manager
## PRD

### Overview
Complete clinic management for doctors, dentists, and healthcare providers.

### Target Categories
Doctor clinic, dental clinic, physiotherapy, veterinary, eye clinic, skin clinic, homeopathy, ayurveda

### Core Features

1. **Patient Records**
   - Patient name, age, gender, phone, blood group
   - Medical history, allergies, ongoing medications
   - Emergency contact
   - Unique patient ID (auto-generated)
   - Family linking (husband-wife-child under one family)

2. **Appointment Management**
   - Online booking (with token number)
   - Walk-in registration
   - Doctor-wise schedule
   - Token display (current serving number)
   - Average wait time calculation
   - Reschedule/cancel

3. **Consultation Notes**
   - Symptoms, diagnosis, prescription
   - Vitals (BP, temperature, weight, SPO2)
   - Follow-up date
   - Referral to specialist
   - Lab test orders
   - Consultation history per patient

4. **Prescription Generator**
   - Medicine name, dosage, frequency, duration
   - Before/after food instructions
   - Digital prescription (shareable PDF/image)
   - Medicine database (common medicines auto-suggest)
   - Previous prescriptions viewable

5. **Lab / Test Management**
   - Order tests from consultation
   - Track results (pending/received)
   - Store reports per patient
   - Normal range indicators

6. **Billing**
   - Consultation fee
   - Procedure charges
   - Medicine charges (if dispensing)
   - Insurance/TPA billing
   - Receipt generation

7. **Follow-up Reminders**
   - Automated follow-up reminder (7 days after visit)
   - Vaccination schedule (pediatric)
   - Chronic disease follow-up (diabetes monthly)
   - Medicine refill reminders

8. **Reports**
   - Daily patient count
   - Revenue (consultation + procedures)
   - Disease-wise statistics
   - Patient demographics
   - Follow-up compliance rate

### Database Tables

**patients**
- id, organization_id, patient_number (auto: PAT-0001)
- name, age, gender, phone, email
- blood_group, allergies TEXT[]
- medical_history TEXT, ongoing_medications TEXT
- emergency_contact, family_id
- created_at

**consultations**
- id, organization_id, patient_id, doctor_name
- date, token_number
- symptoms, diagnosis, prescription JSONB
- vitals JSONB (bp, temp, weight, spo2, pulse)
- follow_up_date, notes
- lab_tests_ordered JSONB
- consultation_fee, procedure_charges
- total_bill, payment_status

**prescriptions**
- id, consultation_id, patient_id, organization_id
- medicines JSONB (name, dosage, frequency, duration, instructions)
- additional_notes, pdf_url
- created_at

**patient_documents**
- id, patient_id, organization_id
- type (lab_report/xray/mri/prescription/insurance)
- title, file_url, date, notes

---
