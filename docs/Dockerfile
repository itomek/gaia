# Copyright(C) 2025-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#
# GAIA SDK Documentation - Auth Proxy
#
# Simple Node.js proxy server for access-code protected docs.

FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --omit=dev

# Copy server
COPY server.js ./

# Set environment
ENV NODE_ENV=production

EXPOSE 3000

CMD ["node", "server.js"]
