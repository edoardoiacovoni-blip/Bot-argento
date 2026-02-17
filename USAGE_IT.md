# Come Usare la Modalità Interattiva

## Guida Rapida

### 1. Attivare la Modalità Interattiva

Per attivare la modalità interattiva, imposta la variabile d'ambiente `INTERACTIVE_MODE=true`:

**Linux/Mac:**
```bash
export INTERACTIVE_MODE=true
python3 main.py
```

**Windows (Command Prompt):**
```cmd
set INTERACTIVE_MODE=true
python main.py
```

**Windows (PowerShell):**
```powershell
$env:INTERACTIVE_MODE="true"
python main.py
```

### 2. Test senza Trading Reale

Per testare la modalità interattiva senza eseguire vere operazioni di trading:

```bash
python3 test_interactive.py
```

Questo script simula il flusso del bot mostrando come funziona la modalità interattiva.

### 3. Utilizzo dei Comandi

Quando il bot è in modalità interattiva, vedrai messaggi come questo:

```
============================================================
PASSO: Controllo segnali istituzionali
============================================================

Premi INVIO per continuare, 's' per saltare, 'q' per uscire:
```

**Comandi disponibili:**

- **Premi INVIO** (tasto Invio vuoto): Il bot procede con l'operazione
  ```
  ✓ Confermato! Procedo...
  ```

- **Digita 's' + INVIO**: Il bot salta questo passo
  ```
  ⊘ Passo saltato.
  ```

- **Digita 'q' + INVIO**: Il bot si chiude
  ```
  ✗ Uscita richiesta dall'utente.
  ```

## Esempio di Sessione Interattiva

```
FLYING WHEEL ENGINE: TAKEOFF
Connected to: Pionex | Render | GitHub

============================================================
MODALITÀ INTERATTIVA ATTIVATA
============================================================
Il bot richiederà la tua conferma prima di ogni operazione.
Comandi disponibili:
  - INVIO: Conferma e procedi
  - 's': Salta questo passo
  - 'q': Esci dal programma
============================================================

⚠️  MODALITÀ INTERATTIVA ATTIVA
Il bot ti chiederà conferma prima di ogni passo.

============================================================
PASSO: Controllo segnali istituzionali
============================================================

Premi INVIO per continuare, 's' per saltare, 'q' per uscire: [INVIO]
✓ Confermato! Procedo...
Checking institutional signals...

============================================================
PASSO: Recupero dati di mercato e calcolo opportunità
============================================================

Premi INVIO per continuare, 's' per saltare, 'q' per uscire: [INVIO]
✓ Confermato! Procedo...
✓ Trovate 3 opportunità

============================================================
PASSO: Esecuzione micro-trade su BTCUSDT (tipo: BUY)
============================================================

Premi INVIO per continuare, 's' per saltare, 'q' per uscire: [INVIO]
✓ Confermato! Procedo...
✓ Trade eseguito con successo su BTCUSDT

============================================================
PASSO: Conversione di 0.25 in Argento (PAXG)
============================================================

Premi INVIO per continuare, 's' per saltare, 'q' per uscire: [INVIO]
✓ Confermato! Procedo...
Moving 0.25 to Silver (PAXG)...
✓ Conversione completata: 0.25 in PAXG
(Nota: PAXG = Paxos Gold, rappresenta oro fisico tokenizzato)

============================================================
PASSO: Controllo finale e accumulazione
============================================================

Premi INVIO per continuare, 's' per saltare, 'q' per uscire: [INVIO]
✓ Confermato! Procedo...
Checking institutional signals...
Accumulating in Silver...
JUMPING: Trend on BTCUSDT (+2.1%)

============================================================
PASSO: Attendere 15 secondi prima del prossimo ciclo
============================================================

Premi INVIO per continuare, 's' per saltare, 'q' per uscire: [INVIO]
✓ Confermato! Procedo...
```

## Quando Usare la Modalità Interattiva

✅ **Consigliata per:**
- Imparare come funziona il bot
- Testare nuove configurazioni
- Monitorare le operazioni in tempo reale
- Situazioni di mercato incerte dove vuoi più controllo
- Debugging e risoluzione problemi

❌ **Non consigliata per:**
- Trading automatico 24/7
- Deployment su server senza supervisione
- Alta frequenza di operazioni

## Modalità Automatica (Default)

Per usare il bot in modalità automatica (senza conferme):

```bash
# Non impostare INTERACTIVE_MODE o impostalo a false
python3 main.py
```

oppure:

```bash
export INTERACTIVE_MODE=false
python3 main.py
```

In modalità automatica, il bot eseguirà tutte le operazioni senza chiedere conferma.

## Suggerimenti

1. **Prima volta**: Usa sempre `test_interactive.py` per familiarizzare con i comandi
2. **Testing**: Prova la modalità interattiva con piccole quantità prima
3. **Monitoraggio**: Tieni d'occhio i log anche in modalità automatica
4. **Sicurezza**: Non lasciare mai le API keys visibili nei file o nei log

## Risoluzione Problemi

**Il bot non chiede conferma:**
- Verifica che `INTERACTIVE_MODE=true` sia impostato
- Controlla che non ci siano errori di sintassi nella variabile

**Il bot non risponde ai comandi:**
- Assicurati di premere INVIO dopo aver digitato il comando
- Verifica che il terminale supporti l'input interattivo

**Interruzione improvvisa:**
- Usa 'q' per uscire in modo pulito invece di Ctrl+C
- Se necessario, usa Ctrl+C per forzare la chiusura
