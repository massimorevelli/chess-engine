import chess
from chess.polyglot import zobrist_hash
import math
import time
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


PHASE_WEIGHTS = {
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4,
}

MAX_PHASE = 24


# ===== PSTs =====


PAWN_MG_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     0, 10, 10,-20,-20, 10, 10,  0,
     5,  0,  0,  0,  0,  0,  0,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
]

PAWN_EG_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,-25,-25,  0,  0,  0,
    -5, -5,-10,-25,-25,-10, -5, -5,
    10, 10, 10, 10, 10, 10, 10, 10,
    20, 20, 20, 25, 25, 20, 20, 20,
    30, 30, 30, 30, 30, 30, 30, 30,
    70, 70, 70, 70, 70, 70, 70, 70,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_MG_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

KNIGHT_EG_TABLE = [
    -60,-60,-30,-25,-25,-30,-60,-60,
    -60,-20,-10, -5, -5,-10,-20,-60,
    -30,-10, 10, 20, 20, 10,-10,-30,
    -25, -5, 20, 25, 25, 20, -5,-25,
    -25, -5, 20, 25, 25, 20, -5,-25,
    -30,-10, 10, 20, 20, 10,-10,-30,
    -60,-20,-10, -5, -5,-10,-20,-60,
    -60,-60,-30,-25,-25,-30,-60,-60,
]

BISHOP_MG_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

BISHOP_EG_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5, 10, 15, 15, 10,  5,-10,
    -10, 10, 15, 20, 20, 15, 10,-10,
    -10, 10, 15, 20, 20, 15, 10,-10,
    -10,  5, 10, 15, 15, 10,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_MG_TABLE = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

ROOK_EG_TABLE = [
     0,  0,  5, 10, 10,  5,  0,  0,
     5, 10, 10, 15, 15, 10, 10,  5,
     0,  5, 10, 10, 10, 10,  5,  0,
     0,  5, 10, 15, 15, 10,  5,  0,
     0,  5, 10, 15, 15, 10,  5,  0,
     5, 10, 15, 20, 20, 15, 10,  5,
    20, 25, 30, 35, 35, 30, 25, 20,
     5, 10, 10, 15, 15, 10, 10,  5,
]

KING_MG_TABLE = [
     20, 35, 10,  0,  0, 10, 35, 20,
     20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
]

KING_EG_TABLE = [
    -50,-30,-20,-20,-20,-20,-30,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -20,-10, 20, 30, 30, 20,-10,-20,
    -20,  0, 30, 40, 40, 30,  0,-20,
    -20,  0, 30, 40, 40, 30,  0,-20,
    -20,-10, 20, 30, 30, 20,-10,-20,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -50,-30,-20,-20,-20,-20,-30,-50,
]

QUEEN_MG_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
      0,  0,  5,  5,  5,  5,  0,  0,
     -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

QUEEN_EG_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10, -5,  0,  5,  5,  0, -5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
     -5,  5, 10, 15, 15, 10,  5, -5,
     -5,  5, 10, 15, 15, 10,  5, -5,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10, -5,  0,  5,  5,  0, -5,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]


MG_PST = {
    chess.PAWN: PAWN_MG_TABLE,
    chess.KNIGHT: KNIGHT_MG_TABLE,
    chess.BISHOP: BISHOP_MG_TABLE,
    chess.ROOK: ROOK_MG_TABLE,
    chess.QUEEN: QUEEN_MG_TABLE,
    chess.KING: KING_MG_TABLE,
}


EG_PST = {
    chess.PAWN: PAWN_EG_TABLE,
    chess.KNIGHT: KNIGHT_EG_TABLE,
    chess.BISHOP: BISHOP_EG_TABLE,
    chess.ROOK: ROOK_EG_TABLE,
    chess.QUEEN: QUEEN_EG_TABLE,
    chess.KING: KING_EG_TABLE,
}


