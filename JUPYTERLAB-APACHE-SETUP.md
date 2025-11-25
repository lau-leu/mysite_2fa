# Configuration Apache pour JupyterLab

Guide d'installation pour JupyterLab via Apache sur votre architecture réseau.

## 🏗️ Architecture

```
Internet (OVH)
    ↓
192.168.1.202 (Apache - romane.leumaire.fr) ← Configuration JupyterLab ICI
    ↓ Direct reverse proxy
192.168.1.96 (JupyterLab sur :8888)
```

## 🚀 Installation

### Étape 1 : Sur vm-ia (192.168.1.96) - Installer JupyterLab

```bash
# SSH sur vm-ia
ssh user@192.168.1.96

# Installer JupyterLab
pip3 install jupyterlab

# Copier le service systemd
sudo cp jupyterlab.service /etc/systemd/system/

# Modifier le user si nécessaire
sudo nano /etc/systemd/system/jupyterlab.service

# Activer et démarrer
sudo systemctl daemon-reload
sudo systemctl enable jupyterlab
sudo systemctl start jupyterlab

# Vérifier
sudo systemctl status jupyterlab
curl http://localhost:8888
```

### Étape 2 : Sur romane (192.168.1.202) - Configurer Apache

```bash
# SSH sur romane
ssh user@192.168.1.202

# Activer les modules Apache nécessaires
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod proxy_wstunnel
sudo a2enmod rewrite
sudo a2enmod headers
sudo a2enmod ssl

# Copier la configuration
sudo cp apache-jupyterlab.conf /etc/apache2/sites-available/jupyter.leumaire.fr.conf

# Activer le site
sudo a2ensite jupyter.leumaire.fr.conf

# Tester la configuration
sudo apache2ctl configtest

# Recharger Apache
sudo systemctl reload apache2
```

### Étape 3 : Configurer le DNS chez OVH

1. Connectez-vous à **OVH**
2. Allez dans **Web Cloud** → **Noms de domaine** → **leumaire.fr**
3. Onglet **Zone DNS**
4. Cliquez sur **Ajouter une entrée**
5. Type **A** :
   - **Sous-domaine** : `jupyter`
   - **Cible** : **IP publique de 192.168.1.202** (votre IP Internet)
   - **TTL** : 3600
6. Validez

### Étape 4 : Configurer l'authentification (Recommandé)

```bash
# Sur romane (192.168.1.202)
# Créer le fichier de mots de passe
sudo htpasswd -c /etc/apache2/.htpasswd laurent

# Ajouter d'autres utilisateurs (sans -c)
sudo htpasswd /etc/apache2/.htpasswd autre_user

# Vérifier les permissions
sudo chmod 644 /etc/apache2/.htpasswd
sudo chown root:www-data /etc/apache2/.htpasswd
```

### Étape 5 : Activer HTTPS avec Let's Encrypt

```bash
# Sur romane (192.168.1.202)
# Installer certbot
sudo apt install certbot python3-certbot-apache -y

# Obtenir un certificat SSL
sudo certbot --apache -d jupyter.leumaire.fr

# Renouvellement automatique déjà configuré
sudo certbot renew --dry-run
```

## 🔒 Sécurité - Firewall

### Sur vm-ia (192.168.1.96)

JupyterLab ne doit être accessible QUE depuis romane (192.168.1.202) :

```bash
# Sur vm-ia
sudo ufw allow from 192.168.1.202 to any port 8888
sudo ufw deny 8888  # Bloquer l'accès public
sudo ufw status
```

### Sur romane (192.168.1.202)

Les ports 80 et 443 sont déjà ouverts (votre configuration actuelle).

## ✅ Test

1. **Vérifier JupyterLab sur vm-ia** :
   ```bash
   curl http://192.168.1.96:8888
   ```

2. **Tester depuis romane** :
   ```bash
   # Sur 192.168.1.202
   curl http://192.168.1.96:8888
   ```

3. **Tester depuis Internet** :
   - Ouvrez : `http://jupyter.leumaire.fr`
   - Vous devriez voir la popup d'authentification
   - Puis l'interface JupyterLab

4. **Tester l'exécution de code** :
   - Créez un nouveau notebook
   - Exécutez du code Python
   - Vérifiez que ça fonctionne (WebSockets actifs)

## 🐛 Dépannage

### Apache ne démarre pas

```bash
# Vérifier la syntaxe
sudo apache2ctl configtest

# Voir les logs
sudo tail -f /var/log/apache2/error.log
sudo tail -f /var/log/apache2/jupyter_error.log
```

### Erreur 502 Bad Gateway

```bash
# Vérifier que JupyterLab tourne sur vm-ia
ssh user@192.168.1.96
sudo systemctl status jupyterlab

# Vérifier la connectivité depuis romane
telnet 192.168.1.96 8888
```

### WebSockets ne fonctionnent pas

Vérifiez que les modules sont activés :

```bash
sudo apache2ctl -M | grep proxy
# Doit montrer :
# proxy_module (shared)
# proxy_http_module (shared)
# proxy_wstunnel_module (shared)
```

Si manquants :
```bash
sudo a2enmod proxy_wstunnel
sudo systemctl restart apache2
```

### Authentification ne fonctionne pas

```bash
# Vérifier le fichier htpasswd
sudo cat /etc/apache2/.htpasswd

# Retester le mot de passe
sudo htpasswd -v /etc/apache2/.htpasswd laurent
```

## 📝 Commandes utiles

```bash
# Voir les logs en temps réel
sudo tail -f /var/log/apache2/jupyter_access.log
sudo tail -f /var/log/apache2/jupyter_error.log

# Recharger Apache
sudo systemctl reload apache2

# Redémarrer Apache
sudo systemctl restart apache2

# Voir le statut
sudo systemctl status apache2
```

## 🎯 Alternative : Sous-chemin au lieu de sous-domaine

Si vous préférez `https://django.leumaire.fr/jupyter/` :

Dans votre VirtualHost `django.leumaire.fr` sur romane, ajoutez :

```apache
<Location /jupyter/>
    ProxyPass http://192.168.1.96:8888/ upgrade=websocket
    ProxyPassReverse http://192.168.1.96:8888/
    ProxyPreserveHost On

    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Prefix "/jupyter"
</Location>
```

Et configurez JupyterLab :
```bash
# Sur vm-ia
nano ~/.jupyter/jupyter_lab_config.py
# Ajoutez :
c.ServerApp.base_url = '/jupyter/'
```

## 📊 Résumé

| Composant | Serveur | Port | Rôle |
|-----------|---------|------|------|
| Apache | 192.168.1.202 | 80/443 | Point d'entrée + Reverse proxy |
| JupyterLab | 192.168.1.96 | 8888 | Application JupyterLab |

**URL finale** : `https://jupyter.leumaire.fr`

Avec cette configuration :
- ✅ Support complet des WebSockets
- ✅ Exécution de code Python
- ✅ Terminaux interactifs
- ✅ Authentification HTTP Basic
- ✅ HTTPS avec Let's Encrypt
- ✅ Architecture cohérente avec votre réseau existant
