# Récapitulatif de l'intégration des applications Flask

## ✅ Travail accompli

### 1. Architecture mise en place

```
Internet (OVH)
    ↓
192.168.1.202 (Apache - romane.leumaire.fr / serverweb)
    ├─→ https://django.leumaire.fr → Django (192.168.1.58:8000)
    │      ├─→ /chat/ → vm-ia:5000 (Chat IA)
    │      ├─→ /ao/ → vm-ia:5002 (Gestion AO)
    │      └─→ /jupyterlab/ → vm-ia:5001 (JupyterLab Chat Assistant)
    │
    └─→ https://jupyter.leumaire.fr → JupyterLab IDE (vm-ia:8888)
```

### 2. Modifications effectuées dans appliweb (Django)

**✅ Fichiers créés/modifiés :**
- `appliweb/authentication/jupyterlab_proxy.py` - Proxy vers vm-ia:5001
- `appliweb/authentication/ao_proxy.py` - Proxy vers vm-ia:5002
- `appliweb/authentication/urls.py` - Routes pour /jupyterlab/ et /ao/
- `appliweb/templates/base.html` - Boutons menu pour "Gestion AO" et "JupyterLab"

**Protection :** Toutes les vues proxy sont protégées par :
- `@login_required` - Authentification Django
- `@otp_required` - Authentification 2FA (TOTP)

### 3. Modifications dans vm-ia-AO-flask

**✅ Fichiers créés/modifiés :**
- `app/flask_app.py` - Ajout de `PrefixMiddleware` et `ProxyFix` pour gérer le proxy
- `app/templates/base.html` - Bouton "Retour à Appliweb" (ligne 69)
- `deploy.sh` - Script de déploiement avec gunicorn sur port 5002

**Middleware critique :** Le `PrefixMiddleware` permet à Flask de :
- Lire le header `X-Forwarded-Prefix` envoyé par Django
- Ajuster les URLs générées pour inclure le préfixe `/ao/`
- Éviter les erreurs 404 sur les liens internes

### 4. Modifications dans vm-ia-jupyterlab (Chat Assistant)

**✅ Fichiers créés/modifiés :**
- `app.py` - Ajout de `PrefixMiddleware` et `ProxyFix` pour gérer le proxy
- `templates/base.html` - Bouton "Retour à Appliweb" (ligne 18)
- `deploy.sh` - Script de déploiement avec gunicorn sur port 5001

### 5. Configuration JupyterLab IDE (vrai JupyterLab)

**✅ Fichiers créés :**
- `jupyterlab.service` - Service systemd pour JupyterLab sur port 8888
- `apache-jupyterlab.conf` - Config Apache avec support WebSockets
- `setup-jupyterlab-apache.sh` - Script d'installation automatique
- `JUPYTERLAB-APACHE-SETUP.md` - Documentation complète

**Service JupyterLab :** Déjà démarré et fonctionnel sur vm-ia:8888

## 📋 Actions à réaliser

### Sur vm-ia (192.168.1.96)

#### 1. Pusher les modifications des submodules

Les submodules ont été modifiés localement mais ne peuvent pas être pushés depuis cet environnement. Vous devez pusher manuellement :

```bash
# Sur votre machine locale
cd ~/chemin/vers/mysite_2fa

# Pusher vm-ia-jupyterlab
cd vm-ia-jupyterlab
git push origin main
cd ..

# Note: vm-ia-AO-flask et vm-ia-chat ont peut-être déjà été pushés précédemment
```

#### 2. Déployer/redémarrer les services Flask

Si ce n'est pas déjà fait, déployez les applications Flask avec gunicorn :

```bash
# Sur vm-ia (192.168.1.96)

# Chat IA (si pas déjà actif)
cd ~/vm-ia-chat
./deploy.sh  # Suivre les instructions pour créer le service

# Gestion AO
cd ~/vm-ia-AO-flask
./deploy.sh  # Suivre les instructions pour créer le service

# JupyterLab Chat Assistant
cd ~/vm-ia-jupyterlab
./deploy.sh  # Suivre les instructions pour créer le service
```

**Vérifier que les services tournent :**
```bash
# Sur vm-ia
sudo systemctl status chat-ia
sudo systemctl status gestion-ao
sudo systemctl status jupyterlab-chat-ia

# Vérifier les ports
netstat -tlnp | grep -E '5000|5001|5002|8888'
```

### Sur serverweb (192.168.1.202)

#### 3. Configurer Apache pour JupyterLab IDE

Deux options :

**Option A : Script automatique (recommandé)**
```bash
# Sur serverweb
# 1. Copier les fichiers depuis le repo mysite_2fa
scp user@autre-machine:~/mysite_2fa/apache-jupyterlab.conf .
scp user@autre-machine:~/mysite_2fa/setup-jupyterlab-apache.sh .

# 2. Exécuter le script
sudo ./setup-jupyterlab-apache.sh
```

