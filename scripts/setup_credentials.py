#!/usr/bin/env python3
"""
Script d'installation des identifiants sécurisés pour OpenManus.
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.secure_credentials import credential_manager

def clear_screen():
    """Efface l'écran de la console."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Affiche l'en-tête du programme."""
    clear_screen()
    print("=" * 50)
    print("CONFIGURATION DES IDENTIFIANTS SÉCURISÉS".center(50))
    print("=" * 50)
    print("\nCe programme vous guide pour configurer vos identifiants de manière sécurisée.\n")

def get_yes_no(prompt):
    """Demande une confirmation oui/non."""
    while True:
        response = input(f"{prompt} (o/n): ").strip().lower()
        if response in ('o', 'oui'):
            return True
        elif response in ('n', 'non'):
            return False
        print("Veuillez répondre par 'o' pour oui ou 'n' pour non.")

def setup_credentials():
    """Configure les identifiants de manière interactive."""
    print_header()
    
    # Configuration de Facebook
    print("\n" + "="*50)
    print("CONFIGURATION FACEBOOK".center(50))
    print("="*50)
    
    if get_yes_no("Voulez-vous configurer les identifiants Facebook ?"):
        email = input("\nEntrez votre email Facebook: ").strip()
        password = input("Entrez votre mot de passe Facebook: ").strip()
        
        credential_manager.set_credential("facebook", "email", email)
        credential_manager.set_credential("facebook", "password", password)
        print("\n✅ Identifiants Facebook enregistrés avec succès!")
    
    # Configuration de GitHub
    print("\n" + "="*50)
    print("CONFIGURATION GITHUB".center(50))
    print("="*50)
    
    if get_yes_no("\nVoulez-vous configurer les identifiants GitHub ?"):
        username = input("\nEntrez votre nom d'utilisateur GitHub: ").strip()
        token = input("Entrez votre token d'accès GitHub: ").strip()
        
        credential_manager.set_credential("github", "username", username)
        credential_manager.set_credential("github", "token", token)
        print("\n✅ Identifiants GitHub enregistrés avec succès!")
    
    # Configuration personnalisée
    if get_yes_no("\nVoulez-vous ajouter d'autres identifiants personnalisés ?"):
        while True:
            print("\n" + "-"*50)
            service = input("\nNom du service (ou 'fin' pour terminer): ").strip().lower()
            
            if service in ('fin', ''):
                break
                
            key = input(f"Clé pour {service} (ex: 'api_key', 'username'): ").strip()
            value = input(f"Valeur pour {service}_{key}: ").strip()
            
            credential_manager.set_credential(service, key, value)
            print(f"✅ {service}_{key} enregistré avec succès!")
    
    print("\n" + "="*50)
    print("CONFIGURATION TERMINÉE".center(50))
    print("="*50)
    print("\nVous pouvez maintenant utiliser les identifiants dans vos prompts avec la syntaxe :")
    print("  #nom_du_service_clef#")
    print("\nExemple: #facebook_email#, #github_token#")
    print("\nLe fichier de configuration se trouve dans: config/credentials.ini")
    print("Assurez-vous qu'il est bien ignoré par Git (vérifiez votre .gitignore).")

if __name__ == "__main__":
    try:
        setup_credentials()
    except KeyboardInterrupt:
        print("\n\nConfiguration annulée par l'utilisateur.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Une erreur est survenue: {str(e)}")
        sys.exit(1)
