-- ============================================
-- PATIENT / CLINIC MANAGER + STUDENT / BATCH MANAGER
-- ============================================

-- PATIENTS
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    patient_number TEXT,
    name TEXT NOT NULL,
    age INTEGER,
    gender TEXT CHECK (gender IN ('male', 'female', 'other')),
    phone TEXT,
    email TEXT,
    blood_group TEXT,
    allergies TEXT[] DEFAULT '{}',
    medical_history TEXT,
    ongoing_medications TEXT,
    emergency_contact TEXT,
    address TEXT,
    family_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_patient_org ON patients(organization_id);
CREATE INDEX IF NOT EXISTS idx_patient_phone ON patients(phone);

-- CONSULTATIONS
CREATE TABLE IF NOT EXISTS consultations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_name TEXT,
    date DATE DEFAULT CURRENT_DATE,
    token_number INTEGER,
    symptoms TEXT,
    diagnosis TEXT,
    prescription JSONB DEFAULT '[]',
    vitals JSONB DEFAULT '{}',
    follow_up_date DATE,
    lab_tests_ordered JSONB DEFAULT '[]',
    notes TEXT,
    consultation_fee DECIMAL(10,2) DEFAULT 0,
    procedure_charges DECIMAL(10,2) DEFAULT 0,
    total_bill DECIMAL(10,2) DEFAULT 0,
    payment_status TEXT DEFAULT 'paid' CHECK (payment_status IN ('paid', 'pending', 'insurance')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_consult_org ON consultations(organization_id);
CREATE INDEX IF NOT EXISTS idx_consult_patient ON consultations(patient_id);
CREATE INDEX IF NOT EXISTS idx_consult_date ON consultations(organization_id, date);

-- PATIENT DOCUMENTS
CREATE TABLE IF NOT EXISTS patient_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL,
    type TEXT DEFAULT 'report' CHECK (type IN ('lab_report', 'xray', 'mri', 'prescription', 'insurance', 'other')),
    title TEXT,
    file_url TEXT,
    date DATE DEFAULT CURRENT_DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pd_patient ON patient_documents(patient_id);

-- BATCHES (for coaching/classes)
CREATE TABLE IF NOT EXISTS batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    schedule JSONB DEFAULT '{}',
    teacher_name TEXT,
    capacity INTEGER DEFAULT 30,
    current_strength INTEGER DEFAULT 0,
    fee_amount DECIMAL(10,2) DEFAULT 0,
    fee_frequency TEXT DEFAULT 'monthly' CHECK (fee_frequency IN ('monthly', 'quarterly', 'half_yearly', 'yearly', 'one_time')),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_batch_org ON batches(organization_id);

-- STUDENTS
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT,
    parent_phone TEXT,
    email TEXT,
    address TEXT,
    date_of_birth DATE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'dropped', 'on_hold')),
    notes TEXT,
    emergency_contact TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_student_org ON students(organization_id);
CREATE INDEX IF NOT EXISTS idx_student_phone ON students(phone);

-- STUDENT-BATCH MAPPING
CREATE TABLE IF NOT EXISTS student_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    batch_id UUID NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    joined_date DATE DEFAULT CURRENT_DATE,
    status TEXT DEFAULT 'active',
    UNIQUE(student_id, batch_id)
);

-- ATTENDANCE
CREATE TABLE IF NOT EXISTS student_attendance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL,
    batch_id UUID NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    status TEXT DEFAULT 'present' CHECK (status IN ('present', 'absent', 'late')),
    marked_by TEXT,
    UNIQUE(batch_id, student_id, date)
);
CREATE INDEX IF NOT EXISTS idx_att_batch_date ON student_attendance(batch_id, date);

-- STUDENT FEES
CREATE TABLE IF NOT EXISTS student_fees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    batch_id UUID REFERENCES batches(id),
    month INTEGER,
    year INTEGER,
    amount DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    final_amount DECIMAL(10,2) NOT NULL,
    status TEXT DEFAULT 'due' CHECK (status IN ('due', 'paid', 'overdue', 'partial')),
    paid_date DATE,
    payment_method TEXT,
    receipt_number TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, batch_id, month, year)
);
CREATE INDEX IF NOT EXISTS idx_sf_org ON student_fees(organization_id);
CREATE INDEX IF NOT EXISTS idx_sf_student ON student_fees(student_id);
CREATE INDEX IF NOT EXISTS idx_sf_status ON student_fees(status);

-- RLS
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE consultations ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_fees ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_all_patients" ON patients FOR ALL USING (true);
CREATE POLICY "service_all_consultations" ON consultations FOR ALL USING (true);
CREATE POLICY "service_all_pd" ON patient_documents FOR ALL USING (true);
CREATE POLICY "service_all_batches" ON batches FOR ALL USING (true);
CREATE POLICY "service_all_students" ON students FOR ALL USING (true);
CREATE POLICY "service_all_sb" ON student_batches FOR ALL USING (true);
CREATE POLICY "service_all_sa" ON student_attendance FOR ALL USING (true);
CREATE POLICY "service_all_sf" ON student_fees FOR ALL USING (true);

-- Register modules
INSERT INTO modules (id, name, description, icon, category, is_core, default_plans, sort_order, status) VALUES
('clinic', 'Clinic / Patient', 'Patient records, consultations, prescriptions', 'Stethoscope', 'operations', false, '{pro,enterprise}', 18, 'active'),
('students', 'Students / Batches', 'Student enrollment, attendance, fees, batches', 'GraduationCap', 'operations', false, '{pro,enterprise}', 19, 'active')
ON CONFLICT (id) DO NOTHING;

-- Templates
INSERT INTO industry_templates (id, name, description, icon, category, module_ids, sort_order) VALUES
('dentist', 'Dentist', 'For dental clinics and orthodontists', 'Smile', 'healthcare', '{crm,clinic,booking,billing,whatsapp,website,analytics}', 32),
('physiotherapy', 'Physiotherapy', 'For physiotherapy and rehab centers', 'HeartPulse', 'healthcare', '{crm,clinic,booking,billing,whatsapp,website,analytics}', 33),
('veterinary', 'Veterinary Clinic', 'For vet clinics and pet care', 'PawPrint', 'healthcare', '{crm,clinic,booking,billing,whatsapp,website,analytics}', 34),
('driving_school', 'Driving School', 'For driving training institutes', 'Car', 'education', '{crm,students,booking,billing,whatsapp,website,analytics}', 35),
('music_dance', 'Music / Dance Class', 'For music, dance, and art academies', 'Music', 'education', '{crm,students,billing,whatsapp,website,analytics}', 36),
('computer_training', 'Computer Training', 'For IT training centers', 'Monitor', 'education', '{crm,students,billing,whatsapp,website,analytics}', 37)
ON CONFLICT (id) DO NOTHING;
