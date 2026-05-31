def equal_weight_strategy(request):

    n = len(request.securities)

    return [1 / n] * n
