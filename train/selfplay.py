"""
Self-play generation for AlphaZero-style Gomoku implementation.
Generates training data by having the neural network play against itself.
"""

import numpy as np
import random
from typing import List, Tuple
from gomoku_game import GomokuGame, GomokuLogic
from mcts import MCTS, NeuralNetWrapper
from nnet import GomokuNNet


def execute_episode(game: GomokuGame, mcts: MCTS, temperature: float = 1.0) -> Tuple[List[Tuple[np.ndarray, np.ndarray, float]], float]:
    """
    Execute one episode of self-play.
    
    Returns:
    - List of (board, policy_target, game_result) tuples
    - Final game result (1 for player 1 win, -1 for player -1 win, 0 for draw)
    """
    boards = []
    policies = []
    game_results = []
    
    board = game.get_initial_state()
    player = 1  # Player 1 starts
    
    # Store the sequence of states
    state_history = []
    
    while True:
        # Add current board to history
        state_history.append((board.copy(), player))
        
        # Get action probabilities from MCTS
        action_probs = mcts.search(board, player)
        
        # Store board and policy target
        if temperature > 0.1:  # Add exploration during early game
            # Sample action based on policy probabilities
            action = np.random.choice(len(action_probs), p=action_probs)
        else:  # Use greedy selection for final moves
            action = np.argmax(action_probs)
        
        # For training, we want to store the policy that MCTS actually computed
        boards.append(game.get_canonical_form(board, player))
        policies.append(action_probs)
        
        # Get next state
        board = game.get_next_state(board, action, player)
        
        # Check if game ended
        game_result = game.get_game_ended(board, action)
        if abs(game_result) > 0.0001:  # Game ended
            # Determine the winner from the perspective of the player who just moved
            if game_result == 1:  # Player 1 won
                result = 1 if player == 1 else -1
            elif game_result == -1:  # Player -1 won
                result = 1 if player == -1 else -1
            else:  # Draw
                result = 0
            
            # Backfill game results for all positions with the final result
            game_results = [result if i % 2 == 0 else -result for i in range(len(boards))]
            break
        
        # Switch player
        player *= -1
    
    # Create training examples: (canonical_board, policy_target, game_result)
    training_examples = []
    for i in range(len(boards)):
        canonical_board = boards[i]
        policy_target = policies[i]
        result = game_results[i]
        training_examples.append((canonical_board, policy_target, result))
    
    return training_examples, result


def generate_selfplay_games(num_games: int, 
                           game: GomokuGame, 
                           neural_net_wrapper: NeuralNetWrapper, 
                           num_mcts_sims: int = 25) -> List[Tuple[np.ndarray, np.ndarray, float]]:
    """
    Generate training data by running multiple self-play games.
    
    Returns:
    - List of (board, policy_target, game_result) tuples
    """
    training_data = []
    
    for i in range(num_games):
        print(f"Playing game {i+1}/{num_games}")
        
        # Create a new MCTS for this game
        mcts = MCTS(game, neural_net_wrapper, num_sims=num_mcts_sims)
        
        # Execute one episode
        examples, result = execute_episode(game, mcts, temperature=1.0 if i < num_games * 0.8 else 0.1)
        
        # Add symmetries to training data
        for board, policy, game_result in examples:
            # Get all symmetries of the board and policy
            sym_boards_policies = game.get_symmetries(board, policy)
            for sym_board, sym_policy in sym_boards_policies:
                training_data.append((sym_board, sym_policy, game_result))
    
    return training_data


def test_selfplay():
    """
    Test the self-play functionality.
    """
    print("Testing self-play generation...")
    
    board_size = 9  # Use smaller board for testing
    game = GomokuGame(board_size=board_size)
    
    # Create a simple neural network for testing
    nnet = GomokuNNet(board_size=board_size, num_channels=64, num_res_blocks=5)  # Smaller model for testing
    nn_wrapper = NeuralNetWrapper(nnet)
    
    # Generate a single game for testing
    training_data = generate_selfplay_games(num_games=1, 
                                           game=game, 
                                           neural_net_wrapper=nn_wrapper, 
                                           num_mcts_sims=50)  # Fewer simulations for testing speed
    
    print(f"Generated {len(training_data)} training examples")
    
    # Print first example
    if training_data:
        board, policy, result = training_data[0]
        print(f"Board shape: {board.shape}")
        print(f"Policy shape: {policy.shape}")
        print(f"Game result: {result}")
        print(f"Board example:\n{board[:, :, 0] if board.ndim == 3 else board}")


if __name__ == "__main__":
    test_selfplay()