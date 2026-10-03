"""Client API de l'équipe 4 — ScanFacture (OCR.space + Gemini)."""

import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

TIMEOUT_S = 30


class ApiError(Exception):
    """L'API n'a pas pu répondre correctement (clé, réseau, quota, format)."""


def cle(nom):
    valeur = os.getenv(nom)
    if not valeur:
        raise ApiError(f"{nom} manquante : copiez .env.example en .env et ajoutez votre clé.")
    return valeur


def requete(methode, url, **kwargs):
    """Envoie la requête HTTP, vérifie le code de retour et renvoie la réponse."""
    try:
        reponse = requests.request(methode, url, timeout=TIMEOUT_S, **kwargs)
    except requests.RequestException as exc:
        raise ApiError(f"Réseau indisponible ou délai dépassé : {exc}") from exc
    if reponse.status_code == 401:
        raise ApiError("Clé API invalide ou absente (401).")
    if reponse.status_code == 429:
        raise ApiError("Quota gratuit dépassé (429) : attendez un peu ou utilisez le cache.")
    if reponse.status_code >= 400:
        raise ApiError(f"Erreur {reponse.status_code} : {reponse.text[:200]}")
    return reponse


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODELE = os.getenv("GEMINI_MODELE", "gemini-3.5-flash")


def gemini(prompt, json_attendu=False):
    """Envoie un prompt à Gemini et renvoie le texte généré."""
    corps = {"contents": [{"parts": [{"text": prompt}]}]}
    if json_attendu:
        corps["generationConfig"] = {"responseMimeType": "application/json"}
    data = requete(
        "POST", f"{GEMINI_URL}/{GEMINI_MODELE}:generateContent",
        headers={"x-goog-api-key": cle("GEMINI_API_KEY")}, json=corps,
    ).json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


OCR_URL = "https://api.ocr.space/parse/image"


def ocr(contenu, nom_fichier, langue="fre"):
    """Extrait le texte d'une image (jpg, png, pdf). « helloworld » = clé de démo très limitée."""
    data = requete(
        "POST", OCR_URL,
        data={"apikey": os.getenv("OCR_SPACE_KEY", "helloworld"), "language": langue},
        files={"file": (nom_fichier, contenu)},
    ).json()
    if data.get("IsErroredOnProcessing"):
        raise ApiError(f"OCR impossible : {data.get('ErrorMessage')}")
    return data["ParsedResults"][0]["ParsedText"]


def valider_facture(data):
    """Vérifie le JSON extrait : date AAAA-MM-JJ valide, total numérique."""
    if not isinstance(data, dict):
        raise ApiError("Réponse Gemini inattendue : un objet JSON est attendu.")

    # date au format AAAA-MM-JJ
    try:
        datetime.strptime(str(data.get("date")), "%Y-%m-%d")
    except ValueError as exc:
        raise ApiError(f"Date invalide : {data.get('date')!r}") from exc

    # total numérique
    total = data.get("total")
    if isinstance(total, bool) or total is None:
        raise ApiError(f"Total invalide : {total!r}")
    try:
        data["total"] = float(total)
    except (TypeError, ValueError) as exc:
        raise ApiError(f"Total invalide : {total!r}") from exc

    return data


def extraire_facture(texte_ocr):
    """Demande à Gemini un JSON {fournisseur, date, total, devise}, puis le valide."""
    prompt = (
        "Extrais de ce texte de facture un objet JSON avec les clés "
        "fournisseur, date (AAAA-MM-JJ), total (nombre), devise. "
        "Mets null si une information est absente.\n\n" + texte_ocr
    )
    brut = gemini(prompt, json_attendu=True)
    try:
        data = json.loads(brut)
    except json.JSONDecodeError as exc:
        raise ApiError(f"Gemini n'a pas renvoyé un JSON valide : {brut[:100]}") from exc
    return valider_facture(data)


if __name__ == "__main__":
    # Test rapide : python api_client.py
    texte = """STE ALPHA SARL
    Facture du 12/09/2026
    Total TTC : 245,500 TND"""
    print(extraire_facture(texte))