import os
from typing import List, Dict
from langchain_gigachat import GigaChat
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
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

class CitizenRequestClassifier:
    def __init__(self):
        """Инициализация классификатора обращений граждан."""
        self.llm = GigaChat(
            credentials=os.getenv('GIGACHAT_CREDENTIALS'),
            verify_ssl_certs=False
        )
        
        template = """Ты - система классификации обращений граждан. 
        Твоя задача - определить, какому департаменту следует направить обращение.
        
        Список департаментов:
        {departments}
        
        Ответь только названием департамента из списка выше.
        Если обращение можно отнести к нескольким департаментам, выбери наиболее подходящий.
        Если обращение не относится ни к одному департаменту, ответь: "Не определено"
        
        Обращение: {request}
        Департамент:"""
        
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["departments", "request"]
        )
        
        # Создаем цепочку с использованием нового синтаксиса
        self.chain = self.prompt | self.llm

    def classify_request(self, request_text: str) -> str:
        """
        Классифицирует обращение гражданина и определяет целевой департамент.
        
        Args:
            request_text (str): Текст обращения
            
        Returns:
            str: Название департамента или "Не определено"
        """
        try:
            response = self.chain.invoke({
                "departments": json.dumps(DEPARTMENTS, ensure_ascii=False, indent=2),
                "request": request_text
            })
            department = response.content.strip()
            
            # Проверяем, что ответ входит в список департаментов
            if department in DEPARTMENTS:
                return department
            return "Не определено"
            
        except Exception as e:
            print(f"Ошибка при классификации: {e}")
            return "Не определено"

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
            department = classifier.classify_request(request_text)
            
            # Вывод результата
            print("\nРезультат обработки:")
            print("-" * 30)
            if department == "Не определено":
                print("Не удалось определить подходящий департамент.")
                print("Пожалуйста, уточните ваш запрос или обратитесь к оператору.")
            else:
                print(f"Ваше обращение будет направлено в: {department}")
            print("-" * 30)
            
        except KeyboardInterrupt:
            print("\n\nЗавершение работы...")
            break
        except Exception as e:
            print(f"\nПроизошла ошибка: {e}")
            print("Пожалуйста, попробуйте еще раз.")

if __name__ == "__main__":
    main() 