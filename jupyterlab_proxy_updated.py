"""
Vue proxy pour rediriger vers JupyterLab IDE sur vm-ia
"""
import requests
from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django_otp.decorators import otp_required
from django.conf import settings


@login_required
@otp_required
@csrf_exempt
def jupyterlab_proxy(request, path=''):
    """
    Proxy transparent vers JupyterLab IDE sur vm-ia
    Accessible uniquement pour les utilisateurs authentifiés avec 2FA

    IMPORTANT: JupyterLab doit être configuré avec --ServerApp.base_url=/jupyterlab/
    pour que les chemins relatifs fonctionnent correctement.

    LIMITATION: Les WebSockets ne sont pas supportés par ce proxy basique.
    Pour une fonctionnalité complète (exécution de kernels), utilisez Django Channels
    ou un reverse proxy Apache/Nginx dédié.
    """
    # URL du vrai JupyterLab IDE sur vm-ia (port 8888)
    jupyterlab_url = f"http://192.168.1.96:8888/jupyterlab/{path}"

    # Copier les headers de la requête (sauf Host)
    headers = {}
    for key, value in request.META.items():
        if key.startswith('HTTP_'):
            header_name = key[5:].replace('_', '-').title()
            if header_name not in ['Host', 'Cookie']:
                headers[header_name] = value

    # Ajouter le Content-Type (important pour les requêtes POST JSON)
    if 'CONTENT_TYPE' in request.META:
        headers['Content-Type'] = request.META['CONTENT_TYPE']

    # Ajouter les headers pour le proxy
    headers['X-Forwarded-For'] = request.META.get('REMOTE_ADDR', '')
    headers['X-Forwarded-Proto'] = 'https' if request.is_secure() else 'http'
    headers['X-Forwarded-Host'] = request.get_host()

    # Copier les cookies si nécessaire
    cookies = request.COOKIES

    try:
        # Faire la requête vers vm-ia
        if request.method == 'GET':
            response = requests.get(
                jupyterlab_url,
                params=request.GET,
                headers=headers,
                cookies=cookies,
                stream=True,
                timeout=30
            )
        elif request.method == 'POST':
            response = requests.post(
                jupyterlab_url,
                data=request.body,
                headers=headers,
                cookies=cookies,
                timeout=180  # 3 minutes pour les opérations JupyterLab
            )
        elif request.method == 'DELETE':
            response = requests.delete(
                jupyterlab_url,
                headers=headers,
                cookies=cookies,
                timeout=30
            )
        else:
            return HttpResponse('Method not allowed', status=405)

        # Retourner la réponse
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = {
            key: value for key, value in response.headers.items()
            if key.lower() not in excluded_headers
        }

        proxy_response = HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('content-type', 'text/html')
        )

        for key, value in response_headers.items():
            proxy_response[key] = value

        return proxy_response

    except requests.exceptions.RequestException as e:
        return HttpResponse(
            f'Erreur de connexion à JupyterLab: {str(e)}',
            status=503
        )
