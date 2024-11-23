# -*- coding: utf-8 -*-

# Importa librería numpy como np
import numpy as np

# Importa clase Union de typing para hint
from typing import Union

#
#

def get_verifier(number: Union[int, str]) -> str:
    '''
    Calcula el dígito verificador de un correlativo de RUT de acuerdo con el
    algoritmo Módulo 11 utilizado en Chile.

    Parámetros
        number (int, str): Correlativo de RUT al que calcular el dígito verificador.
    
    Retorno
        str: El dígito verificador del correlativo pasado como argumento.
    '''

    # Convierte el correlativo en un array de int
    number_array = np.array(list(str(number)), dtype=int)

    # Define array con los factores de ponderación base de cada dígito del correlativo
    base_weights = np.array([2, 3, 4, 5, 6, 7])

    # Los factores de ponderación se repiten en ciclo hasta completar el largo de dígitos
    # del correlativo. Entonces, se crea un array con los factores de podenración, los que
    # se repiten hasta completar el largo de dígitos del correlativo. Ejemplo: La lista base
    # de factores es base = [2, 3, 4, 5, 6, 7] (len 6). Si el correlativo es 18.854.962, entonces
    # como lista de dígitos es rut = [1, 8, 8, 5, 4, 9, 6, 2] (len 8). Como la cantidad de dígitos
    # del correlativo es más larga que la lista base de factores, entonces se repiten en ciclo los
    # factores hasta completar el mismo largo factores = [2, 3, 4, 5, 6, 7, 2, 3] (len 8).
    weights = np.tile(base_weights, (number_array.shape[0] // base_weights.shape[0] + 1))[:number_array.shape[0]]

    # Suma del producto de los factores de ponderación y dígitos del correlativo.
    # Notar que el producto de ambos array es tomando los dígitos del correlativo
    # en forma invertida. Usando el ejemplo anterior, rut_inv = [2, 6, 9, 4, 5, 8, 8, 1].
    # Luego, sum(rut_inv * factores).
    product_sum = (np.flip(number_array) * weights).sum()

    # Se calcula la diferencia entre 11 y el resto del cociente entre la suma del producto con 11
    verifier = str(11 - product_sum % 11)

    # Si la operación anterior es "10", el verificador es "K". Si es "11", el verificador es "0".
    # En cualquier otro caso, es solo el resultado de la operación
    verifier = {'10': 'K', '11': '0'}.get(verifier, verifier)
    
    # Retorna el dígito verificador como str
    return verifier