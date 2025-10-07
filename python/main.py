# -*- coding: utf-8 -*-
import pygame
import sys
import time
from openai import OpenAI
import logging
import builtins
import numpy as np
import argparse
import random
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables with fallback values
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5")

# 配置日志记录
logging.basicConfig(
    filename='dbg.log',
    filemode='w',  # This will automatically overwrite the file
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Changed from DEBUG to INFO to reduce verbosity
)

# 配置第三方库的日志级别以减少噪音
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# 启动时清空日志文件 (this is redundant since filemode='w' already does this,
# but adding explicit clear at the beginning of the log for clarity)
logging.info("="*50)
logging.info("NEW GAME SESSION STARTED")
logging.info("="*50)

# 重定向print函数到日志
def custom_print(*args, **kwargs):
    # 构建消息
    message = ' '.join(str(arg) for arg in args)
    # 记录到日志
    logging.info(f"PRINT: {message}")
    # 如果希望同时在控制台显示，可以取消下面一行的注释
    # builtins.print(*args, **kwargs)

# 保存原始的print函数
original_print = builtins.print

# 替换内置的print函数
builtins.print = custom_print

# ==================== 配置区（用户可修改）====================
BOARD_SIZE = 15
CELL_SIZE = 40
MARGIN = 40



try:
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
except Exception as e:
    print("❌ 初始化失败:", e)
    sys.exit(1)

# ==================== Pygame 初始化 ====================
pygame.init()
pygame.mixer.init()  # Initialize sound mixer
WIDTH = BOARD_SIZE * CELL_SIZE + 2 * MARGIN
HEIGHT = BOARD_SIZE * CELL_SIZE + 2 * MARGIN
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("五子棋 - 智能AI防守版")
clock = pygame.time.Clock()

# Initialize sound effects
# Create simple sound effects if files are not available
def create_simple_sound(frequency=440, duration=200, volume=0.5):
    """Create a simple sound using sine wave"""
    import numpy as np
    sample_rate = 22050
    n_samples = int(round(duration * sample_rate / 1000.0))
    
    # Generate array of samples
    buf = np.zeros((n_samples, 2), dtype=np.int16)  # Stereo
    for s in range(n_samples):
        t = float(s) / sample_rate  # Time in seconds
        val = int(32767.0 * volume * np.sin(2 * np.pi * frequency * t))
        buf[s][0] = val  # Left channel
        buf[s][1] = val  # Right channel
    
    # Convert to bytes and create sound
    sound = pygame.sndarray.make_sound(buf)
    return sound

try:
    place_sound = pygame.mixer.Sound("place.wav")  # Sound for placing a piece
except:
    # Generate a short "click" sound
    place_sound = create_simple_sound(frequency=800, duration=100, volume=0.3)

try:
    win_sound = pygame.mixer.Sound("win.wav")  # Sound for winning
except:
    # Generate a pleasant win sound (chord)
    win_sound = create_simple_sound(frequency=523, duration=1000, volume=0.5)  # C note

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
RED = (255, 100, 100)

board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
current_player = 1
game_over = False
winner = None

# Game UI elements
turn_timer = 0  # Timer for current player's turn
MAX_TURN_TIME = 30  # Max time per turn in seconds

# Track last move for highlighting
last_move = None  # Tuple of (row, col) for the last placed stone

# LLM usage flag - defaults to False (traditional methods only)
use_llm = False
def detect_live_three(board, player):
    """检测玩家是否有‘活三’（两端空的三个连续子）"""
    directions = [(1,0), (0,1), (1,1), (1,-1)]
    threats = []

    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == player:
                for dx, dy in directions:
                    chain = []
                    x, y = i, j
                    # 正向扫描
                    while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == player:
                        chain.append((x, y))
                        x += dx
                        y += dy
                    # 反向扫描
                    x, y = i - dx, j - dy
                    while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == player:
                        chain.insert(0, (x, y))
                        x -= dx
                        y -= dy

                    if len(chain) == 3:
                        start = chain[0]
                        end = chain[-1]
                        before_start = (start[0] - dx, start[1] - dy)
                        after_end = (end[0] + dx, end[1] + dy)

                        # 检查是否为“活三”：两端都在界内且为空
                        if (0 <= before_start[0] < BOARD_SIZE and 0 <= before_start[1] < BOARD_SIZE and
                                board[before_start[0]][before_start[1]] == 0 and
                                0 <= after_end[0] < BOARD_SIZE and 0 <= after_end[1] < BOARD_SIZE and
                                board[after_end[0]][after_end[1]] == 0):
                            threats.append(before_start)
                            threats.append(after_end)
    return threats
