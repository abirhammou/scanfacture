"""Tests professionnels — API + Validation et tests (Pytest)."""

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


# ===========================================================================
# Helpers
# ===========================================================================

def fausse_reponse(json_data, status=200):
    """Crée une fausse réponse HTTP pour les tests."""
    r = MagicMock(status_code=status, text=str(json_data))
    r.json.return_value = json_data
    return r


FACTURE_VALIDE = {
    "fournisseur": "ACME Sarl",
    "date": "2024-03-15",
    "total": 150.0,
    "devise": "TND",
}


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture(autouse=True)
def cles(monkeypatch):
    """Injecte de fausses clés API pour tous les tests."""
    for nom in (
        "HF_TOKEN",
        "GROQ_API_KEY",
        "GEMINI_API_KEY",
        "COHERE_API_KEY",
        "OCR_SPACE_KEY",
    ):
        monkeypatch.setenv(nom, "cle-de-test")


@pytest.fixture(autouse=True)
def reset_doublons():
    """Repart d'un historique de doublons vide avant chaque test."""
    reinitialiser_doublons()
    yield
    reinitialiser_doublons()


# ===========================================================================
# Tests — Client API
# ===========================================================================

def test_quota_depasse_donne_une_erreur_claire():
    """Une erreur HTTP 429 doit produire une ApiError."""
    with patch(
        "api_client.requests.request",
        return_value=fausse_reponse({}, 429),
    ):
        with pytest.raises(api_client.ApiError, match="429"):
            api_client.extraire_facture("x")


def test_ocr_puis_extraction():
    """Teste successivement l'OCR puis l'extraction Gemini."""
    ocr = {
        "IsErroredOnProcessing": False,
        "ParsedResults": [
            {
                "ParsedText": "TOTAL 12,5 TND",
            }
        ],
    }

    with patch(
        "api_client.requests.request",
        return_value=fausse_reponse(ocr),
    ):
        assert "TOTAL" in api_client.ocr(b"img", "f.jpg")

    gem = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"total": 12.5, "devise": "TND"}',
                        }
                    ]
                }
            }
        ]
    }

    with patch(
        "api_client.requests.request",
        return_value=fausse_reponse(gem),
    ):
        result = api_client.extraire_facture("TOTAL 12,5 TND")
        assert result["total"] == 12.5


# ===========================================================================
# Tests — valider_json
# ===========================================================================

class TestValiderJson:

    def test_json_valide_retourne_le_dict(self):
        result = valider_json(FACTURE_VALIDE.copy())
        assert result["fournisseur"] == "ACME Sarl"
        assert result["total"] == 150.0

    def test_json_non_dict_leve_erreur(self):
        with pytest.raises(ErreurValidation, match="objet"):
            valider_json(["pas", "un", "dict"])

    def test_champ_manquant_leve_erreur(self):
        data = {
            k: v
            for k, v in FACTURE_VALIDE.items()
            if k != "total"
        }

        with pytest.raises(ErreurValidation, match="total"):
            valider_json(data)


# ===========================================================================
# Tests — valider_date
# ===========================================================================

class TestValiderDate:

    @pytest.mark.parametrize(
        "date_valide",
        [
            "2024-01-01",
            "2000-12-31",
            "2026-10-03",
        ],
    )
    def test_dates_valides(self, date_valide):
        assert valider_date(date_valide) == date_valide

    @pytest.mark.parametrize(
        "mauvaise_date",
        [
            "15/03/2024",
            "2024-3-5",
            "03-15-2024",
            "abcd-ef-gh",
            "2024-13-01",
            "2024-02-30",
        ],
    )
    def test_dates_invalides(self, mauvaise_date):
        with pytest.raises(ErreurValidation):
            valider_date(mauvaise_date)

    def test_date_none_leve_erreur(self):
        with pytest.raises(ErreurValidation, match="absente"):
            valider_date(None)


# ===========================================================================
# Tests — valider_total
# ===========================================================================

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

    def test_total_none_leve_erreur(self):
        with pytest.raises(ErreurValidation, match="absent"):
            valider_total(None)

    def test_total_non_numerique_leve_erreur(self):
        with pytest.raises(ErreurValidation, match="non numérique"):
            valider_total("abc")

    def test_total_negatif_leve_erreur(self):
        with pytest.raises(ErreurValidation, match="négatif"):
            valider_total(-5)


# ===========================================================================
# Tests — champs_manquants
# ===========================================================================

class TestChampsManquants:

    def test_aucun_champ_manquant(self):
        assert champs_manquants(FACTURE_VALIDE) == []

    def test_date_null(self):
        data = {
            **FACTURE_VALIDE,
            "date": None,
        }

        assert "date" in champs_manquants(data)

    def test_plusieurs_champs_null(self):
        data = {
            **FACTURE_VALIDE,
            "total": None,
            "devise": None,
        }

        manquants = champs_manquants(data)

        assert "total" in manquants
        assert "devise" in manquants


# ===========================================================================
# Tests — détection de doublons
# ===========================================================================

class TestDoublons:

    def test_premiere_facture_pas_doublon(self):
        assert est_doublon(FACTURE_VALIDE) is False

    def test_meme_facture_deux_fois_est_doublon(self):
        est_doublon(FACTURE_VALIDE)
        assert est_doublon(FACTURE_VALIDE) is True

    def test_fournisseur_different_pas_doublon(self):
        est_doublon(FACTURE_VALIDE)

        autre = {
            **FACTURE_VALIDE,
            "fournisseur": "Autre Fournisseur",
        }

        assert est_doublon(autre) is False

    def test_total_different_pas_doublon(self):
        est_doublon(FACTURE_VALIDE)

        autre = {
            **FACTURE_VALIDE,
            "total": 999.0,
        }

        assert est_doublon(autre) is False

    def test_casse_fournisseur_ignoree(self):
        """ACME SARL et acme sarl doivent être considérés identiques."""
        est_doublon(FACTURE_VALIDE)

        variante = {
            **FACTURE_VALIDE,
            "fournisseur": "ACME SARL",
        }

        assert est_doublon(variante) is True

    def test_reinitialiser_efface_historique(self):
        est_doublon(FACTURE_VALIDE)
        reinitialiser_doublons()

        assert est_doublon(FACTURE_VALIDE) is False