from app.strategy.equal_weight import equal_weight_strategy
from app.strategy.min_volatility import min_volatility_strategy

def optimize_portfolio(request):

    strategy = request.strategy

    if strategy == "equal_weight":
        weights = equal_weight_strategy(request)

    elif strategy == "minimize_volatility":
        weights = min_volatility_strategy(request)

    else:
        raise Exception("Invalid strategy")

    response = []

    for i, security in enumerate(request.securities):

        optimized_weight = round(weights[i] * 100, 2)

        response.append({
            "ticker": security.ticker,
            "security_name": security.security_name,
            "current_weight": security.current_weight,
            "optimized_weight": optimized_weight,
            "change": round(
                optimized_weight - security.current_weight,
                2
            )
        })

    return {
        "optimization_strategy": strategy,
        "allocation_changes": response
    }