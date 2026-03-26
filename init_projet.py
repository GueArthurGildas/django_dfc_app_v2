"""
Script d'initialisation CIE Manager
Lance les migrations et charge les fixtures dans le bon ordre.
Usage : python init_projet.py
"""
import os
import sys
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=== CIE Manager — Initialisation ===\n")

print("1. Migrations authentication...")
call_command('makemigrations', 'authentication', verbosity=0)

print("2. Migrations organisation...")
call_command('makemigrations', 'organisation', verbosity=0)

print("3. Migrations operations...")
call_command('makemigrations', 'operations', verbosity=0)

print("4. Migrations comptabilite...")
call_command('makemigrations', 'comptabilite', verbosity=0)

print("5. Application des migrations...")
call_command('migrate', verbosity=1)

print("\n6. Chargement fixtures — Rôles...")
call_command('loaddata', 'fixtures/roles.json', verbosity=1)

print("7. Chargement fixtures — Sous-Directions (SDCC + SDPCC)...")
call_command('loaddata', 'fixtures/sous_directions.json', verbosity=1)

print("8. Chargement fixtures — Sections...")
call_command('loaddata', 'fixtures/sections.json', verbosity=1)

print("\n9. Création du superutilisateur admin...")
from apps.authentication.models import Utilisateur, Role
if not Utilisateur.objects.filter(username='admin').exists():
    role_admin = Role.objects.get(code='admin')
    Utilisateur.objects.create_superuser(
        username='admin',
        password='admin123',
        email='admin@cie-manager.ci',
        first_name='Admin',
        last_name='CIE',
        role=role_admin,
        matricule='ADM-001'
    )
    print("   Superutilisateur créé : admin / admin123")
else:
    print("   Superutilisateur déjà existant.")

print("\n=== Initialisation terminée ✓ ===")
print("Lancer le serveur : python run_server.py")
print("Ou en dev        : python manage.py runserver")
