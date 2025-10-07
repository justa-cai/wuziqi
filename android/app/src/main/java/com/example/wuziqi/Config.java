package com.example.wuziqi;

public class Config {
    // Default values - these can be overridden based on app configuration
    public static String OPENAI_API_KEY = "your-api-key";
    public static String OPENAI_BASE_URL = "https://api.openai.com/v1/chat/completions";
    public static String MODEL_NAME = "gpt-4";
    
    // Method to load configuration from a secure storage or configuration file
    public static void loadConfiguration() {
        // In a real implementation, this would load from a secure source
        // For now, we'll just use the default values
    }
}