**Option B : Commandes manuelles**
```bash
# Sur serverweb
# 1. Activer les modules Apache
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite headers

# 2. Copier le fichier de configuration
sudo cp apache-jupyterlab.conf /etc/apache2/sites-available/jupyter.leumaire.fr.conf

# 3. Créer l'authentification HTTP Basic
sudo htpasswd -c /etc/apache2/.htpasswd laurent

# 4. Tester la configuration
sudo apache2ctl configtest

# 5. Activer le site
sudo a2ensite jupyter.leumaire.fr

# 6. Recharger Apache
sudo systemctl reload apache2
```

#### 4. Tester l'accès HTTP

Une fois Apache configuré :
```bash
# Sur serverweb, surveiller les logs
sudo tail -f /var/log/apache2/jupyter_error.log
```

Puis testez dans votre navigateur : `http://jupyter.leumaire.fr`

#### 5. Configurer HTTPS avec certbot

Une fois que HTTP fonctionne :
```bash
# Sur serverweb
sudo certbot --apache -d jupyter.leumaire.fr
```

### Sur django-app (192.168.1.58)

#### 6. Mettre à jour le code Django

Si les modifications ne sont pas encore sur le serveur :
```bash
# Sur django-app
cd ~/appliweb  # ou le chemin de votre appliweb
git pull origin main  # ou la branche appropriée

# Redémarrer Django (si nécessaire)
sudo systemctl restart django-app  # ou votre service Django
```

## 🧪 Tests à effectuer

### 1. Tester les proxies Django

Depuis votre navigateur :
- ✅ https://django.leumaire.fr/chat/ → Chat IA
- ✅ https://django.leumaire.fr/ao/ → Gestion AO
- ✅ https://django.leumaire.fr/jupyterlab/ → JupyterLab Chat Assistant

**Vérifier :**
- Les boutons dans le menu fonctionnent
- Les boutons "Retour à Appliweb" fonctionnent
- Les liens internes dans chaque application fonctionnent (pas de 404)
- L'authentification 2FA est requise

### 2. Tester JupyterLab IDE

- ✅ http://jupyter.leumaire.fr (puis HTTPS après certbot)

**Vérifier :**
- L'interface JupyterLab se charge
- Les WebSockets fonctionnent (nécessaires pour les kernels)
- Vous pouvez créer et exécuter un notebook
- L'authentification HTTP Basic fonctionne

## 📝 Fichiers de configuration importants

### Services systemd créés

1. **chat-ia.service** - Chat IA sur port 5000
2. **gestion-ao.service** - Gestion AO sur port 5002
3. **jupyterlab-chat-ia.service** - Chat Assistant sur port 5001
4. **jupyterlab.service** - JupyterLab IDE sur port 8888

### Configuration Apache

- `/etc/apache2/sites-available/jupyter.leumaire.fr.conf` - Config JupyterLab
- `/etc/apache2/.htpasswd` - Authentification HTTP Basic

## 🔒 Sécurité

Toutes les applications sont protégées :
- **Django proxy** : Authentification 2FA obligatoire
- **JupyterLab IDE** : HTTP Basic Auth + firewall UFW (seul serverweb peut accéder)

## 📚 Documentation

- `JUPYTERLAB-APACHE-SETUP.md` - Guide complet pour JupyterLab
- `setup-jupyterlab-apache.sh` - Script d'installation Apache
- `deploy.sh` (dans chaque app Flask) - Scripts de déploiement

## 🐛 Troubleshooting

### Problème : 404 sur les liens internes dans les apps Flask
**Solution :** Le middleware `PrefixMiddleware` a été ajouté pour résoudre ce problème.

### Problème : 503 Service Unavailable pour JupyterLab
**Solutions possibles :**
1. Vérifier que JupyterLab tourne : `systemctl status jupyterlab`
2. Vérifier que le site Apache est activé : `ls -la /etc/apache2/sites-enabled/ | grep jupyter`
3. Vérifier les modules Apache : `apache2ctl -M | grep proxy`
4. Consulter les logs : `tail -f /var/log/apache2/jupyter_error.log`

### Problème : WebSockets ne fonctionnent pas
**Solution :** Vérifier que `mod_proxy_wstunnel` est activé : `sudo a2enmod proxy_wstunnel`

## ✨ Prochaines étapes (optionnel)

1. **Monitoring** : Ajouter Prometheus/Grafana pour surveiller les services
2. **Backup** : Configurer des sauvegardes automatiques des données
3. **CI/CD** : Automatiser les déploiements avec GitHub Actions
4. **Load Balancing** : Si nécessaire, ajouter plusieurs instances de vm-ia

## 📞 Support

En cas de problème, vérifiez :
1. Les logs systemd : `journalctl -u nom-du-service -f`
2. Les logs Apache : `tail -f /var/log/apache2/error.log`
3. Les logs Django : selon votre configuration
4. L'état du réseau : `ping`, `telnet`, `curl`
