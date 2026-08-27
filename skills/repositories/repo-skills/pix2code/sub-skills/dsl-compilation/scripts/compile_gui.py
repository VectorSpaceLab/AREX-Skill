#!/usr/bin/env python3
"""Self-contained pix2code DSL compiler for web, Android, and iOS outputs.

Examples:
    python compile_gui.py --platform web --input screen.gui --output screen.html --seed 7
    python compile_gui.py --platform android --input screen.gui
"""

import argparse
import os
import random
import string
import sys

WEB = {
    "opening-tag": "{",
    "closing-tag": "}",
    "body": "<html>\n  <header>\n    <meta charset=\"utf-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n    <link rel=\"stylesheet\" href=\"https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css\">\n<style>\n.header{margin:20px 0}nav ul.nav-pills li{background-color:#333;border-radius:4px;margin-right:10px}.col-lg-3{width:24%;margin-right:1.333333%}.col-lg-6{width:49%;margin-right:2%}.col-lg-12,.col-lg-3,.col-lg-6{margin-bottom:20px;border-radius:6px;background-color:#f5f5f5;padding:20px}.row .col-lg-3:last-child,.row .col-lg-6:last-child{margin-right:0}footer{padding:20px 0;text-align:center;border-top:1px solid #bbb}\n</style>\n    <title>Scaffold</title>\n  </header>\n  <body>\n    <main class=\"container\">\n      {}\n      <footer class=\"footer\">\n        <p>&copy; Tony Beltramelli 2017</p>\n      </footer>\n    </main>\n  </body>\n</html>\n",
    "header": "<div class=\"header clearfix\">\n  <nav>\n    <ul class=\"nav nav-pills pull-left\">\n      {}\n    </ul>\n  </nav>\n</div>\n",
    "btn-active": "<li class=\"active\"><a href=\"#\">[]</a></li>\n",
    "btn-inactive": "<li><a href=\"#\">[]</a></li>\n",
    "row": "<div class=\"row\">{}</div>\n",
    "single": "<div class=\"col-lg-12\">\n{}\n</div>\n",
    "double": "<div class=\"col-lg-6\">\n{}\n</div>\n",
    "quadruple": "<div class=\"col-lg-3\">\n{}\n</div>\n",
    "btn-green": "<a class=\"btn btn-success\" href=\"#\" role=\"button\">[]</a>\n",
    "btn-orange": "<a class=\"btn btn-warning\" href=\"#\" role=\"button\">[]</a>\n",
    "btn-red": "<a class=\"btn btn-danger\" href=\"#\" role=\"button\">[]</a>",
    "big-title": "<h2>[]</h2>",
    "small-title": "<h4>[]</h4>",
    "text": "<p>[]</p>\n",
}

