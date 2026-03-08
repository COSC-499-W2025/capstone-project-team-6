#!/bin/bash

# Docker Setup Test Script


# Check if we're in the scripts directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Please run this script from the scripts/ directory"
    echo "   cd scripts && ./test-docker-setup.sh"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo " Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "Docker is installed"
echo "Docker Compose is installed"
echo ""

# Check if .env file exists in project root
if [ ! -f "../.env" ]; then
    echo ".env file not found in project root. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example ../.env
        echo "Created ../.env file. Please edit it with your API keys."
    else
        echo ".env.example not found"
        exit 1
    fi
else
    echo "✅ .env file exists in project root"
fi
echo ""

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "Dockerfile not found"
    exit 1
fi
echo "Dockerfile exists"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "docker-compose.yml not found"
    exit 1
fi
echo "docker-compose.yml exists"
echo ""

echo "Ready to build! Run:"
echo "   docker-compose up --build"
echo ""
echo "Or run in detached mode:"
echo "   docker-compose up -d --build"
echo ""
