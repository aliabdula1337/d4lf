import os
import pathlib
import re

import lxml.html

from src.config.models import AffixFilterCountModel, AffixFilterModel, ItemFilterModel, ProfileModel
from src.dataloader import Dataloader
from src.gui.importer.common import fix_offhand_type, fix_weapon_type, get_with_retry, match_to_enum, retry_importer, save_as_profile
from src.item.data.affix import Affix
from src.item.data.item_type import ItemType
from src.item.descr.text import clean_str, closest_match
from src.logger import Logger

BUILD_GUIDE_ACTIVE_LOADOUT_XPATH = "//*[@class='m-fsuco1']"
BUILD_GUIDE_BASE_URL = "https://mobalytics.gg/diablo-4/"
BUILD_GUIDE_NAME_XPATH = "//*[@class='m-a53mf3']"
IMAGE_XPATH = ".//img"
ITEM_AFFIXES_EMPTY_XPATH = ".//*[@class='m-19epikr']"
ITEM_EMPTY_XPATH = ".//*[@class='m-16arb5z']"
ITEM_NAME_XPATH = ".//*[@class='m-ndz0o2']"
STATS_GRID_OCCUPIED_XPATH = ".//*[@class='m-0']"
STATS_GRID_XPATH = "//*[@class='m-4tf4x5']"
STATS_LIST_XPATH = ".//*[@class='m-qodgh2']"
TEMPERING_ICON_XPATH = ".//*[contains(@src, 'Tempreing.svg')]"


class MobalyticsException(Exception):
    pass


@retry_importer
def import_mobalytics(url: str):
    url = url.strip().replace("\n", "")
    if BUILD_GUIDE_BASE_URL not in url:
        Logger.error("Invalid url, please use a mobalytics build guide")
        return
    if "equipmentTab" not in url:
        if "?" in url:
            url += "&"
        else:
            url += "?"
        url += "equipmentTab=gear-stats"
    elif "equipmentTab=aspects-and-uniques" in url:
        url = url.replace("equipmentTab=aspects-and-uniques", "equipmentTab=gear-stats")
    Logger.info(f"Loading {url}")
    try:
        r = get_with_retry(url=url)
    except ConnectionError as ex:
        Logger.error(msg := "Couldn't get build")
        raise MobalyticsException(msg) from ex
    data = lxml.html.fromstring(r.text)
    build_elem = data.xpath(BUILD_GUIDE_NAME_XPATH)
    if not build_elem:
        Logger.error(msg := "No build found")
        raise MobalyticsException(msg)
    build_name = build_elem[0].tail
    class_name = _get_class_name(input_str=build_elem[0].text)
    if not (stats_grid := data.xpath(STATS_GRID_XPATH)):
        Logger.error(msg := "No stats grid found")
        raise MobalyticsException(msg)
    if not (items := stats_grid[0].xpath(STATS_GRID_OCCUPIED_XPATH)):
        Logger.error(msg := "No items found")
        raise MobalyticsException(msg)
    finished_filters = []
    for item in items:
        item_filter = ItemFilterModel()
        if not (name := item.xpath(ITEM_NAME_XPATH)):
            if item.xpath(ITEM_EMPTY_XPATH):
                continue
            Logger.error(msg := "No item name found")
            raise MobalyticsException(msg)
        if "aspect" not in (x := name[0].text).lower():
            Logger.warning(f"Uniques are not supported. Skipping: {x}")
            continue
        if not (slot_elem := item.xpath(IMAGE_XPATH)):
            Logger.error(msg := "No item_type found")
            raise MobalyticsException(msg)
        slot = slot_elem[0].attrib["alt"]
        if not (stats := item.xpath(STATS_LIST_XPATH)):
            if item.xpath(ITEM_AFFIXES_EMPTY_XPATH):
                continue
            Logger.error(msg := "No stats found")
            raise MobalyticsException(msg)
        item_type = None
        affixes = []
        inherents = []
        for stat in stats:
            if stat.xpath(TEMPERING_ICON_XPATH):
                continue
            affix_name = stat.xpath("./span")[0].text
            if "weapon" in slot.lower() and (x := fix_weapon_type(input_str=affix_name)) is not None:
                item_type = x
                continue
            if "offhand" in slot.lower() and (x := fix_offhand_type(input_str=affix_name, class_str=class_name)) is not None:
                item_type = x
                if any(
                    substring in affix_name.lower() for substring in ["focus", "offhand", "shield", "totem"]
                ):  # special line indicating the item type
                    continue
            affix_obj = Affix(name=closest_match(clean_str(_corrections(input_str=affix_name)).strip().lower(), Dataloader().affix_dict))
            if affix_obj.name is None:
                Logger.error(f"Couldn't match {affix_name=}")
                continue
            if (x := stat.xpath("./span/span")) and "implicit" in x[0].text.lower():
                inherents.append(affix_obj)
            else:
                affixes.append(affix_obj)
        item_type = match_to_enum(enum_class=ItemType, target_string=re.sub(r"\d+", "", slot.lower())) if item_type is None else item_type
        if item_type is None:
            Logger.warning(f"Couldn't match item_type: {slot}. Please edit manually")
        item_filter.itemType = [item_type] if item_type is not None else []
        item_filter.affixPool = [
            AffixFilterCountModel(
                count=[AffixFilterModel(name=x.name) for x in affixes],
                minCount=2,
                minGreaterAffixCount=0,
            )
        ]
        if inherents:
            item_filter.inherentPool = [AffixFilterCountModel(count=[AffixFilterModel(name=x.name) for x in inherents])]
        filter_name_template = item_filter.itemType[0].name if item_filter.itemType else slot.replace(" ", "")
        filter_name = filter_name_template
        i = 2
        while any(filter_name == next(iter(x)) for x in finished_filters):
            filter_name = f"{filter_name_template}{i}"
            i += 1
        finished_filters.append({filter_name: item_filter})
    profile = ProfileModel(name="imported profile", Affixes=sorted(finished_filters, key=lambda x: next(iter(x))))
    build_name = build_name if build_name else f"{class_name}_{data.xpath(BUILD_GUIDE_ACTIVE_LOADOUT_XPATH)[0].text()}"
    save_as_profile(file_name=build_name, profile=profile, url=url)
    Logger.info("Finished")


def _corrections(input_str: str) -> str:
    match input_str.lower():
        case "max life":
            return "maximum life"
    return input_str


def _get_class_name(input_str: str) -> str:
    input_str = input_str.lower()
    if "barbarian" in input_str:
        return "Barbarian"
    if "druid" in input_str:
        return "Druid"
    if "necromancer" in input_str:
        return "Necromancer"
    if "rogue" in input_str:
        return "Rogue"
    if "sorcerer" in input_str:
        return "Sorcerer"
    Logger.error(f"Couldn't match class name {input_str=}")
    return "Unknown"


if __name__ == "__main__":
    Logger.init("debug")
    os.chdir(pathlib.Path(__file__).parent.parent.parent.parent)
    URLS = [
        "https://mobalytics.gg/diablo-4/profile/2a93597f-152e-4266-8e96-df63792e4f9c/builds/d2f8186d-b2ea-42a2-9f77-535d1881f5a0",
    ]
    for X in URLS:
        import_mobalytics(url=X)
