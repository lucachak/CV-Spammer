# 💎 Catho Invincible Stealth Scraper & Automated Apply

An industrial-grade, anti-bot-evading automated job candidate scraper designed specifically for **Catho**. Built using **Selenium 4 (Python)**, **Chrome DevTools Protocol (CDP) fakes**, and **PyAutoGUI keyboard engines**, this tool runs securely under Linux (X11 & Wayland) to process job applications dynamically across pages, bypassing translation popups, initial popups, "CV Sent" overlays, and "Killer Question" questionnaires completely!

---

## ✨ Key Capabilities

*   **🛡️ CDP Anti-Bot Evasions (Stealth Mode)**: Overrides `navigator.webdriver` to `undefined`, injects standard desktop plug-in listings, fakes user languages (`pt-BR`, `pt`, `en-US`), and spoofs standard `Intel HD Graphics 620` WebGL rendering signatures to stay fully invisible to anti-scraping scanners.
*   **📂 Workspace Persistent Session Loader**: Dynamically maps Chrome's `Default` user-data directory from the workspace. This loads your active login session automatically, bypassing MFA and login forms.
*   **⌨️ PyAutoGUI Keyboard Evasion**: Simulates a human delay (1.0s to 3.0s) upon initial Catho tile clicking and injects 3 to 7 physical `ESC` keystrokes to close Chrome's initial popups or translate prompts.
*   **🚨 Invincible Popup Evasion**: Checks for and immediately closes blocking dialogs (such as *"Seu CV já foi enviado"* or *"Questionário da vaga (Killer Questions)"*). If standard clicks are intercepted, the script catches the error, clears the viewport using high-precision selectors (`span.i_close`, `button[data-modal-close]`), and recovers using fallback JS click injections.
*   **🔗 Dynamic Pagination Query Formatting**: Dynamically inspects the `REAL_BASE_URL` search query parameters. If parameters already exist (e.g., `?order=dataAtualizacao`), the crawler seamlessly paginates using `&page=N` instead of breaking URLs with `?page=N`.
*   **⚙️ Externalized `.env` Orchestration**: Control target URLs, credentials, pagination thresholds, active modes (`TEST_MODE`), and human interaction limits safely from the [.env](file:///.env) file.

---

## 📁 Workspace Structure

```text
.
├── click_button.py        # Main execution scraper and automated candidate engine
├── .env                  # External configuration variables (Credentials, modes, limits)
├── requirements.txt      # Required Python dependencies
├── setup.sh              # Automated bash installer (Creates virtual env, configures display)
└── README.md             # Complete project guide and reference documentation
```

---

## ⚡ Installation & Quick Start

### 1. Execute the Installer
Run the automated `setup.sh` script to set up your virtual environment, update dependencies, and configure environment templates:
```bash
./setup.sh
```

### 2. Configure PyAutoGUI Display Permissions (Linux)
Since PyAutoGUI interacts with the physical keyboard, Linux display servers (X11/Wayland) require authorization permissions:
```bash
# Export active display session authority
export XAUTHORITY=~/.Xauthority
touch ~/.Xauthority

# For Wayland environments, ensure utility is installed:
sudo pacman -S ydotool
```

### 3. Customize Configurations
Open **[.env](file:///.env)** and configure your target search URL, pagination caps, and credentials:
```ini
email=[EMAIL_ADDRESS]
passwd=YourSecurePassword123!

# --- SCRAPER CONFIGURATIONS ---
# Set to true to run visual tests via shortcut buttons, false to run production-apply
TEST_MODE=true

# URL of the job search page to crawl (Python jobs in SP sorted by date)
REAL_BASE_URL=https://www.catho.com.br/vagas/programador-python/sao-paulo-sp/?order=dataAtualizacao

# Maximum number of pagination pages to crawl
MAX_PAGES_TO_SCRAPE=50

# Human interaction delay range (seconds) between applications
MIN_DELAY=1.5
MAX_DELAY=3.0
```

---

## 🚀 Execution

To execute the scraper in your current setup, run the main Python script:
```bash
./.venv/bin/python click_button.py
```

### 📌 Executing Modes:
*   **`TEST_MODE=true` (Recommended First Run)**: Opens Chromium's start tab page, locates and clicks the Catho shortcut button, executes PyAutoGUI `ESC` key presses, transitions into the target search URL page 1, and runs candidate clicks with popup-clearing routines.
*   **`TEST_MODE=false` (Production Mode)**: Connects directly, logs in automatically using credentials if a profile session is not active, navigates to `REAL_BASE_URL`, and clicks buttons continuously across pages.

---

## 🛡️ Stealth Safety Advice

*   Keep `MIN_DELAY` and `MAX_DELAY` above `1.5` seconds to maintain human-like navigation behavior.
*   To prevent Google profile locking warnings, ensure that no other instances of the Chromium `Default` folder are running elsewhere before launching the script.
*   Use `Ctrl + C` in the executing terminal to graciosuly trigger `KeyboardInterrupt` and exit the program cleanly.
# CV-Spammer
