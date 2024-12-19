import random
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt

ranking_final=[]
tuplas_comparaciones=[]
diccionario_resultados={}
perdedores=[]
contador_comparaciones=0
def torneo_recursivo(numeros):
    global perdedores,ranking_final,contador_comparaciones
    ganadores=[]
    random.shuffle(numeros)  # Barajamos los números para simular aleatoriedad
    while len(numeros) > 1:
        # Emparejamos a los números dos a dos
        num1 = numeros.pop()
        num2 = numeros.pop()
        
        if ((num1,num2) not in tuplas_comparaciones) and ((num2,num1) not in tuplas_comparaciones):
            tuplas_comparaciones.append((num1,num2))
            if num1 > num2:
                contador_comparaciones+=1
                ganadores.append(num1)
                perdedores.append(num2)
                diccionario_resultados[(num1,num2)]=num1
            else:
                contador_comparaciones+=1
                ganadores.append(num2)
                perdedores.append(num1)
                diccionario_resultados[(num1,num2)]=num2
        else:
            if (num1,num2) in diccionario_resultados:
                ganador_comparacion=diccionario_resultados[(num1,num2)]
                if ganador_comparacion == num1:
                    ganadores.append(num1)
                    perdedores.append(num2)
                else:
                    ganadores.append(num2)
                    perdedores.append(num1)
            elif (num2,num1) in diccionario_resultados:
                ganador_comparacion=diccionario_resultados[(num2,num1)]
                if ganador_comparacion == num1:
                    ganadores.append(num1)
                    perdedores.append(num2)
                else:
                    ganadores.append(num2)
                    perdedores.append(num1)
    if len(numeros) == 1:  # Si hay un número impar, se pasa automáticamente a la siguiente ronda
        ganadores.append(numeros.pop())
    if len(ganadores) > 1:
        torneo_recursivo(ganadores)
    else:
        if len(ganadores) > 0:
            ranking_final.append(ganadores[0])
            p=perdedores
            perdedores=[]
            torneo_recursivo(p)
        

datos=[]
medias=[]
# Ejemplo de uso:
numero_repeticiones=1000
suma_porcentajes_repetidos=0
suma_comparaciones=0
for num in range(20,4,-1):
    for i in range(numero_repeticiones):
        numeros = random.sample(range(1, 101), num)
        #print("Lista original: ", numeros)
        torneo_recursivo(numeros)
        #print("Ranking final (de mayor a menor):", ranking_final)
        ranking_final=[]

        # Normalizamos las tuplas para que el orden de los elementos no importe
        # Por ejemplo, (54, 1) y (1, 54) se consideran iguales
        tuplas_normalizadas = [tuple(sorted(tupla)) for tupla in tuplas_comparaciones]

        # Contamos cuántas veces aparece cada tupla normalizada
        contador = Counter(tuplas_normalizadas)

        # Identificamos las tuplas repetidas
        tuplas_repetidas = {tupla: cuenta for tupla, cuenta in contador.items() if cuenta > 1}

        # Imprimimos los resultados
        #print("Tuplas repetidas:")
        for tupla, cuenta in tuplas_repetidas.items():
            print(f"{tupla} aparece {cuenta} veces.")

        #Contamos cuantas veces se repite un elemento en comparaciones consecutivas:
        contador_consecutivas=0
        
        for i in range(0,len(tuplas_comparaciones)-1):
            tupla_izq=tuplas_comparaciones[i]
            tupla_der=tuplas_comparaciones[i+1]
            if (tupla_izq[0] in tupla_der) or (tupla_izq[1] in tupla_der):
                contador_consecutivas+=1
        tuplas_comparaciones=[]
        #print(f'Para {num} elementos se repiten elementos en comparaciones consecutivas {contador_consecutivas} veces en {contador_comparaciones} comparaciones')
        porcentaje_repetidos=(contador_consecutivas*100)/contador_comparaciones
        suma_porcentajes_repetidos+=porcentaje_repetidos
        suma_comparaciones+=contador_comparaciones
        datos.append({
            "elementos": num,
            "repetidos_comp_consecutivas": contador_consecutivas,
            "comparaciones": contador_comparaciones,
            "porcentaje_repetidos": porcentaje_repetidos
        })
        contador_comparaciones=0
    medias.append({
        "elementos":num,
        "media_porcentaje": suma_porcentajes_repetidos/numero_repeticiones,
        "media_comparaciones": suma_comparaciones/numero_repeticiones
    })
    suma_porcentajes_repetidos=0
    suma_comparaciones=0
    

#print(datos)        
tabla=pd.DataFrame(datos)
tabla_medias=pd.DataFrame(medias)
#print(tabla_medias)

#Tabla que representa el porcentaje de comparaciones por numero de elementos
#Eje X: numero de elementos, Eje Y: Porcentaje de repeticiones en comparaciones consecutivas
plt.figure(figsize=(10, 6))
plt.plot(tabla_medias['elementos'], tabla_medias['media_porcentaje'], marker='o', color='b', label='Porcentaje de repetidos')
plt.xlabel('Numero de elementos (N)')
plt.ylabel('Porcentaje de repeticiones en comparaciones consecutivas (%)')
plt.title('Tendencia de las repeticiones de elementos en comparaciones consecutivas')
plt.legend()
plt.grid(True)
plt.show()

#Eje X: numero de elementos, Eje Y: Media de comparaciones
plt.figure(figsize=(10, 6))
plt.plot(tabla_medias['elementos'], tabla_medias['media_comparaciones'], marker='o', color='b', label='Comparaciones por elementos')
plt.xlabel('Numero de elementos (N)')
plt.ylabel('Número medio de comparaciones')
plt.title('Tendencia de comparaciones')
plt.legend()
plt.grid(True)
plt.show()




