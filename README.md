import os
import time
from decimal import Decimal

# CONFIGURAZIONE API PIONEX
# Sostituisci i valori tra virgolette con le tue chiavi reali
PIONEX_API_KEY = "LA_TUA_API_KEY_QUI"
PIONEX_SECRET_KEY = "LA_TUA_SECRET_KEY_QUI"

def calcola_profitto_reale(prezzo_acquisto, prezzo_vendita, quantita):
    """Calcola il guadagno effettivo non finto"""
    investimento = Decimal(prezzo_acquisto) * Decimal(quantita)
    ricavo = Decimal(prezzo_vendita) * Decimal(quantita)
    return ricavo - investimento

def esegui_trading_oro():
    # Simulazione logica corretta PR #3
    prezzo_oro_attuale = 2350.50  # Esempio prezzo PAXG
    budget_usdt = 100.0
    
    # FIX: Calcola quanto PAXG comprare in base ai dollari (non 1:1!)
    quantita_paxg = Decimal(budget_usdt) / Decimal(prezzo_oro_attuale)
    
    print(f"--- BOT ARGENTO AVVIATO ---")
    print(f"Prezzo Oro: {prezzo_oro_attuale} USDT")
    print(f"Quantità da acquistare: {quantita_paxg:.6f} PAXG")
    
    # Esempio calcolo profitto reale (non più 0.25 fisso)
    profitto = calcola_profitto_reale(2350.00, 2355.00, quantita_paxg)
    print(f"Profitto stimato operazione: +{profitto:.4f} USDT")

if __name__ == "__main__":
    esegui_trading_oro()
