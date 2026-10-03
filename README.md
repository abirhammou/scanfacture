# Équipe 4 — ScanFacture

Kit de démarrage de l'atelier **AI App Studio**.
API utilisée : **OCR.space + Gemini**. Les étapes pour obtenir la clé sont sur votre fiche d'équipe.

## Démarrer

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux / macOS : source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # Linux / macOS : cp .env.example .env
# ouvrez .env et collez votre clé
pytest                           # les tests utilisent des mocks : ils passent sans clé
streamlit run app.py
```

## Contenu

| Fichier | Rôle |
|---|---|
| `api_client.py` | Appels à l'API, déjà fonctionnels. À enrichir (cache, solution de secours...). |
| `app.py` | Interface Streamlit minimale. C'est ici que vous construisez votre application. |
| `test_api_client.py` | Exemples de tests avec mocks. À compléter. |
| `.env.example` | Modèle du fichier `.env`. **Ne versionnez jamais `.env`.** |

Si un modèle change de nom, modifiez-le dans `.env` sans toucher au code.
