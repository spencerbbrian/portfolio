import csv
import random


# Define the headers and data
headers = ['ProductID', 'ProductName', 'Quantity','Price']
products = [
    'Laptop', 'Smartphone', 'Tablet', 'Monitor', 'Keyboard', 'Mouse', 'Printer', 'Scanner', 'Camera', 'Headphones',
    'Speakers', 'Microphone', 'Smartwatch', 'Fitness Tracker', 'External Hard Drive', 'USB Flash Drive', 'Router',
    'Modem', 'Projector', 'Webcam', 'Graphics Card', 'Motherboard', 'Processor', 'RAM', 'Power Supply', 'Cooling Fan',
    'Case', 'Laptop Bag', 'Phone Case', 'Screen Protector', 'Charger', 'Power Bank', 'HDMI Cable', 'Ethernet Cable',
    'Surge Protector', 'Extension Cord', 'VR Headset', 'Gaming Console', 'Game Controller', 'Smart Light', 'Smart Plug',
    'Smart Thermostat', 'Smart Doorbell', 'Smart Lock', 'Security Camera', 'Drone', '3D Printer', 'Electric Scooter',
    'Electric Bike', 'Hoverboard', 'Fitness Equipment', 'Treadmill', 'Exercise Bike', 'Elliptical', 'Dumbbells',
    'Yoga Mat', 'Resistance Bands', 'Jump Rope', 'Foam Roller', 'Massage Gun', 'Blender', 'Coffee Maker', 'Toaster',
    'Microwave', 'Air Fryer', 'Slow Cooker', 'Pressure Cooker', 'Rice Cooker', 'Electric Kettle', 'Stand Mixer',
    'Hand Mixer', 'Food Processor', 'Juicer', 'Ice Cream Maker'
]
data = []

# Generate random data
for i in range(1, 74):
    product_id = i
    product_name = products[i]
    quantity = random.randint(1, 452)
    price = round(random.uniform(1, 1000), 2)
    data.append([product_id, product_name, quantity, price])
    

# Write data to CSV file
with open('ecommerce_data.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(headers)
    writer.writerows(data)