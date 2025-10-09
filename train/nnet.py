"""
Neural Network model for AlphaZero-style Gomoku implementation.
The model is based on the AlphaZero architecture with residual blocks.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualBlock(nn.Module):
    """
    Residual block for the neural network.
    """
    def __init__(self, num_channels: int = 256):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(num_channels, num_channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(num_channels)
        self.conv2 = nn.Conv2d(num_channels, num_channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(num_channels)

    def forward(self, x):
        residual = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual  # Skip connection
        out = F.relu(out)
        return out


class GomokuNNet(nn.Module):
    """
    Neural network for Gomoku that outputs both policy and value.
    Based on AlphaZero architecture with residual blocks.
    """
    def __init__(self, board_size: int = 15, num_channels: int = 256, num_res_blocks: int = 19):
        super(GomokuNNet, self).__init__()
        self.board_size = board_size
        self.num_channels = num_channels
        
        # Input embedding
        self.initial_conv = nn.Conv2d(1, num_channels, kernel_size=3, padding=1, bias=False)
        self.initial_bn = nn.BatchNorm2d(num_channels)
        
        # Residual tower
        self.res_blocks = nn.ModuleList([ResidualBlock(num_channels) for _ in range(num_res_blocks)])
        
        # Policy head
        self.policy_conv = nn.Conv2d(num_channels, 2, kernel_size=1, bias=False)
        self.policy_bn = nn.BatchNorm2d(2)
        self.policy_fc = nn.Linear(2 * board_size * board_size, board_size * board_size)
        
        # Value head
        self.value_conv = nn.Conv2d(num_channels, 1, kernel_size=1, bias=False)
        self.value_bn = nn.BatchNorm2d(1)
        self.value_fc1 = nn.Linear(board_size * board_size, 256)
        self.value_fc2 = nn.Linear(256, 1)
        
    def forward(self, x):
        # Input shape: (batch_size, 1, board_size, board_size)
        batch_size = x.size(0)
        
        # Input embedding
        h = F.relu(self.initial_bn(self.initial_conv(x)))
        
        # Residual tower
        for res_block in self.res_blocks:
            h = res_block(h)
        
        # Policy head
        p = F.relu(self.policy_bn(self.policy_conv(h)))
        p = p.view(batch_size, -1)  # Flatten
        policy = self.policy_fc(p)  # Output shape: (batch_size, board_size^2)
        
        # Value head
        v = F.relu(self.value_bn(self.value_conv(h)))
        v = v.view(batch_size, -1)  # Flatten
        v = F.relu(self.value_fc1(v))
        value = torch.tanh(self.value_fc2(v))  # Output value between -1 and 1
        
        # Apply softmax to policy to get probabilities (this is typically done outside the network
        # during training, but here we return logits)
        return policy, value


def test_model():
    """
    Test the model with a sample input.
    """
    board_size = 15
    model = GomokuNNet(board_size=board_size)
    
    # Create a sample input (batch_size=1, channels=1, height=15, width=15)
    sample_input = torch.randn(1, 1, board_size, board_size)
    
    policy, value = model(sample_input)
    
    print(f"Input shape: {sample_input.shape}")
    print(f"Policy shape: {policy.shape}")
    print(f"Value shape: {value.shape}")
    print(f"Policy output: {policy[0, :10]}...")  # First 10 policy values
    print(f"Value output: {value[0].item()}")


if __name__ == "__main__":
    test_model()