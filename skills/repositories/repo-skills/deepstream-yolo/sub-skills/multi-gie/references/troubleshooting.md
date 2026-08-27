# Multi-GIE troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Only one detector appears | The secondary GIE section is missing or the IDs still match the primary detector | Check the `secondary-gieN` section names, `gie-unique-id`, and `operate-on-gie-id` values |
| Engine loads from the wrong folder | The engine cache was left in the root directory | Move the engine back into the owning `gieN/` folder and update the config path |
| Plugin load fails | `YOLOLAYER_PLUGIN_VERSION` was not incremented in the copied library | Change the version number in each copied `yoloPlugins.h` and rebuild the library in that folder |
| Secondary detector returns no boxes | `operate-on-class-ids` is too restrictive or points at the wrong parent GIE | Loosen the class filter or fix the parent `gie-unique-id` |
| The app uses the wrong config file | The copied `gieN/` config path still points at the root template | Repoint each `config-file` entry to the matching copied config |

## Notes

- The multi-GIE path is a configuration and folder-layout problem first, not a model-export problem.
- If the user has not exported the models yet, send them back to the model-conversion sub-skill.
