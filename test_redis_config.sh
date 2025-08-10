#!/bin/bash

echo "🧪 Testing Redis configuration without version check errors..."

# Test 1: Custom config without RedisSearch
echo "📋 Test 1: Custom config (RedisSearch disabled)"
docker run --rm -d --name test-redis-custom \
  -p 36379:6379 \
  -v "$(pwd)/docker/redismod/redis.conf:/etc/redis/redis.conf" \
  redislabs/redismod:edge \
  redis-server /etc/redis/redis.conf

sleep 3

# Check if Redis is running
if python -c "import socket; s = socket.socket(); result = s.connect_ex(('127.0.0.1', 36379)); s.close(); exit(0 if result == 0 else 1)"; then
    echo "✅ Redis is running successfully!"
    
    # Check logs for version errors
    if docker logs test-redis-custom 2>&1 | grep -q "version is too old"; then
        echo "❌ Version error still present"
    else
        echo "✅ No version errors in logs!"
    fi
    
    # Test Redis modules
    echo "🔍 Checking loaded modules..."
    docker logs test-redis-custom 2>&1 | grep "Module.*loaded"
    
else
    echo "❌ Redis failed to start"
fi

# Cleanup
docker stop test-redis-custom 2>/dev/null

echo "🏁 Test completed!"
