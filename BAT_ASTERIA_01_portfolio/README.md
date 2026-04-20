# BAT_ASTERIA_01 Portfolio

Base de projet GTB/GTC portfolio pour vitrine publique + démo live.

## Architecture
- `apps/public-docs` : site public statique pour présenter le projet
- `apps/demo-web` : interface web live de démonstration
- `apps/demo-api` : API FastAPI avec données simulées, WebSocket et scénarios
- `infra/` : exemples de configuration d'hébergement et de proxy
- `data/seed.json` : données initiales du bâtiment

## Lancer en local
```bash
cd apps/demo-api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Puis ouvrir :
- Démo : http://localhost:8000/demo
- Public : http://localhost:8000/

## Hébergement conseillé
- Documentation publique : GitHub Pages
- Démo live : Render, ou VPS Docker avec Traefik
- Base de données / historique : PostgreSQL + TimescaleDB si tu veux industrialiser
