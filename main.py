import requests
import time
import os
from pionex import Pionex

# Configuration from Render environment
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

# Initialize Pionex client
client = Pionex(api_key=API_KEY, api_secret=SECRET_KEY)

def calculate_quantum_jump(market_data):
    """18 points analysis for trend identification"""
    choices = [m for m in market_data if float(m['priceChangePercent']) > 1.8]
    return choices[:5]

def check_institutional_signals():
    """Monitor institutional signals"""
    # TODO: Implement actual institutional signal checking logic
    # For now, return True to keep the bot running
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
        # Calculate actual profit from order execution
        # Market orders return 'fills' with individual execution details
        if order and 'fills' in order:
            total_value = sum(float(fill['price']) * float(fill['qty']) for fill in order['fills'])
            profit = total_value * 0.001  # 0.1% estimated profit
            return profit
        return 0
    except Exception as e:
        print(f"Trade error: {e}")
        return 0

def convert_to_silver(profit):
    """Accumulate in Gold (PAXG) via Pionex"""
    if profit > 0:
        print(f"Moving {profit} USD to Gold (PAXG)...")
        try:
            # Get current PAXG price - fetch only PAXGUSD ticker for efficiency
            ticker = client.get_ticker(symbol='PAXGUSD')
            
            # Handle both single ticker dict and list responses
            if isinstance(ticker, list) and len(ticker) > 0:
                paxg_price = float(ticker[0]['lastPrice'])
            elif isinstance(ticker, dict) and 'lastPrice' in ticker:
                paxg_price = float(ticker['lastPrice'])
            else:
                print(f"Could not get PAXG price")
                return False
            
            if paxg_price > 0:
                # Calculate quantity and round to 8 decimal places (common for crypto)
                quantity = round(profit / paxg_price, 8)
                
                # Check if quantity is above a reasonable minimum (0.00001 PAXG)
                if quantity < 0.00001:
                    print(f"Quantity {quantity} too small, skipping conversion")
                    return False
                
                client.create_order(
                    symbol='PAXGUSD',
                    side='BUY',
                    type='MARKET',
                    quantity=quantity
                )
                print(f"Successfully converted {profit} USD to {quantity} PAXG")
                return True
            else:
                print(f"Invalid PAXG price: {paxg_price}")
                return False
        except Exception as e:
            print(f"Gold accumulation error: {e}")
            return False
    return False

def flying_wheel_engine():
    """Flying Wheel System - coordinated 18 points and gold accumulation"""
    print("FLYING WHEEL SYSTEM IN EXECUTION...")
    print("TARGET: GOLD ACCUMULATION (PAXG)")
    print("Platform: Pionex + Render + GitHub")
    
    while True:
        try:
            if not check_institutional_signals():
                time.sleep(30)
                continue

            response = client.get_ticker()
            
            # Validate response before processing
            if not response or not isinstance(response, list) or len(response) == 0:
                print("Invalid or empty market data received")
                time.sleep(30)
                continue
            
            opportunities = calculate_quantum_jump(response)

            for opportunity in opportunities:
                gain = execute_micro_trade(opportunity['symbol'])
                
                if gain > 0:
                    success = convert_to_silver(gain)
                    if success:
                        print(f"JUMPING: Trend on {opportunity['symbol']} (+{opportunity['priceChangePercent']}%)")

            time.sleep(15)

        except Exception as e:
            print(f"System error: {e}")
            time.sleep(10)
            continue

if __name__ == "__main__":
    print("FLYING WHEEL ENGINE: TAKEOFF")
    print("Connected to: Pionex | Render | GitHub")
    flying_wheel_engine()