# ==================== AI 决策函数 ====================
def ai_move():
    if game_over:
        logging.debug("Game over, skipping AI move")
        return None

    # 1. 检查自己是否有立即获胜的机会 (五连珠) - 最高优先级
    # 遍历整个棋盘，检查是否AI下一颗棋就能形成五连珠
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == 0:  # 空位才能放置
                # 临时放置AI棋子
                board[i][j] = 2
                if check_winner(i, j) == 2:  # 如果AI获胜
                    logging.info(f"AI detected immediate win at ({i}, {j})")
                    print(f"🎉 AI 发现立即获胜机会: ({i}, {j})")
                    board[i][j] = 0  # 恢复棋盘
                    return i, j
                board[i][j] = 0  # 恢复棋盘

    # 2. 检查对手是否有立即获胜的机会 - 第二优先级
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == 0:  # 空位才能放置
                # 临时放置对手棋子
                board[i][j] = 1
                if check_winner(i, j) == 1:  # 如果对手获胜
                    logging.info(f"AI detected opponent immediate win at ({i}, {j}), blocking")
                    print(f"🚨 AI 发现对手立即获胜威胁: ({i}, {j})")
                    board[i][j] = 0  # 恢复棋盘
                    return i, j
                board[i][j] = 0  # 恢复棋盘

    # 3. 检查自己是否有活四可以进攻 - 第三优先级
    has_my_live_four, my_four_points = has_threat(board, 2)
    if has_my_live_four:
        logging.info(f"AI detected live four for itself at positions: {my_four_points}")
        print("🎯 AI 发现活四可以进攻")
        for r, c in my_four_points:
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == 0:
                logging.debug(f"AI attacking with live four at ({r}, {c}) using traditional method")
                return r, c

    # 4. 检查对手是否有活四 → 必须挡 - 第四优先级
    has_live_four, four_points = has_threat(board, 1)
    if has_live_four:
        logging.info(f"AI detected live four for player 1 at positions: {four_points}")
        print("🚨 发现活四！紧急防守")
        for r, c in four_points:
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == 0:
                logging.debug(f"AI blocking live four at ({r}, {c}) using traditional method")
                return r, c

    # 5. 检查自己是否有活三可以进攻 - 第五优先级
    my_live_three_points = detect_live_three(board, 2)
    if len(my_live_three_points) > 0:
        logging.info(f"AI detected live three for itself at positions: {my_live_three_points}")
        print("💡 AI 发现活三可以进攻")
        # 优先选择能同时进攻的点
        for r, c in my_live_three_points:
            if board[r][c] == 0:
                score = evaluate_position(r, c, 2)
                if score > 150:  # Higher threshold for self-attack
                    logging.debug(f"AI found attacking move at ({r}, {c}) with score {score}")
                    return r, c

    # 6. 检查对手是否有活三 → 高危，优先压制 - 第六优先级
    live_three_points = detect_live_three(board, 1)
    if len(live_three_points) > 0:
        logging.info(f"AI detected live three for player 1 at positions: {live_three_points}")
        print("⚠️ 发现活三！考虑压制")
        # 优先选择能同时阻止+自己发展的点
        for r, c in live_three_points:
            if board[r][c] == 0:
                # 可加入评估函数判断是否值得下
                score = evaluate_position(r, c, 2)
                if score > 100:  # 有进攻潜力
                    logging.debug(f"AI found attacking move at ({r}, {c}) with score {score}")
                    return r, c

    # 7. 如果没有紧急威胁，先用传统评估方法
    logging.info("No critical threats detected, using traditional evaluation")
    traditional_move = strategic_fallback()
    if traditional_move:
        logging.info(f"Traditional evaluation suggests move: {traditional_move}")
        # Verify this is a good defensive move before LLM
        r, c = traditional_move
        # If this move blocks opponent's potential win or creates a strong position, use it
        opp_threat_score = evaluate_position(r, c, 1)  # Score for blocking opponent
        if opp_threat_score >= 10000:  # If it blocks significant opponent threat
            logging.info(f"Traditional method found strong defensive move at ({r}, {c}), using it")
            return traditional_move

    # 8. 如果启用LLM，则调用大模型，否则直接使用传统方法
    if not use_llm:
        logging.info("LLM is disabled, using traditional evaluation as final strategy")
        print("🔍 使用传统AI策略")
        return traditional_move
    
    # 8. 启用LLM的情况下才调用大模型
    logging.info("LLM is enabled, using OpenAI API for advanced strategy")
    print("🧠 AI 正在深度思考...")
    
    # 构造棋盘文本
    board_str = ""
    for i in range(BOARD_SIZE):
        row = []
        for j in range(BOARD_SIZE):
            if board[i][j] == 0:
                row.append(".")
            elif board[i][j] == 1:
                row.append("X")  # 玩家黑子
            else:
                row.append("O")  # AI 白子
        board_str += " ".join(row) + "\n"

    # 💥 强化 Prompt：让 AI 像职业棋手一样思考
    prompt = f"""
你是一个世界顶级五子棋AI，执白子'O'，对手是'X'。
棋盘大小：{BOARD_SIZE}x{BOARD_SIZE}，坐标从0开始。

【当前棋盘】
{board_str}

【你的任务】
轮到你下，请输出最佳落子位置（格式：row,col），并遵循以下规则：

🎯 决策顺序（必须优先考虑）：
1. ❗ 防守：如果对手下一步能形成“活四”或“双三”，必须立即阻挡！
2. ✅ 攻击：如果你能形成“活四”或“冲四+活三”，优先进攻取胜。
3. 🔄 攻防兼备：如果某个位置既能阻止对手，又能建立自己的进攻线路，优先选择它。
4. ⚠️ 斜线同样重要！不要忽略对角线威胁。

📌 示例：
- 如果 X 有活四，你必须挡。
- 如果你下在某点，既可堵住 X 的活三，又可形成自己的活三 → 这是最佳选择。
- 不要只想着“我不能输”，而要思考“我能赢”。

⚠️ 注意：
- 绝不能忽略对手的“活三”！
- 输出格式：只返回一行 "row,col"，例如 "7,7"
- 不要解释，不要多说话。
"""

    try:
        logging.info("AI calling OpenAI API for move decision")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是专业五子棋AI，冷静、精准、防守严密，只输出 row,col。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=32,
            n=1
        )
        reply = response.choices[0].message.content.strip()
        print(f"🤖 AI 回复: {reply}")
        logging.debug(f"OpenAI response: {reply}")

        # 更鲁棒的解析
        lines = [line.strip() for line in reply.splitlines()]
        for line in lines:
            cleaned = line.replace(" ", "").replace("(", "").replace(")", "")
            if "," in cleaned:
                parts = cleaned.split(",")
                if len(parts) == 2:
                    try:
                        r, c = int(parts[0]), int(parts[1])
                        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == 0:
                            print(f"✅ AI 落子于 ({r}, {c})")
                            logging.info(f"AI decided move: ({r}, {c})")
                            return r, c
                    except ValueError as e:
                        logging.error(f"Failed to parse AI response: {parts}, error: {e}")
                        continue
        
        logging.warning("AI response was invalid, using traditional fallback strategy")
        print("⚠️ AI 输出无效，使用传统AI策略...")
        return traditional_move

    except Exception as e:
        logging.error(f"AI error: {e}")
        print(f"❌ AI 错误: {e}")
        return traditional_move
    
