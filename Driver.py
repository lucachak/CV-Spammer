import argparse
import sys
from components.linkedin_scraper import LinkedInScraper
from components.catho_scraper import run_scraper as scrape_catho
from components.search_builder import SearchBuilder
from components.launch_browser import LaunchBrowser

class ArachneDriver:
    """Central driver class to orchestrate all scraping and utility commands."""
    
    @staticmethod
    def execute():
        parser = argparse.ArgumentParser(
            description="🕷️ Arachne Master Driver - Central Command",
            formatter_class=argparse.RawTextHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
        
        # Comandos principais
        linkedin_parser = subparsers.add_parser("scrape_linkedin", help="Inicia a caçada no LinkedIn (Caminho da Raposa)")
        linkedin_parser.add_argument("--debug", action="store_true", help="Modo debug: desabilita startup_jitter e delays de segurança")
        subparsers.add_parser("scrape_catho", help="Inicia a caçada furtiva na Catho")
        subparsers.add_parser("launch_browser", help="Abre o navegador com o perfil persistente para validação humana")
        
        # Modo de teste encapsulado
        test_parser = subparsers.add_parser("test", help="Modo de testes e utilitários")
        test_parser.add_argument(
            "action", 
            choices=["url", "browser"], 
            help="'url' para retornar uma URL gerada, 'browser' para abrir o navegador de testes."
        )

        # Se nenhum comando for passado, exibe o painel de ajuda
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)

        args = parser.parse_args()

        # Roteamento elegante dos comandos
        if args.command == "scrape_linkedin":
            LinkedInScraper.scrape_linkedin(debug_mode=getattr(args, 'debug', False))
            
        elif args.command == "scrape_catho":
            scrape_catho()
            
        elif args.command == "launch_browser":
            LaunchBrowser.run()
            
        elif args.command == "test":
            if args.action == "url":
                print(f"🎯 URL de Teste Gerada:\n{SearchBuilder.return_single_url()}")
            elif args.action == "browser":
                LaunchBrowser.run()

if __name__ == "__main__":
    ArachneDriver.execute()