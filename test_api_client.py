"""Tests — api_client + validation (Pytest)."""

from unittest.mock import MagicMock, patch

import pytest

import api_client
from validation import (
    ErreurValidation,
    champs_manquants,
    est_doublon,
    reinitialiser_doublons,
    valider_date,
    valider_json,
    valider_total,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def fausse_reponse(json_data, status=200):
    r = MagicMock(status_code=status, text=str(json_data))
    r.json.return_value = json_data
    return r


FACTURE_VALIDE = {
    "fournisseur": "ACME Sarl",
    "date": "2024-03-15",
    "total": 150.0,
    "devise": "TND",
}

OCR_OK = {"IsErroredOnProcessing": False, "ParsedResults": [{"ParsedText": "TOTAL 12,5 TND"}]}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def cles(monkeypatch):
    for nom in ("GEMINI_API_KEY", "OCR_SPACE_KEY"):
        monkeypatch.setenv(nom, "cle-de-test")


@pytest.fixture(autouse=True)
def vider_cache_ocr():
    api_client._cache_ocr.clear()
    yield
    api_client._cache_ocr.clear()


@pytest.fixture(autouse=True)
def reset_doublons():
    reinitialiser_doublons()
    yield
    reinitialiser_doublons()


# ── Tests api_client ─────────────────────────────────────────────────────────

def test_quota_depasse_donne_une_erreur_claire():
    with patch("api_client.requests.request", return_value=fausse_reponse({}, 429)):
        with pytest.raises(api_client.ApiError, match="429"):
            api_client.extraire_facture("x")


def test_ocr_puis_extraction():
    with patch("api_client.requests.request", return_value=fausse_reponse(OCR_OK)):
        assert "TOTAL" in api_client.ocr(b"img", "f.jpg")
    gem = {"candidates": [{"content": {"parts": [
        {"text": '{"fournisseur": "X", "date": "2026-09-12", "total": 12.5, "devise": "TND"}'}
    ]}}]}
    with patch("api_client.requests.request", return_value=fausse_reponse(gem)):
        assert api_client.extraire_facture("TOTAL 12,5 TND")["total"] == 12.5


def test_ocr_fichier_trop_lourd():
    with pytest.raises(api_client.ApiError, match="1 Mo"):
        api_client.ocr(b"x" * (1024 * 1024 + 1), "f.jpg")


def test_ocr_fichier_vide():
    with pytest.raises(api_client.ApiError, match="vide"):
        api_client.ocr(b"", "f.jpg")


def test_ocr_format_non_supporte():
    with pytest.raises(api_client.ApiError, match="Format"):
        api_client.ocr(b"img", "f.gif")


def test_ocr_erreur_du_service():
    rep = {"IsErroredOnProcessing": True, "ErrorMessage": ["Fichier illisible"]}
    with patch("api_client.requests.request", return_value=fausse_reponse(rep)):
        with pytest.raises(api_client.ApiError, match="OCR impossible"):
            api_client.ocr(b"img", "f.jpg")


def test_ocr_aucun_texte():
    rep = {"IsErroredOnProcessing": False, "ParsedResults": [{"ParsedText": "  "}]}
    with patch("api_client.requests.request", return_value=fausse_reponse(rep)):
        with pytest.raises(api_client.ApiError, match="Aucun texte"):
            api_client.ocr(b"img", "f.jpg")


def test_ocr_cache_evite_un_second_appel():
    with patch("api_client.requests.request", return_value=fausse_reponse(OCR_OK)) as mock:
        api_client.ocr(b"img", "f.jpg")
        api_client.ocr(b"img", "f.jpg")
        assert mock.call_count == 1


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


# ── Tests validation ─────────────────────────────────────────────────────────

class TestValiderJson:
    def test_json_valide(self):
        r = valider_json(FACTURE_VALIDE.copy())
        assert r["total"] == 150.0

    def test_json_non_dict(self):
        with pytest.raises(ErreurValidation, match="objet"):
            valider_json(["pas", "un", "dict"])

    def test_champ_manquant(self):
        data = {k: v for k, v in FACTURE_VALIDE.items() if k != "total"}
        with pytest.raises(ErreurValidation, match="total"):
            valider_json(data)


class TestValiderDate:
    @pytest.mark.parametrize("d", ["2024-01-01", "2000-12-31", "2026-10-03"])
    def test_dates_valides(self, d):
        assert valider_date(d) == d

    @pytest.mark.parametrize("d", ["15/03/2024", "2024-3-5", "abcd-ef-gh", "2024-13-01", "2024-02-30"])
    def test_dates_invalides(self, d):
        with pytest.raises(ErreurValidation):
            valider_date(d)

    def test_date_none(self):
        with pytest.raises(ErreurValidation, match="absente"):
            valider_date(None)


class TestValiderTotal:
    @pytest.mark.parametrize("v,a", [(150.0, 150.0), ("99,99", 99.99), ("0", 0.0), (1, 1.0)])
    def test_totaux_valides(self, v, a):
        assert valider_total(v) == a

    def test_total_none(self):
        with pytest.raises(ErreurValidation, match="absent"):
            valider_total(None)

    def test_total_non_numerique(self):
        with pytest.raises(ErreurValidation, match="non numérique"):
            valider_total("abc")

    def test_total_negatif(self):
        with pytest.raises(ErreurValidation, match="négatif"):
            valider_total(-5)


class TestDoublons:
    def test_premiere_facture_pas_doublon(self):
        assert est_doublon(FACTURE_VALIDE) is False

    def test_meme_facture_deux_fois(self):
        est_doublon(FACTURE_VALIDE)
        assert est_doublon(FACTURE_VALIDE) is True

    def test_fournisseur_different_pas_doublon(self):
        est_doublon(FACTURE_VALIDE)
        assert est_doublon({**FACTURE_VALIDE, "fournisseur": "Autre"}) is False

    def test_reinitialiser(self):
        est_doublon(FACTURE_VALIDE)
        reinitialiser_doublons()
        assert est_doublon(FACTURE_VALIDE) is False
