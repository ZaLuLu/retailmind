import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid

# Set random seed for reproducibility
np.random.seed(42)

# Configuration
DAYS_HISTORY = 180
TARGET_ROWS = np.random.randint(5000, 10001)
START_DATE = datetime.now() - timedelta(days=DAYS_HISTORY)

# Product catalog with BCG matrix classification
products = [
    # STARS: High volume, high margin (3-4 products)
    {'id': 'STAR-001', 'name': 'Premium Wireless Headphones', 'category': 'Electronics', 
     'price': 199.99, 'cost': 80.00, 'bcg': 'Star', 'base_daily_volume': 25},
    {'id': 'STAR-002', 'name': 'Smart Fitness Watch', 'category': 'Wearables', 
     'price': 249.99, 'cost': 100.00, 'bcg': 'Star', 'base_daily_volume': 20},
    {'id': 'STAR-003', 'name': 'Portable Power Bank 20000mAh', 'category': 'Accessories', 
     'price': 49.99, 'cost': 15.00, 'bcg': 'Star', 'base_daily_volume': 30},
    {'id': 'STAR-004', 'name': 'USB-C Fast Charging Cable', 'category': 'Accessories', 
     'price': 24.99, 'cost': 5.00, 'bcg': 'Star', 'base_daily_volume': 35},
    
    # CASH COWS: High volume, low margin (4-5 products)
    {'id': 'CASHCOW-001', 'name': 'Basic Phone Case', 'category': 'Accessories', 
     'price': 12.99, 'cost': 9.00, 'bcg': 'Cash Cow', 'base_daily_volume': 40},
    {'id': 'CASHCOW-002', 'name': 'Screen Protector Pack', 'category': 'Accessories', 
     'price': 9.99, 'cost': 7.50, 'bcg': 'Cash Cow', 'base_daily_volume': 45},
    {'id': 'CASHCOW-003', 'name': 'AA Battery 4-Pack', 'category': 'Accessories', 
     'price': 6.99, 'cost': 5.20, 'bcg': 'Cash Cow', 'base_daily_volume': 35},
    {'id': 'CASHCOW-004', 'name': 'Microfiber Cleaning Cloth', 'category': 'Accessories', 
     'price': 4.99, 'cost': 3.80, 'bcg': 'Cash Cow', 'base_daily_volume': 50},
    {'id': 'CASHCOW-005', 'name': 'Universal Phone Stand', 'category': 'Accessories', 
     'price': 14.99, 'cost': 11.00, 'bcg': 'Cash Cow', 'base_daily_volume': 28},
    
    # HIDDEN GEMS: Low volume, extremely high margin (2-3 products)
    {'id': 'GEM-001', 'name': 'Professional Audio Mixer', 'category': 'Electronics', 
     'price': 899.99, 'cost': 200.00, 'bcg': 'Hidden Gem', 'base_daily_volume': 1},
    {'id': 'GEM-002', 'name': 'Premium Leather Laptop Bag', 'category': 'Accessories', 
     'price': 349.99, 'cost': 80.00, 'bcg': 'Hidden Gem', 'base_daily_volume': 2},
    {'id': 'GEM-003', 'name': 'Extended Warranty 3-Year', 'category': 'Services', 
     'price': 149.99, 'cost': 15.00, 'bcg': 'Hidden Gem', 'base_daily_volume': 3},
    
    # REGULAR PERFORMERS: Medium volume, medium margin (filler products)
    {'id': 'REG-001', 'name': 'Bluetooth Speaker', 'category': 'Electronics', 
     'price': 79.99, 'cost': 35.00, 'bcg': 'Regular', 'base_daily_volume': 12},
    {'id': 'REG-002', 'name': 'Wireless Mouse', 'category': 'Electronics', 
     'price': 34.99, 'cost': 18.00, 'bcg': 'Regular', 'base_daily_volume': 15},
    {'id': 'REG-003', 'name': 'Laptop Cooling Pad', 'category': 'Accessories', 
     'price': 39.99, 'cost': 20.00, 'bcg': 'Regular', 'base_daily_volume': 8},
    {'id': 'REG-004', 'name': 'HDMI Cable 6ft', 'category': 'Accessories', 
     'price': 19.99, 'cost': 8.00, 'bcg': 'Regular', 'base_daily_volume': 18},
    {'id': 'REG-005', 'name': 'Device Repair Service', 'category': 'Services', 
     'price': 89.99, 'cost': 25.00, 'bcg': 'Regular', 'base_daily_volume': 5},
    {'id': 'REG-006', 'name': 'Smart LED Light Bulb', 'category': 'Electronics', 
     'price': 29.99, 'cost': 12.00, 'bcg': 'Regular', 'base_daily_volume': 10},
    
    # DEAD WEIGHT: Very low volume, haven't sold in last 30 days
    {'id': 'DEAD-001', 'name': 'VGA to HDMI Adapter', 'category': 'Accessories', 
     'price': 24.99, 'cost': 15.00, 'bcg': 'Dead Weight', 'base_daily_volume': 0.1},
    {'id': 'DEAD-002', 'name': 'CD/DVD Cleaning Kit', 'category': 'Accessories', 
     'price': 14.99, 'cost': 10.00, 'bcg': 'Dead Weight', 'base_daily_volume': 0.08},
    {'id': 'DEAD-003', 'name': 'Floppy Disk USB Reader', 'category': 'Electronics', 
     'price': 34.99, 'cost': 22.00, 'bcg': 'Dead Weight', 'base_daily_volume': 0.05},
    {'id': 'DEAD-004', 'name': 'iPod Classic Dock', 'category': 'Accessories', 
     'price': 29.99, 'cost': 18.00, 'bcg': 'Dead Weight', 'base_daily_volume': 0.06},
]

