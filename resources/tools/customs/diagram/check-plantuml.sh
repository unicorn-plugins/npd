#!/bin/bash
# PlantUML Syntax Checker using Docker Container
# Similar to Mermaid checker - checks container status before validation

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Check if file path is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No file path provided${NC}"
    echo "Usage: $0 <plantuml-file>"
    echo "Example: $0 diagram.puml"
    exit 1
fi

FILE_PATH="$1"

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    echo -e "${RED}Error: File not found: $FILE_PATH${NC}"
    exit 1
fi

# Get absolute path
ABSOLUTE_PATH=$(realpath "$FILE_PATH")
FILE_NAME=$(basename "$ABSOLUTE_PATH")

echo -e "\n${CYAN}Checking PlantUML syntax for: $FILE_NAME${NC}"
echo -e "${GRAY}$(printf '=%.0s' {1..60})${NC}"

# Check container status: running / stopped / not exists
CONTAINER_RUNNING=$(docker ps --filter "name=plantuml" --format "{{.Names}}" 2>/dev/null)
CONTAINER_EXISTS=$(docker ps -a --filter "name=plantuml" --format "{{.Names}}" 2>/dev/null)

if [ -z "$CONTAINER_RUNNING" ]; then
    if [ ! -z "$CONTAINER_EXISTS" ]; then
        # Container exists but stopped - restart it
        echo -e "${YELLOW}PlantUML container is stopped. Restarting...${NC}"
        docker start plantuml >/dev/null 2>&1
        sleep 2
        echo -e "${GREEN}Container restarted.${NC}"
    else
        # Container does not exist - create and start it
        echo -e "${YELLOW}PlantUML container does not exist. Creating...${NC}"
        docker run -d --name plantuml -p 38080:8080 plantuml/plantuml-server:latest >/dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo -e "${RED}Error: Failed to create PlantUML container${NC}"
            exit 1
        fi
        sleep 3
        echo -e "${GREEN}Container created and started.${NC}"
    fi
fi

# Generate unique temp filename
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
PID=$$
TEMP_FILE="/tmp/puml_${TIMESTAMP}_${PID}.puml"

# Copy file to container
echo -e "${GRAY}Copying file to container...${NC}"
docker cp "$ABSOLUTE_PATH" "plantuml:$TEMP_FILE" >/dev/null 2>&1

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to copy file to container${NC}"
    exit 1
fi

# Find JAR file location
echo -e "${GRAY}Finding PlantUML JAR file location...${NC}"
JAR_PATH=$(docker exec plantuml sh -c 'find / -name "plantuml*.jar" 2>/dev/null | head -1')

if [ -z "$JAR_PATH" ]; then
    echo -e "${RED}Error: PlantUML JAR file not found in container.${NC}"
    docker exec -u root plantuml rm -f "$TEMP_FILE" >/dev/null 2>&1
    exit 1
fi

# Run syntax check
echo -e "${GRAY}Running syntax check...${NC}"
OUTPUT=$(docker exec plantuml sh -c "java -jar '$JAR_PATH' -checkonly '$TEMP_FILE'" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}Success: PlantUML syntax is valid!${NC}"
else
    echo -e "\n${RED}Error: PlantUML syntax validation failed!${NC}"
    echo -e "\n${RED}Error details:${NC}"

    # Detailed error check
    DETAIL=$(docker exec plantuml sh -c "cd /tmp && java -jar $JAR_PATH -failfast -v $TEMP_FILE 2>&1 | grep -E 'Error line'" 2>&1)

    if [ ! -z "$DETAIL" ]; then
        while IFS= read -r line; do
            echo -e "  ${RED}$line${NC}"
        done <<< "$DETAIL"
    else
        echo -e "  ${RED}$OUTPUT${NC}"
    fi

    # Clean up and exit with error
    docker exec -u root plantuml rm -f "$TEMP_FILE" >/dev/null 2>&1
    exit 1
fi

# Clean up temp files
echo -e "\n${GRAY}Cleaning up...${NC}"
docker exec -u root plantuml rm -f "$TEMP_FILE" >/dev/null 2>&1

echo -e "\n${CYAN}Validation complete!${NC}"

# Note: Container is kept running for subsequent checks
# To stop: docker stop plantuml && docker rm plantuml
