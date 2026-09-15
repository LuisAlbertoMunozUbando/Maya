# Maya Multimodal Corpus & Speech Research Platform

Plataforma colaborativa para capturar, segmentar, anotar y preservar habla maya y su contexto multimodal.

## Arquitectura

- Frontend: Next.js + TypeScript, pensado para Vercel en `maya.albertomunoz.ai`.
- API: FastAPI separada, pensada para DGX Spark en `127.0.0.1:8030` y publicada mediante un Cloudflare Tunnel dedicado como `maya-api.albertomunoz.ai`.
- Persistencia operacional: SQLite en MVP, migrable a PostgreSQL.
- Archivo científico: Google Drive, carpeta Maya existente.
- Procesamiento: ffmpeg/ffprobe/yt-dlp y, por capas, ASR, fonética, LID, traducción y modelos futuros.
- Agentes: interfaces preparadas para NemoClaw/Nemotron como orquestador y OpenShell como ejecución controlada.

## Principio científico

Nunca se sobrescribe la evidencia original. Cada segmento conserva representaciones, inferencias automáticas, anotaciones humanas y validaciones con provenance.

## MVP

1. Captura Express desde celular: audio + descripción contextual + transcripción/traducción opcionales.
2. YouTube Annotator: URL + ventana temporal + extracción de audio + anotaciones.
3. Corpus Explorer: lista y consulta de observaciones y segmentos.
4. Export JSONL reproducible.
5. Sincronización opcional a Google Drive.

## Desarrollo local

Backend:

```bash
cd services/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8030
```

Frontend:

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

## Despliegue Spark

La API es deliberadamente independiente del Spark Control Panel. No usa el puerto 8099 ni modifica `panel.albertomunoz.ai`.

```bash
docker compose up -d --build api
curl http://127.0.0.1:8030/healthz
```

Después se crea un Cloudflare Tunnel/ingress independiente para `maya-api.albertomunoz.ai -> http://127.0.0.1:8030`.

## Google Drive

La carpeta existente `Maya` es el archivo científico. Configure `MAYA_DRIVE_FOLDER_ID` y credenciales de Google únicamente en el Spark; nunca se versionan secretos.
