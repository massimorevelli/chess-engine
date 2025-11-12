import chess
import chess.pgn
from chess.polyglot import zobrist_hash
import math
import time
from datetime import datetime, timezone
import os


# ===== VALUES / BONUSES / PENALTIES =====


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


TEMPO_BONUS = 10
BISHOP_PAIR_BONUS = 30
ROOK_SAME_FILE_BONUS = 12
ROOK_SAME_RANK_BONUS = 12
OPEN_FILE_BONUS = 20
SEMI_OPEN_FILE_BONUS = 10

DOUBLED_PAWN_PENALTY = 10
ISOLATED_PAWN_PENALTY = 8
PASSED_PAWN_BONUS_BY_RANK = [0, 5, 10, 20, 35, 60, 100, 0]


# ===== PSTs =====


PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KING_TABLE = [
     20, 35, 10,  0,  0, 10, 35, 20,
     20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
      0,  0,  5,  5,  5,  5,  0, -5,
     -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

PST = {chess.PAWN: PAWN_TABLE,
       chess.KNIGHT: KNIGHT_TABLE,
       chess.BISHOP: BISHOP_TABLE,
       chess.ROOK: ROOK_TABLE,
       chess.KING: KING_TABLE,
       chess.QUEEN: QUEEN_TABLE
       }


# ===== STATIC BOARD EVALUATION =====

def evaluate(board):
    """Returns a centipawn score from White's perspective"""
    
    score = 0

    if board.is_checkmate():
        return -99999 if board.turn else 99999
    
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_threefold_repetition():
        return 0
    
    # Material count + PST

    for piece_type, value in PIECE_VALUES.items():

        for sq in board.pieces(piece_type, chess.WHITE):
            score += value
            score += PST[piece_type][sq]

        for sq in board.pieces(piece_type, chess.BLACK):
            score -= value
            score -= PST[piece_type][chess.square_mirror(sq)]

    # Bishop pair
        
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        score += BISHOP_PAIR_BONUS
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        score -= BISHOP_PAIR_BONUS

    # Rook coordination
    
    for color, sign in ((chess.WHITE, +1), (chess.BLACK, -1)):
        rooks = list(board.pieces(chess.ROOK, color))

        if len(rooks) >= 2:
            files = [chess.square_file(sq) for sq in rooks]
            ranks = [chess.square_rank(sq) for sq in rooks]
            if len(set(files)) < len(files):
                score += sign * ROOK_SAME_FILE_BONUS
            if len(set(ranks)) < len(ranks):
                score += sign * ROOK_SAME_RANK_BONUS

        my_pawn_files = {chess.square_file(sq) for sq in board.pieces(chess.PAWN, color)}
        opp_color = chess.BLACK if color == chess.WHITE else chess.WHITE
        opp_pawn_files = {chess.square_file(sq) for sq in board.pieces(chess.PAWN, opp_color)}

        for sq in rooks:
            f = chess.square_file(sq)
            if f not in my_pawn_files and f not in opp_pawn_files:
                score += sign * OPEN_FILE_BONUS
            elif f not in my_pawn_files:
                score += sign * SEMI_OPEN_FILE_BONUS

    # Pawn structure
        
    for color, sign in ((chess.WHITE, +1), (chess.BLACK, -1)):
        pawns = list(board.pieces(chess.PAWN, color))
        files = [chess.square_file(sq) for sq in pawns]

        file_counts = {}
        for f in files:
            file_counts[f] = file_counts.get(f, 0) + 1
        for cnt in file_counts.values():
            if cnt > 1:
                score -= sign * DOUBLED_PAWN_PENALTY * (cnt - 1)

        my_pawn_files = set(files)
        opp = chess.BLACK if color == chess.WHITE else chess.WHITE
        opp_pawns = board.pieces(chess.PAWN, opp)

        for sq in pawns:
            f = chess.square_file(sq)
            r = chess.square_rank(sq)

            left_has = (f - 1) in my_pawn_files
            right_has = (f + 1) in my_pawn_files
            if not left_has and not right_has:
                score -= sign * ISOLATED_PAWN_PENALTY

            is_passed = True
            if color == chess.WHITE:
                ahead_ranks = range(r + 1, 8)
                rank_to_index = lambda rr: rr
            else:
                ahead_ranks = range(r - 1, -1, -1)
                rank_to_index = lambda rr: 7 - rr

            for rr in ahead_ranks:
                for ff in (f - 1, f, f + 1):
                    if 0 <= ff <= 7:
                        if chess.square(ff, rr) in opp_pawns:
                            is_passed = False
                            break
                if not is_passed:
                    break
            if is_passed:
                rr = rank_to_index(r)
                score += sign * PASSED_PAWN_BONUS_BY_RANK[rr]

    return score


def eval_to_play(board):
    s = evaluate(board)
    s += TEMPO_BONUS if board.turn == chess.WHITE else -TEMPO_BONUS
    return s if board.turn == chess.WHITE else -s


# ===== MOVE ORDERING =====

def ordered_moves(board):

    # TT caching

    entry = TT.get(zobrist_hash(board))
    tt_move = entry[3] if entry else None

    # Heuristic sorting

    moves = []

    for m in board.legal_moves:
        score = 0
        if board.is_capture(m):

            victim = board.piece_type_at(m.to_square)
            if victim is None and board.is_en_passant(m):
                victim = chess.PAWN

            attacker = board.piece_type_at(m.from_square)
            if victim:
                score += 10000 + PIECE_VALUES[victim] - PIECE_VALUES[attacker]

        if m.promotion:
            score += 5000 + PIECE_VALUES.get(m.promotion, 0)

        if tt_move is not None and m == tt_move:
            score += 5000

        if board.gives_check(m):
            score += 50

            if not board.is_capture(m) and not m.promotion:
                board.push(m)
                to_sq = m.to_square
                mover = not board.turn
                opp = board.turn
                hanging = (board.is_attacked_by(opp, to_sq) and not board.is_attacked_by(mover, to_sq))
                board.pop()
                if hanging:
                    continue

        moves.append((score, m))

    moves.sort(key=lambda item: item[0], reverse=True)

    ordered = []

    for score, move in moves:
        ordered.append(move)

    return ordered


# ===== TRANSPOSITION TABLE CACHING =====

EXACT, LOWER, UPPER = 0, 1, 2
TT = {}
MAX_TT_SIZE = 200000

def tt_probe(board, depth, alpha, beta):
    key = zobrist_hash(board)
    entry = TT.get(key)
    if not entry:
        return None
    score, edepth, flag, move = entry
    if edepth < depth:
        return None
    
    if flag == EXACT:
        return score
    if flag == LOWER and score >= beta:
        return score
    if flag == UPPER and score <= alpha:
        return score
    return None

def tt_store(board, depth, score, alpha0, beta, best_move):
    key = zobrist_hash(board)
    flag = EXACT
    if score <= alpha0:
        flag = UPPER
    elif score >= beta:
        flag = LOWER

    if key in TT:
        old_score, old_depth, _, _ = TT[key]
        if depth >= old_depth:
            TT[key] = (score, depth, flag, best_move)
        return
    
    if len(TT) >= MAX_TT_SIZE:
        TT.pop(next(iter(TT)))

    TT[key] = (score, depth, flag, best_move)


# ===== QUIESCENCE SEARCH =====

def qsearch(board, alpha, beta):

    if board.is_checkmate():
        return -99999
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_threefold_repetition():
        return 0

    if board.is_check():
        best = -math.inf
        for move in board.legal_moves:
            board.push(move)
            score = -qsearch(board, -beta, -alpha)
            board.pop()
            if score >= beta:
                return beta
            if score > best:
                best = score
            if score > alpha:
                alpha = score
        return best

    stand_pat = eval_to_play(board)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    for move in ordered_moves(board):
        if not (board.is_capture(move) or move.promotion):
            continue
        board.push(move)
        score = -qsearch(board, -beta, -alpha)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


# ===== MOVE SEARCH AND SELECTION =====

def search(board, depth, alpha, beta):
    """Returns score from side-to-move's point of view"""

    # Quiescence search when depth hits 0

    if depth == 0 or board.is_game_over():
        return qsearch(board, alpha, beta)

    # TT probe

    cached = tt_probe(board, depth, alpha, beta)
    if cached is not None:
        return cached
    
    # Search with alpha-beta pruning

    alpha0 = alpha
    best = -math.inf
    best_move = None

    for move in ordered_moves(board):
        board.push(move)
        score = -search(board, depth - 1, -beta, -alpha)
        board.pop()

        if score > best:
            best = score
            best_move = move
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best == -math.inf:
        best = eval_to_play(board)

    tt_store(board, depth, best, alpha0, beta, best_move)

    return best


def best_move(board, depth):
    """Pick the best move at the root and return (move, score)."""
    alpha, beta = -math.inf, math.inf
    best = None
    best_score = -math.inf

    for move in ordered_moves(board):
        board.push(move)
        score = -search(board, depth - 1, -beta, -alpha)
        board.pop()

        if score > best_score:
            best_score, best = score, move
        if score > alpha:
            alpha = score

    return best, best_score


# ===== SEARCH EVAL FOR CLI DISPLAY =====

def white_eval_after_move(board, depth_white, depth_black):

    depth = depth_white if board.turn == chess.WHITE else depth_black
    s = search(board, depth, -math.inf, math.inf)

    return s if board.turn == chess.WHITE else -s


def show_eval(board, depth_white, depth_black):
    static_white = evaluate(board)
    search_white = white_eval_after_move(board, depth_white, depth_black)
    turn_str = "White" if board.turn else "Black"

    print(f"[{turn_str} to move] static: {static_white:+} cp | search: {search_white:+} cp")


# ===== CLI =====

def play_cli(depth_white=3, depth_black=3, engine_plays_white=False):

    board = chess.Board()
    print(board, "\n")
    while not board.is_game_over():
        engine_turn = (board.turn == chess.WHITE and engine_plays_white) or (board.turn == chess.BLACK and not engine_plays_white)
        if engine_turn:
            depth = depth_white if board.turn == chess.WHITE else depth_black
            move, score = best_move(board, depth=depth)
            if move is None:
                break
            print(f"Engine ({'White' if board.turn else 'Black'}) plays: {board.san(move)}")
            board.push(move)

            show_eval(board, depth_white, depth_black)
            
        else:
            user = input("Your move: ").strip()
            try:
                board.push_san(user)
                show_eval(board, depth_white, depth_black)
            except:
                print("Illegal/unknown move, try again.")
                continue
        print(board, "\n")

    print("Game over:", board.result())


# ===== ENGINE SELF-PLAY (PGN OUTPUT) =====

def self_play_to_pgn(
    n_games=8,
    depth_white=3,
    depth_black=3,
    ply_limit=300,
    base_dir="testing/self_play",
    white_name="Engine (White)",
    black_name="Engine (Black)",
    event="Self-Play",
    annotate_eval=True
):
    """Run self-play for n_games and save each game in PGN format"""


    os.makedirs(base_dir, exist_ok=True)
    out_path = os.path.join(base_dir, "selfplay.pgn")

    results = {"1-0": 0, "0-1": 0, "1/2-1/2": 0}

    for game_index in range(1, n_games + 1):
        print(f"\n=== Starting Game {game_index}/{n_games} ===")
        board = chess.Board()
        game = chess.pgn.Game()

        game.headers["Event"] = event
        game.headers["Site"] = "Local"
        game.headers["Date"] = datetime.now(timezone.utc).strftime("%Y.%m.%d")
        game.headers["Round"] = str(game_index)
        game.headers["White"] = white_name
        game.headers["Black"] = black_name

        node = game
        ply = 0
        TT.clear()

        while not board.is_game_over() and ply < ply_limit:
            print(f"Move {ply+1} | {'White' if board.turn else 'Black'} thinking...")
            start = time.time()

            depth = depth_white if board.turn == chess.WHITE else depth_black
            move, _ = best_move(board, depth=depth)
            if move is None:
                print("No legal move found — terminating early.")
                break

            san = board.san(move)
            board.push(move)

            eval_cp = white_eval_after_move(board, depth_white, depth_black)
            node = node.add_variation(move)

            elapsed = time.time() - start
            print(f"→ {san} ({eval_cp:+} cp) in {elapsed:.2f}s")

            if annotate_eval:
                node.comment = f"eval {eval_cp:+} cp"

            ply += 1

        result = board.result() if board.is_game_over() else "1/2-1/2"
        results[result] = results.get(result, 0) + 1
        game.headers["Result"] = result

        with open(out_path, "a", encoding="utf-8") as f:
            exporter = chess.pgn.FileExporter(f)
            game.accept(exporter)
            f.write("\n\n")

        print(f"Game {game_index} finished ({result})")


    total = sum(results.values())
    wins = results.get("1-0", 0)
    losses = results.get("0-1", 0)
    draws = results.get("1/2-1/2", 0)

    print("\n=== Summary ===")
    print(f"Total games: {total}")
    print(f"W-D-L: {wins}-{draws}-{losses}")
    print(f"PGN: {out_path}")

    return out_path



# ===== UCI (UNIVERSAL CHESS INTERFACE) LOOP =====

def uci_loop():
    import sys
    board = chess.Board()

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()

        if line == "uci":
            print("id name Max's Engine")
            print("id author Massimo Revelli")
            print("uciok")
            sys.stdout.flush()

        elif line == "isready":
            print("readyok")
            sys.stdout.flush()

        elif line.startswith("ucinewgame"):
            TT.clear()
            board = chess.Board()

        elif line.startswith("position"):
            parts = line.split()
            if "startpos" in parts:
                board = chess.Board()
                idx = parts.index("startpos") + 1
                if idx < len(parts) and parts[idx] == "moves":
                    for mv in parts[idx+1:]:
                        board.push_uci(mv)
            elif "fen" in parts:
                fen_index = parts.index("fen") + 1
                fen = " ".join(parts[fen_index:fen_index+6])
                board = chess.Board(fen)
                rest = parts[fen_index+6:]
                if rest and rest[0] == "moves":
                    for mv in rest[1:]:
                        board.push_uci(mv)

        elif line.startswith("go"):
            depth = 3
            parts = line.split()
            if "depth" in parts:
                try:
                    depth = int(parts[parts.index("depth")+1])
                except:
                    pass
            move, score = best_move(board, depth=depth)
            if move is None:
                print("bestmove 0000")
            else:
                print(f"bestmove {move.uci()}")
            sys.stdout.flush()

        elif line == "quit":
            break

if __name__ == "__main__":
    import sys, os

    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "selfplay"

    dw = int(os.getenv("DEPTH_WHITE", "3"))
    db = int(os.getenv("DEPTH_BLACK", "3"))
    ply_limit = int(os.getenv("PLY_LIMIT", "300"))
    base_dir = os.getenv("OUT_DIR", "testing/self_play")
    engine_plays_white = os.getenv("ENGINE_PLAYS_WHITE", "0").lower() in ("1", "true", "yes", "y")
    n_games = int(os.getenv("N_GAMES", "1"))


    if mode == "cli":
        play_cli(depth_white=dw, depth_black=db, engine_plays_white=engine_plays_white)

    elif mode == "selfplay":
        self_play_to_pgn(
            n_games=n_games,
            depth_white=dw,
            depth_black=db,
            ply_limit=ply_limit,
            base_dir = base_dir
        )

    elif mode == "uci":
        uci_loop()

    elif mode in ("-h", "--help", "help"):
        print(
            "Usage: python chess_engine.py [cli|selfplay|uci]\n"
            "Vars (optional):\n"
            "  DEPTH_WHITE, DEPTH_BLACK (default 3)\n"
            "  ENGINE_PLAYS_WHITE=1|0 (CLI only, default 0)\n"
            "  N_GAMES (selfplay only, default 1)\n"
            "  PLY_LIMIT (selfplay only, default 300)\n"
            "  OUT_DIR (selfplay only, default testing/self_play)\n"
        )
    else:
        print("Unknown mode. Use one of: cli, selfplay, uci (or --help)")