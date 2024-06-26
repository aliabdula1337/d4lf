import datetime
import os
import pathlib
import re
import time

import lxml.html
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.config.models import AffixFilterCountModel, AffixFilterModel, ItemFilterModel, ProfileModel
from src.dataloader import Dataloader
from src.gui.importer.common import (
    fix_offhand_type,
    fix_weapon_type,
    match_to_enum,
    retry_importer,
    save_as_profile,
)
from src.item.data.affix import Affix
from src.item.data.item_type import ItemType
from src.item.descr.text import clean_str, closest_match
from src.logger import Logger

BASE_URL = "https://d4builds.gg/builds"
BUILD_OVERVIEW_XPATH = "//*[@class='builder__stats__list']"
CLASS_XPATH = ".//*[contains(@class, 'builder__header__description')]/*"
ITEM_GROUP_XPATH = ".//*[contains(@class, 'builder__stats__group')]"
ITEM_SLOT_XPATH = ".//*[contains(@class, 'builder__stats__slot')]"
ITEM_STATS_XPATH = ".//*[contains(@class, 'dropdown__button__wrapper')]"
PAPERDOLL_ITEM_SLOT_XPATH = ".//*[contains(@class, 'builder__gear__slot')]"
PAPERDOLL_ITEM_XPATH = ".//*[contains(@class, 'builder__gear__item') and not(contains(@class, 'disabled'))]"
PAPERDOLL_XPATH = "//*[contains(@class, 'builder__gear__items')]"
TEMPERING_ICON_XPATH = ".//*[contains(@src, 'tempering_02.png')]"
UNIQUE_ICON_XPATH = ".//*[contains(@src, '/Uniques/')]"


class D4BuildsException(Exception):
    pass


@retry_importer(inject_webdriver=True)
def import_d4builds(driver: ChromiumDriver = None, url: str = None):
    url = url.strip().replace("\n", "")
    if BASE_URL not in url:
        Logger.error("Invalid url, please use a d4builds url")
        return
    Logger.info(f"Loading {url}")
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.XPATH, BUILD_OVERVIEW_XPATH)))
    wait.until(EC.presence_of_element_located((By.XPATH, PAPERDOLL_XPATH)))
    time.sleep(5)  # super hacky but I didn't find anything else. The page is not fully loaded when the above wait is done
    data = lxml.html.fromstring(driver.page_source)
    class_name = data.xpath(CLASS_XPATH)[0].tail.lower()
    if not (items := data.xpath(BUILD_OVERVIEW_XPATH)):
        Logger.error(msg := "No items found")
        raise D4BuildsException(msg)
    non_unique_slots = _get_non_unique_slots(data=data)
    finished_filters = []
    for item in items[0]:
        item_filter = ItemFilterModel()
        if not (slot := item.xpath(ITEM_SLOT_XPATH)[1].tail):
            Logger.error("No item_type found")
            continue
        if slot not in non_unique_slots:
            Logger.warning(f"Uniques or empty are not supported. Skipping: {slot}")
            continue
        if not (stats := item.xpath(ITEM_STATS_XPATH)):
            Logger.error(f"No stats found for {slot=}")
            continue
        item_type = None
        affixes = []
        inherents = []
        for stat in stats:
            if stat.xpath(TEMPERING_ICON_XPATH):
                continue
            if "filled" not in stat.xpath("../..")[0].attrib["class"]:
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
            if ("ring" in slot.lower() and any(substring in affix_name.lower() for substring in ["resistance"])) or (
                "boots" in slot.lower() and any(substring in affix_name.lower() for substring in ["max evade charges", "attacks reduce"])
            ):
                inherents.append(affix_obj)
            else:
                affixes.append(affix_obj)
        item_type = (
            match_to_enum(enum_class=ItemType, target_string=re.sub(r"\d+", "", slot.replace(" ", ""))) if item_type is None else item_type
        )
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
    save_as_profile(
        file_name=f"d4build_{class_name}_{datetime.datetime.now(tz=datetime.UTC).strftime("%Y_%m_%d_%H_%M_%S")}", profile=profile, url=url
    )
    Logger.info("Finished")


def _corrections(input_str: str) -> str:
    input_str = input_str.lower()
    match input_str:
        case "max life":
            return "maximum life"
        case "total armor":
            return "armor"
    if "ranks to" in input_str or "ranks of" in input_str:
        return input_str.replace("ranks to", "to").replace("ranks of", "to")
    return input_str


def _get_non_unique_slots(data: lxml.html.HtmlElement) -> list[str]:
    result = []
    if not (paperdoll := data.xpath(PAPERDOLL_XPATH)):
        Logger.error(msg := "No paperdoll found")
        raise D4BuildsException(msg)
    if not (items := paperdoll[0].xpath(PAPERDOLL_ITEM_XPATH)):
        Logger.error(msg := "No items found")
        raise D4BuildsException(msg)
    for item in items:
        if not item.xpath(UNIQUE_ICON_XPATH):
            slot = item.xpath(PAPERDOLL_ITEM_SLOT_XPATH)
            result.append(slot[0].text)
    return result


if __name__ == "__main__":
    Logger.init("debug")
    os.chdir(pathlib.Path(__file__).parent.parent.parent.parent)
    URLS = [
        "https://d4builds.gg/builds/463e7337-8fa9-491f-99a0-cbd6c65fc6f4/?var=1",
    ]
    for X in URLS:
        import_d4builds(url=X)
