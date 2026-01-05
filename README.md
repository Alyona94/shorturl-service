## Запуск локально
1. pip install -r requirements.txt
2. python app.py

## Запуск готового образа с Docker Hub
 docker run -d -p 8001:80 -v shorturl_data:/app/data alyonaloz/shorturl-service:latest
  
### Остановка и удаление контейнера:
docker stop shorturl
docker rm shorturl
