import random
import itertools
from collections import Counter
from src.tables.preflop_ranges import preflop_ranges


# --- Normalización de manos ---
def normalize_hand(card1, card2, suited=None):
    ranks = '23456789TJQKA'
    # Mayor valor siempre a la izquierda
    if ranks.index(card1) > ranks.index(card2):
        high, low = card1, card2
    else:
        high, low = card2, card1

    if suited is True:
        return f"{high}{low}s"
    elif suited is False:
        return f"{high}{low}o"
    else:
        return f"{high}{low}"  # parejas


# --- Generación de todas las combinaciones ---
def get_all_hands():
    ranks = '23456789TJQKA'
    suited_combinations = [normalize_hand(c1, c2, suited=True) for c1, c2 in itertools.combinations(ranks, 2)]
    offsuit_combinations = [normalize_hand(c1, c2, suited=False) for c1, c2 in itertools.combinations(ranks, 2)]
    pairs = [normalize_hand(c, c) for c in ranks]
    
    return suited_combinations + offsuit_combinations + pairs


# --- Formateo de mano individual (por si acaso) ---
def format_hand(hand_str):
    # En caso de que el string ya venga correcto, lo devolvemos
    if len(hand_str) in (2, 3):
        return hand_str
    return hand_str


# --- Main Loop ---
def main():
    # Todas las posiciones excepto BB (no se abre desde Big Blind)
    all_positions = [pos for pos in preflop_ranges.keys() if pos != "BB"]
    all_hands = get_all_hands()
    stats = Counter()

    print("--- Entrenamiento de Rangos de Poker ---")
    print("Escribe 's' para abrir, 'n' para no abrir, o 'exit' para terminar.")
    print("---------------------------------------")

    while True:
        position = random.choice(all_positions)
        hand = random.choice(all_hands)
        
        formatted_hand = format_hand(hand)

        is_in_range = formatted_hand in preflop_ranges.get(position, set())
        
        user_input = input(f"{position} {formatted_hand}: ").strip().lower()

        if user_input == "exit":
            break
        
        if user_input not in ["s", "n"]:
            continue

        if user_input == "s" and is_in_range:
            print("¡Correcto! ✅")
            stats["aciertos"] += 1
        elif user_input == "n" and not is_in_range:
            print("¡Correcto! ✅")
            stats["aciertos"] += 1
        else:
            correct_action = "abrir" if is_in_range else "no abrir"
            print(f"¡Incorrecto! ❌ La respuesta correcta era: {correct_action} "
                  f"({formatted_hand} {'está' if is_in_range else 'no está'} en el rango de {position}).")
            stats["errores"] += 1
    
    print("\n--- Resultados ---")
    print(f"Aciertos: {stats['aciertos']}")
    print(f"Errores: {stats['errores']}")
    print("¡Gracias por entrenar! ¡Vuelve pronto! 🃏")
    if stats['aciertos'] + stats['errores'] > 0:
        print(f"Porcentaje de éxito: {stats['aciertos'] / (stats['aciertos'] + stats['errores']) * 100:.2f}%")


if __name__ == "__main__":
    main()
