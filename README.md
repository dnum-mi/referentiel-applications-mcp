# referentiel-applications-mcp

Serveur MCP FastMCP pour exposer automatiquement les endpoints de Referentiel Applications (RefApp) en outils MCP a partir d'un Swagger/OpenAPI distant.

Ce repo permet de:

- transformer l'API RefApp en outils MCP (sans coder les outils un par un)
- propager automatiquement un token Bearer entrant vers l'API RefApp
- brancher ces outils dans Open Web UI
- brancher ces outils dans VS Code / GitHub Copilot via [.vscode/mcp.json](.vscode/mcp.json)

## Ce qu'il est possible de faire

Avec ce repo, vous pouvez:

1. Demarrer un serveur MCP HTTP sur http://localhost:9000/mcp
2. Laisser FastMCP generer les tools depuis le Swagger RefApp
3. Interroger ces tools depuis:
   - Open Web UI (chat web)
   - VS Code / GitHub Copilot (MCP HTTP)
4. Utiliser un LLM externe dans Open Web UI avec un token API (API compatible OpenAI)
5. Utiliser OIDC (Keycloak) dans Open Web UI

## Architecture

- [server.py](server.py)
  - charge le Swagger via SWAGGER_URL
  - construit le serveur MCP via FastMCP.from_openapi(...)
  - injecte automatiquement Authorization: Bearer <token> sur les appels sortants vers RefApp
- [compose.yml](compose.yml)
  - service refapp-mcp
  - service open-web-ui
- [.vscode/mcp.json](.vscode/mcp.json)
  - configuration MCP HTTP pour VS Code / Copilot

## Prerequis

- Docker + Docker Compose
- RefApp backend accessible depuis Docker (exemple: host.docker.internal:3500)
- Keycloak accessible si vous activez OIDC
- Un token API LLM si vous voulez le chat modele dans Open Web UI

## Demarrage rapide

Depuis ce dossier:

```bash
docker compose up --build
```

Services exposes:

- MCP: http://localhost:9000/mcp
- Open Web UI: http://localhost:8180

## Configuration Open Web UI + token LLM

Le service Open Web UI de [compose.yml](compose.yml) est deja configure pour une API compatible OpenAI:

- OPENAI_API_BASE_URL=${LLM_API_BASE_URL:-https://api.openai.com/v1}
- OPENAI_API_KEY=${LLM_API_KEY:-}
- DEFAULT_MODELS=${LLM_MODEL:-}

Creez un fichier .env (non versionne) dans ce dossier:

```env
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=votre_token_llm
LLM_MODEL=votre_modele
```

Puis relancez:

```bash
docker compose up -d --build
```

Vous pouvez utiliser n'importe quel endpoint compatible OpenAI en ajustant LLM_API_BASE_URL, LLM_API_KEY et LLM_MODEL.

## Utilisation OIDC (Keycloak) dans Open Web UI

Les variables OIDC sont deja presentes dans [compose.yml](compose.yml):

- OPENID_PROVIDER_URL
- OPENID_REDIRECT_URI
- OAUTH_CLIENT_ID
- OAUTH_CLIENT_SECRET
- OAUTH_SCOPES

Points importants:

1. Le client OIDC doit exister dans Keycloak avec redirect URI autorisee.
2. OAUTH_CLIENT_SECRET doit etre remplace par la vraie valeur.
3. Open Web UI devra recevoir un token valide pour les actions protegees.

## Utilisation du MCP avec VS Code / GitHub Copilot

Le fichier [.vscode/mcp.json](.vscode/mcp.json) configure un serveur MCP HTTP:

- url: http://localhost:9000/mcp
- header Authorization: Bearer ${input:refapp-access-token}

Cela permet d'utiliser le serveur deja demarre sans lancer un nouveau process MCP en stdio.

## Variables d'environnement MCP

Variables du service refapp-mcp:

- SWAGGER_URL: URL absolue du Swagger/OpenAPI RefApp (JSON ou YAML)

Le serveur MCP ecoute toujours sur `0.0.0.0:9000`.

Exemple actuel:

```yaml
SWAGGER_URL: http://host.docker.internal:3500/api/v2/swagger/json
```

## Lancement sans Open Web UI

Vous pouvez lancer seulement le serveur MCP:

```bash
docker compose up --build refapp-mcp
```

Ou en local Python:

```bash
pip install -r requirements.txt
python server.py
```

## Authentification et propagation du token

Le client HTTP interne du MCP:

1. tente de lire le token via get_access_token()
2. sinon lit l'en-tete Authorization entrant
3. reinjecte ce Bearer vers l'API RefApp

Cela permet d'appeler des endpoints RefApp proteges tant que le token entrant est valide et non expire.

## Troubleshooting

- 401 Unauthorized sur les tools RefApp
  - verifier que le token est un access token (pas un ID token)
  - verifier la date d'expiration (claim exp)
  - verifier les droits/roles de l'utilisateur
- Open Web UI ne repond pas avec le modele
  - verifier LLM_API_KEY
  - verifier OPENAI_API_BASE_URL et DEFAULT_MODELS
- MCP ne charge pas les tools
  - verifier SWAGGER_URL
  - verifier l'accessibilite reseau vers RefApp depuis le conteneur

## Fichiers principaux

- [server.py](server.py): serveur FastMCP + propagation Bearer
- [compose.yml](compose.yml): stack Docker MCP + Open Web UI
- [Dockerfile](Dockerfile): image du serveur MCP
- [requirements.txt](requirements.txt): dependances Python
- [.vscode/mcp.json](.vscode/mcp.json): config MCP VS Code/Copilot
