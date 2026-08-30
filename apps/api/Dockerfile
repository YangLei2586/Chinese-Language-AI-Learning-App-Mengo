FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY app ./app
EXPOSE 8000
ENV MENGO_DATABASE_URL=sqlite:////data/mengo.db
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
