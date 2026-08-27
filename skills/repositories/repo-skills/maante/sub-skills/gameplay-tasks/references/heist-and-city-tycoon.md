# Heist and City-Tycoon Workflows

## When To Read

Read this for PinkPaw Heist, WithdrawMoney, Furniture, city-tycoon menu navigation, product choice, reward logging, and character/city ability support data.

## PinkPaw Heist

Task: `PinkPawHeist`, entry `PinkPawHeist_Main`, controller `Win32-Front`.

Pipeline structure:

- Main loop: `PinkPawHeist_Main` → `PinkPawHeist_Loop` → `PinkPawHeist_CoreSequence`.
- Interaction and recovery: `PinkPawHeist_FindXiaoZhi`, `PinkPawHeist_RecoverXiaoZhi`, `PinkPawHeist_DetectXiaoZhi`, `PinkPawHeist_ReturnToEntranceAction`.
- Scheme dispatch: `PinkPawHeist_ExecuteScheme` routes to scheme-specific Python actions.
- Reward summary: reward logger action records/announces extracted rewards.

Options:

- Infinite loop defaults on; bounded mode exposes a loop count.
- Auto resize defaults on and targets 1280×720.
- Scheme choices:
  - Core1: older unstable route, runner key `3`.
  - Core2: higher-stability route with specific party requirements and 120 FPS recommendation.
  - Core3: default route adapted from ok-nte path, with party composition and early-extract options.

Operational constraints:

- Must run near 小吱 or rely on recovery to return to the entrance.
- User should configure a global stop hotkey before starting.
- Game settings such as movement-camera correction, lock camera recentering, lock mode, performance graphics, and frame-rate range matter for route timing.
- Core3 requires a revive item according to task option description.

Development notes:

- Heist code is timing-sensitive and control-heavy. Preserve stop checks and key/button release logic.
- Avoid replacing verified route timing with broad sleeps; if route drift occurs, inspect current scheme constants and recovery branches.
- Use `PinkPawHeist_AutoResizeGameWindowConfig.attach.auto_resize_game_window` when changing resize behavior.
- Treat fixed team-slot assumptions as user-facing configuration, not hidden implementation detail.

## Withdraw Money and Restock

Task: `WithdrawMoney`, entry `WithdrawMoneyEntrance`, controller `Win32` or `Win32-Front`.

Behavior:

1. Enter city-tycoon menu through SceneManager.
2. Click 一咖舍.
3. Withdraw earnings and confirm.
4. Optional: enter product list and run `withdraw_money_choose_item`.
5. Optional: restock 24h, handle stock-full prompt, delivery confirmation, and exit.

Options:

- `Restock`: toggles the `点击补货` branch.
- `ChooseProduct`: toggles `WithdrawMoneyEnterItemList` and Python item choice.

Failure surfaces:

- OCR mismatch for 一咖舍, 提取收益, 商品列表, 补货, 24小时, or confirm buttons.
- Product-list UI changed but the Python choice action still assumes old screen state.
- Controller mismatch if background mode fails to click/long-press correctly.

## Furniture

Task: `Furniture`, entry `FurnitureEntrance`, controller `Win32-Front`.

Behavior:

- Enter city-tycoon property screen.
- Iterate over apartment branches with `max_hit: 1` per property.
- For purchased apartments, teleport home, click furniture button with `alt_click`, open enhancement overview, swipe/claim rewards, then return to the next property.
- For unpurchased apartments, `FurnitureGotoBuy` logs/focuses that it is skipped.

Apartment option switches independently enable:

- Wiener Apartments.
- Eden Apartments.
- Skyview Halls.
- Golden Capital.
- Tian Jun.
- Fenglin Villa.

Development notes:

- The pipeline uses anchors (`FurnitureNext`, `FurnitureApartmentsNext`) to advance property selection. Preserve anchor behavior when adding properties.
- `furniture_choose_property` owns property selection details. Do not duplicate it with blind coordinates in Pipeline without a reason.

## Rewards

`ClaimRewards` covers activity and battle-pass reward collection. The activity path enters the exploration-guide menu and page 2; the battle-pass path enters the battle-pass menu and collects experience/rewards. Keep the two option toggles independent.

## Character Ability Support Data

Character/city ability sync writes a JSON config consumed by other workflows that need ability levels. The storage manager validates skill0 as 0–5 and skill1 as 0–2 or -1. If you change character names, portrait templates, or OCR replacements, verify both the Pipeline recognition nodes and Python template-name mapping.
