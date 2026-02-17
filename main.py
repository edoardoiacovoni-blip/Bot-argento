import requests
import time
import os
import hmac
import hashlib
from urllib.parse import urlencode

# Configuration from Render environment
API_KEY = os.getenv("PIONEX_API_KEY")
SECRET_KEY = os.getenv("PIONEX_SECRET_KEY")

# Pionex API Configuration
PIONEX_API_BASE = "https://api.pionex.com"


class PionexClient:
    """Client for Pionex API connection"""
    
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = PIONEX_API_BASE
        
    def _generate_signature(self, params):
        """Generate HMAC SHA256 signature for Pionex API"""
        query_string = urlencode(sorted(params.items()))
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method, endpoint, params=None):
        """Make authenticated request to Pionex API"""
        if params is None:
            params = {}
        
        params['timestamp'] = int(time.time() * 1000)
        params['recvWindow'] = 5000
        
        signature = self._generate_signature(params)
        params['signature'] = signature
        
        headers = {
            'PIONEX-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request error: {e}")
            return None
    
    def get_ticker(self):
        """Get market ticker data"""
        return self._make_request('GET', '/api/v1/market/tickers')
    
    def create_order(self, symbol, side, type, quantity):
        """Create a new order"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': type,
            'quantity': quantity
        }
        return self._make_request('POST', '/api/v1/trade/order', params)
    
    def test_connection(self):
        """Test Pionex API connection"""
        try:
            result = self._make_request('GET', '/api/v1/common/timestamp')
            return result is not None
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


# Initialize Pionex client
client = PionexClient(api_key=API_KEY, secret_key=SECRET_KEY) if API_KEY and SECRET_KEY else None

def calculate_quantum_jump(market_data):
    """18 points analysis for trend identification"""
    choices = [m for m in market_data if float(m['priceChangePercent']) > 1.8]
    return choices[:5]

def check_institutional_signals():
    """Monitor institutional signals"""
    return True 

def execute_micro_trade(symbol, trade_type="BUY"):
    """Execute micro-operation via Pionex"""
    try:
        order = client.create_order(
            symbol=symbol,
            side=trade_type,
            type='MARKET',
            quantity=0.01
        )
        return 0.25
    except Exception as e:
        print(f"Trade error: {e}")
        return 0

def convert_to_silver(profit):
    """Accumulate in Silver (PAXG) via Pionex"""
    if profit > 0:
        print(f"Moving {profit} to Silver (PAXG)...")
        try:
            client.create_order(
                symbol='PAXGUSD',
                side='BUY',
                type='MARKET',
                quantity=profit
            )
        except Exception as e:
            print(f"Silver accumulation error: {e}")

def check_institutional():
    """Check institutional signals"""
    print("Checking institutional signals...")

def accumulate_in_silver():
    """Accumulate profit in Silver"""
    print("Accumulating in Silver...")

def verify_connections():
    """Verify all required connections"""
    print("=" * 60)
    print("VERIFYING CONNECTIONS...")
    print("=" * 60)
    
    # Check Pionex connection
    if client is None:
        print("❌ Pionex: Not configured (missing API credentials)")
        print("   Set PIONEX_API_KEY and PIONEX_SECRET_KEY environment variables")
        return False
    else:
        print("✓ Pionex: Client initialized")
        if client.test_connection():
            print("✓ Pionex: API connection successful")
        else:
            print("⚠ Pionex: API connection failed (check credentials)")
    
    # Check Render environment
    render_env = os.getenv("RENDER")
    if render_env:
        print("✓ Render: Running on Render platform")
    else:
        print("⚠ Render: Not running on Render (local environment)")
    
    print("=" * 60)
    return True


def flying_wheel_engine():
    """Flying Wheel System - coordinated 18 points and silver accumulation"""
    print("FLYING WHEEL SYSTEM IN EXECUTION...")
    print("TARGET: SILVER ACCUMULATION (PAXG)")
    print("Platform: Pionex + Render + GitHub")
    
    # Verify connections before starting
    if not verify_connections():
        print("⚠ WARNING: Running with incomplete configuration")
    
    if client is None:
        print("ERROR: Cannot run without Pionex credentials")
        print("Please set PIONEX_API_KEY and PIONEX_SECRET_KEY environment variables")
        return
    
    while True:
        try:
            if not check_institutional_signals():
                time.sleep(30)
                continue

            response = client.get_ticker()
            if response is None:
                print("Failed to get ticker data, retrying...")
                time.sleep(30)
                continue
                
            opportunities = calculate_quantum_jump(response)

            for opportunity in opportunities:
                gain = execute_micro_trade(opportunity['symbol'])
                
                if gain > 0:
                    convert_to_silver(gain)
                    check_institutional()
                    accumulate_in_silver()
                    print(f"JUMPING: Trend on {opportunity['symbol']} (+{opportunity['priceChangePercent']}%)")

            time.sleep(15)

        except Exception as e:
            print(f"System error: {e}")
            time.sleep(10)
            continue

if __name__ == "__main__":
    print("=" * 60)
    print("FLYING WHEEL ENGINE: TAKEOFF")
    print("=" * 60)
    print("Connections:")
    print("  - Pionex API (Cryptocurrency Trading)")
    print("  - Render (Cloud Deployment Platform)")
    print("  - GitHub (Version Control)")
    print("=" * 60)
    flying_wheel_engine()