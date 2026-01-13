import requests
from requests.auth import HTTPBasicAuth
from typing import Any, Dict, List, Optional


# -----------------------------
# Config
# -----------------------------
BASE_URL = "https://confluence.example.com"  # no trailing slash

PAGE_ID = 744202791
FORM_NAME = "InterviewTracking"

USERNAME = "your.username"
PASSWORD = "your.password"

# Only these fields will be translated (IDs -> labels).
# Add any other radio/dropdown fields you want to map.
FIELDS_TO_TRANSLATE = [
    "OfferStatus",
    "Status",
    "InterviewStatus",
    "ProposedLevel",
    # "Shift",   # if Shift is stored as an ID with a values map; otherwise leave it out
]


# -----------------------------
# REST calls
# -----------------------------
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    s.auth = HTTPBasicAuth(USERNAME, PASSWORD)
    return s


def cf_search(session: requests.Session, page_id: int, form_name: str) -> Dict[str, Any]:
    """
    GET /rest/confiforms/1.0/search/{pageId}/{formName}
    Returns:
      { "total": N, "list": { "entry": [ ... ] } }
    """
    url = f"{BASE_URL}/rest/confiforms/1.0/search/{page_id}/{form_name}"
    r = session.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def cf_definition(session: requests.Session, page_id: int, form_name: str) -> Dict[str, Any]:
    """
    GET /rest/confiforms/1.0/definition/{pageId}/{formName}
    Returns:
      { "formName": "...", "fields": [ ... ] }
    """
    url = f"{BASE_URL}/rest/confiforms/1.0/definition/{page_id}/{form_name}"
    r = session.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


# -----------------------------
# Parse responses (your exact shapes)
# -----------------------------
def extract_entries(search_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        return search_json["list"]["entry"]
    except Exception as e:
        raise ValueError(f"Unexpected search JSON shape; expected list.entry[]. Error: {e}")


def extract_def_fields(defn_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    fields = defn_json.get("fields")
    if not isinstance(fields, list):
        raise ValueError("Unexpected definition JSON shape; expected top-level 'fields' list")
    return fields


# -----------------------------
# Build ID -> Label lookup from definition
# -----------------------------
def build_value_maps(defn_json: Dict[str, Any], target_field_names: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Builds:
      {
        "OfferStatus": {"a": "Recommended for Hire", ...},
        ...
      }

    Prefers field["values"] when present (it is already a dict).
    Falls back to field["valuePairs"] -> {id: value}.
    """
    lookups: Dict[str, Dict[str, str]] = {}

    for f in extract_def_fields(defn_json):
        name = f.get("name")
        if name not in target_field_names:
            continue

        # Best case: "values" is already the mapping dict
        values = f.get("values")
        if isinstance(values, dict) and values:
            lookups[name] = {str(k): str(v) for k, v in values.items()}
            continue

        # Fallback: "valuePairs" list of {id, value}
        value_pairs = f.get("valuePairs")
        if isinstance(value_pairs, list) and value_pairs:
            m: Dict[str, str] = {}
            for vp in value_pairs:
                if not isinstance(vp, dict):
                    continue
                vid = vp.get("id")
                vlab = vp.get("value")
                if vid is not None and vlab is not None:
                    m[str(vid)] = str(vlab)
            lookups[name] = m
            continue

        # No mapping present (could be user picker, text, etc.)
        lookups[name] = {}

    return lookups


# -----------------------------
# Apply mapping to search entries
# -----------------------------
def translate_entries(
    entries: List[Dict[str, Any]],
    lookups: Dict[str, Dict[str, str]],
    fields_to_translate: List[str],
) -> List[Dict[str, Any]]:
    """
    For each entry:
      - Reads entry["fields"][<FieldName>] which is an ID like "a", "b", "c"
      - Adds entry["fieldsLabels"][<FieldName>] = translated label
    Leaves original entry["fields"] untouched.
    """
    out: List[Dict[str, Any]] = []

    for entry in entries:
        new_entry = dict(entry)

        fields = entry.get("fields") or {}
        if not isinstance(fields, dict):
            fields = {}

        labels: Dict[str, Any] = {}

        for field_name in fields_to_translate:
            if field_name not in fields:
                continue

            raw = fields.get(field_name)
            if raw is None:
                labels[field_name] = None
                continue

            raw_id = str(raw)
            label_map = lookups.get(field_name, {})
            labels[field_name] = label_map.get(raw_id, raw_id)  # fallback: keep ID if unknown

        new_entry["fieldsLabels"] = labels
        out.append(new_entry)

    return out


# -----------------------------
# Main
# -----------------------------
def main():
    session = make_session()

    search_json = cf_search(session, PAGE_ID, FORM_NAME)
    entries = extract_entries(search_json)

    defn_json = cf_definition(session, PAGE_ID, FORM_NAME)
    lookups = build_value_maps(defn_json, FIELDS_TO_TRANSLATE)

    translated = translate_entries(entries, lookups, FIELDS_TO_TRANSLATE)

    # Preview a few rows
    for e in translated[:5]:
        print(
            {
                "recordId": e.get("recordId"),
                "CandidateName": (e.get("fields") or {}).get("CandidateName"),
                "OfferStatus": (e.get("fields") or {}).get("OfferStatus"),
                "OfferStatus__label": (e.get("fieldsLabels") or {}).get("OfferStatus"),
            }
        )


if __name__ == "__main__":
    main()