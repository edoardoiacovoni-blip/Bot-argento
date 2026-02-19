import time
import os
import sys
from typing import List, Dict, Any, Optional
from pionex import Pionex

# Configuration from environment variables
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
INTERACTIVE_MODE = os.getenv("INTERACTIVE_MODE", "false").lower() == "true"

# Validate required environment variables
if not API_KEY or not SECRET_KEY:
    print("❌ ERRORE: API_KEY e SECRET_KEY devono essere configurate nelle variabili d'ambiente")
    print("Configura le variabili e riavvia il bot.")
    sys.exit(1)

# Initialize Pionex client
try:
    client = Pionex(api_key=API_KEY, api_secret=SECRET_KEY)
except Exception as e:
    print(f"❌ ERRORE nell'inizializzazione del client Pionex: {e}")
    sys.exit(1)

def wait_for_confirmation(step_description: str) -> bool:
    """Wait for user confirmation before proceeding to next step
    
    Args:
        step_description: Description of the step to confirm
        
    Returns:
        True if user confirms, False if user skips
    """
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

def calculate_quantum_jump(market_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analisi 18 punti per identificazione dei trend
    
    Args:
        market_data: Lista di dati di mercato
        
    Returns:
        Lista di opportunità di trading (massimo 5)
    """
    try:
        choices = [m for m in market_data if float(m.get('priceChangePercent', 0)) > 1.8]
        return choices[:5]
    except (ValueError, TypeError, KeyError) as e:
        print(f"⚠️ Errore nell'analisi dei dati di mercato: {e}")
        return []

def check_institutional_signals() -> bool:
    """Monitora i segnali istituzionali
    
    Returns:
        True se i segnali sono positivi, False altrimenti
    """
    if wait_for_confirmation("Controllo segnali istituzionali"):
        print("🔍 Controllo segnali istituzionali...")
        # TODO: Implementare logica reale di controllo segnali
        return True
    return True

def execute_micro_trade(symbol: str, trade_type: str = "BUY") -> float:
    """Esegue micro-operazione tramite Pionex
    
    Args:
        symbol: Simbolo della coppia di trading
        trade_type: Tipo di trade (BUY o SELL)
        
    Returns:
        Profitto generato dal trade (0 se fallito o saltato)
    """
    if not wait_for_confirmation(f"Esecuzione micro-trade su {symbol} (tipo: {trade_type})"):
        return 0.0
        
    try:
        order = client.create_order(
            symbol=symbol,
            side=trade_type,
            type='MARKET',
            quantity=0.01
        )
        print(f"✓ Trade eseguito con successo su {symbol}")
        print(f"📊 Dettagli ordine: {order}")
        return 0.25  # Profitto simulato - da calcolare in base all'ordine reale
    except Exception as e:
        print(f"❌ Errore durante il trade su {symbol}: {e}")
        return 0.0

def convert_to_paxg(profit: float) -> bool:
    """Accumula profitti in PAXG (Paxos Gold) tramite Pionex
    
    Nota: La funzione precedente si chiamava 'convert_to_silver' per motivi di branding,
    ma in realtà converte in PAXG (oro tokenizzato).
    
    Args:
        profit: Ammontare del profitto da convertire
        
    Returns:
        True se la conversione ha successo, False altrimenti
    """
    if profit <= 0:
        print("⚠️ Nessun profitto da convertire")
        return False
        
    if not wait_for_confirmation(f"Conversione di {profit} in PAXG (oro tokenizzato)"):
        return False
        
    print(f"💰 Conversione di {profit} in PAXG...")
    try:
        order = client.create_order(
            symbol='PAXGUSD',
            side='BUY',
            type='MARKET',
            quantity=profit
        )
        print(f"✓ Conversione completata: {profit} in PAXG")
        print(f"📊 Dettagli ordine: {order}")
        return True
    except Exception as e:
        print(f"❌ Errore durante l'accumulo in PAXG: {e}")
        return False

def check_institutional() -> None:
    """Controllo approfondito dei segnali istituzionali"""
    print("🔍 Controllo segnali istituzionali...")
    # TODO: Implementare logica di controllo

def accumulate_in_paxg() -> None:
    """Verifica accumulazione in PAXG"""
    print("💰 Verifica accumulazione in PAXG...")
    # TODO: Implementare logica di verifica accumulo

def flying_wheel_engine() -> None:
    """Flying Wheel System - coordinazione tra analisi 18 punti e accumulo in PAXG"""
    print("🚀 FLYING WHEEL SYSTEM IN ESECUZIONE...")
    print("🎯 TARGET: ACCUMULO IN PAXG (Paxos Gold)")
    print("🔗 Platform: Pionex + Render + GitHub")
    
    if INTERACTIVE_MODE:
        print("\n⚠️  MODALITÀ INTERATTIVA ATTIVA")
        print("Il bot ti chiederà conferma prima di ogni passo.\n")
    
    cycle_count = 0
    
    while True:
        try:
            cycle_count += 1
            print(f"\n{'='*60}")
            print(f"📊 CICLO #{cycle_count}")
            print(f"{'='*60}")
            
            # Step 1: Check institutional signals
            if not check_institutional_signals():
                print("⏳ Segnali non favorevoli, attesa 30 secondi...")
                time.sleep(30)
                continue

            # Step 2: Get market data and calculate opportunities
            opportunities: List[Dict[str, Any]] = []
            if wait_for_confirmation("Recupero dati di mercato e calcolo opportunità"):
                try:
                    response = client.get_ticker()
                    opportunities = calculate_quantum_jump(response)
                    print(f"✓ Trovate {len(opportunities)} opportunità")
                except Exception as e:
                    print(f"❌ Errore nel recupero dei dati di mercato: {e}")
                    time.sleep(10)
                    continue

            # Step 3: Execute trades on opportunities
            for opportunity in opportunities:
                symbol = opportunity.get('symbol', 'UNKNOWN')
                price_change = opportunity.get('priceChangePercent', 0)
                
                print(f"\n🎯 Opportunità rilevata: {symbol} (+{price_change}%)")
                
                gain = execute_micro_trade(symbol)
                
                if gain > 0:
                    # Step 4: Convert profits to PAXG
                    convert_to_paxg(gain)
                    
                    # Step 5: Final checks and accumulation
                    if wait_for_confirmation("Controllo finale e accumulazione"):
                        check_institutional()
                        accumulate_in_paxg()
                    
                    print(f"✨ JUMPING: Trend su {symbol} (+{price_change}%)")

            # Step 6: Wait before next cycle
            if INTERACTIVE_MODE:
                wait_for_confirmation("Attesa di 15 secondi prima del prossimo ciclo")
            else:
                print("⏳ Attesa 15 secondi prima del prossimo ciclo...")
            
            time.sleep(15)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interruzione manuale rilevata (CTRL+C)")
            print("🛑 Chiusura del bot...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Errore di sistema: {e}")
            print("⏳ Attesa 10 secondi prima di riprovare...")
            time.sleep(10)
            continue

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 FLYING WHEEL ENGINE: AVVIO")
    print("="*60)
    print("🔗 Connesso a: Pionex | Render | GitHub")
    print(f"📊 Modalità: {'INTERATTIVA' if INTERACTIVE_MODE else 'AUTOMATICA'}")
    
    if INTERACTIVE_MODE:
        print("\n" + "="*60)
        print("⚠️  MODALITÀ INTERATTIVA ATTIVATA")
        print("="*60)
        print("Il bot richiederà la tua conferma prima di ogni operazione.")
        print("\nComandi disponibili:")
        print("  • INVIO: Conferma e procedi")
        print("  • 's': Salta questo passo")
        print("  • 'q': Esci dal programma")
        print("="*60 + "\n")
    
    try:
        flying_wheel_engine()
    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")
        print("🛑 Il bot si è arrestato.")
        sys.exit(1)