# Customer segment weights
customer_segments = {
    'Walk-in': 0.50,
    'Online': 0.30,
    'B2B': 0.20
}

def generate_transactions():
    """Generate synthetic transaction data with realistic patterns"""
    transactions = []
    
    # Calculate daily transaction allocation
    transactions_per_day = TARGET_ROWS / DAYS_HISTORY
    
    for day_offset in range(DAYS_HISTORY):
        current_date = START_DATE + timedelta(days=day_offset)
        day_of_week = current_date.weekday()  # Monday=0, Sunday=6
        
        # Day-of-week seasonality multiplier
        # Weekends: higher for walk-in (1.4x Sat, 1.3x Sun)
        # Weekdays: higher for B2B (1.2x Mon-Thu)
        # Friday: balanced (1.0x)
        if day_of_week == 5:  # Saturday
            weekend_multiplier = 1.4
        elif day_of_week == 6:  # Sunday
            weekend_multiplier = 1.3
        else:
            weekend_multiplier = 0.9
            
        # Daily transaction count with variation
        daily_transactions = int(transactions_per_day * np.random.uniform(0.8, 1.2))
        
        for _ in range(daily_transactions):
            # Select product based on BCG volume weights
            product = np.random.choice(products, p=calculate_product_weights())
            
            # Skip dead weight products in last 30 days (simulate no sales)
            if product['bcg'] == 'Dead Weight' and day_offset >= (DAYS_HISTORY - 30):
                if np.random.random() > 0.01:  # 99% chance to skip
                    continue
            
            # Determine customer segment with day-of-week influence
            if day_of_week >= 5:  # Weekend
                segment_weights = {'Walk-in': 0.65, 'Online': 0.30, 'B2B': 0.05}
            elif day_of_week < 5:  # Weekday
                segment_weights = {'Walk-in': 0.35, 'Online': 0.30, 'B2B': 0.35}
            else:
                segment_weights = customer_segments
            
            segment = np.random.choice(
                list(segment_weights.keys()),
                p=list(segment_weights.values())
            )
            
            # Apply segment-specific volume and pricing behavior
            if segment == 'B2B':
                # B2B: Higher quantities, slight bulk discount
                base_qty = np.random.randint(3, 15)
                price_multiplier = 0.95
            elif segment == 'Online':
                # Online: Medium quantities, standard pricing
                base_qty = np.random.randint(1, 5)
                price_multiplier = 1.0
            else:  # Walk-in
                # Walk-in: Smaller quantities, standard pricing
                base_qty = np.random.randint(1, 3)
                price_multiplier = 1.0
            
            # Apply weekend multiplier to walk-in
            if segment == 'Walk-in':
                qty_multiplier = weekend_multiplier
            else:
                qty_multiplier = 1.0
            
            qty_sold = max(1, int(base_qty * qty_multiplier))
            
            # Calculate unit price with minor random variation
            unit_price = round(product['price'] * price_multiplier * np.random.uniform(0.98, 1.02), 2)
            unit_cost = round(product['cost'] * np.random.uniform(0.97, 1.03), 2)
            
            # Create transaction record
            transaction = {
                'transaction_id': str(uuid.uuid4()),
                'date': current_date.strftime('%Y-%m-%d'),
                'product_id': product['id'],
                'product_name': product['name'],
                'category': product['category'],
                'qty_sold': qty_sold,
                'unit_price': unit_price,
                'unit_cost': unit_cost,
                'customer_segment': segment,
                'bcg_classification': product['bcg']  # Added for reference
            }
            
            transactions.append(transaction)
    
    return pd.DataFrame(transactions)

def calculate_product_weights():
    """Calculate probability weights for product selection based on daily volume"""
    weights = np.array([p['base_daily_volume'] for p in products])
    return weights / weights.sum()

def main():
    print(f"Generating retail sales data...")
    print(f"Target rows: {TARGET_ROWS}")
    print(f"Date range: {START_DATE.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Days of history: {DAYS_HISTORY}")
    
    # Generate transactions
    df = generate_transactions()
    
    # Save to Excel
    df.to_excel('/mnt/user-data/outputs/demo_retail_data.xlsx', index=False)
    
    # Summary statistics
    print(f"\n✓ Dataset generated successfully!")
    print(f"Total rows: {len(df)}")
    print(f"\nBreakdown by BCG Classification:")
    print(df.groupby('bcg_classification').agg({
        'transaction_id': 'count',
        'qty_sold': 'sum',
        'unit_price': 'mean',
        'unit_cost': 'mean'
    }).round(2))
    
    print(f"\nBreakdown by Customer Segment:")
    print(df['customer_segment'].value_counts())
    
    print(f"\nBreakdown by Category:")
    print(df['category'].value_counts())
    
    # Calculate margin percentage statistics
    df['margin_pct'] = ((df['unit_price'] - df['unit_cost']) / df['unit_price'] * 100)
    print(f"\nMargin Statistics:")
    print(f"Average margin: {df['margin_pct'].mean():.2f}%")
    print(f"Median margin: {df['margin_pct'].median():.2f}%")
    
    print(f"\nFile saved: /mnt/user-data/outputs/demo_retail_data.xlsx")

if __name__ == "__main__":
    main()
