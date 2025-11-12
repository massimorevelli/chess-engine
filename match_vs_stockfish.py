import sys, os
import chess, chess.pgn, chess.engine
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.abspath(__file__))  # /chess-engine/

STOCKFISH = os.path.join(ROOT, "testing", "stockfish.exe")
MAX = [sys.executable, os.path.join(ROOT, "chess_engine.py")]

GAMES = 24
MAX_DEPTH = 3
SF_ELO = 2300


def main():

    sf = chess.engine.SimpleEngine.popen_uci(STOCKFISH)
    sf.configure({
        "UCI_LimitStrength": True,
        "UCI_Elo": SF_ELO,
        "Threads": 1,
        "Hash": 16,
    })

    max = chess.engine.SimpleEngine.popen_uci(MAX)

    print("Engines:")
    print("  Stockfish:", sf.id)
    print("  Max's Engine :", max.id)

    PGN_DIR = os.path.join(ROOT, "testing", "pgn_vs_stockfish")
    os.makedirs(PGN_DIR, exist_ok=True)

    max_white_wins = 0
    max_white_draws = 0
    max_white_losses = 0

    max_black_wins = 0
    max_black_draws = 0
    max_black_losses = 0

    for i in range(GAMES):
        board = chess.Board()
        white, black = (sf, max) if i % 2 == 0 else (max, sf)

        now = datetime.now(timezone.utc)

        game = chess.pgn.Game()
        game.headers["Event"] = "Match: Max's Engine vs Stockfish"
        game.headers["Site"] = "Local"
        game.headers["Date"] = now.strftime("%Y.%m.%d")
        game.headers["Time"] = now.strftime("%H:%M:%S")
        game.headers["Round"] = str(i + 1)

        STOCKFISH_NAME = f"Stockfish (Elo {SF_ELO})"
        MAX_NAME = f"Max's Engine (Depth {MAX_DEPTH})"

        game.headers["White"] = STOCKFISH_NAME if white is sf else MAX_NAME
        game.headers["Black"] = MAX_NAME if black is max else STOCKFISH_NAME
        node = game

        limit_sf = chess.engine.Limit(time=0.5)
        limit_max = chess.engine.Limit(depth=MAX_DEPTH)
        

        print(f"\nGame {i+1} of {GAMES}: White = {game.headers['White']}  Black = {game.headers['Black']}", flush=True)

        while not board.is_game_over(claim_draw=True):
            eng = white if board.turn == chess.WHITE else black
            limit = limit_sf if eng is sf else limit_max

            try:
                res = eng.play(board, limit)
            except chess.engine.EngineTerminatedError:
                loser_is_white = (board.turn == chess.WHITE)
                result = "0-1" if loser_is_white else "1-0"
                game.headers["Result"] = result
                game.headers["Termination"] = "abandoned"
                print(f"Engine crash: {'White' if loser_is_white else 'Black'} forfeits.")
                break

            if res.move is None or res.move == chess.Move.null():
                loser_is_white = (board.turn == chess.WHITE)
                result = "0-1" if loser_is_white else "1-0"
                game.headers["Result"] = result
                game.headers["Termination"] = "resignation"
                print(f"{board.fullmove_number}{'.' if board.turn else '...'} -- "
                    f"({'White' if board.turn else 'Black'} resigns)")
                break

            san = board.san(res.move)
            prefix = f"{board.fullmove_number}." if board.turn else f"{board.fullmove_number}..."
            print(f"{prefix} {san} ({'White' if board.turn else 'Black'})", flush=True)

            board.push(res.move)
            node = node.add_variation(res.move)

        if game.headers.get("Result", "*") == "*":
            game.headers["Result"] = board.result(claim_draw=True)

        path = os.path.join(PGN_DIR, f"game_{i+1}.pgn")
        with open(path, "w", encoding="utf-8") as f:
            print(game, file=f)
        
        result_str = game.headers["Result"]
        white_name = game.headers["White"]
        black_name = game.headers["Black"]

        max_plays_white = "Max's Engine" in white_name
        
        if result_str == "1-0":
            winner = white_name
            if not max_plays_white:
                max_black_losses += 1
            else:
                max_white_wins +=1
        elif result_str == "0-1":
            winner = black_name
            if max_plays_white:
                max_white_losses += 1
            else:
                max_black_wins += 1
        else:
            winner = "Draw"
            if max_plays_white:
                max_white_draws += 1
            else:
                max_black_draws += 1

        print(f"Result: {result_str}  |  Winner: {winner}  (saved {path})")

    sf.quit()
    max.quit()

    max_wins = max_white_wins + max_black_wins
    draws = max_white_draws + max_black_draws
    sf_wins = GAMES - max_wins - draws

    max_score = max_wins + 0.5*draws
    sf_score = sf_wins + 0.5*draws

    print("\n=== Final summary ===")
    print(f"Games: {GAMES}")
    print(f"\nW-D-L for Max's Engine: {max_wins} - {draws} - {sf_wins}")

    print(f"\nMax's Engine: Score {max_score:.1f} / {GAMES}")
    print(f"Stockfish: Score {sf_score:.1f} / {GAMES}")

    print("\n=== Per-color performance (Max's Engine) ===")

    games_as_white = max_white_wins + max_white_draws + max_white_losses
    games_as_black = max_black_wins + max_black_draws + max_black_losses

    if games_as_white:
        white_winrate = 100.0 * max_white_wins / games_as_white
        print(f"White: W-D-L = {max_white_wins}-{max_white_draws}-{max_white_losses} "
            f"({white_winrate:.1f}% wins over {games_as_white} games)")
        
    if games_as_black:
        black_winrate = 100.0 * max_black_wins / games_as_black
        print(f"Black: W-D-L = {max_black_wins}-{max_black_draws}-{max_black_losses} "
            f"({black_winrate:.1f}% wins over {games_as_black} games)")

if __name__ == "__main__":
    main()