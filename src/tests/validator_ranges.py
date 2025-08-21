# poker_validator.py

from src.tables.btn_ranges import btn_ranges
from src.tables.bb_ranges import bb_ranges

def check_ranges(ranges_dict, name):
    is_valid = True
    errors = []

    # Iterar sobre las manos y sus acciones, independientemente de la anidación
    if isinstance(ranges_dict, dict):
        for key, value in ranges_dict.items():
            if isinstance(value, dict) and 'RAISE' in value or 'CALL' in value:
                total_frequency = sum(value.values())
                if round(total_frequency, 3) != 1.0:
                    errors.append(f"❌ Error en la mano '{key}'. Suma de frecuencias: {total_frequency} (debe ser 1.0)")
                    is_valid = False
            else:
                is_valid_nested, nested_errors = check_ranges(value, key)
                is_valid = is_valid and is_valid_nested
                errors.extend(nested_errors)

    if not errors:
        print(f"✅ ¡La validación para {name} ha sido exitosa! Todas las sumas dan 1.0.")
    else:
        print(f"--- Errores en la validación de {name} ---")
        for error in errors:
            print(error)
        print("------------------------------------------")
    return is_valid, errors

if __name__ == '__main__':
    # Validar btn_ranges
    print("--- Validando el rango de BTN (OR) ---")
    check_ranges(btn_ranges['OR'], 'btn_ranges')

    print("\n--- Validando el rango de BB (CC) ---")
    check_ranges(bb_ranges['CC']['BTN'], 'bb_ranges')