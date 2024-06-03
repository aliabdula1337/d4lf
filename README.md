# ![logo](assets/logo.png)

## Diablo 4 Loot Filter

Filter items and sigils in your inventory based on affixes, aspects, and thresholds of their values.

For questions, feature requests, or issue reports, join the [Discord](https://discord.gg/YyzaPhAN6T) or use [GitHub Issues](https://github.com/aeon0/d4lf/issues).


![sample](assets/thumbnail.jpg)]

## Features

- Filter items in inventory and stash
- Filter by item type, item power and greater affix count
- Filter by affix and their values
- Filter uniques by their affix and aspect values
- Filter sigils by blacklisting and whitelisting locations and affixes
- Quickly move items from your stash or inventory
- Supported resolutions are all aspect ratios between 16:10 and 21:9

## How to Setup

### Game Settings

- Font size can be small or medium in the Gameplay Settings
- Game Language must be English
- The tool does not play well with HDR as it makes everything super bright
- The advanced item comparison feature might cause incorrect classifications

### Run

- Download the latest version (.zip) from the releases: https://github.com/aeon0/d4lf/releases
- Execute d4lf.exe and go to your D4 screen
- There is a small overlay on the center bottom with buttons:
    - max/min: Show or hide the console output
    - filter: Auto filter inventory and stash if open (number of stash tabs configurable)
    - vision: Turn vision mode (overlay) on/off
- Alternative use the hotkeys. e.g. f11 for filtering

### Configs

The config folder contains:

