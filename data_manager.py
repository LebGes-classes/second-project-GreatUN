import json
from pathlib import Path
from typing import Dict, List, Optional

from models import Customer, Employee, Order, PointOfSale, Product, Warehouse, WarehouseCell


class TxtSerializer:
    """Читает каталог товаров из TXT-файла с разделителем ';'."""

    @staticmethod
    def read_file(path_to_file: str | Path) -> list[dict[str, object]]:
        """Возвращает список товаров в виде словарей (атрибут: значение)."""

        path = Path(path_to_file)
        if not path.exists():
            return []

        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            return []

        headers = [header.strip() for header in lines[0].split(";")]
        products: list[dict[str, object]] = []

        for line in lines[1:]:
            values = [value.strip() for value in line.split(";")]
            product = {headers[index]: values[index] if index < len(values) else "" for index in range(len(headers))}
            products.append(product)

        return products


class JsonDeserializer:
    """Читает каталог товаров из JSON-файла."""

    @staticmethod
    def read_file(path_to_file: str | Path) -> list[dict[str, object]]:
        """Возвращает список товаров из JSON. Если файл отсутствует или пуст, вернет []."""

        path = Path(path_to_file)
        if not path.exists() or path.stat().st_size == 0:
            return []

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        raise ValueError("Ожидался JSON-массив карточек товаров")


class JsonSerializer:
    """Записывает каталог товаров в JSON-файл."""

    @staticmethod
    def write_file(path_to_file: str | Path, products: list[dict[str, object]] | dict[str, object]) -> None:
        """Перезаписывает JSON-файл актуальным списком карточек товаров или словарем."""

        path = Path(path_to_file)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(products, file, ensure_ascii=False, indent=2)


class ProductCatalogStorage:
    """Система хранения каталога товаров с автоматической синхронизацией в JSON."""

    def __init__(self, json_path: str | Path, txt_path: str | Path | None = None) -> None:
        self.json_path = Path(json_path)
        self.txt_path = Path(txt_path) if txt_path else None
        self.products: list[dict[str, object]] = []

    def load(self) -> list[dict[str, object]]:
        """Загружает товары: из JSON или из TXT."""

        self.products = JsonDeserializer.read_file(self.json_path)

        if not self.products and self.txt_path is not None:
            self.products = TxtSerializer.read_file(self.txt_path)
            if self.products:
                JsonSerializer.write_file(self.json_path, self.products)

        return self.products

    def add_product(self, product_data: dict[str, object]) -> None:
        """Добавляет новую карточку товара и перезаписывает JSON."""

        self.products.append(product_data)
        self._persist()

    def update_product(self, product_id: str, updated_fields: dict[str, object], id_key: str = "ID") -> bool:
        """Обновляет карточку товара по ID и перезаписывает JSON."""

        for product in self.products:
            if str(product.get(id_key)) == str(product_id):
                product.update(updated_fields)
                self._persist()
                return True

        return False

    def delete_product(self, product_id: str, id_key: str = "ID") -> bool:
        """Удаляет карточку товара по ID и перезаписывает JSON."""

        initial_count = len(self.products)
        self.products = [product for product in self.products if str(product.get(id_key)) != str(product_id)]

        if len(self.products) != initial_count:
            self._persist()
            return True

        return False

    def _persist(self) -> None:
        """Сохраняет текущий каталог в JSON."""

        JsonSerializer.write_file(self.json_path, self.products)