def evaluate_position(r, c, player):
    """评估 (r,c) 对 player 的价值（攻防综合评分）"""
    if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE or board[r][c] != 0:
        return 0
    
    score = 0
    directions = [(1,0), (0,1), (1,1), (1,-1)]
    opp = 3 - player

    for dx, dy in directions:
        # 计算当前方向上的连子数和阻塞情况
        own_chain = 0
        block_count = 0

        # 正向
        x, y = r + dx, c + dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
            if board[x][y] == player:
                own_chain += 1
            elif board[x][y] != 0:
                block_count += 1
                break
            else:
                break
            x += dx
            y += dy

        # 反向
        x, y = r - dx, c - dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
            if board[x][y] == player:
                own_chain += 1
            elif board[x][y] != 0:
                block_count += 1
                break
            else:
                break
            x -= dx
            y -= dy

        length = own_chain + 1
        if block_count == 2:
            score += 0  # 两面被堵，无效
        elif block_count == 1:
            # 单面被堵
            if length >= 5:
                score += 100000  # 五连
            elif length == 4:
                score += 10000   # 冲四
            elif length == 3:
                score += 1000    # 眠三
            elif length == 2:
                score += 100     # 眠二
        else:
            # 无阻塞
            if length >= 5:
                score += 1000000 # 连五
            elif length == 4:
                score += 100000  # 活四
            elif length == 3:
                score += 10000   # 活三
            elif length == 2:
                score += 1000    # 活二

    return score


