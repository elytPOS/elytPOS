# 🎨 Appearance Themes

elytPOS supports a wide variety of professional color schemes to match your workspace and preferences. All themes are designed with high contrast and accessibility in mind.

## 🌟 Available Themes

| Theme | Description |
| :--- | :--- |
| **Mocha** | The default Catppuccin-inspired dark theme. Soft and balanced. |
| **Latte** | A clean, high-contrast light theme for bright environments. |
| **Nord** | Arctic-inspired, using cool blues and frosty tones. |
| **Dracula** | The classic vibrant dark theme for high-energy productivity. |
| **Amoled** | Pure black background for OLED displays and maximum power saving. |
| **Emerald** | A deep forest-green theme for a calming retail experience. |
| **Tokyo Night** | Modern dark theme inspired by the neon lights of Tokyo. |
| **Gruvbox** | Retro-inspired "retro groove" with warm, earthy colors. |
| **One Dark** | Based on the popular Atom editor palette. Clean and professional. |
| **Rose Pine** | Sophisticated dark theme with ethereal, muted tones. |
| **Solarized Dark** | Based on precision color theory for long-term eye comfort. |
| **Everforest** | A pleasant and comfortable green-tinted dark theme. |
| **Frappe** | A slightly lighter, more "milky" Catppuccin variant. |
| **Monokai** | The legendary vibrant theme with high-contrast colors. |
| **Synthwave 84** | Retro-futuristic theme with glowing neons and deep purples. |
| **Night Owl** | Fine-tuned for nighttime coding and visual clarity. |

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
