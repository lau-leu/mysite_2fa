# Intégration de vm-ia-AO-flask

Ce document décrit les modifications nécessaires pour intégrer l'application vm-ia-AO-flask avec appliweb.

## ⚠️ Note importante

Le dépôt `vm-ia-AO-flask` n'était pas accessible lors de la configuration. Les instructions ci-dessous décrivent ce qui doit être fait pour compléter l'intégration.

## Modifications déjà effectuées dans appliweb

✅ **Vue proxy créée** : `appliweb/authentication/ao_proxy.py`
- Redirige vers `http://192.168.1.96:5002/`
- Accessible aux utilisateurs authentifiés uniquement

✅ **Route configurée** : `appliweb/authentication/urls.py`
- URL: `/ao/<path>`
- Nom: `ao_proxy`

✅ **Bouton ajouté** : `appliweb/templates/base.html`
- Menu: "📋 Gestion AO"
- Lien: `{% url 'ao_proxy' path='' %}`

## Modifications à effectuer dans vm-ia-AO-flask

### 1. Configuration du port (config.py)

Assurez-vous que l'application Flask est configurée pour écouter sur le port **5002** :

```python
class Config:
    # Serveur Flask
    HOST = '0.0.0.0'
    PORT = 5002  # Port pour Gestion AO
    DEBUG = False
```

### 2. Script de déploiement avec Gunicorn (deploy.sh)

Créez ou modifiez le fichier `deploy.sh` pour inclure la configuration Gunicorn :

```bash
#!/bin/bash

set -e

echo "========================================================"
echo "Déploiement Gestion AO sur vm-ia"
echo "========================================================"
echo ""

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "app.py" ]; then
    echo "❌ Erreur: app.py non trouvé."
    exit 1
fi

# Créer l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer et installer les dépendances
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Déploiement terminé!"
echo ""
echo "Pour démarrer avec Gunicorn (recommandé):"
echo "  source venv/bin/activate"
echo "  gunicorn -w 4 -b 0.0.0.0:5002 --timeout 180 app:app"
echo ""
echo "L'application sera accessible sur:"
echo "  http://192.168.1.96:5002"
echo "  https://django.leumaire.fr/ao/ (via proxy)"
```

### 3. Service systemd (optionnel)

Pour un démarrage automatique, créez `/etc/systemd/system/ao-flask.service` :

```ini
[Unit]
Description=Gestion AO Flask Application
After=network.target

[Service]
User=votre_utilisateur
WorkingDirectory=/chemin/vers/vm-ia-AO-flask
Environment="PATH=/chemin/vers/vm-ia-AO-flask/venv/bin"
ExecStart=/chemin/vers/vm-ia-AO-flask/venv/bin/gunicorn -w 4 -b 0.0.0.0:5002 --timeout 180 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Puis activez le service :

```bash
sudo systemctl daemon-reload
sudo systemctl enable ao-flask
sudo systemctl start ao-flask
```

### 4. Bouton "Retour à Appliweb"

Dans le template principal de vm-ia-AO-flask (probablement `templates/base.html`), ajoutez un bouton de retour :

```html
<header>
    <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>📋 Gestion AO</h1>
                <p class="subtitle">Application de Gestion des Appels d'Offres</p>
            </div>
            <a href="https://django.leumaire.fr/" class="btn-return-appliweb"
               style="text-decoration: none; background: linear-gradient(135deg, #4f46e5, #7c3aed);
                      color: white; padding: 10px 20px; border-radius: 8px;
                      font-weight: 600; transition: transform 0.2s;">
                ← Retour à Appliweb
            </a>
        </div>
    </div>
</header>
```

### 5. Requirements.txt

Assurez-vous que `requirements.txt` contient au minimum :

```
Flask==3.0.0
gunicorn==21.2.0
requests==2.31.0
```

## Test de l'intégration

1. **Démarrer l'application sur vm-ia** :
   ```bash
   cd /chemin/vers/vm-ia-AO-flask
   source venv/bin/activate
   gunicorn -w 4 -b 0.0.0.0:5002 --timeout 180 app:app
   ```

2. **Tester l'accès direct** :
   - Ouvrir : `http://192.168.1.96:5002`

3. **Tester via le proxy** :
   - Se connecter à appliweb : `https://django.leumaire.fr`
   - Cliquer sur "📋 Gestion AO" dans le menu
   - Vérifier que l'application s'affiche correctement
   - Tester le bouton "Retour à Appliweb"

## Configuration réseau

Assurez-vous que :
- Le port 5002 est ouvert sur le firewall de vm-ia
- La VM django-app (192.168.1.58) peut accéder à vm-ia (192.168.1.96) sur le port 5002

```bash
# Sur vm-ia, vérifier le firewall
sudo ufw allow 5002/tcp
sudo ufw status
```

## Dépannage

### L'application ne démarre pas
```bash
# Vérifier les logs
journalctl -u ao-flask -f

# Tester le port
netstat -tlnp | grep 5002
```

### Erreur 503 depuis appliweb
- Vérifier que l'application est démarrée sur vm-ia
- Vérifier la connectivité réseau : `ping 192.168.1.96`
- Tester l'accès direct : `curl http://192.168.1.96:5002`

### Le proxy ne fonctionne pas
- Vérifier les logs Django : `sudo journalctl -u gunicorn -f`
- Redémarrer gunicorn sur django-app : `sudo systemctl restart gunicorn`

## Commandes utiles

```bash
# Démarrer l'application
sudo systemctl start ao-flask

# Arrêter l'application
sudo systemctl stop ao-flask

# Redémarrer l'application
sudo systemctl restart ao-flask

# Voir les logs
sudo journalctl -u ao-flask -f

# Vérifier le statut
sudo systemctl status ao-flask
```
