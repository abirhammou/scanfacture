"""Module de validation des données extraites par Gemini."""

import re
from datetime import datetime

CHAMPS_REQUIS = {"fournisseur", "date", "total", "devise"}
_factures_vues: set[tuple] = set()


class ErreurValidation(Exception):
    """Données de facture invalides ou incomplètes."""


def valider_json(data: dict) -> dict:
    """Valide le dictionnaire renvoyé par extraire_facture()."""
    if not isinstance(data, dict):
        raise ErreurValidation("Le JSON reçu n'est pas un objet.")
    champs_manquants_liste = [c for c in CHAMPS_REQUIS if c not in data]
    if champs_manquants_liste:
        raise ErreurValidation(f"Champs manquants : {', '.join(champs_manquants_liste)}")
    data["date"] = valider_date(data["date"])
    data["total"] = valider_total(data["total"])
    return data


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def valider_date(valeur) -> str:
    if valeur is None:
        raise ErreurValidation("La date est absente (null).")
    if not DATE_RE.match(str(valeur)):
        raise ErreurValidation(f"Format de date invalide : '{valeur}' (attendu AAAA-MM-JJ).")
    try:
        datetime.strptime(valeur, "%Y-%m-%d")
    except ValueError as exc:
        raise ErreurValidation(f"Date impossible : {valeur}") from exc
    return valeur


def valider_total(valeur) -> float:
    if valeur is None:
        raise ErreurValidation("Le total est absent (null).")
    try:
        total = float(str(valeur).replace(",", "."))
    except ValueError as exc:
        raise ErreurValidation(f"Total non numérique : '{valeur}'.") from exc
    if total < 0:
        raise ErreurValidation(f"Total négatif suspect : {total}.")
    return total


def champs_manquants(data: dict) -> list[str]:
    return [c for c in CHAMPS_REQUIS if data.get(c) is None]


def est_doublon(data: dict) -> bool:
    cle = (
        str(data.get("fournisseur", "")).strip().lower(),
        str(data.get("date", "")),
        float(data.get("total") or 0),
    )
    if cle in _factures_vues:
        return True
    _factures_vues.add(cle)
    return False


def reinitialiser_doublons():
    _factures_vues.clear()
