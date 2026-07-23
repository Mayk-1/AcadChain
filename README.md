# AcadChain Backend - Certificación Académica con Blockchain

Este es el backend de **AcadChain**, una aplicación web diseñada para la emisión y verificación inmutable de certificados académicos universitarios. El sistema utiliza una arquitectura blockchain interna basada en una **Lista Enlazada de Bloques**, **Árboles de Merkle** para la agrupación eficiente de datos y criptografía **SHA-256** para garantizar la seguridad.

Desarrollado con **Python**, **Django** y **MySQL**.

---

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado en tu máquina local:
* Python 3.10 o superior
* Servidor MySQL (XAMPP, MySQL Workbench, o similar)
* Git

---

## Guía de Clonación y Configuración Local

Sigue estos pasos en orden para levantar el entorno de desarrollo en tu computadora.

### 1. Clonar el Repositorio
Abre tu terminal, navega hasta tu carpeta de proyectos y ejecuta:
```bash
git clone https://github.com/Mayk-1/AcadChain
git pull origin main
```

### Crear y activar el entorno virtual

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Abre el gestor de MySql y crea la base de datos

```
CREATE DATABASE certichain_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Adaptar las variables de entorno segun el archivo .env.example en un archivo .env en la carpeta principal certichain donde se encuentra manage.py

```
DB_NAME=certichain_db
DB_USER=tu_usuario_local
DB_PASSWORD=tu_contraseña_local
DB_HOST=localhost
DB_PORT=3306
```

##Ejecutar Migraciones

```bash
cd certichain
python manage.py migrate
```

### Ejecutar commandos para simulación y pruebas (OPCIONAL)

```bash
python manage.py generar_datos 5000
python manage.py minar_bloques
```

### Poner en marcha la API web localmente

```bash
python manage.py runserver
```

### Servir el html por http localmente o si puedes de otra manera

Ejecutar dentro de la carpeta frontend y configurar el puerto para las variables de entorno
```bash
python -m http.server 'puerto'
```
