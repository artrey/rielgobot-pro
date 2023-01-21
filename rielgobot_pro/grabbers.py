import json
import re
import typing as ty

import bs4
import requests

from rielgobot_pro.models import FlatInfo, Location


def grab_from_gratka(url: str) -> FlatInfo:
    response = requests.get(url)
    text = response.text
    images_json_data = text[text.index("dataJson") + 9 : text.index("contactFormId")].strip()[:-1]
    images = json.loads(images_json_data)[0]["data"]

    geo_index = text.index('"geo":') + 6
    location_json_data = text[geo_index : text.index("}", geo_index) + 1]
    coords = json.loads(location_json_data)

    return FlatInfo(
        location=Location(longitude=coords["longitude"], latitude=coords["latitude"]),
        images=[img["url"] for img in images],
    )


# print(grab_from_gratka("https://gratka.pl/nieruchomosci/do-wynajecia-3-pokoje-70m-konstruktorska-obok-galerii-mokotow/oi/28712999"))


def grab_from_otodom(url: str) -> FlatInfo:
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, features="lxml")
    json_data = json.loads(soup.find(id="__NEXT_DATA__").text)
    flat_data = json_data.get("props", {}).get("pageProps", {}).get("ad") or {}
    coords = flat_data.get("location", {}).get("coordinates")
    target = flat_data.get("target") or {}
    return FlatInfo(
        area=float(target.get("Area", 0)) or None,
        price=f"{target.get('Price', '?')} PLN",
        rooms=int(target.get("Rooms_num", [0])[0]),
        location=Location(longitude=coords["longitude"], latitude=coords["latitude"]),
        images=[img["large"] for img in flat_data["images"]],
    )


# print(grab_from_otodom("https://www.otodom.pl/pl/oferta/mieszkanie-na-goclawiu-z-pieknym-widokiem-ID4jZPg"))
# print(grab_from_otodom("https://www.otodom.pl/pl/oferta/mieszkanie-2-pokoje-jak-nowe-praga-poludnie-goclaw-ID4jZYY"))


def grab_from_olx(url: str) -> FlatInfo:
    response = requests.get(url)
    images = re.findall(r'src="(https://ireland.apollo.olxcdn.com:443/v1/files[^"]+)', response.text)
    return FlatInfo(images=images)


# print(grab_from_olx("https://www.olx.pl/d/oferta/komfortowa-kawalerka-bezpos-przy-dworcu-centralny-CID3-IDSMQMi.html"))


GRABBERS: dict[str, ty.Callable[[str], FlatInfo]] = {
    "olx": grab_from_olx,
    "otodom": grab_from_otodom,
    "gratka": grab_from_gratka,
}
