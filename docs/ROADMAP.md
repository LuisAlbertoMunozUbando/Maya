# Roadmap

- M0 Fundaciones: GitHub, API, frontend, esquema, aislamiento del panel. **Implementado como MVP.**
- M1 Captura Express: MediaRecorder, audio, contexto, transcripción/traducción humana. **MVP implementado.**
- M2 YouTube Annotator: URL, ventana inicio/fin, extracción de audio, anotación. **MVP implementado.**
- M3 Corpus Core: Observation/Segment/Inference, SQLite y JSONL. **MVP implementado; falta PostgreSQL/versionado completo.**
- M4 Procesamiento acústico: waveform, espectrograma, VAD, diarización, embeddings.
- M5 Model Playground: ASR, phone/IPA, LID, MT, ST y comparación de hipótesis.
- M6 Agentes: NemoClaw/Nemotron + OpenShell con provenance y herramientas permitidas.
- M7 Corpus Explorer avanzado: filtros, búsqueda, validación y revisión.
- M8 Dataset Builder: snapshots reproducibles, manifests, checksums, CSV/JSONL.
- M9 Piloto: hablantes, lingüistas, estudiantes e investigadores.

## Próximo hito

Desplegar M0-M3 en Spark/Vercel, validar Captura Express desde teléfono y un segmento real de YouTube; después incorporar sincronización Drive y M4 sin perturbar servicios existentes.
