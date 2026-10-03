from unittest.mock import MagicMock, patch

import pytest

import api_client


def fausse_reponse(json_data, status=200):
    r = MagicMock(status_code=status, text=str(json_data))
    r.json.return_value = json_data
    return r


@pytest.fixture(autouse=True)
def cles(monkeypatch):
    for nom in ("HF_TOKEN", "GROQ_API_KEY", "GEMINI_API_KEY", "COHERE_API_KEY", "OCR_SPACE_KEY"):
        monkeypatch.setenv(nom, "cle-de-test")


def test_quota_depasse_donne_une_erreur_claire():
    with patch("api_client.requests.request", return_value=fausse_reponse({}, 429)):
        with pytest.raises(api_client.ApiError, match="429"):
            api_client.extraire_facture("x")


def test_ocr_puis_extraction():
    ocr = {"IsErroredOnProcessing": False, "ParsedResults": [{"ParsedText": "TOTAL 12,5 TND"}]}
    with patch("api_client.requests.request", return_value=fausse_reponse(ocr)):
        assert "TOTAL" in api_client.ocr(b"img", "f.jpg")
    # La date est maintenant obligatoire (validation du JSON)
    gem = {"candidates": [{"content": {"parts": [
        {"text": '{"fournisseur": "X", "date": "2026-09-12", "total": 12.5, "devise": "TND"}'}
    ]}}]}
    with patch("api_client.requests.request", return_value=fausse_reponse(gem)):
        assert api_client.extraire_facture("TOTAL 12,5 TND")["total"] == 12.5


# ---- Tests de la validation du JSON Gemini ----

def test_facture_valide():
    r = api_client.valider_facture(
        {"fournisseur": "X", "date": "2026-09-12", "total": "245.5", "devise": "TND"}
    )
    assert r["total"] == 245.5


def test_facture_sans_total():
    with pytest.raises(api_client.ApiError):
        api_client.valider_facture(
            {"fournisseur": "X", "date": "2026-09-12", "total": None, "devise": "TND"}
        )


def test_date_invalide():
    with pytest.raises(api_client.ApiError):
        api_client.valider_facture(
            {"fournisseur": "X", "date": "32/13/2026", "total": 10, "devise": "TND"}
        )


def test_json_invalide_de_gemini(monkeypatch):
    monkeypatch.setattr(api_client, "gemini", lambda prompt, json_attendu=False: "pas du json")
    with pytest.raises(api_client.ApiError):
        api_client.extraire_facture("texte quelconque")