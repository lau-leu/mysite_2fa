# Configuration JupyterLab IDE via Django avec 2FA

Ce guide explique comment accéder au **vrai JupyterLab IDE** via Django avec authentification 2FA obligatoire.

## 🎯 Objectif

- URL d'accès : **`https://django.leumaire.fr/jupyterlab/`**
- Protection : Authentification Django + 2FA (TOTP)
- Backend : JupyterLab IDE sur vm-ia:8888

## ✅ Modifications effectuées

### 1. Proxy Django modifié

**Fichier :** `appliweb/authentication/jupyterlab_proxy.py`
- Changé le port de 5001 (Chat Assistant) → 8888 (vrai JupyterLab IDE)
- Mis à jour l'URL de proxy : `http://192.168.1.96:8888/jupyterlab/`

### 2. Service JupyterLab modifié

**Fichier :** `jupyterlab.service`
- Ajouté `--ServerApp.base_url=/jupyterlab/` pour que JupyterLab serve ses ressources sous le bon préfixe

## 📋 Déploiement

### Sur vm-ia (192.168.1.96)

#### 1. Mettre à jour le service JupyterLab

```bash
# Sur vm-ia
cd /home/laurent

# Copier le nouveau fichier service depuis le repo
sudo cp jupyterlab.service /etc/systemd/system/

# Recharger systemd
sudo systemctl daemon-reload

# Redémarrer JupyterLab
sudo systemctl restart jupyterlab

# Vérifier que ça fonctionne
sudo systemctl status jupyterlab

# Vérifier que JupyterLab écoute bien
curl http://localhost:8888/jupyterlab/
```

**Vérification importante :** Le service doit maintenant servir JupyterLab à `/jupyterlab/` au lieu de `/lab/`.

### Sur django-app (192.168.1.58)

#### 2. Mettre à jour le proxy Django

```bash
# Sur django-app
cd ~/appliweb  # ou le chemin de votre application

# Récupérer les dernières modifications
git pull origin main  # ou votre branche

# Redémarrer Django
sudo systemctl restart django-app  # ou votre service Django

# Vérifier
sudo systemctl status django-app
```

## 🧪 Tests

### 1. Tester depuis votre navigateur

1. Allez sur **`https://django.leumaire.fr/jupyterlab/`**
2. Authentifiez-vous (login + 2FA si pas déjà fait)
3. Vous devriez voir l'interface JupyterLab

### 2. Vérifier que les ressources se chargent

Ouvrez la console développeur (F12) et vérifiez :
- Pas d'erreurs MIME type
- Les fichiers JS/CSS se chargent depuis `/jupyterlab/static/...`
- Pas d'erreurs 404

### 3. Tester la création d'un notebook

- Créez un nouveau notebook Python 3
- Essayez d'exécuter une cellule simple : `print("Hello")`

## ⚠️ Limitations connues

### WebSockets non supportés

Ce proxy Django basique utilise la bibliothèque `requests` qui **ne supporte pas les WebSockets**.

**Impact :**
- ✅ L'interface JupyterLab se charge
- ✅ Vous pouvez naviguer dans les fichiers
- ✅ Vous pouvez créer des notebooks
- ❌ **L'exécution de code peut ne pas fonctionner** (les kernels utilisent WebSockets)
- ❌ Les terminaux intégrés peuvent ne pas fonctionner

### Solutions pour WebSockets

Si l'exécution de code ne fonctionne pas, vous avez 3 options :

#### Option 1 : Django Channels (recommandé mais complexe)

Implémenter un proxy WebSocket avec Django Channels.

**Avantages :**
- Support complet WebSockets
- Garde l'authentification 2FA
- Tout via Django

**Inconvénients :**
- Nécessite l'installation de Django Channels
- Configuration plus complexe
- Nécessite Redis ou autre message broker

#### Option 2 : Apache/Nginx en front avec auth Django (hybrid)

Configurer Apache/Nginx pour :
1. Vérifier la session Django (via module auth)
2. Proxier vers JupyterLab avec support WebSocket

**Avantages :**
- Support complet WebSockets
- Garde l'authentification 2FA
- Performant

**Inconvénients :**
- Configuration complexe Apache/Nginx + Django
- Nécessite module d'authentification custom

#### Option 3 : JupyterLab séparé avec son propre auth

Utiliser `https://jupyter.leumaire.fr` avec Apache et HTTP Basic Auth (comme prévu initialement).

**Avantages :**
- Fonctionne complètement
- Configuration simple
- Support WebSocket natif

**Inconvénients :**
- Pas d'intégration avec l'auth Django 2FA
- Nécessite un mot de passe séparé (HTTP Basic)

## 🔍 Troubleshooting

### Erreur "MIME type incorrect"

**Cause :** JupyterLab ne sert pas à `/jupyterlab/`

**Solution :**
```bash
# Sur vm-ia, vérifier la configuration
sudo systemctl cat jupyterlab | grep ExecStart

# Doit contenir --ServerApp.base_url=/jupyterlab/
# Si absent, mettre à jour le service et redémarrer
```

### Erreur 404 sur les ressources

**Cause :** JupyterLab n'a pas redémarré avec le nouveau base_url

**Solution :**
```bash
# Sur vm-ia
sudo systemctl restart jupyterlab
sudo systemctl status jupyterlab
```

### Erreur 503 "Service Unavailable"

**Cause :** JupyterLab n'est pas démarré ou inaccessible

**Solution :**
```bash
# Sur vm-ia
sudo systemctl status jupyterlab
sudo journalctl -u jupyterlab -f

# Tester localement
curl http://localhost:8888/jupyterlab/
```

### L'interface se charge mais l'exécution de code ne fonctionne pas

**Cause :** WebSockets non supportés par le proxy Django

**Solution :** Choisir une des options ci-dessus (Django Channels, Apache hybrid, ou JupyterLab séparé)

## 📚 Prochaines étapes

1. **Tester l'accès via Django** : Vérifier que l'interface se charge
2. **Tester l'exécution de code** : Voir si les WebSockets passent
3. **Si WebSockets ne fonctionnent pas** : Décider quelle solution implémenter (Channels, Apache, ou séparé)

## 🔗 Liens utiles

- [Documentation JupyterLab sur les reverse proxy](https://jupyterlab.readthedocs.io/en/stable/user/urls.html)
- [Django Channels](https://channels.readthedocs.io/)
- [Configuration Apache avec WebSocket](https://httpd.apache.org/docs/2.4/mod/mod_proxy_wstunnel.html)

## 📝 Notes

- Le Chat Assistant JupyterLab (Flask sur port 5001) est toujours disponible mais non utilisé
- Vous pouvez le désactiver si vous n'en avez plus besoin : `sudo systemctl disable jupyterlab-chat-ia`
