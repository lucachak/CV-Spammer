import time
import re
import random
import traceback
from enum import Enum
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from decouple import config

from components.search_builder import SearchBuilder
from components.browser_engine import setup_driver, Colors, highlight_element
from components.config_loader import load_env_configurations
from helpers.resume import meu_curriculo


# ==========================================
# HUMAN BEHAVIOR UTILITIES
# ==========================================

def gaussian_delay(center_s: float, sigma_s: float = 0.35, min_s: float = 0.2):
    delay = max(min_s, random.gauss(center_s, sigma_s))
    time.sleep(delay)


def block_pause():
    duration = max(300, random.gauss(600, 120))
    mins = duration / 60
    print(f"\n  {Colors.YELLOW}[block_pause]{Colors.END} Pausa de {mins:.1f} min antes do proximo bloco...")
    time.sleep(duration)


class FieldType(Enum):
    TEXT_INPUT    = "text_input"     # <input type="text"> ou <input type="number">
    SELECT_DROPDOWN = "select"       # <select> — exige Select() do Selenium
    TEXTAREA      = "textarea"       # <textarea> — caixas de texto longas
    RADIO_GROUP   = "radio"          # <input type="radio"> — sim/não, opções únicas
    CHECKBOX      = "checkbox"       # <input type="checkbox">
    UNKNOWN       = "unknown"        # Tipo não identificado — segurança primeiro




