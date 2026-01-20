# H&H Detailing – Booking Website (MVP)

Dit is een nette website waar klanten een afspraak kunnen plannen.
Zodra iemand boekt, is dat tijdslot direct gereserveerd (dubbel boeken kan niet).

## Snel starten (lokaal)
1) Installeer Python 3.10+  
2) In deze map:
   - `pip install -r requirements.txt`
   - `python app.py`
3) Open: `http://127.0.0.1:5000`

## Admin
- Admin pagina: `/admin`
- Zet je eigen wachtwoord via environment variable:
  - `ADMIN_PASSWORD` = jouw wachtwoord
  - `APP_SECRET` = lange random string

## Wat zit erin?
- Homepagina met pakketten + polijst services
- Afspraak plannen pagina met pakket-aanvinken + datum/tijd reserveren
- Admin pagina om reserveringen te bekijken en datums te blokkeren

## Upgrades die ik kan toevoegen
- Bevestigingsmail + WhatsApp notificatie
- Aanbetaling/betaallink (iDEAL)
- Meerdere medewerkers, duur per pakket, meer tijdsloten
- Google Calendar koppeling
