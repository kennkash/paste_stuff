#!/bin/bash
# RAIL Portal Plugin Build and Deploy Script
set -e 

# --- Colors & Functions ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' 

print_step() { echo -e "${GREEN}==>${NC} $1"; }
print_error() { echo -e "${RED}ERROR:${NC} $1"; }
print_warning() { echo -e "${YELLOW}WARNING:${NC} $1"; }

# --- Step 0: Dependency Check ---
check_dependencies() {
    local dependencies=("npm" "atlas-mvn" "git-cliff" "curl" "git" "awk" "cut" "tr")
    for cmd in "${dependencies[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            print_error "Dependency '$cmd' is not installed. Please install it to proceed."
            exit 1
        fi
    done
}

# --- Configuration ---
PROJECT_ROOT="/mnt/${USER}/git/rail-at-sas"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
BACKEND_DIR="${PROJECT_ROOT}/backend"
PROJECT_ID="123456" 
TOKEN="${GL_DEPLOY_TOKEN}"
GITLAB_URL="https://gitlab.com"

# Start Execution
check_dependencies

# Step 1: Git Pull
print_step "Step 1/9: Pulling latest changes..."
cd "${PROJECT_ROOT}"
git pull

# Step 2: Version Management
print_step "Step 2/9: Version Validation..."
RAW_VERSION=$(cd "${BACKEND_DIR}" && atlas-mvn help:evaluate -Dexpression=project.version -q -DforceStdout | grep -E '^[0-9]' | tail -n 1 | tr -d '[:space:]')
CURRENT_VERSION=${RAW_VERSION:-"1.0.0"}

BASE_VERSION=$(echo "$CURRENT_VERSION" | cut -d. -f1-2)
PATCH_VERSION=$(echo "$CURRENT_VERSION" | cut -d. -f3)
SUGGESTED_VERSION="${BASE_VERSION}.$((PATCH_VERSION + 1))"

echo -e "${YELLOW}Current POM version: ${CURRENT_VERSION}${NC}"
read -p "Enter version for this release (Default suggestion: ${SUGGESTED_VERSION}): " NEW_VERSION
VERSION=${NEW_VERSION:-$SUGGESTED_VERSION}

# BLOCKER: Check GitLab Registry
print_step "Verifying version uniqueness..."
PACKAGE_EXISTS=$(curl -s --header "PRIVATE-TOKEN: ${TOKEN}" \
    "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/packages?package_version=${VERSION}" | grep -c "version\":\"${VERSION}\"" || true)

if [ "$PACKAGE_EXISTS" -gt 0 ]; then
    print_error "Version ${VERSION} already exists in GitLab Registry! Aborting build."
    exit 1
fi

# Apply version to POM
cd "${BACKEND_DIR}"
atlas-mvn versions:set -DnewVersion="$VERSION" -DgenerateBackupPoms=false -q

# Step 3 & 4: Build
print_step "Step 3/9: Building frontend..."
cd "${FRONTEND_DIR}"
[ ! -d "node_modules" ] && npm install
npm run build:plugin

print_step "Step 4/9: Building backend..."
cd "${BACKEND_DIR}"
atlas-mvn clean package -DskipTests

# Step 5: Process JAR & Upload
print_step "Step 5/9: Uploading to GitLab Registry..."
cd "${BACKEND_DIR}/target"
FINAL_JAR="rail-portal-plugin-${VERSION}.jar"
PACKAGE_URL="${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/packages/generic/rail-portal/${VERSION}/${FINAL_JAR}"

curl --fail --header "PRIVATE-TOKEN: ${TOKEN}" \
     --upload-file "${FINAL_JAR}" \
     "${PACKAGE_URL}"

echo "" 

# Step 6: Git Flow & Changelog
print_step "Step 6/9: Committing Release Metadata & Generating Changelog..."
cd "${PROJECT_ROOT}"

echo -e "${YELLOW}Type (feat|fix|chore|refactor):${NC}"
read TYPE
echo -e "${YELLOW}Scope (ui|nav|backend):${NC}"
read SCOPE
echo -e "${YELLOW}Description:${NC}"
read DESC

FULL_MSG="${TYPE}(${SCOPE:-all}): ${DESC}"

if [[ -n $(git status -s) ]]; then
    git add .
    git commit -m "${FULL_MSG}"
fi

# Release Anchor
git commit --allow-empty -m "chore(release): prepare for v${VERSION}"
git-cliff --tag "v${VERSION}" --output CHANGELOG.md
git add CHANGELOG.md
git commit --amend --no-edit

# Step 7: Tagging
print_step "Step 7/9: Finalizing Git Tag..."
git tag -a "v${VERSION}" -m "${FULL_MSG}"

# Step 8: Final Push
print_step "Step 8/9: Pushing code and tags..."
git push origin main --tags -f

# Step 9: Create GitLab Release Entry with Assets
print_step "Step 9/9: Creating Official GitLab Release..."
# FIX: Explicitly target the new tag for the description notes
NOTES=$(git-cliff --latest --strip all)

curl --header "Content-Type: application/json" \
     --header "PRIVATE-TOKEN: ${TOKEN}" \
     --data "{
       \"name\": \"Release ${VERSION}\",
       \"tag_name\": \"v${VERSION}\",
       \"description\": \"${NOTES}\",
       \"assets\": {
         \"links\": [{
           \"name\": \"${FINAL_JAR}\",
           \"url\": \"${PACKAGE_URL}\",
           \"link_type\": \"package\"
         }]
       }
     }" \
     --request POST "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/releases"

echo -e "\n${GREEN}✓ Release ${VERSION} complete! Artifact linked in GitLab Releases.${NC}\n"
