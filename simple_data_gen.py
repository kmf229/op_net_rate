#!/usr/bin/env python3
"""
Simple dummy data generator using only standard library.
Creates realistic physical therapy clinic data with hierarchical structure.
"""

import sqlite3
import random
from datetime import datetime, timedelta

# Set random seed for reproducible results
random.seed(42)

# CPT codes commonly used in physical therapy
PT_CPT_CODES = [
    ('97110', 'Therapeutic Exercise', 45.0, 85.0),
    ('97112', 'Neuromuscular Re-education', 48.0, 90.0),
    ('97116', 'Gait Training', 42.0, 82.0),
    ('97140', 'Manual Therapy', 52.0, 95.0),
    ('97150', 'Therapeutic Activities', 46.0, 87.0),
    ('97530', 'Dynamic Activities', 48.0, 88.0),
    ('97535', 'Self-Care Training', 44.0, 85.0),
    ('97750', 'Physical Performance Test', 38.0, 75.0),
    ('97161', 'PT Evaluation Low Complexity', 95.0, 145.0),
    ('97162', 'PT Evaluation Moderate Complexity', 125.0, 185.0),
    ('97163', 'PT Evaluation High Complexity', 155.0, 225.0),
    ('97164', 'PT Re-evaluation', 85.0, 125.0),
]

# Payer mix with typical rates
PAYERS = [
    ('Medicare', 0.25, 0.70),
    ('Medicaid', 0.15, 0.55), 
    ('BCBS', 0.20, 0.95),
    ('Aetna', 0.12, 0.92),
    ('Humana', 0.10, 0.88),
    ('UnitedHealthcare', 0.15, 0.90),
    ('Cash/Self-Pay', 0.03, 1.20),
]

