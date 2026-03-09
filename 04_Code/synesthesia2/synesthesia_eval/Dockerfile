FROM node:20-slim

WORKDIR /app

# Copy data (clips + labels + metadata)
COPY data/ ./data/

# Copy server source
COPY web-labeler/server/ ./web-labeler/server/

# Copy pre-built React client (already built in repo)
COPY web-labeler/client/build/ ./web-labeler/client/build/

# Install server dependencies
WORKDIR /app/web-labeler/server
RUN npm install --production

ENV CLIPS_DIR=/app/data/clips
ENV PORT=3001

EXPOSE 3001

# Run migration then start server
CMD node src/migrate/002_seed_from_json.js && node src/index.js
