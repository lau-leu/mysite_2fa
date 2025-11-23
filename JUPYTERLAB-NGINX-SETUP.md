# Configuration Nginx pour JupyterLab

Guide complet pour configurer JupyterLab avec Nginx et support WebSockets.

## 📋 Prérequis

- JupyterLab installé sur vm-ia (192.168.1.96)
- Nginx installé sur django-app (192.168.1.58)
- Accès SSH aux deux serveurs

## 🚀 Installation

### Étape 1 : Installer et démarrer JupyterLab sur vm-ia

```bash
# Sur vm-ia (192.168.1.96)
ssh user@192.168.1.96

# Installer JupyterLab
pip3 install jupyterlab

# Copier le fichier service
sudo cp jupyterlab.service /etc/systemd/system/

# Modifier le user dans le service si nécessaire
sudo nano /etc/systemd/system/jupyterlab.service
# Changez "User=laurent" par votre utilisateur

# Activer et démarrer
sudo systemctl daemon-reload
sudo systemctl enable jupyterlab
sudo systemctl start jupyterlab

# Vérifier
sudo systemctl status jupyterlab
curl http://localhost:8888  # Doit répondre
```

### Étape 2 : Installer Nginx sur django-app (si pas déjà fait)

```bash
# Sur django-app (192.168.1.58)
ssh laurent@192.168.1.58

# Installer Nginx
sudo apt update
sudo apt install nginx -y

# Vérifier l'installation
nginx -v
```

### Étape 3 : Configurer Nginx pour JupyterLab

```bash
# Sur django-app
# Copier la configuration
sudo cp nginx-jupyterlab.conf /etc/nginx/sites-available/jupyterlab

# Créer un lien symbolique
sudo ln -s /etc/nginx/sites-available/jupyterlab /etc/nginx/sites-enabled/

# Tester la configuration
sudo nginx -t

# Recharger Nginx
sudo systemctl reload nginx
```

### Étape 4 : Configuration DNS

Ajoutez une entrée DNS pour `jupyter.leumaire.fr` pointant vers **192.168.1.58**.

Ou utilisez un sous-chemin sur le domaine existant (voir option alternative ci-dessous).

### Étape 5 : HTTPS avec Let's Encrypt (Recommandé)

```bash
# Sur django-app
# Installer certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtenir un certificat SSL
sudo certbot --nginx -d jupyter.leumaire.fr

# Le renouvellement automatique est déjà configuré
sudo certbot renew --dry-run
```

## 🔧 Options alternatives

### Option A : Sous-domaine dédié (Recommandé)

**URL** : `https://jupyter.leumaire.fr`

✅ Avantages :
- Configuration plus propre
- Plus facile à gérer
- Certificat SSL séparé

Utilisez la configuration fournie telle quelle.

### Option B : Sous-chemin sur django.leumaire.fr

**URL** : `https://django.leumaire.fr/jupyter/`

Modifiez la configuration Nginx :

```nginx
# Dans /etc/nginx/sites-available/default ou votre site principal

location /jupyter/ {
    proxy_pass http://192.168.1.96:8888/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # WebSocket
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
    proxy_buffering off;

    # Réécriture pour JupyterLab
    rewrite ^/jupyter/(.*) /$1 break;
}

location ~ ^/jupyter/(api/kernels|terminals)/ {
    proxy_pass http://192.168.1.96:8888;
    # ... même configuration WebSocket
}
```

Et configurez JupyterLab pour connaître son préfixe :

```bash
# Sur vm-ia, éditer ~/.jupyter/jupyter_lab_config.py
c.ServerApp.base_url = '/jupyter/'
```

## 🔒 Sécurité

### Authentification

JupyterLab est configuré sans token/password dans le service systemd pour simplifier l'accès via le proxy.

**⚠️ Important** : Ajoutez une authentification Nginx si vous exposez sur Internet :

```nginx
# Dans le bloc server
auth_basic "JupyterLab Access";
auth_basic_user_file /etc/nginx/.htpasswd;
```

Créer le fichier de mot de passe :

```bash
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd votre_utilisateur
```

### Firewall

```bash
# Sur vm-ia, autoriser seulement django-app à accéder au port 8888
sudo ufw allow from 192.168.1.58 to any port 8888
sudo ufw deny 8888  # Bloquer l'accès public
```

## ✅ Test

1. Vérifiez que JupyterLab est accessible :
   ```bash
   curl http://192.168.1.96:8888
   ```

2. Testez via Nginx :
   ```bash
   curl http://jupyter.leumaire.fr
   # ou
   curl http://django.leumaire.fr/jupyter/
   ```

3. Ouvrez dans le navigateur et testez :
   - Navigation des fichiers ✅
   - Création de notebook ✅
   - Exécution de code Python ✅
   - Terminal interactif ✅

## 🐛 Dépannage

### JupyterLab ne répond pas

```bash
# Sur vm-ia
sudo systemctl status jupyterlab
sudo journalctl -u jupyterlab -n 50
```

### Nginx erreur 502

```bash
# Vérifier que vm-ia:8888 est accessible depuis django-app
telnet 192.168.1.96 8888

# Vérifier les logs Nginx
sudo tail -f /var/log/nginx/jupyterlab_error.log
```

### WebSockets ne fonctionnent pas

Vérifiez que la configuration Nginx inclut bien :
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

## 📝 Maintenance

### Mettre à jour JupyterLab

```bash
# Sur vm-ia
pip3 install --upgrade jupyterlab
sudo systemctl restart jupyterlab
```

### Voir les logs

```bash
# JupyterLab
sudo journalctl -u jupyterlab -f

# Nginx
sudo tail -f /var/log/nginx/jupyterlab_access.log
sudo tail -f /var/log/nginx/jupyterlab_error.log
```

## 🎯 Résumé

Avec cette configuration :
- ✅ JupyterLab pleinement fonctionnel
- ✅ Support WebSockets pour l'exécution de code
- ✅ Terminaux interactifs
- ✅ HTTPS sécurisé
- ✅ Performance optimale
- ✅ Démarrage automatique au boot

**URL finale** : `https://jupyter.leumaire.fr` ou `https://django.leumaire.fr/jupyter/`
