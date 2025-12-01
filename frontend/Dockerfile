# ---- Base image ----
FROM node:18-alpine AS base

WORKDIR /app

# ---- Install dependencies ----
FROM base AS deps

COPY package.json package-lock.json* pnpm-lock.yaml* ./

RUN npm install

# ---- Dev image ----
FROM base AS dev

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
