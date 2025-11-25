# Configuration JupyterLab Standalone via Apache

Ce guide configure un accès **direct** à JupyterLab via `https://jupyter.leumaire.fr` avec :
- ✅ Support complet WebSocket (exécution de code)
- ✅ Authentification HTTP Basic
- ✅ SSL/HTTPS avec Let's Encrypt
- ✅ Performance optimale

## 🎯 Architecture

```
Internet
    ↓
serverweb (192.168.1.202) - Apache
    ↓ (proxy + WebSocket)
vm-ia (192.168.1.96:8889) - JupyterLab Standalone
```

**Note :** Cette instance est **séparée** de celle utilisée par Django (port 8888).

## 📋 Étape 1 : Sur vm-ia (192.168.1.96)

### 1.1 Créer le service JupyterLab standalone

```bash
# Sur vm-ia
sudo cp jupyterlab-standalone.service /etc/systemd/system/

# Recharger systemd
sudo systemctl daemon-reload

# Activer et démarrer le service
sudo systemctl enable jupyterlab-standalone
sudo systemctl start jupyterlab-standalone

# Vérifier
sudo systemctl status jupyterlab-standalone

# Tester
curl http://localhost:8889/lab
```

### 1.2 Configurer le firewall

```bash
# Autoriser serverweb (192.168.1.202) à accéder au port 8889
sudo ufw allow from 192.168.1.202 to any port 8889

# Bloquer pour tous les autres
sudo ufw deny 8889

# Vérifier
sudo ufw status
```

## 📋 Étape 2 : Sur serverweb (192.168.1.202)

### 2.1 Activer les modules Apache nécessaires

```bash
# Sur serverweb
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod proxy_wstunnel
sudo a2enmod rewrite
sudo a2enmod headers
sudo a2enmod ssl
```

### 2.2 Copier la configuration Apache

```bash
# Copier le fichier de configuration
sudo cp apache-jupyter-standalone.conf /etc/apache2/sites-available/jupyter.leumaire.fr.conf

# OU créer manuellement
sudo nano /etc/apache2/sites-available/jupyter.leumaire.fr.conf
# (Coller le contenu du fichier apache-jupyter-standalone.conf)
```

### 2.3 Créer l'authentification HTTP Basic

```bash
# Créer le fichier de mots de passe
sudo htpasswd -c /etc/apache2/.htpasswd laurent

# Entrez le mot de passe quand demandé
# Répétez pour confirmer

# Vérifier
sudo cat /etc/apache2/.htpasswd
```

### 2.4 Tester la configuration Apache

```bash
# Tester la syntaxe
sudo apache2ctl configtest

# Devrait afficher "Syntax OK"
```

### 2.5 Activer le site

```bash
# Activer le site (SANS chemin, juste le nom)
sudo a2ensite jupyter.leumaire.fr

# Vérifier que le lien symbolique est créé
ls -la /etc/apache2/sites-enabled/ | grep jupyter

# Recharger Apache
sudo systemctl reload apache2

# Vérifier le statut
sudo systemctl status apache2
```

## 📋 Étape 3 : Configuration DNS

Sur **OVH** (ou votre provider DNS) :

1. Connectez-vous à votre espace client OVH
2. Allez dans "Noms de domaine" → leumaire.fr
3. Onglet "Zone DNS"
4. Ajoutez un enregistrement **A** :
   - Sous-domaine : `jupyter`
   - Type : `A`
   - Cible : IP publique de serverweb
   - TTL : 3600 (1 heure)

**Propagation DNS :** Attendez 5-30 minutes pour que le DNS se propage.

### Vérifier la propagation DNS

```bash
# Depuis n'importe où
nslookup jupyter.leumaire.fr

# Ou
dig jupyter.leumaire.fr
```

## 📋 Étape 4 : Test HTTP (avant SSL)

Une fois le DNS propagé :

1. Ouvrez votre navigateur
2. Allez sur **`http://jupyter.leumaire.fr`**
3. Entrez vos identifiants HTTP Basic (laurent / mot-de-passe)
4. L'interface JupyterLab devrait se charger

### Tester l'exécution de code

1. Créez un nouveau notebook Python 3
2. Dans une cellule, tapez : `print("Hello from JupyterLab!")`
3. Exécutez (Shift+Entrée)
4. Le code devrait s'exécuter et afficher "Hello from JupyterLab!"

✅ Si ça fonctionne, les WebSockets sont OK !

## 📋 Étape 5 : Configurer HTTPS avec Let's Encrypt

