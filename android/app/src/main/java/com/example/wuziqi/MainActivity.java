package com.example.wuziqi;

import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {
    private GomokuBoardView gomokuBoardView;
    private GameEngine gameEngine;
    private SoundManager soundManager;
    private Handler handler;
    private Runnable timerRunnable;
    private long turnStartTime;
    private Button undoButton;
    private Button newGameButton;
    private Button settingsButton;
    private android.widget.TextView statsText;
    
    // For auto new game after game ends
    private Runnable autoNewGameRunnable;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        // 设置中文locale确保中文显示
        Locale.setDefault(Locale.SIMPLIFIED_CHINESE);
        
        gomokuBoardView = findViewById(R.id.gomokuBoard);
        undoButton = findViewById(R.id.undoButton);
        newGameButton = findViewById(R.id.newGameButton);
        settingsButton = findViewById(R.id.settingsButton);
        statsText = findViewById(R.id.statsText);
        
        gameEngine = new GameEngine(gomokuBoardView);
        
        // Initialize sound manager
        soundManager = new SoundManager(this);
        gameEngine.setSoundManager(soundManager);
        
        // Configure LLM if needed - get from config or preferences
        Config.loadConfiguration();
        gameEngine.configureLLM(Config.OPENAI_API_KEY, Config.OPENAI_BASE_URL, Config.MODEL_NAME);
        // You can set this based on a preference or configuration
        // gameEngine.setUseLLM(true); // Set to true to enable LLM AI
        
        gomokuBoardView.setGameEngine(gameEngine);

        // Set up button listeners
        setupButtonListeners();
        
        // Set up game end callback for auto new game
        gameEngine.setGameEndCallback(new GameEngine.GameEndCallback() {
            @Override
            public void onGameEnd(int winner) {
                if (gameEngine.isAutoNewGame()) {
                    // Schedule a new game after the delay
                    if (autoNewGameRunnable != null) {
                        handler.removeCallbacks(autoNewGameRunnable);
                    }
                    
                    autoNewGameRunnable = new Runnable() {
                        @Override
                        public void run() {
                            gameEngine.resetGame();
                            updateUI();
                            Toast.makeText(MainActivity.this, R.string.new_game_started, Toast.LENGTH_SHORT).show();
                        }
                    };
                    
                    handler.postDelayed(autoNewGameRunnable, gameEngine.getAutoNewGameDelay());
                }
            }
        });
        
        handler = new Handler();
        setupTimer();
        updateUI();
    }
    
    private void setupButtonListeners() {
        undoButton.setOnClickListener(v -> {
            if (gameEngine.canUndo()) {
                // Only allow undo during the player's turn (not AI's turn)
                if (gameEngine.getCurrentPlayer() == 1 && !gameEngine.isGameOver()) {
                    gameEngine.undoMove();
                    Toast.makeText(this, R.string.move_undone, Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(this, R.string.cannot_undo_now, Toast.LENGTH_SHORT).show();
                }
            } else {
                Toast.makeText(this, R.string.no_move_to_undo, Toast.LENGTH_SHORT).show();
            }
        });
        
        newGameButton.setOnClickListener(v -> {
            // Start a new game
            gameEngine.resetGame();
            updateUI();
            Toast.makeText(this, R.string.new_game_started, Toast.LENGTH_SHORT).show();
        });
        
        settingsButton.setOnClickListener(v -> {
            // Open settings activity
            android.content.Intent intent = new android.content.Intent(this, SettingsActivity.class);
            startActivity(intent);
        });
    }

    private void setupTimer() {
        timerRunnable = new Runnable() {
            @Override
            public void run() {
                updateTimer();
                if (!gameEngine.isGameOver()) {
                    handler.postDelayed(this, 1000);
                }
            }
        };
        handler.post(timerRunnable);
    }

    private void updateTimer() {
        if (gameEngine.getCurrentPlayer() != 0 && !gameEngine.isGameOver()) {
            long elapsed = (System.currentTimeMillis() - turnStartTime) / 1000;
            long remaining = Math.max(0, gameEngine.getMaxTurnTime() - elapsed);
            
            runOnUiThread(() -> {
                ((android.widget.TextView) findViewById(R.id.timerText)).setText(
                    String.format(getString(R.string.time_limit), remaining)
                );
                
                if (remaining <= 0) {
                    handleTimeOut();
                }
            });
        }
    }

    private void handleTimeOut() {
        if (gameEngine.getCurrentPlayer() == 1) {
            // Player timeout - make random move
            gameEngine.makeRandomMove();
        } else if (gameEngine.getCurrentPlayer() == 2) {
            // AI timeout - make random move
            gameEngine.makeRandomMove();
        }
        updateUI();
    }

    public void updateUI() {
        runOnUiThread(() -> {
            String turnText;
            if (gameEngine.getCurrentPlayer() == 1 && !gameEngine.isGameOver()) {
                turnText = getString(R.string.player_turn);
                turnStartTime = System.currentTimeMillis();
            } else if (gameEngine.getCurrentPlayer() == 2 && !gameEngine.isGameOver()) {
                turnText = getString(R.string.ai_turn);
                turnStartTime = System.currentTimeMillis();
                // Trigger AI move in a background thread
                new Thread(() -> gameEngine.makeAIMove()).start();
            } else {
                turnText = getString(R.string.game_over);
            }
            
            ((android.widget.TextView) findViewById(R.id.turnIndicator)).setText(turnText);
            
            // Update statistics display
            if (statsText != null) {
                statsText.setText(gameEngine.getGameStatsString());
            }
            
            // Update undo button state
            if (undoButton != null) {
                undoButton.setEnabled(gameEngine.canUndo() && 
                                     gameEngine.getCurrentPlayer() == 1 && 
                                     !gameEngine.isGameOver());
            }
        });
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (handler != null && timerRunnable != null) {
            handler.removeCallbacks(timerRunnable);
        }
        if (handler != null && autoNewGameRunnable != null) {
            handler.removeCallbacks(autoNewGameRunnable);
        }
        if (soundManager != null) {
            soundManager.release();
        }
    }
}