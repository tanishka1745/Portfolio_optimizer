import sys
sys.path.insert(0, r"c:\Users\tanis\portfolio_optimizer")
import app.main as m
print('docs_url', m.app.docs_url)
print('redoc_url', m.app.redoc_url)
print('openapi_url', m.app.openapi_url)
print([route.path for route in m.app.routes])
