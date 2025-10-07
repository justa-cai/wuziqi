#!/bin/bash

# Debug script for WuZiQi (Gomoku) Android app
# This script builds, installs, and runs the debug APK

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}Debugging WuZiQi (Gomoku) Android Project${NC}"
echo "Project directory: $PROJECT_DIR"

# Change to project directory
cd "$PROJECT_DIR"

# Function to print usage
usage() {
    echo "Usage: $0 [option]"
    echo "Options:"
    echo "  build     - Build the debug APK only (default)"
    echo "  install   - Build and install debug APK to connected device/emulator"
    echo "  run       - Build, install, and run the app"
    echo "  clean     - Clean build files"
    echo "  help      - Show this help message"
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check if we're in the right directory
    if [ ! -f "build.gradle" ] || [ ! -f "settings.gradle" ]; then
        echo -e "${RED}Error: build.gradle or settings.gradle not found.${NC}"
        exit 1
    fi

    # Check if gradlew exists
    if [ ! -x "gradlew" ]; then
        echo -e "${RED}Error: gradlew not found or not executable.${NC}"
        exit 1
    fi

    # Check if gradle-wrapper.jar exists
    if [ ! -f "gradle/wrapper/gradle-wrapper.jar" ]; then
        echo -e "${YELLOW}gradle-wrapper.jar not found. Attempting to set up wrapper...${NC}"
        if command -v gradle >/dev/null 2>&1; then
            gradle wrapper --gradle-version 8.0
            if [ -f "gradle/wrapper/gradle-wrapper.jar" ]; then
                echo -e "${GREEN}Gradle wrapper set up successfully!${NC}"
            else
                echo -e "${RED}Failed to set up Gradle wrapper.${NC}"
                echo -e "${YELLOW}Make sure Gradle is installed and in your PATH.${NC}"
                exit 1
            fi
        else
            echo -e "${RED}gradle command not found.${NC}"
            echo -e "${YELLOW}Please install Gradle first or run: ./build.sh setup-wrapper${NC}"
            exit 1
        fi
    fi

    # Verify that the JAR file is actually a JAR and not a text file
    if file "gradle/wrapper/gradle-wrapper.jar" 2>/dev/null | grep -q "text"; then
        echo -e "${RED}gradle-wrapper.jar appears to be a text file, not a binary JAR.${NC}"
        echo -e "${YELLOW}This project requires a proper Gradle wrapper to build.${NC}"
        echo -e "${YELLOW}Please ensure you have a proper Android Studio/Gradle environment.${NC}"
        exit 1
    fi

    echo -e "${GREEN}Prerequisites check passed${NC}"
}

# Function to build debug APK
build_debug() {
    echo -e "${YELLOW}Building debug APK...${NC}"
    
    if ./gradlew --info  assembleDebug; then
        echo -e "${GREEN}Debug APK built successfully!${NC}"
        echo "Location: app/build/outputs/apk/debug/app-debug.apk"
    else
        echo -e "${RED}Gradle build failed.${NC}"
        echo -e "${YELLOW}This may be due to Java version incompatibility or missing Android SDK.${NC}"
        echo -e "${YELLOW}Make sure you have Android SDK installed and JAVA_HOME set correctly.${NC}"
        exit 1
    fi
}

# Function to install debug APK to device
install_debug() {
    echo -e "${YELLOW}Installing debug APK to connected device...${NC}"
    
    # Check if there's a connected device
    if ! adb devices | grep -q "device"; then
        echo -e "${RED}No connected devices found. Please connect a device or start an emulator.${NC}"
        echo -e "${YELLOW}To start an emulator: emulator -avd <your_avd_name>${NC}"
        exit 1
    fi
    
    if ./gradlew installDebug; then
        echo -e "${GREEN}Debug APK installed successfully!${NC}"
    else
        echo -e "${RED}Gradle install failed.${NC}"
        echo -e "${YELLOW}This may be due to Java version incompatibility or missing Android SDK.${NC}"
        echo -e "${YELLOW}Make sure you have Android SDK installed and JAVA_HOME set correctly.${NC}"
        exit 1
    fi
}

# Function to run the app
run_app() {
    echo -e "${YELLOW}Running the app...${NC}"
    
    # Define the package name and main activity
    PACKAGE_NAME="com.example.wuziqi"
    MAIN_ACTIVITY="com.example.wuziqi.MainActivity"
    
    # Start the activity using adb
    if adb shell am start -n "$PACKAGE_NAME/$MAIN_ACTIVITY" 2>/dev/null; then
        echo -e "${GREEN}App started successfully!${NC}"
        echo -e "${YELLOW}Check your device/emulator for the WuZiQi game.${NC}"
    else
        echo -e "${RED}Failed to start the app.${NC}"
        echo -e "${YELLOW}Make sure the app is installed correctly.${NC}"
        # Try to install first before running
        install_debug
        if adb shell am start -n "$PACKAGE_NAME/$MAIN_ACTIVITY"; then
            echo -e "${GREEN}App started successfully after installation!${NC}"
        else
            echo -e "${RED}Could not start the app.${NC}"
            exit 1
        fi
    fi
}

# Function to clean build files
clean_build() {
    echo -e "${YELLOW}Cleaning build files...${NC}"
    
    if ./gradlew clean; then
        echo -e "${GREEN}Build files cleaned successfully!${NC}"
    else
        echo -e "${RED}Gradle clean failed.${NC}"
        echo -e "${YELLOW}This may be due to Java version incompatibility or missing Android SDK.${NC}"
        echo -e "${YELLOW}Make sure you have Android SDK installed and JAVA_HOME set correctly.${NC}"
        exit 1
    fi
}

# Default action
ACTION=${1:-build}

# Check prerequisites
check_prerequisites

case "$ACTION" in
    "build")
        build_debug
        ;;
    "install")
        build_debug
        install_debug
        ;;
    "run")
        build_debug
        install_debug
        run_app
        ;;
    "clean")
        clean_build
        ;;
    "help"|"-h"|"--help")
        usage
        ;;
    *)
        echo -e "${RED}Unknown option: $ACTION${NC}"
        usage
        exit 1
        ;;
esac

echo -e "${GREEN}Debug script completed successfully!${NC}"