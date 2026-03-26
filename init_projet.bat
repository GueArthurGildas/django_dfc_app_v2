@echo off
echo ================================================
echo   CIE Manager - Initialisation
echo ================================================
cd /d %~dp0

echo Creation de l'environnement virtuel...
python -m venv venv

echo Installation des dependances...
call venv\Scripts\activate
pip install -r requirements.txt

echo Initialisation de la base de donnees...
python init_projet.py

echo.
echo === Termine ! Lancer start.bat pour demarrer ===
pause
