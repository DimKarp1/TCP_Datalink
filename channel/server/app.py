from fastapi import FastAPI, HTTPException, Request
import json
import random
from typing import List, Dict, Any
import uvicorn
import httpx
from pydantic import BaseModel
from ham import Hamming


CHANCE_OF_ERROR = 0.08
CHANCE_OF_LOSS = 0.02  # Вероятность потери сообщения


def make_data(json_data: Dict[str, Any]) -> str:
    """
    Преобразует JSON-объект в закодированную бинарную строку с использованием кода Хэмминга [7,4].
    """
    json_str = json.dumps(json_data, ensure_ascii=False)
    byte_data = json_str.encode('utf-8')
    encoded_result = []
    
    for byte in byte_data:
        binary_byte = format(byte, '08b')
        for i in range(0, 8, 4):
            four_bits = binary_byte[i:i+4]
            if len(four_bits) < 4:
                four_bits = four_bits.ljust(4, '0')
            encoded_block = Hamming.encode(four_bits)
            encoded_result.append(encoded_block)
    
    return ''.join(encoded_result)


def make_mistake(encoded_data: str) -> str:
    """
    Вносит ровно одну случайную ошибку в закодированные данные.
    """
    if random.random() > CHANCE_OF_ERROR:
        return encoded_data
    print('Бит испорчен')
    error_pos = random.randint(0, len(encoded_data) - 1)
    corrupted_bit = '1' if encoded_data[error_pos] == '0' else '0'
    corrupted_data = encoded_data[:error_pos] + corrupted_bit + encoded_data[error_pos + 1:]
    return corrupted_data


def decode_data(encoded_data: str) -> dict:
    """
    Декодирует данные, закодированные кодом Хэмминга [7,4].
    """
    hamming_blocks = [encoded_data[i:i+7] for i in range(0, len(encoded_data), 7)]
    decoded_bits = []
    
    for block in hamming_blocks:
        decoded_block = Hamming.decode(block)
        decoded_bits.append(decoded_block)
    
    full_binary = ''.join(decoded_bits)
    byte_array = bytearray()
    
    for i in range(0, len(full_binary), 8):
        byte_str = full_binary[i:i+8]
        if len(byte_str) == 8:
            byte_array.append(int(byte_str, 2))
    
    try:
        json_str = byte_array.decode('utf-8')
        return json.loads(json_str)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError("Ошибка декодирования данных") from e


class HammingClient(BaseModel):
    target_server_url: str

    async def transfer_segment(self, json_data: Dict[str, Any]) -> bool:
        """
        Асинхронно отправляет JSON-данные на целевой сервер.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.target_server_url,
                    json=json_data,
                    timeout=10.0
                )
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                print(f"Ошибка при отправке данных: {e}")
                return False


app = FastAPI()


@app.post("/CodeSegment")
async def process_hamming(request: Request):
    """
    Обрабатывает входящий JSON с применением кодирования Хэмминга.
    """
    try:
        json_data = await request.json()
        client = HammingClient(target_server_url="http://192.168.68.145:8081/TransferSegment")
        print("Received JSON:", json_data)

        encoded_data = make_data(json_data)
        print('Закодировано')
        corrupted_data = make_mistake(encoded_data)
        
        if random.random() > CHANCE_OF_ERROR:
            decoded_data = decode_data(corrupted_data)
            print('decoded', decoded_data)
            if not await client.transfer_segment(decoded_data):
                print("Ошибка передачи сегмента Роме")
            return {"status": "success", "data": decoded_data}
        else:
            print('Пакет потерян')

    except Exception as e:
        print(str(e)+' segment')
    

@app.post("/CodeReceipt")
async def process_hamming(request: Request):
    """
    Обрабатывает входящие квитанции с применением кодирования Хэмминга.
    """
    try:
        json_data = await request.json()
        client = HammingClient(target_server_url="http://192.168.68.145:8080/TransferReceipt")
        print("Received JSON:", json_data)

        encoded_data = make_data(json_data)
        print('Закодировано')
        corrupted_data = make_mistake(encoded_data)
        
        if random.random() > CHANCE_OF_LOSS:
            decoded_data = decode_data(corrupted_data)
            print('decoded', decoded_data)
            if not await client.transfer_segment(decoded_data):
                print("Ошибка передачи рецепта Роме")
            return {"status": "success", "data": decoded_data}
        else:
            print('Пакет потерян')

    except Exception as e:
        print(str(e)+' receipt')


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3050)
