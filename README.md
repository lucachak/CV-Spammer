# 💎 Catho Invincible Stealth Scraper & Automated Apply

An industrial-grade, anti-bot-evading automated job candidate scraper designed specifically for **Catho**. Built using **Selenium 4 (Python)**, **Chrome DevTools Protocol (CDP) fakes**, and **PyAutoGUI keyboard engines**, this tool runs securely under Linux (X11 & Wayland) to process job applications dynamically across pages, bypassing translation popups, initial popups, "CV Sent" overlays, and "Killer Question" questionnaires completely!

---

## ✨ Key Capabilities

*   **📋 Sequential Keyword Worklist Queue**: Automates sequential job hunting by looping through keywords (e.g., `java`, `backend`, `programador junior`, etc.) defined in your `.env`. The script dynamically slugifies spaces into hyphens and navigates from one keyword to another when zero clickable buttons are left.
*   **⏭️ Regular Expression Senior Skip Filter**: Scans each job card (`li[data-offer-item]`) and automatically skips positions containing senior indicators (`senior`, `sênior`, `sn`, `sr`). It uses case-insensitive regex word boundaries (`\b`) to guarantee **zero false positives** on regular words (like *desnudar* or *Israel*).
*   **🤫 Compact Console TUI Mode**: Silences excessive logs (interactive delays, keyboard keypresses, popup closing attempts) into a streamlined, single-line dynamic console indicator:
    `➤ Targeting: 'Analista Programador' (1/12)... ✔ [CLICK]`. 
    Toggle `VERBOSE=true` in your `.env` at any time to re-enable full, high-fidelity debug details.
*   **🛡️ CDP Anti-Bot Evasions (Stealth Mode)**: Overrides `navigator.webdriver` to `undefined`, injects standard desktop plug-in listings, fakes user languages (`pt-BR`, `pt`, `en-US`), and spoofs standard `Intel HD Graphics 620` WebGL rendering signatures to stay fully invisible to anti-scraping scanners.
*   **📂 Workspace Persistent Session Loader**: Dynamically maps Chrome's `Default` user-data directory from the workspace. This loads your active login session automatically, bypassing MFA and login forms.
*   **⌨️ PyAutoGUI Keyboard Evasion**: Simulates a human delay (1.0s to 3.0s) upon initial Catho tile clicking and injects 3 to 7 physical `ESC` keystrokes to close Chrome's initial popups or translate prompts.
*   **🚨 Modal-Relative Popup Evasion**: Detects popups and consent dialogs strictly inside visible modal containers, avoiding standard search chip closer elements. If standard clicks are blocked, it executes native ESC keys, PyAutoGUI esc, or JS click injections to clear the screen instantly.

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
chmod +x setup.sh
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
Open **[.env](.env)** and configure your credentials, target keywords, sênior filters, and console verbosity:
```ini
email=lucas.example@gmail.com
passwd=YourSecurePassword123!

# --- SCRAPER CONFIGURATIONS ---
# Set to true to run visual tests via shortcut buttons, false to run production-apply
TEST_MODE=true

# URL of the job search page to crawl
REAL_BASE_URL=https://www.catho.com.br/vagas/programador-python/sao-paulo-sp/?order=dataAtualizacao

# Maximum number of pagination pages to crawl
MAX_PAGES_TO_SCRAPE=50

# Human interaction delay range (seconds) between applications
MIN_DELAY=1.5
MAX_DELAY=3.0

# Comma-separated list of job titles/keywords to crawl sequentially
KEYWORDS_WORKLIST=programador-python, java, backend, programador junior, programador jr, estagio

# Comma-separated list of keywords to identify senior roles to skip (case-insensitive)
SENIOR_TERMS=senior, sênior, sn, sr

# Verbosity of terminal output (true for full logs, false for elegant compact mode)
VERBOSE=false
```

---

## 🚀 Execution

To execute the scraper in your current setup, run the main Python script:
```bash
./.venv/bin/python click_button.py
```

### 📌 Executing Modes:
*   **`TEST_MODE=true` (Recommended First Run)**: Opens Chromium's start tab page, locates and clicks the Catho shortcut button, executes PyAutoGUI `ESC` key presses, transitions into the target search URL page 1, and runs candidate clicks with popup-clearing routines in simulated/test mode.
*   **`TEST_MODE=false` (Production Mode)**: Connects directly, logs in automatically using credentials if a profile session is not active, navigates sequentially through your `KEYWORDS_WORKLIST`, and clicks buttons continuously across pages.

---

## 🛡️ Stealth Safety Advice

> [!TIP]
> Keep `MIN_DELAY` and `MAX_DELAY` above `1.5` seconds to maintain human-like navigation behavior.

> [!IMPORTANT]
> To prevent Google profile locking warnings, ensure that no other instances of the Chromium `Default` folder are running elsewhere before launching the script.

> [!NOTE]
> Use `Ctrl + C` in the executing terminal to gracefully trigger `KeyboardInterrupt` and exit the program cleanly.
