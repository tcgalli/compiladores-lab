"""
Entrega 4, primeira metade — codigo de tres enderecos.

Cada operacao binaria ou unaria e isolada numa instrucao com temporario.
"""


class GeradorIR:
    def __init__(self, tabela):
        self.tabela = tabela
        self.linhas = []
        self.temp = 0
        self.label = 0
        self.escopos = []

    def _emit(self, linha):
        self.linhas.append(linha)

    def _novo_temp(self):
        temp = f'$t{self.temp}'
        self.temp += 1
        return temp

    def _novo_label(self):
        label = f'L{self.label}'
        self.label += 1
        return label

    def _tipo_nome(self, nome):
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return None

    def _tipo_expr(self, no):
        rotulo = no.rotulo
        if rotulo.startswith('literal '):
            return rotulo.split(maxsplit=2)[1]
        if rotulo.startswith('variavel '):
            return self._tipo_nome(rotulo.split(maxsplit=1)[1])
        if rotulo.startswith('chamada '):
            return self.tabela.funcoes[rotulo.split()[1]].tipo
        if rotulo.startswith('unario '):
            op = rotulo.split(maxsplit=1)[1]
            return 'logico' if op == 'nao' else self._tipo_expr(no.filhos[0])
        if rotulo.startswith('binario '):
            op = rotulo.split(maxsplit=1)[1]
            esq = self._tipo_expr(no.filhos[0])
            dir_ = self._tipo_expr(no.filhos[1])
            if op in ('+', '-', '*', '/'):
                if op == '+' and esq == dir_ == 'texto':
                    return 'texto'
                return 'real' if 'real' in (esq, dir_) else 'inteiro'
            if op == '%':
                return 'inteiro'
            return 'logico'
        return None

    def _convert_real(self, valor, tipo):
        if tipo == 'inteiro':
            temp = self._novo_temp()
            self._emit(f'{temp} = real {valor}')
            return temp
        return valor

    def _expr(self, no):
        rotulo = no.rotulo
        if rotulo.startswith('literal '):
            return rotulo.split(maxsplit=2)[2]
        if rotulo.startswith('variavel '):
            return rotulo.split(maxsplit=1)[1]
        if rotulo.startswith('unario '):
            op = rotulo.split(maxsplit=1)[1]
            operando = self._expr(no.filhos[0])
            temp = self._novo_temp()
            self._emit(f'{temp} = {op} {operando}')
            return temp
        if rotulo.startswith('binario '):
            op = rotulo.split(maxsplit=1)[1]
            esquerda_no, direita_no = no.filhos
            esquerda = self._expr(esquerda_no)
            direita = self._expr(direita_no)
            if op != '%' and self._tipo_expr(esquerda_no) != self._tipo_expr(direita_no):
                if self._tipo_expr(esquerda_no) == 'inteiro':
                    esquerda = self._convert_real(esquerda, 'inteiro')
                if self._tipo_expr(direita_no) == 'inteiro':
                    direita = self._convert_real(direita, 'inteiro')
            temp = self._novo_temp()
            self._emit(f'{temp} = {esquerda} {op} {direita}')
            return temp
        if rotulo.startswith('chamada '):
            nome = rotulo.split()[1]
            assinatura = self.tabela.funcoes[nome].parametros
            for argumento, tipo_param in zip(no.filhos, assinatura):
                valor = self._expr(argumento)
                valor = self._convert_real(valor, self._tipo_expr(argumento)) if tipo_param == 'real' else valor
                self._emit(f'argumento {valor}')
            self._emit(f'chama {nome} {len(no.filhos)}')
            temp = self._novo_temp()
            self._emit(f'{temp} = resultado_chamada')
            return temp
        raise ValueError(f'expressao desconhecida: {rotulo}')

    def _bloco(self, no):
        self._emit('scope_push')
        self.escopos.append({})
        for comando in no.filhos:
            self._comando(comando)
        self.escopos.pop()
        self._emit('scope_pop')

    def _comando(self, no):
        rotulo = no.rotulo
        self._emit(f'.linha {getattr(no, "linha", 1) or 1} {getattr(no, "coluna", 1) or 1}')

        if rotulo == 'bloco':
            self._bloco(no)
            return

        if rotulo.startswith('declaracao '):
            _, nome, tipo = rotulo.split(maxsplit=2)
            self.escopos[-1][nome] = tipo
            self._emit(f'local {nome} {tipo}')
            if no.filhos:
                valor = self._expr(no.filhos[0])
                valor = self._convert_real(valor, self._tipo_expr(no.filhos[0])) if tipo == 'real' else valor
                self._emit(f'{nome} = {valor}')
            return

        if rotulo.startswith('atribuicao '):
            nome = rotulo.split(maxsplit=1)[1]
            tipo = self._tipo_nome(nome)
            valor = self._expr(no.filhos[0])
            valor = self._convert_real(valor, self._tipo_expr(no.filhos[0])) if tipo == 'real' else valor
            self._emit(f'{nome} = {valor}')
            return

        if rotulo == 'se':
            fim_entao = self._novo_label()
            fim = self._novo_label() if len(no.filhos) == 3 else fim_entao
            condicao = self._expr(no.filhos[0])
            self._emit(f'seFalso {condicao} desvie {fim_entao}')
            self._bloco(no.filhos[1])
            if len(no.filhos) == 3:
                self._emit(f'desvie {fim}')
                self._emit(f'{fim_entao}:')
                self._bloco(no.filhos[2])
                self._emit(f'{fim}:')
            else:
                self._emit(f'{fim_entao}:')
            return

        if rotulo == 'enquanto':
            inicio = self._novo_label()
            fim = self._novo_label()
            self._emit(f'{inicio}:')
            self._emit(f'.linha {getattr(no, "linha", 1) or 1} {getattr(no, "coluna", 1) or 1}')
            condicao = self._expr(no.filhos[0])
            self._emit(f'seFalso {condicao} desvie {fim}')
            self._bloco(no.filhos[1])
            self._emit(f'desvie {inicio}')
            self._emit(f'{fim}:')
            return

        if rotulo == 'escreva':
            self._emit(f'escreva {self._expr(no.filhos[0])}')
            return

        if rotulo == 'retorne':
            if no.filhos:
                valor = self._expr(no.filhos[0])
                tipo_retorno = self._retorno_atual
                if tipo_retorno == 'real':
                    valor = self._convert_real(valor, self._tipo_expr(no.filhos[0]))
                self._emit(f'retorne {valor}')
            else:
                self._emit('retorne')
            return

        if rotulo.startswith('chamada '):
            nome = rotulo.split()[1]
            assinatura = self.tabela.funcoes[nome].parametros
            for argumento, tipo_param in zip(no.filhos, assinatura):
                valor = self._expr(argumento)
                valor = self._convert_real(valor, self._tipo_expr(argumento)) if tipo_param == 'real' else valor
                self._emit(f'argumento {valor}')
            self._emit(f'chama {nome} {len(no.filhos)}')
            if self.tabela.funcoes[nome].tipo != 'vazio':
                self._emit('descarta')
            return

        raise ValueError(f'comando desconhecido: {rotulo}')

    def _funcao(self, no):
        nome, retorno = no.rotulo.split()[1:3]
        self._retorno_atual = retorno
        self._emit(f'funcao {nome} {retorno}')
        self.escopos.append({})
        for parametro in no.filhos[0].filhos:
            _, nome_param, tipo_param = parametro.rotulo.split(maxsplit=2)
            self.escopos[-1][nome_param] = tipo_param
            self._emit(f'param {nome_param} {tipo_param}')
        self._bloco(no.filhos[1])
        self.escopos.pop()
        self._emit('fim')


def gerar(arvore, tabela):
    """Devolve o codigo de tres enderecos."""
    gerador = GeradorIR(tabela)
    for funcao in arvore.filhos:
        gerador._funcao(funcao)
    return gerador.linhas


def despejar(codigo):
    """Devolve as linhas do --ir."""
    return list(codigo)