class DataManager:
    """Класс управления всеми файлами данных системы CRM

    args:
        base_dir: Базовая директория для сохранения файлов данных
    """

    def __init__(self, base_dir: str | Path = "data") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.employees_path = self.base_dir / "employees.json"
        self.customers_path = self.base_dir / "customers.json"
        self.warehouses_path = self.base_dir / "warehouses.json"
        self.pos_path = self.base_dir / "pos.json"
        self.financials_path = self.base_dir / "financials.json"

    def load_employees(self) -> List[Employee]:
        """Загружает список сотрудников из файла

        returns:
            Список объектов Employee
        """

        data = JsonDeserializer.read_file(self.employees_path)
        result: List[Employee] = []

        for item in data:
            employee = Employee(
                person_id=str(item.get("person_id", "")),
                name=str(item.get("name", "")),
                phone=str(item.get("phone", "")),
                role=str(item.get("role", "")),
                salary=float(item.get("salary", 0.0)),
                is_active=bool(item.get("is_active", True)),
            )
            result.append(employee)

        return result

    def save_employees(self, employees: List[Employee]) -> None:
        """Сохраняет список сотрудников в файл

        args:
            employees: Список объектов Employee
        """

        data = [emp.to_dict() for emp in employees]
        JsonSerializer.write_file(self.employees_path, data)

    def load_customers(self) -> List[Customer]:
        """Загружает список клиентов из файла

        returns:
            Список объектов Customer
        """

        data = JsonDeserializer.read_file(self.customers_path)
        result: List[Customer] = []

        for item in data:
            customer = Customer(
                person_id=str(item.get("person_id", "")),
                name=str(item.get("name", "")),
                phone=str(item.get("phone", "")),
                discount=float(item.get("discount", 0.0)),
            )
            result.append(customer)

        return result

    def save_customers(self, customers: List[Customer]) -> None:
        """Сохраняет список клиентов в файл

        args:
            customers: Список объектов Customer
        """

        data = [cust.to_dict() for cust in customers]
        JsonSerializer.write_file(self.customers_path, data)

    def load_warehouses(self) -> List[Warehouse]:
        """Загружает список складов из файла

        returns:
            Список объектов Warehouse
        """

        data = JsonDeserializer.read_file(self.warehouses_path)
        result: List[Warehouse] = []

        for item in data:
            cells_data = item.get("cells", [])
            cells: List[WarehouseCell] = []
            for c_item in cells_data:
                cell = WarehouseCell(
                    cell_id=str(c_item.get("cell_id", "")),
                    capacity=int(c_item.get("capacity", 0)),
                    products={str(k): int(v) for k, v in c_item.get("products", {}).items()},
                )
                cells.append(cell)

            warehouse = Warehouse(
                warehouse_id=str(item.get("warehouse_id", "")),
                name=str(item.get("name", "")),
                manager_id=str(item.get("manager_id", "")) if item.get("manager_id") else None,
                cells=cells,
            )
            result.append(warehouse)

        return result

    def save_warehouses(self, warehouses: List[Warehouse]) -> None:
        """Сохраняет список складов в файл

        args:
            warehouses: Список объектов Warehouse
        """

        data = [wh.to_dict() for wh in warehouses]
        JsonSerializer.write_file(self.warehouses_path, data)

    def load_pos(self) -> List[PointOfSale]:
        """Загружает список пунктов продаж из файла

        returns:
            Список объектов PointOfSale
        """

        data = JsonDeserializer.read_file(self.pos_path)
        result: List[PointOfSale] = []

        for item in data:
            pos = PointOfSale(
                pos_id=str(item.get("pos_id", "")),
                name=str(item.get("name", "")),
                manager_id=str(item.get("manager_id", "")) if item.get("manager_id") else None,
                products={str(k): int(v) for k, v in item.get("products", {}).items()},
                employee_ids=[str(emp_id) for emp_id in item.get("employee_ids", [])],
            )
            result.append(pos)

        return result

    def save_pos(self, pos_list: List[PointOfSale]) -> None:
        """Сохраняет список пунктов продаж в файл

        args:
            pos_list: Список объектов PointOfSale
        """

        data = [pos.to_dict() for pos in pos_list]
        JsonSerializer.write_file(self.pos_path, data)

    def load_financials(self) -> Dict[str, object]:
        """Загружает финансовые показатели и историю заказов

        returns:
            Словарь с финансовыми показателями и заказами
        """

        path = Path(self.financials_path)
        if not path.exists() or path.stat().st_size == 0:
            result = {"revenue": 0.0, "expenses": 0.0, "orders": []}

        else:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            orders_list: List[Order] = []
            for item in data.get("orders", []):
                order = Order(
                    order_id=str(item.get("order_id", "")),
                    customer_id=str(item.get("customer_id", "")),
                    product_id=str(item.get("product_id", "")),
                    quantity=int(item.get("quantity", 0)),
                    total_price=float(item.get("total_price", 0.0)),
                    order_type=str(item.get("order_type", "sale")),
                )
                orders_list.append(order)

            result = {
                "revenue": float(data.get("revenue", 0.0)),
                "expenses": float(data.get("expenses", 0.0)),
                "orders": orders_list,
            }

        return result

    def save_financials(self, revenue: float, expenses: float, orders: List[Order]) -> None:
        """Сохраняет финансовые показатели и историю заказов в файл

        args:
            revenue: Доход
            expenses: Расход
            orders: Список заказов
        """

        data = {
            "revenue": revenue,
            "expenses": expenses,
            "orders": [order.to_dict() for order in orders],
        }
        JsonSerializer.write_file(self.financials_path, data)