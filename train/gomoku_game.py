"""
Gomoku (Five in a Row) game environment for AlphaZero implementation.
"""

import numpy as np
from typing import List, Tuple, Optional


class GomokuGame:
    """
    Represents the Gomoku (Five in a Row) game environment.
    Board positions are indexed from 0 to board_size-1 for both row and column.
    Player 1 is represented as 1, Player -1 as -1, and empty as 0.
    """
    
    def __init__(self, board_size: int = 15):
        self.board_size = board_size
        self.action_size = board_size * board_size  # Each position on board is an action
    
    def get_initial_state(self) -> np.ndarray:
        """Returns the initial state of the game."""
        return np.zeros((self.board_size, self.board_size), dtype=np.int8)
    
    def get_next_state(self, board: np.ndarray, action: int, player: int) -> np.ndarray:
        """
        Returns the next state after action is taken by player.
        Action is an integer representing the position on the board (row * board_size + col).
        """
        row = action // self.board_size
        col = action % self.board_size
        
        # Validate the action
        if board[row, col] != 0:
            raise ValueError(f"Action {action} on non-empty position [{row}, {col}]")
        
        next_board = board.copy()
        next_board[row, col] = player
        return next_board
    
    def get_valid_moves(self, board: np.ndarray) -> np.ndarray:
        """
        Returns a binary array of size action_size where 1 indicates a valid move.
        """
        valid_moves = (board.reshape(-1) == 0).astype(np.uint8)
        return valid_moves
    
    def check_win(self, board: np.ndarray, action: int) -> bool:
        """
        Check if the last action resulted in a win.
        """
        if action == -1:  # No action taken yet
            return False
            
        row = action // self.board_size
        col = action % self.board_size
        player = board[row, col]
        
        if player == 0:
            return False  # No player at this position
        
        # Directions: horizontal, vertical, diagonal, anti-diagonal
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1  # The stone just placed
            
            # Check in positive direction
            r, c = row + dr, col + dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and board[r, c] == player:
                count += 1
                r, c = r + dr, c + dc
            
            # Check in negative direction
            r, c = row - dr, col - dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and board[r, c] == player:
                count += 1
                r, c = r - dr, c - dc
            
            if count >= 5:
                return True
        
        return False
    
    def get_game_ended(self, board: np.ndarray, action: int) -> float:
        """
        Returns 1 if player 1 won, -1 if player -1 won, 0 if draw, 0.0001 if game not ended.
        """
        if self.check_win(board, action):
            return float(board[action // self.board_size, action % self.board_size])
        
        # Check for draw (board full)
        if np.sum(board == 0) == 0:
            return 0  # Draw
        
        return 0.0001  # Game not ended
    
    def get_canonical_form(self, board: np.ndarray, player: int) -> np.ndarray:
        """
        Returns the canonical form of the board from the player's perspective.
        Canonical form is always from player 1's perspective.
        """
        return board * player
    
    def get_symmetries(self, board: np.ndarray, policy: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Returns all symmetries of the board and policy.
        This is used for data augmentation during training.
        """
        symmetries = []
        
        # Original
        symmetries.append((board, policy))
        
        # Rotations and reflections
        for i in range(1, 4):  # 90, 180, 270 degree rotations
            rotated_board = np.rot90(board, i)
            rotated_policy = np.rot90(policy.reshape(self.board_size, self.board_size), i).reshape(-1)
            symmetries.append((rotated_board, rotated_policy))
        
        # Horizontal flip followed by rotations
        flipped_board = np.fliplr(board)
        flipped_policy = np.fliplr(policy.reshape(self.board_size, self.board_size)).reshape(-1)
        symmetries.append((flipped_board, flipped_policy))
        
        for i in range(1, 4):
            rotated_board = np.rot90(flipped_board, i)
            rotated_policy = np.rot90(flipped_policy.reshape(self.board_size, self.board_size), i).reshape(-1)
            symmetries.append((rotated_board, rotated_policy))
        
        return symmetries
    
    def string_representation(self, board: np.ndarray) -> str:
        """
        Returns a string representation of the board for hashing.
        """
        return board.tostring()
    
    def get_action_from_string(self, row: int, col: int) -> int:
        """
        Convert row, col coordinates to action index.
        """
        return row * self.board_size + col


class GomokuLogic:
    """
    Utility functions for Gomoku game logic.
    """
    
    @staticmethod
    def print_board(board: np.ndarray):
        """
        Prints the board in a readable format.
        """
        board_size = board.shape[0]
        print("  " + " ".join([f"{i:2d}" for i in range(board_size)]))
        
        for i in range(board_size):
            row_str = f"{i:2d}"
            for j in range(board_size):
                if board[i, j] == 1:
                    row_str += " X"
                elif board[i, j] == -1:
                    row_str += " O"
                else:
                    row_str += " ."
            print(row_str)