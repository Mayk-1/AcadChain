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
cd certichain
```

### Crear y activar el entorno virtual

```bash
python -m venv env
env\Scripts\activate
```

### Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Abre el gestor de MySql y crea la base de datos

```
CREATE DATABASE certichain_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Abrir el archivo settings.py y modifica las credenciales de tu base de datos

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'certichain_db',
        'USER': 'tu_usuario_local',
        'PASSWORD': 'tu_contraseña_local',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

##Ejecutar Migraciones

```bash
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
