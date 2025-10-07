package com.example.wuziqi;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Toast;

public class GomokuBoardView extends View {
    private static final int BOARD_SIZE = 15;
    private int CELL_SIZE = 80; // Adjusted for Android screen - not final so it can be changed dynamically

    private Paint paint;
    private int[][] board;
    private GameEngine gameEngine;
    private int boardWidth, boardHeight;
    private int boardLeft, boardTop;
    private int lastMoveRow = -1, lastMoveCol = -1;

    public GomokuBoardView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    private void init() {
        paint = new Paint();
        paint.setAntiAlias(true);
        setBackgroundColor(Color.rgb(245, 222, 179)); // Wheat color background
    }

    public void setGameEngine(GameEngine engine) {
        this.gameEngine = engine;
        this.board = engine.getBoard();
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);

        int minDimension = Math.min(w, h - 150); // Account for UI elements above
        boardWidth = (BOARD_SIZE - 1) * CELL_SIZE;
        boardHeight = (BOARD_SIZE - 1) * CELL_SIZE;

        // Adjust cell size if needed to fit the screen
        if (boardWidth > minDimension || boardHeight > minDimension) {
            float scaleX = (float) minDimension / boardWidth;
            float scaleY = (float) minDimension / boardHeight;
            float scale = Math.min(scaleX, scaleY);
            boardWidth = (int) (boardWidth * scale);
            boardHeight = (int) (boardHeight * scale);
            CELL_SIZE = boardWidth / (BOARD_SIZE - 1);
        }

        boardLeft = (w - boardWidth) / 2;
        boardTop = (h - boardHeight) / 2;
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        // Draw grid
        drawGrid(canvas);

        // Draw stones
        if (board != null) {
            drawStones(canvas);
        }
    }

    private void drawGrid(Canvas canvas) {
        paint.setColor(Color.BLACK);
        paint.setStrokeWidth(2);

        // Draw vertical lines
        for (int i = 0; i < BOARD_SIZE; i++) {
            int x = boardLeft + i * CELL_SIZE;
            canvas.drawLine(x, boardTop, x, boardTop + boardHeight, paint);
        }

        // Draw horizontal lines
        for (int i = 0; i < BOARD_SIZE; i++) {
            int y = boardTop + i * CELL_SIZE;
            canvas.drawLine(boardLeft, y, boardLeft + boardWidth, y, paint);
        }

        // Draw star points (hoshi)
        int[] starPoints = {3, 7, 11};
        paint.setColor(Color.BLACK);
        paint.setStyle(Paint.Style.FILL);
        for (int r : starPoints) {
            for (int c : starPoints) {
                int x = boardLeft + c * CELL_SIZE;
                int y = boardTop + r * CELL_SIZE;
                canvas.drawCircle(x, y, 6, paint);
            }
        }
    }

    private void drawStones(Canvas canvas) {
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (board[i][j] != 0) {
                    int x = boardLeft + j * CELL_SIZE;
                    int y = boardTop + i * CELL_SIZE;

                    // Draw stone
                    if (board[i][j] == 1) { // Player's stone (black)
                        paint.setColor(Color.BLACK);
                        paint.setStyle(Paint.Style.FILL);
                        canvas.drawCircle(x, y, CELL_SIZE / 2 - 4, paint);

                        // Draw outline
                        paint.setColor(Color.GRAY);
                        paint.setStyle(Paint.Style.STROKE);
                        paint.setStrokeWidth(2);
                        canvas.drawCircle(x, y, CELL_SIZE / 2 - 4, paint);
                    } else if (board[i][j] == 2) { // AI's stone (white)
                        paint.setColor(Color.WHITE);
                        paint.setStyle(Paint.Style.FILL);
                        canvas.drawCircle(x, y, CELL_SIZE / 2 - 4, paint);

                        // Draw outline
                        paint.setColor(Color.GRAY);
                        paint.setStyle(Paint.Style.STROKE);
                        paint.setStrokeWidth(2);
                        canvas.drawCircle(x, y, CELL_SIZE / 2 - 4, paint);
                    }

                    // Highlight last move with red circle
                    if (i == lastMoveRow && j == lastMoveCol) {
                        paint.setColor(Color.RED);
                        paint.setStyle(Paint.Style.STROKE);
                        paint.setStrokeWidth(4);
                        canvas.drawCircle(x, y, CELL_SIZE / 2 - 2, paint);
                    }
                }
            }
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (event.getAction() == MotionEvent.ACTION_DOWN) {
            float x = event.getX();
            float y = event.getY();

            // Convert touch coordinates to board coordinates
            int col = Math.round((x - boardLeft) / (float) CELL_SIZE);
            int row = Math.round((y - boardTop) / (float) CELL_SIZE);

            // Check if the coordinates are within the board
            if (row >= 0 && row < BOARD_SIZE && col >= 0 && col < BOARD_SIZE) {
                if (gameEngine != null) {
                    if (gameEngine.getCurrentPlayer() == 1 && !gameEngine.isGameOver()) { // Player's turn
                        boolean placed = gameEngine.placeStone(row, col);
                        if (!placed) {
                            // Show error message
                            Toast.makeText(getContext(), "该位置已有棋子！", Toast.LENGTH_SHORT).show();
                        }
                    }
                }
            }
            return true;
        }
        return super.onTouchEvent(event);
    }

    public void updateBoard() {
        // Get the last move from game engine
        if (gameEngine != null) {
            lastMoveRow = gameEngine.getLastMoveRow();
            lastMoveCol = gameEngine.getLastMoveCol();
        }
        invalidate(); // Redraw the board
    }
}