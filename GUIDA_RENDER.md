# 🚀 Guida Deploy: Bot-argento su Render (Worker)

## Prerequisiti

- Account [Render](https://render.com) (gratuito)
- API Key e Secret Key di Pionex → [Ottienile qui](https://www.pionex.com/en-US/account/api-management)
  - ⚠️ Le chiavi devono avere **solo permesso Trading** — **NON abilitare Withdraw**
- Accesso owner/collaborator al repository GitHub

## 📋 Checklist Rapida

- [ ] Account Render creato
- [ ] API Key Pionex disponibili (solo Trading, no Withdraw)
- [ ] Accesso al repository GitHub confermato

## 🎯 Procedura in 5 Passaggi

### Passaggio 1: Accedi a Render

```
1. Vai su https://dashboard.render.com/
2. Fai login o registrati
3. Autorizza Render ad accedere a GitHub quando richiesto
```

### Passaggio 2: Crea il Worker

```
1. Clicca "New +" (in alto a destra)
2. Seleziona "Background Worker"   ← IMPORTANTE: NON "Web Service"
3. Cerca "Bot-argento" nella lista dei repository
4. Clicca "Connect"
```

### Passaggio 3: Verifica la Configurazione

```
Render compilerà automaticamente questi campi grazie al file render.yaml:

✓ Name: bot-argento
✓ Type: Background Worker
✓ Environment: Python 3
✓ Build Command: pip install -r requirements.txt
✓ Start Command: python main.py
✓ DRY_RUN: 0  (trading reale — cambia a 1 per test)
✓ SYMBOL: XAG_USDT
✓ LOOP_SECONDS: 10
✓ ... (tutte le variabili di default)
```

### Passaggio 4: Aggiungi le Credenziali (IMPORTANTE!)

```
Nella sezione "Environment Variables", aggiungi:

1. PIONEX_API_KEY  = [la tua API key di Pionex]
2. PIONEX_SECRET_KEY = [il tuo Secret key di Pionex]

Per il trading simulato imposta anche:
3. DRY_RUN = 1   (raccomandato per il primo test)

⚠️ SENZA le API key il bot si fermerà con un errore chiaro nei log.
⚠️ Le API key devono avere SOLO permesso Trading, mai Withdraw.
```

### Passaggio 5: Deploy

```
1. Clicca "Create Background Worker"
2. Aspetta il build (2-3 minuti — installa pandas/numpy)
3. Controlla i log per vedere "FLYING WHEEL ENGINE: TAKEOFF"
4. ✅ Il bot è attivo!
```

## 🔍 Come Monitorare il Worker

1. Vai su https://dashboard.render.com/
2. Clicca sul servizio "bot-argento"
3. Sezione **Logs**: output in tempo reale
4. Sezione **Environment**: variabili d'ambiente configurate
5. Sezione **Events**: storia dei deploy

### Cosa cercare nei log

```
🔵 Modalità DRY_RUN attiva       ← OK se DRY_RUN=1
🔴 Modalità REALE attiva          ← Attenzione: ordini reali!
Connessione API Pionex OK
FLYING WHEEL ENGINE: TAKEOFF
  [01/18] PASS — check_01: trend rialzista ...
  [02/18] FAIL — check_02: nessun BOS ...    ← normale se mercato non in setup
  ...
⚠️  Flying Wheel: uno o più check falliti    ← normale, nessun ordine
✅ Flying Wheel completato — piano: BUY ...   ← tutti i check passati
DRY_RUN: simulazione trade BUY XAG_USDT      ← se DRY_RUN=1
ORDINE ESEGUITO: BUY XAG_USDT ...            ← se DRY_RUN=0
```

## ⚙️ Configurazione Avanzata

### Provider DXY (Correlazione Dollaro)

Il check 10 (correlazione DXY) richiede un provider esterno:

```
# Disabilitato (default) — il check viene saltato
DXY_PROVIDER=none

# Custom URL — deve rispondere con {"bias": "bullish"|"bearish"}
DXY_PROVIDER=url
DXY_URL=https://your-dxy-api.example.com/bias
DXY_API_KEY=optional_key
```

### Provider Notizie

Il check 14 (filtro notizie) richiede un provider esterno:

```
# Disabilitato (default) — il check viene saltato
NEWS_PROVIDER=none

# Custom URL — deve rispondere con {"high_impact": true|false}
NEWS_PROVIDER=url
NEWS_URL=https://your-news-api.example.com/high-impact
NEWS_API_KEY=optional_key
```

### STRICT_EXTERNALS

```
STRICT_EXTERNALS=0  (default) → check 10/14 passano sempre se provider mancante
STRICT_EXTERNALS=1            → check 10/14 FALLISCONO se provider mancante
```

## 🔄 Aggiornamenti Automatici

Una volta collegato:
- Ogni `git push` su GitHub → Render fa automaticamente il redeploy
- Il Worker si riavvia con il nuovo codice

## ⚡ Risoluzione Problemi Comuni

### Problema: "Repository not found"
**Soluzione**: Autorizza Render ad accedere ai tuoi repository GitHub nelle impostazioni account.

### Problema: "Build failed"
**Soluzione**: Verifica che `requirements.txt` contenga pandas e numpy.

### Problema: "Bot si ferma subito con errore variabili mancanti"
**Soluzione**: Aggiungi `PIONEX_API_KEY` e `PIONEX_SECRET_KEY` nelle Environment Variables.

### Problema: "Tutti i check FAIL — nessun ordine"
**Soluzione**: Normale durante fasi di mercato senza setup. Il bot attende le condizioni giuste.

### Problema: "check_01 FAIL — close <= EMA200"
**Soluzione**: Il mercato è in trend ribassista. Il bot non opera finché il prezzo non supera EMA200.

## ✅ Checklist Post-Deploy

Dopo il deploy, verifica nei log:
- [ ] `Connessione API Pionex OK`
- [ ] `FLYING WHEEL ENGINE: TAKEOFF` appare ogni ~10 secondi
- [ ] Nessun errore `Errore richiesta API Pionex`
- [ ] Con `DRY_RUN=1`: appare `DRY_RUN: simulazione trade` quando i check passano

## 📚 Documentazione

- [README.md](./README.md) — Descrizione completa del progetto e variabili d'ambiente
- [render.yaml](./render.yaml) — Configurazione automatica Render
- [.env.example](./.env.example) — Template variabili d'ambiente

