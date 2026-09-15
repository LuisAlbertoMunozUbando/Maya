# Arquitectura

## Separación operacional

Maya es una aplicación independiente. Su API escucha en `127.0.0.1:8030` en el host Spark y se publica exclusivamente mediante `maya-api.albertomunoz.ai`. No comparte proceso, puerto, configuración ni túnel con `panel.albertomunoz.ai`.

## Objetos científicos

- Observation: evento/fuente original.
- Segment: ventana temporal analizable.
- Representation: audio, espectrograma, IPA, embeddings, etc.
- Inference: salida versionada de un modelo.
- Annotation: aportación humana.
- Validation: revisión humana/experta.

Nunca se reemplaza la evidencia original.

## Agentic vision

La futura capa `services/agents` podrá usar NemoClaw/Nemotron para decidir qué transformaciones conviene ejecutar. OpenShell será la frontera de ejecución controlada de herramientas. Toda acción del agente debe generar provenance y ninguna inferencia automática adquiere estatus de ground truth sin validación.

## Fallback conceptual

`audio -> VAD -> LID -> ASR`; si ASR es pobre/vacío, `phone recognition`; si existe video, análisis de keyframes/contexto; después revisión humana.

## Drive

Google Drive es archivo científico y destino de snapshots/exportaciones, no base transaccional. La base operacional conserva índices y relaciones. La carpeta existente `Maya` es el destino previsto.
