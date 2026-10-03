"""Client API de l'équipe 4 — ScanFacture (OCR.space + Gemini)."""

import hashlib
import json
import os

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
TAILLE_MAX_OCR = 1024 * 1024  # 1 Mo : limite de l'offre gratuite OCR.space
EXTENSIONS_OCR = {".jpg", ".jpeg", ".png", ".pdf"}
_cache_ocr = {}


def ocr(contenu, nom_fichier, langue="fre"):
    """Extrait le texte d'une image (jpg, png, pdf). « helloworld » = clé de démo très limitée."""
    if not contenu:
        raise ApiError("Fichier vide.")
    if len(contenu) > TAILLE_MAX_OCR:
        taille = len(contenu) / (1024 * 1024)
        raise ApiError(f"Fichier trop lourd ({taille:.1f} Mo) : maximum 1 Mo avec OCR.space gratuit.")
    if os.path.splitext(nom_fichier)[1].lower() not in EXTENSIONS_OCR:
        raise ApiError("Format non supporté : utilisez jpg, png ou pdf.")

    empreinte = hashlib.sha256(contenu).hexdigest() + langue
    if empreinte in _cache_ocr:
        return _cache_ocr[empreinte]

    data = requete(
        "POST", OCR_URL,
        data={"apikey": os.getenv("OCR_SPACE_KEY", "helloworld"), "language": langue},
        files={"file": (nom_fichier, contenu)},
    ).json()
    if data.get("IsErroredOnProcessing"):
        message = data.get("ErrorMessage")
        if isinstance(message, list):
            message = " ".join(message)
        raise ApiError(f"OCR impossible : {message}")

    resultats = data.get("ParsedResults") or []
    texte = "\n".join(r.get("ParsedText", "") for r in resultats).strip()
    if not texte:
        raise ApiError("Aucun texte détecté : essayez une photo plus nette et mieux éclairée.")

    _cache_ocr[empreinte] = texte
    return texte

def extraire_facture(texte_ocr):
    """Demande à Gemini un JSON {fournisseur, date, total, devise}."""
    prompt = (
        "Extrais de ce texte de facture un objet JSON avec les clés "
        "fournisseur, date (AAAA-MM-JJ), total (nombre), devise. "
        "Mets null si une information est absente.\n\n" + texte_ocr
    )
    return json.loads(gemini(prompt, json_attendu=True))