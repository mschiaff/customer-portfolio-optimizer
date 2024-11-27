# -*- coding: utf-8 -*-

import mip
import numpy as np
from numpy import ndarray
from typing import Union
from pandas import DataFrame
from pandas import RangeIndex
from mip import Model, LinExprTensor
from dataclasses import dataclass, field
from mip import OptimizationStatus as mipStatuts

@dataclass
class Optimizer:
    """
    Optimizador que busca balancear la distribución de registros acompañados de una
    medida continua o discreta (valor) en distintas clases o etiqueta.

    Parámetros
    ----------
    dataset : pandas.DataFrame
        Dataset que contiene los valores que se busca distribuir en las distintas clases.
        Los registros son tomados de `pandas.DataFrame.index`, por lo que se recomienda que
        sea un `pandas.RangeIndex` (start=0, stop=n-1, step=1).

    values_name : str
        Nombre del campo con los valores a distribuir en clases dentro del `dataset`. Este
        nombre también es usado para los nombres de las restricciones que determinan cuánto
        de los valores acumulará cada clase o etiqueta. Ver `labels_name` para conocer la
        representación.
    
    n_labels : int
        Cantidad clases o etiquetas en las que se desea distribuir en forma balanceada
        la cantidad de registros y valores que los acompañan.
    
    records_slack (opcional) : int, default 0
        Holgura para la cantidad de registros que se desea entregar a las registricciones
        de cantidad de registros. Si cada clase debe contener `N/M` registros, este valor
        permite que sean al menos `N/M - records_slack`.
    
    values_slack (opcional) : int, default 0
        Holgura para la suma de valores que debe acumular cada clase. Típicamente sería
        `F/M`, y con holgura se permite que sean al menos `F/M - values_slack`.
    
    records_name (opcional): str, default 'record'
        Parte del nombre que tendrán las restricciones y variables de decisión relacionadas con
        la variable de decisión. Siendo `i` cada registro y `j` cada clase o etiqueta, las variables
        de decisión tendrán el nombre `f'{records_name}_{labels_name}_i_j'`; las restricciones que
        determinan la cantidad de registros por clase o etiqueta tendrán el nombre `f'{records_name}_{labels_name}'`;
        y las restricciones que determinan si un registro es asignado a una clase tendrán el nombre
        `f'{records_name}_{i}_assigned'`. Para más detalles sobre cómo acceder a las restricciones,
        ver `@property.model`.
    
    labels_name (opcional): str, default 'label'
        Parte del nombre que tendrán las restricciones relacionadas con los valores a ser distribuidos
        en cada clase o etiqueta. Siendo `i` cada registro y `j` cada clase o etiqueta, las variables
        de decisión tendrán el nombre `f'{records_name}_{labels_name}_i_j'`; las restricciones que
        determinan la cantidad de registros por clase o etiqueta tendrán el nombre `f'{records_name}_{labels_name}'`;
        y las restricciones que determinan cuánto de los valores acumulará cada clase o etiqueta
        tendrán el nombre f'{values_name}_{labels_name}_{j}'. Para más detalles sobre cómo acceder a
        las restricciones, ver `@property.model`.
    
    model_name (opcional) : str, default ''
        Nombre que tendrá la instancia de `mip.Model` creada dentro de la clase `Optimizer`. Para
        más detalles, ver `@property.model`.
    
    Funcionamiento
    --------------
    Una vez instanciado exitosamente un objeto de clase `opt = Optimizer(dataset, values_name, n_labels)`,
    el modelo se ejecuta como `status = opt.model.optimize(max_seconds)`. Se recomienda capturar en una
    variable la salida del método, como `status` en el ejemplo. Además, también se recomienda definir
    el valor de `max_seconds` para limitar el tiempo de ejecución del modelo, como `max_seconds=300`.
    La propiedad `opt.model` devuelve un objeto de clase `mip.Model`.
    
    Propiedades
    -----------
    model (`@getter`): mip.Model
        Instancia de clase `mip.Model` creada dentro del objeto instanciado de clase `Optimizer`.
        Hereda todos los métodos y propiedades de `mip.Model`. No cuenta con un `@setter`, por lo
        que no puede ser modificado externamente. La documentación completa de la clase `mip.Model`
        se encuentra en https://docs.python-mip.com/en/latest/classes.html#model.
    n_labels (`@getter`, `@setter`) : int
        Devuelve la cantidad de clases o etiquetas ingresadas como parámetro en la creación del
        objeto `Optimizer`. Puede ser modificado posterior a la creación de la instancia para
        probar con diferentes cantidades sin crear una nueva instancia.
    records_slack (`@getter`, `@setter`) : int
        Devuelve la holgura de registros. Puede ser modificada sin crear una nueva instancia.
    values_slack (`@getter`, `@setter`) : int
        Devuelve la holgura para la suma de valores por clase o etiqueta. Puede ser modificada
        sin crear una nueva instancia.
    model_name (`@getter`, `@setter`) : str
        Devuelve el nombre del modelo que es pasado a la instancia interna de `mip.Model`. Puede
        ser modificado sin crear una nueva instancia. Está sincronizado con `opt.model.name`.
    
    Ejemplos
    --------
    **Creación de instancia y ejecución del modelo**
    >>> opt = Optimizer(dataset=df, values_name='income', n_labels=5, records_slack=1, values_slack=5_000_000)
    >>> status = opt.model.optimize(max_seconds=300)
    >>> status.name
    'FEASIBLE'

    **Con un objeto instanciado y modelo exitosamente ejecutado**
    
    El estado también puede ser consultado como atributo de `@property.model`:
    >>> opt.model.status.name
    'FEASIBLE'

    Si se modifica `n_labels`, `records_slack` y/o `values_slack`, el modelo
    debe ser ejecutado nuevamente:
    >>> opt.n_labels = 4
    >>> status = opt.model.optimize(max_seconds=300)
    >>> status.name
    'OPTIMAL'
    """
    
    dataset: DataFrame = field()
    values_name: str = field()
    n_labels: int = field()
    records_slack: int = field(default=0)
    values_slack: int = field(default=0)
    records_name: str = field(default='record')
    labels_name: str = field(default='label')
    model_name: str = field(default='')
    n_records: int = field(init=False)
    records_mean: int = field(init=False)
    values_sum: Union[int, float] = field(init=False)
    values_mean: int = field(init=False)

    def __post_init__(self):
        self._check_model_name()
        self._model = self._create_model()

        self.dataset = self.dataset[[self.values_name]].copy()
        self.n_records = self.dataset.shape[0]
        self.values_sum = self.dataset[self.values_name].sum()
        self.records_mean, self.values_mean = self._get_means()
        
        self.model_vars = self._set_model_vars()
        self.model_values = self._set_model_values()
        self._set_model()
    
    #
    # PROPERTIES AND SETTERS
    #

    @property
    def model(self) -> Model:
        return self._model
    
    @property
    def n_labels(self) -> int:
        return self._n_labels
    
    @n_labels.setter
    def n_labels(self, value: int) -> None:
        self._n_labels = value
        if hasattr(self, '_model') and self._model:
            self._model.remove([constr for constr in self._model.constrs])
            self._model.remove([vars for vars in self._model.vars])
            self.records_mean, self.values_mean = self._get_means()
            self.model_vars = self._set_model_vars()
            self._set_model()
    
    @property
    def records_slack(self) -> int:
        return self._records_slack
    
    @records_slack.setter
    def records_slack(self, value: int) -> None:
        self._records_slack = value
        if hasattr(self, '_model') and self._model:
            self._model.remove([constr for constr in self._model.constrs])
            self._build_constraints()
    
    @property
    def values_slack(self) -> int:
        return self._values_slack
    
    @values_slack.setter
    def values_slack(self, value: int) -> None:
        self._values_slack = value
        if hasattr(self, '_model') and self._model:
            self._model.remove([constr for constr in self._model.constrs])
            self._build_constraints()
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @model_name.setter
    def model_name(self, value: str) -> None:
        self._model_name = value
        if hasattr(self, '_model') and self._model:
            self._model.name = value
    
    #
    # INTERNAL FUNCTIONS
    #
    
    def _check_model_name(self) -> None:
        '''Valida si la clase está inicializada para asignar y nombre de modelo'''
        if isinstance(self.model_name, property):
            self.model_name = ""
    
    def _create_model(self) -> Model:
        '''Retorna un objeto mip.Model definido'''
        return mip.Model(name=self.model_name, sense=mip.MINIMIZE, solver_name=mip.CBC)
    
    def _set_model_vars(self) -> LinExprTensor:
        '''Crea variable con las variables del modelo y las agrega al modelo'''
        model_vars = self._model.add_var_tensor(
            shape=(self.n_records, self.n_labels),
            name=f'{self.records_name}_{self.labels_name}',
            var_type=mip.BINARY
        )
        return model_vars
    
    def _set_model_values(self) -> ndarray:
        '''Define matriz diagonal con los valores del modelo'''
        model_values = np.diagflat(
            self.dataset[self.values_name].to_numpy()
        )
        return model_values
    
    def _get_means(self) -> tuple[int]:
        '''Define las medias simples de registros y suma de valores'''
        records_mean = self.n_records // self.n_labels
        values_mean = self.values_sum // self.n_labels
        return records_mean, values_mean
    
    def _set_model(self) -> None:
        '''Ejecuta las funciones que definen función objetivo y restricciones'''
        self._build_objective()
        self._build_constraints()
    
    def _build_objective(self) -> None:
        '''Define la función objetivo'''
        records_range = range(self.n_records)
        labels_range = range(self.n_labels)
        self._model.objective = mip.xsum(
            self.model_values[i,i] * self.model_vars[i,j] for i in records_range for j in labels_range
        )
    
    def _build_constraints(self):
        '''Ejecuta todas las funciones que definen restricciones'''
        self._constr_records()
        self._constr_labels()
        self._constr_assignment()
    
    def _constr_records(self) -> None:
        '''Define las restricciones de cantidad de registros por clase o etiqueta'''
        for j in range(self.n_labels):
            self._model.add_constr(
                mip.xsum(
                    self.model_vars[i,j] for i in range(self.n_records)
                ) >= self.records_mean - self.records_slack,
                name=f'{self.records_name}_{self.labels_name}_{j}'
            )
    
    def _constr_labels(self) -> None:
        '''Define las restricciones de suma de valores por clase o etiqueta'''
        for j in range(self.n_labels):
            self._model.add_constr(
                mip.xsum(
                    self.model_values[i,i] * self.model_vars[i,j] for i in range(self.n_records)
                ) >= self.values_mean - self.values_slack,
                name=f'{self.values_name}_{self.labels_name}_{j}'
            )
    
    def _constr_assignment(self) -> None:
        '''Define las restricciones de asignación de registro a clase o etiqueta'''
        for i in range(self.n_records):
            self._model.add_constr(
                mip.xsum(
                    self.model_vars[i,j] for j in range(self.n_labels)
                ) <= 1,
                name=f'{self.records_name}_{i}_assigned'
            )
    
    #
    # DEFINED FUNCTIONS
    #

    def get_results(self) -> DataFrame:
        '''Obtiene los resultados de las asignaciones si es que el modelo
        alcanzó alguna solución óptima o factible'''
        if self._model.status not in [mipStatuts.OPTIMAL, mipStatuts.FEASIBLE]:
            raise ValueError(f'No solution to get results from. Status: {self._model.status.name}')
        else:
            raw_data = []
            for i in range(self.n_records):
                raw_data.append([self.model_vars[i,j].x for j in range(self.n_labels)])
            
            col_names = [f'{self.labels_name}_{j}' for j in range(self.n_labels)]
            df = DataFrame(raw_data, columns=col_names)
            df['assigned'] = df.sum(axis=1).replace({0: 'not assigned', 1: np.nan})
            
            for col in col_names:
                df[col] = df[col].replace({1: col, 0: np.nan})
                df['assigned'] = df['assigned'].fillna(df[col])
            
            df.drop(columns=col_names, inplace=True)
            df = self.dataset.merge(df, left_index=True, right_index=True)
            return df

opt = Optimizer()