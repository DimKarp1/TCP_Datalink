class Hamming:
    @staticmethod
    def _calc_redundant_bits(m: int) -> int:
        """
        Вычисляет количество избыточных битов для данных длины m.
        
        Args:
            m: Длина исходных данных.
            
        Returns:
            Количество избыточных битов (r).
        """
        for i in range(m):
            if 2 ** i >= m + i + 1:
                return i
        return 0

    @staticmethod
    def _pos_redundant_bits(data: str, r: int) -> str:
        """
        Размещает избыточные биты в позициях степеней 2.
        
        Args:
            data: Исходные данные (битовая строка).
            r: Количество избыточных битов.
            
        Returns:
            Строка с добавленными нулевыми избыточными битами.
        """
        j = 0
        k = 1
        m = len(data)
        res = ''

        for i in range(1, m + r + 1):
            if i == 2 ** j:
                res += '0'
                j += 1
            else:
                res += data[-k]  # Берем биты с конца исходных данных
                k += 1

        return res[::-1]  # Разворачиваем строку

    @staticmethod
    def _calc_parity_bits(arr: str, r: int) -> str:
        """
        Вычисляет значения контрольных битов.
        
        Args:
            arr: Данные с нулевыми избыточными битами.
            r: Количество избыточных битов.
            
        Returns:
            Закодированная строка с контрольными битами.
        """
        n = len(arr)

        for i in range(r):
            val = 0
            for j in range(1, n + 1):
                if j & (2 ** i):
                    val ^= int(arr[-j])  # XOR для битов на нужных позициях
            
            # Вставляем вычисленный бит четности
            pos = n - (2 ** i)
            arr = arr[:pos] + str(val) + arr[pos + 1:]

        return arr[::-1]  # Разворачиваем результат

    @staticmethod
    def _detect_error(arr: str) -> int:
        """Находит позицию ошибки (0 если ошибок нет)."""
        nr = 0
        for i in range(1, len(arr)):
            if 2 ** i >= len(arr):
                nr = i
                break

        res = 0
        for i in range(nr):
            val = 0
            for j in range(1, len(arr) + 1):
                if j & (2 ** i):
                    val ^= int(arr[j - 1])
            res += val * (10 ** i)

        error_pos = int(str(res), 2)
        return error_pos

    @staticmethod
    def _fix_error(data: str) -> str:
        """Исправляет ошибку в данных."""
        n_error = Hamming._detect_error(data)
        if n_error == 0:
            return data
        corrected_bit = '0' if data[n_error - 1] == '1' else '1'
        return Hamming._replace_at(data, n_error - 1, corrected_bit)

    @staticmethod
    def _decoding_ham(data: str) -> str:
        """Декодирует данные, удаляя контрольные биты."""
        data = Hamming._fix_error(data)
        nr = 0
        for i in range(1, len(data)):
            if 2 ** i >= len(data):
                nr = i
                break

        for i in range(nr - 1, -1, -1):
            pos = 2 ** i - 1
            data = data[:pos] + data[pos + 1:]
        return data[::-1]

    @staticmethod
    def _replace_at(s: str, index: int, replacement: str) -> str:
        """Заменяет символ в строке по индексу."""
        return s[:index] + replacement + s[index + 1:]

    @classmethod
    def decode(cls, data: str) -> str:
        """Декодирует данные с исправлением ошибок."""
        return cls._decoding_ham(data)

    @classmethod
    def encode(cls, data: str) -> str:
        """
        Кодирует данные кодом Хэмминга.
        
        Args:
            data: Исходные данные (битовая строка).
            
        Returns:
            Закодированная строка.
        """
        r = cls._calc_redundant_bits(len(data))
        data_with_zeros = cls._pos_redundant_bits(data, r)
        return cls._calc_parity_bits(data_with_zeros, r)
