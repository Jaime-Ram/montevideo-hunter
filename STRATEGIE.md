# Montevideo Website Hunter — Strategie

## 1. De kans

Uruguay heeft ~90% internetpenetration maar veel kleine bedrijven opereren alleen via
Instagram/Facebook. Dit is vooral zichtbaar in:
- Kapsalons, schoonheidssalons, nagelstudio's
- Restaurants en cafés
- Boetieks en kledingwinkels
- Thuiszorg, poetsbedrijven, klussers
- Kleine supermarkten (almacenes)

Google Maps toont hen wél, maar zonder website missen ze directe klanten en SEO.

---

## 2. Welke wijken — volgorde van prioriteit

| Prio | Wijk | Waarom |
|------|------|--------|
| 1 | **Pocitos** | Meest welvarend, businesses willen professioneel ogen |
| 2 | **Punta Carretas** | Veel zelfstandigen, hoge bereidheid te betalen |
| 3 | **Palermo** | Hipster-winkels, cafés, indie-bedrijven, trendy clientèle |
| 4 | **Parque Rodó** | Mix van studenten en gezinnen, veel kleinschalige horeca |
| 5 | **Cordón** | Residentieel + lokale winkels, minder concurrentie van andere webdesigners |
| 6 | **Centro** | Druk maar prijs-gevoelig, meer doorloop = meer gesprekken |

Loop op doordeweekse ochtenden (9:00–12:30). Eigenaren zijn dan aanwezig,
en de winkel is niet te druk.

---

## 3. Moet je van tevoren een website maken? JA

Maak **3 demo-sites** in verschillende niches vóór je begint. Gebruik Carrd.co of
een simpele Vercel-site.

### Demo-ideeën
- **Kapsalon-demo**: foto's, openingstijden, WhatsApp-button, Google Maps embed
- **Restaurant-demo**: menu, reserveringslink, Instagram-feed, foto's
- **Winkel-demo**: productgalerij, adres, openingstijden, "neem contact op"

### Waarom demos werken
1. Je laat het letterlijk zien op je telefoon — geen abstractie nodig
2. Ze herkennen hun eigen niche direct
3. Je sluit dezelfde dag af ("vandaag nog online") in plaats van na een week

---

## 4. Pricing in Uruguay

### Valuta
- 1 USD ≈ 40–42 UYU (controleer de koers op de dag zelf)
- Zeg altijd prijzen in **USD** (stabiel, professioneel imago) maar accepteer UYU

### Prijsranges

