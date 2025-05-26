@echo off
setlocal EnableDelayedExpansion

REM Docker run script for Turath AI Agent (Windows)
REM Usage: scripts\docker-run.bat [dev|prod] [--build]

set "ENV=dev"
set "BUILD=false"

REM Parse arguments
:parse_args
if "%1"=="" goto :check_env
if "%1"=="dev" (
    set "ENV=dev"
    shift
    goto :parse_args
)
if "%1"=="prod" (
    set "ENV=prod"
    shift
    goto :parse_args
)
if "%1"=="--build" (
    set "BUILD=true"
    shift
    goto :parse_args
)
echo Unknown argument: %1
echo Usage: %0 [dev^|prod] [--build]
exit /b 1

:check_env
REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found. Copying from env.example...
    if exist env.example (
        copy env.example .env
        echo 🔑 Please edit .env file with your actual API keys before running!
        pause
        exit /b 1
    ) else (
        echo ❌ env.example file not found. Please create .env file manually.
        pause
        exit /b 1
    )
)

echo 🐳 Starting Turath AI Agent in %ENV% mode

REM Build if requested
if "%BUILD%"=="true" (
    echo 🔨 Building Docker images...
    docker-compose build
)

REM Run based on environment
if "%ENV%"=="prod" (
    echo 🚀 Starting production environment...
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    echo ✅ Services started in production mode!
    echo 🌐 AI Agent: http://localhost:8000
    echo 🔧 MCP Server: http://localhost:8001
    echo 📊 Check logs: docker-compose logs -f
    echo 🛑 Stop services: docker-compose down
) else (
    echo 🔧 Starting development environment...
    docker-compose up
)

endlocal 