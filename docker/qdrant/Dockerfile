FROM qdrant/qdrant:v1.11.3

USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Не переключаем пользователя обратно - пусть работает как в базовом образе