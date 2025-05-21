#!/usr/bin/env python3
"""
Utilitaire en ligne de commande pour gérer les identifiants sécurisés.
"""
import argparse
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.secure_credentials import (
    credential_manager,
    get_credential,
    set_credential,
    delete_credential,
    list_credentials
)

def print_credentials():
    """Affiche tous les identifiants enregistrés."""
    credentials = list_credentials()
    if not credentials:
        print("Aucun identifiant enregistré.")
        return
    
    for service, creds in credentials.items():
        print(f"\n[{service.upper()}]")
        for key, _ in creds.items():
            print(f"  {key}")

def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Gestion des identifiants sécurisés")
    subparsers = parser.add_subparsers(dest='command', help='Commande à exécuter')
    
    # Commande: list
    list_parser = subparsers.add_parser('list', help='Lister les identifiants')
    
    # Commande: get
    get_parser = subparsers.add_parser('get', help='Récupérer un identifiant')
    get_parser.add_argument('service', help='Nom du service')
    get_parser.add_argument('key', help='Clé de l\'identifiant')
    
    # Commande: set
    set_parser = subparsers.add_parser('set', help='Définir un identifiant')
    set_parser.add_argument('service', help='Nom du service')
    set_parser.add_argument('key', help='Clé de l\'identifiant')
    set_parser.add_argument('value', help='Valeur de l\'identifiant')
    
    # Commande: delete
    delete_parser = subparsers.add_parser('delete', help='Supprimer un identifiant')
    delete_parser.add_argument('service', help='Nom du service')
    delete_parser.add_argument('key', help='Clé de l\'identifiant')
    
    # Commande: init
    init_parser = subparsers.add_parser('init', help='Initialiser le fichier de configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'list':
            print_credentials()
            
        elif args.command == 'get':
            value = get_credential(args.service, args.key)
            if value is not None:
                print(f"{args.service}.{args.key} = {value}")
            else:
                print(f"Identifiant non trouvé: {args.service}.{args.key}")
                sys.exit(1)
                
        elif args.command == 'set':
            set_credential(args.service, args.key, args.value)
            print(f"✅ {args.service}.{args.key} mis à jour avec succès")
            
        elif args.command == 'delete':
            if delete_credential(args.service, args.key):
                print(f"✅ {args.service}.{args.key} supprimé avec succès")
            else:
                print(f"❌ Impossible de supprimer {args.service}.{args.key}")
                sys.exit(1)
                
        elif args.command == 'init':
            credential_manager._ensure_credentials_file()
            print("✅ Fichier de configuration initialisé avec succès")
            print(f"Emplacement: {credential_manager.credentials_file.absolute()}")
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
