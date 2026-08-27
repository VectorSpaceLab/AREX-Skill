# RoboCasa kitchen task catalog

## What is registered

The public task documentation describes **65 atomic tasks** and **300 composite
tasks**. The installed RoboCasa 1.0.1 package exposes 374 registered kitchen
environment classes through the kitchen metaclass. The difference is expected:
registration also contains base/helper classes used to build or support the
public task set. Use the documented task names and the registered class names
as the runtime contract; do not infer availability from a directory count.

`docs/composite_tasks/task_attributes.json` contains 365 task records: 65 with
`activity: "Atomic"` and 300 with composite activity names. The generated
atomic index groups the public atomic tasks by fixture source file.

## Atomic tasks by owned fixture/module

The following is the 65-task public catalog, grouped by the source module that
owns the configuration and success predicate:

- **Blender (3):** `OpenBlenderLid`, `CloseBlenderLid`, `TurnOnBlender`.
- **Coffee machine (3):** `CoffeeServeMug`, `CoffeeSetupMug`,
  `StartCoffeeMachine`.
- **Doors (12):** `OpenCabinet`, `CloseCabinet`, `OpenMicrowave`,
  `CloseMicrowave`, `OpenFridge`, `CloseFridge`, `OpenOven`, `CloseOven`,
  `OpenDishwasher`, `CloseDishwasher`, `OpenToasterOvenDoor`,
  `CloseToasterOvenDoor`.
- **Drawer (5):** `OpenDrawer`, `CloseDrawer`, `OpenFridgeDrawer`,
  `CloseFridgeDrawer`, `SlideDishwasherRack`.
- **Electric kettle (3):** `TurnOnElectricKettle`, `OpenElectricKettleLid`,
  `CloseElectricKettleLid`.
- **Microwave (2):** `TurnOnMicrowave`, `TurnOffMicrowave`.
- **Navigation (1):** `NavigateKitchen`.
- **Oven (2):** `PreheatOven`, `SlideOvenRack`.
- **Pick/place (21):** `PickPlaceCounterToCabinet`,
  `PickPlaceCabinetToCounter`, `PickPlaceCounterToSink`,
  `PickPlaceSinkToCounter`, `PickPlaceCounterToMicrowave`,
  `PickPlaceMicrowaveToCounter`, `PickPlaceCounterToOven`,
  `PickPlaceCounterToToasterOven`, `PickPlaceToasterOvenToCounter`,
  `PickPlaceToasterToCounter`, `PickPlaceCounterToStandMixer`,
  `PickPlaceCounterToBlender`, `PickPlaceCounterToStove`,
  `PickPlaceStoveToCounter`, `PickPlaceCounterToDrawer`,
  `PickPlaceDrawerToCounter`, `PickPlaceFridgeShelfToDrawer`,
  `PickPlaceFridgeDrawerToShelf`, `CheesyBread`, `MakeIcedCoffee`,
  `PackDessert`.
- **Sink (4):** `TurnOnSinkFaucet`, `TurnOffSinkFaucet`, `TurnSinkSpout`,
  `AdjustWaterTemperature`.
- **Stand mixer (2):** `OpenStandMixerHead`, `CloseStandMixerHead`.
- **Stove (3):** `TurnOnStove`, `TurnOffStove`, `LowerHeat`.
- **Toaster (1):** `TurnOnToaster`.
- **Toaster oven (3):** `TurnOnToasterOven`, `AdjustToasterOvenTemperature`,
  `SlideToasterOvenRack`.

When a requested operation is a single interaction with one appliance or one
transfer, start with the atomic catalog. Most atomic classes expose task-
specific constructor arguments such as `obj_groups`, `cab_id`, or
`enable_fixtures`; inspect the class before passing overrides.

## Composite activities

The 300 composite tasks are grouped into 60 activity folders. The current
activity headings are:

`Adding Ice to Beverages`, `Arranging Buffet`, `Arranging Cabinets`,
`Arranging Condiments`, `Baking`, `Boiling`, `Brewing`, `Broiling Fish`,
`Chopping Food`, `Chopping Vegetables`, `Cleaning Appliances`, `Cleaning Sink`,
`Clearing Table`, `Defrosting Food`, `Filling Serving Dishes`, `Frying`,
`Garnishing Dishes`, `Loading Dishwasher`, `Loading Fridge`, `Making Juice`,
`Making Salads`, `Making Smoothies`, `Making Tea`, `Making Toast`,
`Managing Freezer Space`, `Measuring Ingredients`, `Meat Preparation`,
`Microwaving Food`, `Mixing Ingredients`, `Mixing and Blending`,
`Organizing Dishes and Containers`, `Organizing Recycling`,
`Organizing Utensils`, `Packing Lunches`, `Plating Food`, `Portioning Meals`,
`Preparing Hot Chocolate`, `Preparing Marinade`, `Preparing Sandwiches`,
`Reheating Food`, `Restocking Supplies`, `Sanitizing Cutting Board`,
`Sanitizing Surface`, `Sauteing Vegetables`, `Seasoning Food`, `Serving Beverages`,
`Serving Food`, `Setting the Table`, `Simmering Sauces`, `Slicing Meat`,
`Slow Cooking`, `Snack Preparation`, `Sorting Ingredients`, `Steaming Food`,
`Steaming Vegetables`, `Storing Leftovers`, `Tidying Cabinets and Drawers`,
`Toasting Bread`, `Washing Dishes`, and `Washing Fruits and Vegetables`.

The activity heading is a catalog concept; the Python folder uses a normalized
snake-case name. Examples of useful composite classes are `PrepareCoffee`,
`PlaceEqualIceCubes`, `RinseSinkBasin`, and `GatherTableware`. Composite code
usually adds multiple objects, records references in `fixture_refs` or episode
metadata, initializes appliance state in `_setup_scene`/`_reset_internal`,
and checks a multi-stage condition in `_check_success`.

## Choosing and adapting a task

1. Search the task metadata by exact class name and read its natural-language
   description and `num_subtasks` field.
2. Read the corresponding atomic or composite Python class. The class is the
   authoritative source for fixture requirements, object groups, placement
   sizes, exclusions, and success semantics.
3. Check layout exclusions and fixture availability before choosing a split.
   Tasks that require a dining counter, island, oven, freezer, auxiliary lid,
   or a particular appliance may exclude layouts or need `enable_fixtures`.
4. Keep task semantics separate from scene randomization. A different style or
   layout should not silently change the object role, receptacle, or success
   predicate.

Do not route generic environment construction or rollout requests through this
catalog. It supplies the task class and the configuration arguments that the
simulation workflow consumes.
