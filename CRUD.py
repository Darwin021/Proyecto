from abc import ABC, abstractmethod

class CRUD(ABC):
    @abstractmethod
    def agregar(self):
        pass

    @abstractmethod
    def get_edit(self):
        pass

    @abstractmethod
    def borrar(self):
        pass

    @abstractmethod
    def editar(self):
        pass
