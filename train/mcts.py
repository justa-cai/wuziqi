"""
Monte Carlo Tree Search (MCTS) for AlphaZero-style Gomoku implementation.
"""

import numpy as np
import math
import torch
from typing import Dict, List, Tuple
from collections import defaultdict
from gomoku_game import GomokuGame


class MCTSNode:
    """
    Node in the MCTS tree.
    """
    def __init__(self, board: np.ndarray, parent=None, action_taken=None, player: int = 1):
        self.board = board
        self.parent = parent
        self.action_taken = action_taken
        self.player = player  # The player who made the move that led to this node
        
        self.children = []  # List of child nodes
        self.is_expanded = False
        
        # Statistics for this node
        self.visit_count = 0
        self.total_value = 0.0
        self.action_probs = np.zeros(self.board.shape[0] ** 2)  # Probabilities from neural net
        
    def expand(self, action_probs: np.ndarray):
        """
        Expand this node by adding children for each valid action.
        action_probs: output from neural network's policy head (after softmax)
        """
        valid_moves = (self.board.reshape(-1) == 0).astype(np.uint8)
        masked_probs = action_probs * valid_moves  # Mask invalid moves
        total = np.sum(masked_probs)
        
        if total > 0:
            masked_probs /= total  # Normalize
        else:
            # If all valid moves had zero probability, make them equal
            masked_probs = valid_moves / np.sum(valid_moves)
        
        self.action_probs = masked_probs
        
        # Create child nodes for valid moves
        for action in range(len(masked_probs)):
            if masked_probs[action] > 0:
                new_board = self.board.copy()
                row, col = action // self.board.shape[0], action % self.board.shape[0]
                
                if new_board[row, col] == 0:  # Valid move
                    # Apply the move to get the next board state
                    new_game = GomokuGame(self.board.shape[0])
                    next_board = new_game.get_next_state(new_board, action, self.player)
                    child_node = MCTSNode(next_board, parent=self, action_taken=action, player=-self.player)
                    self.children.append(child_node)
        
        self.is_expanded = True
    
    def get_value(self) -> float:
        """
        Get average value for this node.
        """
        if self.visit_count == 0:
            return 0
        return self.total_value / self.visit_count
    
    def is_terminal(self) -> bool:
        """
        Check if this node is terminal (game over).
        """
        game = GomokuGame(self.board.shape[0])
        # Check if any action led to this state resulted in a win
        if self.action_taken is not None:
            return abs(game.get_game_ended(self.board, self.action_taken)) > 0.0001
        # If no action taken (root node), no win possible yet
        return False
    
    def ucb_score(self, child: 'MCTSNode', exploration_param: float = 2.0) -> float:
        """
        Calculate UCB score for selecting child node.
        """
        if child.visit_count == 0:
            # Give unvisited nodes an infinite UCB score
            return float('inf')
        
        # Calculate exploitation term (average value from this child's perspective)
        # Since we're always calculating from current player's perspective,
        # we need to consider the value from the opponent's perspective at the child level
        exploitation = -child.get_value()  # Negative because value is from opponent's perspective
        
        # Calculate exploration term
        exploration = exploration_param * child.action_probs[child.action_taken] * \
                     math.sqrt(self.visit_count) / (child.visit_count + 1)
        
        return exploitation + exploration


