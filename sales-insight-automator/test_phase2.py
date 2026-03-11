import requests
import json

with open('data/sales_q1_2026.csv', 'rb') as f:
    files = {'file': ('sales_q1_2026.csv', f, 'text/csv')}
    data = {'recipient_email': 'ceo@yourcompany.com'}
    response = requests.post('http://localhost:8000/api/v1/upload', files=files, data=data)
    
result = response.json()
print('AI EXECUTIVE BRIEF:')
print('=' * 70)
print(result['ai_brief'])
print()
print('=' * 70)
print('SUMMARY STATS:')
print(f"  Total Revenue: ${result['stats']['total_revenue']:,.2f}")
print(f"  Total Units: {result['stats']['total_units_sold']:,}")
print(f"  Top Category: {result['stats']['top_category']} (${result['stats']['top_category_revenue']:,.2f})")
print(f"  Rows Analyzed: {result['rows_analyzed']}")
print()
print('Full Response JSON:')
print(json.dumps(result, indent=2))
