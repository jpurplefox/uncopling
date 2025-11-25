# Uncoupling

Django project with MercadoLibre OAuth integration.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd uncoupling
```

2. Create and activate a virtual environment:
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Variables Configuration

1. Copy the environment variables example file:
```bash
cp uncoupling/.env.example uncoupling/.env
```

2. Edit the `uncoupling/.env` file with your credentials:
```bash
# Django Settings
SECRET_KEY='your-secret-key-here'
DEBUG=True

# MercadoLibre OAuth Settings
MELI_CLIENT_ID='your-meli-client-id-here'
MELI_CLIENT_SECRET='your-meli-client-secret-here'
MELI_REDIRECT_URI='https://localhost:8000/auth/meli/callback/'
```

### Getting MercadoLibre Credentials

1. Create an application in the [MercadoLibre Developer Portal](https://developers.mercadolibre.com.ar/apps/home)
2. Configure the redirect URL in your application to match `MELI_REDIRECT_URI`
3. Copy the `Client ID` and `Client Secret` from your application

## HTTPS Configuration for Local Development

You need to generate SSL certificates for local development:

```bash
cd uncoupling

# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

During certificate generation, you can press Enter for all fields or fill in the requested information.

## Database Configuration

Apply database migrations:

```bash
cd uncoupling
python manage.py migrate
```

## Create a Superuser (Optional)

To access the Django admin panel:

```bash
python manage.py createsuperuser
```

## Running the Server with HTTPS

To start the development server with HTTPS:

```bash
cd uncoupling
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem
```

The server will be available at: **https://localhost:8000**

**Note:** Your browser will show a security warning because the certificate is self-signed. This is normal in development. You can proceed by clicking "Advanced" and then "Continue" or "Proceed".

### Alternative without HTTPS (Not recommended for OAuth)

If you just want to test the project without HTTPS:

```bash
cd uncoupling
python manage.py runserver
```

The server will be available at: **http://localhost:8000**

**Important:** MercadoLibre requires HTTPS for OAuth redirects, so you must use the HTTPS server to test the full integration.

## Troubleshooting

### Browser doesn't allow access to localhost with HTTPS
- Click on "Advanced"
- Select "Continue to localhost (unsafe)" or "Proceed to localhost (unsafe)"
- In Chrome, you can type `thisisunsafe` on the warning page

### MercadoLibre redirect error
Verify that:
1. The `MELI_REDIRECT_URI` in the `.env` file matches exactly with the one configured in the developer portal
2. You are using HTTPS
3. The port matches (default 8000)
