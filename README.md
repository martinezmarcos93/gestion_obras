# Gestión de Obras

Sistema de gestión de presupuestos y facturas para Maestro Mayor de Obras.

## Funcionalidades

- **Clientes** — alta, baja y modificación de consorcios, particulares y empresas
- **Presupuestos** — creación, aprobación y seguimiento por cliente
- **Facturas** — registro por tipo (adelanto / saldo / parcial), adjunto de comprobante AFIP (PDF o imagen), marcado como abonada
- **Dashboard** — KPIs en tiempo real: trabajos activos, montos por cobrar, gráfico de facturación mensual
- **Cierre desde la app** — botón de salida en el sidebar sin necesidad de usar la terminal

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend + Backend | Python · Streamlit |
| Base de datos | SQLite (archivo local) |
| Gráficos | Altair |
| Distribución | PyInstaller (`--onedir`) |

## Requisitos para desarrollo

- Python 3.9 o superior
- pip

```bash
pip install streamlit pandas altair
```

## Ejecutar en modo desarrollo

```bash
streamlit run app.py
```

La app abre en `http://localhost:8501`.

## Estructura del proyecto

```
gestion_obras/
├── app.py                   # Dashboard principal
├── database.py              # Modelos y acceso a SQLite
├── utils.py                 # Componentes compartidos (botón salir)
├── main_frozen.py           # Entry point para PyInstaller
├── GestionObras.spec        # Configuración de empaquetado
├── pages/
│   ├── 1_Clientes.py
│   ├── 2_Presupuestos.py
│   └── 3_Facturas.py
├── .streamlit/
│   └── config.toml          # Tema visual
├── build_completo.bat       # Genera el ejecutable distribuible
├── iniciar.bat              # Lanzador rápido para desarrollo
└── consorcios_precargados.md
```

Los datos en producción se guardan en `datos/` junto al ejecutable:

```
datos/
├── gestion_obras.db
└── archivos/facturas/       # Comprobantes AFIP adjuntos
```

## Generar el ejecutable distribuible

```bash
build_completo.bat
```

Genera `dist/GestionObras/` con todo incluido (~230 MB). El destinatario no necesita instalar Python ni ninguna dependencia.

**Para entregar:** comprimir `dist/GestionObras/` en ZIP y enviar. El cliente hace doble clic en `GestionObras.exe`.

## Flujo de trabajo típico

```
Nuevo cliente
     ↓
Crear presupuesto  →  Aprobar presupuesto
                            ↓
                    Emitir factura adelanto (en AFIP)
                            ↓
                    Registrar factura en la app + adjuntar PDF
                            ↓
                    Marcar como abonada al cobrar
                            ↓
                    Emitir factura saldo → repetir
```

## Base de datos

Esquema simplificado:

```
clientes
  └── presupuestos (estado: pendiente | aprobado | cancelado)
        └── facturas (tipo: adelanto | saldo | parcial | otros)
                     (estado: pendiente | abonada)
```

Los archivos adjuntos (PDF/imágenes de AFIP) se almacenan en el sistema de archivos; la base de datos guarda solo el nombre del archivo.

## Notas

- Las facturas **no se generan** dentro de la app — se emiten en AFIP y se adjuntan como comprobante
- El archivo `consorcios_precargados.md` contiene los datos para cargar la lista inicial de clientes
- Hacer backup periódico de la carpeta `datos/` en producción
