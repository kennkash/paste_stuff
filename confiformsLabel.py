import requests
from requests.auth import HTTPBasicAuth
from typing import Any, Dict, List, Optional

# -----------------------------
# Config
# -----------------------------
BASE_URL = "https://confluence.example.com"  # no trailing slash
PAGE_ID = 123456
FORM_NAME = "MyForm"

# Auth: Basic (username/password). Swap to Bearer if your DC supports PAT that way.
USERNAME = "your.username"
PASSWORD = "your.password"

# Field keys to translate (exactly as they appear in the search results JSON)
FIELDS_TO_TRANSLATE = [
    "myRadio",
    "myDropdownAdvanced",
]

# -----------------------------
# REST calls
# -----------------------------
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    s.auth = HTTPBasicAuth(USERNAME, PASSWORD)
    return s

def cf_search(session: requests.Session, page_id: int, form_name: str, query: Optional[str] = None) -> Any:
    """
    GET /filter/rest/confiforms/1.0/search/{pageId}/{formName}
    Note: param support varies by ConfiForms version; keep query optional.
    """
    url = f"{BASE_URL}/filter/rest/confiforms/1.0/search/{page_id}/{form_name}"
    params = {}
    if query:
        params["query"] = query
    r = session.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def cf_definition(session: requests.Session, page_id: int, form_name: str, lazy: bool = False) -> Any:
    """
    GET /rest/confiforms/1.0/definition/{pageId}/{formName}?lazy=false
    lazy=false is commonly needed to include option lists.
    """
    url = f"{BASE_URL}/rest/confiforms/1.0/definition/{page_id}/{form_name}"
    r = session.get(url, params={"lazy": str(lazy).lower()}, timeout=60)
    r.raise_for_status()
    return r.json()

# -----------------------------
# JSON shape helpers
# -----------------------------
def extract_entries(search_json: Any) -> List[Dict[str, Any]]:
    """Normalize search response to a list of entry dicts."""
    if isinstance(search_json, list):
        return search_json
    if isinstance(search_json, dict):
        for k in ("results", "entries", "data", "items"):
            if isinstance(search_json.get(k), list):
                return search_json[k]
    raise ValueError("Unexpected search response JSON shape; can’t find an entries list.")

def extract_fields(defn_json: Any) -> List[Dict[str, Any]]:
    """Normalize definition response to a list of field dicts."""
    if isinstance(defn_json, dict):
        if isinstance(defn_json.get("fields"), list):
            return defn_json["fields"]
        # Some versions nest it
        nested = defn_json.get("formDefinition", {}).get("fields")
        if isinstance(nested, list):
            return nested
    raise ValueError("Unexpected definition JSON shape; can’t find fields list.")

