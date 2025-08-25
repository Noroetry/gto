import itertools

RANKS = "23456789TJQKA"
SUITS = "shdc"  
DECK = [r + s for r in RANKS for s in SUITS]

def generate_boards(dead_cards):
    available_deck = [c for c in DECK if c not in dead_cards]
    return itertools.combinations(available_deck, 5)


def best_hand(cards7):
    # TODO: implementar ranking real de 5 cartas
    return len("".join(cards7))  # <- dummy

def compute_equity(hero, villain, max_boards=None):
    dead = hero + villain
    wins = ties = losses = 0
    total = 0

    for i, board in enumerate(generate_boards(dead)):
        best_hero = best_hand(hero + list(board))
        best_villain = best_hand(villain + list(board))

        if best_hero > best_villain:
            wins += 1
        elif best_hero < best_villain:
            losses += 1
        else:
            ties += 1
        total += 1

        if max_boards and i + 1 >= max_boards:
            break

    equity = (wins + 0.5 * ties) / total if total > 0 else 0
    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "total": total,
        "equity": equity,
    }


# -------------------
# 5. Ejemplo de uso
# -------------------
if __name__ == "__main__":
    hero = ["As", "Ks"]
    villain = ["9c", "9d"]

    result = compute_equity(hero, villain, max_boards=1000)  # limitar boards para test
    print("Resultados de testeo:")
    print(result)
