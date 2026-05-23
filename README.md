# 🕷️ Arachne Multi-Platform Stealth Scraper & Automated Apply

An industrial-grade, anti-bot-evading automated job application suite designed to execute seamless, high-volume job hunting across major platforms (**LinkedIn** and **Catho**). Powered by **Selenium 4**, **Undetected Chromedriver (UC)**, **Chrome DevTools Protocol (CDP) fakes**, and dynamic interaction heuristics.

The system features **Arachne LinkedIn Easy Apply (Caminho da Raposa)**, which dynamically parses job application questions (inputs, textareas, radio buttons, checkboxes, and select dropdowns) and matches them intelligently using your local `Resume` object (`helpers/resume.py`) as a high-fidelity single source of truth.

---

## ✨ Core Capabilities

### 🌐 1. LinkedIn "Easy Apply" Automation (Caminho da Raposa)
*   **📋 Intelligent Form Auto-Filler**: Classifies forms inside LinkedIn modals on-the-fly into their exact field types (`TEXT_INPUT`, `SELECT_DROPDOWN`, `TEXTAREA`, `RADIO_GROUP`, `CHECKBOX`).
*   **🧠 Resume-Driven Answers**: Automatically resolves complex form questions (languages, years of experience, tools, summaries) by matching questions to data fields defined in `helpers/resume.py`.
*   **🔄 Anti-Overwriting Safety**: Detects fields already pre-filled by LinkedIn (such as email, country codes, or phone numbers) and skips them dynamically. This prevents breaking form validation and avoids infinite loops.
*   **🎲 Conservative Fallbacks**: Injects smart fallback values (like conservative random years of experience or simulation flags) for fields not answered in your resume structure.

### 💎 2. Catho Stealth Automation
*   **⏭️ Senior Skip Regex Filter**: Scans job cards and skips positions containing senior indicators (`senior`, `sênior`, `sr`, `sn`) using boundary-safe regex to prevent false positives.
*   **🚨 Modal-Relative Popup Evasion**: Detects and clears overlay popups, translation dialogs, and questionnaires seamlessly to prevent interaction blocking.

### 🛡️ 3. Industrial Stealth Evasions
*   **🤫 Silent Console TUI Mode**: Elegant colorized logging showing exact field classifications (e.g., `📝 [TEXT_INPUT]`, `🔽 [DROPDOWN]`) and resolution statuses.
*   **🎭 Deep CDP Evasions**: Overrides standard `navigator.webdriver` variables, structures complete mock native `window.chrome` objects, injects standard plugins array lengths, and fakes user-agent and GPU vendor profiles.
*   **🤖 Human-Like ActionChains**: Emulates organic mouse cursors with realistic coordinate targeting, randomized hover pauses (`0.5s` - `3s`), and variable keyboard delays.

---

## 📁 Workspace Structure

```text
.
├── Driver.py                   # Central orchestrator CLI (Entrypoint)
├── .env                        # Configuration secrets, worklist keywords & credentials
├── requirements.txt            # Python dependencies (undetected-chromedriver, selenium, etc.)
├── setup.sh                    # Automated system setup & environment configurer
├── persona.md                  # Project design philosophy & persona definitions (git-ignored)
│
├── components/
│   ├── __init__.py
│   ├── browser_engine.py       # Chrome profile settings & CDP stealth injects
│   ├── config_loader.py        # Safe parser for overrideable config environment files
│   ├── linkedin_scraper.py     # LinkedIn Easy Apply logic & Modal answering
│   ├── catho_scraper.py        # Catho stealth scraper engine
│   ├── launch_browser.py       # Helper to run browser with active profile
│   └── search_builder.py       # Formats and safely encodes job search target URLs
│
├── helpers/
│   ├── __init__.py
│   ├── resume.template.py      # Template file containing career metrics and data structure
│   ├── resume.py               # Single Source of Truth with your actual career data (git-ignored)
│   └── [utilities]             # Custom DOM parsers, screenshots, cookie checkers & tests
```

---

## ⚡ Installation & Quick Start

### 1. Execute the Installer
Set up the automated virtual environment, prepare python dependencies, and build the template configuration:
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment Options
Open the newly generated `.env` file on your workspace and fill in your credentials:
```ini
email=your_catho_email@example.com
passwd=your_catho_password
linkedin_passwd=your_linkedin_password

# --- CONFIGURATIONS ---
KEYWORDS_WORKLIST=python, backend, django, devops, estagio
MIN_DELAY=1.5
MAX_DELAY=3.5
VERBOSE=false
```

### 3. Setup Your Resume Truth (`helpers/resume.py`)
Because your career details are private, `helpers/resume.py` is ignored by Git. 

To configure it, copy the template and customize your professional details:
```bash
cp helpers/resume.template.py helpers/resume.py
```
Open the new `helpers/resume.py` file and define your skills, languages, experience metrics, and career summaries inside this file to feed the automated LinkedIn parser.

---

## 🚀 Execution & Command Reference

Arachne is orchestrated through a central, unified CLI. Execute the commands using the virtual environment:

### Run LinkedIn Scraper
Processes job pages sequentially, detects "Easy Apply" buttons, and fills form inputs dynamically:
```bash
source .venv/bin/activate
python3 Driver.py scrape_linkedin
```

### Run Catho Scraper
Launches the stealth engine targeting job boards on Catho:
```bash
source .venv/bin/activate
python3 Driver.py scrape_catho
```

### Launch Validating Browser
Opens a Chromium window loaded with your persistent local user profile. Use this command to log in manually, complete one-time 2FA challenges, or verify cookies:
```bash
source .venv/bin/activate
python3 Driver.py launch_browser
```

### Test Generators
Verify that target search parameters are compiled correctly:
```bash
source .venv/bin/activate
python3 Driver.py test url
```

---

## 🛡️ Operational Safeguards

> [!TIP]
> Keep `MIN_DELAY` above `1.5` seconds and `MAX_DELAY` above `3.5` seconds to prevent rate-limiting triggers and maintain human-like behavior.

> [!IMPORTANT]
> Always run `python3 Driver.py launch_browser` first if it is your first time or if you get a session challenge. Complete the manual verification or log in, then close the browser completely before running the headless/automatic scraper.

> [!WARNING]
> Do not leave another window of your local Chrome user profile open while running the script, as Chrome locks directories to single-process accesses.