ANDROID = {
    "opening-tag": "{", "closing-tag": "}",
    "body": "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<LinearLayout\n    xmlns:android=\"http://schemas.android.com/apk/res/android\"\n    xmlns:app=\"http://schemas.android.com/apk/res-auto\"\n    xmlns:tools=\"http://schemas.android.com/tools\"\n    android:id=\"@+id/container\"\n    android:layout_width=\"match_parent\"\n    android:layout_height=\"match_parent\"\n    android:orientation=\"vertical\"\n    tools:context=\"com.tonybeltramelli.android_gui.MainActivity\">\n    {}\n</LinearLayout>\n",
    "stack": "<FrameLayout android:id=\"@+id/content\" android:layout_width=\"match_parent\" android:layout_height=\"match_parent\" android:layout_weight=\"1\" android:padding=\"10dp\">\n    <LinearLayout android:layout_width=\"match_parent\" android:layout_height=\"match_parent\" android:orientation=\"vertical\">\n        {}\n    </LinearLayout>\n</FrameLayout>",
    "row": "<LinearLayout android:layout_width=\"match_parent\" android:layout_height=\"wrap_content\" android:orientation=\"horizontal\" android:paddingTop=\"10dp\" android:paddingBottom=\"10dp\" android:weightSum=\"1\">\n{}\n</LinearLayout>",
    "label": "<TextView android:id=\"@+id/[ID]\" android:layout_width=\"wrap_content\" android:layout_height=\"wrap_content\" android:text=\"[TEXT]\" android:textAppearance=\"@style/TextAppearance.AppCompat.Body2\"/>\n",
    "btn": "<Button android:id=\"@+id/[ID]\" android:layout_width=\"wrap_content\" android:layout_height=\"wrap_content\" android:text=\"[TEXT]\"/>",
    "slider": "<SeekBar android:id=\"@+id/[ID]\" style=\"@style/Widget.AppCompat.SeekBar.Discrete\" android:layout_width=\"wrap_content\" android:layout_height=\"wrap_content\" android:layout_weight=\"0.9\" android:max=\"10\" android:progress=\"5\"/>",
    "check": "<CheckBox android:id=\"@+id/[ID]\" android:layout_width=\"wrap_content\" android:layout_height=\"wrap_content\" android:paddingRight=\"10dp\" android:text=\"[TEXT]\"/>",
    "radio": "<RadioButton android:id=\"@+id/[ID]\" android:layout_width=\"wrap_content\" android:layout_height=\"wrap_content\" android:paddingRight=\"10dp\" android:text=\"[TEXT]\"/>",
    "switch": "<Switch android:id=\"@+id/[ID]\" android:layout_width=\"wrap_content\" android:layout_height=\"wrap_content\" android:paddingRight=\"10dp\" android:text=\"[TEXT]\"/>",
    "footer": "<LinearLayout android:layout_width=\"match_parent\" android:layout_height=\"wrap_content\" android:orientation=\"horizontal\" android:weightSum=\"1\">\n    {}\n</LinearLayout>",
    "btn-home": "<Button android:id=\"@+id/[ID]\" android:layout_width=\"wrap_content\" android:layout_height=\"wrap_content\" android:background=\"#0ffffff\" android:layout_weight=\"1\" android:drawableBottom=\"@drawable/ic_home_black_24dp\" android:text=\"\"/>",
    "btn-dashboard": "<Button android:id=\"@+id/[ID]\" android:layout_width=\"wrap_content\" android:layout_height=\"wrap_content\" android:background=\"#0ffffff\" android:layout_weight=\"1\" android:drawableBottom=\"@drawable/ic_dashboard_black_24dp\" android:text=\"\"/>",
    "btn-notifications": "<Button android:id=\"@+id/[ID]\" android:layout_width=\"wrap_content\" android:layout_height=\"wrap_content\" android:background=\"#0ffffff\" android:layout_weight=\"1\" android:drawableBottom=\"@drawable/ic_notifications_black_24dp\" android:text=\"\"/>",
    "btn-search": "<Button android:id=\"@+id/[ID]\" android:layout_width=\"wrap_content\" android:layout_height=\"wrap_content\" android:background=\"#0ffffff\" android:layout_weight=\"1\" android:drawableBottom=\"?android:attr/actionModeWebSearchDrawable\" android:text=\"\"/>",
}

IOS = {
    "opening-tag": "{", "closing-tag": "}",
    "body": "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<document type=\"com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB\" version=\"3.0\" targetRuntime=\"iOS.CocoaTouch\">\n    <scenes>\n        <scene sceneID=\"qAw-JF-viq\">\n            <objects>\n                <viewController id=\"[ID]\" sceneMemberID=\"viewController\">\n                    <view key=\"view\" contentMode=\"center\" id=\"[ID]\">\n                        <subviews>\n                          {}\n                        </subviews>\n                    </view>\n                </viewController>\n            </objects>\n        </scene>\n    </scenes>\n</document>\n",
    "stack": "<stackView opaque=\"NO\" contentMode=\"center\" fixedFrame=\"YES\" axis=\"vertical\" alignment=\"center\" spacing=\"10\" translatesAutoresizingMaskIntoConstraints=\"NO\" id=\"[ID]\">\n    <subviews>\n        {}\n    </subviews>\n</stackView>",
    "row": "<view contentMode=\"center\" ambiguous=\"YES\" translatesAutoresizingMaskIntoConstraints=\"NO\" id=\"[ID]\">\n    <subviews>\n        <stackView opaque=\"NO\" contentMode=\"center\" fixedFrame=\"YES\" spacing=\"30\" translatesAutoresizingMaskIntoConstraints=\"NO\" id=\"[ID]\">\n            <subviews>\n                {}\n            </subviews>\n        </stackView>\n    </subviews>\n</view>",
    "img": "<imageView userInteractionEnabled=\"NO\" contentMode=\"scaleToFill\" id=\"[ID]\"/>",
    "label": "<label opaque=\"NO\" userInteractionEnabled=\"NO\" text=\"[TEXT]\" textAlignment=\"natural\" id=\"[ID]\"/>",
    "switch": "<switch opaque=\"NO\" contentMode=\"scaleToFill\" on=\"YES\" id=\"[ID]\"/>",
    "slider": "<slider opaque=\"NO\" value=\"0.5\" minValue=\"0.0\" maxValue=\"1\" id=\"[ID]\"/>",
    "btn-add": "<button buttonType=\"contactAdd\" id=\"[ID]\"/>",
    "footer": "<tabBar contentMode=\"scaleToFill\" fixedFrame=\"YES\" id=\"[ID]\">\n    <items>\n        {}\n    </items>\n</tabBar>",
    "btn-search": "<tabBarItem systemItem=\"search\" id=\"[ID]\"/>",
    "btn-contact": "<tabBarItem systemItem=\"contacts\" id=\"[ID]\"/>",
    "btn-download": "<tabBarItem systemItem=\"downloads\" id=\"[ID]\"/>",
    "btn-more": "<tabBarItem systemItem=\"more\" id=\"[ID]\"/>",
}

