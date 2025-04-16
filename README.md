# Videó Elemző Webapp - Vercel Deployment

Ez az alkalmazás videók elemzésére és az eredmények vizuális megjelenítésére szolgál. Az API segítségével a feltöltött videók részletes elemzését készíti el, amely tartalmazza a pszichometria, vizuális és hang stimuláció, valamint a public speech szempontok értékelését.

## Vercel-re történő telepítés

Az alkalmazás Vercel-re történő telepítéséhez kövesd az alábbi lépéseket:

1. Telepítsd a Vercel CLI-t:

```bash
npm i -g vercel
```

2. Jelentkezz be a Vercel fiókodba:

```bash
vercel login
```

3. Navigálj a projekt könyvtárába és futtasd:

```bash
vercel
```

4. Kövesd a telepítési utasításokat.

## Környezeti változók

A következő környezeti változókat állíthatod be a Vercel felületén:

- `GEMINI_API_KEY`: A Google Gemini API kulcs (alapértelmezett érték már be van állítva)
- `SECRET_KEY`: A Flask alkalmazás titkos kulcsa a session kezeléshez
- `APP_USERNAME`: Bejelentkezési felhasználónév (alapértelmezett: "tris")
- `APP_PASSWORD`: Bejelentkezési jelszó (alapértelmezett: "tris123")

## Projekt struktúra

```
/
├── app.py                 # Flask alkalmazás fő fájl
├── requirements.txt       # Python függőségek
├── runtime.txt            # Python verzió (3.9)
├── vercel.json            # Vercel konfigurációs fájl
├── static/                # Statikus fájlok
│   ├── css/               # CSS fájlok
│   │   └── style.css      # Fő stíluslap
│   └── uploads/           # Feltöltött fájlok és elemzési eredmények
├── templates/             # HTML sablonok
│   ├── index.html         # Főoldal
│   ├── login.html         # Bejelentkezési oldal
│   ├── upload.html        # Videó feltöltési oldal
│   ├── dashboard.html     # Elemzési eredmények dashboard
│   └── error.html         # Hibaoldal
└── utils/                 # Segédfunkciók
    └── analyzer.py        # Videó elemző modul
```

## Funkciók

- Videófájlok feltöltése és elemzése
- A Gemini API használata a videóelemzéshez
- Részletes dashboard az elemzés eredményeinek vizualizálására
- Időintervallumokra bontott elemzés
- Diagramok és metrikák megjelenítése
- Fejlesztési javaslatok

## Technológiák

- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- Videóelemzés: Google Gemini API
- Vizualizáció: Chart.js
- Telepítés: Vercel