def evaluate_board():
    """评估整个棋盘局势"""
    total_score = 0
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] != 0:
                # 评价该位置对当前玩家的价值
                player = board[i][j]
                position_score = 0
                directions = [(1,0), (0,1), (1,1), (1,-1)]
                
                for dx, dy in directions:
                    # 计算该点在各方向上的连子情况
                    chain = 1  # 当前点
                    block_count = 0
                    
                    # 正向
                    x, y = i + dx, j + dy
                    while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == player:
                        chain += 1
                        x += dx
                        y += dy
                    if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE) or board[x][y] != 0:
                        block_count += 1
                    
                    # 反向
                    x, y = i - dx, j - dy
                    while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == player:
                        chain += 1
                        x -= dx
                        y -= dy
                    if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE) or board[x][y] != 0:
                        block_count += 1
                    
                    # 根据连子数和阻塞数评分
                    if block_count == 2:
                        continue  # 两面被堵
                    elif block_count == 1:
                        # 单面被堵
                        if chain >= 5:
                            return 1000000 if player == 2 else -1000000  # 立即胜利
                        elif chain == 4:
                            position_score += 10000
                        elif chain == 3:
                            position_score += 1000
                        elif chain == 2:
                            position_score += 100
                    else:
                        # 无阻塞
                        if chain >= 5:
                            return 1000000 if player == 2 else -1000000  # 立即胜利
                        elif chain == 4:
                            position_score += 100000
                        elif chain == 3:
                            position_score += 10000
                        elif chain == 2:
                            position_score += 1000
                
                # 累加此位置的分数
                if player == 2:  # AI棋子
                    total_score += position_score
                else:  # 人类棋子
                    total_score -= position_score
    
    return total_score


