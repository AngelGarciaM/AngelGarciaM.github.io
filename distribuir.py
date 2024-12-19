import math
from collections import defaultdict
import random

def distribute_reviews_uniform(elements, num_correctors):
    # Calculamos cuántas veces como mínimo tiene que corregirse cada elemento
    num_min_correcciones = (num_correctors // 2) + 1 if num_correctors % 2 == 0 else math.ceil(num_correctors / 2)

    # Creamos una lista auxiliar donde los elementos se repiten `num_min_correcciones` veces
    elementos_repetidos = []
    for _ in range(num_min_correcciones):
        elementos_repetidos += elements

    # Creamos un diccionario para cada corrector
    diccionario = {f'Corrector {i}': [] for i in range(num_correctors)}

    lista_keys = list(diccionario.keys())
    i = 0

    while len(elementos_repetidos) > 0:
        if i > len(lista_keys) - 1:
            i = 0  # Volver al primer corrector si llegamos al último
        
        corrector = lista_keys[i]
        lista = diccionario[corrector]
        contains = False
        intentos = 0  # Contador de intentos para evitar bucles infinitos

        while not contains:
            if intentos > len(elementos_repetidos):  # Si todos los elementos ya están en la lista, salir
                print(f"No se pueden asignar más elementos únicos al {corrector}.")
                break
            
            # Generar un índice aleatorio
            numero_aleatorio = random.randint(0, len(elementos_repetidos) - 1)
            elemento = elementos_repetidos[numero_aleatorio]
            
            if elemento not in lista:
                lista.append(elemento)  # Añadir el elemento a la lista del corrector
                elementos_repetidos.pop(numero_aleatorio)  # Eliminar el elemento de la lista repetida
                diccionario[corrector] = lista  # Actualizar el diccionario
                contains = True  # Salir del bucle
            else:
                intentos += 1  # Incrementar intentos si el elemento ya estaba en la lista
        
        i += 1  # Pasar al siguiente corrector
    
    return diccionario

        
        
def count_reviewers(corrector_assignments, elements):
    """
    Contar cuántos correctores han revisado cada elemento.
    
    Args:
        corrector_assignments (dict): Diccionario con listas asignadas a cada corrector.
        elements (list): Lista de elementos distribuidos.
    
    Returns:
        dict: Diccionario con el conteo de correctores por elemento.
    """
    corrector_count_per_element = {element: 0 for element in elements}
    for assignments in corrector_assignments.values():
        for element in assignments:
            corrector_count_per_element[element] += 1
    return corrector_count_per_element


elements = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
num_correctors = 3 # Cambiar para ajustar el número de correctores

result = distribute_reviews_uniform(elements, num_correctors)
corrector_count_per_element = count_reviewers(result, elements)
for corrector, assignments in result.items():
    print(f"{corrector}: {assignments}")

# Mostrar conteo de correctores por elemento
print("\nNúmero de correctores por elemento:")
for element, count in corrector_count_per_element.items():
    print(f"Elemento {element}: {count} correctores")
