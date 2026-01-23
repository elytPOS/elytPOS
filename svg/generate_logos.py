import os
import re

THEMES = {
    "mocha": {"bg": "#1e1e2e", "fg": "#ffffff", "accent": "#89b4fa", "is_light": False},
    "latte": {"bg": "#eff1f5", "fg": "#202030", "accent": "#0044cc", "is_light": True},
    "nord": {"bg": "#2e3440", "fg": "#eceff4", "accent": "#88c0d0", "is_light": False},
    "dracula": {
        "bg": "#282a36",
        "fg": "#f8f8f2",
        "accent": "#bd93f9",
        "is_light": False,
    },
    "amoled": {
        "bg": "#000000",
        "fg": "#ffffff",
        "accent": "#bb86fc",
        "is_light": False,
    },
    "emerald": {
        "bg": "#06201b",
        "fg": "#d1fae5",
        "accent": "#10b981",
        "is_light": False,
    },
    "tokyo_night": {
        "bg": "#1a1b26",
        "fg": "#c0caf5",
        "accent": "#7aa2f7",
        "is_light": False,
    },
    "gruvbox": {
        "bg": "#282828",
        "fg": "#ebdbb2",
        "accent": "#83a598",
        "is_light": False,
    },
    "one_dark": {
        "bg": "#282c34",
        "fg": "#abb2bf",
        "accent": "#61afef",
        "is_light": False,
    },
    "rose_pine": {
        "bg": "#191724",
        "fg": "#e0def4",
        "accent": "#ebbcba",
        "is_light": False,
    },
    "solarized_dark": {
        "bg": "#002b36",
        "fg": "#839496",
        "accent": "#268bd2",
        "is_light": False,
    },
    "everforest": {
        "bg": "#2d353b",
        "fg": "#d3c6aa",
        "accent": "#a7c080",
        "is_light": False,
    },
    "frappe": {
        "bg": "#303446",
        "fg": "#c6d0f5",
        "accent": "#8caaee",
        "is_light": False,
    },
    "monokai": {
        "bg": "#272822",
        "fg": "#f8f8f2",
        "accent": "#a6e22e",
        "is_light": False,
    },
    "synthwave84": {
        "bg": "#262335",
        "fg": "#ffffff",
        "accent": "#ff7edb",
        "is_light": False,
    },
    "night_owl": {
        "bg": "#011627",
        "fg": "#d6deeb",
        "accent": "#82aaff",
        "is_light": False,
    },
}


def generate_logos():
    # Paths are relative to the script location (the svg folder)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    original_path = os.path.join(base_dir, "original_logo.svg")

    if not os.path.exists(original_path):
        print(f"Error: {original_path} not found.")
        return

    with open(original_path, "r") as f:
        original_content = f.read()

    for theme_name, colors in THEMES.items():
        content = original_content

        if colors.get("is_light"):
            content = re.sub(r"fill:#1f1f2f", "fill:none", content)
        else:
            content = re.sub(r"fill:#1f1f2f", f"fill:{colors['bg']}", content)

        content = re.sub(r"fill:#89b4fa", f"fill:{colors['accent']}", content)
        content = re.sub(r"fill:#ffffff", f"fill:{colors['fg']}", content)

        output_path = os.path.join(base_dir, f"logo_{theme_name}.svg")
        with open(output_path, "w") as f:
            f.write(content)
        print(f"Generated {output_path}")


if __name__ == "__main__":
    generate_logos()
