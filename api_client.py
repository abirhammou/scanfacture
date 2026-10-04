import hashlib
import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv


load_dotenv()


class ApiError(Exception):
    """Erreur liée aux API OCR ou Gemini."""


OCR_URL = "https://api.ocr.space/parse/image"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"

cle = os.getenv("OCR_SPACE_KEY")
requete = os.getenv("GEMINI_API_KEY")


def gemini(prompt, json_attendu=False):
    """Envoie un prompt à Gemini et retourne le texte généré."""
    if not requete:
        raise ApiError("GEMINI_API_KEY manquante dans le fichier .env.")

    modele = os.getenv("GEMINI_MODELE", "gemini-3.5-flash")

    url = f"{GEMINI_URL}/{modele}:generateContent"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    if json_attendu:
        payload["generationConfig"] = {
            "responseMimeType": "application/json"
        }

    try:
        response = requests.post(
            url,
            params={"key": requete},
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except requests.RequestException as exc:
        raise ApiError(f"Erreur Gemini : {exc}") from exc
    except (KeyError, IndexError, TypeError) as exc:
        raise ApiError("Réponse Gemini inattendue.") from exc


def ocr(fichier):
    """
    Effectue l'OCR d'un fichier image ou PDF.

    Le fichier est vérifié, puis envoyé à OCR.space.
    """
    if not cle:
        raise ApiError("OCR_SPACE_KEY manquante dans le fichier .env.")

    if not os.path.exists(fichier):
        raise ApiError(f"Fichier introuvable : {fichier}")

    taille_max = 10 * 1024 * 1024

    if os.path.getsize(fichier) > taille_max:
        raise ApiError("Le fichier dépasse la taille maximale autorisée de 10 Mo.")

    extensions_autorisees = {
        ".png",
        ".jpg",
        ".jpeg",
        ".pdf",
        ".bmp",
        ".gif",
    }

    extension = os.path.splitext(fichier)[1].lower()

    if extension not in extensions_autorisees:
        raise ApiError(f"Extension non autorisée : {extension}")

    try:
        with open(fichier, "rb") as fichier_ouvert:
            contenu = fichier_ouvert.read()

        fichier_hash = hashlib.sha256(contenu).hexdigest()

        response = requests.post(
            OCR_URL,
            files={
                "file": (
                    os.path.basename(fichier),
                    contenu,
                )
            },
            data={
                "apikey": cle,
                "language": "fre",
                "isOverlayRequired": "false",
                "OCREngine": "2",
            },
            timeout=60,
        )

        response.raise_for_status()
        data = response.json()

        if data.get("IsErroredOnProcessing"):
            raise ApiError(
                f"OCR impossible : {data.get('ErrorMessage')}"
            )

        parsed_results = data.get("ParsedResults")

        if not parsed_results:
            raise ApiError("Aucun texte n'a été extrait par OCR.")

        texte = parsed_results[0].get("ParsedText", "")

        if not texte.strip():
            raise ApiError("Le texte extrait par OCR est vide.")

        return texte

    except requests.RequestException as exc:
        raise ApiError(f"Erreur OCR : {exc}") from exc
    except (ValueError, TypeError) as exc:
        raise ApiError("Réponse OCR invalide.") from exc


def valider_facture(data):
    """Vérifie le JSON extrait : date AAAA-MM-JJ valide, total numérique."""

    if not isinstance(data, dict):
        raise ApiError(
            "Réponse Gemini inattendue : un objet JSON est attendu."
        )

    try:
        datetime.strptime(
            str(data.get("date")),
            "%Y-%m-%d"
        )
    except ValueError as exc:
        raise ApiError(
            f"Date invalide : {data.get('date')!r}"
        ) from exc

    total = data.get("total")

    if isinstance(total, bool) or total is None:
        raise ApiError(
            f"Total invalide : {total!r}"
        )

    try:
        data["total"] = float(total)
    except (TypeError, ValueError) as exc:
        raise ApiError(
            f"Total invalide : {total!r}"
        ) from exc

    return data


def extraire_facture(texte_ocr):
    """
    Demande à Gemini un JSON
    {fournisseur, date, total, devise},
    puis le valide.
    """

    if not texte_ocr or not texte_ocr.strip():
        raise ApiError("Le texte OCR est vide.")

    prompt = f"""
Tu es un système d'extraction de données de factures.

À partir du texte OCR suivant, extrais exactement les informations suivantes :

- fournisseur
- date au format AAAA-MM-JJ
- total numérique
- devise

Retourne uniquement un objet JSON avec cette structure :

{{
    "fournisseur": "...",
    "date": "AAAA-MM-JJ",
    "total": 0,
    "devise": "..."
}}

Texte OCR :
{texte_ocr}
"""

    brut = gemini(
        prompt,
        json_attendu=True
    )

    try:
        data = json.loads(brut)
    except json.JSONDecodeError as exc:
        raise ApiError(
            f"Gemini n'a pas renvoyé un JSON valide : {brut[:100]}"
        ) from exc

    return valider_facture(data)