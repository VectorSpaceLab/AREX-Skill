# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `parse_time` gives a surprising span or point | The input still contains noise or ambiguous modifiers | Clean the string first, then adjust `ret_future`, `lunar_date`, or `time_base`.
| `phone_location` returns `unknown` for a mobile number | The phone regex needs a non-digit boundary before the number | Call it on the surrounding text, or make sure the number is not glued to neighboring digits.
| `parse_id_card` returns `None` | The ID number is invalid or the region code is not supported | Use a valid 18-digit mainland ID and confirm the administrative code exists in the dictionary.
| `parse_motor_vehicle_licence_plate` returns `None` | The plate is not a supported mainland plate format | Check that the plate matches the regular civilian or new-energy patterns.
| `idiom_solitaire` says `can not find next` | The dictionary has no unused follow-up idiom for the chosen matching rule | Relax `same_tone`, switch `same_pinyin`, or restart the game.
| `pinyin` / `char_radical` returns placeholder values | The character or token is missing from the packaged lookup data | Accept the placeholder or extend the packaged dictionaries before refreshing the skill.
