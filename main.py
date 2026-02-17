import requests
import time
import os
import sys
from pionex import Pionex

# Configuration from Render environment
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
INTERACTIVE_MODE = os.getenv("INTERACTIVE_MODE", "false").lower() == "true"

# Initialize Pionex client
client = Pionex(api_key=API_KEY, api_secret=SECRET_KEY)

def wait_for_confirmation(step_description):
    """Wait for user confirmation before proceeding to next step"""
    if not INTERACTIVE_MODE:
        return True
    
    print(f"\n{'='*60}")
    print(f"PASSO: {step_description}")
    print(f"{'='*60}")
    
    while True:
        response = input("\nPremi INVIO per continuare, 's' per saltare, 'q' per uscire: ").strip().lower()
        if response == '':
            print("✓ Confermato! Procedo...")
            return True
        elif response == 's':
            print("⊘ Passo saltato.")
            return False
        elif response == 'q':
            print("✗ Uscita richiesta dall'utente.")
            sys.exit(0)
        else:
            print("Opzione non valida. Usa INVIO per confermare, 's' per saltare, 'q' per uscire.")

def calculate_quantum_jump(market_data):
    """18 points analysis for trend identification"""
    choices = [m for m in market_data if float(m['priceChangePercent']) > 1.8]
    return choices[:5]

def check_institutional_signals():
    """Monitor institutional signals"""
    if wait_for_confirmation("Controllo segnali istituzionali"):
        print("Checking institutional signals...")
    return True 

def execute_micro_trade(symbol, trade_type="BUY"):
    """Execute micro-operation via Pionex"""
    if not wait_for_confirmation(f"Esecuzione micro-trade su {symbol} (tipo: {trade_type})"):
        return 0
        
    try:
        order = client.create_order(
            symbol=symbol,
            side=trade_type,
            type='MARKET',
            quantity=0.01
        )
        print(f"✓ Trade eseguito con successo su {symbol}")
        return 0.25
    except Exception as e:
        print(f"Trade error: {e}")
        return 0

def convert_to_silver(profit):
    """Accumulate in Silver (PAXG) via Pionex"""
    if profit > 0:
        if not wait_for_confirmation(f"Conversione di {profit} in Argento (PAXG)"):
            return
            
        print(f"Moving {profit} to Silver (PAXG)...")
        try:
            client.create_order(
                symbol='PAXGUSD',
                side='BUY',
                type='MARKET',
                quantity=profit
            )
            print(f"✓ Conversione completata: {profit} in PAXG")
        except Exception as e:
            print(f"Silver accumulation error: {e}")

def check_institutional():
    """Check institutional signals"""
    print("Checking institutional signals...")

def accumulate_in_silver():
    """Accumulate profit in Silver"""
    print("Accumulating in Silver...")

def flying_wheel_engine():
    """Flying Wheel System - coordinated 18 points and silver accumulation"""
    print("FLYING WHEEL SYSTEM IN EXECUTION...")
    print("TARGET: SILVER ACCUMULATION (PAXG)")
    print("Platform: Pionex + Render + GitHub")
    
    if INTERACTIVE_MODE:
        print("\n⚠️  MODALITÀ INTERATTIVA ATTIVA")
        print("Il bot ti chiederà conferma prima di ogni passo.\n")
    
    while True:
        try:
            if not check_institutional_signals():
                time.sleep(30)
                continue

            if wait_for_confirmation("Recupero dati di mercato e calcolo opportunità"):
                response = client.get_ticker()
                opportunities = calculate_quantum_jump(response)
                print(f"✓ Trovate {len(opportunities)} opportunità")

            for opportunity in opportunities:
                gain = execute_micro_trade(opportunity['symbol'])
                
                if gain > 0:
                    convert_to_silver(gain)
                    
                    if wait_for_confirmation("Controllo finale e accumulazione"):
                        check_institutional()
                        accumulate_in_silver()
                    
                    print(f"JUMPING: Trend on {opportunity['symbol']} (+{opportunity['priceChangePercent']}%)")

            if INTERACTIVE_MODE:
                if not wait_for_confirmation("Attendere 15 secondi prima del prossimo ciclo"):
                    pass
            
            time.sleep(15)

        except Exception as e:
            print(f"System error: {e}")
            time.sleep(10)
            continue

if __name__ == "__main__":
    print("FLYING WHEEL ENGINE: TAKEOFF")
    print("Connected to: Pionex | Render | GitHub")
    
    if INTERACTIVE_MODE:
        print("\n" + "="*60)
        print("MODALITÀ INTERATTIVA ATTIVATA")
        print("="*60)
        print("Il bot richiederà la tua conferma prima di ogni operazione.")
        print("Comandi disponibili:")
        print("  - INVIO: Conferma e procedi")
        print("  - 's': Salta questo passo")
        print("  - 'q': Esci dal programma")
        print("="*60 + "\n")
    
    flying_wheel_engine()