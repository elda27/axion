# Deveopnment for Agent
This document provides instructions for setting up a development environment for the Agent component of the Axion project. The Agent is responsible for executing tasks and communicating with the Axion server.

## Running for development
You can start the development environment using Docker Compose. The `compose.dev.yaml` file includes additional services and configurations for development purposes.
Maybe different user has up containers, so we may need to check the status of containers before running the command.
```bash
docker compose -f compose.yaml -f compose.dev.yaml up -d
```

| App          | Port |
| ------------ | ---- |
| Axion Server | 8000 |
| Axion UI     | 5173 |

## Debugging UI
### Overview
You can use playwright CLI to run the UI in development mode. It will automatically reload the UI when you make changes to the code.
```bash
npx playwright test --headed --project=chromium
```

This is very useful for debugging the UI or server logic because you can see the changes in real-time and interact with the UI to test the functionality.

### Develop ui logic
A recommendation to develop UI logic is to use the sperate codes with React codes because the logic code should separate with the UI code.
You can create a folder named `logic` in the `axion_ui` folder and write the logic code in it. Then you can import the logic code in the React components and use it.
But `logic/` should includes only logic code and it refers DDD (Domain-Driven Design) and each folder has single feature or domain.

### Develop API clients
You should facade API clients to interact with the Axion server.
It is recommended to use openapi-generator to generate API services code and use it in the client code.
You can find the OpenAPI specification for the Axion server in the `openapi.json` in axion server like `http://localhost:8000/openapi.json`.

