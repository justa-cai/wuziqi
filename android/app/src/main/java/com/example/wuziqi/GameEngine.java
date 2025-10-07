package com.example.wuziqi;

import android.util.Log;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class GameEngine {
    private static final String TAG = "GameEngine";
    private static final int BOARD_SIZE = 15;
    private static final int EMPTY = 0;
    private static final int PLAYER_BLACK = 1;
    private static final int AI_WHITE = 2;
    
    private int[][] board;
    private int currentPlayer;
    private boolean gameOver;
    private int winner;
    private int lastMoveRow, lastMoveCol;
    private final GomokuBoardView boardView;
    private final Random random;
    private final int maxTurnTime = 30; // 30 seconds per turn
    
    // Interface for game end callback
    private GameEndCallback gameEndCallback;
    
    public interface GameEndCallback {
        void onGameEnd(int winner);
    }
    
    // For auto new game after game ends
    private boolean autoNewGame = true;
    private int autoNewGameDelay = 2000; // 2 seconds in milliseconds
    
    // For win/loss tracking
    private int playerWins = 0;
    private int aiWins = 0;
    private int draws = 0;
    
    // LLM configuration
    private boolean useLLM = false;
    private String openaiApiKey = "";
    private String openaiBaseUrl = "https://api.openai.com/v1/chat/completions";
    private String modelName = "gpt-4";
    private OpenAIApiClient apiClient;
    
    // Sound manager
    private SoundManager soundManager;
    
    // For undo functionality
    private final java.util.Stack<MoveRecord> moveHistory;

    public GameEngine(GomokuBoardView boardView) {
        this.boardView = boardView;
        this.random = new Random();
        this.board = new int[BOARD_SIZE][BOARD_SIZE]; // Initialize board before calling resetGame
        this.moveHistory = new java.util.Stack<>();
        resetGame();
    }
    
    // Record class to store move information for undo
    private static class MoveRecord {
        int row;
        int col;
        int player;
        int winner;
        boolean gameOver;
        int[][] boardSnapshot;
        
        MoveRecord(int row, int col, int player, int winner, boolean gameOver, int[][] board) {
            this.row = row;
            this.col = col;
            this.player = player;
            this.winner = winner;
            this.gameOver = gameOver;
            
            // Create a snapshot of the board state before the move
            this.boardSnapshot = new int[BOARD_SIZE][BOARD_SIZE];
            for (int i = 0; i < BOARD_SIZE; i++) {
                System.arraycopy(board[i], 0, this.boardSnapshot[i], 0, BOARD_SIZE);
            }
        }
    }
    
    public void setSoundManager(SoundManager soundManager) {
        this.soundManager = soundManager;
    }
    
    public void setGameEndCallback(GameEndCallback callback) {
        this.gameEndCallback = callback;
    }
    
    public void configureLLM(String apiKey, String baseUrl, String modelName) {
        this.openaiApiKey = apiKey;
        this.openaiBaseUrl = baseUrl != null ? baseUrl : "https://api.openai.com/v1/chat/completions";
        this.modelName = modelName != null ? modelName : "gpt-4";
        this.apiClient = new OpenAIApiClient(apiKey, this.openaiBaseUrl, this.modelName, this);
    }
    
    public void setUseLLM(boolean useLLM) {
        this.useLLM = useLLM;
    }
    
    public boolean isUsingLLM() {
        return useLLM;
    }

    public void resetGame() {
        // Clear the board - set all positions to EMPTY
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                board[i][j] = EMPTY;
            }
        }
        
        currentPlayer = PLAYER_BLACK; // Player goes first
        gameOver = false;
        winner = EMPTY;
        lastMoveRow = -1;
        lastMoveCol = -1;
        
        // Clear move history
        moveHistory.clear();
        
        Log.d(TAG, "Game reset");
        
        // Update the board view to reflect the cleared board
        if (boardView != null) {
            boardView.updateBoard();
        }
    }

    public boolean placeStone(int row, int col) {
        if (gameOver || board[row][col] != EMPTY) {
            return false;
        }

        // Record the move in history before making it
        MoveRecord moveRecord = new MoveRecord(lastMoveRow, lastMoveCol, currentPlayer, winner, gameOver, board);
        moveHistory.push(moveRecord);

        board[row][col] = currentPlayer;
        lastMoveRow = row;
        lastMoveCol = col;
        Log.d(TAG, "Stone placed at (" + row + ", " + col + ") by player " + currentPlayer);

        // Play place sound
        if (soundManager != null) {
            soundManager.playPlaceSound();
        }

        // Check for winner
        winner = checkWinner(row, col);
        if (winner != EMPTY) {
            gameOver = true;
            Log.d(TAG, "Game over! Winner: " + winner);
            
            // Update win/loss statistics
            if (winner == PLAYER_BLACK) {
                playerWins++;
            } else if (winner == AI_WHITE) {
                aiWins++;
            }
            
            // Play win sound
            if (soundManager != null) {
                soundManager.playWinSound();
            }
            
            // Notify game end callback
            if (gameEndCallback != null) {
                gameEndCallback.onGameEnd(winner);
            }
        } else if (isBoardFull()) {
            gameOver = true;
            Log.d(TAG, "Game over! Draw - board full");
            
            // Update draw statistics
            draws++;
            
            // Notify game end callback for draw
            if (gameEndCallback != null) {
                gameEndCallback.onGameEnd(EMPTY); // EMPTY represents a draw
            }
        } else {
            // Switch player
            currentPlayer = (currentPlayer == PLAYER_BLACK) ? AI_WHITE : PLAYER_BLACK;
        }

        boardView.updateBoard();
        ((MainActivity) boardView.getContext()).updateUI();

        return true;
    }
    
    public boolean canUndo() {
        // Can only undo if the game is not over and there are moves in history
        return !gameOver && !moveHistory.isEmpty();
    }
    
    public boolean undoMove() {
        if (!canUndo()) {
            return false;
        }
        
        // Get the last move from history
        MoveRecord lastMove = moveHistory.pop();
        
        // Restore the board state before the move
        for (int i = 0; i < BOARD_SIZE; i++) {
            System.arraycopy(lastMove.boardSnapshot[i], 0, board[i], 0, BOARD_SIZE);
        }
        
        // Restore game state
        lastMoveRow = lastMove.row;
        lastMoveCol = lastMove.col;
        currentPlayer = lastMove.player;
        winner = lastMove.winner;
        gameOver = lastMove.gameOver;
        
        Log.d(TAG, "Undo move at (" + lastMove.row + ", " + lastMove.col + ")");
        
        // Update the UI
        boardView.updateBoard();
        ((MainActivity) boardView.getContext()).updateUI();
        
        return true;
    }

    private boolean isBoardFull() {
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] == EMPTY) {
                    return false;
                }
            }
        }
        return true;
    }

    public int checkWinner(int row, int col) {
        int color = board[row][col];
        if (color == EMPTY) {
            return EMPTY;
        }

        // Check all 4 directions: horizontal, vertical, diagonal, anti-diagonal
        int[][] directions = {{0, 1}, {1, 0}, {1, 1}, {1, -1}};
        
        for (int[] dir : directions) {
            int count = 1; // Count the current stone
            
            // Check positive direction
            int r = row + dir[0], c = col + dir[1];
            while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] == color) {
                count++;
                r += dir[0];
                c += dir[1];
            }
            
            // Check negative direction
            r = row - dir[0]; c = col - dir[1];
            while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] == color) {
                count++;
                r -= dir[0];
                c -= dir[1];
            }
            
            if (count >= 5) {
                return color;
            }
        }
        
        return EMPTY;
    }

    public void makeAIMove() {
        if (gameOver || currentPlayer != AI_WHITE) {
            return;
        }

        // If using LLM, make the API call directly
        if (useLLM && apiClient != null) {
            Log.d(TAG, "Making LLM API call for AI move");
            
            OpenAIApiClient.LLMResponseCallback callback = new OpenAIApiClient.LLMResponseCallback() {
                @Override
                public void onSuccess(int row, int col) {
                    Log.d(TAG, "LLM suggests move: (" + row + ", " + col + ")");
                    android.os.Handler mainHandler = new android.os.Handler(android.os.Looper.getMainLooper());
                    mainHandler.post(() -> placeStone(row, col));
                }

                @Override
                public void onError(String error) {
                    Log.e(TAG, "LLM request failed: " + error + ", falling back to traditional AI");
                    // Fallback to traditional AI
                    int[] fallbackMove = getTraditionalAIMove();
                    if (fallbackMove != null) {
                        android.os.Handler mainHandler = new android.os.Handler(android.os.Looper.getMainLooper());
                        mainHandler.post(() -> placeStone(fallbackMove[0], fallbackMove[1]));
                    }
                }
            };
            
            // Make async API call
            apiClient.getAIMove(board, BOARD_SIZE, callback);
        } else {
            // Use traditional AI method
            int[] move = getTraditionalAIMove();
            if (move != null) {
                android.os.Handler mainHandler = new android.os.Handler(android.os.Looper.getMainLooper());
                mainHandler.post(() -> placeStone(move[0], move[1]));
            }
        }
    }

    private int[] aiMove() {
        // If LLM is enabled, try using it first
        if (useLLM && apiClient != null) {
            Log.d(TAG, "Using LLM for AI move decision");
            
            // For now, we'll use the traditional method as fallback
            // In a complete implementation, we would make an async API call
            OpenAIApiClient.LLMResponseCallback callback = new OpenAIApiClient.LLMResponseCallback() {
                @Override
                public void onSuccess(int row, int col) {
                    Log.d(TAG, "LLM suggests move: (" + row + ", " + col + ")");
                    android.os.Handler mainHandler = new android.os.Handler(android.os.Looper.getMainLooper());
                    mainHandler.post(() -> placeStone(row, col));
                }

                @Override
                public void onError(String error) {
                    Log.e(TAG, "LLM request failed: " + error + ", falling back to traditional AI");
                    // Fallback to traditional AI
                    int[] fallbackMove = getTraditionalAIMove();
                    if (fallbackMove != null) {
                        android.os.Handler mainHandler = new android.os.Handler(android.os.Looper.getMainLooper());
                        mainHandler.post(() -> placeStone(fallbackMove[0], fallbackMove[1]));
                    }
                }
            };
            
            // Make async API call
            apiClient.getAIMove(board, BOARD_SIZE, callback);
            
            // For now, return a traditional move as the main thread needs an immediate response
            // In a real implementation, we would need to wait for the API response or handle it differently
            return getTraditionalAIMove();
        } else {
            // Use traditional AI methods
            return getTraditionalAIMove();
        }
    }
    
    // Traditional AI logic in a separate method
    private int[] getTraditionalAIMove() {
        // 1. Check if AI can win immediately
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] == EMPTY) {
                    board[i][j] = AI_WHITE;
                    if (checkWinner(i, j) == AI_WHITE) {
                        board[i][j] = EMPTY; // Restore
                        Log.d(TAG, "AI found immediate win at (" + i + ", " + j + ")");
                        return new int[]{i, j};
                    }
                    board[i][j] = EMPTY; // Restore
                }
            }
        }

        // 2. Check if player can win next move (block)
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] == EMPTY) {
                    board[i][j] = PLAYER_BLACK;
                    if (checkWinner(i, j) == PLAYER_BLACK) {
                        board[i][j] = EMPTY; // Restore
                        Log.d(TAG, "AI blocking player win at (" + i + ", " + j + ")");
                        return new int[]{i, j};
                    }
                    board[i][j] = EMPTY; // Restore
                }
            }
        }

        // 3. Look for live four opportunities
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] == EMPTY) {
                    if (hasLiveFour(i, j, AI_WHITE)) {
                        Log.d(TAG, "AI found live four at (" + i + ", " + j + ")");
                        return new int[]{i, j};
                    }
                }
            }
        }

        // 4. Block player's live four
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] == EMPTY) {
                    if (hasLiveFour(i, j, PLAYER_BLACK)) {
                        Log.d(TAG, "AI blocking player's live four at (" + i + ", " + j + ")");
                        return new int[]{i, j};
                    }
                }
            }
        }

        // 5. Look for live three opportunities
        List<int[]> liveThreeMoves = detectLiveThree(AI_WHITE);
        if (!liveThreeMoves.isEmpty()) {
            Log.d(TAG, "AI found live three at some positions");
            // Choose the best one based on evaluation
            return evaluateBestMove(liveThreeMoves, AI_WHITE);
        }

        // 6. Block player's live three
        List<int[]> playerLiveThreeMoves = detectLiveThree(PLAYER_BLACK);
        if (!playerLiveThreeMoves.isEmpty()) {
            Log.d(TAG, "AI blocking player's live three at some positions");
            return evaluateBestMove(playerLiveThreeMoves, PLAYER_BLACK);
        }

        // 7. Use strategic fallback (alpha-beta search or evaluation)
        int[] strategicResult = strategicFallback();
        if (strategicResult != null && strategicResult[1] != -1 && strategicResult[2] != -1) {
            // The alpha-beta search returns [score, row, col]
            return new int[]{strategicResult[1], strategicResult[2]};
        } else if (strategicResult != null) {
            // Fallback to simple evaluation if alpha-beta didn't return a valid move
            int bestScore = Integer.MIN_VALUE;
            int[] bestMove = null;

            for (int i = 0; i < BOARD_SIZE; i++) {
                for (int j = 0; j < BOARD_SIZE; j++) {
                    if (board[i][j] == EMPTY) {
                        // Evaluate this position for AI (offense) and also block player (defense)
                        int aiScore = evaluatePosition(i, j, AI_WHITE);
                        int blockScore = evaluatePosition(i, j, PLAYER_BLACK);
                        int totalScore = aiScore + blockScore * 12 / 10; // Slightly favor blocking

                        if (totalScore > bestScore) {
                            bestScore = totalScore;
                            bestMove = new int[]{i, j};
                        }
                    }
                }
            }
            
            if (bestMove != null) {
                return bestMove;
            }
        }

        // 8. Fallback to random move if all else fails
        Log.d(TAG, "All strategies failed, using random move");
        return getRandomMove();
    }

    private boolean hasLiveFour(int row, int col, int player) {
        // Check if placing at (row, col) creates a live four for the specified player
        board[row][col] = player;
        boolean hasThreat = hasThreat(board, player);
        board[row][col] = EMPTY; // Restore
        return hasThreat;
    }

    private List<int[]> detectLiveThree(int player) {
        List<int[]> threats = new ArrayList<>();
        int[][] directions = {{1, 0}, {0, 1}, {1, 1}, {1, -1}};

        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] == EMPTY) {
                    for (int[] dir : directions) {
                        int count = 1; // The potential stone
                        int blocked = 0;

                        // Check positive direction
                        int r = i + dir[0], c = j + dir[1];
                        while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] == player) {
                            count++;
                            r += dir[0];
                            c += dir[1];
                        }
                        if (r < 0 || r >= BOARD_SIZE || c < 0 || c >= BOARD_SIZE || board[r][c] != EMPTY) {
                            blocked++;
                        }

                        // Check negative direction
                        r = i - dir[0]; c = j - dir[1];
                        while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] == player) {
                            count++;
                            r -= dir[0];
                            c -= dir[1];
                        }
                        if (r < 0 || r >= BOARD_SIZE || c < 0 || c >= BOARD_SIZE || board[r][c] != EMPTY) {
                            blocked++;
                        }

                        if (count == 3 && blocked == 0) { // Live three
                            threats.add(new int[]{i, j});
                        }
                    }
                }
            }
        }

        return threats;
    }

    private int[] evaluateBestMove(List<int[]> moves, int player) {
        int[] bestMove = null;
        int bestScore = Integer.MIN_VALUE;

        for (int[] move : moves) {
            int score = evaluatePosition(move[0], move[1], player);
            if (score > bestScore) {
                bestScore = score;
                bestMove = move;
            }
        }

        return bestMove;
    }

    private int evaluatePosition(int r, int c, int player) {
        if (r < 0 || r >= BOARD_SIZE || c < 0 || c >= BOARD_SIZE || board[r][c] != EMPTY) {
            return 0;
        }

        int score = 0;
        int[][] directions = {{1, 0}, {0, 1}, {1, 1}, {1, -1}};
        int opponent = (player == PLAYER_BLACK) ? AI_WHITE : PLAYER_BLACK;

        for (int[] dir : directions) {
            int ownChain = 0;
            int blockCount = 0;

            // Positive direction
            int x = r + dir[0], y = c + dir[1];
            while (x >= 0 && x < BOARD_SIZE && y >= 0 && y < BOARD_SIZE && board[x][y] == player) {
                ownChain++;
                x += dir[0];
                y += dir[1];
            }
            if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE || board[x][y] != EMPTY) {
                blockCount++;
            }

            // Negative direction
            x = r - dir[0]; y = c - dir[1];
            while (x >= 0 && x < BOARD_SIZE && y >= 0 && y < BOARD_SIZE && board[x][y] == player) {
                ownChain++;
                x -= dir[0];
                y -= dir[1];
            }
            if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE || board[x][y] != EMPTY) {
                blockCount++;
            }

            int length = ownChain + 1;
            if (blockCount == 2) {
                // Both sides blocked - no value
            } else if (blockCount == 1) {
                // One side blocked
                if (length >= 5) score += 100000; // Five in a row
                else if (length == 4) score += 10000; // Four blocked
                else if (length == 3) score += 1000; // Three blocked
                else if (length == 2) score += 100; // Two blocked
            } else {
                // Not blocked
                if (length >= 5) score += 1000000; // Five in a row
                else if (length == 4) score += 100000; // Live four
                else if (length == 3) score += 10000; // Live three
                else if (length == 2) score += 1000; // Live two
            }
        }

        return score;
    }

    private boolean hasThreat(int[][] board, int player) {
        // Check for 4 stones in a row (not necessarily live)
        int[][] directions = {{1, 0}, {0, 1}, {1, 1}, {1, -1}};

        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] == player) {
                    for (int[] dir : directions) {
                        int count = 1;
                        int r = i + dir[0], c = j + dir[1];
                        
                        while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] == player) {
                            count++;
                            r += dir[0];
                            c += dir[1];
                        }
                        
                        r = i - dir[0]; c = j - dir[1];
                        while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] == player) {
                            count++;
                            r -= dir[0];
                            c -= dir[1];
                        }
                        
                        if (count == 4) {
                            return true;
                        }
                    }
                }
            }
        }
        return false;
    }

    private int[] strategicFallback() {
        // Use alpha-beta search for better strategy
        int[] bestMove = alphaBetaSearch(2, Integer.MIN_VALUE, Integer.MAX_VALUE, true);
        
        if (bestMove != null) {
            return bestMove;
        }
        
        // Fallback to simple evaluation
        int bestScore = Integer.MIN_VALUE;
        bestMove = null;

        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] == EMPTY) {
                    // Evaluate this position for AI (offense) and also block player (defense)
                    int aiScore = evaluatePosition(i, j, AI_WHITE);
                    int blockScore = evaluatePosition(i, j, PLAYER_BLACK);
                    int totalScore = aiScore + blockScore * 12 / 10; // Slightly favor blocking

                    if (totalScore > bestScore) {
                        bestScore = totalScore;
                        bestMove = new int[]{i, j};
                    }
                }
            }
        }

        return bestMove;
    }
    
    private int[] alphaBetaSearch(int depth, int alpha, int beta, boolean maximizingPlayer) {
        // Check if game is over or max depth reached
        int winner = getWinner();
        if (depth == 0 || winner != EMPTY || isBoardFull()) {
            if (winner == AI_WHITE) {
                return new int[]{Integer.MAX_VALUE, -1, -1}; // Return score, row, col
            } else if (winner == PLAYER_BLACK) {
                return new int[]{Integer.MIN_VALUE, -1, -1};
            } else {
                // Return the evaluation score and a dummy position
                return new int[]{evaluateBoard(), -1, -1};
            }
        }

        // Get potential moves
        int[][] moves = getValidMoves();
        int bestRow = -1, bestCol = -1;

        if (maximizingPlayer) { // AI's turn (maximizing)
            int maxEval = Integer.MIN_VALUE;

            for (int[] move : moves) {
                int r = move[0], c = move[1];
                board[r][c] = AI_WHITE;

                int[] result = alphaBetaSearch(depth - 1, alpha, beta, false);
                int eval = result[0];

                board[r][c] = EMPTY; // Undo move

                if (eval > maxEval) {
                    maxEval = eval;
                    bestRow = r;
                    bestCol = c;
                }

                alpha = Math.max(alpha, eval);
                if (beta <= alpha) { // Alpha-beta pruning
                    break;
                }
            }

            return new int[]{maxEval, bestRow, bestCol};
        } else { // Player's turn (minimizing)
            int minEval = Integer.MAX_VALUE;

            for (int[] move : moves) {
                int r = move[0], c = move[1];
                board[r][c] = PLAYER_BLACK;

                int[] result = alphaBetaSearch(depth - 1, alpha, beta, true);
                int eval = result[0];

                board[r][c] = EMPTY; // Undo move

                if (eval < minEval) {
                    minEval = eval;
                    bestRow = r;
                    bestCol = c;
                }

                beta = Math.min(beta, eval);
                if (beta <= alpha) { // Alpha-beta pruning
                    break;
                }
            }

            return new int[]{minEval, bestRow, bestCol};
        }
    }

    private int evaluateBoard() {
        int totalScore = 0;
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] != EMPTY) {
                    int positionScore = 0;
                    int[][] directions = {{1, 0}, {0, 1}, {1, 1}, {1, -1}};
                    int player = board[i][j];
                    
                    for (int[] dir : directions) {
                        int chain = 1; // Current stone
                        int blockCount = 0;
                        
                        // Positive direction
                        int r = i + dir[0], c = j + dir[1];
                        while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] == player) {
                            chain++;
                            r += dir[0];
                            c += dir[1];
                        }
                        if (r < 0 || r >= BOARD_SIZE || c < 0 || c >= BOARD_SIZE || board[r][c] != EMPTY) {
                            blockCount++;
                        }
                        
                        // Negative direction
                        r = i - dir[0]; c = j - dir[1];
                        while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] == player) {
                            chain++;
                            r -= dir[0];
                            c -= dir[1];
                        }
                        if (r < 0 || r >= BOARD_SIZE || c < 0 || c >= BOARD_SIZE || board[r][c] != EMPTY) {
                            blockCount++;
                        }
                        
                        // Score based on chain and block count
                        if (blockCount == 2) {
                            // Both sides blocked - no value
                        } else if (blockCount == 1) {
                            // Single side blocked
                            if (chain >= 5) positionScore += 1000000; // Five in a row
                            else if (chain == 4) positionScore += 10000; // Blocked four
                            else if (chain == 3) positionScore += 1000; // Blocked three
                            else if (chain == 2) positionScore += 100; // Blocked two
                        } else {
                            // Not blocked
                            if (chain >= 5) positionScore += 1000000; // Five in a row
                            else if (chain == 4) positionScore += 100000; // Live four
                            else if (chain == 3) positionScore += 10000; // Live three
                            else if (chain == 2) positionScore += 1000; // Live two
                        }
                    }
                    
                    // Add to total score
                    if (player == AI_WHITE) {
                        totalScore += positionScore;
                    } else {
                        totalScore -= positionScore;
                    }
                }
            }
        }
        return totalScore;
    }

    private int[][] getValidMoves() {
        java.util.List<int[]> movesList = new java.util.ArrayList<>();
        
        // First find all occupied positions
        java.util.List<int[]> occupied = new java.util.ArrayList<>();
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] != EMPTY) {
                    occupied.add(new int[]{i, j});
                }
            }
        }
        
        // Add adjacent empty positions
        int[][] directions = {{-1,-1}, {-1,0}, {-1,1}, {0,-1}, {0,1}, {1,-1}, {1,0}, {1,1}};
        java.util.Set<String> candidates = new java.util.HashSet<>();
        
        for (int[] pos : occupied) {
            int r = pos[0], c = pos[1];
            for (int[] dir : directions) {
                int nr = r + dir[0], nc = c + dir[1];
                if (nr >= 0 && nr < BOARD_SIZE && nc >= 0 && nc < BOARD_SIZE && board[nr][nc] == EMPTY) {
                    candidates.add(nr + "," + nc);
                }
            }
        }
        
        // If no adjacent positions, use center area
        if (candidates.isEmpty()) {
            int center = BOARD_SIZE / 2;
            for (int i = Math.max(0, center-2); i < Math.min(BOARD_SIZE, center+3); i++) {
                for (int j = Math.max(0, center-2); j < Math.min(BOARD_SIZE, center+3); j++) {
                    if (board[i][j] == EMPTY) {
                        candidates.add(i + "," + j);
                    }
                }
            }
        }
        
        // If board is still empty, use center
        if (candidates.isEmpty()) {
            candidates.add((BOARD_SIZE/2) + "," + (BOARD_SIZE/2));
        }
        
        // Convert to array and sort by distance to center
        int center = BOARD_SIZE / 2;
        java.util.List<int[]> moves = new java.util.ArrayList<>();
        for (String coord : candidates) {
            String[] parts = coord.split(",");
            int r = Integer.parseInt(parts[0]);
            int c = Integer.parseInt(parts[1]);
            moves.add(new int[]{r, c});
        }
        
        // Sort by distance to center
        moves.sort((a, b) -> {
            int distA = Math.abs(a[0] - center) + Math.abs(a[1] - center);
            int distB = Math.abs(b[0] - center) + Math.abs(b[1] - center);
            return Integer.compare(distA, distB);
        });
        
        return moves.toArray(new int[0][0]);
    }

    private int[] getRandomMove() {
        List<int[]> emptyCells = new ArrayList<>();
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] == EMPTY) {
                    emptyCells.add(new int[]{i, j});
                }
            }
        }

        if (!emptyCells.isEmpty()) {
            int[] move = emptyCells.get(random.nextInt(emptyCells.size()));
            Log.d(TAG, "Using random move at (" + move[0] + ", " + move[1] + ")");
            return move;
        }

        return null;
    }

    public void makeRandomMove() {
        int[] move = getRandomMove();
        if (move != null) {
            placeStone(move[0], move[1]);
        }
    }

    // Getters
    public int getCurrentPlayer() {
        return currentPlayer;
    }

    public boolean isGameOver() {
        return gameOver;
    }

    public int getWinner() {
        return winner;
    }

    public int[][] getBoard() {
        return board;
    }

    public int getLastMoveRow() {
        return lastMoveRow;
    }

    public int getLastMoveCol() {
        return lastMoveCol;
    }

    public int getMaxTurnTime() {
        return maxTurnTime;
    }

    public int getBoardSize() {
        return BOARD_SIZE;
    }
    
    public void setAutoNewGame(boolean autoNewGame) {
        this.autoNewGame = autoNewGame;
    }
    
    public boolean isAutoNewGame() {
        return autoNewGame;
    }
    
    public void setAutoNewGameDelay(int delayMs) {
        this.autoNewGameDelay = delayMs;
    }
    
    public int getAutoNewGameDelay() {
        return autoNewGameDelay;
    }
    
    // Win/Loss tracking methods
    public int getPlayerWins() {
        return playerWins;
    }
    
    public int getAIWins() {
        return aiWins;
    }
    
    public int getDraws() {
        return draws;
    }
    
    public void resetStatistics() {
        playerWins = 0;
        aiWins = 0;
        draws = 0;
    }
    
    public String getGameStatsString() {
        return String.format("玩家: %d 胜, AI: %d 胜, 平局: %d", playerWins, aiWins, draws);
    }

}