# Gameplay Workflows

## Purpose

This reference summarizes the user-facing MaaNTE task behavior and key options for ordinary gameplay automation.

## Fishing

Task names: `Fish`, `FishNew`.

Primary files:

- Task options: `Fish.json`.
- Old flow entry: `FishEntrance`.
- New flow entry: `FishNewEntrance`.
- Supporting pipelines: fishing scene/status, bait handling, fish navigation routes.

Important behavior:

- Old `Fish` loops through fishing, optional auto sell, optional auto buy bait, and task exit.
- `FishNew` is the newer refactored flow and can call `FishNaviEntrance` before entering the fishing minigame.
- Auto buy bait buys up to 99 bait and can switch/use universal bait when ordinary bait is exhausted.
- Auto sell handles full fish inventory or insufficient fish currency states.

Important options:

- `FishLoopInfinite`: rewires old flow into an infinite loop.
- `FishLoopTime`: bounded old-flow loops when infinite mode is off.
- `FishNumber`: fish count for the old Python action and `FishNewCast` max-hit behavior.
- `FishSellAuto`: enables old and new sell branches.
- `FishBuyBaitAuto`: enables bait purchase/selection branches and exposes `FishBaitThreshold`.
- `FishNewAutoNavi`: enables fish location selection and route navigation.

Common edit points:

- Bait threshold/recognition: template/OCR nodes around `FishChooseGeneralBait` and `FishNewChooseGeneralBait`.
- Fishing minigame action: `auto_fish`, `auto_fish_without_cv`.
- Scene entry: `FishSceneWorldToPrepare`, `FishScenePrepareToFishGameGo`.

## Coffee

Task names: `MakeCoffee`, `MakeCoffeeLite`.

Behavior:

- Enters/uses coffee shop flow, waits for the open-shop/start button, runs a Python action to automate the game loop, waits for goal/reward states, and repeats.
- `MakeCoffeeLoopTime` overrides `AutoMakeCoffee.custom_action_param.count`.
- Lite mode has a combined count/timeout option and a separate Pipeline entry.

Controller: `Win32-Front` in current task JSON. The README says the feature does not need foreground in some user-facing wording, but current task restrictions should be treated as authoritative unless retested.

## Rewards and Fountain

`ClaimRewards`:

- Entry `ClaimRewardsEntrance` runs activity and battle-pass branches.
- Options independently enable activity and battle-pass reward collection.
- Allowed controllers: `Win32`, `Win32-Front`.

`FountainCheckin`:

- Entry `FountainCheckinEntrance` first checks whether teleport is needed, then uses local route navigation to reach the fountain, then performs check-in/wish/skip-story/exit steps.
- Requires `Win32-Front` in task JSON.
- Uses both map teleport and route navigation internals; see navigation sub-skill for those APIs.

## Bid King

Task name: `BidKing`, entry `BidKingEntrance`, controller `Win32-Front`.

Behavior:

- Repeats `BidKingRound` based on `BidKingLoopCount`.
- Clicks start, confirms, waits for the balance marker, repeatedly chooses bid or skip, selects quantity 1, confirms bid, and exits the round.
- Recognition is mostly TemplateMatch with fixed ROIs and thresholds.

## Touch

Task name: `Touch`, entry `TouchDetect`.

Behavior:

- Detects an interaction prompt, presses F, clicks an interaction area, presses Esc, then loops.
- Options control max loop count and delays after F/click.

## Witch Divination

Task name: `WitchDivination`, entry `WitchDivinationEntrance`, controller `Win32-Front`.

Behavior is Pipeline-driven through divination, action, chat, and shuffle-step JSON files. Treat it as a scene/UI pipeline task unless a Python action is introduced later.

## Character Ability and City Ability Sync

Task name: `SyncCharacterAbilityCityAbilityNextCharacter`, entry `SyncCharacterAbilityCityAbilityEntrance`, controller `Win32-Front`.

Behavior:

- Enters the character menu.
- Iterates through characters.
- OCRs character names and city ability levels; TemplateMatch can override names with high-confidence portrait matches.
- Writes `CharacterAbility_CityAbility.json` under the runtime config directory.
- Option `SyncCharacterAbilityCityAbilityFreshRecord` toggles fresh-record mode.

Development notes:

- Name matching uses a map from template file names to Chinese character names.
- Skill0 range is 0–5; skill1 range is 0–2 or `-1` for unavailable.
- This workflow spans Pipeline nodes and Python storage logic; read custom-actions before changing internals.

## Presets

Preset files compose task groups such as AFK, daily, quick daily, and realtime assistance. Always inspect the preset file before changing a task's option defaults because presets can override or assume a specific task branch.
