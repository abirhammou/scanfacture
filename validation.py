"""Personne 3 – Validation et tests : fiabilité des données extraites par Gemini."""

import re
from datetime import datetime

# Champs attendus dans le JSON Gemini
CHAMPS_REQUIS = {"fournisseur", "date", "total", "devise"}

# Historique des factures traitées en session (détection doublons)
_factures_vues: set[tuple] = set()


class ErreurValidation(Exception):
    """Données de facture invalides ou incomplètes."""


# ---------------------------------------------------------------------------
# 1. Validation du JSON Gemini
# ---------------------------------------------------------------------------

def valider_json(data: dict) -> dict:
    """
    Valide le dictionnaire renvoyé par extraire_facture().
    Retourne le dict nettoyé ou lève ErreurValidation.
    """
    if not isinstance(data, dict):
        raise ErreurValidation("Le JSON reçu n'est pas un objet.")

    champs_manquants = [c for c in CHAMPS_REQUIS if c not in data]
    if champs_manquants:
        raise ErreurValidation(f"Champs manquants : {', '.join(champs_manquants)}")

    data["date"] = valider_date(data["date"])
    data["total"] = valider_total(data["total"])

    return data


# ---------------------------------------------------------------------------
# 2. Validation du format de date
# ---------------------------------------------------------------------------

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def valider_date(valeur) -> str:
    """Accepte 'AAAA-MM-JJ'. Lève ErreurValidation sinon."""
    if valeur is None:
        raise ErreurValidation("La date est absente (null).")
    if not DATE_RE.match(str(valeur)):
        raise ErreurValidation(
            f"Format de date invalide : '{valeur}' (attendu AAAA-MM-JJ)."
        )
    try:
        datetime.strptime(valeur, "%Y-%m-%d")
    except ValueError as exc:
        raise ErreurValidation(f"Date impossible : {valeur}") from exc
    return valeur


# ---------------------------------------------------------------------------
# 3. Validation que le total est numérique
# ---------------------------------------------------------------------------

def valider_total(valeur) -> float:
    """Accepte un int/float ou une chaîne convertible. Lève ErreurValidation sinon."""
    if valeur is None:
        raise ErreurValidation("Le total est absent (null).")
    try:
        total = float(str(valeur).replace(",", "."))
    except ValueError as exc:
        raise ErreurValidation(f"Total non numérique : '{valeur}'.") from exc
    if total < 0:
        raise ErreurValidation(f"Total négatif suspect : {total}.")
    return total


# ---------------------------------------------------------------------------
# 4. Gestion des champs manquants (avertissement non bloquant)
# ---------------------------------------------------------------------------

def champs_manquants(data: dict) -> list[str]:
    """Retourne la liste des champs REQUIS dont la valeur est None ou absente."""
    return [c for c in CHAMPS_REQUIS if data.get(c) is None]


# ---------------------------------------------------------------------------
# 5. Détection des doublons
# ---------------------------------------------------------------------------

def est_doublon(data: dict) -> bool:
    """
    Retourne True si une facture identique (fournisseur + date + total) a déjà
    été vue dans cette session.  Enregistre la facture sinon.
    """
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
    """Vide l'historique (utile entre deux sessions ou dans les tests)."""
    _factures_vues.clear()
