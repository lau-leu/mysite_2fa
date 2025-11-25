#!/bin/bash
# Script d'installation et configuration Apache pour JupyterLab
# À exécuter sur serverweb (192.168.1.202)

set -e  # Arrêt en cas d'erreur

echo "=== Configuration Apache pour JupyterLab sur serverweb ==="
echo ""

# Vérifier qu'on est root ou avec sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté avec sudo"
    exit 1
fi

echo "📋 Étape 1/6 : Activation des modules Apache nécessaires..."
a2enmod proxy
a2enmod proxy_http
a2enmod proxy_wstunnel
a2enmod rewrite
a2enmod headers
echo "✅ Modules activés"
echo ""

echo "📋 Étape 2/6 : Copie du fichier de configuration..."
# Le fichier doit être dans le répertoire courant ou préciser le chemin
if [ ! -f "apache-jupyterlab.conf" ]; then
    echo "❌ Fichier apache-jupyterlab.conf introuvable dans le répertoire courant"
    echo "Copiez d'abord le fichier depuis le repo mysite_2fa vers ce serveur"
    exit 1
fi

cp apache-jupyterlab.conf /etc/apache2/sites-available/jupyter.leumaire.fr.conf
echo "✅ Fichier copié vers /etc/apache2/sites-available/jupyter.leumaire.fr.conf"
echo ""

echo "📋 Étape 3/6 : Configuration de l'authentification HTTP Basic..."
# Créer le fichier .htpasswd si n'existe pas
if [ ! -f "/etc/apache2/.htpasswd" ]; then
    echo "Création du fichier .htpasswd pour l'utilisateur 'laurent'..."
    echo "Entrez le mot de passe pour JupyterLab:"
    htpasswd -c /etc/apache2/.htpasswd laurent
    echo "✅ Fichier .htpasswd créé"
else
    echo "⚠️  Le fichier /etc/apache2/.htpasswd existe déjà"
    echo "Pour ajouter/modifier l'utilisateur laurent:"
    echo "  sudo htpasswd /etc/apache2/.htpasswd laurent"
fi
echo ""

echo "📋 Étape 4/6 : Vérification de la configuration Apache..."
apache2ctl configtest
echo ""

echo "📋 Étape 5/6 : Activation du site JupyterLab..."
a2ensite jupyter.leumaire.fr
echo "✅ Site activé"
echo ""

echo "📋 Étape 6/6 : Rechargement d'Apache..."
systemctl reload apache2
systemctl status apache2 --no-pager -l
echo ""

echo "✅ Configuration terminée !"
echo ""
echo "🧪 Tests à effectuer:"
echo "1. Vérifier le lien symbolique:"
echo "   ls -la /etc/apache2/sites-enabled/ | grep jupyter"
echo ""
echo "2. Tester l'accès HTTP (depuis votre navigateur):"
echo "   http://jupyter.leumaire.fr"
echo ""
echo "3. Surveiller les logs en cas de problème:"
echo "   sudo tail -f /var/log/apache2/jupyter_error.log"
echo ""
echo "4. Une fois que HTTP fonctionne, configurer HTTPS avec certbot:"
echo "   sudo certbot --apache -d jupyter.leumaire.fr"
echo ""