def game_phase(board):
    """
    Return the current game phase in [0, 1]
    """

    phase_points = 0

    for piece_type, weight in PHASE_WEIGHTS.items():
        phase_points += weight * len(
            board.pieces(piece_type, chess.WHITE)
        )
        phase_points += weight * len(
            board.pieces(piece_type, chess.BLACK)
        )

    return min(1.0, phase_points / MAX_PHASE)


def pst_value(piece_type, square, phase):
    """
    Blend middlegame and endgame PST values according to game phase
    """

    mg_value = MG_PST[piece_type][square]
    eg_value = EG_PST[piece_type][square]

    return round(
        phase * mg_value
        + (1.0 - phase) * eg_value
    )



# ===== STATIC BOARD EVALUATION =====

def evaluate(board):
    """Return a centipawn score from White's perspective"""
    
    score = 0

    if board.is_checkmate():
        return -99999 if board.turn else 99999
    
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_threefold_repetition():
        return 0


    phase = game_phase(board)
    
    # Material count + PST

    for piece_type, value in PIECE_VALUES.items():

        for sq in board.pieces(piece_type, chess.WHITE):
            score += value
            score += pst_value(
                piece_type,
                sq,
                phase
            )

        for sq in board.pieces(piece_type, chess.BLACK):
            score -= value
            score -= pst_value(
                piece_type,
                chess.square_mirror(sq),
                phase
            )

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
    """Legal move ordering for search efficiency"""

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

        moves.append((score, m))

    moves.sort(key=lambda item: item[0], reverse=True)

    ordered = []

    for score, move in moves:
        ordered.append(move)

    return ordered


def ordered_tactical_moves(board):
    """Order captures and promotions for quiescence search"""

    moves = []

    for move in board.legal_moves:

        if not (board.is_capture(move) or move.promotion):
            continue

        score = 0

        if board.is_capture(move):

            victim = board.piece_type_at(move.to_square)

            if victim is None and board.is_en_passant(move):
                victim = chess.PAWN

            attacker = board.piece_type_at(move.from_square)

            if victim is not None and attacker is not None:
                score += (
                    10000
                    + PIECE_VALUES[victim]
                    - PIECE_VALUES[attacker]
                )

        if move.promotion:
            score += (
                5000
                + PIECE_VALUES.get(move.promotion, 0)
            )

        moves.append((score, move))

    moves.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [move for _, move in moves]


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



# ===== SEARCH INSTRUMENTATION =====

SEARCH_STATS = {
    "nodes": 0,
    "qnodes": 0,
    "tt_probes": 0,
    "tt_hits": 0,
    "beta_cutoffs": 0,
    "q_beta_cutoffs": 0,
    "elapsed": 0.0,
    "nps": 0.0,
    "depth_reached": 0,
}


class SearchTimeout(Exception):
    """Raised when the search exceeds its allotted time"""
    pass


SEARCH_DEADLINE = None


def check_timeout():
    if (
        SEARCH_DEADLINE is not None
        and time.perf_counter() >= SEARCH_DEADLINE
    ):
        raise SearchTimeout


def reset_search_stats():
    for key in SEARCH_STATS:
        SEARCH_STATS[key] = 0


def finalize_search_stats(start_time, depth_reached):
    elapsed = time.perf_counter() - start_time

    SEARCH_STATS["elapsed"] = elapsed
    SEARCH_STATS["depth_reached"] = depth_reached

    total_nodes = SEARCH_STATS["nodes"] + SEARCH_STATS["qnodes"]

    SEARCH_STATS["nps"] = (
        total_nodes / elapsed
        if elapsed > 0
        else 0.0
    )


def get_search_stats():
    """Return a copy of the current search statistics"""
    return SEARCH_STATS.copy()


