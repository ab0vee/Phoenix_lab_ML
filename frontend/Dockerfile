# Используем официальный Node.js образ
FROM node:18-alpine

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm ci

# Копируем остальные файлы
COPY . .

# Переменные окружения для сборки Next.js (NEXT_PUBLIC_* должны быть доступны на этапе сборки)
# Значения по умолчанию, будут переопределены через docker-compose.yml
ARG NEXT_PUBLIC_API_URL=http://localhost:5000
ARG NEXT_PUBLIC_ML_SERVICE_URL=http://localhost:8000

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_ML_SERVICE_URL=$NEXT_PUBLIC_ML_SERVICE_URL
ENV NODE_ENV=production

# Собираем приложение
RUN npm run build

# Открываем порт
EXPOSE 3000

# Переменные окружения для runtime
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Запуск приложения
CMD ["npm", "start"]

