#!/bin/bash

# Android Build Script for WuZiQi (Gomoku) Game
# This script automates the build process for the Android project

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory - always use the directory where the script is located
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}Building WuZiQi (Gomoku) Android Project${NC}"
echo "Project directory: $PROJECT_DIR"

# Change to project directory to ensure proper relative paths
cd "$PROJECT_DIR"

# Function to print usage
usage() {
    echo "Usage: $0 [option]"
    echo "Options:"
    echo "  build          - Build the APK (default)"
    echo "  debug          - Build debug APK"
    echo "  release        - Build release APK"
    echo "  install        - Build and install debug APK to connected device/emulator"
    echo "  clean          - Clean build files"
    echo "  setup-wrapper  - Set up gradle wrapper (create gradle-wrapper.jar)"
    echo "  help           - Show this help message"
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

    echo -e "${GREEN}Prerequisites check passed${NC}"
}

# Function to setup gradle wrapper
setup_wrapper() {
    echo -e "${YELLOW}Setting up Gradle wrapper...${NC}"
    
    # Check if gradle command is available
    if ! command -v gradle >/dev/null 2>&1; then
        echo -e "${RED}Error: gradle command not found.${NC}"
        echo -e "${YELLOW}Please install Gradle first, or use Android Studio which includes Gradle.${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Running: gradle wrapper --gradle-version 8.0${NC}"
    gradle wrapper --gradle-version 8.0
    
    if [ -f "gradle/wrapper/gradle-wrapper.jar" ]; then
        echo -e "${GREEN}Gradle wrapper setup successfully!${NC}"
        echo "File created: gradle/wrapper/gradle-wrapper.jar"
    else
        echo -e "${RED}Gradle wrapper setup failed - gradle-wrapper.jar was not created${NC}"
        exit 1
    fi
}

# Function to build debug APK
build_debug() {
    echo -e "${YELLOW}Building debug APK...${NC}"
    
    # Check if gradle-wrapper.jar exists
    if [ ! -f "gradle/wrapper/gradle-wrapper.jar" ]; then
        echo -e "${YELLOW}gradle-wrapper.jar not found. Attempting to set up wrapper...${NC}"
        setup_wrapper
    fi
    
    # Verify that the JAR file is actually a JAR and not a text file
    if file "gradle/wrapper/gradle-wrapper.jar" 2>/dev/null | grep -q "text"; then
        echo -e "${RED}gradle-wrapper.jar appears to be a text file, not a binary JAR.${NC}"
        echo -e "${YELLOW}This project requires a proper Gradle wrapper to build.${NC}"
        echo -e "${YELLOW}Please ensure you have a proper Android Studio/Gradle environment.${NC}"
        exit 1
    fi
    
    # Try to build with gradlew
    if ./gradlew --info assembleDebug; then
        echo -e "${GREEN}Debug APK built successfully!${NC}"
        echo "Location: app/build/outputs/apk/debug/app-debug.apk"
    else
        echo -e "${RED}Gradle build failed.${NC}"
        echo -e "${YELLOW}This may be due to Java version incompatibility or missing Android SDK.${NC}"
        echo -e "${YELLOW}Make sure you have Android SDK installed and JAVA_HOME set correctly.${NC}"
        exit 1
    fi
}

# Function to build release APK
build_release() {
    echo -e "${YELLOW}Building release APK...${NC}"
    
    # Check if gradle-wrapper.jar exists
    if [ ! -f "gradle/wrapper/gradle-wrapper.jar" ]; then
        echo -e "${YELLOW}gradle-wrapper.jar not found. Attempting to set up wrapper...${NC}"
        setup_wrapper
    fi
    
    # Verify that the JAR file is actually a JAR and not a text file
    if file "gradle/wrapper/gradle-wrapper.jar" 2>/dev/null | grep -q "text"; then
        echo -e "${RED}gradle-wrapper.jar appears to be a text file, not a binary JAR.${NC}"
        echo -e "${YELLOW}This project requires a proper Gradle wrapper to build.${NC}"
        exit 1
    fi
    
    # Try to build with gradlew
    if ./gradlew assembleRelease; then
        echo -e "${GREEN}Release APK built successfully!${NC}"
        echo "Location: app/build/outputs/apk/release/app-release.apk"
    else
        echo -e "${RED}Gradle build failed.${NC}"
        echo -e "${YELLOW}This may be due to Java version incompatibility or missing Android SDK.${NC}"
        echo -e "${YELLOW}Make sure you have Android SDK installed and JAVA_HOME set correctly.${NC}"
        exit 1
    fi
}

# Function to clean build files
clean_build() {
    echo -e "${YELLOW}Cleaning build files...${NC}"
    
    # Check if gradle-wrapper.jar exists
    if [ ! -f "gradle/wrapper/gradle-wrapper.jar" ]; then
        echo -e "${YELLOW}gradle-wrapper.jar not found. Attempting to set up wrapper...${NC}"
        setup_wrapper
    fi
    
    # Verify that the JAR file is actually a JAR and not a text file
    if file "gradle/wrapper/gradle-wrapper.jar" 2>/dev/null | grep -q "text"; then
        echo -e "${RED}gradle-wrapper.jar appears to be a text file, not a binary JAR.${NC}"
        echo -e "${YELLOW}This project requires a proper Gradle wrapper to build.${NC}"
        exit 1
    fi
    
    # Try to clean with gradlew
    if ./gradlew clean; then
        echo -e "${GREEN}Build files cleaned successfully!${NC}"
    else
        echo -e "${RED}Gradle clean failed.${NC}"
        echo -e "${YELLOW}This may be due to Java version incompatibility or missing Android SDK.${NC}"
        echo -e "${YELLOW}Make sure you have Android SDK installed and JAVA_HOME set correctly.${NC}"
        exit 1
    fi
}

# Function to install debug APK to device
install_debug() {
    echo -e "${YELLOW}Building and installing debug APK...${NC}"
    
    # Check if there's a connected device
    if ! adb devices | grep -q "device"; then
        echo -e "${RED}No connected devices found. Please connect a device or start an emulator.${NC}"
        exit 1
    fi
    
    # Check if gradle-wrapper.jar exists
    if [ ! -f "gradle/wrapper/gradle-wrapper.jar" ]; then
        echo -e "${YELLOW}gradle-wrapper.jar not found. Attempting to set up wrapper...${NC}"
        setup_wrapper
    fi
    
    # Verify that the JAR file is actually a JAR and not a text file
    if file "gradle/wrapper/gradle-wrapper.jar" 2>/dev/null | grep -q "text"; then
        echo -e "${RED}gradle-wrapper.jar appears to be a text file, not a binary JAR.${NC}"
        echo -e "${YELLOW}This project requires a proper Gradle wrapper to build.${NC}"
        exit 1
    fi
    
    # Try to install with gradlew
    if ./gradlew installDebug; then
        echo -e "${GREEN}Debug APK installed successfully!${NC}"
    else
        echo -e "${RED}Gradle install failed.${NC}"
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
    "build"|"debug")
        build_debug
        ;;
    "release")
        build_release
        ;;
    "install")
        install_debug
        ;;
    "clean")
        clean_build
        ;;
    "setup-wrapper")
        setup_wrapper
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

echo -e "${GREEN}Build completed successfully!${NC}"