def print_search_stats(stats=None):
    """Print search statistics"""

    if stats is None:
        stats = SEARCH_STATS

    total_nodes = stats["nodes"] + stats["qnodes"]

    tt_hit_rate = (
        100 * stats["tt_hits"] / stats["tt_probes"]
        if stats["tt_probes"] > 0
        else 0.0
    )

    print(
        f"Search stats | "
        f"depth={stats['depth_reached']} | "
        f"nodes={stats['nodes']:,} | "
        f"qnodes={stats['qnodes']:,} | "
        f"total={total_nodes:,} | "
        f"TT hits={stats['tt_hits']:,}/{stats['tt_probes']:,} "
        f"({tt_hit_rate:.1f}%) | "
        f"cutoffs={stats['beta_cutoffs']:,} | "
        f"qcutoffs={stats['q_beta_cutoffs']:,} | "
        f"time={stats['elapsed']:.3f}s | "
        f"NPS={stats['nps']:,.0f}"
    )


def print_uci_info(score, stats=None):
    """Print search information using UCI protocol format"""

    if stats is None:
        stats = SEARCH_STATS

    total_nodes = stats["nodes"] + stats["qnodes"]
    elapsed_ms = int(stats["elapsed"] * 1000)

    print(
        f"info "
        f"depth {stats['depth_reached']} "
        f"score cp {int(score) if math.isfinite(score) else 0} "
        f"nodes {total_nodes} "
        f"nps {int(stats['nps'])} "
        f"time {elapsed_ms}"
    )
    
    print(
        f"info string maxstats "
        f"main_nodes={stats['nodes']} "
        f"qnodes={stats['qnodes']} "
        f"tt_probes={stats['tt_probes']} "
        f"tt_hits={stats['tt_hits']} "
        f"beta_cutoffs={stats['beta_cutoffs']} "
        f"q_beta_cutoffs={stats['q_beta_cutoffs']}"
    )



# ===== TIME MANAGEMENT =====

def calculate_time_budget(
    board,
    wtime_ms,
    btime_ms,
    winc_ms=0,
    binc_ms=0,
    movestogo=None
):
    """
    Calculate how many milliseconds the engine may spend on the current move
    """

    if board.turn == chess.WHITE:
        remaining_ms = wtime_ms
        increment_ms = winc_ms
    else:
        remaining_ms = btime_ms
        increment_ms = binc_ms

    if remaining_ms is None:
        return 2000

    # Reserve
    reserve_ms = max(50, int(0.05 * remaining_ms))
    usable_ms = max(1, remaining_ms - reserve_ms)


    estimated_moves = (
        movestogo
        if movestogo is not None and movestogo > 0
        else 30
    )

    base_ms = usable_ms / estimated_moves

    increment_bonus_ms = 0.8 * increment_ms

    budget_ms = base_ms + increment_bonus_ms

    if movestogo is None:
        max_budget_ms = 0.20 * usable_ms + increment_bonus_ms
        budget_ms = min(budget_ms, max_budget_ms)

    budget_ms = min(budget_ms, usable_ms)

    return max(1, int(budget_ms))



# ===== QUIESCENCE SEARCH =====

def qsearch(board, alpha, beta):
    """Quiescence search to avoid horizon effect"""

    check_timeout()
    SEARCH_STATS["qnodes"] += 1

    if board.is_checkmate():
        return -99999
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_threefold_repetition():
        return 0

    if board.is_check():
        best = -math.inf
        for move in board.legal_moves:

            board.push(move)
            try:
                score = -qsearch(board, -beta, -alpha)
            finally:
                board.pop()

            if score >= beta:
                SEARCH_STATS["q_beta_cutoffs"] += 1
                return beta
            if score > best:
                best = score
            if score > alpha:
                alpha = score
        return best

    stand_pat = eval_to_play(board)
    if stand_pat >= beta:
        SEARCH_STATS["q_beta_cutoffs"] += 1
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    for move in ordered_tactical_moves(board):

        board.push(move)
        try:
            score = -qsearch(board, -beta, -alpha)
        finally:
            board.pop()

        if score >= beta:
            SEARCH_STATS["q_beta_cutoffs"] += 1
            return beta
        if score > alpha:
            alpha = score

    return alpha


