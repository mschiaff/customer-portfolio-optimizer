# Prueba de Concepto (POC)

En esta sección se encuentra una POC desarrollada en Jupyter Notebook utilizando un dataset sintético como ejemplo. Todo el código de la POC se encuentra documentado dentro cada Jupyter Notebook.

## Tabla de Contenidos

- [Creación del dataset](#creación-del-dataset)
- [Modelo de optimización](#modelo-de-optimización)
- [Principales resultados y conclusiones](#principales-resultados-y-conclusiones)

## Creación del dataset

> :warning: DISCLAIMER: Es posible que algunos `Rut` correspondan a empresas reales en Chile, lo cual sólo sería una coincidencia, ya que, como se muestra en [1-Creacion_Dataset.ipynb](./1-Creacion_Dataset.ipynb), los datos fueron generados aleatoriamente, y la semilla aleatoria fue fijada para poder reproducir los resultados. Lo mismo aplica para los `Ingresos` de cada empresa.

Se crea un dataset con los campos de `Rut` e `Ingresos` para simular un caso de uso, donde contamos con 5.721 clientes empresas, con los respectivos ingresos que cada uno representa. Además, para agregarle una cuota de realismo, se calcula el dígito verificador de cada correlativo de `Rut`.

El campo de `Rut` es creado mediante la generación aleatoria de correlativos que siguen una distribución uniforme en el rango de $[50.000.000, 75.000.000]$. Luego, se calcula el dígito verificador de cada correlativo generado aleatoriamente aplicando el algoritmo [Módulo 11](https://es.wikipedia.org/wiki/Código_de_control), que es el utilizado en Chile, y su implementación encuentra dentro de este mismo repositorio ([Implementación Módulo 11](./lib/rut.py)).

El campo de `Ingresos` también es creado mediante la generación aleatoria de valores que siguen una distribución uniforme, pero en el rango de $[\$900.000, \$3.000.000]$.

Luego de mostrar alguna información y estadísticas básicas del dataset, este es exportado a un libro Excel que se encuentra en la carpeta [data](./data/) bajo el nombre `Dataset_Ejemplo.xlsx`.

## Modelo de optimización

El problema propuesto en este ejemplo es distribuir los 5.721 clientes y e ingresos generados aleatoriamente en 4 carteras diferentes, de tal manera que cada cartera concentre una cantidad similar de clientes e ingresos. El desarrollo completo, código, resultados y conclusiones se encuentra en el Jupyter Notebook [2-Modelo_Optimizacion.ipynb](./2-Modelo_Optimizacion.ipynb). Además, en la carpeta [results](./results/) se encuentra el libro Excel `Resultado_Ejemplo.xlsx` con el resultado de la asignación de clientes a cada cartera. También se encuentra el archivo `Modelo_Resultado.lp` con la definición completa del modelo.

## Principales resultados y conclusiones

El modelo planteado consigue asignar a casi todos los clientes entre las 4 carteras, quedando solo 5 sin asignar, los cuales pueden ser perfectamente asignados *"manualmente"*. Las 4 carteras terminan con exactamente la misma cantidad de clientes, y una suma de ingresos bastante similar entre cada una, presentando una desviación promedio de 0,2% respecto al promedio simple del total de ingresos sobre la cantidad de carteras, que vendría a ser el valor teórico ideal.

Con relación al desempeño, el modelo con holgura de ingresos ($h_{f}$) de $\$5.000.000$ converge a una solución óptima en 3 segundos, lo que representa una reducción de 98% en el tiempo de ejecución respecto al modelo con holgura de ingresos de $\$4.000.000$, sin generar un mayor perjuicio en la asignación de clientes e ingresos.

<table align="center">
  <thead>
    <tr>
      <th>Cartera</th>
      <th>Clientes</th>
      <th>Ingresos</th>
      <th>Diferencia Porcentual</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Cartera 0</th>
      <td>1.429</td>
      <td>$2.788.959.691</td>
      <td>-0,2%</td>
    </tr>
    <tr>
      <th>Cartera 1</th>
      <td>1.429</td>
      <td>$2.789.250.729</td>
      <td>-0,2%</td>
    </tr>
    <tr>
      <th>Cartera 2</th>
      <td>1.429</td>
      <td>$2.792.000.840</td>
      <td>-0,1%</td>
    </tr>
    <tr>
      <th>Cartera 3</th>
      <td>1.429</td>
      <td>$2.789.426.508</td>
      <td>-0,2%</td>
    </tr>
    <tr>
      <th>Sin Asignar</th>
      <td>5</td>
      <td>$14.995.234</td>
      <td>-</td>
    </tr>
  </tbody>
</table>