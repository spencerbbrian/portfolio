from stocks import db
from datetime import datetime
from time import time
import random

class Stock(db.Model):
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    stock = db.Column(db.String(length=30), nullable=False)
    price = db.Column(db.Float(), nullable=False)
    volume = db.Column(db.Integer(), nullable=False)
    week = db.Column(db.Integer(), nullable = False, default = 1)
    high = db.Column(db.Float(), nullable=True)
    low = db.Column(db.Float(), nullable=True)

    def update_week(self):
        # Retrieve the last recorded week number for this stock
        last_week_stock = Stock.query.filter_by(stock=self.stock).order_by(Stock.week.desc()).first()
        if last_week_stock:
            last_week = last_week_stock.week
        else:
            last_week = 0
        
        # Increment the week number for this stock
        self.week = last_week + 1

    def __init__(self,stock,price,volume):
        self.stock = stock
        self.price = price
        self.volume = volume

    def update_price(self):
        if self.volume > 10000:
            self.price *= random.uniform(1.01,1.05)
        elif self.volume < 1000:
            self.price *= random.uniform(0.95,0.99)
        else:
            self.price *= random.uniform(0.99,1.01)

    def simulate_weekly_volume(self):
        change = random.uniform(-0.2,0.2) # Allow volume to increase or decrease by up to 20%
        self.volume *= (1 + change) # Apply the change to volume

stocks = [
    Stock("AAPL", 150.0, 10000),  # Apple Inc. - Initial price $150, initial volume 10000
    Stock("GOOGL", 2500.0, 5000),  # Alphabet Inc. (Google) - Initial price $2500, initial volume 5000
    Stock("MSFT", 300.0, 20000),  # Microsoft Corporation - Initial price $300, initial volume 20000
    Stock("AMZN", 3500.0, 8000),  # Amazon.com Inc. - Initial price $3500, initial volume 8000
    Stock("TSLA", 700.0, 15000),  # Tesla Inc. - Initial price $700, initial volume 15000
    Stock("FB", 350.0, 12000),  # Meta Platforms Inc. (formerly Facebook) - Initial price $350, initial volume 12000
    Stock("NVDA", 600.0, 10000),  # NVIDIA Corporation - Initial price $600, initial volume 10000
    Stock("BABA", 200.0, 18000),  # Alibaba Group Holding Limited - Initial price $200, initial volume 18000
    Stock("JPM", 150.0, 25000),  # JPMorgan Chase & Co. - Initial price $150, initial volume 25000
    Stock("V", 250.0, 15000),  # Visa Inc. - Initial price $250, initial volume 15000
    Stock("PYPL", 200.0, 12000),  # PayPal Holdings Inc. - Initial price $200, initial volume 12000
    Stock("NFLX", 500.0, 10000),  # Netflix Inc. - Initial price $500, initial volume 10000
    Stock("INTC", 65.0, 30000),  # Intel Corporation - Initial price $65, initial volume 30000
    Stock("CRM", 220.0, 8000),  # Salesforce.com Inc. - Initial price $220, initial volume 8000
    Stock("DIS", 180.0, 15000),  # The Walt Disney Company - Initial price $180, initial volume 15000
    Stock("SBUX", 110.0, 20000),  # Starbucks Corporation - Initial price $110, initial volume 20000
    Stock("ADBE", 550.0, 7000),  # Adobe Inc. - Initial price $550, initial volume 7000
    Stock("CSCO", 55.0, 25000),  # Cisco Systems Inc. - Initial price $55, initial volume 25000
    Stock("PYPL", 200.0, 12000),  # PayPal Holdings Inc. (duplicate) - Initial price $200, initial volume 12000
    Stock("WMT", 140.0, 18000)  # Walmart Inc. - Initial price $140, initial volume 18000
]

# for stock in stocks:
#     existing_stock = Stock.query.filter_by(stock=stock.stock).first()
#     if not existing_stock:
#         db.session.add(stock)
#         db.session.commit()