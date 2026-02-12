#!/bin/bash

# RAIL Portal Plugin Build and Deploy Script
# This script automates the complete build and deployment workflow

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/mnt/${USER}/git/rail-at-sas"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
BACKEND_DIR="${PROJECT_ROOT}/backend"
JARFILES_DIR="${PROJECT_ROOT}/jarfiles"

# Function to print colored messages
print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Step 1: Git Pull
print_step "Step 1/5: Pulling latest changes from git..."
cd "${PROJECT_ROOT}"
git pull || {
    print_error "Git pull failed!"
    exit 1
}

# Step 2: Frontend Build
print_step "Step 2/5: Building frontend plugin..."
cd "${FRONTEND_DIR}"

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    print_warning "node_modules not found. Installing dependencies..."
    npm install
fi

npm run build:plugin || {
    print_error "Frontend build failed!"
    exit 1
}

# Step 3: Backend Build
print_step "Step 3/5: Building backend with atlas-mvn..."
cd "${BACKEND_DIR}"

atlas-mvn clean package -DskipTests || {
    print_error "Backend build failed!"
    exit 1
}

# Step 4: Find, rename, and copy JAR
print_step "Step 4/5: Processing JAR file..."
cd "${BACKEND_DIR}/target"

# Find the SNAPSHOT JAR
SNAPSHOT_JAR="rail-portal-plugin-2.0.0-SNAPSHOT.jar"

if [ ! -f "${SNAPSHOT_JAR}" ]; then
    print_error "JAR file not found: ${SNAPSHOT_JAR}"
    exit 1
fi

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d%H%M%S)
NEW_JAR_NAME="rail-portal-plugin-2.0.0-${TIMESTAMP}.jar"

# Rename the JAR
mv "${SNAPSHOT_JAR}" "${NEW_JAR_NAME}"
print_step "Renamed JAR to: ${NEW_JAR_NAME}"

# Copy to jarfiles directory
cp "${NEW_JAR_NAME}" "${JARFILES_DIR}/"
print_step "Copied JAR to jarfiles folder"

# Step 5: Git Commit and Push
print_step "Step 5/5: Committing and pushing changes..."
cd "${PROJECT_ROOT}"

# Stage all changes (source code + JAR)
print_step "Staging all changes (source code and JAR)..."
git add -A

# Create commit message with JAR name and timestamp
COMMIT_MESSAGE="Build: ${NEW_JAR_NAME}

- Frontend built with npm run build:plugin
- Backend compiled with atlas-mvn clean package
- JAR file: ${NEW_JAR_NAME}
- Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

# Commit with detailed message
git commit -m "${COMMIT_MESSAGE}" || {
    print_warning "Nothing to commit (all changes already committed)"
}

# Push to remote
git push || {
    print_error "Git push failed!"
    exit 1
}

print_step "All changes committed and pushed successfully"

# Success message
echo ""
echo -e "${GREEN}✓ Build and deployment completed successfully!${NC}"
echo -e "${GREEN}  JAR file: ${NEW_JAR_NAME}${NC}"
echo ""
