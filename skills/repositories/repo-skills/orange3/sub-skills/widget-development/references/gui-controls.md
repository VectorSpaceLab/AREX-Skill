# GUI Controls Reference

`Orange.widgets.gui` wraps Qt widgets and binds them to attributes on the widget instance. Prefer these wrappers over raw Qt controls when the control mirrors a widget setting or runtime attribute, because the wrappers handle layout insertion, callbacks, synchronization, and `self.controls.<attribute>` access.

## Core binding model

Most control calls follow this shape:

```python
gui.control(parent, master, "attribute_name", ..., callback=some_method)
```

- `parent` is usually `self.controlArea`, `self.mainArea`, or a box created with `gui.widgetBox`, `gui.vBox`, or `gui.hBox`.
- `master` is usually `self`.
- The string attribute is synchronized both ways: changing the control updates `self.attribute_name`; assigning `self.attribute_name = value` updates the control front-end.
- Bound controls can be accessed as `self.controls.attribute_name`.
- A `callback` can be a callable or a list of callables. Avoid callbacks that directly assign the same controlled attribute in a loop.

Common keyword options across controls include `tooltip`, `disabled`, `addSpace`, `addToLayout`, `stretch`, `sizePolicy`, `box`, `label`, `labelWidth`, and `orientation`. Qt properties can generally be passed as keyword arguments when the underlying Qt widget has a matching setter.

## Containers and labels

Verified signatures:

```python
gui.widgetBox(widget, box=None, orientation=Qt.Vertical, margin=None, spacing=None, **misc)
gui.vBox(*args, **kwargs)
gui.hBox(*args, **kwargs)
gui.separator(widget, width=None, height=None)
gui.rubber(widget)
gui.widgetLabel(widget, label="", labelWidth=None, **misc)
gui.label(widget, master, label, labelWidth=None, box=None, orientation=Qt.Vertical, **misc)
```

Patterns:

```python
info = gui.widgetBox(self.controlArea, "Info")
self.info_label = gui.widgetLabel(info, "No input yet.")

gui.separator(self.controlArea)
options = gui.widgetBox(self.controlArea, "Options")
gui.rubber(self.controlArea)
```

`gui.label` can render `%(<attribute>)s` placeholders from the master object, which is useful for compact status labels. For dynamic text that does not map to a master attribute, store the returned `QLabel` from `gui.widgetLabel`.

## Text, numeric, and slider controls

Verified signatures:

```python
gui.lineEdit(widget, master, value, label=None, labelWidth=None,
             orientation=Qt.Vertical, box=None, callback=None, valueType=None,
             validator=None, controlWidth=None, callbackOnType=False,
             focusInCallback=None, **misc)

gui.spin(widget, master, value, minv, maxv, step=1, box=None, label=None,
         labelWidth=None, orientation=Qt.Horizontal, callback=None,
         controlWidth=None, callbackOnReturn=False, checked=None,
         checkCallback=None, posttext=None, disabled=False,
         alignment=Qt.AlignLeft, keyboardTracking=True, decimals=None,
         spinType=int, **misc)

gui.doubleSpin(widget, master, value, minv, maxv, step=1, ..., decimals=None, **misc)
gui.hSlider(widget, master, value, box=None, minValue=0, maxValue=10,
            step=1, callback=None, callback_finished=None, label=None,
            labelFormat=" %d", ticks=False, divideFactor=1.0,
            vertical=False, createLabel=True, width=None, intOnly=True, **misc)
```

Guidance:

- Use `lineEdit(..., valueType=int/float, validator=...)` when the stored attribute should be typed.
- For expensive recomputation, set `keyboardTracking=False` on spins and use a commit/apply button or `callbackOnReturn=True`.
- Use `posttext` for units and `labelWidth` to align related controls.
- Use `callback_finished` for sliders when the user should be able to drag without recomputing on every intermediate value.

## Choice, list, and boolean controls

Verified signatures:

