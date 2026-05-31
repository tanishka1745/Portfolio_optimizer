import pandas as pd
import numpy as np

# Create synthetic return series for 5 funds (monthly returns over 24 months)
np.random.seed(42)
months = 24
funds = ['FUND_A', 'FUND_B', 'FUND_C', 'FUND_D', 'FUND_E']
rows = []
for f in funds:
    # generate small random returns
    returns = np.random.normal(loc=0.005, scale=0.03, size=months)  # ~0.5% monthly
    data = {
        'ticker': f,
        'security_name': f"{f} Name",
        'current_weight': 20.0,
        'dividend_yield': round(np.random.uniform(0.01, 0.05), 4),
    }
    for i in range(months):
        data[f'r_{i+1}'] = returns[i]
    rows.append(data)

pdf = pd.DataFrame(rows)
pdf.to_excel('test/example_inputs/securities.xlsx', index=False)

# Create factor returns (Momentum, Value, Size) over same months
factor_returns = {
    'Momentum': np.random.normal(0.004, 0.02, size=months),
    'Value': np.random.normal(0.003, 0.015, size=months),
    'Size': np.random.normal(0.002, 0.01, size=months),
}
ffd = pd.DataFrame(factor_returns)
ffd.to_excel('test/example_inputs/factors.xlsx', index=False)

print('Example files written to test/example_inputs/')
