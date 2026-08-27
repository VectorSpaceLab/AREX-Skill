# Task Catalog

## When To Read

Read this when mapping a user request to MaaNTE task entries, controller requirements, task options, or owning sub-skills. The catalog is distilled from `assets/resource/tasks/*.json`, `assets/interface.json`, and task introduction docs at the source snapshot.

## Controller Legend

- `Any`: no task-level controller restriction; actual runtime may still need a game window, resources, and a suitable MaaFramework controller.
- `Win32`: background SendMessage-style controller.
- `Win32-Front`: foreground/seize controller; several tasks require it because they depend on active input, camera/UI behavior, or game focus.

## Task Families

| Task file | Task name(s) | Entry node(s) | Controller | Owning sub-skill | Notes |
| --- | --- | --- | --- | --- | --- |
| `Fish.json` | `Fish`, `FishNew` | `FishEntrance`, `FishNewEntrance` | Any | `gameplay-tasks` + `navigation-realtime` for auto navigation | Old and new fishing flows, auto sell, auto buy bait, new route navigation. |
| `MakeCoffee.json` | `MakeCoffee` | `AutoMakeCoffee` | `Win32-Front` | `gameplay-tasks` | Python custom action loops coffee-making rounds. |
| `MakeCoffeeLite.json` | `MakeCoffeeLite` | `AutoMakeCoffeeLiteEntrance` | `Win32-Front` | `gameplay-tasks` | Lightweight coffee flow with timeout/count settings. |
| `ClaimRewards.json` | `ClaimRewards` | `ClaimRewardsEntrance` | `Win32`, `Win32-Front` | `gameplay-tasks` | Activity and battle-pass reward toggles. |
| `FountainCheckin.json` | `FountainCheckin` | `FountainCheckinEntrance` | `Win32-Front` | `gameplay-tasks` + `navigation-realtime` | Uses teleport distance check, local route navigation, and fountain interaction pipeline. |
| `WithdrawMoney.json` | `WithdrawMoney` | `WithdrawMoneyEntrance` | `Win32`, `Win32-Front` | `gameplay-tasks` | City-tycoon income collection, optional product choice and restock. |
| `Furniture.json` | `Furniture` | `FurnitureEntrance` | `Win32-Front` | `gameplay-tasks` | Chooses up to six apartments and claims furniture/empowerment items. |
| `BidKing.json` | `BidKing` | `BidKingEntrance` | `Win32-Front` | `gameplay-tasks` | Auction minigame loop with fixed bid/skip recognition. |
| `PinkPawHeist.json` | `PinkPawHeist` | `PinkPawHeist_Main` | `Win32-Front` | `gameplay-tasks` + `media-minigames` for combat/input timing | Multi-scheme heist automation with route profiles, recovery, resize option, and stop-task modal warning. |
| `RealTime.json` | `RealTime` | `RealTimeTaskMain` | `Win32-Front` | `navigation-realtime` | Continuous loop for auto loot, skip story, and configured auto teleport checks. |
| `OnlineMapNavigation.json` | `OnlineMapNavigation` | `OnlineMapNavigation` | Any | `navigation-realtime` | WebSocket state broadcast and route ingestion on default port 14514. |
| `SoundDodge.json` | `SoundDodge` | `SoundDodgeMain` | `Win32-Front` | `media-minigames` | Audio loopback dodge/counter thresholds and mode switch. |
| `Rhythm.json` | `Rhythm` | `RhythmEntrance` | Any | `media-minigames` | Song selection, auto repeat, target FPS, drum template scheduler. |
| `AutoPiano.json` | `AutoPiano` | `AutoPiano` | Any in task JSON, Windows input in implementation | `media-minigames` | MIDI file, speed, transpose; low-level keyboard bridge is Windows-specific. |
| `Tetris.json` | `Tetris` | `TetrisEntrance` | Any | `media-minigames` | Tetris AI, repeat modes, vitality checking, optional speed drop. |
| `BagelSpam.json` | `BagelSpam` | `BagelSpamEntrance` | `Win32-Front` | `media-minigames` | Camera/photo flow, preset or OpenAI-compatible LLM generated title/body, publish-count limit. |
| `AutoFScroll.json` | `AutoFScroll` | `AutoFScroll` | Any | `media-minigames` | Holds F and scrolls for quick pickup; requires user-triggered start context. |
| `AutonomousDrivingDataset.json` | `AutonomousDrivingDatasetCollection` | `AutonomousDrivingDatasetRecorder` | Any but Windows key-state logic | `navigation-realtime` | Records screenshot/key-label sequences for driving data. |
| `SyncCharacterAbilityCityAbility.json` | `SyncCharacterAbilityCityAbilityNextCharacter` | `SyncCharacterAbilityCityAbilityEntrance` | `Win32-Front` | `gameplay-tasks` + `custom-actions` | Scans character list, OCR/template matches names, stores city ability levels in config. |
| `Touch.json` | `Touch` | `TouchDetect` | Any | `gameplay-tasks` | Simple pet/touch interaction loop with configurable delays. |
| `WitchDivination.json` | `WitchDivination` | `WitchDivinationEntrance` | `Win32-Front` | `gameplay-tasks` | Pipeline-only divination/chat/shuffle workflow. |
| `TestMovement.json` | `[测试] 视角转向`, `[测试] 前进`, `[测试] 后退` | `TestTurnEntry`, `TestMoveForwardEntry`, `TestMoveBackwardEntry` | Any | `navigation-realtime` | Developer movement/controller tests. |
| `LocalRouteNavigationMemoryTest.json` | `LocalRouteNavigationMemoryTest` | `LocalRouteNavigationMemoryTest` | Any but live route/game required | `navigation-realtime` | Repeated local route navigation segment test. |
| preset files | `AFK`, `FullDaily`, `QuickDaily`, `RealtimeAssistance` | Preset-defined | Depends on included tasks | `gameplay-tasks` | Composite task groups; inspect actual preset JSON before changing assumptions. |

