# Zeuz Backend

This is the backend for the **Zeuz** project, built using **Django** and **PostgreSQL**.

## Installation Guide

### 1. Clone the Repository
```sh
git clone 
cd zeuz-backend
```

### 2. Create and Activate a Virtual Environment
#### On macOS/Linux:
```sh
python3 -m venv venv
source venv/bin/activate
```

#### On Windows:
```sh
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```


### 4. Configure Database
In your `settings.py`, update the `DATABASES` configuration for local PostgreSQL:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '',  
        'USER': '',  
        'PASSWORD': '',  
        'HOST': 'localhost',  
        'PORT': '5432',  
    }
}
```

### 5. Apply Migrations
```sh
python manage.py migrate
```

### 6. Create a Superuser (Optional)
```sh
python manage.py createsuperuser
```
Follow the prompts to set up an admin user.

### 7. Run the Development Server
```sh
python manage.py runserver
```
The backend should now be running at `http://127.0.0.1:8000/`.

