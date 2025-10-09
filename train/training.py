"""
Training loop for AlphaZero-style Gomoku implementation.
Trains the neural network using self-play data.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from typing import List, Tuple
import os
import time
from gomoku_game import GomokuGame
from nnet import GomokuNNet
from mcts import NeuralNetWrapper
from selfplay import generate_selfplay_games


class GomokuTrainer:
    """
    Trainer for the Gomoku neural network.
    """
    def __init__(self, game: GomokuGame, nn_wrapper: NeuralNetWrapper, args):
        self.game = game
        self.nn_wrapper = nn_wrapper
        self.args = args
        
        # Define loss functions
        self.policy_loss = nn.CrossEntropyLoss()
        self.value_loss = nn.MSELoss()
        
        # Define optimizer
        self.optimizer = optim.Adam(self.nn_wrapper.model.parameters(), 
                                   lr=args['lr'], 
                                   weight_decay=args['weight_decay'])
        
    def train(self, examples: List[Tuple[np.ndarray, np.ndarray, float]]):
        """
        Train the neural network with the given examples.
        
        Args:
            examples: List of (board, policy_target, game_result) tuples
        """
        if len(examples) == 0:
            print("Warning: No training examples provided.")
            return
        
        # Prepare the data
        boards, policies, values = list(zip(*examples))
        
        # Convert to tensors - boards might need reshaping depending on format
        boards = np.array(boards).astype(np.float32)
        if boards.ndim == 3:  # If boards are (n, board_size, board_size), add channel dim
            boards = boards[:, np.newaxis, :, :]  # Add channel dimension
        boards = torch.FloatTensor(boards)
        
        # Use the full policy distribution for training
        policy_targets = torch.FloatTensor(np.array(policies))
        values = torch.FloatTensor(np.array(values).astype(np.float32))
        
        # Create dataset and dataloader
        dataset = TensorDataset(boards, policy_targets, values)
        dataloader = DataLoader(dataset, batch_size=self.args['batch_size'], shuffle=True)
        
        # Training loop
        self.nn_wrapper.model.train()
        
        total_policy_loss = 0
        total_value_loss = 0
        n_batches = 0
        
        for boards_batch, policy_targets_batch, values_batch in dataloader:
            # Forward pass
            policy_logits, pred_values = self.nn_wrapper.model(boards_batch)
            
            # Calculate losses
            # Convert policy_logits to log probabilities for KL divergence
            log_policy = torch.log_softmax(policy_logits, dim=1)
            policy_target_log = torch.log_softmax(policy_targets_batch, dim=1)
            # Use KL divergence for policy loss
            policy_loss = torch.mean(torch.sum(policy_targets_batch * (torch.log(policy_targets_batch + 1e-8) - log_policy), dim=1))
            
            value_loss = self.value_loss(pred_values.squeeze(), values_batch)
            
            # Combined loss (AlphaZero uses equal weighting)
            total_loss = policy_loss + value_loss
            
            # Backward pass
            self.optimizer.zero_grad()
            total_loss.backward()
            self.optimizer.step()
            
            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            n_batches += 1
        
        avg_policy_loss = total_policy_loss / n_batches if n_batches > 0 else 0
        avg_value_loss = total_value_loss / n_batches if n_batches > 0 else 0
        
        print(f"Average Policy Loss: {avg_policy_loss:.4f}, Average Value Loss: {avg_value_loss:.4f}")
    
    def learn(self) -> List[float]:
        """
        Main learning loop that generates self-play games and trains the network.
        """
        # Initialize with random examples if needed
        train_examples = []
        
        for iteration in range(1, self.args['num_iterations'] + 1):
            print(f"ITERATION {iteration}")
            
            # Generate self-play games
            print("Generating self-play games...")
            iteration_examples = []
            
            for eps in range(self.args['num_eps_per_iteration']):
                print(f"Episode {eps + 1}/{self.args['num_eps_per_iteration']}")
                
                # Generate games with current neural network
                episode_examples = self.generate_selfplay_data()
                iteration_examples.extend(episode_examples)
            
            # Add new examples to the training data
            train_examples.extend(iteration_examples)
            
            # Keep only the most recent examples (based on args['max_examples'])
            if len(train_examples) > self.args['max_examples']:
                train_examples = train_examples[-self.args['max_examples']:]
            
            # Train the neural network
            print("Training neural network...")
            self.train(train_examples)
            
            # Save the model checkpoint
            self.nn_wrapper.save_checkpoint(folder=self.args['checkpoint_path'], 
                                          filename=f"iteration-{iteration}.pth.tar")
            
            print(f"Completed iteration {iteration}")
        
        return [0.0]  # Return dummy values for now
    
    def generate_selfplay_data(self) -> List[Tuple[np.ndarray, np.ndarray, float]]:
        """
        Generate self-play data using the current neural network.
        """
        return generate_selfplay_games(
            num_games=self.args['num_selfplay_games'],
            game=self.game,
            neural_net_wrapper=self.nn_wrapper,
            num_mcts_sims=self.args['num_mcts_sims']
        )


def train_gomoku_model(board_size: int = 15):
    """
    Main training function with default hyperparameters.
    """
    # Define hyperparameters
    args = {
        'lr': 0.001,
        'weight_decay': 0.0001,
        'batch_size': 64,
        'num_iterations': 10,  # Number of iterations to run
        'num_eps_per_iteration': 5,  # Number of episodes per iteration
        'num_selfplay_games': 10,  # Number of games to play per episode
        'num_mcts_sims': 50,  # Number of MCTS simulations per move
        'max_examples': 10000,  # Maximum number of examples to keep
        'checkpoint_path': './checkpoints',
        'num_channels': 128,
        'num_res_blocks': 10,
    }
    
    # Create game and neural network
    game = GomokuGame(board_size=board_size)
    nnet = GomokuNNet(
        board_size=board_size,
        num_channels=args['num_channels'],
        num_res_blocks=args['num_res_blocks']
    )
    
    # Create neural network wrapper
    nn_wrapper = NeuralNetWrapper(nnet)
    
    # Create trainer
    trainer = GomokuTrainer(game, nn_wrapper, args)
    
    # Create checkpoint directory
    os.makedirs(args['checkpoint_path'], exist_ok=True)
    
    # Start training
    trainer.learn()


def test_training():
    """
    Test the training functionality with a smaller network.
    """
    print("Testing training functionality...")
    
    # Define hyperparameters for testing
    args = {
        'lr': 0.001,
        'weight_decay': 0.0001,
        'batch_size': 16,  # Smaller batch size for testing
        'num_iterations': 2,  # Just 2 iterations for testing
        'num_eps_per_iteration': 1,  # Just 1 episode per iteration for testing
        'num_selfplay_games': 2,  # Just 2 games for testing
        'num_mcts_sims': 10,  # Fewer simulations for faster testing
        'max_examples': 100,  # Fewer examples for testing
        'checkpoint_path': './checkpoints_test',
        'num_channels': 32,  # Smaller network for testing
        'num_res_blocks': 3,  # Fewer residual blocks for testing
    }
    
    # Create game and neural network
    board_size = 9  # Smaller board for testing
    game = GomokuGame(board_size=board_size)
    nnet = GomokuNNet(
        board_size=board_size,
        num_channels=args['num_channels'],
        num_res_blocks=args['num_res_blocks']
    )
    
    # Create neural network wrapper
    nn_wrapper = NeuralNetWrapper(nnet)
    
    # Create trainer
    trainer = GomokuTrainer(game, nn_wrapper, args)
    
    # Create checkpoint directory
    os.makedirs(args['checkpoint_path'], exist_ok=True)
    
    # Generate some test data
    print("Generating test self-play data...")
    test_examples = trainer.generate_selfplay_data()
    print(f"Generated {len(test_examples)} test examples")
    
    # Test training with the generated data
    print("Testing training step...")
    trainer.train(test_examples[:10])  # Use only first 10 for quick test
    
    print("Training test completed successfully!")


if __name__ == "__main__":
    # Run the test
    test_training()