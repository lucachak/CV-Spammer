import time
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
    """
    Delay com distribuição gaussiana — indistinguível de padrão humano real.
    random.uniform() produz distribuição uniforme detectada por análise estatística.
    Humanos seguem curva gaussiana com cauda longa (diståncias, leituras, distrações).
    """
    delay = max(min_s, random.gauss(center_s, sigma_s))
    time.sleep(delay)


# ==========================================
# FIELD TYPE CLASSIFIER
# ==========================================

class FieldType(Enum):
    """
    Enum representando os tipos de campos de input que podem aparecer
    num formulário do LinkedIn Easy Apply.
    """
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
        """
        Classifica o tipo de campo de um formulário dado o `input_id` do label.

        Retorna: (FieldType, element | None)
        O elemento retornado é o input DOM encontrado, ou None em caso de falha.

        Lógica de classificação:
          1. Tenta localizar por ID direto.
          2. Inspeciona tag_name e atributo `type`.
          3. Se for <input>, diferencia: text/number → TEXT_INPUT, radio → RADIO_GROUP,
             checkbox → CHECKBOX.
          4. <select> → SELECT_DROPDOWN
          5. <textarea> → TEXTAREA
          6. Qualquer outro → UNKNOWN
        """
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
        """
        Tenta encontrar uma resposta para a pergunta baseada nos dados do currículo.

        Ordem de resolução:
          1. Proficiência em idiomas  → meu_curriculo.languages
          2. Anos de experiência com tecnologia → meu_curriculo.years_of_experience
          3. Sumário geral / experiência descritiva → meu_curriculo.summary

        Retorna a resposta como string, ou None se nenhuma regra bater.
        """
        # ── 1. Idiomas ──
        # Mapa de variações de keyword → chave em meu_curriculo.languages
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
        """
        Clique humanizado com trajetória de aproximação e jitter.

        O problema de execute_script('click'): dispara MouseEvent com clientX=0, clientY=0
        — coordenadas impossíveis para um humano. LinkedIn e outros sistemas anti-bot
        monitoram esses valores via event listeners nativos.

        Esta função usa ActionChains nativo que gera eventos reais com coordenadas válidas:
          1. Fase Abordagem: move o cursor para perto do elemento (simula chegada do mouse)
          2. Fase Refinamento: micro-ajustes incrementais até o ponto de clique
          3. Fase Clique: hesitação final + clique nativo (MouseEvent com clientX/Y reais)
        """
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
            # Fallback seguro caso o ActionChains falhe (elemento fora de tela, etc.)
            try:
                driver.execute_script("arguments[0].click();", element)
            except Exception:
                pass
            return False

    @staticmethod
    def _micro_wander(driver, intensity: int = 2):
        """
        Move o mouse levemente durante esperas longas.
        Simula o usuário olhando para a tela enquanto aguarda carregamento.
        Sem isso, o cursor fica completamente parado — padrão não-humano.
        """
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
        """
        Seleciona a melhor opção num <select> dado um valor preferido.

        Lógica de matching (ordem de prioridade):
          1. Match exato (case-insensitive)
          2. Opção contém o `preferred` (ex: 'fluente' em 'Fluente / Nativo')
          3. `preferred` contém o texto da opção (ex: 'Fluent' bate em 'Flu')
          4. Heurística sim/não: procura 'sim'/'yes'
          5. Fallback: index 1 (primeira opção real, pulando placeholder)

        Retorna True se conseguiu selecionar algo, False caso contrário.
        """
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
        """
        Escaneia o painel atual por labels.
        Classifica cada campo pelo tipo DOM, resolve a resposta correta via currículo,
        e aplica a estratégia de preenchimento adequada por tipo.

        Fluxo por campo:
          1. Classificar tipo DOM (_classify_field)
          2. Logar tipo detectado (_log_field_detection)
          3. Tentar resolver resposta do currículo (_resolve_from_resume)
          4. Aplicar resposta por tipo de campo
        """
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
                        # Campo já preenchido, não sobrescreve
                        continue
                    if resolved:
                        elem.clear()
                        elem.send_keys(resolved)
                        print(f"          {Colors.CYAN}↳ Preenchido (resume):{Colors.END} '{resolved[:30]}'")
                    elif any(k in text_lower for k in ["há quantos", "ha quantos", "quantos anos", "how many", "years"]):
                        # Fallback: número aleatório conservador
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
                        # Se temos resolved, tenta bater com os labels dos radios
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
    def scrape_linkedin():
        def human_delay(min_s=1.5, max_s=3.5):
            """Converte a assinatura min/max antiga para gaussian_delay — distribuição realista."""
            center = (min_s + max_s) / 2
            sigma  = (max_s - min_s) / 4
            gaussian_delay(center, sigma, min_s=min_s * 0.6)

        print(f"{Colors.GREEN}{Colors.BOLD}[Arachne LinkedIn Scraper]{Colors.END} Operação 'Caminho da Raposa' Iniciada.")
        conf, credentials = load_env_configurations()
        
        # Iniciando driver (headless mantido de acordo com a conf inicial do bot, falso por padrao para monitorar)
        driver = setup_driver(conf, headless=False)
        wait = WebDriverWait(driver, 12)
        
        # Injeta o login autônomo e barra a execução se falhar completamente
        if not LinkedInScraper.login_to_linkedin(driver, credentials, conf):
            print(f"{Colors.RED}❌ [EXIT]{Colors.END} Falha na validação de login. Operação cancelada para evitar loop em páginas bloqueadas.")
            try:
                driver.quit()
            except:
                pass
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
                
                # Defesa Lógica: Se fomos redirecionados para o login, a sessão nativa falhou.
                current_url_lower = driver.current_url.lower()
                if "login" in current_url_lower or "checkpoint" in current_url_lower:
                    print(f"  {Colors.RED}❌ [FATAL]{Colors.END} A sessão nativa foi derrubada ou interceptada (Login Wall/Captcha). Abortando a caçada atual.")
                    break
                
                # Explicit Wait: Aguardando o container principal carregar em vez de um sleep arbitrário
                try:
                    # Caminho da Raposa: Busca o container oficial (antigo e novo) ou qualquer link de vaga como evidência
                    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "ul.scaffold-layout__list-container, .jobs-search-results-list, ul.jobs-search__results-list") or d.find_elements(By.XPATH, "//a[contains(@href, '/jobs/view/')]"))
                except TimeoutException:
                    print(f"  {Colors.RED}❌ [Timeout]{Colors.END} A lista de vagas não carregou na página {page + 1}. Captcha ou fim da linha? Pulando.")
                    continue
                    
                human_delay(2.5, 4.5) # Tempo extra para os cards renderizarem completamente (SPAs...)
                
                # Buscando elementos de forma resiliente - Seletores velhos, novos e o Caminho do Rato (fallback)
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
                
                for index in range(total_items):
                    try:
                        # Buscando novamente para evitar StaleElementReferenceException (DOM updates são frequentes aqui)
                        current_cards = driver.find_elements(By.XPATH, " | ".join(xpath_selectors))
                        current_cards = list(dict.fromkeys(current_cards))
                        if index >= len(current_cards):
                            break
                            
                        card = current_cards[index]

                        # Skip probabilístico leve (~12%) — humanos não clicam em tudo que veem
                        if random.random() < 0.12:
                            print(f"    {Colors.DIM}- [{index + 1}/{total_items}] [passando] Título ignorado naturalmente.{Colors.END}")
                            gaussian_delay(0.4, 0.15, min_s=0.2)
                            continue

                        # Scroll suave até o card
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", card)
                        # Pausa de "leitura" — tempo variável como usuário lendo título e empresa
                        gaussian_delay(1.0, 0.45, min_s=0.5)
                        LinkedInScraper._micro_wander(driver, intensity=1)
                        
                        # Buscando o link exato da vaga, não a adivinhação de <ul> <li> <a> <span>
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
                            # O Caminho da Serpente: Qualquer link que leve a /jobs/view/
                            try:
                                title_link = card.find_element(By.XPATH, ".//a[contains(@href, '/jobs/view/')]")
                            except:
                                # Fallback bruto (O Caminho do Rato, caso o layout tenha quebrado completamente)
                                try:
                                    title_link = card.find_element(By.TAG_NAME, "a")
                                except:
                                    print(f"    {Colors.DIM}- [{index + 1}/{total_items}]{Colors.END} {Colors.RED}[!] Vaga blindada. Impossível localizar o link <a>.{Colors.END}")
                                    continue

                        title = title_link.text.strip() or "Vaga sem título"
                        print(f"    {Colors.DIM}- [{index + 1}/{total_items}]{Colors.END} Acessando: {Colors.BOLD}{title}{Colors.END}")

                        # _human_click gera MouseEvent real (clientX/Y válidos) — sem JS inject
                        LinkedInScraper._human_click(driver, title_link)
                        
                        # Tempo realista + micro-wander enquanto o painel da direita carrega
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
                            
                            # Iterando pelos painéis do Easy Apply (Candidatura Simplificada)
                            print(f"      {Colors.BLUE}🔄 Interagindo com o modal de candidatura...{Colors.END}")
                            
                            for step in range(10):  # Limite máximo de 10 telas para evitar loops infinitos
                                try:
                                    # Verifica se o modal ainda está aberto
                                    modal = driver.find_element(By.CSS_SELECTOR, "div[data-test-modal-id], div.jobs-easy-apply-modal, div[role='dialog']")
                                except Exception:
                                    print(f"      {Colors.GREEN}✅ Modal finalizado ou fechado.{Colors.END}")
                                    break
                                
                                # Tenta pegar e printar o título do painel atual
                                try:
                                    header = modal.find_element(By.CSS_SELECTOR, "h3, .pb4 h3, .artdeco-modal__header h3")
                                    print(f"        {Colors.CYAN}➡️ Painel [{step+1}]: {header.text.strip()}{Colors.END}")
                                except Exception:
                                    pass
                                    
                                human_delay(1.0, 2.0)
                                LinkedInScraper._micro_wander(driver, intensity=1)  # cursor se move enquanto lê o painel

                                # Aciona a heurística de preenchimento autônomo
                                LinkedInScraper.answer_modal_questions(driver, modal, conf)
                                
                                # Procura pelos botões de avanço: Next, Avançar, Review, Revisar, Submit
                                try:
                                    # Botões primários geralmente têm a classe artdeco-button--primary
                                    primary_buttons = modal.find_elements(By.CSS_SELECTOR, "button.artdeco-button--primary")
                                    
                                    clicked = False
                                    for btn in primary_buttons:
                                        btn_text = btn.text.strip().lower()
                                        if any(word in btn_text for word in ["next", "avançar", "continue", "continuar", "review", "revisar"]):
                                            gaussian_delay(0.8, 0.3, min_s=0.4)  # hesitação pré-clique no Next
                                            print(f"        {Colors.DIM}Clicando em '{btn.text.strip()}'...{Colors.END}")
                                            LinkedInScraper._human_click(driver, btn)
                                            clicked = True
                                            gaussian_delay(1.8, 0.5, min_s=1.2)  # aguarda painel seguinte carregar
                                            break
                                        elif any(word in btn_text for word in ["submit", "enviar"]):
                                            # Se for o botão final, não vamos submeter para evitar spam real durante testes,
                                            # a não ser que seja explicitamente solicitado. Vou clicar por enquanto para finalizar.
                                            print(f"        {Colors.GREEN}🎯 Chegou no botão Final '{btn.text.strip()}'! (Abortando submissão de teste para segurança){Colors.END}")
                                            # Para habilitar a submissão real: driver.execute_script("arguments[0].click();", btn)
                                            clicked = False # Força o loop a fechar o modal na próxima etapa
                                            break
                                            
                                    if not clicked:
                                        # Se não conseguiu clicar em avançar, ou encontrou uma tela de perguntas complexas obrigatórias,
                                        # nós fechamos o modal para ir para a próxima vaga.
                                        print(f"        {Colors.YELLOW}⚠️ Requer intervenção manual ou chegamos no fim. Descartando candidatura para seguir com o loop.{Colors.END}")
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
                            
                        except Exception as e:
                            print(f"      {Colors.YELLOW}⚠️ Easy Apply ausente nesta vaga ou bloqueado.{Colors.END}")
                            
                    except StaleElementReferenceException:
                        print(f"    {Colors.YELLOW}⚠️ [Stale]{Colors.END} O card da vaga index {index + 1} foi re-renderizado pelo React no meio da ação.")
                    except Exception as e:
                        print(f"    {Colors.RED}❌ [Erro Inesperado]{Colors.END} Falha ao processar item {index + 1}: {e}")
                
                human_delay(2.0, 3.5)
                
        print(f"\n{Colors.GREEN}{Colors.BOLD}🕷️ [Arachne]{Colors.END} Fim da caçada. Todas as URLs e páginas processadas.")
        
        try:
            driver.quit()
        except:
            pass
