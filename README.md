# Customer Portfolio Optimizer

Modelo de programación lineal binaria que busca distribuir bases de $n$ registros - donde cada uno está acompañado de un valor continuo o discreto - en $m$ clases o etiquetas, equilibrando el recuento de registros y suma de valores contenidos en cada clase. En la sección de [descripción del modelo](#descripción-del-modelo), este se explica mediante un caso de uso hipotético, pero concreto.

En este repositorio, por un lado, podrán encontrar una [POC (Proof of Concept)](./poc), donde se muestra con mucho detalle la aplicación del modelo utilizando un dataset sintético apoyado por Jupyter Notebooks. Y, por otro lado, también encontrarán el módulo [`optimizer`](./port-opt), el cual contiene una sola clase (`Optimizer`), y representa una implementacion generalizada que lo hace aplicable a cualquier escenario que cumpla con las condiciones.

## Tabla de Contenidos

- [Instalación de dependencias](#instalación-de-dependecias)
- [Descripción del modelo](#descripción-del-modelo)
- [Licencia](#licencia)
- [Referencias](#referencias)

## Instalación de dependecias

> :warning: Se recomienda el uso de un entorno virtual.

Antes de usar la POC o el módulo localmente, es necesario instalar la librería de python ["mip"](https://github.com/coin-or/python-mip?tab=readme-ov-file) y el solver [CBC](https://github.com/coin-or/Cbc?tab=readme-ov-file) (open-source) para programación lineal mixta, el cual es usado por la librería ["mip"](https://github.com/coin-or/python-mip?tab=readme-ov-file).

### macOS - Apple Silicon

1. Instalación de librería "mip"
```sh
pip install git+https://github.com/coin-or/python-mip.git
```

2. Instalación de CBC ([homebrew](https://brew.sh))
```sh
brew tap coin-or-tools/coinor
```

```sh
brew install coin-or-tools/coinor/cbc
```

3. (Recomendado) Actualización de otras dependencias
```sh
pip install --upgrade cffi
```

## Descripción del modelo

El modelo es explicado en base a un ejemplo particular, sin embargo, como se menciona al [inicio](#customer-portfolio-optimizer), puede ser aplicado en otros contextos con necesidades y características similares.

Supongamos que tenemos una base de $n$ clientes que necesitamos distribuir en $m$ carteras. Si solo esa fuera la necesidad, sería relativamente sencillo, pero digamos que también necesitamos equilibrar los ingresos - o montos cobrados a cada cliente - de tal forma que cada cartera contenga aproximadamente la misma cantidad de clientes e ingresos acumulados. Es un probelma bastante complejo, ya que requiere buscar $m$ conjuntos de igual cantidad de clientes donde, además, cada conjunto acumule la misma cantidad de ingresos, y se hace particularmente difícil frente a una distribución muy [asimétrica](https://es.wikipedia.org/wiki/Asimetría_estadística) de los ingresos.

Si contamos con una base de datos que al menos contenga un *"id"* para cada cliente junto con los ingresos que cada cliente representa, entonces ya tenemos la información necesaria para el caso de uso.

<table align="center">
    <thead>
        <tr>
            <th scope="col">Id Cliente</th>
            <th scope="col">Ingresos</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>42</td>
            <td>$2.932.578</td>
        </tr>
        <tr>
            <td>43</td>
            <td>$1.026.269</td>
        </tr>
        <tr  style= "text-align: center;">
            <td>&vellip;</td>
            <td>&vellip;</td>
        </tr>
        <tr>
            <td><math><mi>N</mi></math></td>
            <td><math><mi>F</mi></math></td>
        </tr>
    </tbody>
</table>

### Convenciones

Se define la siguiente convención, la cual tiene como propósito declarar la notación que será utilizada para representar la cantidad de clientes y carteras en las que se busca distribuirlos.

$$
N = \text{Cantidad Clientes }
$$
$$
M = \text{Cantidad Carteras }
$$

Más adelante, también se mostrarán las representaciones matriciales de las variables de decisión, parámetros y función objetivo, la que si bien no es la "tradicional", permite mostrar ciertos elementos del modelo de una manera distinta.

### Variables de decisión

Se define una única variable de decisión binaria $X_{ij}$ que representa si un cliente es asignado a alguna cartera o no. Habrá tantas variables de decisión como el producto entre la cantidad de clientes y carteras donde se quieran distribuir ($N \times M$). Además, notar que se usan las letras $n$ y $m$ (en minúscula) para representar a los clientes y carteras en su forma [*"zero-indexed"*](https://en.wikipedia.org/wiki/Zero-based_numbering). También se muestra la representación matricial de las variables de decisión.

$$
X_{ij} =
\begin{cases} 
1, & \text{Se asigna el cliente “i” a la cartera “j”} \\ 
0, & \text{En caso contrario}
\end{cases}
$$

$$
X_{ij} \in \\{0, 1\\},\ \ \ \forall\ i,j
$$

$$
i \in \\{0, 1, 2, \dots, n\\}
$$

$$
n = N-1
$$

$$
j \in \\{0, 1, 2, \dots, m\\}
$$

$$
m = M-1
$$

$$
X = \begin{bmatrix}
X_{00} & X_{01} & X_{02} & X_{03} \\
X_{10} & X_{11} & X_{12} & X_{13} \\
\vdots & \vdots & \vdots & \vdots \\
X_{n0} & X_{n1} & X_{n2} & X_{nm}
\end{bmatrix}_{N\ \times M}
$$

### Parámetros

Los únicos parámetros del modelo, y también del presente problema de ejemplo, son los ingresos de cada cliente, los cuales son también representados como una matriz diagonal. Además, también se define el parámetro $F_{s}$ como el valor de la suma de los ingresos de todos los clientes.

$$
F_{i} = \text{Ingresos del cliente "i"}
$$

$$
F = \begin{bmatrix}
F_{0} & 0 & 0 & 0 \\
0 & F_{1} & 0 & 0 \\
\vdots & \vdots & \vdots & \vdots \\
0 & 0 & 0 & F_{n}
\end{bmatrix}_{N\ \times N}
$$

$$
F_{s} = \sum_{i=0}^{n} F_{i},\ \forall\ i \in n
$$

### Función objetivo

El modelo se presenta como un problema de minimización de la función objetivo, que es la suma de los ingresos de cada cliente entre todas las carteras. En la sección de [Restricciones](#restricciones) se abordará con más detalle la manera en que esta función hace sentido.

$$
\text{Objetivo} = min\ \sum_{i=0}^{n} \sum_{j=0}^{m} F_{i}X_{ij}
$$

Para que la representación matricial tenga sentido, tenemos que considerar que el producto matricial de $Z=F\ X$ es una matrix de $N \times M$. Luego, se definen los vectores unitarios $A$ y $B$ de dimensiones $N \times 1$ y $M \times 1$, respectivamente. De esta manera, el problema y la función objetivo se pueden representar como:

$$
\text{Objetivo} = min\ A^{T}Z\ B
$$

donde el producto $A^{T}Z\ B = A^{T}(F\ X)\ B$ resulta en un escalar $(1 \times 1)$ que es precisamente la suma de todos los elementos de $Z$, matriz que a su vez es el producto de la matriz de parámetros con la de variables de decisión.

### Restricciones

#### 1. Cantidad de clientes por cartera

Cada cartera debe tener aproximadamente la misma cantidad de clientes. Esto se representa como la suma de todos los clientes en cada cartera debe ser mayor o igual a la parte entera del cociente entre la cantidad de clientes y el número de carteras (parte entera del promedio simple). Además, se considera un parámetro de holgura *opcional* ($h_{c}$) que ayuda a relajar la restricción, contribuyendo a la velocidad de convergencia del modelo.

$$
\sum_{i=0}^{n} X_{ij} \geq \left\lfloor \frac{N}{M} \right\rfloor - h_{c},\ \forall\ j\in m\  \wedge N \gt M
$$

#### 2. Total de ingresos por cartera

Cada cartera debe acumular aproximadamente la misma cantidad de ingresos. Si el cliente es asignado a la cartera, entonces sus ingresos también. Entonces, la suma de esos ingresos debe ser mayor que la parte entera del promedio simple entre la suma de los ingresos y la cantidad de carteras. También se considera un parámetro de holgura *opcional* ($h_{f}$) que ayude a relajar la resitrcción y mejorar la velocidad de convergencia.

$$
\sum_{i=0}^{n} F_{i}X_{ij} \geq \left\lfloor \frac{F_{s}}{M} \right\rfloor - h_{f},\ \forall\ j\in m\  \wedge F_{s} \gt M
$$

#### 3. Asignar clientes a una sola cartera

Cada cliente puede estar asignado a una y solo una cartera, aunque la restricción permite que también pueda no estar asignado a ninguna. Esto es especialmente importante para los casos donde la cantidad de clientes no es un múltiplo del número de carteras.

$$
\sum_{j=0}^{m} X_{ij} \leq 1,\ \forall\ i\in n
$$

#### 4. Variable binaria

Para el cumplimiento de la formalidad, se declara como restricción que las variables de decisión del modelo son todas binarias.

$$
X_{ij} \in \\{0, 1\\},\ \forall\ i\in n\ \wedge j \in m
$$

### Cardinalidad

$$
\text{Cantidad de variables de decisión} = N \cdot M
$$

$$
\text{Cantidad de restricciones (sin binarias)} = 2M + N
$$

$$
\text{Cantidad de restricciones (con binarias)} = 2M + N(1+M)
$$

## Licencia

[MIT](LICENSE)

## Referencias

* [Instalación de mip](https://github.com/coin-or/python-mip?tab=readme-ov-file)
* [Instalación de CBC](https://github.com/coin-or/Cbc?tab=readme-ov-file)

[Volver al Inicio](#tabla-de-contenidos)
