Why is the Current POM version and the Enter version for this release sections returning a bunch of executables and paths?: 

Current POM version: Executing: /mnt/k.kashmiry/atlassian-plugin-sdk-8.2.10/apache-maven-3.9.5/bin/mvn  -gs /mnt/k.kashmiry/atlassian-plugin-sdk-8.2.10/apache-maven-3.9.5/conf/settings.xml help:evaluate -Dexpression=project.version -q -DforceStdout
2.0.0
Enter version for this release (Default suggestion: Executing: /mnt/k kashmiry/atlassian-plugin-sdk-8 2 10/apache-maven-3 9 5/bin/mvn  -gs /mnt/k kashmiry/atlassian-plugin-sdk-8 2 10/apache-maven-3 9 5/conf/settings xml help:evaluate -Dexpression=project 1
2.0.1): 



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
CURRENT_VERSION=$(cd "${BACKEND_DIR}" && atlas-mvn help:evaluate -Dexpression=project.version -q -DforceStdout)

# Logic to suggest the next patch version
SUGGESTED_VERSION=$(echo "$CURRENT_VERSION" | awk -F. '{$NF = $NF + 1;} OFS="." {print $0}')

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
atlas-mvn versions:set -DnewVersion="$VERSION" -DgenerateBackupPoms=false

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

curl --fail --header "PRIVATE-TOKEN: ${TOKEN}" \
     --upload-file "${FINAL_JAR}" \
     "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/packages/generic/rail-portal/${VERSION}/${FINAL_JAR}"

# Step 6: Git Flow & Changelog
print_step "Step 6/8: Committing & Generating Changelog..."
cd "${PROJECT_ROOT}"
echo -e "${YELLOW}Commit Type (feat|fix|chore):${NC}"
read TYPE
echo -e "${YELLOW}Description of work:${NC}"
read DESC

git add .
git commit -m "${TYPE}: ${DESC}"

# Generate Changelog
git-cliff --tag "v${VERSION}" --output CHANGELOG.md
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

