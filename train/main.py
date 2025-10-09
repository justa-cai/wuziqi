"""
Main training script for AlphaZero-style Gomoku implementation.
Orchestrates the training process including self-play, neural network training, and evaluation.
"""

import os
import sys
import argparse
from gomoku_game import GomokuGame
from nnet import GomokuNNet
from mcts import NeuralNetWrapper
from training import GomokuTrainer
from inference import play_against_model, ai_vs_ai_demo, test_inference


def main():
    parser = argparse.ArgumentParser(description='AlphaZero-style Gomoku Training')
    parser.add_argument('--board_size', type=int, default=15, help='Size of the Gomoku board (default: 15)')
    parser.add_argument('--mode', type=str, choices=['train', 'test', 'play', 'demo'], 
                        default='train', help='Mode to run: train, test, play, or demo')
    parser.add_argument('--model_path', type=str, default='./checkpoints/best.pth.tar', 
                        help='Path to the trained model (for play/demo modes)')
    parser.add_argument('--num_iterations', type=int, default=10, help='Number of training iterations')
    parser.add_argument('--num_mcts_sims', type=int, default=50, help='Number of MCTS simulations per move')
    parser.add_argument('--checkpoint_path', type=str, default='./checkpoints', 
                        help='Directory to save model checkpoints')
    
    args = parser.parse_args()
    
    if args.mode == 'train':
        # Training mode
        print("Starting AlphaZero-style Gomoku training...")
        
        # Create game environment
        game = GomokuGame(board_size=args.board_size)
        
        # Create neural network
        nnet = GomokuNNet(
            board_size=args.board_size,
            num_channels=128,  # Adjust based on computational resources
            num_res_blocks=10  # Adjust based on computational resources
        )
        
        # Create neural network wrapper
        nn_wrapper = NeuralNetWrapper(nnet)
        
        # Define training hyperparameters
        training_args = {
            'lr': 0.001,
            'weight_decay': 0.0001,
            'batch_size': 64,
            'num_iterations': args.num_iterations,
            'num_eps_per_iteration': 5,      # Number of episodes per iteration
            'num_selfplay_games': 10,        # Number of self-play games per episode
            'num_mcts_sims': args.num_mcts_sims,
            'max_examples': 10000,           # Maximum training examples to keep
            'checkpoint_path': args.checkpoint_path,
            'num_channels': 128,
            'num_res_blocks': 10,
        }
        
        # Create trainer
        trainer = GomokuTrainer(game, nn_wrapper, training_args)
        
        # Create checkpoint directory
        os.makedirs(training_args['checkpoint_path'], exist_ok=True)
        
        # Start training
        print("Beginning training process...")
        trainer.learn()
        print("Training completed!")
        
    elif args.mode == 'test':
        # Test mode - runs the test functions to verify implementation
        print("Running tests...")
        
        # Test the neural network
        print("\nTesting neural network...")
        from nnet import test_model
        test_model()
        
        # Test MCTS
        print("\nTesting MCTS...")
        # MCTS test would require a trained model or mock network
        
        # Test self-play
        print("\nTesting self-play...")
        from selfplay import test_selfplay
        test_selfplay()
        
        # Test training
        print("\nTesting training...")
        from training import test_training
        test_training()
        
        # Test inference
        print("\nTesting inference...")
        test_inference()
        
        print("\nAll tests completed!")
        
    elif args.mode == 'play':
        # Play mode - play against trained model
        print("Playing against trained model...")
        if not os.path.exists(args.model_path):
            print(f"Model not found at {args.model_path}. Please train a model first.")
            return
        
        play_against_model(args.model_path, args.board_size, args.num_mcts_sims)
        
    elif args.mode == 'demo':
        # Demo mode - demonstration of AI vs AI
        print("Running AI vs AI demo...")
        if not os.path.exists(args.model_path):
            print(f"Model not found at {args.model_path}. Please train a model first.")
            return
        
        ai_vs_ai_demo(args.model_path, board_size=args.board_size)


if __name__ == "__main__":
    main()