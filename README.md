# referentiel-applications-mcp

Serveur MCP FastMCP qui expose l'API RefApp en outils MCP a partir de son Swagger.

## Prerequis

- Docker + Docker Compose
- RefApp backend accessible depuis Docker (ex: `host.docker.internal:3500`)
- Un token RefApp (**Profil > Mes tokens** dans RefApp)
- Optionnel: un token API LLM compatible OpenAI

## Demarrage rapide

Creez un fichier `.env` (non versionne) :

```env
REFAPP_TOKEN=votre_token_refapp
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=votre_cle_llm
```

Puis :

```bash
docker compose up --build
```

Services exposes :

- MCP : http://localhost:9000/mcp
- Open Web UI : http://localhost:8180 (serveur MCP RefApp pre-configure, acces direct sans login)

La stack utilise un seul container `ghcr.io/open-webui/open-webui:ollama`, qui embarque aussi Ollama.

Pour telecharger `llama3.2:3b`, vous pouvez ensuite :

- soit utiliser l'UI Open WebUI si vous activez le pull de modele depuis l'interface
- soit executer `docker compose exec open-web-ui ollama pull llama3.2:3b`

Une fois le modele telecharge, il apparait directement dans Open WebUI.

## Utilisation avec VS Code / GitHub Copilot

Le fichier [.vscode/mcp.json](.vscode/mcp.json) configure le serveur MCP HTTP sur http://localhost:9000/mcp.
VS Code demandera le token RefApp au premier usage (champ masque, stocke en session).

## Fonctionnement

Le serveur MCP lit le header `x-refapp-token` des requetes entrantes et le propage vers l'API RefApp. La validation du token est faite par RefApp.

## Variables d'environnement

| Variable           | Description                          |
| ------------------ | ------------------------------------ |
| `SWAGGER_URL`      | URL du Swagger RefApp (JSON ou YAML) |
| `REFAPP_TOKEN`     | Token RefApp pour Open Web UI        |
| `LLM_API_BASE_URL` | Base URL endpoint compatible OpenAI  |
| `LLM_API_KEY`      | Cle API LLM                          |

Si vous n'utilisez qu'Ollama en local, `LLM_API_BASE_URL` et `LLM_API_KEY` peuvent rester absents.