# ===== MOVE SEARCH AND SELECTION =====

def search(board, depth, alpha, beta):
    """Return score from side-to-move's point of view"""

    check_timeout()

    # Quiescence search when depth hits 0

    if depth == 0 or board.is_game_over():
        return qsearch(board, alpha, beta)

    SEARCH_STATS["nodes"] += 1

    # TT probe

    SEARCH_STATS["tt_probes"] += 1
    cached = tt_probe(board, depth, alpha, beta)

    if cached is not None:
        SEARCH_STATS["tt_hits"] += 1
        return cached
    
    # Search with alpha-beta pruning

    alpha0 = alpha
    best = -math.inf
    best_move = None

    for move in ordered_moves(board):
        board.push(move)
        try:
            score = -search(board, depth - 1, -beta, -alpha)
        finally:
            board.pop()

        if score > best:
            best = score
            best_move = move
        if best > alpha:
            alpha = best
        if alpha >= beta:
            SEARCH_STATS["beta_cutoffs"] += 1
            break

    if best == -math.inf:
        best = eval_to_play(board)

    tt_store(board, depth, best, alpha0, beta, best_move)

    return best


def _best_move_at_depth(board, depth, preferred_move=None):
    """Run one complete fixed-depth root search"""

    alpha, beta = -math.inf, math.inf
    best = None
    best_score = -math.inf

    moves = ordered_moves(board)

    if preferred_move is not None and preferred_move in moves:
        moves.remove(preferred_move)
        moves.insert(0, preferred_move)

    for move in moves:
        check_timeout()

        board.push(move)
        try:
            score = -search(
                board,
                depth - 1,
                -beta,
                -alpha
            )
        finally:
            board.pop()

        if score > best_score:
            best_score = score
            best = move

        if score > alpha:
            alpha = score

    return best, best_score


def best_move_fixed(board, depth):
    """Search exactly to the requested depth"""

    global SEARCH_DEADLINE

    reset_search_stats()
    SEARCH_DEADLINE = None

    start_time = time.perf_counter()

    move, score = _best_move_at_depth(board, depth)

    finalize_search_stats(
        start_time=start_time,
        depth_reached=depth
    )

    return move, score


def best_move_timed(board, time_limit=2.0, max_depth=20):
    """
    Iteratively deepen until the time limit expires
    """

    global SEARCH_DEADLINE

    reset_search_stats()

    start_time = time.perf_counter()
    SEARCH_DEADLINE = start_time + time_limit

    moves = ordered_moves(board)
    best = moves[0] if moves else None
    best_score = 0

    completed_depth = 0
    preferred_move = None

    try:
        for depth in range(1, max_depth + 1):

            move, score = _best_move_at_depth(
                board,
                depth,
                preferred_move=preferred_move
            )

            if move is None:
                break

            best = move
            best_score = score
            completed_depth = depth
            preferred_move = move

    except SearchTimeout:
        pass

    finally:
        SEARCH_DEADLINE = None

    finalize_search_stats(
        start_time=start_time,
        depth_reached=completed_depth
    )

    return best, best_score


# ===== EVAL FOR CLI DISPLAY =====


def show_eval(board):
    static_white = evaluate(board)
    turn_str = "White" if board.turn else "Black"

    print(
        f"[{turn_str} to move] "
        f"static evaluation: {static_white:+} cp"
    )


# ===== CLI =====

def play_cli(
    engine_plays_white=False,
    time_limit=2.0
):
    """Interactive interface"""

    board = chess.Board()
    print(board, "\n")
    while not board.is_game_over():
        engine_turn = (board.turn == chess.WHITE and engine_plays_white) or (board.turn == chess.BLACK and not engine_plays_white)
        if engine_turn:
            move, score = best_move_timed(
                board,
                time_limit=time_limit
            )
            move_stats = get_search_stats()
            if move is None:
                break
            print(f"Engine ({'White' if board.turn else 'Black'}) plays: {board.san(move)}")
            print_search_stats(move_stats)

            board.push(move)

            show_eval(board)
            
        else:
            user = input("Your move: ").strip()
            try:
                board.push_san(user)
            except ValueError:
                print("Illegal/unknown move, try again.")
                continue
            show_eval(board)
        print(board, "\n")

    print("Game over:", board.result())



