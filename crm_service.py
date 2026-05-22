from pathlib import Path
from typing import List, Optional

from data_manager import DataManager, ProductCatalogStorage
from models import Customer, Employee, Order, PointOfSale, Warehouse, WarehouseCell


class CRMService:
    """Класс системы CRM, предоставляющий методы бизнес-логики

    args:
        data_dir: Директория для файлов данных
    """

    def __init__(self, data_dir: str = "data") -> None:
        self.data_manager = DataManager(data_dir)
        self.catalog_storage = ProductCatalogStorage(
            json_path=Path(data_dir) / "catalog.json", txt_path=Path(data_dir) / "catalog.txt"
        )

        self._initialize_default_catalog()

        self.employees = self.data_manager.load_employees()
        self.customers = self.data_manager.load_customers()
        self.warehouses = self.data_manager.load_warehouses()
        self.pos_list = self.data_manager.load_pos()

        fin = self.data_manager.load_financials()
        self.revenue = float(fin.get("revenue", 0.0))
        self.expenses = float(fin.get("expenses", 0.0))
        self.orders = list(fin.get("orders", []))

    def _initialize_default_catalog(self) -> None:
        """Инициализирует тестовый каталог товаров, если он отсутствует"""

        catalog_path = self.catalog_storage.json_path
        txt_path = self.catalog_storage.txt_path

        if not catalog_path.exists() and txt_path is not None:
            txt_path.parent.mkdir(parents=True, exist_ok=True)
            content = (
                "product_id;name;purchase_price;selling_price\n"
                "PROD1;Ноутбук;50000;75000\n"
                "PROD2;Смартфон;20000;35000\n"
                "PROD3;Наушники;3000;6000\n"
                "PROD4;Клавиатура;1500;3000\n"
            )
            txt_path.write_text(content, encoding="utf-8")

        self.catalog_storage.load()

    def purchase_product(self, product_id: str, quantity: int, warehouse_id: str, cell_id: str) -> str:
        """Закупка товара из каталога на склад

        args:
            product_id: Идентификатор товара из каталога
            quantity: Количество закупаемых единиц
            warehouse_id: Идентификатор склада
            cell_id: Идентификатор ячейки склада

        returns:
            Текстовый статус выполнения операции
        """

        catalog = self.catalog_storage.products
        product_data = None
        for p in catalog:
            if str(p.get("product_id")) == product_id:
                product_data = p
                break

        if not product_data:
            result = "Товар не найден в каталоге."

        else:
            warehouse = next((w for w in self.warehouses if w.warehouse_id == warehouse_id), None)
            if not warehouse:
                result = "Склад не найден."

            else:
                cell = next((c for c in warehouse.cells if c.cell_id == cell_id), None)
                if not cell:
                    result = "Ячейка не найдена."

                elif not cell.add_product(product_id, quantity):
                    result = "Недостаточно места в ячейке склада."

                else:
                    purchase_price = float(product_data.get("purchase_price", 0.0))
                    total_cost = purchase_price * quantity
                    self.expenses += total_cost

                    self.data_manager.save_warehouses(self.warehouses)
                    self.data_manager.save_financials(self.revenue, self.expenses, self.orders)
                    result = f"Закуплено {quantity} шт. {product_id} на сумму {total_cost:.2f} руб."

        return result

    def move_product(
        self,
        src_wh_id: str,
        src_cell_id: str,
        product_id: str,
        quantity: int,
        target_type: str,
        target_id: str,
        target_cell_id: Optional[str] = None,
    ) -> str:
        """Перемещение товара со склада в другую ячейку или на пункт продаж

        args:
            src_wh_id: ID исходного склада
            src_cell_id: ID исходной ячейки
            product_id: ID товара
            quantity: Количество
            target_type: Тип получателя ("warehouse" или "pos")
            target_id: ID целевого склада или пункта продаж
            target_cell_id: ID ячейки назначения (для склада)

        returns:
            Текстовый статус выполнения
        """

        src_wh = next((w for w in self.warehouses if w.warehouse_id == src_wh_id), None)
        if not src_wh:
            result = "Исходный склад не найден."

        else:
            src_cell = next((c for c in src_wh.cells if c.cell_id == src_cell_id), None)
            if not src_cell:
                result = "Исходная ячейка не найдена."

            elif src_cell.products.get(product_id, 0) < quantity:
                result = "В исходной ячейке недостаточно товара."

            elif target_type == "warehouse":
                if not target_cell_id:
                    result = "Не указана целевая ячейка склада."

                else:
                    tgt_wh = next((w for w in self.warehouses if w.warehouse_id == target_id), None)
                    if not tgt_wh:
                        result = "Целевой склад не найден."

                    else:
                        tgt_cell = next((c for c in tgt_wh.cells if c.cell_id == target_cell_id), None)
                        if not tgt_cell:
                            result = "Целевая ячейка не найдена."

                        elif not tgt_cell.add_product(product_id, quantity):
                            result = "В целевой ячейке склада недостаточно места."

                        else:
                            src_cell.remove_product(product_id, quantity)
                            self.data_manager.save_warehouses(self.warehouses)
                            result = f"Товар {product_id} перемещен в ячейку {target_cell_id} склада {target_id}."

            elif target_type == "pos":
                tgt_pos = next((p for p in self.pos_list if p.pos_id == target_id), None)
                if not tgt_pos:
                    result = "Целевой пункт продаж не найден."

                else:
                    tgt_pos.add_product(product_id, quantity)
                    src_cell.remove_product(product_id, quantity)
                    self.data_manager.save_warehouses(self.warehouses)
                    self.data_manager.save_pos(self.pos_list)
                    result = f"Товар {product_id} перемещен на пункт продаж {target_id}."

            else:
                result = "Неверный тип целевого объекта."

        return result

    def sell_product(self, pos_id: str, product_id: str, quantity: int, customer_id: str) -> str:
        """Продажа товара из пункта продаж клиенту

        args:
            pos_id: ID пункта продаж
            product_id: ID товара
            quantity: Количество товара
            customer_id: ID клиента

        returns:
            Результат проведения продажи
        """

        pos = next((p for p in self.pos_list if p.pos_id == pos_id), None)
        if not pos:
            result = "Пункт продаж не найден."

        elif pos.products.get(product_id, 0) < quantity:
            result = "Недостаточно товара в пункте продаж."

        else:
            catalog = self.catalog_storage.products
            product_data = next((p for p in catalog if str(p.get("product_id")) == product_id), None)
            if not product_data:
                result = "Товар отсутствует в каталоге продаж."

            else:
                selling_price = float(product_data.get("selling_price", 0.0))
                customer = next((c for c in self.customers if c.person_id == customer_id), None)
                discount = customer.discount if customer else 0.0

                total_price = selling_price * quantity * (1.0 - discount)
                pos.remove_product(product_id, quantity)
                self.revenue += total_price

                order_id = f"ORD{len(self.orders) + 1}"
                new_order = Order(
                    order_id=order_id,
                    customer_id=customer_id,
                    product_id=product_id,
                    quantity=quantity,
                    total_price=total_price,
                    order_type="sale",
                )
                self.orders.append(new_order)

                self.data_manager.save_pos(self.pos_list)
                self.data_manager.save_financials(self.revenue, self.expenses, self.orders)
                result = f"Продано {quantity} шт. {product_id} за {total_price:.2f} руб. (ID заказа: {order_id})"

        return result

    def return_product(self, order_id: str, pos_id: str) -> str:
        """Возврат товара клиентом по ID заказа

        args:
            order_id: ID оригинального заказа продажи
            pos_id: ID пункта продаж, куда возвращается товар

        returns:
            Статус возврата
        """

        order = next((o for o in self.orders if o.order_id == order_id), None)
        if not order:
            result = "Заказ не найден."

        elif order.order_type == "return":
            result = "По этому заказу уже выполнен возврат."

        else:
            pos = next((p for p in self.pos_list if p.pos_id == pos_id), None)
            if not pos:
                result = "Пункт продаж для проведения возврата не найден."

            else:
                pos.add_product(order.product_id, order.quantity)
                self.revenue -= order.total_price
                order.order_type = "return"

                return_order_id = f"RET{len(self.orders) + 1}"
                return_order = Order(
                    order_id=return_order_id,
                    customer_id=order.customer_id,
                    product_id=order.product_id,
                    quantity=order.quantity,
                    total_price=-order.total_price,
                    order_type="return",
                )
                self.orders.append(return_order)

                self.data_manager.save_pos(self.pos_list)
                self.data_manager.save_financials(self.revenue, self.expenses, self.orders)
                result = f"Успешно оформлен возврат по заказу {order_id}. Товар передан на {pos_id}."

        return result

    def hire_employee(self, emp_id: str, name: str, phone: str, role: str, salary: float) -> str:
        """Найм нового сотрудника

        args:
            emp_id: Уникальный ID
            name: ФИО
            phone: Номер телефона
            role: Должность
            salary: Заработная плата

        returns:
            Статус операции
        """

        existing = next((e for e in self.employees if e.person_id == emp_id), None)
        if existing:
            if existing.is_active:
                result = "Сотрудник с таким ID уже работает."

            else:
                existing.is_active = True
                existing.name = name
                existing.phone = phone
                existing.role = role
                existing.salary = salary
                result = f"Ранее уволенный сотрудник {name} восстановлен на должности {role}."

        else:
            new_emp = Employee(emp_id, name, phone, role, salary)
            self.employees.append(new_emp)
            result = f"Сотрудник {name} успешно нанят на должность: {role}."

        self.data_manager.save_employees(self.employees)

        return result

    def fire_employee(self, emp_id: str) -> str:
        """Увольнение сотрудника (перевод в неактивное состояние)

        args:
            emp_id: ID сотрудника

        returns:
            Статус увольнения
        """

        emp = next((e for e in self.employees if e.person_id == emp_id), None)
        if not emp:
            result = "Сотрудник не найден."

        elif not emp.is_active:
            result = "Сотрудник уже уволен."

        else:
            emp.is_active = False
            for w in self.warehouses:
                if w.manager_id == emp_id:
                    w.manager_id = None

            for p in self.pos_list:
                if p.manager_id == emp_id:
                    p.manager_id = None
                if emp_id in p.employee_ids:
                    p.employee_ids.remove(emp_id)

            self.data_manager.save_employees(self.employees)
            self.data_manager.save_warehouses(self.warehouses)
            self.data_manager.save_pos(self.pos_list)
            result = f"Сотрудник {emp.name} успешно уволен."

        return result

    def register_customer(self, cust_id: str, name: str, phone: str, discount: float = 0.0) -> str:
        """Регистрация клиента в системе

        args:
            cust_id: ID клиента
            name: ФИО
            phone: Номер телефона
            discount: Скидка (от 0.0 до 1.0)

        returns:
            Статус операции
        """

        existing = next((c for c in self.customers if c.person_id == cust_id), None)
        if existing:
            existing.name = name
            existing.phone = phone
            existing.discount = discount

        else:
            new_cust = Customer(cust_id, name, phone, discount)
            self.customers.append(new_cust)

        self.data_manager.save_customers(self.customers)
        result = f"Клиент {name} зарегистрирован со скидкой {discount * 100}%."

        return result

    def open_warehouse(self, wh_id: str, name: str, manager_id: Optional[str] = None) -> str:
        """Открытие нового склада с тремя базовыми ячейками

        args:
            wh_id: ID склада
            name: Название
            manager_id: ID ответственного лица

        returns:
            Статус операции
        """

        existing = next((w for w in self.warehouses if w.warehouse_id == wh_id), None)
        if existing:
            result = "Склад с таким ID уже существует."

        elif manager_id and not next((e for e in self.employees if e.person_id == manager_id and e.is_active), None):
            result = "Назначаемый менеджер отсутствует в списке активных сотрудников."

        else:
            cells = [
                WarehouseCell("C1", 10),
                WarehouseCell("C2", 50),
                WarehouseCell("C3", 100),
            ]
            new_wh = Warehouse(wh_id, name, manager_id, cells)
            self.warehouses.append(new_wh)
            self.data_manager.save_warehouses(self.warehouses)
            result = f"Новый склад '{name}' успешно открыт."

        return result

    def close_warehouse(self, wh_id: str) -> str:
        """Закрытие склада

        args:
            wh_id: ID закрываемого склада

        returns:
            Статус операции
        """

        warehouse = next((w for w in self.warehouses if w.warehouse_id == wh_id), None)
        if not warehouse:
            result = "Склад не найден."

        else:
            self.warehouses.remove(warehouse)
            self.data_manager.save_warehouses(self.warehouses)
            result = f"Склад '{warehouse.name}' закрыт и исключен из реестра."

        return result

    def open_pos(self, pos_id: str, name: str, manager_id: Optional[str] = None) -> str:
        """Открытие нового пункта продаж

        args:
            pos_id: ID пункта
            name: Название пункта продаж
            manager_id: ID ответственного лица

        returns:
            Статус операции
        """

        existing = next((p for p in self.pos_list if p.pos_id == pos_id), None)
        if existing:
            result = "Пункт продаж с таким ID уже существует."

        elif manager_id and not next((e for e in self.employees if e.person_id == manager_id and e.is_active), None):
            result = "Менеджер не найден или не является активным сотрудником."

        else:
            new_pos = PointOfSale(pos_id, name, manager_id)
            if manager_id:
                new_pos.employee_ids.append(manager_id)
            self.pos_list.append(new_pos)
            self.data_manager.save_pos(self.pos_list)
            result = f"Пункт продаж '{name}' успешно открыт."

        return result

    def close_pos(self, pos_id: str) -> str:
        """Закрытие пункта продаж

        args:
            pos_id: ID пункта

        returns:
            Статус операции
        """

        pos = next((p for p in self.pos_list if p.pos_id == pos_id), None)
        if not pos:
            result = "Пункт продаж не найден."

        else:
            self.pos_list.remove(pos)
            self.data_manager.save_pos(self.pos_list)
            result = f"Пункт продаж '{pos.name}' успешно закрыт."

        return result

    def change_manager(self, entity_type: str, entity_id: str, manager_id: str) -> str:
        """Смена ответственного лица склада или пункта продаж

        args:
            entity_type: "warehouse" или "pos"
            entity_id: ID склада или пункта продаж
            manager_id: ID нового ответственного сотрудника

        returns:
            Статус операции
        """

        mgr = next((e for e in self.employees if e.person_id == manager_id and e.is_active), None)
        if not mgr:
            result = "Назначаемый сотрудник не найден или неактивен."

        elif entity_type == "warehouse":
            wh = next((w for w in self.warehouses if w.warehouse_id == entity_id), None)
            if not wh:
                result = "Склад не найден."

            else:
                wh.manager_id = manager_id
                self.data_manager.save_warehouses(self.warehouses)
                result = f"Менеджером склада '{wh.name}' назначен сотрудник {mgr.name}."

        elif entity_type == "pos":
            pos = next((p for p in self.pos_list if p.pos_id == entity_id), None)
            if not pos:
                result = "Пункт продаж не найден."

            else:
                pos.manager_id = manager_id
                if manager_id not in pos.employee_ids:
                    pos.employee_ids.append(manager_id)
                self.data_manager.save_pos(self.pos_list)
                result = f"Менеджером пункта продаж '{pos.name}' назначен сотрудник {mgr.name}."

        else:
            result = "Неверно указан тип объекта."

        return result

    def get_warehouses_info(self) -> str:
        """Возвращает сводную информацию о складах

        returns:
            Строка отчета
        """

        if not self.warehouses:
            result = "Склады отсутствуют."

        else:
            lines = ["--- СПИСОК СКЛАДОВ ---"]
            for w in self.warehouses:
                mgr_name = "Не назначен"
                if w.manager_id:
                    mgr = next((e for e in self.employees if e.person_id == w.manager_id), None)
                    if mgr:
                        mgr_name = mgr.name
                lines.append(f"Склад: {w.name} (ID: {w.warehouse_id}) | Ответственный: {mgr_name}")
                for cell in w.cells:
                    load = cell.get_current_load()
                    lines.append(f"  - Ячейка {cell.cell_id}: Занято {load}/{cell.capacity} ед. Товар: {cell.products}")
            result = "\n".join(lines)

        return result

    def get_pos_info(self) -> str:
        """Возвращает сводную информацию о пунктах продаж

        returns:
            Строка отчета
        """

        if not self.pos_list:
            result = "Пункты продаж отсутствуют."

        else:
            lines = ["--- СПИСОК ПУНКТОВ ПРОДАЖ ---"]
            for p in self.pos_list:
                mgr_name = "Не назначен"
                if p.manager_id:
                    mgr = next((e for e in self.employees if e.person_id == p.manager_id), None)
                    if mgr:
                        mgr_name = mgr.name
                lines.append(f"Пункт продаж: {p.name} (ID: {p.pos_id}) | Менеджер: {mgr_name}")
                lines.append(f"  - Товары в продаже: {p.products}")
                lines.append(f"  - Персонал (ID сотрудников): {p.employee_ids}")
            result = "\n".join(lines)

        return result

    def get_catalog_info(self) -> str:
        """Возвращает перечень товаров, доступных к закупке

        returns:
            Строка отчета
        """

        catalog = self.catalog_storage.products
        if not catalog:
            result = "Каталог пуст или отсутствует."

        else:
            lines = ["--- КАТАЛОГ ТОВАРОВ ДЛЯ ЗАКУПКИ ---"]
            for p in catalog:
                lines.append(
                    f"ID: {p.get('product_id')} | {p.get('name')} | "
                    f"Закупка: {p.get('purchase_price')} руб. | Продажа: {p.get('selling_price')} руб."
                )
            result = "\n".join(lines)

        return result

    def get_financial_report(self) -> str:
        """Возвращает финансовый отчет о доходности

        returns:
            Строка отчета
        """

        profit = self.revenue - self.expenses
        lines = [
            "--- ФИНАНСОВЫЙ ОТЧЕТ ПРЕДПРИЯТИЯ ---",
            f"Общий доход (Выручка): {self.revenue:.2f} руб.",
            f"Общие расходы (Закупки): {self.expenses:.2f} руб.",
            f"Текущая прибыль (Доходность): {profit:.2f} руб.",
            f"Всего транзакций: {len(self.orders)}",
        ]
        result = "\n".join(lines)

        return result