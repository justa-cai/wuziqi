"""
Inference system for AlphaZero-style Gomoku implementation.
Allows the trained model to play games against human players or other models.
"""

import numpy as np
import torch
import os
from typing import Tuple, Optional
from gomoku_game import GomokuGame, GomokuLogic
from nnet import GomokuNNet
from mcts import MCTS, NeuralNetWrapper


class GomokuPlayer:
    """
    A player that uses the trained neural network and MCTS to make moves.
    """
    def __init__(self, nn_wrapper: NeuralNetWrapper, game: GomokuGame, num_mcts_sims: int = 50, temperature: float = 0.1):
        self.nn_wrapper = nn_wrapper
        self.game = game
        self.num_mcts_sims = num_mcts_sims
        self.temperature = temperature  # Lower temperature for more deterministic play
    
    def get_action(self, board: np.ndarray, player: int, verbose: bool = False) -> int:
        """
        Get the best action for the current player given the board state.
        
        Args:
            board: Current board state
            player: Current player (1 or -1)
            verbose: Whether to print MCTS information
            
        Returns:
            Action index (row * board_size + col)
        """
        # Create MCTS with current neural network
        mcts = MCTS(self.game, self.nn_wrapper, num_sims=self.num_mcts_sims)
        
        # Perform MCTS search
        action_probs = mcts.search(board, player)
        
        if verbose:
            print(f"MCTS visit counts: {action_probs}")
        
        # Select action based on policy distribution
        if self.temperature == 0:  # Greedy selection
            action = np.argmax(action_probs)
        else:  # Sample from distribution
            action = np.random.choice(len(action_probs), p=action_probs)
        
        return action


def play_game(player1: GomokuPlayer, player2: GomokuPlayer, game: GomokuGame, verbose: bool = True) -> float:
    """
    Play a game between two players.
    
    Returns:
        1 if player 1 wins, -1 if player 2 wins, 0 if draw
    """
    board = game.get_initial_state()
    current_player = 1  # Player 1 starts
    
    if verbose:
        print("Starting new game...")
        GomokuLogic.print_board(board)
        print()
    
    while True:
        if verbose:
            print(f"Player {current_player}'s turn")
        
        # Get the current player
        if current_player == 1:
            action = player1.get_action(board, current_player, verbose=verbose)
        else:
            action = player2.get_action(board, current_player, verbose=verbose)
        
        # Convert action to row, col
        row = action // game.board_size
        col = action % game.board_size
        
        if verbose:
            print(f"Player {current_player} selects position ({row}, {col})")
        
        # Apply the action
        board = game.get_next_state(board, action, current_player)
        
        if verbose:
            GomokuLogic.print_board(board)
            print()
        
        # Check if game ended
        result = game.get_game_ended(board, action)
        if abs(result) > 0.0001:  # Game ended
            if result == 1:
                winner = current_player
            elif result == -1:
                winner = -current_player
            else:  # Draw
                winner = 0
                
            if verbose:
                if winner == 0:
                    print("Game ended in a draw!")
                else:
                    print(f"Player {winner} wins!")
            
            return float(winner)
        
        # Switch player
        current_player *= -1


class GomokuHumanPlayer:
    """
    A human player that can interact with the game.
    """
    def __init__(self, game: GomokuGame):
        self.game = game
    
    def get_action(self, board: np.ndarray, player: int, verbose: bool = True) -> int:
        """
        Get action from human player input.
        """
        if verbose:
            print(f"Your turn (Player {player}). Current board:")
            GomokuLogic.print_board(board)
            print(f"You are {'X' if player == 1 else 'O'}")
        
        while True:
            try:
                user_input = input("Enter your move (row,col) or 'quit' to exit: ").strip()
                
                if user_input.lower() == 'quit':
                    return -1  # Special value to indicate quit
                
                row, col = map(int, user_input.split(','))
                
                if not (0 <= row < self.game.board_size and 0 <= col < self.game.board_size):
                    print(f"Invalid position! Position must be between 0 and {self.game.board_size-1}.")
                    continue
                
                # Check if the position is empty
                if board[row, col] != 0:
                    print("Position is already occupied! Choose an empty position.")
                    continue
                
                # Convert to action
                action = self.game.get_action_from_string(row, col)
                return action
            
            except ValueError:
                print("Invalid input format! Please enter row,col (e.g., 7,7)")


