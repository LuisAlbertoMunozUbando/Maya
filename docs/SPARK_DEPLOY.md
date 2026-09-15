# Despliegue en DGX Spark

Este procedimiento no toca Spark Control Panel ni sus servicios.

```bash
cd ~
git clone https://github.com/LuisAlbertoMunozUbando/Maya.git maya-speech-lab
cd maya-speech-lab
cp services/api/.env.example services/api/.env
docker compose up -d --build api
curl -sS http://127.0.0.1:8030/healthz
```

Si el repositorio ya existe localmente:

```bash
cd ~/maya-speech-lab
git pull
docker compose up -d --build api
curl -sS http://127.0.0.1:8030/healthz
```

## Cloudflare

Crear un tunnel/ingress dedicado:

`maya-api.albertomunoz.ai -> http://127.0.0.1:8030`

No reutilizar ni modificar el hostname `panel.albertomunoz.ai`.

## Frontend

En Vercel usar `apps/web` como Root Directory y definir:

`NEXT_PUBLIC_API_BASE_URL=https://maya-api.albertomunoz.ai`

Después asociar `maya.albertomunoz.ai` al proyecto.

## Verificación

```bash
curl -sS http://127.0.0.1:8030/healthz
curl -sS https://maya-api.albertomunoz.ai/healthz
```

Sólo después de ambos 200 debe considerarse la API pública operativa.
