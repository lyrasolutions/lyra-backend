#!/bin/bash

echo "🚀 Lyra Backend MVP Deployment Script"
echo "======================================"

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set. Content generation will not work."
    echo "   Set it with: export OPENAI_API_KEY=sk-your-key-here"
fi

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗄️  Initializing database..."
python -c "from app.db.session import init_db; init_db()"

echo "🌟 Starting Lyra Backend MVP..."
echo "   API Documentation: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo ""
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
