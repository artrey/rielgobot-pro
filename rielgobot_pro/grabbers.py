import json
import re
import typing as ty

import bs4
import requests

from rielgobot_pro.models import FlatInfo, Location
from rielgobot_pro.settings import BS4_PARSER


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


def grab_from_otodom(url: str) -> FlatInfo:
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, features=BS4_PARSER)
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


def grab_from_olx(url: str) -> FlatInfo:
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, features=BS4_PARSER)
    id_str = soup.find("div", attrs={"data-cy": "ad-footer-bar-section"}).find("span").text
    flat_id = re.findall(r"(\d+)", id_str)[0]

    response = requests.get(f"https://www.olx.pl/api/v1/offers/{flat_id}")
    data = response.json().get("data") or {}
    coords = data.get("map") or {}

    info = FlatInfo(
        location=Location(longitude=coords["lon"], latitude=coords["lat"]),
        images=[
            x.get("link", "").format(width=x.get("width", 1024), height=x.get("height", 768))
            for x in data.get("photos", [])
        ],
    )

    params = data.get("params") or []
    for param in params:
        key = param.get("key")
        if key == "m":
            info.area = float(param.get("value", {}).get("key", 0)) or None
        if key == "rooms":
            room_key = param.get("value", {}).get("key")
            info.rooms = {"one": 1, "two": 2, "three": 3, "four": 4}.get(room_key)
        if key == "price":
            value = param.get("value") or {}
            info.price = f"{value.get('value') or ''} {value.get('currency') or ''}".strip() or None

    return info


def grab_from_morizon(url: str) -> FlatInfo:
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, features=BS4_PARSER)
    images = soup.find(id="multimediaBox").find(class_="imageThumbs").find_all("img")
    gmap = soup.find(class_="GoogleMap")

    return FlatInfo(
        location=Location(
            longitude=float(gmap.attrs["data-lng"]),
            latitude=float(gmap.attrs["data-lat"]),
        ),
        images=[x.get("src").replace("/144/100/4/", "/832/468/2/") for x in images],
    )


GRABBERS: dict[str, ty.Callable[[str], FlatInfo]] = {
    "olx": grab_from_olx,
    "otodom": grab_from_otodom,
    "gratka": grab_from_gratka,
    "morizon": grab_from_morizon,
}


if __name__ == "__main__":
    # morizon
    print(
        grab_from_morizon(
            "https://www.morizon.pl/oferta/wynajem-mieszkanie-warszawa-srodmiescie-kolska-68m2-mzn2041527811"
        )
    )

    # gratka
    print(
        grab_from_gratka(
            "https://gratka.pl/nieruchomosci/do-wynajecia-3-pokoje-70m-konstruktorska-obok-galerii-mokotow/oi/28712999"
        )
    )

    # otodom
    print(grab_from_otodom("https://www.otodom.pl/pl/oferta/mieszkanie-na-goclawiu-z-pieknym-widokiem-ID4jZPg"))
    print(
        grab_from_otodom("https://www.otodom.pl/pl/oferta/mieszkanie-2-pokoje-jak-nowe-praga-poludnie-goclaw-ID4jZYY")
    )

    # olx
    print(
        grab_from_olx("https://www.olx.pl/d/oferta/komfortowa-kawalerka-bezpos-przy-dworcu-centralny-CID3-IDSMQMi.html")
    )