# Simple name generators
FIRST_NAMES = ["John", "Jane", "Michael", "Sarah", "David", "Lisa", "Robert", "Emily", "James", "Jessica", 
               "William", "Ashley", "Christopher", "Amanda", "Matthew", "Stephanie", "Anthony", "Jennifer"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

def create_database():
    """Create SQLite database with required tables."""
    conn = sqlite3.connect('net_rate_data.db')
    cursor = conn.cursor()
    
    # Drop existing tables to ensure clean state
    tables = ['visit_cpts', 'visits', 'therapists', 'clinics', 'markets', 'regions', 'cpt_codes', 'payers']
    for table in tables:
        cursor.execute(f'DROP TABLE IF EXISTS {table}')
    
    # Organizational hierarchy
    cursor.execute('''
        CREATE TABLE regions (
            region_id INTEGER PRIMARY KEY,
            region_name TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE markets (
            market_id INTEGER PRIMARY KEY,
            market_name TEXT NOT NULL,
            region_id INTEGER,
            FOREIGN KEY (region_id) REFERENCES regions (region_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE clinics (
            clinic_id INTEGER PRIMARY KEY,
            clinic_name TEXT NOT NULL,
            market_id INTEGER,
            address TEXT,
            FOREIGN KEY (market_id) REFERENCES markets (market_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE therapists (
            therapist_id INTEGER PRIMARY KEY,
            therapist_name TEXT NOT NULL,
            clinic_id INTEGER,
            license_type TEXT,
            hire_date DATE,
            FOREIGN KEY (clinic_id) REFERENCES clinics (clinic_id)
        )
    ''')
    
    # Financial/visit data
    cursor.execute('''
        CREATE TABLE visits (
            visit_id INTEGER PRIMARY KEY,
            patient_id TEXT,
            therapist_id INTEGER,
            clinic_id INTEGER,
            visit_date DATE,
            visit_type TEXT,
            payer_name TEXT,
            total_units INTEGER,
            gross_charges REAL,
            allowed_amount REAL,
            net_revenue REAL,
            copay_expected REAL,
            copay_collected REAL,
            contractual_adjustment REAL,
            write_off_amount REAL,
            FOREIGN KEY (therapist_id) REFERENCES therapists (therapist_id),
            FOREIGN KEY (clinic_id) REFERENCES clinics (clinic_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE visit_cpts (
            visit_id INTEGER,
            cpt_code TEXT,
            units INTEGER,
            gross_charge REAL,
            allowed_amount REAL,
            net_revenue REAL,
            FOREIGN KEY (visit_id) REFERENCES visits (visit_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE cpt_codes (
            cpt_code TEXT PRIMARY KEY,
            description TEXT,
            base_rate REAL,
            max_rate REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE payers (
            payer_name TEXT PRIMARY KEY,
            market_share REAL,
            rate_multiplier REAL
        )
    ''')
    
    conn.commit()
    return conn

def generate_name():
    """Generate a random name."""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def generate_address():
    """Generate a simple address."""
    street_num = random.randint(100, 9999)
    streets = ["Main St", "Oak Ave", "First St", "Park Rd", "Elm St", "Washington Ave", "Lincoln Blvd"]
    cities = ["Springfield", "Franklin", "Georgetown", "Madison", "Chester", "Riverside", "Fairview"]
    states = ["TX", "CA", "FL", "NY", "PA", "OH", "IL", "NC", "GA", "MI"]
    
    return f"{street_num} {random.choice(streets)}, {random.choice(cities)}, {random.choice(states)} {random.randint(10000, 99999)}"

def weighted_choice(choices, weights):
    """Choose an item based on weights."""
    total = sum(weights)
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in zip(choices, weights):
        if upto + weight >= r:
            return choice
        upto += weight
    return choices[-1]

def generate_organizational_data(conn):
    """Generate the organizational hierarchy."""
    cursor = conn.cursor()
    
    # Regions (4 total)
    regions = [
        'Northeast Region',
        'Southeast Region', 
        'Midwest Region',
        'Southwest Region'
    ]
    
    for i, region in enumerate(regions, 1):
        cursor.execute(
            'INSERT INTO regions (region_id, region_name) VALUES (?, ?)',
            (i, region)
        )
    
    # Markets (10 per region)
    market_id = 1
    for region_id in range(1, 5):
        region_name = regions[region_id - 1].split()[0]
        
        for market_num in range(1, 11):
            market_name = f"{region_name} Market {market_num:02d}"
            cursor.execute(
                'INSERT INTO markets (market_id, market_name, region_id) VALUES (?, ?, ?)',
                (market_id, market_name, region_id)
            )
            market_id += 1
    
    # Clinics (50 per market)
    clinic_id = 1
    for market_id in range(1, 41):  # 40 markets total
        for clinic_num in range(1, 51):
            clinic_name = f"PT Clinic {clinic_id:04d}"
            address = generate_address()
            
            cursor.execute(
                'INSERT INTO clinics (clinic_id, clinic_name, market_id, address) VALUES (?, ?, ?, ?)',
                (clinic_id, clinic_name, market_id, address)
            )
            clinic_id += 1
    
    # Therapists (2-4 per clinic)
    therapist_id = 1
    license_types = ['PT', 'PTA', 'PT', 'PTA']  # Weighted towards PTs
    
    for clinic_id in range(1, 2001):  # 2000 clinics total
        num_therapists = random.randint(2, 4)
        
        for _ in range(num_therapists):
            therapist_name = generate_name()
            license_type = random.choice(license_types)
            
            # Generate hire date (within last 5 years)
            days_ago = random.randint(30, 1825)  # 30 days to 5 years ago
            hire_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            cursor.execute(
                'INSERT INTO therapists (therapist_id, therapist_name, clinic_id, license_type, hire_date) VALUES (?, ?, ?, ?, ?)',
                (therapist_id, therapist_name, clinic_id, license_type, hire_date)
            )
            therapist_id += 1
    
    conn.commit()
    print(f"Generated organizational data: {len(regions)} regions, 40 markets, 2000 clinics, ~{therapist_id-1} therapists")

def generate_reference_data(conn):
    """Generate CPT codes and payer data."""
    cursor = conn.cursor()
    
    # CPT codes
    for cpt_code, description, base_rate, max_rate in PT_CPT_CODES:
        cursor.execute(
            'INSERT INTO cpt_codes (cpt_code, description, base_rate, max_rate) VALUES (?, ?, ?, ?)',
            (cpt_code, description, base_rate, max_rate)
        )
    
    # Payers
    for payer_name, market_share, rate_multiplier in PAYERS:
        cursor.execute(
            'INSERT INTO payers (payer_name, market_share, rate_multiplier) VALUES (?, ?, ?)',
            (payer_name, market_share, rate_multiplier)
        )
    
    conn.commit()
    print(f"Generated {len(PT_CPT_CODES)} CPT codes and {len(PAYERS)} payers")

def generate_visit_data(conn, num_months=12, visits_per_therapist_per_month=45):
    """Generate realistic visit and financial data."""
    cursor = conn.cursor()
    
    # Get therapist data
    cursor.execute('''
        SELECT t.therapist_id, t.clinic_id, t.license_type
        FROM therapists t
        JOIN clinics c ON t.clinic_id = c.clinic_id
    ''')
    therapists = cursor.fetchall()
    
    visit_id = 1
    start_date = datetime.now().replace(day=1) - timedelta(days=365)
    
    print(f"Generating visit data for {len(therapists)} therapists over {num_months} months...")
    
    for month_offset in range(num_months):
        month_start = start_date + timedelta(days=30 * month_offset)
        
        for therapist_id, clinic_id, license_type in therapists:
            # Vary visits per month
            base_visits = visits_per_therapist_per_month
            if license_type == 'PTA':
                base_visits = int(base_visits * 0.7)  # PTAs see fewer patients
            
            monthly_variation = random.uniform(0.8, 1.2)
            num_visits = int(base_visits * monthly_variation)
            
            for visit_num in range(num_visits):
                visit_date = month_start + timedelta(days=random.randint(0, 29))
                
                # Determine visit type
                visit_types = ['Evaluation', 'Follow-up', 'Re-evaluation']
                visit_weights = [0.15, 0.80, 0.05]
                visit_type = weighted_choice(visit_types, visit_weights)
                
                # Select payer
                payer_names = [p[0] for p in PAYERS]
                payer_weights = [p[1] for p in PAYERS]
                payer_name = weighted_choice(payer_names, payer_weights)
                payer_rate_multiplier = next(p[2] for p in PAYERS if p[0] == payer_name)
                
                # Generate CPT codes for this visit
                if visit_type == 'Evaluation':
                    eval_cpts = ['97161', '97162', '97163']
                    main_cpt = random.choice(eval_cpts)
                    additional_cpts = random.choices(
                        ['97110', '97112', '97140', '97150'],
                        k=random.randint(1, 3)
                    )
                    cpt_codes = [main_cpt] + additional_cpts
                else:
                    # Follow-up visit
                    cpt_codes = random.choices(
                        ['97110', '97112', '97116', '97140', '97150', '97530'],
                        k=random.randint(2, 4)
                    )
                
                # Calculate financials
                total_units = 0
                gross_charges = 0
                allowed_amount = 0
                net_revenue = 0
                
                for cpt_code in cpt_codes:
                    units = random.randint(1, 3) if cpt_code not in ['97161', '97162', '97163', '97164'] else 1
                    
                    # Get base rates
                    cpt_data = next((c for c in PT_CPT_CODES if c[0] == cpt_code), None)
                    if cpt_data:
                        base_rate = cpt_data[2]
                        max_rate = cpt_data[3]
                        
                        # Gross charge (what clinic bills)
                        unit_gross = random.uniform(base_rate * 1.1, max_rate)
                        unit_allowed = base_rate * payer_rate_multiplier
                        
                        # Collection efficiency varies
                        collection_efficiency = random.uniform(0.85, 0.98)
                        unit_net = unit_allowed * collection_efficiency
                        
                        gross_charges += unit_gross * units
                        allowed_amount += unit_allowed * units
                        net_revenue += unit_net * units
                        total_units += units
                        
                        # Insert CPT detail
                        cursor.execute('''
                            INSERT INTO visit_cpts (visit_id, cpt_code, units, gross_charge, allowed_amount, net_revenue)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (visit_id, cpt_code, units, unit_gross * units, unit_allowed * units, unit_net * units))
                
                # Calculate copay
                if payer_name not in ['Medicare', 'Medicaid']:
                    copay_expected = random.uniform(15, 45)
                else:
                    copay_expected = random.uniform(0, 20)
                    
                copay_collection_rate = random.uniform(0.75, 0.95)
                copay_collected = copay_expected * copay_collection_rate
                
                # Contractual adjustments and write-offs
                contractual_adjustment = gross_charges - allowed_amount
                write_off_amount = allowed_amount - net_revenue - copay_collected
                
                # Insert visit record
                patient_id = f"PT{random.randint(100000, 999999)}"
                
                cursor.execute('''
                    INSERT INTO visits (
                        visit_id, patient_id, therapist_id, clinic_id, visit_date, visit_type,
                        payer_name, total_units, gross_charges, allowed_amount, net_revenue,
                        copay_expected, copay_collected, contractual_adjustment, write_off_amount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    visit_id, patient_id, therapist_id, clinic_id,
                    visit_date.strftime('%Y-%m-%d'), visit_type, payer_name, total_units,
                    gross_charges, allowed_amount, net_revenue, copay_expected, copay_collected,
                    contractual_adjustment, write_off_amount
                ))
                
                visit_id += 1
                
                if visit_id % 10000 == 0:
                    print(f"Generated {visit_id:,} visits...")
                    conn.commit()
    
    conn.commit()
    print(f"Generated {visit_id-1:,} total visits")

def main():
    """Generate all dummy data for the prototype."""
    print("Creating Net Rate Decomposition Tool dummy data...")
    
    conn = create_database()
    
    try:
        generate_organizational_data(conn)
        generate_reference_data(conn)
        generate_visit_data(conn)
        
        # Generate summary statistics
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM visits')
        total_visits = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(net_revenue) FROM visits')
        total_revenue = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT therapist_id) FROM visits')
        active_therapists = cursor.fetchone()[0]
        
        print(f"\nData generation complete!")
        print(f"Total visits: {total_visits:,}")
        print(f"Total revenue: ${total_revenue:,.2f}")
        print(f"Average net rate: ${total_revenue/total_visits:.2f}")
        print(f"Active therapists: {active_therapists}")
        print(f"Database saved as: net_rate_data.db")
        
    except Exception as e:
        print(f"Error generating data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()