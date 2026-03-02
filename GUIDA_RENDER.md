# 🚀 Guida Deploy: Bot-argento su Render (Worker)

## Prerequisiti

- Account [Render](https://render.com) (gratuito)
- API Key e Secret Key di Pionex → [Ottienile qui](https://www.pionex.com/en-US/account/api-management)
- Accesso owner/collaborator al repository GitHub

## 📋 Checklist Rapida

- [ ] Account Render creato
- [ ] API Key Pionex disponibili
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
✓ DRY_RUN: 1 (impostato automaticamente)
```

### Passaggio 4: Aggiungi le Credenziali (IMPORTANTE!)

```
Nella sezione "Environment Variables", aggiungi:

1. PIONEX_API_KEY  = [la tua API key di Pionex]
2. PIONEX_SECRET_KEY = [il tuo Secret key di Pionex]
3. SILVER_SYMBOL = [simbolo argento SPOT, es. XAG_USDT]

Per il trading reale imposta anche:
4. DRY_RUN = 0   (default: 1 = modalità sicura, nessun ordine reale)

⚠️ SENZA le API key e SILVER_SYMBOL il bot si fermerà con un errore chiaro nei log.
```

### Passaggio 5: Deploy

```
1. Clicca "Create Background Worker"
2. Aspetta il build (1-2 minuti)
3. Controlla i log per vedere "FLYING WHEEL ENGINE: TAKEOFF"
4. ✅ Il bot è attivo!
```

## 🔍 Come Monitorare il Worker

1. Vai su https://dashboard.render.com/
2. Clicca sul servizio "bot-argento"
3. Sezione **Logs**: output in tempo reale (cerca "FLYING WHEEL ENGINE")
4. Sezione **Environment**: variabili d'ambiente configurate
5. Sezione **Events**: storia dei deploy

## 🔄 Aggiornamenti Automatici

Una volta collegato:
- Ogni `git push` su GitHub → Render fa automaticamente il redeploy
- Il Worker si riavvia con il nuovo codice

## ⚡ Risoluzione Problemi Comuni

### Problema: "Repository not found"
**Soluzione**: Autorizza Render ad accedere ai tuoi repository GitHub nelle impostazioni account.

### Problema: "Build failed"
**Soluzione**: Verifica che `requirements.txt` sia presente nel repository.

### Problema: "Bot si ferma subito con errore variabili mancanti"
**Soluzione**: Aggiungi `PIONEX_API_KEY` e `PIONEX_SECRET_KEY` nelle Environment Variables del Worker.

### Problema: "Tutti i check PASS ma nessun ordine eseguito"
**Soluzione**: Verifica che `DRY_RUN` sia impostato a `0` se vuoi il trading reale.

## ✅ Checklist Post-Deploy

Dopo il deploy, verifica nei log:
- [ ] `Modalità DRY_RUN attiva` (oppure `REALE` se intenzionale)
- [ ] `FLYING WHEEL ENGINE: TAKEOFF`
- [ ] `[01/18] PASS` … `[18/18] PASS`
- [ ] `FLYING WHEEL ENGINE: TUTTI I CHECK SUPERATI ✅`

Se tutto è ✅, il bot è attivo! 🎉

## 📚 Documentazione

- [README.md](./README.md) — Descrizione completa del progetto
- [render.yaml](./render.yaml) — Configurazione automatica Render
- [.env.example](./.env.example) — Template variabili d'ambiente

