#!/bin/bash
# Test script for file upload functionality

echo "======================================"
echo "File Upload Test Script"
echo "======================================"
echo ""

# Check if server is running
echo "1. Checking if backend server is running..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "   ✓ Server is running!"
else
    echo "   ✗ Server is NOT running!"
    echo ""
    echo "Please start the server first:"
    echo "   cd src/backend"
    echo "   source .venv/bin/activate"
    echo "   uvicorn main:app --reload"
    exit 1
fi

echo ""
echo "2. Creating test files..."
echo "   Creating test_file_1.txt..."
echo "This is test file #1" > test_file_1.txt

echo "   Creating test_file_2.txt..."
echo "This is test file #2" > test_file_2.txt

echo "   Creating test_image.txt (simulated image)..."
echo "Simulated image content" > test_image.txt

echo "   ✓ Test files created!"

echo ""
echo "3. Testing single file upload..."
python upload_cli.py upload test_file_1.txt

echo ""
echo "4. Testing multiple file upload..."
python upload_cli.py upload test_file_2.txt test_image.txt

echo ""
echo "5. Checking uploaded files..."
echo "   Files in uploads directory:"
ls -lh uploads/

echo ""
echo "======================================"
echo "Test Complete!"
echo "======================================"
echo ""
echo "To view uploaded files:"
echo "   ls -la uploads/"
echo ""
echo "To clean up test files:"
echo "   rm test_file_1.txt test_file_2.txt test_image.txt"
