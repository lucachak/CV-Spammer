import argparse
import sys

from components.catho_scraper import run_scraper as scrape_catho
from components.launch_browser import LaunchBrowser
from components.linkedin_scraper import LinkedInScraper
from components.search_builder import SearchBuilder


class ArachneDriver:
    @staticmethod
    def execute():
        parser = argparse.ArgumentParser(
            description="🕷️ Arachne Master Driver - Central Command",
            formatter_class=argparse.RawTextHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
        
        linkedin_parser = subparsers.add_parser("scrape_linkedin", help="Inicia a caçada no LinkedIn (Caminho da Raposa)")
        linkedin_parser.add_argument("--debug", action="store_true", help="Modo debug: desabilita startup_jitter e delays de segurança")
        subparsers.add_parser("scrape_catho", help="Inicia a caçada furtiva na Catho")
        subparsers.add_parser("launch_browser", help="Abre o navegador com o perfil persistente para validação humana")
        
        test_parser = subparsers.add_parser("test", help="Modo de testes e utilitários")
        test_parser.add_argument(
            "action", 
            choices=["url", "browser"], 
            help="'url' para retornar uma URL gerada, 'browser' para abrir o navegador de testes."
        )

        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)

        args = parser.parse_args()

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
