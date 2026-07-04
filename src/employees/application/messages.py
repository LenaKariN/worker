from __future__ import annotations

ERR_PREFIX = "Ошибка"
ERR_VALIDATION_PREFIX = "Ошибка валидации"

LABEL_YES = "да"
LABEL_NO = "нет"

LABEL_PRESENT_TIME = "настоящее время"

FMT_DATE = "%Y-%m-%d"
FMT_DATETIME = "%Y-%m-%d %H:%M:%S"
MSG_INVALID_DATE_FORMAT = "Дата должна быть в формате YYYY-MM-DD"

NULL_PLACEHOLDER = "—"

GROUP_EMPLOYEE = "employee"
GROUP_POSITION = "position"

SORT_UP = "up"
SORT_DOWN = "down"

MSG_EMPTY_EMPLOYEE_LIST = "Список сотрудников пуст."
MSG_EMPTY_POSITION_LIST = "Справочник позиций пуст."

MSG_SALARY_MUST_BE_NUMBER = "зарплата должна быть числом"
MSG_SALARY_NEGATIVE = "Зарплата не может быть отрицательной"

MSG_ID_EMPTY = "id не может быть пустым"
MSG_ID_NOT_SPECIFIED = "укажите --id сотрудника"

MSG_CODE_EMPTY = "code не может быть пустым"
MSG_CODE_NOT_SPECIFIED = "укажите --code позиции"

MSG_CODE_VALIDATION = (
    "code должен содержать только латинские буквы, цифры и подчёркивание"
)

MSG_POSITION_NOT_FOUND = "должность с кодом '{code}' не найдена в справочнике"

MSG_EMPLOYEE_NOT_FOUND = "сотрудник с id '{id}' не найден"
MSG_POSITION_NOT_FOUND_CODE = "позиция с кодом '{code}' не найдена"

MSG_DUPLICATE_POSITION = "позиция с кодом '{code}' уже существует"
MSG_DUPLICATE_EMPLOYEE = (
    "сотрудник '{last_name} {first_name}' с телефоном '{phone}' уже существует"
)

MSG_FIELD_NOT_FOUND = "Нет поля с номером {field_no}. Допустимые: {valid_range}"

MSG_LAST_NAME_EMPTY = "Фамилия не может быть пустой"
MSG_FIRST_NAME_EMPTY = "Имя не может быть пустым"
MSG_PHONE_EMPTY = "Телефон не может быть пустым"
MSG_NAME_EMPTY = "Наименование не может быть пустым"
MSG_POSITION_CODE_EMPTY = "Код должности не может быть пустым"
MSG_NAME_TOO_LONG = "Наименование не может быть длиннее 200 символов"
MSG_DESCRIPTION_TOO_LONG = "Описание не может быть длиннее 2000 символов"

MSG_DATE_START_AFTER_END = "Дата начала должна быть раньше даты окончания"
MSG_DATE_END_BEFORE_START = "Дата окончания должна быть позже даты начала"

MSG_CANNOT_CHANGE_REFERENCED_CODE = (
    "Нельзя изменить код '{code}': на него ссылаются сотрудники"
)
MSG_DUPLICATE_EMPLOYEE_UPDATE = "Сотрудник с такими ФИО и телефоном уже существует"
MSG_DUPLICATE_CODE = "Элемент с кодом '{code}' уже существует"

MSG_PARSE_ERROR = "Ошибка разбора команды: {exc}"
MSG_EXIT_CODE = "[код выхода: {exit_code}]"

MSG_DIALOG_PROMPT = "Введите <номер> <значение> или 0 для выхода: "
MSG_DIALOG_INVALID_FORMAT = "Ошибка: введите номер поля и значение через пробел."
MSG_DIALOG_FIELD_NOT_NUMBER = "Ошибка: номер поля должен быть числом."
MSG_DIALOG_UPDATED = " обновлен(о)."

MSG_PAGE = "Страница {page}"
MSG_PAGE_TENURE = "Страница {page}, найдено: {total}"
MSG_NO_TENURE = "Нет сотрудников со стажем более {years} лет."

PAGE_UNLIMITED = 100_000


def err(msg: str) -> str:
    return f"{ERR_PREFIX}: {msg}"


def validation_err(msg: str) -> str:
    return f"{ERR_VALIDATION_PREFIX}: {msg}"