| Product | Prijs USD | Prijs UYU |
|---------|-----------|-----------|
| Eenmalige landingspagina (1 pagina) | $150–250 | 6.000–10.000 |
| Kleine zakelijke site (4–5 pagina's) | $350–600 | 14.000–25.000 |
| E-commerce (webshop) | $600–1.200 | 25.000–50.000 |
| Maandelijks onderhoud + hosting | $25–40/m | 1.000–1.600/m |
| WhatsApp Business + Google Profiel setup | $50 | 2.000 |

**Slimme bundel om mee te openen:**
> "Por $350 dólares te hago el sitio completo, te lo muestro funcionando esta misma semana,
> y el primer año de hosting va incluido."

### Aanbetaling
Vraag altijd **50% vooraf**, 50% bij oplevering. Geen 100% achteraf — te veel no-shows.

### Betaalmethodes Uruguay
- **Transferencia bancaria** (BROU, Santander, Itaú) — meest vertrouwd
- **Mercado Pago** — werkt als PayPal, hebben velen
- **Contado** (contant) — nog steeds gangbaar voor kleinere bedragen
- **PayPal/Wise** — als ze online-savvy zijn

---

## 5. Wat je ter plekke zegt

### Openingszin (Spaans)
> "Hola, vi que tienen su negocio en Google Maps pero no tienen página web propia.
>  Les hago una en una semana, por un precio fijo. ¿Le puedo mostrar un ejemplo?"

### Als ze zeggen "tenemos Instagram"
> "Instagram es genial, pero en Google la gente busca directamente. Sin web,
>  no aparecen en los resultados de búsqueda cuando alguien busca '[su rubro] en Pocitos'."

### Bezwaar: "es muy caro"
> "La landingpage básica son 200 dólares — una sola venta nueva ya la paga.
>  ¿Cuántos clientes nuevos por mes busca?"

### Sluit af met WhatsApp
> "¿Me da su WhatsApp? Le mando hoy la demo personalizada con el nombre de su negocio."

Stuur dezelfde avond een bericht met een link naar de demo. Conversie is veel hoger
als je follow-up dezelfde dag doet.

---

## 6. Tech-stack voor de sites die je verkoopt

### Snel en goedkoop
- **Carrd.co** — $19/jaar per site, supersnelle one-pagers, mobielvriendelijk
- **Framer** — mooier, $12–15/m per site
- **Webflow** — professioneler, $14/m per site

### Eigen hosting (hogere marge)
- **Vercel** — gratis voor statische sites
- **Netlify** — gratis tier
- Gebruik een eenvoudig template (Astro, Next.js, of plain HTML)

### Domein
- **.com.uy** domein: ~$15–20/jaar via NIC Uruguay (nic.org.uy)
- **.uy** domein: iets duurder maar korter
- Versluit je die kosten door ze mee te facturen

---

## 7. Hoe de scraper te gebruiken

```bash
# 1. Installeer
cd ~/montevideo-hunter
pip install -r requirements.txt

# 2. Haal Google Places API-key op
#    → console.cloud.google.com
#    → Nieuw project → Places API inschakelen → Credentials → API key
#    → Nieuwe accounts krijgen $300 gratis credit

# 3. Stel key in
export GOOGLE_PLACES_API_KEY="AIzaSy..."

# 4. Start (alle wijken)
python scraper.py

# 5. Of alleen specifieke wijken
python scraper.py --wijken pocitos punta_carretas ciudad_vieja

# 6. Herstart na onderbreking (gaat verder waar gebleven)
python scraper.py

# 7. Alleen kaart opnieuw genereren
python scraper.py --kaart-only
```

### Output
- `prospects.csv` — Excel-compatible lijst met naam, adres, telefoon, Maps-link
- `kaart_prospects.html` — Interactieve kaart, open in browser
- `checkpoint.json` — Wordt automatisch bewaard, script hervat na onderbreking

---

## 8. Google Places API-kosten schatten

| Actie | Kosten per call |
|-------|----------------|
| Nearby Search | $0.032 |
| Place Details (basic+contact) | $0.020 |

Nieuwe Google Cloud accounts krijgen **$300 gratis krediet** — genoeg voor de hele stad.

Alleen de wijken Ciudad Vieja + Pocitos + Punta Carretas kost ~$8–15 totaal.

---

## 9. Alternatief: geen code, kant-en-klare dienst

Als je de API niet wil opzetten:
- **Outscraper.com** — $25 voor 5.000 bedrijven inclusief website-filter
- **Apify Google Maps Scraper** — $5–10 voor een run
- **PhantomBuster** — heeft ook een Maps-extractor

Upload de output (CSV) in Google Maps → "Mijn kaarten" → eigen laag aanmaken.

---

## 10. Dagplanning voor de straat

| Tijdstip | Activiteit |
|----------|------------|
| Avond ervoor | Scraper draaien, kaart openen, route plannen |
| 9:00 | Start in wijk #1 (bv. Pocitos) |
| 9:00–12:30 | ~15–20 gesprekken, WhatsApp-nummers verzamelen |
| 12:30–14:00 | Lunch, follow-up berichten sturen met demo-link |
| 14:00–17:00 | Wijk #2 (bv. Ciudad Vieja) |
| Avond | Offertes opstellen, demos personaliseren |

Realistisch: **2–4 betalende klanten per dag** bij een goede pitch en goede locatie.
Bij $250 gemiddeld = $500–1.000/dag bruto bij consistent werken.