class MCTS:
    """
    Monte Carlo Tree Search algorithm for Gomoku.
    """
    def __init__(self, game: GomokuGame, neural_net, num_sims: int = 25):
        self.game = game
        self.neural_net = neural_net
        self.num_sims = num_sims  # Number of simulations per search
        
    def search(self, board: np.ndarray, player: int) -> np.ndarray:
        """
        Perform MCTS and return visit count distribution for the root node.
        """
        # Create root node
        root = MCTSNode(board, player=player)
        
        # Get policy and value from neural network for root
        canonical_board = self.game.get_canonical_form(board, player)
        board_input = canonical_board[np.newaxis, np.newaxis, :, :].astype(np.float32)
        policy, value = self.neural_net.predict(board_input)
        policy = policy[0]
        value = value[0]
        
        # Apply softmax to policy to get probabilities
        valid_moves = (board.reshape(-1) == 0).astype(np.float32)
        masked_policy = policy - (1 - valid_moves) * 1e8  # Mask invalid moves
        exp_policy = np.exp(masked_policy)
        action_probs = exp_policy / np.sum(exp_policy)
        
        root.expand(action_probs)
        
        for _ in range(self.num_sims):
            node = root
            search_path = [node]
            
            # Select
            while node.is_expanded and not node.is_terminal():
                # Select child with highest UCB score
                ucb_scores = [node.ucb_score(child) for child in node.children]
                best_child_idx = np.argmax(ucb_scores)
                node = node.children[best_child_idx]
                search_path.append(node)
            
            # Check if terminal
            if not node.is_terminal():
                # Get value from neural network
                canonical_board = self.game.get_canonical_form(node.board, node.player)
                board_input = canonical_board[np.newaxis, np.newaxis, :, :].astype(np.float32)
                policy, value = self.neural_net.predict(board_input)
                policy = policy[0]
                value = value[0]
                
                # Expand if not terminal
                valid_moves = (node.board.reshape(-1) == 0).astype(np.float32)
                masked_policy = policy - (1 - valid_moves) * 1e8  # Mask invalid moves
                exp_policy = np.exp(masked_policy)
                action_probs = exp_policy / np.sum(exp_policy)
                
                node.expand(action_probs)
            else:
                # Terminal node - get game result
                if node.action_taken is not None:
                    game_result = self.game.get_game_ended(node.board, node.action_taken)
                    value = game_result
                else:
                    value = 0  # This shouldn't happen in practice
            
            # Backpropagate
            for path_node in search_path:
                path_node.visit_count += 1
                # Add value from the perspective of the player who made the move in that node
                # Note: path_node.player is the player who made the move to reach path_node.board
                if path_node.player == player:  # Current player's turn at this node
                    path_node.total_value += value
                else:  # Opponent's turn at this node
                    path_node.total_value += -value  # Value is negative from opponent's perspective
        
        # Return visit count distribution
        visit_counts = np.zeros(self.game.action_size)
        for child in root.children:
            visit_counts[child.action_taken] = child.visit_count
        
        # Apply temperature for exploration (temperature=1 for normal distribution)
        # In self-play, we might want to use temperature > 0 for exploration
        # For final move selection, we might want temperature approaching 0
        temperature = 1.0  # This can be adjusted
        if temperature == 0:
            # Greedy selection
            best_action = np.argmax(visit_counts)
            action_probs = np.zeros_like(visit_counts)
            action_probs[best_action] = 1.0
        else:
            # Apply temperature and normalize
            visit_counts_power = visit_counts ** (1.0 / temperature)
            action_probs = visit_counts_power / np.sum(visit_counts_power)
        
        return action_probs


class NeuralNetWrapper:
    """
    Wrapper for neural network to interface with MCTS.
    """
    def __init__(self, model):
        self.model = model
    
    def predict(self, board: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict policy and value for a given board state.
        board: (batch_size, 1, board_size, board_size)
        Returns: (policy, value), where each is a numpy array
        """
        import torch
        
        # Convert numpy array to PyTorch tensor
        board_tensor = torch.FloatTensor(board)
        
        # Set model to evaluation mode
        self.model.eval()
        
        with torch.no_grad():
            policy_logits, value = self.model(board_tensor)
            
            # Convert back to numpy
            policy = policy_logits.cpu().numpy()
            value = value.cpu().numpy()
        
        return policy, value
    
    def save_checkpoint(self, folder: str, filename: str):
        """
        Save the model checkpoint.
        """
        import os
        filepath = os.path.join(folder, filename)
        torch.save(self.model.state_dict(), filepath)
    
    def load_checkpoint(self, folder: str, filename: str):
        """
        Load the model checkpoint.
        """
        filepath = os.path.join(folder, filename)
        self.model.load_state_dict(torch.load(filepath))