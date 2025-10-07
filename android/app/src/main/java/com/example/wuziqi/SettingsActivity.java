package com.example.wuziqi;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;

public class SettingsActivity extends AppCompatActivity {
    
    private Spinner boardSizeSpinner;
    private EditText timeLimitEditText;
    private CheckBox autoNewGameCheckBox;
    private EditText autoNewGameDelayEditText;
    private CheckBox llmCheckBox;
    private Button saveSettingsButton;
    private Button defaultSettingsButton;
    
    private static final String PREFS_NAME = "GomokuPrefs";
    private static final String KEY_BOARD_SIZE = "board_size";
    private static final String KEY_TIME_LIMIT = "time_limit";
    private static final String KEY_AUTO_NEW_GAME = "auto_new_game";
    private static final String KEY_AUTO_NEW_GAME_DELAY = "auto_new_game_delay";
    private static final String KEY_LLM_ENABLED = "llm_enabled";
    
    // Default values
    private static final int DEFAULT_BOARD_SIZE = 15;
    private static final int DEFAULT_TIME_LIMIT = 30;
    private static final boolean DEFAULT_AUTO_NEW_GAME = true;
    private static final int DEFAULT_AUTO_NEW_GAME_DELAY = 2;
    private static final boolean DEFAULT_LLM_ENABLED = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);

        initViews();
        loadCurrentSettings();
        setupListeners();
    }

    private void initViews() {
        boardSizeSpinner = findViewById(R.id.boardSizeSpinner);
        timeLimitEditText = findViewById(R.id.timeLimitEditText);
        autoNewGameCheckBox = findViewById(R.id.autoNewGameCheckBox);
        autoNewGameDelayEditText = findViewById(R.id.autoNewGameDelayEditText);
        llmCheckBox = findViewById(R.id.llmCheckBox);
        saveSettingsButton = findViewById(R.id.saveSettingsButton);
        defaultSettingsButton = findViewById(R.id.defaultSettingsButton);

        // Set up board size spinner with recommended size based on screen density
        String[] boardSizes = {"9x9", "13x13", "15x15", "19x19"};
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, boardSizes);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        boardSizeSpinner.setAdapter(adapter);
        
        // Set recommended board size based on screen density
        int recommendedSizeIndex = getRecommendedBoardSizeIndex();
        boardSizeSpinner.setSelection(recommendedSizeIndex);
    }
    
    private int getRecommendedBoardSizeIndex() {
        // Get screen density information
        float density = getResources().getDisplayMetrics().density;
        int screenHeight = getResources().getDisplayMetrics().heightPixels;
        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        
        // Calculate the approximate available space for the board
        // Considering UI elements, we'll assume ~80% of screen height is available
        int availableSpace = Math.min(screenHeight, screenWidth) * 80 / 100;
        
        // Calculate approximate cell size for each board size
        // With 9x9: availableSpace / 9, 13x13: availableSpace / 13, etc.
        if (availableSpace / 19 > 30) {
            return 3; // 19x19 for high density
        } else if (availableSpace / 15 > 35) {
            return 2; // 15x15 for medium density
        } else if (availableSpace / 13 > 40) {
            return 1; // 13x13 for lower density
        } else {
            return 0; // 9x9 for lowest density
        }
    }

    private void loadCurrentSettings() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        
        int boardSize = prefs.getInt(KEY_BOARD_SIZE, DEFAULT_BOARD_SIZE);
        // Set spinner selection based on board size
        switch (boardSize) {
            case 9:
                boardSizeSpinner.setSelection(0);
                break;
            case 13:
                boardSizeSpinner.setSelection(1);
                break;
            case 15:
                boardSizeSpinner.setSelection(2);
                break;
            case 19:
                boardSizeSpinner.setSelection(3);
                break;
            default:
                boardSizeSpinner.setSelection(2); // Default to 15x15
        }
        
        int timeLimit = prefs.getInt(KEY_TIME_LIMIT, DEFAULT_TIME_LIMIT);
        timeLimitEditText.setText(String.valueOf(timeLimit));
        
        boolean autoNewGame = prefs.getBoolean(KEY_AUTO_NEW_GAME, DEFAULT_AUTO_NEW_GAME);
        autoNewGameCheckBox.setChecked(autoNewGame);
        
        int autoNewGameDelay = prefs.getInt(KEY_AUTO_NEW_GAME_DELAY, DEFAULT_AUTO_NEW_GAME_DELAY);
        autoNewGameDelayEditText.setText(String.valueOf(autoNewGameDelay));
        
        boolean llmEnabled = prefs.getBoolean(KEY_LLM_ENABLED, DEFAULT_LLM_ENABLED);
        llmCheckBox.setChecked(llmEnabled);
    }

    private void setupListeners() {
        saveSettingsButton.setOnClickListener(v -> saveSettings());
        defaultSettingsButton.setOnClickListener(v -> resetToDefaults());
    }

    private void resetToDefaults() {
        boardSizeSpinner.setSelection(2); // Default to 15x15
        timeLimitEditText.setText(String.valueOf(DEFAULT_TIME_LIMIT));
        autoNewGameCheckBox.setChecked(DEFAULT_AUTO_NEW_GAME);
        autoNewGameDelayEditText.setText(String.valueOf(DEFAULT_AUTO_NEW_GAME_DELAY));
        llmCheckBox.setChecked(DEFAULT_LLM_ENABLED);
    }

    private void saveSettings() {
        // Validate inputs
        String timeLimitStr = timeLimitEditText.getText().toString();
        String autoNewGameDelayStr = autoNewGameDelayEditText.getText().toString();

        if (timeLimitStr.isEmpty()) {
            timeLimitEditText.setError("请输入时间限制");
            return;
        }

        if (autoNewGameDelayStr.isEmpty()) {
            autoNewGameDelayEditText.setError("请输入延迟时间");
            return;
        }

        int timeLimit;
        int autoNewGameDelay;
        
        try {
            timeLimit = Integer.parseInt(timeLimitStr);
            autoNewGameDelay = Integer.parseInt(autoNewGameDelayStr);
        } catch (NumberFormatException e) {
            Toast.makeText(this, "请输入有效的数字", Toast.LENGTH_SHORT).show();
            return;
        }

        if (timeLimit <= 0) {
            timeLimitEditText.setError("时间限制必须大于0");
            return;
        }

        if (autoNewGameDelay <= 0) {
            autoNewGameDelayEditText.setError("延迟时间必须大于0");
            return;
        }

        // Save to SharedPreferences
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        SharedPreferences.Editor editor = prefs.edit();
        
        // Get board size from spinner
        int boardSize;
        switch (boardSizeSpinner.getSelectedItemPosition()) {
            case 0: boardSize = 9; break;
            case 1: boardSize = 13; break;
            case 2: boardSize = 15; break;
            case 3: boardSize = 19; break;
            default: boardSize = 15; // default to 15
        }
        
        editor.putInt(KEY_BOARD_SIZE, boardSize);
        editor.putInt(KEY_TIME_LIMIT, timeLimit);
        editor.putBoolean(KEY_AUTO_NEW_GAME, autoNewGameCheckBox.isChecked());
        editor.putInt(KEY_AUTO_NEW_GAME_DELAY, autoNewGameDelay);
        editor.putBoolean(KEY_LLM_ENABLED, llmCheckBox.isChecked());
        editor.apply();

        // Inform user that board size change requires app restart
        if (boardSize != 15) { // if not default size
            Toast.makeText(this, R.string.board_size_restart_message, Toast.LENGTH_LONG).show();
        } else {
            Toast.makeText(this, "设置已保存", Toast.LENGTH_SHORT).show();
        }
        finish();
    }
}