# -----------------------------
# Build id -> label lookup for single-value option fields
# -----------------------------
def build_option_lookup(defn_json: Any, target_fields: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Returns:
      {
        "myRadio": {"optId1": "Label 1", ...},
        "myDropdownAdvanced": {"optIdX": "Label X", ...}
      }

    Tries common ConfiForms definition patterns:
      - field.options = [{id/value/key, label/name/text}, ...]
      - field.values  = [{id/value/key, label/name/text}, ...]
      - field.optionsMap/options_map = {id: label, ...}
    """
    lookups: Dict[str, Dict[str, str]] = {f: {} for f in target_fields}

    for f in extract_fields(defn_json):
        key = f.get("name") or f.get("key") or f.get("fieldName")
        if key not in lookups:
            continue

        # Pattern A: list under "options"
        options = f.get("options")
        if isinstance(options, list):
            for opt in options:
                oid = opt.get("id") or opt.get("value") or opt.get("key")
                lab = opt.get("label") or opt.get("name") or opt.get("text")
                if oid is not None and lab is not None:
                    lookups[key][str(oid)] = str(lab)
            continue

        # Pattern B: list under "values"
        values = f.get("values")
        if isinstance(values, list):
            for opt in values:
                oid = opt.get("id") or opt.get("value") or opt.get("key")
                lab = opt.get("label") or opt.get("name") or opt.get("text")
                if oid is not None and lab is not None:
                    lookups[key][str(oid)] = str(lab)
            continue

        # Pattern C: map/dict
        options_map = f.get("optionsMap") or f.get("options_map") or f.get("map")
        if isinstance(options_map, dict):
            for oid, lab in options_map.items():
                if oid is not None and lab is not None:
                    lookups[key][str(oid)] = str(lab)

    return lookups

# -----------------------------
# Translate IDs to labels (single value only)
# -----------------------------
def translate_entries(
    entries: List[Dict[str, Any]],
    lookups: Dict[str, Dict[str, str]],
    fields: List[str],
) -> List[Dict[str, Any]]:
    """
    Adds "<field>__label" for each field in fields if present on entry.
    Leaves the original stored value intact.
    """
    out: List[Dict[str, Any]] = []
    for e in entries:
        new_e = dict(e)
        for field in fields:
            if field not in e:
                continue
            raw = e.get(field)
            if raw is None:
                new_e[f"{field}__label"] = None
                continue

            raw_id = str(raw)
            new_e[f"{field}__label"] = lookups.get(field, {}).get(raw_id, raw_id)  # fallback to id
        out.append(new_e)
    return out

# -----------------------------
# Main
# -----------------------------
def main():
    session = make_session()

    search_json = cf_search(session, PAGE_ID, FORM_NAME)
    entries = extract_entries(search_json)

    defn_json = cf_definition(session, PAGE_ID, FORM_NAME, lazy=False)
    lookups = build_option_lookup(defn_json, FIELDS_TO_TRANSLATE)

    translated = translate_entries(entries, lookups, FIELDS_TO_TRANSLATE)

    # Print a preview
    for e in translated[:10]:
        preview = {k: e.get(k) for k in ["id", *FIELDS_TO_TRANSLATE, *(f"{f}__label" for f in FIELDS_TO_TRANSLATE)] if k in e}
        print(preview)

if __name__ == "__main__":
    main()


This endpoint: /rest/confiforms/1.0/search/744202791/InterviewTracking 

Returns this json structure: 
{
  "total": 91,
  "list": {
    "entry": [
      {
        "recordId": 2,
        "createdBy": "johndoe",
        "created": 1760554624957,
        "id": "32c77390-22eb-4959-9ef2-d9dc37deb19e",
        "fields": {
          "Shift": "D",
          "Status": "e",
          "HiringManagerPOC": "johndoe",
          "OfferStatus": "c",
          "ProposedTitle": "Tech 1/2",
          "ActualManagerSupervisor": "janedoe",
          "RequisitionNumber": "E123456",
          "Department": "ETCH",
          "InterviewStatus": "c",
          "CandidateName": "Person 1",
          "ProposedLevel": "b",
          "class": "fields",
          "Notes": "We are looking for a Senior Technician, Luis would be a good hire at a later date . \r\n\r\nSent to Randstad as possible contractor, he has declined due to pay."
        },
        "ownedBy": "johndoe"
      },
      {
        "recordId": 3,
        "createdBy": "johnnydoe",
        "created": 1760558964090,
        "id": "31c212e5-bacb-44ac-9e6f-072a4978e55d",
        "fields": {
          "Shift": "A",
          "Status": "d",
          "HiringManagerPOC": "johnnydoe",
          "OfferStatus": "a",
          "ProposedTitle": "Senior Tech",
          "ActualManagerSupervisor": "jamesdoe",
          "RequisitionNumber": "E78910212",
          "Department": "ETCH",
          "InterviewStatus": "c",
          "CandidateName": "Person 2",
          "ProposedLevel": "d",
          "class": "fields",
          "Notes": "Previously worked here, great tech excited to have him back"
        },
        "ownedBy": "johnnydoe"
      },
   ]
  }
}


This endpoint: /rest/confiforms/1.0/definition/744202791/InterviewTracking


Returns this where "name": "OfferStatus" is one of the fields I am trying to map for
{
  "formName": "InterviewTracking",
  "fields": [
    {
      "viewRestrictions": "",
      "editRestrictions": "",
      "smartField": false,
      "name": "LastUpdate",
      "dbField": false,
      "formula": false,
      "readOnly": false,
      "autoField": false,
      "title": "Last Update",
      "type": "datetime",
      "required": false
    },
    {
      "viewRestrictions": "",
      "editRestrictions": "",
      "smartField": false,
      "name": "HiringManagerPOC",
      "dbField": false,
      "formula": false,
      "readOnly": false,
      "autoField": false,
      "title": "Hiring Manager or POC",
      "type": "usersimple",
      "required": false
    },
    {
      "editRestrictions": "",
      "smartField": false,
      "valuePairs": [
        {
          "id": "a",
          "value": "Recommended for Hire"
        },
        {
          "id": "b",
          "value": "NOT Recommended for Hire"
        },
        {
          "id": "c",
          "value": "Decision Not Yet Made"
        }
      ],
      "values": {
        "a": "Recommended for Hire",
        "b": "NOT Recommended for Hire",
        "c": "Decision Not Yet Made"
      },
      "dbField": false,
      "readOnly": false,
      "autoField": false,
      "title": "Offer Status",
      "type": "radio_group",
      "required": true,
      "viewRestrictions": "",
      "name": "OfferStatus",
      "formula": false
    },
  ]
}

update the script accordingly for the json structures I have sent
