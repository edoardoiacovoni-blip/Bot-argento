# 🚀 Guida Rapida: Collegare Bot-argento a Render

## Risposta Rapida

**❌ NO** - Il repository GitHub NON è già su Render.  
**✅ DEVI** collegarlo tu manualmente.  
**📛 NOME**: Apparirà come **"bot-argento"** (o il nome che scegli tu).

## 📋 Checklist Veloce

- [ ] Hai un account Render? → [Registrati qui](https://render.com)
- [ ] Hai le API Key di Pionex? → [Ottienile qui](https://www.pionex.com/en-US/account/api-management)
- [ ] Hai accesso a questo repository GitHub? → Verifica di essere owner/collaborator

## 🎯 Procedura in 5 Passaggi

### Passaggio 1: Accedi a Render
```
1. Vai su https://dashboard.render.com/
2. Fai login o registrati
3. Autorizza Render ad accedere a GitHub quando richiesto
```

### Passaggio 2: Crea il Servizio
```
1. Clicca "New +" (in alto a destra)
2. Seleziona "Web Service"
3. Cerca "Bot-argento" nella lista dei repository
4. Clicca "Connect"
```

### Passaggio 3: Verifica la Configurazione
```
Render compilerà automaticamente questi campi grazie al file render.yaml:

✓ Name: bot-argento
✓ Environment: Python 3
✓ Build Command: pip install -r requirements.txt
✓ Start Command: python main.py
✓ Plan: Free (o scegli un piano a pagamento)
```

### Passaggio 4: Aggiungi le Credenziali (IMPORTANTE!)
```
Nella sezione "Environment Variables", aggiungi:

1. PIONEX_API_KEY = [la tua API key di Pionex]
2. PIONEX_SECRET_KEY = [il tuo Secret key di Pionex]

⚠️ SENZA queste variabili il bot NON funzionerà!
```

### Passaggio 5: Deploy
```
1. Clicca "Create Web Service"
2. Aspetta il build (1-2 minuti)
3. Controlla i log per vedere "FLYING WHEEL ENGINE: TAKEOFF"
4. ✅ Il bot è attivo!
```

## 🔍 Come Trovare il Servizio Dopo il Deploy

1. Vai su https://dashboard.render.com/
2. Vedrai il servizio "bot-argento" nella lista
3. Clicca sul nome per vedere:
   - **Logs**: Output in tempo reale del bot
   - **Environment**: Variabili d'ambiente
   - **Settings**: Configurazione del servizio
   - **Events**: Storia dei deploy

## 💡 URL del Servizio

Render assegnerà un URL pubblico tipo:
```
https://bot-argento.onrender.com
```

oppure:
```
https://bot-argento-xyz123.onrender.com
```

⚠️ **Nota**: Questo bot non ha una interfaccia web, quindi visitare l'URL mostrerà solo che il servizio è attivo.

## 🔄 Aggiornamenti Automatici

Una volta collegato:
- Ogni `git push` su GitHub → Render fa automaticamente il redeploy
- Non devi fare nulla manualmente
- Il bot si riavvia con il nuovo codice

## ⚡ Risoluzione Problemi Comuni

### Problema: "Repository not found"
**Soluzione**: Verifica di aver autorizzato Render ad accedere ai tuoi repository GitHub.

### Problema: "Build failed"
**Soluzione**: Controlla che `requirements.txt` sia presente nel repository.

### Problema: "Bot non si avvia"
**Soluzione**: Verifica che le variabili d'ambiente PIONEX_API_KEY e PIONEX_SECRET_KEY siano configurate.

### Problema: "Service keeps crashing"
**Soluzione**: Controlla i logs su Render. Probabilmente le API key sono errate o mancanti.

## 📞 Hai ancora dubbi?

- 📚 Leggi la documentazione completa nel [README.md](./README.md)
- 🔧 Controlla la configurazione in [render.yaml](./render.yaml)
- 💬 Apri una Issue su GitHub per supporto

## ✅ Checklist Post-Deploy

Dopo il deploy, verifica:
- [ ] Il servizio è "Running" nel Dashboard
- [ ] I logs mostrano "FLYING WHEEL ENGINE: TAKEOFF"
- [ ] I logs mostrano "✓ Pionex: API connection successful"
- [ ] Non ci sono errori nei logs

Se tutto è ✅, il bot è attivo e funzionante! 🎉
