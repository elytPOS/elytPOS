# 🎨 Appearance Themes

elytPOS supports a wide variety of professional color schemes to match your workspace and preferences. All themes are designed with high contrast and accessibility in mind.

## 🌟 Available Themes

| Theme | Description | Preview |
| :--- | :--- | :--- |
| **Mocha** | The default Catppuccin-inspired dark theme. Soft and balanced. | ![Mocha](screenshots/theme_mocha.png) |
| **Latte** | A clean, high-contrast light theme for bright environments. | ![Latte](screenshots/theme_latte.png) |
| **Nord** | Arctic-inspired, using cool blues and frosty tones. | ![Nord](screenshots/theme_nord.png) |
| **Dracula** | The classic vibrant dark theme for high-energy productivity. | ![Dracula](screenshots/theme_dracula.png) |
| **Amoled** | Pure black background for OLED displays and maximum power saving. | ![Amoled](screenshots/theme_amoled.png) |
| **Emerald** | A deep forest-green theme for a calming retail experience. | ![Emerald](screenshots/theme_emerald.png) |
| **Tokyo Night** | Modern dark theme inspired by the neon lights of Tokyo. | ![Tokyo Night](screenshots/theme_tokyo_night.png) |
| **Gruvbox** | Retro-inspired "retro groove" with warm, earthy colors. | ![Gruvbox](screenshots/theme_gruvbox.png) |
| **One Dark** | Based on the popular Atom editor palette. Clean and professional. | ![One Dark](screenshots/theme_one_dark.png) |
| **Rose Pine** | Sophisticated dark theme with ethereal, muted tones. | ![Rose Pine](screenshots/theme_rose_pine.png) |
| **Solarized Dark** | Based on precision color theory for long-term eye comfort. | ![Solarized Dark](screenshots/theme_solarized_dark.png) |
| **Everforest** | A pleasant and comfortable green-tinted dark theme. | ![Everforest](screenshots/theme_everforest.png) |
| **Frappe** | A slightly lighter, more "milky" Catppuccin variant. | ![Frappe](screenshots/theme_frappe.png) |
| **Monokai** | The legendary vibrant theme with high-contrast colors. | ![Monokai](screenshots/theme_monokai.png) |
| **Synthwave 84** | Retro-futuristic theme with glowing neons and deep purples. | ![Synthwave 84](screenshots/theme_synthwave84.png) |
| **Night Owl** | Fine-tuned for nighttime coding and visual clarity. | ![Night Owl](screenshots/theme_night_owl.png) |
| **Everforest Light** | A pleasant and comfortable green-tinted light theme. | ![Everforest Light](screenshots/theme_everforest_light.png) |
| **Gruvbox Light** | Retro-inspired earthy tones on a light background. | ![Gruvbox Light](screenshots/theme_gruvbox_light.png) |
| **Solarized Light** | Based on precision color theory for long-term eye comfort. | ![Solarized Light](screenshots/theme_solarized_light.png) |
| **One Light** | Clean, minimalist light theme based on Atom. | ![One Light](screenshots/theme_one_light.png) |

## 🚀 How to Change Themes

You can switch between themes instantly without restarting the application:

1. Go to the **Administration** menu in the top bar.
2. Select **Appearance Themes**.
3. Choose your desired color scheme.

The system will automatically:
- Update the entire interface colors.
- Change the window and splash icons to match the theme.
- Save your preference permanently in the database.

## 🛠️ Technical Details

Themes are defined using standard Qt Style Sheets (QSS) in `styles.py`. The application uses semantic naming (e.g., `setObjectName("title")`) to ensure all dialogs and widgets adapt dynamically when the theme is changed.