## High-Value Options by Workflow

### Fishing

- `FishLoopInfinite`: rewires old fishing nodes back to `FishLoopStart` for infinite looping.
- `FishNumber`: overrides `FishGameStart.custom_action_param.count`.
- `FishSellAuto`: toggles old `AutoSellFish` and new `FishNewOpenFishMaster` branches.
- `FishBuyBaitAuto`: toggles bait buying branches and exposes `FishBaitThreshold`.
- `FishNewAutoNavi`: enables `FishNaviEntrance`; route selection lives in `Fish/FishNavi/FishNavi.json`.

### Daily and City-Tycoon

- `ClaimRewardsActivity`, `ClaimRewardsBattlePass`: independent reward toggles.
- `Restock`: enables or disables the city-tycoon restock branch after income withdrawal.
- `ChooseProduct`: enables product-list entry and `withdraw_money_choose_item` selection.
- Furniture apartment switches independently enable each property branch.

### Pink Paw Heist

- `PinkPawHeist_Loop` and `PinkPawHeist_LoopCount` decide infinite or bounded loops.
- `PinkPawHeist_Scheme` selects Core1, Core2, or Core3 and also configures recovery runner keys.
- Core3 exposes route/avoidance/early-extract sub-options. Its description notes game settings, role positions, frame-rate expectations, camera settings, and revive-item requirements.
- `PinkPawHeist_AutoResizeGameWindow` defaults on; disabling it requires the user to keep the game at 1280×720.

### Navigation and Realtime

- `OnlineMapNavigationSettings`: `port`, `tolerance`, `frame_interval`.
- `OnlineMapNavigationPositionBackend`: `auto`, `coordinate`, `map`.
- `OnlineMapNavigationAngleBackend`: `auto`, `directml`, `cpu`.
- `OnlineMapNavigationDebug`: OpenCV/log debugging; not for ordinary runtime.
- `RealTimeCheckInterval`: sets the continuous loop delay.

### Media and Minigames

- `SoundDodgeEnable`, `SoundDodgeAllAttacks`, `SoundDodgeThreshold`, `SoundCounterThreshold` configure audio trigger behavior.
- Rhythm options cover auto song selection, fixed/max repeat, repeat count, and target FPS.
- AutoPiano accepts MIDI path, speed, and transpose; implementation also supports `key_mode`, `tracks`, and `out_of_range_mode` through custom parameters.
- BagelSpam has optional photo capture, preset vs LLM text mode, LLM API configuration, and publish count.

## Catalog Maintenance Tips

- New task files must be imported by `assets/interface.json`; otherwise MaaFramework will not load them.
- Keep task `entry` values aligned with actual Pipeline node keys.
- Controller restrictions should match implementation requirements; do not assume `Any` means background-safe.
- If an option writes `pipeline_override`, verify the target node name and field shape after edits. The helper `scripts/inspect_task_catalog.py` catches basic missing imports and summarizes task metadata.
