from app import app

from app.celery_app import make_celery

app = create_app()
celery = make_celery(app)

# Configurar Celery
app.config.update(
    CELERY_BROKER_URL="redis://localhost:6379/0",
    CELERY_RESULT_BACKEND="redis://localhost:6379/0"
)
celery = make_celery(app)

if __name__ == "__main__":
    app.run(debug=True)

