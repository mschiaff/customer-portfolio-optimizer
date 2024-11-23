# -*- coding: utf-8 -*-

import mip
import numpy as np
from numpy import ndarray
from typing import Union
from pandas import DataFrame
from mip import Model, LinExprTensor
from dataclasses import dataclass, field
from mip import OptimizationStatus as mipStatuts

@dataclass
class Optimizer:
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
        '''Define las restricciones de cantidad de registros por etiqueta'''
        for j in range(self.n_labels):
            self._model.add_constr(
                mip.xsum(
                    self.model_vars[i,j] for i in range(self.n_records)
                ) >= self.records_mean - self.records_slack,
                name=f'{self.records_name}_{self.labels_name}_{j}'
            )
    
    def _constr_labels(self) -> None:
        '''Define las restricciones de suma de valores por etiqueta'''
        for j in range(self.n_labels):
            self._model.add_constr(
                mip.xsum(
                    self.model_values[i,i] * self.model_vars[i,j] for i in range(self.n_records)
                ) >= self.values_mean - self.values_slack,
                name=f'{self.values_name}_{self.labels_name}_{j}'
            )
    
    def _constr_assignment(self) -> None:
        '''Define las restricciones de asignación de registro a etiqueta'''
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