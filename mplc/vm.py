"""
Entrega 4, terceira metade — a maquina virtual.

Cada chamada possui seu proprio registro de ativacao; a pilha de operandos e
compartilhada e preservada entre chamadas.
"""
import ast

from mplc.erros import ErroMPL


class VM:
    LIMITE_PILHA = 10000
    LIMITE_CHAMADAS = 1000

    def __init__(self, texto_mplb, saida):
        self.saida = saida
        self.linhas = [linha.strip() for linha in texto_mplb.splitlines() if linha.strip()]
        self.ip = 0
        self.pilha = []
        self.chamadas = []
        self.funcoes = {}
        self.linha_atual = 1
        self.coluna_atual = 1
        self._indexar_funcoes()

    def _indexar_funcoes(self):
        funcao_atual = None
        for indice, instrucao in enumerate(self.linhas):
            if instrucao.startswith('funcao '):
                _, nome, tipo = instrucao.split()
                funcao_atual = nome
                self.funcoes[nome] = {
                    'tipo': tipo,
                    'inicio': indice + 1,
                    'parametros': [],
                    'rotulos': {},
                }
            elif funcao_atual is not None:
                if instrucao.startswith('param '):
                    self.funcoes[funcao_atual]['parametros'].append(instrucao.split()[1])
                elif instrucao.endswith(':'):
                    self.funcoes[funcao_atual]['rotulos'][instrucao[:-1]] = indice
                elif instrucao == 'fim':
                    funcao_atual = None

    def _erro(self, mensagem):
        raise ErroMPL('execucao', self.linha_atual, self.coluna_atual, mensagem)

    def _push(self, valor):
        if len(self.pilha) >= self.LIMITE_PILHA:
            self._erro('estouro de pilha')
        self.pilha.append(valor)

    def _pop(self):
        if not self.pilha:
            self._erro('pilha vazia')
        return self.pilha.pop()

    def _frame(self):
        if not self.chamadas:
            self._erro('instrucao fora de funcao')
        return self.chamadas[-1]

    def _constante(self, texto):
        if texto == 'verdadeiro':
            return True
        if texto == 'falso':
            return False
        if texto.startswith('"'):
            try:
                return ast.literal_eval(texto)
            except (SyntaxError, ValueError):
                self._erro('literal de texto invalido')
        if '.' in texto:
            return float(texto)
        return int(texto)

    def _buscar_local(self, nome):
        for escopo in reversed(self._frame()['escopos']):
            if nome in escopo:
                return escopo[nome]
        self._erro(f"variavel '{nome}' nao inicializada")

    def _atribuir_local(self, nome, valor):
        escopos = self._frame()['escopos']
        if nome.startswith('$t') and nome[2:].isdigit():
            escopos[0][nome] = valor
            return
        for escopo in reversed(escopos):
            if nome in escopo:
                escopo[nome] = valor
                return
        escopos[-1][nome] = valor

    def _dividir(self, esquerda, direita):
        if direita == 0:
            self._erro('divisao por zero')
        if isinstance(esquerda, int) and isinstance(direita, int):
            quociente = abs(esquerda) // abs(direita)
            return -quociente if (esquerda < 0) != (direita < 0) else quociente
        return esquerda / direita

    def _restar(self, dividendo, divisor):
        if divisor == 0:
            self._erro('divisao por zero')
        quociente = abs(dividendo) // abs(divisor)
        if (dividendo < 0) != (divisor < 0):
            quociente = -quociente
        return dividendo - quociente * divisor

    def _ir_para(self, rotulo):
        funcao = self._frame()['funcao']
        destino = self.funcoes[funcao]['rotulos'].get(rotulo)
        if destino is None:
            self._erro(f"rotulo '{rotulo}' nao encontrado")
        self.ip = destino

    def _retornar(self, valor=None):
        frame = self.chamadas.pop()
        if frame['retorno_ip'] is None:
            self.ip = len(self.linhas)
            return
        self.ip = frame['retorno_ip']
        if valor is not None:
            self._push(valor)

    def _executar_instrucao(self, linha):
        if linha.startswith('.linha '):
            _, numero, coluna = linha.split()
            self.linha_atual = int(numero)
            self.coluna_atual = int(coluna)
            return
        if linha.startswith('funcao ') or linha.startswith('param '):
            return
        if linha == 'fim':
            frame = self._frame()
            self._retornar(frame['retorno'])
            return
        if linha == 'scope_push':
            self._frame()['escopos'].append({})
            return
        if linha == 'scope_pop':
            escopos = self._frame()['escopos']
            if len(escopos) <= 1:
                self._erro('escopo invalido')
            escopos.pop()
            return
        if linha.endswith(':'):
            return
        if linha.startswith('desvie '):
            self._ir_para(linha.split()[1])
            return
        if linha.startswith('jz '):
            destino = linha.split()[1]
            if not self._pop():
                self._ir_para(destino)
            return
        if linha.startswith('local '):
            _, nome, tipo = linha.split()
            padroes = {
                'inteiro': 0,
                'real': 0.0,
                'logico': False,
                'texto': '',
            }
            self._frame()['escopos'][-1][nome] = padroes[tipo]
            return
        if linha.startswith('const '):
            self._push(self._constante(linha.split(maxsplit=1)[1]))
            return
        if linha.startswith('load '):
            self._push(self._buscar_local(linha.split()[1]))
            return
        if linha.startswith('store '):
            self._atribuir_local(linha.split()[1], self._pop())
            return
        if linha.startswith('call '):
            _, nome, quantidade = linha.split()
            destino = self.funcoes.get(nome)
            if destino is None:
                self._erro(f"funcao '{nome}' nao encontrada")
            if len(self.chamadas) >= self.LIMITE_CHAMADAS:
                self._erro('estouro de pilha')
            quantidade = int(quantidade)
            argumentos = [self._pop() for _ in range(quantidade)]
            argumentos.reverse()
            if quantidade != len(destino['parametros']):
                self._erro('quantidade de argumentos invalida')
            frame = {
                'funcao': nome,
                'retorno_ip': self.ip,
                'retorno': None,
                'escopos': [dict(zip(destino['parametros'], argumentos))],
            }
            self.chamadas.append(frame)
            self.ip = destino['inicio']
            return
        if linha == 'retorne':
            self._retornar()
            return
        if linha.startswith('print'):
            valor = self._pop()
            if isinstance(valor, bool):
                texto = 'verdadeiro' if valor else 'falso'
            elif isinstance(valor, float):
                texto = f'{valor:.6f}'
            else:
                texto = str(valor)
            self.saida.write(texto + '\n')
            return
        if linha == 'descarta':
            self._pop()
            return

        unarios = {
            'not': lambda valor: not valor,
            'neg': lambda valor: -valor,
            'to_real': lambda valor: float(valor),
        }
        if linha in unarios:
            self._push(unarios[linha](self._pop()))
            return

        if linha in ('add', 'sub', 'mul', 'div', 'mod', 'eq', 'ne', 'lt',
                     'le', 'gt', 'ge', 'and', 'or'):
            direita = self._pop()
            esquerda = self._pop()
            operacoes = {
                'add': lambda a, b: a + b,
                'sub': lambda a, b: a - b,
                'mul': lambda a, b: a * b,
                'div': self._dividir,
                'mod': self._restar,
                'eq': lambda a, b: a == b,
                'ne': lambda a, b: a != b,
                'lt': lambda a, b: a < b,
                'le': lambda a, b: a <= b,
                'gt': lambda a, b: a > b,
                'ge': lambda a, b: a >= b,
                'and': lambda a, b: a and b,
                'or': lambda a, b: a or b,
            }
            self._push(operacoes[linha](esquerda, direita))
            return
        self._erro(f"instrucao desconhecida: {linha}")

    def executar(self):
        principal = self.funcoes.get('principal')
        if principal is None:
            self._erro("funcao 'principal' nao encontrada")
        self.chamadas.append({
            'funcao': 'principal',
            'retorno_ip': None,
            'retorno': None,
            'escopos': [{}],
        })
        self.ip = principal['inicio']
        while self.ip < len(self.linhas):
            linha = self.linhas[self.ip]
            self.ip += 1
            self._executar_instrucao(linha)


def executar(texto_mplb, saida):
    """Executa o bytecode e escreve a saida MPL em `saida`."""
    VM(texto_mplb, saida).executar()
