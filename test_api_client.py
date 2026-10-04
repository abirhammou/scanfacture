"""Tests — api_client + validation (Pytest)."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import api_client
from validation import (
    ErreurValidation,
    est_doublon,
    reinitialiser_doublons,
    valider_date,
    valider_json,
    valider_total,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def fausse_reponse(json_data, status=200):
    response = MagicMock(status_code=status, text=str(json_data))
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


FACTURE_VALIDE = {
    "fournisseur": "ACME Sarl",
    "date": "2024-03-15",
    "total": 150.0,
    "devise": "TND",
}

OCR_OK = {
    "IsErroredOnProcessing": False,
    "ParsedResults": [
        {
            "ParsedText": "TOTAL 12,5 TND"
        }
    ],
}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def cles(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "cle-de-test")
    monkeypatch.setenv("OCR_SPACE_KEY", "cle-de-test")


@pytest.fixture(autouse=True)
def reset_doublons():
    reinitialiser_doublons()
    yield
    reinitialiser_doublons()


# ── Tests Gemini ──────────────────────────────────────────────────────────────

def test_quota_depasse_donne_une_erreur_claire():
    with (
        patch(
            "api_client.requests.post",
            return_value=fausse_reponse({}, 429),
        ),
        pytest.raises(api_client.ApiError, match="429"),
    ):
        api_client.gemini("test")


def test_extraction_facture():
    gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                '{"fournisseur": "X", '
                                '"date": "2026-09-12", '
                                '"total": 12.5, '
                                '"devise": "TND"}'
                            )
                        }
                    ]
                }
            }
        ]
    }

    with patch(
        "api_client.requests.post",
        return_value=fausse_reponse(gemini_response),
    ):
        resultat = api_client.extraire_facture(
            "TOTAL 12,5 TND"
        )

    assert resultat["total"] == 12.5
    assert resultat["date"] == "2026-09-12"


def test_json_invalide_de_gemini(monkeypatch):
    monkeypatch.setattr(
        api_client,
        "gemini",
        lambda prompt, json_attendu=False: "pas du json",
    )

    with pytest.raises(api_client.ApiError):
        api_client.extraire_facture("texte quelconque")


# ── Tests OCR ─────────────────────────────────────────────────────────────────

def creer_fichier_temporaire(contenu=b"image"):
    fichier = tempfile.NamedTemporaryFile(
        suffix=".jpg",
        delete=False,
    )
    fichier.write(contenu)
    fichier.close()
    return fichier.name


def test_ocr_fichier():
    chemin = creer_fichier_temporaire()

    try:
        with patch(
            "api_client.requests.post",
            return_value=fausse_reponse(OCR_OK),
        ):
            resultat = api_client.ocr(chemin)

        assert "TOTAL" in resultat

    finally:
        Path(chemin).unlink(missing_ok=True)


def test_ocr_fichier_trop_lourd():
    chemin = creer_fichier_temporaire(b"x" * 100)

    try:
        with patch("api_client.os.path.getsize", return_value=11 * 1024 * 1024):
            with pytest.raises(
                api_client.ApiError,
                match="10 Mo",
            ):
                api_client.ocr(chemin)
    finally:
        Path(chemin).unlink(missing_ok=True)


def test_ocr_fichier_inexistant():
    with pytest.raises(
        api_client.ApiError,
        match="introuvable",
    ):
        api_client.ocr("fichier_inexistant.jpg")


def test_ocr_format_non_supporte():
    chemin = tempfile.NamedTemporaryFile(
        suffix=".txt",
        delete=False,
    )

    chemin.write(b"test")
    chemin.close()

    try:
        with pytest.raises(
            api_client.ApiError,
            match="Extension non autorisée",
        ):
            api_client.ocr(chemin.name)
    finally:
        Path(chemin.name).unlink(missing_ok=True)


def test_ocr_erreur_du_service():
    chemin = creer_fichier_temporaire()

    try:
        reponse = {
            "IsErroredOnProcessing": True,
            "ErrorMessage": ["Fichier illisible"],
        }

        with patch(
            "api_client.requests.post",
            return_value=fausse_reponse(reponse),
        ):
            with pytest.raises(
                api_client.ApiError,
                match="OCR impossible",
            ):
                api_client.ocr(chemin)

    finally:
        Path(chemin).unlink(missing_ok=True)


def test_ocr_aucun_texte():
    chemin = creer_fichier_temporaire()

    try:
        reponse = {
            "IsErroredOnProcessing": False,
            "ParsedResults": [
                {
                    "ParsedText": "   "
                }
            ],
        }

        with patch(
            "api_client.requests.post",
            return_value=fausse_reponse(reponse),
        ):
            with pytest.raises(
                api_client.ApiError,
                match="vide",
            ):
                api_client.ocr(chemin)

    finally:
        Path(chemin).unlink(missing_ok=True)


# ── Tests validation.py ──────────────────────────────────────────────────────

class TestValiderJson:

    def test_json_valide(self):
        resultat = valider_json(
            FACTURE_VALIDE.copy()
        )

        assert resultat["total"] == 150.0

    def test_json_non_dict(self):
        with pytest.raises(
            ErreurValidation,
            match="objet",
        ):
            valider_json(
                ["pas", "un", "dict"]
            )

    def test_champ_manquant(self):
        data = {
            key: value
            for key, value in FACTURE_VALIDE.items()
            if key != "total"
        }

        with pytest.raises(
            ErreurValidation,
            match="total",
        ):
            valider_json(data)


class TestValiderDate:

    @pytest.mark.parametrize(
        "date",
        [
            "2024-01-01",
            "2000-12-31",
            "2026-10-03",
        ],
    )
    def test_dates_valides(self, date):
        assert valider_date(date) == date

    @pytest.mark.parametrize(
        "date",
        [
            "15/03/2024",
            "2024-3-5",
            "abcd-ef-gh",
            "2024-13-01",
            "2024-02-30",
        ],
    )
    def test_dates_invalides(self, date):
        with pytest.raises(ErreurValidation):
            valider_date(date)

    def test_date_none(self):
        with pytest.raises(
            ErreurValidation,
            match="absente",
        ):
            valider_date(None)


class TestValiderTotal:

    @pytest.mark.parametrize(
        "valeur, attendu",
        [
            (150.0, 150.0),
            ("99,99", 99.99),
            ("0", 0.0),
            (1, 1.0),
        ],
    )
    def test_totaux_valides(self, valeur, attendu):
        assert valider_total(valeur) == attendu

    def test_total_none(self):
        with pytest.raises(
            ErreurValidation,
            match="absent",
        ):
            valider_total(None)

    def test_total_non_numerique(self):
        with pytest.raises(
            ErreurValidation,
            match="non numérique",
        ):
            valider_total("abc")

    def test_total_negatif(self):
        with pytest.raises(
            ErreurValidation,
            match="négatif",
        ):
            valider_total(-5)


class TestDoublons:

    def test_premiere_facture_pas_doublon(self):
        assert est_doublon(
            FACTURE_VALIDE
        ) is False

    def test_meme_facture_deux_fois(self):
        est_doublon(FACTURE_VALIDE)

        assert est_doublon(
            FACTURE_VALIDE
        ) is True

    def test_fournisseur_different_pas_doublon(self):
        est_doublon(FACTURE_VALIDE)

        autre_facture = {
            **FACTURE_VALIDE,
            "fournisseur": "Autre",
        }

        assert est_doublon(
            autre_facture
        ) is False

    def test_reinitialiser(self):
        est_doublon(FACTURE_VALIDE)

        reinitialiser_doublons()

        assert est_doublon(
            FACTURE_VALIDE
        ) is False