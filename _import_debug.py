import sys
import traceback
sys.path.insert(0, r'c:\Users\tanis\portfolio_optimizer')
try:
    import app.main as m
    print('OK', hasattr(m, 'app'))
except Exception:
    traceback.print_exc()
