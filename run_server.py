"""
Script de lancement CIE Manager avec Waitress
Usage : python run_server.py [--host 0.0.0.0] [--port 8000]
"""
import argparse
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

def main():
    parser = argparse.ArgumentParser(description='Lancement CIE Manager')
    parser.add_argument('--host', default='0.0.0.0', help='Adresse (défaut: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port (défaut: 8000)')
    args = parser.parse_args()

    import django
    django.setup()

    from waitress import serve
    from config.wsgi import application

    print(f"╔══════════════════════════════════════════╗")
    print(f"║         CIE Manager — DFC/CIE            ║")
    print(f"║  Serveur : http://{args.host}:{args.port}   ║")
    print(f"║  Ctrl+C pour arrêter                     ║")
    print(f"╚══════════════════════════════════════════╝")

    serve(application, host=args.host, port=args.port, threads=8)

if __name__ == '__main__':
    main()