```python
gui.checkBox(widget, master, value, label, box=None, callback=None,
             getwidget=False, id_=None, labelWidth=None,
             disables=None, stateWhenDisabled=None, **misc)

gui.comboBox(widget, master, value, box=None, label=None, labelWidth=None,
             orientation=Qt.Vertical, items=(), callback=None,
             sendSelectedValue=None, emptyString=None, editable=False,
             contentsLength=None, searchable=False, *, model=None,
             tooltips=None, **misc)

gui.radioButtonsInBox(widget, master, value, btnLabels=(), tooltips=None,
                      box=None, label=None, orientation=Qt.Vertical,
                      callback=None, **misc)

gui.listBox(widget, master, value=None, labels=None, box=None, callback=None,
            selectionMode=QListWidget.SingleSelection, enableDragDrop=False,
            dragDropCallback=None, dataValidityCallback=None, sizeHint=None, **misc)

gui.listView(widget, master, value=None, model=None, box=None, callback=None,
             sizeHint=None, *, viewType=ListViewWithSizeHint, **misc)
```

Patterns:

```python
mode = Setting(0)
feature_index = Setting(0)
selected_rows = Setting([])
choices = ["Fast", "Accurate"]

gui.comboBox(options, self, "mode", label="Mode:", items=self.choices,
             callback=self.settings_changed)
gui.checkBox(options, self, "auto_apply", "Apply automatically")
gui.radioButtonsInBox(options, self, "feature_index", ["First", "Best"],
                      box="Feature")
```

Use a model-backed combo box (`model=...`) for domain variables or other dynamic objects. If a combo stores variables that depend on input data, use `ContextSetting` and a context handler rather than a plain `Setting`.

## Buttons, auto-apply, and deferred commits

Verified signatures:

```python
gui.button(widget, master, label, callback=None, width=None, height=None,
           toggleButton=False, value="", default=False, autoDefault=True,
           buttonType=QPushButton, **misc)

gui.auto_apply(widget, master, value="auto_apply", **kwargs)
gui.auto_commit(widget, master, value, label, auto_label=None, box=False,
                checkbox_label=None, orientation=None, commit=None,
                callback=None, **misc)
gui.deferred(func)
```

Common pattern:

```python
auto_apply = Setting(True)

def commit(self):
    self.Outputs.result.send(self.result)

self.apply_button = gui.auto_apply(
    self.buttonsArea, self, "auto_apply", "Apply", commit=self.commit
)
```

If a widget exposes both manual and automatic updates, make callbacks mark the widget as outdated and call a deferred commit instead of recomputing repeatedly while controls are still changing.

## Tables and custom Qt controls

`gui.table(widget, rows=0, columns=0, selectionMode=-1, addToLayout=True)` creates a `QTableWidget` and inserts it into a layout. It is useful for small result summaries. For large/dynamic tabular views, prefer a Qt model/view and use `gui.listView`, `TableView`, or a custom `QAbstractItemModel`.

When raw Qt controls are necessary:

- Pass static Qt properties as keyword arguments to constructors where practical.
- Add controls to a parent layout explicitly.
- If the control mirrors a `Setting`, wire callbacks and initial state manually or wrap it with `connectControl` only when you understand Orange's control-front/control-back pattern.

## GUI testing tips

Use `Orange.widgets.tests.base.WidgetTest` and `Orange.widgets.tests.utils.simulate` for controls:

```python
self.widget = self.create_widget(OWExample)
self.widget.controls.mode.setCurrentIndex(1)
self.process_events()
self.assertEqual(self.widget.mode, 1)
```

For signal-driven widgets, assert both control state and outputs:

```python
self.send_signal(self.widget.Inputs.data, data)
self.wait_until_finished()
self.assertIsNotNone(self.get_output(self.widget.Outputs.result))
```

If a control value affects a context setting, also test `settingsHandler.pack_data(widget)` followed by `create_widget(OWExample, stored_settings=settings)` and a new input domain.
