Why is step 6 on the same line as the response from step 5? 
==> Step 5/8: Uploading to GitLab Registry...
{"message":"201 Created"}==> Step 6/8: Committing & Generating Changelog...
Commit Type (feat|fix|chore):

#!/bin/bash
# RAIL Portal Plugin Build and Deploy Script
set -e 

# --- Original Colors & Functions ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' 

print_step() { echo -e "${GREEN}==>${NC} $1"; }
print_error() { echo -e "${RED}ERROR:${NC} $1"; }
print_warning() { echo -e "${YELLOW}WARNING:${NC} $1"; }

# --- Step 0: Dependency Check ---
check_dependencies() {
    local dependencies=("npm" "atlas-mvn" "git-cliff" "curl" "git" "awk")
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
TOKEN="your_gl_token"
GITLAB_URL="https://gitlab.com"

# Start Execution
check_dependencies

# Step 1: Git Pull
print_step "Step 1/8: Pulling latest changes..."
cd "${PROJECT_ROOT}"
git pull

# Step 2: Version Management
print_step "Step 2/8: Version Validation..."

# 1. Fetch version and strip any 'Executing...' noise or whitespace
RAW_VERSION=$(cd "${BACKEND_DIR}" && atlas-mvn help:evaluate -Dexpression=project.version -q -DforceStdout | grep -E '^[0-9]' | tail -n 1 | tr -d '[:space:]')

# 2. Safety check: If RAW_VERSION is empty, fall back to a safe default
CURRENT_VERSION=${RAW_VERSION:-"1.0.0"}

# 3. Increment the patch version (the robust way)
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

# Step 3: Frontend Build
print_step "Step 3/8: Building frontend..."
cd "${FRONTEND_DIR}"
if [ ! -d "node_modules" ]; then
    print_warning "node_modules not found. Installing..."
    npm install
fi
npm run build:plugin

# Step 4: Backend Build
print_step "Step 4/8: Building backend..."
cd "${BACKEND_DIR}"
atlas-mvn clean package -DskipTests

# Step 5: Process JAR & Upload
print_step "Step 5/8: Uploading to GitLab Registry..."
cd "${BACKEND_DIR}/target"
FINAL_JAR="rail-portal-plugin-${VERSION}.jar"

if [ ! -f "${FINAL_JAR}" ]; then
    print_error "JAR file not found: ${FINAL_JAR}"
    exit 1
fi

# We add -s (silent) but keep --fail to ensure we see the result cleanly
curl --fail --header "PRIVATE-TOKEN: ${TOKEN}" \
     --upload-file "${FINAL_JAR}" \
     "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/packages/generic/rail-portal/${VERSION}/${FINAL_JAR}"

# THIS IS THE FIX: Forces a newline after the API response
echo "" 

# Step 6: Git Flow & Changelog
print_step "Step 6/8: Committing & Generating Changelog..."
cd "${PROJECT_ROOT}"

echo -e "${YELLOW}Select Commit Type (feat|fix|chore|refactor|docs):${NC}"
read TYPE
echo -e "${YELLOW}Enter Scope (e.g., ui, backend, nav) or leave blank:${NC}"
read SCOPE
echo -e "${YELLOW}Enter Description:${NC}"
read DESC

# Format the message based on whether a scope was provided
if [ -z "$SCOPE" ]; then
    FULL_MSG="${TYPE}: ${DESC}"
else
    FULL_MSG="${TYPE}(${SCOPE}): ${DESC}"
fi

# Stage and commit your current work
if [[ -n $(git status -s) ]]; then
    git add .
    git commit -m "${FULL_MSG}"
else
    print_warning "No local changes to commit. Proceeding to release metadata..."
fi

# This is the 'Metadata' commit that git-cliff will skip in the changelog
# We use the specific 'prepare for' syntax to satisfy your .toml skip rule
git commit --allow-empty -m "chore(release): prepare for v${VERSION}"

# Generate Changelog
git-cliff --tag "v${VERSION}" --output CHANGELOG.md

# Amend the release metadata commit to include the updated CHANGELOG.md
git add CHANGELOG.md
git commit --amend --no-edit


# Step 7: Tagging
print_step "Step 7/8: Finalizing Git Tag..."
git tag -a "v${VERSION}" -m "${TYPE}: ${DESC}"

# Step 8: Final Push
print_step "Step 8/8: Pushing code and tags to GitLab..."
git push origin main --tags -f

# Final Success Message
echo -e "\n${GREEN}─────────────────────────────────────────────────────────────────${NC}"
echo -e "${GREEN}✓ Release ${VERSION} is complete!${NC}"
echo -e "${YELLOW}Artifact URL:${NC} ${GITLAB_URL}/${PROJECT_ID}/-/packages"
echo -e "${YELLOW}Tag:${NC} v${VERSION}"
echo -e "${YELLOW}Changelog updated and pushed.${NC}"
echo -e "${GREEN}─────────────────────────────────────────────────────────────────${NC}\n"