# ===== UCI (UNIVERSAL CHESS INTERFACE) LOOP =====

def uci_loop():
    """Universal Chess Interface mode"""
    
    import sys
    board = chess.Board()

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()

        if line == "uci":
            print("id name Max's Engine v1.1")
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
            parts = line.split()

            # -------------------------------------------------
            # 1. Explicit fixed move time
            # -------------------------------------------------

            if "movetime" in parts:
                try:
                    movetime_ms = int(
                        parts[parts.index("movetime") + 1]
                    )
                except (ValueError, IndexError):
                    movetime_ms = 2000

                move, score = best_move_timed(
                    board,
                    time_limit=movetime_ms / 1000.0
                )

            # -------------------------------------------------
            # 2. Explicit fixed depth
            # -------------------------------------------------

            elif "depth" in parts:
                try:
                    depth = int(
                        parts[parts.index("depth") + 1]
                    )
                except (ValueError, IndexError):
                    depth = 3

                depth = max(1, depth)

                move, score = best_move_fixed(
                    board,
                    depth=depth
                )

            # -------------------------------------------------
            # 3. Chess-clock time management
            # -------------------------------------------------

            elif "wtime" in parts or "btime" in parts:

                def get_uci_int(name, default=0):
                    try:
                        return int(parts[parts.index(name) + 1])
                    except (ValueError, IndexError):
                        return default

                wtime_ms = (
                    get_uci_int("wtime", None)
                    if "wtime" in parts
                    else None
                )

                btime_ms = (
                    get_uci_int("btime", None)
                    if "btime" in parts
                    else None
                )

                winc_ms = (
                    get_uci_int("winc", 0)
                    if "winc" in parts
                    else 0
                )

                binc_ms = (
                    get_uci_int("binc", 0)
                    if "binc" in parts
                    else 0
                )

                movestogo = (
                    get_uci_int("movestogo", None)
                    if "movestogo" in parts
                    else None
                )

                budget_ms = calculate_time_budget(
                    board=board,
                    wtime_ms=wtime_ms,
                    btime_ms=btime_ms,
                    winc_ms=winc_ms,
                    binc_ms=binc_ms,
                    movestogo=movestogo
                )

                print(f"info string allocated time {budget_ms} ms")

                move, score = best_move_timed(
                    board,
                    time_limit=budget_ms / 1000.0
                )

            # -------------------------------------------------
            # 4. Fallback
            # -------------------------------------------------

            else:
                move, score = best_move_timed(
                    board,
                    time_limit=2.0
                )

            # UCI search information

            stats = get_search_stats()
            print_uci_info(score, stats)

            # UCI best move

            if move is None:
                print("bestmove 0000")
            else:
                print(f"bestmove {move.uci()}")

            sys.stdout.flush()

        elif line == "quit":
            break



if __name__ == "__main__":
    import sys, os

    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "uci"

    think_time = float(os.getenv("THINK_TIME", "2.0"))
    engine_plays_white = os.getenv("ENGINE_PLAYS_WHITE", "0").lower() in ("1", "true", "yes", "y")

    if mode == "cli":
        play_cli(
            engine_plays_white=engine_plays_white,
            time_limit=think_time
        )

    elif mode == "uci":
        uci_loop()

    elif mode in ("-h", "--help", "help"):
        print(
            "Usage: python chess_engine.py [cli|uci]\n"
            "Vars (optional):\n"
            "  ENGINE_PLAYS_WHITE=1|0 (CLI only, default 0)\n"
            "  THINK_TIME (CLI thinking time in seconds, default 2.0)\n"
        )
    else:
        print("Unknown mode. Use one of: cli, uci (or --help)")