- __profiles/*.yaml__: These files determine what should be filtered
- __params.ini__: Different hotkey settings and number of chest stashes that should be looked at

### params.ini

| [general]                  | Description                                                                                                                                                                                                                        |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| profiles                   | A set of profiles separated by comma. d4lf will look for these yaml files in config/profiles and in C:/Users/WINDOWS_USER/.d4lf/profiles                                                                                           |
| keep_aspects               | `all`: Keep all legendary items - `upgrade`: Keep all legendary items that upgrade your codex of power -`none`: Keep no legendary items based on aspect (they are still filtered!)                                                 |
| handle_rares               | `filter`: Filter them based on your profiles - `ignore`: Ignores all rares, vision mode shows them as blue and auto mode never junks or favorites them -`junk`: Vision mode shows them always as red, auto mode always junks rares |
| run_vision_mode_on_startup | If the vision mode should automatically start when starting d4lf. Otherwise has to be started manually with the vision button or the hotkey                                                                                        |
| check_chest_tabs           | Which chest tabs will be checked and filtered for items in case chest is open when starting the filter. You need to buy all slots. Counting is done left to right. E.g. 1,2,4 will check tab 1, tab 2, tab 4                       |
| move_item_type             | Which types of items to move when using fast move functionality. Will only affect tabs defined in check_chest_tabs. `junk`: Move junk only - `non_favorites`: Only items not marked as favorite - `everything`: Move everything    |
| hidden_transparency        | The overlay will become transparent after not hovering it for a while. This can be changed by specifying any value between [0, 1] with 0 being completely invisible and 1 completely visible                                       |
| browser                    | Which browser to use to get builds, please make sure you pick an installed browser: chrome, edge or firefox are currently supported                                                                                                |
| full_dump                  | When using the import build feature, whether to use the full dump (e.g. contains all filter items) or not                                                                                                                          |

| [char]    | Description                       |
|-----------|-----------------------------------|
| inventory | Your hotkey for opening inventory |

| [advanced_options] | Description                                                                                                              |
|--------------------|--------------------------------------------------------------------------------------------------------------------------|
| move_to_inv        | Hotkey for moving items from stash to inventory                                                                          |
| move_to_chest      | Hotkey for moving items from inventory to stash                                                                          |
| run_scripts        | Hotkey to start/stop vision mode                                                                                         |
| run_filter         | Hotkey to start/stop filtering items                                                                                     |
| exit_key           | Hotkey to exit d4lf.exe                                                                                                  |
| log_level          | Logging level. Can be any of [debug, info, warning, error, critical]                                                     |
| scripts            | Running different scripts                                                                                                |
| process_name       | Process name of the D4 app. Defaults to "Diablo IV.exe". In case of using some remote play this might need to be adapted |

### GUI

Not yet finished. For now, it should be self-explanatory. Just start `gui.bat` in the archive.

## How to filter / Profiles

All profiles define whitelist filters. If no filter included in your profiles matches the item, it will be discarded.

Your config files will be validated on startup and will prevent the program from starting if the structure or syntax is
incorrect. The error message will provide hints about the specific problem.

The following sections will explain each type of filter that you can specify in your profiles. How you define them in
your YAML files is up to you; you can put all of these into just one file or have a dedicated file for each type of
filter, or even split the same type of filter over multiple files. Ultimately, all profiles specified in
your `params.ini` will be used to determine if an item should be kept. If one of the profiles wants to keep the item, it
will be kept regardless of the other profiles. Similarly, if a filter is missing in all profiles (e.g., there is
no `Sigils` section in any profile), all corresponding items (in this case, sigils) will be kept.

### Affix / Aspects Filter Syntax

You have two choices on how to specify aspects or affixes of an item:

- You can use the shorthand and just specify the aspect name
- For more sophisticated filtering, you can use the following syntax: `[NAME, THRESHOLD, CONDITION]`. The
  condition can be any of `[larger, smaller]` and defaults to `larger` if no value is given.

<details><summary>Examples</summary>

```yaml
  # Filter for attack speed
  - attack_speed
  # Filter for attack speed larger than 4
  - [ attack_speed, 4 ]
  # Filter for attack speed smaller than 4
  - [ attack_speed, 4, smaller ]
```

</details>

### Affixes

Affixes are defined by the top-level key `Affixes`. It contains a list of filters that you want to apply. Each filter
has a name and can filter for any combination of the following:

- `itemType`: The name of the type or a list of multiple types.
  See [assets/lang/enUS/item_types.json](assets/lang/enUS/item_types.json)
- `minPower`: Minimum item power
- `minGreaterAffixCount`: Minimum number of greater affixes. Note that this is on the overall item and independent
  of `affixPool`
- `affixPool`: A list of multiple different rulesets to filter for. Each ruleset must be fulfilled or the item is
  discarded
    - `count`: Define a list of affixes (see [syntax](#affix--aspects-filter-syntax)) and
      optionally `minCount`, `maxCount` and `minGreaterAffixCount`
        - `minCount`: specifies the minimum number of affixes that must match the item. defaults to amount of specified
          affixes
        - `maxCount` specifies the maximum number of affixes that must match the item. defaults to amount of specified
          affixes
        - `minGreaterAffixCount`: specifies the minimum number of greater affixes inside this count group. defaults
          to `0`
- `inherentPool`: The same rules as for `affixPool` apply, but this is evaluated against the inherent affixes of the
  item

<details><summary>Config Examples</summary>

```yaml
Affixes:
  # Search for chest armor and pants that are at least item level 725 and have at least 3 affixes of the affixPool
  - NiceArmor:
      itemType: [ chest armor, pants ]
      minPower: 725
      affixPool:
        - count:
            - [ dexterity, 33 ]
            - [ damage_reduction, 5 ]
            - [ lucky_hit_chance, 3 ]
            - [ total_armor, 9 ]
            - [ maximum_life, 700 ]
          minCount: 3

  # Search for chest armor that is at least item level 925 and have at least 3 affixes of the affixPool. At least 2 of the matched affixes must be greater affixes
  - NiceArmor:
      itemType: chest armor
      minPower: 925
      affixPool:
        - count:
            - dexterity
            - damage_reduction
            - lucky_hit_chance
            - total_armor
            - maximum_life
          minCount: 3
          minGreaterAffixCount: 2

  # Search for boots that have at least 2 of the specified affixes and
  # either max evade charges or reduced evade cooldown as inherent affix
  - GreatBoots:
      itemType: boots
      minPower: 800
      inherentPool:
        - count:
            - maximum_evade_charges
            - attacks_reduce_evades_cooldown_by_seconds
          minCount: 1
      affixPool:
        - count:
            - [ movement_speed, 16 ]
            - [ cold_resistance ]
            - [ lightning_resistance ]
          minCount: 2

  # Search for boots with movement speed and 2 resistances from a pool of shadow, cold, lightning res
  - ResBoots:
      itemType: boots
      minPower: 800
      affixPool:
        - count:
            - [ movement_speed, 16 ]
        - count:
            - [ shadow_resistance ]
            - [ cold_resistance ]
            - [ lightning_resistance ]
          minCount: 2

  # Search for boots with movement speed and 2 resistances from a pool of shadow, cold, lightning res. At least two of all item affixes must be a greater affix
  - ResBoots:
      itemType: boots
      minPower: 800
      minGreaterAffixCount: 2
      affixPool:
        - count:
            - [ movement_speed, 16 ]
        - count:
            - [ shadow_resistance ]
            - [ cold_resistance ]
            - [ lightning_resistance ]
          minCount: 2
```

</details>

Affix names are lower case and spaces are replaced by underscore. You can find the full list of names
in [assets/lang/enUS/affixes.json](assets/lang/enUS/affixes.json).

### Sigils

Sigils are defined by the top-level key `Sigils`. It contains a list of affix or location names that you want to filter
for. If no Sigil filter is provided, all Sigils will be kept.

<details><summary>Config Examples</summary>

```yaml
Sigils:
  minTier: 40
  maxTier: 100
  blacklist:
    # locations
    - endless_gates
    - vault_of_the_forsaken

    # affixes
    - armor_breakers
    - resistance_breakers
```

If you want to filter for a specific affix or location, you can also use the `whitelist` key. Even if `whitelist` is
present, `blacklist` will be used to discard sigils that match any of the blacklisted affixes or locations.

```yaml
# Only keep sigils for vault_of_the_forsaken without any of the affixes armor_breakers and resistance_breakers
Sigils:
  minTier: 40
  maxTier: 100
  blacklist:
    - armor_breakers
    - resistance_breakers
  whitelist:
    - vault_of_the_forsaken
```

You can also create conditional filters based on a single affix or location.

```yaml
# Only keep sigils for iron_hold when it also has shadow_damage
Sigils:
  minTier: 40
  maxTier: 100
  blacklist:
    - armor_breakers
    - resistance_breakers
  whitelist:
    - [ iron_hold, shadow_damage ]
```

</details>

Sigil affixes and location names are lower case and spaces are replaced by underscore. You can find the full list of
names in [assets/lang/enUS/sigils.json](assets/lang/enUS/sigils.json).

### Uniques

Uniques are defined by the top-level key `Uniques`. It contains a list of parameters that you want to filter for. If no
Unique filter is provided, all unique items will be kept.
Uniques can be filtered similar to [Affixes](#Affixes) but due to their nature of fixed
effects, you only have to specify the thresholds that you want to apply.

<details><summary>Config Examples</summary>

```yaml
# Take all uniques with item power > 800
Uniques:
  - minPower: 900
```

```yaml
# Take all unique pants
Uniques:
  - itemType: pants
```

```yaml
# Take all unique chest armors and pants
Uniques:
  - itemType: [ chest armor, pants ]
```

```yaml
# Take all unique chest armors and pants with min item power > 900
Uniques:
  - itemType: [ chest armor, pants ]
    minPower: 900
```

```yaml
# Take all Tibault's Will pants
Uniques:
  - aspect: [ tibaults_will ]
```

```yaml
# Take all Tibault's Will pants with at least 2 greater affixes
Uniques:
  - aspect: [ tibaults_will ]
    minGreaterAffixCount: 2
```

```yaml
# Take all Tibault's Will pants that have item power > 900 and dmg reduction from close > 12 as well as aspect value > 25
Uniques:
  - aspect: [ tibaults_will, 25 ]
    minPower: 900
    affix:
      - [ damage_reduction_from_close_enemies, 12 ]
```

</details>

Unique names are lower case and spaces are replaced by underscore. You can find the full list of names
in [assets/lang/enUS/uniques.json](assets/lang/enUS/uniques.json).

## Custom configs

D4LF will search for `params.ini` and for `profiles/*.yaml` in `C:/Users/WINDOWS_USER/.d4lf`. All values
in `C:/Users/WINDOWS_USER/.d4lf/params.ini` will overwrite the values from the `params.ini` file in the D4LF folder. In
the profiles folder, additional custom profiles can be added and used.

This setup is helpful to facilitate updating to a new version as you don't need to copy around your config and profiles.

**In the event of breaking changes to the configuration, there will be a major release, such as updating from 2.x.x to
3.x.x.**

## Development Guide

### Python Setup

You can set up your Python environment using either [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/) or standard Python.

#### Conda Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/aeon0/d4lf
   cd d4lf
   ```
2. Create the Conda environment:
   ```bash
   conda env create -f environment.yml
   ```
3. Activate the environment:
   ```bash
   conda activate d4lf
   ```
4. Run the main script:
   ```bash
   python -m src.main
   ```

#### Python Setup (Windows, Linux venv activation differs)

1. Clone the repository:
   ```bash
   git clone https://github.com/aeon0/d4lf
   cd d4lf
   ```
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   ```bash
   venv\Scripts\activate
   ```
4. Install the required packages:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Run the main script:
   ```bash
   python -m src.main
   ```

### Formatting & Linting

We use Ruff for linting and auto-formatting. To format and check your code, run the following commands:

- Format code:
  ```bash
  ruff format
  ```
- Check code:
  ```bash
  ruff check
  ```
 
To set up VS Code for optimal use with Ruff, install the [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) and enable the "trim trailing whitespaces" setting in your VS Code preferences.

## Credits

- Icon based of: [CarbotAnimations](https://www.youtube.com/carbotanimations/about)
- Some of the OCR code is originally from [@gleed](https://github.com/aliig). Good guy.
- Names and textures for matching from [Blizzard](https://www.blizzard.com)

## Legal

d4lf is not affiliated with Blizzard Entertainment and does not represent the views or opinions of Blizzard Entertainment or anyone officially involved in creating or managing Diablo IV.

Diablo IV and Blizzard Entertainment are trademarks or registered trademarks of Blizzard Entertainment, Inc. ©
