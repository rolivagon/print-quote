# Exponer a Internet con Cloudflare Tunnel

Esta guía te permite exponer tu aplicación Print Quote a internet usando Cloudflare Tunnel de forma gratuita y segura.

## ¿Cómo funciona?

1. El frontend se compila a archivos estáticos
2. FastAPI sirve el frontend en la ruta raíz (`/`)
3. La API está disponible en `/api/*`
4. Cloudflare Tunnel crea una URL pública que apunta a tu servidor local

```
Usuario → https://abc123.trycloudflare.com
                ↓
        Cloudflare Tunnel
                ↓
        Tu computadora (localhost:8000)
                ↓
        FastAPI: / → frontend estático
        FastAPI: /api/* → API endpoints
```

## 🚀 Uso Rápido (Un comando)

```bash
./scripts/start-tunnel.sh
```

Esto hará:
1. Build del frontend
2. Iniciar servidor backend en puerto 8000
3. Crear túnel de Cloudflare

**Tu URL aparecerá en la terminal después de unos segundos.**

## 📋 Comandos Individuales

Si prefieres controlar cada paso:

### 1. Build del frontend
```bash
make build-frontend
```

### 2. Iniciar servidor
```bash
make serve
# o con puerto personalizado:
make serve PORT=9000
```

### 3. Iniciar tunnel (en otra terminal)
```bash
make tunnel
# o con puerto personalizado:
make tunnel PORT=9000
```

## 🔧 Solución de Problemas

### Error: "cloudflared: command not found"
Instala cloudflared:
```bash
# macOS con Homebrew
brew install cloudflared

# Linux
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Error: "Puerto 8000 en uso"
```bash
# Cambia el puerto
make serve PORT=9000
make tunnel PORT=9000
```

### El frontend no se ve pero la API sí
Verifica que el build existe:
```bash
ls -la frontend/dist/
```
Si está vacío, ejecuta:
```bash
make build-frontend
```

### La API no responde
Las rutas API ahora tienen prefijo `/api`. Por ejemplo:
- Antes: `POST /auth/login`
- Ahora: `POST /api/auth/login`

El frontend ya está configurado para usar rutas relativas automáticamente.

## 📝 Notas Importantes

1. **URL temporal**: Las URLs de `trycloudflare.com` cambian cada vez que inicias el túnel
2. **No necesitas cambiar tu desarrollo local**: Cuando desarrollas localmente, sigues usando `make dev` (puerto 5001 para backend, 5173 para frontend con hot-reload)
3. **El túnel es solo para demos**: No uses esto para producción real

## 🛑 Detener el túnel

Presiona `Ctrl+C` en la terminal donde corre el script, o:
```bash
make tunnel-stop
```