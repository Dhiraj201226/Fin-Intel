import csv
import os

input_file = r'c:\Users\dhira\Downloads\EQUITY_L.csv'
output_file = r'c:\Users\dhira\OneDrive\Desktop\CEP SEM4\1st attempt\ARA-1-Financial-Agent\backend\app\ticker_mapping.csv'

with open(input_file, mode='r', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    
    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['Company Name', 'Ticker'])
        
        for row in reader:
            name = row.get('NAME OF COMPANY', '').strip()
            symbol = row.get('SYMBOL', '').strip()
            if name and symbol:
                writer.writerow([name, f"{symbol}.NS"])

print(f"Successfully created {output_file}")
