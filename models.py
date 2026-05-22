from typing import Dict, List, Optional


class Product:
    """Класс, описывающий товар предприятия

    args:
        product_id: Уникальный идентификатор товара
        name: Наименование товара
        purchase_price: Закупочная цена товара
        selling_price: Розничная цена товара
    """

    def __init__(self, product_id: str, name: str, purchase_price: float, selling_price: float) -> None:
        self.product_id = product_id
        self.name = name
        self.purchase_price = purchase_price
        self.selling_price = selling_price

    def to_dict(self) -> Dict[str, object]:
        """Преобразует объект товара в словарь

        returns:
            Словарь с данными товара
        """

        result = {
            "product_id": self.product_id,
            "name": self.name,
            "purchase_price": self.purchase_price,
            "selling_price": self.selling_price,
        }

        return result


class Person:
    """Базовый класс для описания человека

    args:
        person_id: Уникальный идентификатор
        name: ФИО человека
        phone: Номер телефона
    """

    def __init__(self, person_id: str, name: str, phone: str) -> None:
        self.person_id = person_id
        self.name = name
        self.phone = phone


class Employee(Person):
    """Класс, описывающий сотрудника предприятия

    args:
        person_id: Уникальный идентификатор
        name: ФИО
        phone: Телефон
        role: Должность
        salary: Заработная плата
        is_active: Статус работы (работает/уволен)
    """

    def __init__(
        self,
        person_id: str,
        name: str,
        phone: str,
        role: str,
        salary: float,
        is_active: bool = True,
    ) -> None:
        super().__init__(person_id, name, phone)
        self.role = role
        self.salary = salary
        self.is_active = is_active

    def to_dict(self) -> Dict[str, object]:
        """Преобразует данные сотрудника в словарь

        returns:
            Словарь данных
        """

        result = {
            "person_id": self.person_id,
            "name": self.name,
            "phone": self.phone,
            "role": self.role,
            "salary": self.salary,
            "is_active": self.is_active,
        }

        return result


class Customer(Person):
    """Класс, описывающий клиента компании

    args:
        person_id: Уникальный идентификатор
        name: ФИО
        phone: Телефон
        discount: Процент скидки (0.0 - 1.0)
    """

    def __init__(self, person_id: str, name: str, phone: str, discount: float = 0.0) -> None:
        super().__init__(person_id, name, phone)
        self.discount = discount

    def to_dict(self) -> Dict[str, object]:
        """Преобразует данные клиента в словарь

        returns:
            Словарь данных
        """

        result = {
            "person_id": self.person_id,
            "name": self.name,
            "phone": self.phone,
            "discount": self.discount,
        }

        return result


class WarehouseCell:
    """Класс ячейки склада для хранения товаров

    args:
        cell_id: Номер или идентификатор ячейки
        capacity: Максимальная вместимость ячейки (в единицах товара)
        products: Словарь вида {product_id: quantity}
    """

    def __init__(self, cell_id: str, capacity: int, products: Optional[Dict[str, int]] = None) -> None:
        self.cell_id = cell_id
        self.capacity = capacity
        self.products = products if products is not None else {}

    def get_current_load(self) -> int:
        """Возвращает общую текущую занятость ячейки

        returns:
            Количество хранящихся единиц товара
        """

        result = sum(self.products.values())

        return result

    def add_product(self, product_id: str, quantity: int) -> bool:
        """Добавляет товар в ячейку с учетом вместимости

        args:
            product_id: ID товара
            quantity: Количество

        returns:
            True если операция успешна, иначе False
        """

        if self.get_current_load() + quantity > self.capacity:
            result = False

        else:
            self.products[product_id] = self.products.get(product_id, 0) + quantity
            result = True

        return result

    def remove_product(self, product_id: str, quantity: int) -> bool:
        """Удаляет товар из ячейки

        args:
            product_id: ID товара
            quantity: Количество для удаления

        returns:
            True если операция успешна, иначе False
        """

        current_qty = self.products.get(product_id, 0)

        if current_qty < quantity:
            result = False

        else:
            self.products[product_id] = current_qty - quantity
            if self.products[product_id] == 0:
                del self.products[product_id]
            result = True

        return result

    def to_dict(self) -> Dict[str, object]:
        """Преобразует ячейку в словарь

        returns:
            Словарь данных ячейки
        """

        result = {
            "cell_id": self.cell_id,
            "capacity": self.capacity,
            "products": self.products,
        }

        return result


