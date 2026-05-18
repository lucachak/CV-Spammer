#!/usr/bin/env bash

# ==============================================================================
# Catho Invincible Stealth Scraper - Environment Setup Script
# ==============================================================================

# Colors for professional terminal output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "======================================================================"
echo "          CATHO INVINCIBLE STEALTH SCRAPER & AUTOMATED APPLY"
echo "                      Environment Setup Script"
echo "======================================================================"
echo -e "${NC}"

# Step 1: Verify prerequisites
echo -e "⚡ [1/5] Checking prerequisites..."
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Error: python3 is not installed. Please install it first.${NC}"
    exit 1
fi
echo -e "  -> Python 3 detected: $(python3 --version)"

if ! command -v google-chrome &>/dev/null && ! command -v chromium &>/dev/null; then
    echo -e "${YELLOW}Warning: Neither Google Chrome nor Chromium was found in PATH.${NC}"
    echo -e "  Make sure Chrome/Chromium is installed for Selenium to execute headful runs."
else
    echo -e "  -> Chrome/Chromium executable detected."
fi

# Step 2: Set up Python Virtual Environment
echo -e "\n⚡ [2/5] Creating Python virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    if [ $? -eq 0 ]; then
        echo -e "  -> ${GREEN}Virtual environment created successfully!${NC}"
    else
        echo -e "${RED}Error: Failed to create virtual environment.${NC}"
        exit 1
    fi
else
    echo -e "  -> Virtual environment (.venv) already exists. Skipping creation."
fi

# Step 3: Install required Python dependencies
echo -e "\n⚡ [3/5] Installing dependencies from requirements.txt..."
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "  -> ${GREEN}All dependencies installed successfully!${NC}"
else
    echo -e "${RED}Error: Dependency installation failed.${NC}"
    exit 1
fi

# Step 4: Configure X11 / Wayland PyAutoGUI keyboard display authority
echo -e "\n⚡ [4/5] Aligning display server graphics authorizations..."
XAUTH_FILE="$HOME/.Xauthority"
if [ ! -f "$XAUTH_FILE" ]; then
    touch "$XAUTH_FILE"
    echo -e "  -> ${GREEN}Created blank ~/.Xauthority file to prevent Xlib initialization crashes.${NC}"
else
    echo -e "  -> ~/.Xauthority already exists."
fi

# Check if XAUTHORITY variable is exportable
if [[ -z "$XAUTHORITY" ]]; then
    echo -e "  -> ${YELLOW}Notice: XAUTHORITY environment variable is not currently set.${NC}"
    echo -e "     We recommend running: ${CYAN}export XAUTHORITY=~/.Xauthority${NC} in your shell."
fi

# Step 5: Check and initialize default .env template
echo -e "\n⚡ [5/5] Aligning configuration controls (.env)..."
if [ ! -f ".env" ]; then
    cat <<EOT > .env
email=your_email@example.com
passwd=your_password

# --- SCRAPER CONFIGURATIONS ---
# Set to true to run the Chromium starting page shortcut test, false to run live scraping
TEST_MODE=true

# URL of the job search page to crawl
REAL_BASE_URL=https://www.catho.com.br/vagas/programador-python/sao-paulo-sp/?order=dataAtualizacao

# Maximum number of pagination pages to crawl
MAX_PAGES_TO_SCRAPE=50

# Human interaction delay range (seconds) between applications
MIN_DELAY=1.5
MAX_DELAY=3.0
EOT
    echo -e "  -> ${GREEN}Default .env template generated! Please fill in your credentials.${NC}"
else
    echo -e "  -> Active .env file detected. Keeping your current configurations safe."
fi

echo -e "\n${GREEN}======================================================================"
echo "                  SETUP COMPLETED SUCCESSFULLY!"
echo "======================================================================${NC}"
echo -e "To execute the scraper in test mode:"
echo -e "  ${CYAN}./.venv/bin/python click_button.py${NC}"
echo ""
