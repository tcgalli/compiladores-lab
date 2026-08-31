"""
Entrega 1 — analise lexica.

Transformar o texto do programa numa lista de tokens.

O que voces tem que devolver: uma lista de Token. O ultimo elemento e sempre
um token FIM_ARQUIVO. A regra de posicao dele esta em CONTRATOS.md, secao 7.

Leiam antes: LINGUAGEM.md secao 2, e CONTRATOS.md secao 2.
"""
from mplc.erros import ErroMPL


PALAVRAS_RESERVADAS = {
    'funcao': 'FUNCAO',
    'retorne': 'RETORNE',
    'se': 'SE',
    'senao': 'SENAO',
    'enquanto': 'ENQUANTO',
    'escreva': 'ESCREVA',
    'inteiro': 'TIPO_INTEIRO',
    'real': 'TIPO_REAL',
    'logico': 'TIPO_LOGICO',
    'texto': 'TIPO_TEXTO',
    'vazio': 'TIPO_VAZIO',
    'verdadeiro': 'LOGICO',
    'falso': 'LOGICO',
    'e': 'E',
    'ou': 'OU',
    'nao': 'NAO',
}

OPERADORES = {
    '==': 'IGUAL',
    '!=': 'DIFERENTE',
    '<=': 'MENOR_IGUAL',
    '>=': 'MAIOR_IGUAL',
    '<': 'MENOR',
    '>': 'MAIOR',
    '+': 'MAIS',
    '-': 'MENOS',
    '*': 'VEZES',
    '/': 'DIVIDE',
    '%': 'RESTO',
    '=': 'ATRIBUI',
    '(': 'ABRE_PAR',
    ')': 'FECHA_PAR',
    '{': 'ABRE_CHAVE',
    '}': 'FECHA_CHAVE',
    ',': 'VIRGULA',
    ';': 'PONTO_VIRGULA',
}

ESCAPES = {
    'n': '\n',
    't': '\t',
    '"': '"',
    '\\': '\\',
}


class Token:
    __slots__ = ('tipo', 'lexema', 'linha', 'coluna')

    def __init__(self, tipo, lexema, linha, coluna):
        self.tipo = tipo          # 'ID', 'INTEIRO', 'MAIS', ... (a lista esta no contrato)
        self.lexema = lexema      # o texto exato como apareceu no fonte
        self.linha = linha
        self.coluna = coluna      # a coluna do PRIMEIRO caractere do token

    def __str__(self):
        # esta e a linha que o --tokens imprime; nao mexam no formato
        return f"{self.linha},{self.coluna},{self.tipo},{self.lexema}"


def _eh_letra(ch):
    return ch == '_' or ('a' <= ch <= 'z') or ('A' <= ch <= 'Z')


def _eh_digito(ch):
    return '0' <= ch <= '9'


def _avancar(fonte, indice, linha, coluna):
    if indice >= len(fonte):
        return indice, linha, coluna

    ch = fonte[indice]
    indice += 1
    if ch == '\r':
        if indice < len(fonte) and fonte[indice] == '\n':
            indice += 1
        return indice, linha + 1, 1
    if ch == '\n':
        return indice, linha + 1, 1
    return indice, linha, coluna + 1


def analisar(fonte):
    """Recebe o texto do programa. Devolve a lista de Token."""
    tokens = []
    indice = 0
    linha = 1
    coluna = 1
    comprimento = len(fonte)

    while indice < comprimento:
        linha_ini = linha
        coluna_ini = coluna
        ch = fonte[indice]

        if ch in ' \t\r\n':
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            continue

        if ch == '/' and indice + 1 < comprimento and fonte[indice + 1] == '/':
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            while indice < comprimento and fonte[indice] not in '\r\n':
                indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            continue

        if ch == '/' and indice + 1 < comprimento and fonte[indice + 1] == '*':
            linha_inicio = linha_ini
            coluna_inicio = coluna_ini
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            while indice < comprimento:
                if fonte[indice] == '*' and indice + 1 < comprimento and fonte[indice + 1] == '/':
                    indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
                    indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
                    break
                indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            else:
                raise ErroMPL('lexico', linha_inicio, coluna_inicio, 'comentario de bloco nao fechado')
            continue

        if _eh_letra(ch):
            inicio = indice
            while indice < comprimento and (_eh_letra(fonte[indice]) or _eh_digito(fonte[indice])):
                indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            lexema = fonte[inicio:indice]
            tipo = PALAVRAS_RESERVADAS.get(lexema, 'ID')
            tokens.append(Token(tipo, lexema, linha_ini, coluna_ini))
            continue

        if _eh_digito(ch):
            inicio = indice
            while indice < comprimento and _eh_digito(fonte[indice]):
                indice, linha, coluna = _avancar(fonte, indice, linha, coluna)

            if indice < comprimento and fonte[indice] == '.':
                if indice + 1 < comprimento and _eh_digito(fonte[indice + 1]):
                    indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
                    while indice < comprimento and _eh_digito(fonte[indice]):
                        indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
                    lexema = fonte[inicio:indice]
                    tokens.append(Token('REAL', lexema, linha_ini, coluna_ini))
                    continue
                raise ErroMPL('lexico', linha, coluna, 'numero real invalido')

            lexema = fonte[inicio:indice]
            tokens.append(Token('INTEIRO', lexema, linha_ini, coluna_ini))
            continue

        if ch == '.':
            raise ErroMPL('lexico', linha, coluna, 'numero real invalido')

        if ch == '"':
            inicio = indice
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            while indice < comprimento:
                ch = fonte[indice]
                if ch == '"':
                    indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
                    break
                if ch == '\\':
                    if indice + 1 >= comprimento:
                        raise ErroMPL('lexico', linha_ini, coluna_ini, 'texto nao fechado')
                    esc = fonte[indice + 1]
                    if esc not in ESCAPES:
                        raise ErroMPL('lexico', linha, coluna, 'escape invalido')
                    indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
                    indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
                    continue
                if ch in '\r\n':
                    raise ErroMPL('lexico', linha_ini, coluna_ini, 'texto nao fechado')
                indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            else:
                raise ErroMPL('lexico', linha_ini, coluna_ini, 'texto nao fechado')

            lexema = fonte[inicio:indice]
            tokens.append(Token('TEXTO', lexema, linha_ini, coluna_ini))
            continue

        if ch == '!' and indice + 1 < comprimento and fonte[indice + 1] == '=':
            lexema = '!='
            tokens.append(Token('DIFERENTE', lexema, linha_ini, coluna_ini))
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            continue

        if ch == '=' and indice + 1 < comprimento and fonte[indice + 1] == '=':
            lexema = '=='
            tokens.append(Token('IGUAL', lexema, linha_ini, coluna_ini))
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            continue

        if ch == '<' and indice + 1 < comprimento and fonte[indice + 1] == '=':
            lexema = '<='
            tokens.append(Token('MENOR_IGUAL', lexema, linha_ini, coluna_ini))
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            continue

        if ch == '>' and indice + 1 < comprimento and fonte[indice + 1] == '=':
            lexema = '>='
            tokens.append(Token('MAIOR_IGUAL', lexema, linha_ini, coluna_ini))
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            continue

        if ch in OPERADORES:
            lexema = ch
            tipo = OPERADORES[ch]
            tokens.append(Token(tipo, lexema, linha_ini, coluna_ini))
            indice, linha, coluna = _avancar(fonte, indice, linha, coluna)
            continue

        raise ErroMPL('lexico', linha, coluna, f'caractere invalido: {ch!r}')

    tokens.append(Token('FIM_ARQUIVO', '', linha, coluna))
    return tokens
