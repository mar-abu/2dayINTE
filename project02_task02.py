import os
from typing import List, Dict
from datetime import datetime
from langchain_gigachat import GigaChat
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel
import json
from dotenv import load_dotenv

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

class CitizenRequestClassifier:
    def __init__(self):
        """Инициализация классификатора обращений граждан."""
        self.llm = GigaChat(
            credentials=os.getenv('GIGACHAT_CREDENTIALS'),
            verify_ssl_certs=False
        )
        
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
            
            return result
            
        except Exception as e:
            print(f"Ошибка при классификации: {e}")
            return CitizenRequest(
                request_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                request_topic="Не удалось определить тему",
                target_department="Не определено"
            )

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