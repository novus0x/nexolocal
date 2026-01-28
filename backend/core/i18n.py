########## Modules ##########
import json

########## Variables ##########
_en = json.load(open("i18n/en.json"))
_es = json.load(open("i18n/es.json"))

TRANSLATIONS = {
    "en": _en,
    "es": _es,
}

########## Choose Lang ##########
def translate(lang: str, key: str):
    print(lang)
    parts = key.split(".")
    d = TRANSLATIONS.get(lang, _es)

    for p in parts:
        if p in d:
            d = d[p]
        else:
            return key
    return d