class Warehouse:
    """Класс склада

    args:
        warehouse_id: Уникальный идентификатор склада
        name: Название склада
        manager_id: ID ответственного лица (работника)
        cells: Список ячеек WarehouseCell
    """

    def __init__(
        self,
        warehouse_id: str,
        name: str,
        manager_id: Optional[str] = None,
        cells: Optional[List[WarehouseCell]] = None,
    ) -> None:
        self.warehouse_id = warehouse_id
        self.name = name
        self.manager_id = manager_id
        self.cells = cells if cells is not None else []

    def to_dict(self) -> Dict[str, object]:
        """Преобразует склад в словарь

        returns:
            Словарь данных склада
        """

        result = {
            "warehouse_id": self.warehouse_id,
            "name": self.name,
            "manager_id": self.manager_id,
            "cells": [cell.to_dict() for cell in self.cells],
        }

        return result


class PointOfSale:
    """Класс пункта продаж

    args:
        pos_id: Уникальный идентификатор пункта продаж
        name: Название пункта
        manager_id: ID ответственного лица
        products: Словарь вида {product_id: quantity}
        employee_ids: Список ID прикрепленных сотрудников
    """

    def __init__(
        self,
        pos_id: str,
        name: str,
        manager_id: Optional[str] = None,
        products: Optional[Dict[str, int]] = None,
        employee_ids: Optional[List[str]] = None,
    ) -> None:
        self.pos_id = pos_id
        self.name = name
        self.manager_id = manager_id
        self.products = products if products is not None else {}
        self.employee_ids = employee_ids if employee_ids is not None else []

    def add_product(self, product_id: str, quantity: int) -> None:
        """Добавляет товар в пункт продаж

        args:
            product_id: ID товара
            quantity: Количество
        """

        self.products[product_id] = self.products.get(product_id, 0) + quantity

    def remove_product(self, product_id: str, quantity: int) -> bool:
        """Удаляет товар из пункта продаж

        args:
            product_id: ID товара
            quantity: Количество

        returns:
            True если товар успешно списан, иначе False
        """

        current_qty = self.products.get(product_id, 0)

        if current_qty < quantity:
            result = False

        else:
            self.products[product_id] = current_qty - quantity
            if self.products[product_id] == 0:
                del self.products[product_id]
            result = True

        return result

    def to_dict(self) -> Dict[str, object]:
        """Преобразует пункт продаж в словарь

        returns:
            Словарь данных
        """

        result = {
            "pos_id": self.pos_id,
            "name": self.name,
            "manager_id": self.manager_id,
            "products": self.products,
            "employee_ids": self.employee_ids,
        }

        return result


class Order:
    """Класс заказа для фиксации продаж или возвратов

    args:
        order_id: Уникальный идентификатор заказа
        customer_id: ID клиента
        product_id: ID товара
        quantity: Количество товара
        total_price: Итоговая стоимость заказа с учетом скидки
        order_type: Тип сделки ("sale" - продажа, "return" - возврат)
    """

    def __init__(
        self,
        order_id: str,
        customer_id: str,
        product_id: str,
        quantity: int,
        total_price: float,
        order_type: str = "sale",
    ) -> None:
        self.order_id = order_id
        self.customer_id = customer_id
        self.product_id = product_id
        self.quantity = quantity
        self.total_price = total_price
        self.order_type = order_type

    def to_dict(self) -> Dict[str, object]:
        """Преобразует заказ в словарь

        returns:
            Словарь данных заказа
        """

        result = {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "total_price": self.total_price,
            "order_type": self.order_type,
        }

        return result