def load_model(model_path: str, board_size: int = 15) -> NeuralNetWrapper:
    """
    Load a trained model from the specified path.
    """
    # Create a new network with the same architecture
    nnet = GomokuNNet(board_size=board_size)
    nn_wrapper = NeuralNetWrapper(nnet)
    
    # Load the model weights
    nn_wrapper.load_checkpoint(folder=os.path.dirname(model_path), 
                              filename=os.path.basename(model_path))
    
    return nn_wrapper


def play_against_model(model_path: str, board_size: int = 15, num_mcts_sims: int = 50):
    """
    Play a game against the trained model.
    """
    # Load the trained model
    print(f"Loading model from {model_path}...")
    nn_wrapper = load_model(model_path, board_size)
    
    # Create game
    game = GomokuGame(board_size=board_size)
    
    # Create players
    human_player = GomokuHumanPlayer(game)
    ai_player = GomokuPlayer(nn_wrapper, game, num_mcts_sims, temperature=0.0)  # Deterministic play
    
    print("Starting game: Human vs AI")
    print("You are 'X' (player 1) and will play first.")
    print("Enter moves as 'row,col' (e.g., '7,7')")
    
    # Play the game
    result = play_game(human_player, ai_player, game, verbose=False)
    
    if result == 1:
        print("Congratulations! You won!")
    elif result == -1:
        print("AI wins! Better luck next time.")
    else:
        print("Game ended in a draw!")


def ai_vs_ai_demo(model_path1: str, model_path2: Optional[str] = None, board_size: int = 15):
    """
    Demo of two AI players playing against each other.
    If only one model_path is provided, the same model plays against itself.
    """
    # Load the model(s)
    print(f"Loading model 1 from {model_path1}...")
    nn_wrapper1 = load_model(model_path1, board_size)
    
    if model_path2:
        print(f"Loading model 2 from {model_path2}...")
        nn_wrapper2 = load_model(model_path2, board_size)
    else:
        print("Using the same model for both players...")
        nn_wrapper2 = nn_wrapper1
    
    # Create game
    game = GomokuGame(board_size=board_size)
    
    # Create AI players
    ai_player1 = GomokuPlayer(nn_wrapper1, game, num_mcts_sims=50, temperature=0.0)
    ai_player2 = GomokuPlayer(nn_wrapper2, game, num_mcts_sims=50, temperature=0.0)
    
    print("Starting AI vs AI game...")
    result = play_game(ai_player1, ai_player2, game, verbose=True)
    
    if result == 1:
        print("AI Player 1 (using model 1) wins!")
    elif result == -1:
        print("AI Player 2 (using model 2) wins!")
    else:
        print("Game ended in a draw!")


def test_inference():
    """
    Test the inference functionality with a small network.
    """
    print("Testing inference functionality...")
    
    # Create a small board for testing
    board_size = 6
    game = GomokuGame(board_size=board_size)
    
    # Create a random model for testing
    nnet = GomokuNNet(board_size=board_size, num_channels=32, num_res_blocks=2)
    nn_wrapper = NeuralNetWrapper(nnet)
    
    # Create AI player
    ai_player = GomokuPlayer(nn_wrapper, game, num_mcts_sims=20, temperature=0.0)  # Fewer simulations for testing speed
    
    # Test getting an action
    board = game.get_initial_state()
    action = ai_player.get_action(board, 1, verbose=True)
    print(f"Selected action: {action}")
    print(f"Action corresponds to position: ({action // board_size}, {action % board_size})")
    
    # Test a simple game between two AI players
    print("\nTesting AI vs AI game...")
    ai_player2 = GomokuPlayer(nn_wrapper, game, num_mcts_sims=20, temperature=0.0)
    result = play_game(ai_player, ai_player2, game, verbose=True)
    
    print(f"Game result: {result}")
    print("Inference test completed successfully!")


if __name__ == "__main__":
    test_inference()