MAPPINGS = {"web": WEB, "android": ANDROID, "ios": IOS}
EXTENSIONS = {"web": ".html", "android": ".xml", "ios": ".storyboard"}


class Node:
    def __init__(self, key, parent=None):
        self.key = key
        self.parent = parent
        self.children = []

    def render(self, mapping, rng):
        if self.key not in mapping:
            raise KeyError("Unknown token {!r} for selected platform".format(self.key))
        content = "".join(child.render(mapping, rng) for child in self.children)
        value = mapping[self.key]
        if content:
            value = value.replace("{}", content)
        value = fill_placeholders(self.key, value, rng)
        return value


def random_text(rng, length_text=10, space_number=1, with_upper_case=True):
    chars = [rng.choice(string.ascii_lowercase) for _ in range(length_text)]
    if chars and with_upper_case:
        chars[0] = chars[0].upper()
    used = set()
    while len(used) < space_number and length_text > 5:
        pos = rng.randint(2, length_text - 3)
        if pos in used:
            break
        chars[pos] = " "
        if with_upper_case and pos + 1 < len(chars):
            chars[pos + 1] = chars[pos + 1].upper()
        used.add(pos)
    return "".join(chars)


def random_ios_id(rng, length=10):
    chars = [rng.choice(string.digits + string.ascii_letters) for _ in range(length)]
    if length > 6:
        chars[3] = "-"
        chars[6] = "-"
    return "".join(chars)


def random_android_id(rng, length=10):
    return "".join(rng.choice(string.ascii_letters) for _ in range(length))


def fill_placeholders(key, value, rng):
    if "[]" in value:
        if "btn" in key:
            repl = random_text(rng)
        elif "title" in key:
            repl = random_text(rng, length_text=5, space_number=0)
        elif "text" in key:
            repl = random_text(rng, length_text=56, space_number=7, with_upper_case=False)
        else:
            repl = random_text(rng)
        value = value.replace("[]", repl)
    while "[TEXT]" in value:
        value = value.replace("[TEXT]", random_text(rng, length_text=6, space_number=0), 1)
    while "[ID]" in value:
        if "android:" in value or "@+id" in value:
            value = value.replace("[ID]", random_android_id(rng), 1)
        else:
            value = value.replace("[ID]", random_ios_id(rng), 1)
    return value


def parse_gui(text, mapping):
    root = Node("body")
    current = root
    stack = [root]
    for line_no, raw in enumerate(text.splitlines(), 1):
        token = raw.replace(" ", "").strip()
        if not token:
            continue
        if "{" in token:
            key = token.replace("{", "")
            if not key:
                raise ValueError("Line {} has an opening brace without a token".format(line_no))
            if key not in mapping:
                raise KeyError("Line {} unknown container token {!r}".format(line_no, key))
            node = Node(key, current)
            current.children.append(node)
            current = node
            stack.append(node)
        elif "}" in token:
            if len(stack) == 1:
                raise ValueError("Line {} has a closing brace without a matching opening token".format(line_no))
            stack.pop()
            current = stack[-1]
        else:
            for child_key in [part for part in token.split(",") if part]:
                if child_key not in mapping:
                    raise KeyError("Line {} unknown leaf token {!r}".format(line_no, child_key))
                current.children.append(Node(child_key, current))
    if len(stack) != 1:
        raise ValueError("Unclosed tokens: {}".format(", ".join(node.key for node in stack[1:])))
    return root


def default_output(input_path, platform):
    base, _ = os.path.splitext(input_path)
    return base + EXTENSIONS[platform]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compile a pix2code .gui DSL file into platform scaffold code.")
    parser.add_argument("--platform", choices=sorted(MAPPINGS), required=True)
    parser.add_argument("--input", required=True, help="Path to input .gui file")
    parser.add_argument("--output", help="Output path; defaults next to input with platform extension")
    parser.add_argument("--seed", type=int, default=1234, help="Seed for deterministic placeholder text and IDs")
    args = parser.parse_args(argv)

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()
    mapping = MAPPINGS[args.platform]
    root = parse_gui(text, mapping)
    out = args.output or default_output(args.input, args.platform)
    rendered = root.render(mapping, random.Random(args.seed))
    parent = os.path.dirname(os.path.abspath(out))
    if parent and not os.path.exists(parent):
        os.makedirs(parent)
    with open(out, "w", encoding="utf-8") as f:
        f.write(rendered)
    print("Wrote {}".format(out))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("ERROR: {}: {}".format(exc.__class__.__name__, exc), file=sys.stderr)
        raise SystemExit(2)
