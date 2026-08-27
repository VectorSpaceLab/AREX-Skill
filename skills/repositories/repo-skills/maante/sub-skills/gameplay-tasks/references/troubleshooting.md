# Gameplay Task Troubleshooting

## Fishing

Symptoms:

- The flow cannot enter fishing preparation/game.
- Bait selection fails.
- Auto buy/sell branches never trigger.
- FishNew loops back through the error restart anchor.

Likely causes:

- Not near a fishing interaction prompt or auto-navigation is disabled/misrouted.
- `FishSceneOnFishGame` composite check fails because bait/hook button templates changed.
- Bait threshold too high; task option can lower it down to 0.4 in current config.
- Month-card or other popups interrupt overnight loops.
- Fish inventory/currency state is not covered by the current branch order.

Fix approach:

- Inspect `FishScene*` status nodes before modifying the minigame action.
- Add/adjust popup/loading branches rather than increasing `max_hit`.
- Verify `FishSellAuto` and `FishBuyBaitAuto` enable/disable both old and new nodes.

## Coffee

Symptoms:

- Cannot find “开始营业”.
- Coffee task enters shop but Python action exits early.
- Loop count ignored.

Checks:

- `MakeCoffeeLoopTime` should override `AutoMakeCoffee.custom_action_param.count`.
- OCR ROI for the start button is around the lower-right button region.
- If using Lite mode, inspect the Lite-specific task and Pipeline entry; do not assume it shares every node with `MakeCoffee`.

## Rewards/Fountain

Symptoms:

- ClaimRewards enters wrong menu or misses page tabs.
- FountainCheckin fails before reaching the fountain.

Checks:

- For rewards, verify SceneManager public menu entries and page tab templates.
- For fountain, split diagnosis into teleport-required check, local route navigation, and fountain interaction OCR.
- Fountain route/navigation issues belong to the navigation sub-skill; fountain button/wish/skip-story OCR issues belong here.

## City-Tycoon Income and Furniture

Symptoms:

- WithdrawMoney skips restock/product choice unexpectedly.
- Furniture stops after one property.
- Unpurchased apartments cause loops.

Checks:

- Confirm task options enabled the intended branches.
- Check anchor behavior in Furniture property iteration.
- Confirm `FurnitureGotoBuy` routes back to the apartment anchor instead of treating unpurchased property as failure.
- Product choice runs Python; use custom-actions guidance for `withdraw_money_choose_item` internals.

## PinkPaw Heist

Symptoms:

- Cannot find 小吱.
- Enters heist but route drifts.
- Combat loops forever or misses monsters.
- Controls remain held after stop/failure.

Likely causes:

- Start position or recovery scheme does not match selected Core route.
- Game resolution/FPS/camera settings differ from task description.
- Required party composition or role slot is wrong.
- Color/OCR checks for gates, interact prompts, monsters, or evacuation no longer match UI.
- Long route action missed `tasker.stopping` or control release on an exception.

Fix approach:

- Do not replace scheme logic with blind retry loops.
- Preserve or improve stop checks and release controls first.
- Use single-run bounded verification before long farming loops.
- Keep option descriptions aligned with the actual scheme-specific parameters.

## Character Ability Sync

Symptoms:

- Character names are wrong or missing.
- Skill level output has invalid values.
- The loop never detects end of character list.

Checks:

- TemplateMatch portrait mapping takes priority at high confidence.
- OCR name replacement rules are in the Pipeline node.
- Skill0 range is 0–5; skill1 range is 0–2 or -1.
- Consecutive no-change and max-iteration limits prevent infinite scanning; preserve them.
