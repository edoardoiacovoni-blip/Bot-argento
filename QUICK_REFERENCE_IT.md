# 🚀 Riferimento Rapido - Modalità Interattiva

## Attivazione
```bash
export INTERACTIVE_MODE=true
python3 main.py
```

## Test (Senza Trading Reale)
```bash
python3 test_interactive.py
```

## Comandi Durante l'Esecuzione

| Comando | Azione | Risultato |
|---------|--------|-----------|
| `INVIO` | Conferma e procedi | ✓ Esegue il passo corrente |
| `s` + `INVIO` | Salta questo passo | ⊘ Passa al prossimo passo |
| `q` + `INVIO` | Esci dal programma | ✗ Chiude il bot in modo pulito |

## Passi del Bot

1. 🔍 **Controllo segnali istituzionali**
2. 📊 **Recupero dati di mercato e calcolo opportunità**
3. 💰 **Esecuzione micro-trade su [SIMBOLO]**
4. 🥇 **Conversione in PAXG** (Paxos Gold - oro tokenizzato)
5. ✅ **Controllo finale e accumulazione**
6. ⏱️ **Attendere 15 secondi prima del prossimo ciclo**

> **Nota**: Il bot si chiama "Bot Argento" ma accumula in PAXG che rappresenta l'oro (gold). Il nome "Argento" è parte del branding del sistema.

## Modalità

### Interattiva ✋
- Controllo manuale di ogni operazione
- Ideale per: apprendimento, test, monitoraggio
- **Attivazione**: `INTERACTIVE_MODE=true`

### Automatica 🤖
- Esecuzione automatica senza intervento
- Ideale per: trading continuo, deployment produzione
- **Attivazione**: `INTERACTIVE_MODE=false` (o non impostato)

## Icone di Status

- ✓ Operazione completata con successo
- ⊘ Operazione saltata dall'utente
- ✗ Uscita o errore
- ⚠️ Avviso o notifica importante

## Supporto

Per problemi o domande, consulta:
- `README.md` - Documentazione completa
- `USAGE_IT.md` - Guida dettagliata in italiano
- Issues del repository su GitHub
