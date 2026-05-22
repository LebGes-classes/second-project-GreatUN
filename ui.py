import sys

from crm_service import CRMService


class ConsoleUI:
    """Класс консольного пользовательского интерфейса

    args:
        crm_service: Ссылка на экземпляр CRMService
    """

    def __init__(self, crm_service: CRMService) -> None:
        self.crm = crm_service

    def run(self) -> None:
        """Запуск основного цикла консольного меню"""

        while True:
            print("\n" + "=" * 50)
            print(" СИСТЕМА УПРАВЛЕНИЯ ПРЕДПРИЯТИЕМ (CRM)")
            print("=" * 50)
            print("1.  Информация о складах")
            print("2.  Информация о пунктах продаж")
            print("3.  Финансовый отчет")
            print("4.  Каталог товаров для закупки")
            print("5.  Закупка товара на склад")
            print("6.  Перемещение товара")
            print("7.  Оформление продажи")
            print("8.  Оформление возврата по ID заказа")
            print("9.  Найм сотрудника")
            print("10. Увольнение сотрудника")
            print("11. Регистрация клиента")
            print("12. Открытие склада")
            print("13. Закрытие склада")
            print("14. Открытие пункта продаж")
            print("15. Закрытие пункта продаж")
            print("16. Сменить ответственное лицо")
            print("0.  Выход")
            print("=" * 50)

            choice = input("Выберите пункт меню: ").strip()

            if choice == "1":
                print(self.crm.get_warehouses_info())

            elif choice == "2":
                print(self.crm.get_pos_info())

            elif choice == "3":
                print(self.crm.get_financial_report())

            elif choice == "4":
                print(self.crm.get_catalog_info())

            elif choice == "5":
                self._handle_purchase()

            elif choice == "6":
                self._handle_move()

            elif choice == "7":
                self._handle_sale()

            elif choice == "8":
                self._handle_return()

            elif choice == "9":
                self._handle_hire()

            elif choice == "10":
                self._handle_fire()

            elif choice == "11":
                self._handle_customer_registration()

            elif choice == "12":
                self._handle_open_warehouse()

            elif choice == "13":
                self._handle_close_warehouse()

            elif choice == "14":
                self._handle_open_pos()

            elif choice == "15":
                self._handle_close_pos()

            elif choice == "16":
                self._handle_change_manager()

            elif choice == "0":
                print("Программа завершена. До свидания!")
                sys.exit(0)

            else:
                print("Некорректный ввод. Попробуйте еще раз.")

    def _handle_purchase(self) -> None:
        """Обработка ввода параметров закупки"""

        print("\n--- Закупка товара ---")
        prod_id = input("Введите ID товара из каталога (например, PROD1): ").strip()
        qty_str = input("Количество: ").strip()
        wh_id = input("ID склада назначения: ").strip()
        cell_id = input("ID ячейки склада (C1, C2, C3): ").strip()

        try:
            qty = int(qty_str)
            if qty <= 0:
                print("Ошибка: количество должно быть больше 0.")

            else:
                status = self.crm.purchase_product(prod_id, qty, wh_id, cell_id)
                print(status)

        except ValueError:
            print("Ошибка: введено нечисловое значение.")

    def _handle_move(self) -> None:
        """Обработка ввода параметров перемещения"""

        print("\n--- Перемещение товара ---")
        src_wh = input("ID склада-отправителя: ").strip()
        src_cell = input("ID ячейки-отправителя (C1, C2, C3): ").strip()
        prod_id = input("ID товара: ").strip()
        qty_str = input("Количество: ").strip()
        target_type = input("Тип получателя (warehouse или pos): ").strip().lower()
        target_id = input("ID получателя: ").strip()
        target_cell = None

        if target_type == "warehouse":
            target_cell = input("ID целевой ячейки склада: ").strip()

        try:
            qty = int(qty_str)
            if qty <= 0:
                print("Ошибка: количество должно быть больше 0.")

            else:
                status = self.crm.move_product(src_wh, src_cell, prod_id, qty, target_type, target_id, target_cell)
                print(status)

        except ValueError:
            print("Ошибка: введено нечисловое значение.")

    def _handle_sale(self) -> None:
        """Обработка ввода параметров продажи"""

        print("\n--- Продажа товара ---")
        pos_id = input("ID пункта продаж: ").strip()
        prod_id = input("ID товара: ").strip()
        qty_str = input("Количество: ").strip()
        cust_id = input("ID покупателя: ").strip()

        try:
            qty = int(qty_str)
            if qty <= 0:
                print("Ошибка: количество должно быть больше 0.")

            else:
                status = self.crm.sell_product(pos_id, prod_id, qty, cust_id)
                print(status)

        except ValueError:
            print("Ошибка: введено нечисловое значение.")

    def _handle_return(self) -> None:
        """Обработка ввода параметров возврата"""

        print("\n--- Возврат товара ---")
        order_id = input("ID заказа продажи (например, ORD1): ").strip()
        pos_id = input("ID пункта продаж для приемки: ").strip()

        status = self.crm.return_product(order_id, pos_id)
        print(status)

    def _handle_hire(self) -> None:
        """Обработка ввода параметров найма"""

        print("\n--- Найм сотрудника ---")
        emp_id = input("Задайте ID сотрудника: ").strip()
        name = input("ФИО: ").strip()
        phone = input("Телефон: ").strip()
        role = input("Должность: ").strip()
        salary_str = input("Оклад: ").strip()

        try:
            salary = float(salary_str)
            if salary < 0:
                print("Ошибка: оклад не может быть отрицательным.")

            else:
                status = self.crm.hire_employee(emp_id, name, phone, role, salary)
                print(status)

        except ValueError:
            print("Ошибка: некорректный формат оклада.")

    def _handle_fire(self) -> None:
        """Обработка параметров увольнения"""

        print("\n--- Увольнение сотрудника ---")
        emp_id = input("ID увольняемого сотрудника: ").strip()
        status = self.crm.fire_employee(emp_id)
        print(status)

    def _handle_customer_registration(self) -> None:
        """Обработка ввода параметров клиента"""

        print("\n--- Регистрация клиента ---")
        cust_id = input("ID клиента: ").strip()
        name = input("ФИО: ").strip()
        phone = input("Телефон: ").strip()
        discount_str = input("Скидка (например, 0.05 для 5%): ").strip()

        try:
            discount = float(discount_str)
            if not 0.0 <= discount <= 1.0:
                print("Ошибка: скидка должна быть в диапазоне от 0.0 до 1.0.")

            else:
                status = self.crm.register_customer(cust_id, name, phone, discount)
                print(status)

        except ValueError:
            print("Ошибка: некорректный формат скидки.")

    def _handle_open_warehouse(self) -> None:
        """Обработка создания нового склада"""

        print("\n--- Открытие склада ---")
        wh_id = input("ID склада: ").strip()
        name = input("Название: ").strip()
        mgr_id = input("ID ответственного (оставьте пустым, если нет): ").strip()
        mgr_id = mgr_id if mgr_id else None

        status = self.crm.open_warehouse(wh_id, name, mgr_id)
        print(status)

    def _handle_close_warehouse(self) -> None:
        """Обработка удаления склада"""

        print("\n--- Закрытие склада ---")
        wh_id = input("ID склада для закрытия: ").strip()
        status = self.crm.close_warehouse(wh_id)
        print(status)

    def _handle_open_pos(self) -> None:
        """Обработка создания пункта продаж"""

        print("\n--- Открытие пункта продаж ---")
        pos_id = input("ID пункта продаж: ").strip()
        name = input("Название: ").strip()
        mgr_id = input("ID менеджера (оставьте пустым, если нет): ").strip()
        mgr_id = mgr_id if mgr_id else None

        status = self.crm.open_pos(pos_id, name, mgr_id)
        print(status)

    def _handle_close_pos(self) -> None:
        """Обработка закрытия пункта продаж"""

        print("\n--- Закрытие пункта продаж ---")
        pos_id = input("ID пункта продаж для закрытия: ").strip()
        status = self.crm.close_pos(pos_id)
        print(status)

    def _handle_change_manager(self) -> None:
        """Обработка переназначения ответственного"""

        print("\n--- Смена ответственного лица ---")
        entity_type = input("Тип объекта (warehouse или pos): ").strip().lower()
        entity_id = input("ID объекта: ").strip()
        mgr_id = input("ID сотрудника: ").strip()

        status = self.crm.change_manager(entity_type, entity_id, mgr_id)
        print(status)