```bash
# Sur serverweb
# Installer certbot si pas déjà fait
sudo apt install certbot python3-certbot-apache

# Obtenir et installer le certificat SSL
sudo certbot --apache -d jupyter.leumaire.fr

# Répondez aux questions :
# - Email : votre email
# - Termes : Accepter
# - Redirection HTTPS : Oui (recommandé)

# Certbot va automatiquement :
# 1. Obtenir le certificat
# 2. Modifier la config Apache
# 3. Activer HTTPS
# 4. Rediriger HTTP → HTTPS
```

### Vérifier le renouvellement automatique

```bash
# Tester le renouvellement (dry-run)
sudo certbot renew --dry-run

# Le renouvellement est automatique via cron/systemd timer
```

## 📋 Étape 6 : Test final HTTPS

1. Allez sur **`https://jupyter.leumaire.fr`**
2. Vérifiez le certificat SSL (cadenas vert)
3. Authentifiez-vous (HTTP Basic)
4. Testez l'exécution de code

## 🔍 Troubleshooting

### Erreur 502 Bad Gateway

**Cause :** Apache ne peut pas joindre JupyterLab sur vm-ia

**Solutions :**
```bash
# Sur vm-ia
sudo systemctl status jupyterlab-standalone
sudo journalctl -u jupyterlab-standalone -f

# Tester localement
curl http://localhost:8889/lab

# Vérifier le firewall
sudo ufw status
```

### Erreur 503 Service Unavailable

**Cause :** JupyterLab n'est pas démarré

**Solution :**
```bash
# Sur vm-ia
sudo systemctl start jupyterlab-standalone
```

### Les WebSockets ne fonctionnent pas

**Symptômes :** L'interface se charge mais le code ne s'exécute pas

**Solutions :**
```bash
# Sur serverweb
# Vérifier que mod_proxy_wstunnel est activé
apache2ctl -M | grep proxy_wstunnel

# Si absent
sudo a2enmod proxy_wstunnel
sudo systemctl reload apache2
```

### Vérifier les logs Apache

```bash
# Sur serverweb
sudo tail -f /var/log/apache2/jupyter_error.log
sudo tail -f /var/log/apache2/jupyter_ssl_error.log
```

## 📊 Comparaison des deux approches

### Via Django (https://django.leumaire.fr/jupyterlab/)
- ✅ Authentification Django + 2FA
- ✅ Interface unifiée
- ❌ WebSockets limités (exécution peut ne pas marcher)
- ❌ Performance réduite (double proxy)

### Via Apache (https://jupyter.leumaire.fr)
- ✅ WebSockets complets (exécution de code garantie)
- ✅ Performance maximale
- ✅ Configuration simple
- ⚠️ HTTP Basic Auth (pas Django 2FA)
- ⚠️ Site séparé

## 🔐 Sécurité

### Renforcer HTTP Basic Auth

```bash
# Ajouter plusieurs utilisateurs
sudo htpasswd /etc/apache2/.htpasswd alice
sudo htpasswd /etc/apache2/.htpasswd bob

# Changer le mot de passe
sudo htpasswd /etc/apache2/.htpasswd laurent
```

### Restreindre l'accès par IP (optionnel)

Éditez `/etc/apache2/sites-available/jupyter.leumaire.fr.conf` :

```apache
<Location />
    AuthType Basic
    AuthName "JupyterLab Access"
    AuthUserFile /etc/apache2/.htpasswd
    Require valid-user

    # N'autoriser que certaines IPs
    Require ip 1.2.3.4  # Remplacez par votre IP publique
</Location>
```

## 🔄 Maintenance

### Redémarrer JupyterLab

```bash
# Sur vm-ia
sudo systemctl restart jupyterlab-standalone
```

### Mettre à jour JupyterLab

```bash
# Sur vm-ia
source /home/laurent/vm-ia-jupyterlab/venv/bin/activate
pip install --upgrade jupyterlab
sudo systemctl restart jupyterlab-standalone
```

### Renouveler le certificat SSL

Le renouvellement est automatique, mais si besoin :

```bash
# Sur serverweb
sudo certbot renew
sudo systemctl reload apache2
```

## 📝 Résumé des URLs

- **Django (avec 2FA)** : https://django.leumaire.fr/jupyterlab/
  - Port vm-ia : 8888
  - WebSocket : Limité
  - Usage : Navigation, visualisation

- **Apache (HTTP Basic)** : https://jupyter.leumaire.fr
  - Port vm-ia : 8889
  - WebSocket : Complet
  - Usage : Développement, exécution de code

Les deux peuvent coexister sans problème !
