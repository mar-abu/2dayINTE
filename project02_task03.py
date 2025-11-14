import os
from typing import List, Dict, Any
from datetime import datetime
from langchain_gigachat import GigaChat
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
from dotenv import load_dotenv
ihdfijbdgkdbfgkjdbgijbdfgjkg

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
DEPARTMENTS = [
    "Департамент транспорта",
    "Департамент культуры",
    "Департамент здравоохранения",
    "Департамент образования",
    "Департамент экологии",
    "Департамент физической культуры и спорта"
]

class CitizenRequest(BaseModel):
    """Модель данных обращения гражданина."""
    request_date: str
    request_topic: str
    target_department: str

class JsonSaveTool(BaseTool):
    """Инструмент для сохранения JSON в файл."""
    name: str = Field(default="json_save_tool")
    description: str = Field(default="Сохраняет данные обращения в JSON файл")
    
    def _load_existing_data(self) -> List[Dict]:
        """Загружает существующие данные из файла."""
        try:
            with open('requests.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_data(self, data: List[Dict]):
        """Сохраняет данные в файл."""
        with open('requests.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _run(self, tool_input: str = "", **kwargs) -> str:
        """Добавляет новое обращение в файл."""
        try:
            # Загружаем существующие данные
            existing_data = self._load_existing_data()
            
            # Преобразуем строку в JSON если это необходимо
            if isinstance(tool_input, str):
                try:
                    request_data = json.loads(tool_input)
                except json.JSONDecodeError:
                    request_data = kwargs
            else:
                request_data = tool_input
            
            # Добавляем новое обращение
            existing_data.append(request_data)
            
            # Сохраняем обновленные данные
            self._save_data(existing_data)
            
            return "Данные успешно сохранены в requests.json"
        except Exception as e:
            return f"Ошибка при сохранении данных: {str(e)}"

class CitizenRequestClassifier:
    def __init__(self):
        """Инициализация классификатора обращений граждан."""
        self.llm = GigaChat(
            credentials=os.getenv('GIGACHAT_CREDENTIALS'),
            verify_ssl_certs=False
        )
        
        # Инициализация инструмента сохранения JSON
        self.json_tool = JsonSaveTool()
        
        template = """Ты - система классификации обращений граждан. 
        Твоя задача - определить тему обращения и департамент, в который его следует направить.
        
        Список департаментов:
        {departments}
        
        Проанализируй обращение и верни ответ в следующем формате JSON:
        {{
            "request_topic": "краткая тема обращения (не более 5-7 слов)",
            "target_department": "название департамента из списка выше"
        }}
        
        Если обращение можно отнести к нескольким департаментам, выбери наиболее подходящий.
        Если обращение не относится ни к одному департаменту, используй "Не определено" в поле target_department.
        
        Обращение: {request}
        
        Ответ (только JSON):"""
        
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["departments", "request"]
        )
        
        self.chain = self.prompt | self.llm

    def classify_request(self, request_text: str) -> CitizenRequest:
        """
        Классифицирует обращение гражданина и определяет целевой департамент.
        
        Args:
            request_text (str): Текст обращения
            
        Returns:
            CitizenRequest: Структурированный ответ с информацией об обращении
        """
        try:
            response = self.chain.invoke({
                "departments": json.dumps(DEPARTMENTS, ensure_ascii=False, indent=2),
                "request": request_text
            })
            
            # Извлекаем JSON из ответа
            response_text = response.content.strip()
            response_data = json.loads(response_text)
            
            # Создаем объект CitizenRequest
            result = CitizenRequest(
                request_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                request_topic=response_data["request_topic"],
                target_department=response_data["target_department"]
            )
            
            # Сохраняем результат в файл
            self.json_tool._run(result.model_dump())
            
            return result
            
        except Exception as e:
            print(f"Ошибка при классификации: {e}")
            result = CitizenRequest(
                request_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                request_topic="Не удалось определить тему",
                target_department="Не определено"
            )
            
            # Сохраняем даже ошибочный результат
            self.json_tool._run(result.model_dump())
            
            return result

def main():
    """Основная функция программы."""
    print("\nДобро пожаловать в систему маршрутизации обращений граждан!")
    print("=" * 60)
    print("\nДля выхода введите 'exit' или нажмите Ctrl+C")
    print("-" * 60)
    
    # Инициализация классификатора
    try:
        classifier = CitizenRequestClassifier()
    except Exception as e:
        print(f"Ошибка при инициализации системы: {e}")
        return
    
    while True:
        try:
            # Получение обращения от пользователя
            print("\nВведите ваше обращение:")
            request_text = input("> ").strip()
            
            # Проверка на выход
            if request_text.lower() == 'exit':
                print("\nЗавершение работы...")
                break
            
            # Проверка на пустой ввод
            if not request_text:
                print("Обращение не может быть пустым. Попробуйте еще раз.")
                continue
            
            # Классификация обращения
            print("\nОбрабатываем ваше обращение...")
            result = classifier.classify_request(request_text)
            
            # Вывод результата в JSON
            print("\nРезультат обработки:")
            print("-" * 30)
            print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
            print("-" * 30)
            
        except KeyboardInterrupt:
            print("\n\nЗавершение работы...")
            break
        except Exception as e:
            print(f"\nПроизошла ошибка: {e}")
            print("Пожалуйста, попробуйте еще раз.")

if __name__ == "__main__":
    main() 