"""
Entrega 4, segunda metade — geracao do codigo executavel.

Traduz as instrucoes de tres enderecos para instrucoes legiveis da VM de pilha.
"""
import re


OPERADORES = {
    '+': 'add',
    '-': 'sub',
    '*': 'mul',
    '/': 'div',
    '%': 'mod',
    '==': 'eq',
    '!=': 'ne',
    '<': 'lt',
    '<=': 'le',
    '>': 'gt',
    '>=': 'ge',
    'e': 'and',
    'ou': 'or',
}


def _valor(valor):
    valor = valor.strip()
    if valor in ('verdadeiro', 'falso') or valor.startswith('"'):
        return [f'const {valor}']
    if valor.startswith('$t') and valor[2:].isdigit():
        return [f'load {valor}']
    if valor and (valor[0].isalpha() or valor[0] == '_'):
        return [f'load {valor}']
    return [f'const {valor}']


def _expressao(expressao):
    expressao = expressao.strip()
    if expressao.startswith('real '):
        return _valor(expressao.split(maxsplit=1)[1]) + ['to_real']
    if expressao.startswith('nao '):
        return _valor(expressao.split(maxsplit=1)[1]) + ['not']
    if expressao.startswith('- '):
        return _valor(expressao.split(maxsplit=1)[1]) + ['neg']
    binario = re.match(
        r'("(?:\\.|[^"\\])*"|\S+)\s+(==|!=|<=|>=|[+\-*/%<>]|e|ou)\s+(.+)$',
        expressao)
    if binario:
        esquerda, operador, direita = binario.groups()
        instrucao = OPERADORES.get(operador)
        if instrucao:
            return _valor(esquerda) + _valor(direita) + [instrucao]
    return _valor(expressao)


def _traduzir(linha):
    if linha.startswith('funcao ') or linha.startswith('param ') or linha.startswith('local '):
        return [linha]
    if linha in ('scope_push', 'scope_pop', 'fim', 'descarta'):
        return [linha]
    if linha.startswith('.linha '):
        return [linha]
    if linha.endswith(':'):
        return [linha]
    if linha.startswith('desvie '):
        return [linha]
    if linha.startswith('seFalso '):
        _, condicao, _, destino = linha.split()
        return _valor(condicao) + [f'jz {destino}']
    if linha.startswith('escreva '):
        return _expressao(linha.split(maxsplit=1)[1]) + ['print']
    if linha == 'retorne':
        return [linha]
    if linha.startswith('retorne '):
        return _expressao(linha.split(maxsplit=1)[1]) + ['retorne']
    if linha.startswith('argumento '):
        return _valor(linha.split(maxsplit=1)[1])
    if linha.startswith('chama '):
        _, nome, quantidade = linha.split()
        return [f'call {nome} {quantidade}']
    if ' = ' in linha:
        destino, expressao = linha.split(' = ', 1)
        if expressao == 'resultado_chamada':
            return [f'store {destino}']
        return _expressao(expressao) + [f'store {destino}']
    return [linha]


def gerar(codigo_intermediario):
    """Devolve as linhas do arquivo .mplb."""
    resultado = []
    for linha in codigo_intermediario:
        resultado.extend(_traduzir(linha))
    return resultado
