import pandas as pd

def get_covariance_matrix(securities):

    returns = []

    for security in securities:
        returns.append(security.returns)

    df = pd.DataFrame(returns).T

    return df.cov().values
