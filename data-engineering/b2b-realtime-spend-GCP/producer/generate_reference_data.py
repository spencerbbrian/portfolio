import csv
import random

from faker import Faker

fake = Faker()

VENDOR_CATEGORIES = [
    "saas_software",
    "travel",
    "office_supplies",
    "payroll_services",
    "advertising_marketing",
    "professional_services",
    "logistics_shipping",
    "telecom_internet",
    "facilities_utilities",
    "hardware_equipment",
]
 
SIZE_TIERS = ["smb", "mid_market", "enterprise"]

BASELINE_SPEND_RANGES = {
    "smb": (5000, 50000),
    "mid_market": (50000, 500000),
    "enterprise": (500000, 5000000),
}

def generate_companies(n: int) -> list[dict]:
    companies = []
    for i in range(n):
        size_tier = random.choice(SIZE_TIERS)
        low, high = BASELINE_SPEND_RANGES[size_tier]

        companies.append(
            {
                "company_id": f"company_{i:04d}",
                "name": fake.company(),
                "industry": fake.bs().split()[0],  # quick stand-in for an industry label
                "size_tier": size_tier,
                "home_country": fake.country_code(),
                "baseline_monthly_spend": round(random.uniform(low, high), 2),
            }
        )
    return companies

def generate_vendors(n:int) -> list[dict]:
    vendors = []
    for i in range(n):
        vendors.append(
            {
                "vendor_id": f"vendor_{i:04d}",
                "name": fake.company(),
                "category": random.choice(VENDOR_CATEGORIES),
                # A coarse risk tier — used later as one input into the rule
                # checks (e.g. flag amounts above a lower threshold for
                # higher-risk vendor categories).
                "risk_tier": random.choices(
                    ["low", "medium", "high"], weights=[0.7, 0.25, 0.05]
                )[0],
            }
        )
    return vendors

def write_csv(rows: list[dict], path:str) -> None:
    if not rows:
        raise ValueError(f"No rows to write to {path}")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    companies = generate_companies(40)
    vendors = generate_vendors(120)

    write_csv(companies, "companies.csv")
    write_csv(vendors, "vendors.csv")

    print(f"Wrote {len(companies)} companies to companies.csv")
    print(f"Wrote {len(vendors)} vendors to vendors.csv")