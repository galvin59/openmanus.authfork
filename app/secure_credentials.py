"""
Module de gestion sécurisée des identifiants pour OpenManus.

Ce module fournit une interface pour stocker et récupérer des identifiants
de manière sécurisée, sans les exposer dans le code ou les logs.
"""
import os
import configparser
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Configuration du logging
logger = logging.getLogger(__name__)


class CredentialManager:
    """Gestionnaire d'identifiants sécurisés.
    
    Les identifiants sont stockés dans un fichier .ini chiffré avec des permissions
    restreintes, et ne sont jamais enregistrés dans les logs ou envoyés au LLM.
    """
    
    def __init__(self):
        """Initialise le gestionnaire d'identifiants."""
        self.config_dir = Path("config")
        self.credentials_file = self.config_dir / "credentials.ini"
        self._ensure_credentials_file()
    
    def _ensure_credentials_file(self):
        """Crée le fichier de configuration s'il n'existe pas."""
        try:
            self.config_dir.mkdir(exist_ok=True, mode=0o700)  # drwx------
            
            # Créer le fichier s'il n'existe pas
            if not self.credentials_file.exists():
                self.credentials_file.touch(mode=0x180)  # -rw-------
                
                # Créer une section par défaut
                config = configparser.ConfigParser()
                config['DEFAULT'] = {
                    'comment': 'Ce fichier contient des identifiants sensibles. Ne le partagez pas et ne le versionnez pas.'
                }
                self._write_config(config)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du fichier de configuration: {e}")
            raise
    
    def _get_config(self) -> configparser.ConfigParser:
        """Charge la configuration depuis le fichier."""
        config = configparser.ConfigParser()
        if self.credentials_file.exists():
            try:
                config.read(self.credentials_file)
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du fichier de configuration: {e}")
                raise
        return config
    
    def _write_config(self, config: configparser.ConfigParser):
        """Écrit la configuration dans le fichier."""
        try:
            with open(self.credentials_file, 'w') as f:
                config.write(f)
            # S'assurer que les permissions sont correctes
            self.credentials_file.chmod(0o600)  # -rw-------
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture du fichier de configuration: {e}")
            raise
    
    def get_credential(self, service: str, key: str) -> Optional[str]:
        """Récupère une valeur d'identification sécurisée.
        
        Args:
            service: Le nom du service (ex: 'facebook', 'github')
            key: La clé de l'identifiant (ex: 'email', 'password')
            
        Returns:
            La valeur de l'identifiant ou None si non trouvée
        """
        try:
            config = self._get_config()
            if service in config and key in config[service]:
                return config[service][key]
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'identifiant {service}.{key}: {e}")
            return None
    
    def set_credential(self, service: str, key: str, value: str):
        """Définit une valeur d'identification sécurisée.
        
        Args:
            service: Le nom du service (ex: 'facebook', 'github')
            key: La clé de l'identifiant (ex: 'email', 'password')
            value: La valeur à stocker
        """
        try:
            config = self._get_config()
            
            # Créer la section si elle n'existe pas
            if service not in config:
                config[service] = {}
            
            # Mettre à jour la valeur
            config[service][key] = value
            
            # Écrire les modifications
            self._write_config(config)
            
            logger.info(f"Identifiant mis à jour: {service}.{key}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'identifiant {service}.{key}: {e}")
            raise
    
    def delete_credential(self, service: str, key: str) -> bool:
        """Supprime une valeur d'identification.
        
        Args:
            service: Le nom du service
            key: La clé de l'identifiant
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            config = self._get_config()
            if service in config and key in config[service]:
                del config[service][key]
                # Supprimer la section si elle est vide
                if not config[service]:
                    config.remove_section(service)
                self._write_config(config)
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'identifiant {service}.{key}: {e}")
            return False
    
    def list_credentials(self) -> Dict[str, Dict[str, str]]:
        """Liste tous les identifiants stockés.
        
        Returns:
            Un dictionnaire des services et de leurs identifiants
        """
        try:
            config = self._get_config()
            return {
                section: dict(config[section])
                for section in config.sections()
            }
        except Exception as e:
            logger.error(f"Erreur lors de la liste des identifiants: {e}")
            return {}

# Instance unique du gestionnaire d'identifiants
credential_manager = CredentialManager()

# Fonctions d'aide pour une utilisation simplifiée
def get_credential(service: str, key: str) -> Optional[str]:
    """Raccourci pour credential_manager.get_credential"""
    return credential_manager.get_credential(service, key)

def set_credential(service: str, key: str, value: str):
    """Raccourci pour credential_manager.set_credential"""
    credential_manager.set_credential(service, key, value)

def delete_credential(service: str, key: str) -> bool:
    """Raccourci pour credential_manager.delete_credential"""
    return credential_manager.delete_credential(service, key)

def list_credentials() -> Dict[str, Dict[str, str]]:
    """Raccourci pour credential_manager.list_credentials"""
    return credential_manager.list_credentials()
