from crm_service import CRMService
from ui import ConsoleUI


def main() -> None:
    """Запуск программы"""

    crm_service = CRMService(data_dir="data")
    ui = ConsoleUI(crm_service)
    ui.run()


if __name__ == "__main__":
    main()
    