def get_valid_moves():
    """获取所有有效的位置（空位，且周围有棋子）"""
    moves = []
    # 找到所有有棋子的位置
    occupied = []
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] != 0:
                occupied.append((i, j))
    
    # 扩展到周围空位
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    candidates = set()
    
    for r, c in occupied:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == 0:
                candidates.add((nr, nc))
    
    # 如果没有邻近位置，选择中心附近的空位
    if not candidates:
        center = BOARD_SIZE // 2
        for i in range(max(0, center-2), min(BOARD_SIZE, center+3)):
            for j in range(max(0, center-2), min(BOARD_SIZE, center+3)):
                if board[i][j] == 0:
                    candidates.add((i, j))
    
    # 如果棋盘还是空的，返回中心
    if not candidates:
        candidates.add((BOARD_SIZE//2, BOARD_SIZE//2))
    
    # 按照与中心的距离排序，优先考虑靠近中心的位置
    center = BOARD_SIZE // 2
    moves = sorted(list(candidates), key=lambda pos: abs(pos[0]-center) + abs(pos[1]-center))
    
    return moves


def alpha_beta_search(depth, alpha, beta, maximizing_player):
    """Alpha-Beta剪枝搜索"""
    winner = check_game_over()
    if depth == 0 or winner != 0:
        if winner == 2:  # AI赢
            return float('inf'), None
        elif winner == 1:  # 人类赢
            return float('-inf'), None
        else:  # 深度用完
            return evaluate_board(), None
    
    moves = get_valid_moves()
    
    if maximizing_player:  # AI回合（最大化）
        max_eval = float('-inf')
        best_move = None
        
        for r, c in moves:
            # 尝试落子
            board[r][c] = 2
            
            # 递归搜索
            eval_score, _ = alpha_beta_search(depth - 1, alpha, beta, False)
            
            # 撤销落子
            board[r][c] = 0
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (r, c)
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:  # Alpha-Beta剪枝
                break
        
        return max_eval, best_move
    
    else:  # 人类回合（最小化）
        min_eval = float('inf')
        best_move = None
        
        for r, c in moves:
            # 尝试落子
            board[r][c] = 1
            
            # 递归搜索
            eval_score, _ = alpha_beta_search(depth - 1, alpha, beta, True)
            
            # 撤销落子
            board[r][c] = 0
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (r, c)
            
            beta = min(beta, eval_score)
            if beta <= alpha:  # Alpha-Beta剪枝
                break
        
        return min_eval, best_move


def check_game_over():
    """检查游戏是否结束（简化版本，只检查是否有五子连珠）"""
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] != 0:
                color = board[i][j]
                directions = [(1,0), (0,1), (1,1), (1,-1)]
                
                for dx, dy in directions:
                    count = 1
                    # 正向检查
                    x, y = i + dx, j + dy
                    while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
                        count += 1
                        x += dx
                        y += dy
                    # 反向检查
                    x, y = i - dx, j - dy
                    while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
                        count += 1
                        x -= dx
                        y -= dy
                    if count >= 5:
                        return color  # 返回获胜者
    return 0  # 游戏未结束


def strategic_fallback():
    """基于Alpha-Beta搜索选择最优空位"""
    # 使用Alpha-Beta搜索找最佳位置
    depth = 2  # 搜索深度，可根据性能调整
    logging.info(f"Starting Alpha-Beta search with depth {depth}")
    eval_score, best_move = alpha_beta_search(depth, float('-inf'), float('inf'), True)
    
    if best_move:
        r, c = best_move
        logging.info(f"Alpha-Beta search found move ({r}, {c}) with score {eval_score}")
        print(f"🔧 Alpha-Beta AI落子: {best_move} (搜索深度: {depth})")
        return best_move

    logging.info("Alpha-Beta search failed, falling back to evaluation-based strategy")
    
    # 如果Alpha-Beta搜索失败，使用原来的评估方法
    best_score = float('-inf')
    best_move = None

    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == 0:
                # 综合考虑：AI 自己得分高，且能阻止对手
                my_score = evaluate_position(i, j, 2)      # AI 进攻分
                opp_threat = evaluate_position(i, j, 1)     # 阻止对手得分
                total = my_score + opp_threat * 1.2         # 更重视防守！

                if total > best_score:
                    best_score = total
                    best_move = (i, j)

    if best_move:
        r, c = best_move
        logging.info(f"Fallback strategy selected move ({r}, {c}) with score {best_score:.1f}")
        print(f"🔧 备选落子: {best_move} (评分: {best_score:.1f})")
        return best_move

    # 最后兜底 - 遍历寻找第一个空位
    logging.warning("All strategies failed, using first available position")
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == 0:
                logging.info(f"Using fallback move at ({i}, {j})")
                print(f"🔧 兜底落子: ({i}, {j})")
                return i, j
    logging.error("No valid moves found, game board may be full")
    return None
def check_winner(row, col):
    color = board[row][col]
    directions = [(1,0), (0,1), (1,1), (1,-1)]
    for dx, dy in directions:
        count = 1
        x, y = row + dx, col + dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
            count += 1
            x += dx
            y += dy
        x, y = row - dx, col - dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
            count += 1
            x -= dx
            y -= dy
        if count >= 5:
            return color
    return 0

def draw_board():
    screen.fill(WHITE)
    for i in range(BOARD_SIZE):
        pygame.draw.line(screen, GRAY,
                         (MARGIN, MARGIN + i * CELL_SIZE),
                         (MARGIN + (BOARD_SIZE - 1) * CELL_SIZE, MARGIN + i * CELL_SIZE))
        pygame.draw.line(screen, GRAY,
                         (MARGIN + i * CELL_SIZE, MARGIN),
                         (MARGIN + i * CELL_SIZE, MARGIN + (BOARD_SIZE - 1) * CELL_SIZE))

    star_points = [(3,3), (3,11), (11,3), (11,11), (7,7)]
    for sr, sc in star_points:
        pygame.draw.circle(screen, BLACK,
                           (MARGIN + sc * CELL_SIZE, MARGIN + sr * CELL_SIZE), 5)

    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == 1:
                # Draw black stone
                pygame.draw.circle(screen, BLACK,
                                   (MARGIN + j * CELL_SIZE, MARGIN + i * CELL_SIZE),
                                   CELL_SIZE // 2 - 2)
                # Highlight last move with red border if this is the last move
                if last_move and last_move == (i, j):
                    pygame.draw.circle(screen, RED,
                                       (MARGIN + j * CELL_SIZE, MARGIN + i * CELL_SIZE),
                                       CELL_SIZE // 2 - 2, 3)  # Red border
            elif board[i][j] == 2:
                # Draw white stone
                pygame.draw.circle(screen, WHITE,
                                   (MARGIN + j * CELL_SIZE, MARGIN + i * CELL_SIZE),
                                   CELL_SIZE // 2 - 2)
                pygame.draw.circle(screen, GRAY,
                   (MARGIN + j * CELL_SIZE, MARGIN + i * CELL_SIZE),
                   CELL_SIZE // 2 - 2, 1)  # Gray outline
                # Highlight last move with red border if this is the last move
                if last_move and last_move == (i, j):
                    pygame.draw.circle(screen, RED,
                                       (MARGIN + j * CELL_SIZE, MARGIN + i * CELL_SIZE),
                                       CELL_SIZE // 2 - 2, 3)  # Red border

    # Draw turn indicator and timer with CJK font support
    # Try to use a font that supports Chinese characters
    available_fonts = pygame.font.get_fonts()
    font = None
    
    # Prioritize CJK fonts that are known to support Chinese
    cjk_fonts = [
        "notosanscjksc",  # Noto Sans CJK SC (Simplified Chinese)
        "notoserifcjksc", # Noto Serif CJK SC
        "notosanscjkhk",  # Noto Sans CJK HK
        "notosanscjkjp",  # Noto Sans CJK JP (supports Chinese)
        "notosanscjkkr",  # Noto Sans CJK KR (supports Chinese)
        "arplumingcn",    # AR PL UMing CN
        "arplumingtw",    # AR PL UMing TW
        "wqyzenhei",      # WenQuanYi Zen Hei
        "wqymicrohei",    # WenQuanYi Micro Hei
        "simhei",         # SimHei
    ]
    
    # Try CJK fonts first
    for font_name in cjk_fonts:
        if font_name in available_fonts:
            try:
                font = pygame.font.SysFont(font_name, 24)
                break
            except:
                continue
    
    # If no CJK font found, try system fonts
    if font is None:
        try:
            # Try to use a font that supports Chinese characters
            font = pygame.font.Font("simhei.ttf", 24)
        except:
            try:
                font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 24)  # Windows
            except:
                try:
                    font = pygame.font.Font("/System/Library/Fonts/PingFang.ttc", 24)  # macOS
                except:
                    try:
                        font = pygame.font.Font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)  # Linux
                    except:
                        font = pygame.font.SysFont("arialunicode", 24)  # Unicode font
                        if font.name != "arialunicode":
                            font = pygame.font.SysFont(None, 24)
    
    if current_player == 1 and not game_over:
        turn_text = font.render(f"轮到: 玩家 (黑子)", True, BLACK)
    elif current_player == 2 and not game_over:
        turn_text = font.render(f"轮到: AI (白子)", True, (150, 150, 150))
    else:
        turn_text = font.render("游戏结束", True, RED)
    
    # Calculate remaining time
    remaining_time = max(0, MAX_TURN_TIME - int(turn_timer))
    time_text = font.render(f"时间: {remaining_time}s", True, BLACK if current_player == 1 else (150, 150, 150))
    
    # Position the turn and time indicators
    screen.blit(turn_text, (WIDTH - 180, 0))
    screen.blit(time_text, (WIDTH - 180, 25))
                
def has_threat(board, player):
    directions = [(1,0), (0,1), (1,1), (1,-1)]
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == player:
                for dx, dy in directions:
                    chain = []
                    x, y = i, j
                    while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == player:
                        chain.append((x, y))
                        x += dx
                        y += dy
                    x, y = i - dx, j - dy
                    while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == player:
                        chain.insert(0, (x, y))
                        x -= dx
                        y -= dy

                    if len(chain) == 4:
                        start = chain[0]
                        end = chain[-1]
                        # 检查两端是否为空
                        if (start[0]-dx, start[1]-dy) in [(r,c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)] and board[start[0]-dx][start[1]-dy] == 0:
                            if (end[0]+dx, end[1]+dy) in [(r,c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)] and board[end[0]+dx][end[1]+dy] == 0:
                                return True, [(start[0]-dx, start[1]-dy), (end[0]+dx, end[1]+dy)]
    return False, []

# 在 draw_board() 后面添加
def display_message(msg):
    # 支持中文显示的字体处理
    pygame.font.init()  # 确保字体系统初始化
    
    # 优先使用支持中文的字体
    cjk_fonts = [
        "notosanscjksc",  # Noto Sans CJK SC (Simplified Chinese)
        "notoserifcjksc", # Noto Serif CJK SC (Simplified Chinese)
        "notosanscjkhk",  # Noto Sans CJK HK (Hong Kong)
        "notosanscjkjp",  # Noto Sans CJK JP (Japanese, but supports Chinese)
        "notosanscjkkr",  # Noto Sans CJK KR (Korean, but supports Chinese)
        "arplumingcn",    # AR PL UMing CN (Chinese)
        "arplumingtw",    # AR PL UMing TW (Traditional Chinese)
        "arplumingtwmbe", # AR PL UMing TW MBE (Traditional Chinese)
    ]
    
    font = None
    
    # 尝试使用 Noto CJK 字体
    available_fonts = pygame.font.get_fonts()
    for font_name in cjk_fonts:
        if font_name in available_fonts:
            try:
                font = pygame.font.SysFont(font_name, 40)
                break
            except:
                continue
    
    # 如果没有CJK字体可用，尝试其他支持Unicode的字体
    if font is None:
        try:
            # 尝试使用系统中文字体
            font = pygame.font.Font("simhei.ttf", 40)
        except:
            try:
                # 尝试其他中文字体
                font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 40)  # Windows
            except:
                try:
                    # 尝试其他中文字体路径
                    font = pygame.font.Font("/System/Library/Fonts/PingFang.ttc", 40)  # macOS
                except:
                    try:
                        # 尝试 Linux 字体
                        font = pygame.font.Font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
                    except:
                        # 最后的备选方案，使用默认字体
                        font = pygame.font.SysFont("dejavusans", 40)  # DejaVu Sans 支持更多Unicode
                        if font.name != "dejavusans":  # 如果系统没有该字体，使用默认
                            font = pygame.font.SysFont(None, 40)
    
    text = font.render(msg, True, RED)
    rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(text, rect)
    pygame.display.update()
    pygame.time.delay(2500)
# ==================== 主循环 ====================
def reset_game():
    """重置游戏状态，准备新局"""
    global board, current_player, game_over, winner, last_move
    # 重置棋盘
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    # 重置游戏状态
    current_player = 1
    game_over = False
    winner = None
    last_move = None  # Reset the last move tracking
    print("🔄 开始新局！")

def main():
    global current_player, game_over, winner, turn_timer, last_move
    logging.info("Game started")
    print("🎮 启动！AI 已加载高级战术逻辑")
    
    # 初始新游戏
    reset_game()
    last_time = time.time()

    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        # Update turn timer
        if not game_over:
            turn_timer += dt
            if turn_timer > MAX_TURN_TIME:
                # Time's up - make a random move for the current player
                if current_player == 1:  # Player's turn
                    logging.info("Player timeout - making random move")
                    # Find available moves
                    available_moves = []
                    for i in range(BOARD_SIZE):
                        for j in range(BOARD_SIZE):
                            if board[i][j] == 0:
                                available_moves.append((i, j))
                    
                    if available_moves:
                        random_move = random.choice(available_moves)
                        r, c = random_move
                        board[r][c] = 1
                        logging.info(f"Random player move at ({r}, {c}) due to timeout")
                        last_move = (r, c)  # Track the move
                        place_sound.play()  # Play sound for the move
                        winner = check_winner(r, c)
                        if winner:
                            game_over = True
                        else:
                            current_player = 2
                    else:
                        # No moves available - board is full
                        game_over = True
                elif current_player == 2:  # AI's turn
                    logging.info("AI timeout - making random move")
                    # Find available moves
                    available_moves = []
                    for i in range(BOARD_SIZE):
                        for j in range(BOARD_SIZE):
                            if board[i][j] == 0:
                                available_moves.append((i, j))
                    
                    if available_moves:
                        random_move = random.choice(available_moves)
                        r, c = random_move
                        board[r][c] = 2
                        logging.info(f"Random AI move at ({r}, {c}) due to timeout")
                        last_move = (r, c)  # Track the move
                        place_sound.play()  # Play sound for the move
                        winner = check_winner(r, c)
                        if winner:
                            game_over = True
                        else:
                            current_player = 1
                    else:
                        # No moves available - board is full
                        game_over = True
                
                turn_timer = 0  # Reset timer

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logging.info("Quit event received, exiting game")
                pygame.quit()
                sys.exit()

        if game_over:
            result = "你赢了！" if winner == 1 else "AI 赢了！"
            logging.info(f"Game over: {result} (winner: {winner})")
            display_message(result)
            # 3秒后自动开始新游戏
            pygame.time.delay(1000)  # 延迟3秒
            logging.info("Starting new game after delay")
            reset_game()  # 重置游戏状态
            turn_timer = 0  # Reset timer for new game

        if current_player == 1:  # 玩家
            waiting = True
            start_wait_time = time.time()
            while waiting and not game_over:
                # Update timer during player's turn to ensure it refreshes properly
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time
                turn_timer += dt  # Keep updating the timer during player's turn
                
                if turn_timer > MAX_TURN_TIME:  # Player timeout
                    logging.info("Player timeout during move selection - making random move")
                    # Find available moves
                    available_moves = []
                    for i in range(BOARD_SIZE):
                        for j in range(BOARD_SIZE):
                            if board[i][j] == 0:
                                available_moves.append((i, j))
                    
                    if available_moves:
                        random_move = random.choice(available_moves)
                        r, c = random_move
                        board[r][c] = 1
                        logging.info(f"Random player move at ({r}, {c}) due to timeout")
                        last_move = (r, c)  # Track the move
                        place_sound.play()  # Play sound for the move
                        winner = check_winner(r, c)
                        if winner:
                            game_over = True
                        else:
                            current_player = 2
                    else:
                        # No moves available - board is full
                        game_over = True
                    
                    turn_timer = 0
                    break
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        logging.info("Quit event received during player turn")
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        col = round((x - MARGIN) / CELL_SIZE)
                        row = round((y - MARGIN) / CELL_SIZE)
                        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and board[row][col] == 0:
                            logging.info(f"Player moved at ({row}, {col})")
                            board[row][col] = 1
                            last_move = (row, col)  # Track the last move
                            place_sound.play()  # Play sound for placing piece
                            winner = check_winner(row, col)
                            if winner:
                                game_over = True
                                logging.info(f"Player win detected at ({row}, {col})")
                                win_sound.play()  # Play win sound
                            else:
                                current_player = 2
                                turn_timer = 0  # Reset timer when turn changes
                                logging.debug("Switching to AI player")
                            waiting = False
                draw_board()
                pygame.display.update()
                clock.tick(30)

        elif current_player == 2 and not game_over:
            # Check for timeout before AI move (in case timer was set during general loop)
            if turn_timer > MAX_TURN_TIME:
                logging.info("AI timeout during AI turn - making random move")
                # Find available moves
                available_moves = []
                for i in range(BOARD_SIZE):
                    for j in range(BOARD_SIZE):
                        if board[i][j] == 0:
                            available_moves.append((i, j))
                
                if available_moves:
                    import random
                    random_move = random.choice(available_moves)
                    r, c = random_move
                    board[r][c] = 2
                    logging.info(f"Random AI move at ({r}, {c}) due to timeout")
                    last_move = (r, c)  # Track the move
                    place_sound.play()  # Play sound for the move
                    winner = check_winner(r, c)
                    if winner:
                        game_over = True
                        win_sound.play()  # Play win sound if AI wins
                    else:
                        current_player = 1
                else:
                    # No moves available - board is full
                    game_over = True
                
                turn_timer = 0
            else:
                # Normal AI move
                move = ai_move()
                if move:
                    r, c = move
                    logging.info(f"AI moved at ({r}, {c})")
                    pygame.time.wait(600)  # 增加一点思考感
                    board[r][c] = 2
                    last_move = (r, c)  # Track the last move
                    place_sound.play()  # Play sound for AI placing piece
                    winner = check_winner(r, c)
                    if winner:
                        game_over = True
                        logging.info(f"AI win detected at ({r}, {c})")
                        win_sound.play()  # Play win sound
                    else:
                        current_player = 1
                        turn_timer = 0  # Reset timer when turn changes
                        logging.debug("Switching to human player")

        draw_board()
        pygame.display.update()
        clock.tick(30)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='五子棋游戏')
    parser.add_argument('--llm', action='store_true', 
                        help='启用LLM (默认: 关闭, 仅使用传统AI方法)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    use_llm = args.llm  # Set the global variable based on argument
    main()