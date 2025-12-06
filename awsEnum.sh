#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ "$#" -ne 2 ]; then
    echo -e "${RED}[!] Usage: $0 <ACCESS_KEY_ID> <SECRET_ACCESS_KEY>${NC}"
    exit 1
fi

# Set Credentials temporarily for this session
export AWS_ACCESS_KEY_ID="$1"
export AWS_SECRET_ACCESS_KEY="$2"
export AWS_DEFAULT_REGION="us-east-1" # Default to us-east-1 for global checks
export AWS_PAGER="" # Disable paging to print everything to stdout

echo -e "${BLUE}[*] Starting AWS Key Recon...${NC}"
echo -e "${BLUE}[*] Using Region: $AWS_DEFAULT_REGION${NC}"
echo "---------------------------------------------------"

# 1. CHECK IDENTITY (The Ping)
# ---------------------------------------------------
IDENTITY=$(aws sts get-caller-identity --output json 2>/dev/null)

if [ $? -ne 0 ]; then
    echo -e "${RED}[-] Invalid Credentials or API Error. The key seems dead.${NC}"
    exit 1
else
    echo -e "${GREEN}[+] Valid Credentials!${NC}"
    
    USER_ID=$(echo $IDENTITY | jq -r '.UserId')
    ACCOUNT=$(echo $IDENTITY | jq -r '.Account')
    ARN=$(echo $IDENTITY | jq -r '.Arn')
    
    echo -e "    ${YELLOW}Account ID:${NC} $ACCOUNT"
    echo -e "    ${YELLOW}User ID:${NC}    $USER_ID"
    echo -e "    ${YELLOW}ARN:${NC}        $ARN"
fi

echo "---------------------------------------------------"

# 2. IAM ENUMERATION (Privileges)
# ---------------------------------------------------
# Extract username from ARN (usually last part after /)
USERNAME=$(echo $ARN | awk -F/ '{print $NF}')

echo -e "${BLUE}[*] Attempting IAM Enumeration for user: $USERNAME${NC}"

# Check attached policies
POLICIES=$(aws iam list-attached-user-policies --user-name "$USERNAME" --output json 2>/dev/null)
if [ $? -eq 0 ]; then
    COUNT=$(echo $POLICIES | jq '.AttachedPolicies | length')
    echo -e "${GREEN}[+] List-Attached-User-Policies success ($COUNT found):${NC}"
    echo $POLICIES | jq -r '.AttachedPolicies[].PolicyName' | sed 's/^/    - /'
else
    echo -e "${RED}[-] List-Attached-User-Policies failed (Access Denied).${NC}"
fi

# Check inline policies
INLINE=$(aws iam list-user-policies --user-name "$USERNAME" --output json 2>/dev/null)
if [ $? -eq 0 ]; then
    COUNT=$(echo $INLINE | jq '.PolicyNames | length')
    if [ "$COUNT" -gt 0 ]; then
        echo -e "${GREEN}[+] Inline Policies found:${NC}"
        echo $INLINE | jq -r '.PolicyNames[]' | sed 's/^/    - /'
    fi
fi

echo "---------------------------------------------------"

# 3. S3 ENUMERATION (Data Storage)
# ---------------------------------------------------
echo -e "${BLUE}[*] Attempting to List S3 Buckets...${NC}"
BUCKETS=$(aws s3 ls 2>/dev/null)

if [ $? -eq 0 ]; then
    COUNT=$(echo "$BUCKETS" | wc -l)
    echo -e "${GREEN}[+] S3 List Success! Found $COUNT buckets.${NC}"
    if [ "$COUNT" -gt 0 ]; then
        echo -e "${YELLOW}Top 5 Buckets:${NC}"
        echo "$BUCKETS" | head -n 5 | awk '{print "    - " $3}'
        if [ "$COUNT" -gt 5 ]; then echo "    ... (and more)"; fi
    fi
else
    echo -e "${RED}[-] S3 List Failed (Access Denied).${NC}"
fi

echo "---------------------------------------------------"

# 4. EC2 ENUMERATION (Compute)
# ---------------------------------------------------
echo -e "${BLUE}[*] Attempting to Describe EC2 Instances (us-east-1)...${NC}"
INSTANCES=$(aws ec2 describe-instances --output json 2>/dev/null)

if [ $? -eq 0 ]; then
    # Count running instances
    COUNT=$(echo $INSTANCES | jq -r '.Reservations[].Instances[] | select(.State.Name=="running") | .InstanceId' 2>/dev/null | wc -l)
    echo -e "${GREEN}[+] EC2 Describe Success! Found $COUNT running instances.${NC}"
else
    echo -e "${RED}[-] EC2 Describe Failed (Access Denied).${NC}"
fi

echo "---------------------------------------------------"
echo -e "${BLUE}[*] Recon Complete.${NC}"