class LinkedInScraper:

    @staticmethod
    def login_to_linkedin(driver, credentials, config) -> bool:
        wait = WebDriverWait(driver, 10)
        
        print(f"\n{Colors.BLUE}🌐 [Security Check]{Colors.END} Verificando status da sessão nativa no LinkedIn...")
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)
        
        current_url = driver.current_url.lower()
        
        if "feed" in current_url and "login" not in current_url:
            print(f"  {Colors.GREEN}✅ [Sucesso]{Colors.END} Sessão nativa validada. Já estamos logados.")
            return True
            
        if "login" in current_url or "session_redirect" in current_url or "uas/login" in current_url:
            print(f"  {Colors.YELLOW}⚠️ [Alerta]{Colors.END} Sessão expirada ou desafiada. Iniciando injeção de credenciais...")
            
            try:
                # Procura a senha primeiro, ou o campo de email se estiver totalmente deslogado
                password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='session_password'], input#password, input#session_password")))
                
                try:
                    email_field = driver.find_element(By.CSS_SELECTOR, "input[name='session_key'], input#username")
                    if not email_field.get_attribute('value'):
                        highlight_element(driver, email_field, config, color="#25D366")
                        email_field.clear()
                        email_field.send_keys(credentials.email)
                        time.sleep(0.5)
                except:
                    pass
                    
                highlight_element(driver, password_field, config, color="#25D366")
                password_field.clear()
                password_field.send_keys(credentials.linkedin_password)
                time.sleep(1)
                
                submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button[data-litms-control-urn='login-submit']")
                highlight_element(driver, submit_btn, config, color="#25D366")
                submit_btn.click()
                
                print(f"  {Colors.BLUE}⏳ [Aguardando]{Colors.END} Credenciais injetadas. Aguardando resolução...")
                time.sleep(5)
                
                if "feed" in driver.current_url.lower() or "search" in driver.current_url.lower():
                    print(f"  {Colors.GREEN}✅ [Sucesso]{Colors.END} Login autônomo concluído.")
                    return True
                else:
                    print(f"  {Colors.RED}❌ [Aviso]{Colors.END} Captcha ou 2FA (Pin) detectado. Você tem 45s para resolver no painel Chrome.")
                    start_time = time.time()
                    while time.time() - start_time < 45:
                        if "feed" in driver.current_url.lower() or "search" in driver.current_url.lower():
                            print(f"  {Colors.GREEN}✅ [Sucesso]{Colors.END} Barreira manual superada.")
                            return True
                        time.sleep(2)
                    return False
                    
            except Exception as e:
                print(f"  {Colors.RED}❌ [Erro Inesperado]{Colors.END} Falha ao localizar os campos de login do LinkedIn: {e}")
                return False
                
        print(f"  {Colors.YELLOW}⚠️ [Aviso]{Colors.END} URL desconhecida ao acessar o feed: {current_url}. Presumindo logado ou barrado.")
        return True

    @staticmethod
    def _classify_field(modal, input_id: str) -> tuple:
        try:
            elem = modal.find_element(By.ID, input_id)
            tag = elem.tag_name.lower()

            if tag == "select":
                return FieldType.SELECT_DROPDOWN, elem
            elif tag == "textarea":
                return FieldType.TEXTAREA, elem
            elif tag == "input":
                input_type = (elem.get_attribute("type") or "text").lower()
                if input_type in ("text", "number", "email", "tel", ""):
                    return FieldType.TEXT_INPUT, elem
                elif input_type == "radio":
                    return FieldType.RADIO_GROUP, elem
                elif input_type == "checkbox":
                    return FieldType.CHECKBOX, elem
                else:
                    return FieldType.UNKNOWN, elem
            else:
                return FieldType.UNKNOWN, elem
        except Exception:
            return FieldType.UNKNOWN, None

    @staticmethod
    def _log_field_detection(field_type: FieldType, label_text: str):
        """
        Imprime no terminal um log visual colorido indicando o tipo de campo detectado.
        Cores usadas por tipo:
          TEXT_INPUT      → CYAN   📝
          SELECT_DROPDOWN → YELLOW 🔽
          TEXTAREA        → BLUE   📄
          RADIO_GROUP     → HEADER 🔘
          CHECKBOX        → GREEN  ☑️
          UNKNOWN         → DIM    ❓
        """
        short = label_text[:35]
        type_styles = {
            FieldType.TEXT_INPUT:      (Colors.CYAN,   "📝 [TEXT_INPUT]  "),
            FieldType.SELECT_DROPDOWN: (Colors.YELLOW,  "🔽 [DROPDOWN]    "),
            FieldType.TEXTAREA:        (Colors.BLUE,    "📄 [TEXTAREA]    "),
            FieldType.RADIO_GROUP:     (Colors.HEADER,  "🔘 [RADIO]       "),
            FieldType.CHECKBOX:        (Colors.GREEN,   "☑️  [CHECKBOX]    "),
            FieldType.UNKNOWN:         (Colors.DIM,     "❓ [UNKNOWN]     "),
        }
        color, icon_label = type_styles.get(field_type, (Colors.DIM, "❓ [UNKNOWN]     "))
        print(f"        {color}{icon_label}{Colors.END} → '{short}'")

    @staticmethod
    def _resolve_from_resume(text_lower: str) -> str | None:
        # ── 1. Idiomas ──
        lang_keywords = {
            "inglês":     "English",
            "ingles":     "English",
            "english":    "English",
            "português":  "Portuguese",
            "portugues":  "Portuguese",
            "portuguese": "Portuguese",
            "húngaro":    "Hungarian",
            "hungaro":    "Hungarian",
            "hungarian":  "Hungarian",
            "russo":      "Russian",
            "russian":    "Russian",
        }
        for kw, lang_key in lang_keywords.items():
            if kw in text_lower:
                raw = meu_curriculo.languages.get(lang_key, "")
                if raw:
                    # Remove a nota entre parênteses: "Fluent (Lived in Ireland)" → "Fluent"
                    return raw.split("(")[0].strip()

        # ── 2. Anos de experiência com tecnologias ──
        # keywords ligadas a perguntas de tempo de experiência
        time_signals = [
            "quantos anos", "há quantos", "ha quantos",
            "how many years", "years of experience", "anos de experiência",
            "anos de experiencia", "tempo de experiência", "tempo de experiencia",
        ]
        if any(sig in text_lower for sig in time_signals):
            for tech, years in meu_curriculo.years_of_experience.items():
                if tech in text_lower:
                    # Retorna int se for número inteiro, ex: 4.0 → "4"
                    val = int(years) if years == int(years) else years
                    return str(val)

        # ── 3. Perguntas descritivas (fallback → sumário do currículo) ──
        desc_signals = [
            "nos conte mais", "descreva", "conte-nos", "conte um pouco",
            "tell us", "describe", "fale sobre",
        ]
        if any(sig in text_lower for sig in desc_signals):
            return meu_curriculo.summary

        return None

    @staticmethod
    def _human_click(driver, element) -> bool:
        try:
            # Jitter: humanos nunca acertam o centro exato de um botão
            jitter_x = random.uniform(-5, 5)
            jitter_y = random.uniform(-3, 3)

            actions = ActionChains(driver)

            # Fase 1: Abordagem — cursor chega de uma posição aleatória próxima ao elemento
            approach_x = random.uniform(-55, 55)
            approach_y = random.uniform(-35, 35)
            actions.move_to_element_with_offset(element, approach_x, approach_y)
            actions.pause(random.uniform(0.06, 0.16))

            # Fase 2: Refinamento — micro-ajuste incremental em direção ao alvo real
            steps = random.randint(3, 5)
            dx = (jitter_x - approach_x) / steps
            dy = (jitter_y - approach_y) / steps
            for _ in range(steps):
                actions.move_by_offset(
                    dx + random.uniform(-0.8, 0.8),
                    dy + random.uniform(-0.5, 0.5)
                )
                actions.pause(random.uniform(0.01, 0.03))

            # Fase 3: Hesitação pré-clique + clique nativo (gera MouseEvent real)
            actions.pause(random.uniform(0.09, 0.22))
            actions.click()
            actions.perform()
            return True
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", element)
            except Exception:
                pass
            return False

    @staticmethod
    def _micro_wander(driver, intensity: int = 2):
        try:
            actions = ActionChains(driver)
            for _ in range(intensity):
                actions.move_by_offset(
                    random.randint(-18, 18),
                    random.randint(-12, 12)
                )
                actions.pause(random.uniform(0.25, 0.7))
            actions.perform()
        except Exception:
            pass  # Falha silenciosa — micro-wander não pode derrubar o loop principal

    @staticmethod
    def _select_best_option(select: Select, preferred: str | None) -> bool:
        opts = select.options
        real_opts = [o for o in opts if o.text.strip()]  # descarta placeholders vazios
        if not real_opts:
            return False

        if preferred:
            pref_lower = preferred.lower()

            # 1. Match exato
            for opt in real_opts:
                if opt.text.strip().lower() == pref_lower:
                    opt.click()
                    return True

            # 2. Opção contém o preferred
            for opt in real_opts:
                if pref_lower in opt.text.strip().lower():
                    opt.click()
                    return True

            # 3. preferred contém o texto da opção
            for opt in real_opts:
                opt_text = opt.text.strip().lower()
                if opt_text and opt_text in pref_lower:
                    opt.click()
                    return True

        # 4. Heurística sim/não
        yes_opts = [o for o in real_opts if o.text.strip().lower() in ("sim", "yes", "true")]
        if yes_opts:
            yes_opts[0].click()
            return True

        # 5. Fallback: primeira opção real
        real_opts[0].click()
        return True

    @staticmethod
    def answer_modal_questions(driver, modal, config):

        try:
            labels = modal.find_elements(By.TAG_NAME, "label")
            for label in labels:
                text = label.text.strip()
                text_lower = text.lower()
                input_id = label.get_attribute("for")
                if not input_id:
                    continue

                # ── 1. Classificação cirúrgica do campo ──
                field_type, elem = LinkedInScraper._classify_field(modal, input_id)
                LinkedInScraper._log_field_detection(field_type, text)

                if elem is None:
                    continue

                # ── 2. Resolução da resposta via currículo ──
                resolved = LinkedInScraper._resolve_from_resume(text_lower)
                if resolved:
                    print(f"          {Colors.GREEN}📋 [Resume]{Colors.END} Resposta resolvida: '{resolved[:40]}'")

                # ── 3. Delay contextual por tipo — humanos demoram mais em campos complexos ──
                _field_timing = {
                    FieldType.TEXT_INPUT:      (0.7, 0.25),
                    FieldType.SELECT_DROPDOWN: (1.1, 0.35),
                    FieldType.TEXTAREA:        (2.3, 0.7),   # precisa "ler e pensar"
                    FieldType.RADIO_GROUP:     (1.4, 0.45),
                    FieldType.CHECKBOX:        (0.8, 0.25),
                    FieldType.UNKNOWN:         (0.5, 0.15),
                }
                _center, _sigma = _field_timing.get(field_type, (0.7, 0.25))
                gaussian_delay(_center, _sigma, min_s=0.3)

                # TEXT_INPUT
                if field_type == FieldType.TEXT_INPUT:
                    if elem.get_attribute("value"):
                        continue
                    if resolved:
                        elem.clear()
                        elem.send_keys(resolved)
                        print(f"          {Colors.CYAN}↳ Preenchido (resume):{Colors.END} '{resolved[:30]}'")
                    elif any(k in text_lower for k in ["há quantos", "ha quantos", "quantos anos", "how many", "years"]):
                        answer = str(random.randint(1, 3))
                        elem.clear()
                        elem.send_keys(answer)
                        print(f"          {Colors.CYAN}↳ Preenchido (fallback):{Colors.END} {answer} anos")

                # TEXTAREA
                elif field_type == FieldType.TEXTAREA:
                    if elem.get_attribute("value"):
                        continue
                    content = resolved or meu_curriculo.summary
                    elem.clear()
                    elem.send_keys(content)
                    src = "resume" if resolved else "summary"
                    print(f"          {Colors.BLUE}↳ Textarea preenchida ({src}).{Colors.END}")

                # SELECT_DROPDOWN
                elif field_type == FieldType.SELECT_DROPDOWN:
                    try:
                        select = Select(elem)
                        if len(select.options) <= 1:
                            continue

                        # ── Verifica se o LinkedIn já pré-preencheu com uma opção válida ──
                        # Placeholders costumam ser: texto vazio, "Selecionar opção", "Select an option"
                        already_selected = select.first_selected_option.text.strip()
                        placeholder_hints = ("", "selecionar opção", "select an option", "select option")
                        if already_selected.lower() not in placeholder_hints:
                            print(f"          {Colors.YELLOW}↳ Já pré-preenchido (skip):{Colors.END} '{already_selected}'")
                            continue  # LinkedIn já escolheu o valor certo, não sobrescreve

                        chosen = LinkedInScraper._select_best_option(select, resolved)
                        if chosen:
                            chosen_text = select.first_selected_option.text.strip()
                            src = "resume" if resolved else "heurística"
                            print(f"          {Colors.YELLOW}↳ Selecionado ({src}):{Colors.END} '{chosen_text}'")
                    except Exception:
                        pass

                # RADIO_GROUP
                elif field_type == FieldType.RADIO_GROUP:
                    try:
                        radio_name = elem.get_attribute("name")
                        if not radio_name:
                            continue
                        all_radios = modal.find_elements(
                            By.CSS_SELECTOR, f"input[type='radio'][name='{radio_name}']"
                        )
                        selected = False
                        # Se resolved, tenta bater com os labels dos radios
                        if resolved:
                            res_lower = resolved.lower()
                            for r in all_radios:
                                r_id = r.get_attribute("id")
                                try:
                                    r_label = modal.find_element(By.CSS_SELECTOR, f"label[for='{r_id}']")
                                    r_text = r_label.text.strip().lower()
                                    if res_lower in r_text or r_text in res_lower:
                                        LinkedInScraper._human_click(driver, r)
                                        print(f"          {Colors.HEADER}↳ Radio selecionado (resume):{Colors.END} '{r_label.text.strip()}'")
                                        selected = True
                                        break
                                except Exception:
                                    pass
                        # Fallback: prefere sim/yes, depois index 0
                        if not selected:
                            for r in all_radios:
                                r_id = r.get_attribute("id")
                                try:
                                    r_label = modal.find_element(By.CSS_SELECTOR, f"label[for='{r_id}']")
                                    if r_label.text.strip().lower() in ("sim", "yes", "true"):
                                        LinkedInScraper._human_click(driver, r)
                                        print(f"          {Colors.HEADER}↳ Radio selecionado (sim/yes):{Colors.END} '{r_label.text.strip()}'")
                                        selected = True
                                        break
                                except Exception:
                                    pass
                        if not selected and all_radios:
                            LinkedInScraper._human_click(driver, all_radios[0])
                            print(f"          {Colors.HEADER}↳ Radio selecionado (fallback index 0){Colors.END}")
                    except Exception:
                        pass

                # CHECKBOX
                elif field_type == FieldType.CHECKBOX:
                    try:
                        if not elem.is_selected():
                            LinkedInScraper._human_click(driver, elem)
                            print(f"          {Colors.GREEN}↳ Checkbox marcado.{Colors.END}")
                    except Exception:
                        pass

                # UNKNOWN
                else:
                    print(f"          {Colors.DIM}↳ Campo desconhecido ignorado (ID: {input_id}).{Colors.END}")

        except Exception as e:
            print(f"        {Colors.RED}❌ [answer_modal_questions]{Colors.END} Erro inesperado: {e}")

    @staticmethod
    def scrape_linkedin(debug_mode: bool = False):
        import datetime
        import os as _os

        def human_delay(min_s=1.5, max_s=3.5):
            """Converte a assinatura min/max antiga para gaussian_delay."""
            center = (min_s + max_s) / 2
            sigma  = (max_s - min_s) / 4
            gaussian_delay(center, sigma, min_s=min_s * 0.6)

        def log_session(applications_sent: int):
            log_path = _os.path.join(
                _os.path.dirname(_os.path.abspath(_os.path.dirname(__file__))),
                "session_log.txt"
            )
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] Sessao encerrada | Aplicacoes enviadas: {applications_sent}\n")
            print(f"\n  {Colors.DIM}[SessionLog]{Colors.END} Sessao registrada em session_log.txt ({applications_sent} aplicacoes)")

        print(f"{Colors.GREEN}{Colors.BOLD}[Arachne LinkedIn Scraper]{Colors.END} Operacao 'Caminho da Raposa' Iniciada.")
        conf, credentials = load_env_configurations()

        # startup_jitter: nunca inicia na mesma janela de tempo exata
        if debug_mode:
            print(f"  {Colors.YELLOW}[DEBUG]{Colors.END} Modo debug ativo — startup_jitter desabilitado.")
        else:
            jitter_secs = abs(random.gauss(0, 12)) * 60
            if jitter_secs > 10:
                print(f"  {Colors.DIM}[startup_jitter]{Colors.END} Aguardando {jitter_secs/60:.1f} min antes de iniciar...")
                time.sleep(jitter_secs)

        # MAX_APPLICATIONS: cap aleatorio baseado no limite configurado
        max_cap = conf.MAX_DAILY_APPLICATIONS
        MAX_APPLICATIONS = random.randint(max(1, max_cap - 2), max_cap + 2)
        applications_sent = 0
        print(f"  {Colors.CYAN}[Cap]{Colors.END} Meta desta sessao: {MAX_APPLICATIONS} aplicacoes")
        
        driver = setup_driver(conf, headless=False)
        wait = WebDriverWait(driver, 12)
        
        if not LinkedInScraper.login_to_linkedin(driver, credentials, conf):
            print(f"{Colors.RED}[EXIT]{Colors.END} Falha na validacao de login. Operacao cancelada.")
            try:
                driver.quit()
            except:
                pass
            log_session(applications_sent)
            return
            
        print(f"\n{Colors.BLUE}🌐 [SearchBuilder]{Colors.END} Construindo alvos...")
        urls = SearchBuilder.build_all()
            
        for base_url in urls:
            print(f"\n{Colors.CYAN}{Colors.BOLD}======================================================={Colors.END}")
            print(f"{Colors.YELLOW}🚀 Iniciando caçada no alvo:{Colors.END} {base_url}")
            print(f"{Colors.CYAN}{Colors.BOLD}======================================================={Colors.END}")
            
            for page in range(6):
                start_param = page * 25
                page_url = f"{base_url}&start={start_param}"
                print(f"\n  {Colors.BLUE}📍 -> Navegando para página {page + 1}...{Colors.END}")
                driver.get(page_url)
                
                current_url_lower = driver.current_url.lower()
                if "login" in current_url_lower or "checkpoint" in current_url_lower:
                    print(f"  {Colors.RED}❌ [FATAL]{Colors.END} A sessão nativa foi derrubada ou interceptada (Login Wall/Captcha). Abortando a caçada atual.")
                    break
                
                try:
                    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "ul.scaffold-layout__list-container, .jobs-search-results-list, ul.jobs-search__results-list") or d.find_elements(By.XPATH, "//a[contains(@href, '/jobs/view/')]"))
                except TimeoutException:
                    print(f"  {Colors.RED}❌ [Timeout]{Colors.END} A lista de vagas não carregou na página {page + 1}. Captcha ou fim da linha? Pulando.")
                    continue
                    
                human_delay(2.5, 4.5)
                
                xpath_selectors = [
                    "//li[contains(@class, 'jobs-search-results__list-item')]",
                    "//div[contains(@class, 'job-card-container')]",
                    "//div[contains(@class, 'job-search-card')]",
                    "//ul[contains(@class, 'jobs-search__results-list')]/li",
                    "//div[contains(@class, 'base-card')]",
                    "//li[.//a[contains(@href, '/jobs/view/')]]",
                    "//div[.//a[contains(@href, '/jobs/view/') and contains(@class, 'job-card')]]"
                ]
                job_cards = driver.find_elements(By.XPATH, " | ".join(xpath_selectors))
                
                # Desduplicando caso XPath retorne ancestrais duplicados
                job_cards = list(dict.fromkeys(job_cards))
                total_items = len(job_cards)
                
                if total_items == 0:
                    print(f"  {Colors.YELLOW}⚠️ [Warning]{Colors.END} Nenhum card de vaga encontrado na página {page + 1}. A muralha subiu.")
                    continue
                    
                print(f"  {Colors.GREEN}✅ -> Sucesso. Encontrei {total_items} vagas expostas.{Colors.END} Passando pela lista...")
                
                visited_job_ids = set()  # Rastreia jobs já processados por URL/ID único
                
                for index in range(total_items):
                    try:
                        current_cards = driver.find_elements(By.XPATH, " | ".join(xpath_selectors))
                        current_cards = list(dict.fromkeys(current_cards))
                        if index >= len(current_cards):
                            break
                            
                        card = current_cards[index]
                        
                        # ── Extrai o job ID único do href para evitar processar o mesmo job ──
                        job_uid = None
                        try:
                            card_link = card.find_element(By.XPATH, ".//a[contains(@href, '/jobs/view/')]")
                            href = card_link.get_attribute("href") or ""
                            # Extrai o ID numérico: /jobs/view/1234567890/
                            match = re.search(r'/jobs/view/(\d+)', href)
                            if match:
                                job_uid = match.group(1)
                        except Exception:
                            pass
                        
                        if job_uid and job_uid in visited_job_ids:
                            print(f"    {Colors.DIM}- [{index + 1}/{total_items}] [skip] Job já visitado (ID: {job_uid}). Pulando duplicata.{Colors.END}")
                            continue
                        
                        if job_uid:
                            visited_job_ids.add(job_uid)

                        # Skip probabilístico leve (~12%) — humanos não clicam em tudo que veem
                        if random.random() < 0.12:
                            print(f"    {Colors.DIM}- [{index + 1}/{total_items}] [passando] Título ignorado naturalmente.{Colors.END}")
                            gaussian_delay(0.4, 0.15, min_s=0.2)
                            continue

                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", card)
                        gaussian_delay(1.0, 0.45, min_s=0.5)
                        LinkedInScraper._micro_wander(driver, intensity=1)
                        
                        title_link = None
                        selectors = [
                            "a.job-card-list__title",
                            "a.job-card-container__link",
                            ".artdeco-entity-lockup__title a",
                            "a.base-card__full-link"
                        ]
                        
                        for selector in selectors:
                            try:
                                title_link = card.find_element(By.CSS_SELECTOR, selector)
                                break
                            except:
                                continue
                                
                        if not title_link:
                            try:
                                title_link = card.find_element(By.XPATH, ".//a[contains(@href, '/jobs/view/')]")
                            except:
                                try:
                                    title_link = card.find_element(By.TAG_NAME, "a")
                                except:
                                    print(f"    {Colors.DIM}- [{index + 1}/{total_items}]{Colors.END} {Colors.RED}[!] Vaga blindada. Impossível localizar o link <a>.{Colors.END}")
                                    continue

                        title = title_link.text.strip() or "Vaga sem título"
                        print(f"    {Colors.DIM}- [{index + 1}/{total_items}]{Colors.END} Acessando: {Colors.BOLD}{title}{Colors.END}")

                        LinkedInScraper._human_click(driver, title_link)
                        
                        gaussian_delay(2.5, 0.6, min_s=1.8)
                        LinkedInScraper._micro_wander(driver, intensity=2)
                        
                        # Procurar botão Easy Apply (Candidatura Simplificada) no painel direito
                        try:
                            right_pane = driver.find_element(By.CSS_SELECTOR, ".jobs-search__job-details--container, .job-view-layout, .jobs-details")
                            apply_button = right_pane.find_element(By.CSS_SELECTOR, "div[class*='jobs-apply'] button, button.jobs-apply-button")

                            print(f"      {Colors.GREEN}🎯 Achou botão Easy Apply! Clicando...{Colors.END}")
                            gaussian_delay(0.6, 0.2, min_s=0.3)  # hesitação pré-clique
                            LinkedInScraper._human_click(driver, apply_button)
                            
                            human_delay(1.5, 2.5)
                            
                            print(f"      {Colors.BLUE}🔄 Interagindo com o modal de candidatura...{Colors.END}")
                            
                            for step in range(10):  # Limite máximo de 10 telas para evitar loops infinitos
                                try:
                                    modal = driver.find_element(By.CSS_SELECTOR, "div[data-test-modal-id], div.jobs-easy-apply-modal, div[role='dialog']")
                                except Exception:
                                    print(f"      {Colors.GREEN}✅ Modal finalizado ou fechado.{Colors.END}")
                                    break
                                
                                try:
                                    header = modal.find_element(By.CSS_SELECTOR, "h3, .pb4 h3, .artdeco-modal__header h3")
                                    print(f"        {Colors.CYAN}➡️ Painel [{step+1}]: {header.text.strip()}{Colors.END}")
                                except Exception:
                                    pass
                                    
                                human_delay(1.0, 2.0)
                                LinkedInScraper._micro_wander(driver, intensity=1)

                                LinkedInScraper.answer_modal_questions(driver, modal, conf)
                                
                                try:
                                    primary_buttons = modal.find_elements(By.CSS_SELECTOR, "button.artdeco-button--primary")
                                    
                                    clicked = False
                                    submitted = False
                                    for btn in primary_buttons:
                                        btn_text = btn.text.strip().lower()
                                        if any(word in btn_text for word in ["submit", "enviar"]):
                                            # ── SUBMISSÃO REAL: clica no botão final ──
                                            print(f"        {Colors.GREEN}{Colors.BOLD}🎯 Submetendo candidatura! Clicando em '{btn.text.strip()}'...{Colors.END}")
                                            gaussian_delay(0.8, 0.3, min_s=0.4)
                                            LinkedInScraper._human_click(driver, btn)
                                            clicked = True
                                            submitted = True
                                            gaussian_delay(2.0, 0.5, min_s=1.5)  # aguarda confirmação do LinkedIn
                                            
                                            # Fecha o modal de confirmação pós-submissão ("Application sent!")
                                            try:
                                                post_modal_close = WebDriverWait(driver, 5).until(
                                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Dismiss'], button[data-test-modal-close-btn], button[aria-label*='Fechar']"))
                                                )
                                                LinkedInScraper._human_click(driver, post_modal_close)
                                                print(f"        {Colors.GREEN}✅ Candidatura enviada com sucesso! Modal de confirmação fechado.{Colors.END}")
                                            except Exception:
                                                print(f"        {Colors.GREEN}✅ Candidatura enviada com sucesso!{Colors.END}")
                                            break
                                        elif any(word in btn_text for word in ["next", "avançar", "continue", "continuar", "review", "revisar"]):
                                            gaussian_delay(0.8, 0.3, min_s=0.4)  # hesitação pré-clique no Next
                                            print(f"        {Colors.DIM}Clicando em '{btn.text.strip()}'...{Colors.END}")
                                            LinkedInScraper._human_click(driver, btn)
                                            clicked = True
                                            gaussian_delay(1.8, 0.5, min_s=1.2)  # aguarda painel seguinte carregar
                                            break
                                            
                                    if submitted:
                                        break  # Sai do loop de painéis — candidatura já foi enviada
                                            
                                    if not clicked:
                                        # Se não conseguiu clicar em avançar, ou encontrou uma tela de perguntas complexas obrigatórias,
                                        # nós fechamos o modal para ir para a próxima vaga.
                                        print(f"        {Colors.YELLOW}⚠️ Requer intervenção manual. Descartando candidatura para seguir com o loop.{Colors.END}")
                                        close_modal_btn = modal.find_element(By.CSS_SELECTOR, "button[data-test-modal-close-btn], button[aria-label*='Dismiss'], button[aria-label*='Fechar']")
                                        LinkedInScraper._human_click(driver, close_modal_btn)

                                        # LinkedIn às vezes pede confirmação de descarte: "Discard application?"
                                        gaussian_delay(1.2, 0.3, min_s=0.8)
                                        try:
                                            discard_btn = driver.find_element(By.CSS_SELECTOR, "button[data-control-name='discard_application_confirm_btn'], button[data-test-dialog-primary-btn]")
                                            LinkedInScraper._human_click(driver, discard_btn)
                                            print(f"        {Colors.DIM}Descarte confirmado.{Colors.END}")
                                        except Exception:
                                            pass
                                        break
                                        
                                except Exception as e:
                                    print(f"        {Colors.RED}❌ Erro ao tentar avançar no painel: {e}{Colors.END}")
                                    try:
                                        active_elem = driver.switch_to.active_element
                                        active_elem.send_keys(Keys.ESCAPE)
                                    except:
                                        pass
                                    break
                                    
                            human_delay(1.0, 2.0)

                            # --- Contagem e controles de sessao ---
                            applications_sent += 1
                            print(f"      {Colors.GREEN}[{applications_sent}/{MAX_APPLICATIONS}]{Colors.END} Aplicacao processada.")

                            # Cap: encerra quando o limite da sessao e atingido
                            if applications_sent >= MAX_APPLICATIONS:
                                print(f"\n  {Colors.YELLOW}[Cap atingido]{Colors.END} {MAX_APPLICATIONS} aplicacoes. Encerrando sessao com seguranca.")
                                log_session(applications_sent)
                                try:
                                    driver.quit()
                                except:
                                    pass
                                return

                            # Block pause a cada 5 aplicacoes enviadas com sucesso
                            if applications_sent % 5 == 0:
                                block_pause()
                            
                        except Exception as e:
                            print(f"      {Colors.YELLOW}⚠️ Easy Apply ausente nesta vaga ou bloqueado.{Colors.END}")
                            
                    except StaleElementReferenceException:
                        print(f"    {Colors.YELLOW}⚠️ [Stale]{Colors.END} O card da vaga index {index + 1} foi re-renderizado pelo React no meio da ação.")
                    except Exception as e:
                        print(f"    {Colors.RED}❌ [Erro Inesperado]{Colors.END} Falha ao processar item {index + 1}: {e}")
                
                # Delay entre paginas: gaussiano ~18s com jitter (nao-uniforme)
                gaussian_delay(random.gauss(18, 4), sigma_s=3, min_s=10)
                
        print(f"\n{Colors.GREEN}{Colors.BOLD}[Arachne]{Colors.END} Fim da cacada. Todas as URLs e paginas processadas.")
        log_session(applications_sent)

        try:
            driver.quit()
        except:
            pass
