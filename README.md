# Bot Argento - Flying Wheel Trading System

Bot di trading automatico che utilizza il "Flying Wheel System" per identificare opportunità di trading e accumulare profitti in PAXG (Paxos Gold) tramite la piattaforma Pionex.

> **Nota sul nome**: Il bot si chiama "Bot Argento" (Silver Bot) per design/branding, ma accumula in PAXG che rappresenta l'oro (Paxos Gold). Il termine "Argento" nel contesto del bot si riferisce all'accumulo di metalli preziosi in generale.

## Caratteristiche

- **Analisi 18 punti**: Sistema di analisi del mercato per identificare trend
- **Micro-trading**: Esecuzione di micro-operazioni su Pionex
- **Accumulo in PAXG**: Conversione automatica dei profitti in PAXG (Paxos Gold - oro tokenizzato)
- **Modalità Interattiva**: Controllo passo-passo delle operazioni

## Configurazione

### Variabili d'Ambiente Richieste

```bash
API_KEY=your_pionex_api_key
SECRET_KEY=your_pionex_secret_key
INTERACTIVE_MODE=TRUE  # Imposta a "true" per attivare la modalità interattiva
```

## Modalità di Esecuzione

### Modalità Automatica (Default)

Il bot esegue operazioni automaticamente senza intervento dell'utente:

```bash
python3 main.py
```

### Modalità Interattiva

Il bot chiede conferma prima di ogni passo:

```bash
export INTERACTIVE_MODE=true
python3 main.py
```

In modalità interattiva, il bot mostrerà:

```
============================================================
PASSO: [Descrizione dell'operazione]
============================================================

Premi INVIO per continuare, 's' per saltare, 'q' per uscire:
```

**Comandi disponibili:**
- **INVIO**: Conferma e procedi con l'operazione
- **s**: Salta questo passo e passa al successivo
- **q**: Esci dal programma

## Passaggi del Bot

Quando attivata la modalità interattiva, il bot richiederà conferma per:

1. **Controllo segnali istituzionali**: Verifica dei segnali di mercato
2. **Recupero dati di mercato**: Ottiene i dati di mercato e calcola le opportunità
3. **Esecuzione micro-trade**: Esegue un trade su un simbolo specifico
4. **Conversione in PAXG**: Converte i profitti in PAXG (oro tokenizzato)
5. **Controllo finale e accumulazione**: Verifica e accumula
6. **Attesa prossimo ciclo**: Pausa di 15 secondi prima del ciclo successivo

## Struttura del Codice

- `wait_for_confirmation()`: Gestisce la conferma utente in modalità interattiva
- `calculate_quantum_jump()`: Analizza i dati di mercato per identificare opportunità
- `check_institutional_signals()`: Monitora i segnali istituzionali
- `execute_micro_trade()`: Esegue un micro-trade su Pionex
- `convert_to_silver()`: Converte profitti in PAXG
- `flying_wheel_engine()`: Motore principale del sistema

## Sicurezza

⚠️ **Importante**: 
- Non condividere mai le tue API keys
- Testa sempre in ambiente di staging prima della produzione
- La modalità interattiva è ideale per test e apprendimento

## Deployment

Il bot è progettato per essere deployato su:
- **Render**: Per esecuzione continua
- **GitHub**: Per controllo versione
- **Pionex**: Piattaforma di trading

## Licenza

Questo progetto è privato e proprietario.
