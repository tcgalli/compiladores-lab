"""
Entrega 3 — analise semantica.

Tabela de simbolos, escopos aninhados e verificacao de tipos.
"""
from mplc.erros import ErroMPL


TIPOS_NUMERICOS = {'inteiro', 'real'}
TIPOS_VALOR = {'inteiro', 'real', 'logico', 'texto'}


class Simbolo:
    def __init__(self, nome, categoria, tipo, linha, parametros=None):
        self.nome = nome
        self.categoria = categoria
        self.tipo = tipo
        self.linha = linha
        self.parametros = parametros or []


class Escopo:
    def __init__(self, numero, descricao, pai):
        self.numero = numero
        self.descricao = descricao
        self.pai = pai
        self.simbolos = []

    def buscar_local(self, nome):
        return next((s for s in self.simbolos if s.nome == nome), None)

    def buscar(self, nome):
        escopo = self
        while escopo is not None:
            simbolo = escopo.buscar_local(nome)
            if simbolo is not None:
                return simbolo
            escopo = escopo.pai
        return None

    def declarar(self, simbolo, no):
        if self.buscar_local(simbolo.nome) is not None:
            _erro(no, f"'{simbolo.nome}' ja declarado neste escopo")
        self.simbolos.append(simbolo)


class Tabela:
    def __init__(self):
        self.escopos = [Escopo(0, 'global', None)]
        self.funcoes = {}

    def abrir_escopo(self, descricao, pai):
        escopo = Escopo(len(self.escopos), descricao, pai)
        self.escopos.append(escopo)
        return escopo


def _erro(no, mensagem):
    raise ErroMPL('semantico', getattr(no, 'linha', 0) or 1,
                  getattr(no, 'coluna', 0) or 1, mensagem)


def _partes(no, prefixo, quantidade):
    partes = no.rotulo.split()
    if len(partes) != quantidade or partes[0] != prefixo:
        _erro(no, f'arvore invalida: esperado {prefixo}')
    return partes


def _compativel(destino, origem):
    return destino == origem or (destino == 'real' and origem == 'inteiro')


class Analisador:
    def __init__(self, arvore):
        self.arvore = arvore
        self.tabela = Tabela()

    def analisar(self):
        if not self.arvore.rotulo == 'programa':
            _erro(self.arvore, 'arvore invalida: esperado programa')

        self._coletar_assinaturas()
        if 'principal' not in self.tabela.funcoes:
            _erro(self.arvore, "funcao 'principal' nao declarada")
        principal = self.tabela.funcoes['principal']
        if principal.parametros:
            _erro(self._no_funcao('principal'), "principal nao pode receber parametros")
        if principal.tipo != 'vazio':
            _erro(self._no_funcao('principal'), "principal deve retornar vazio")

        for funcao in self.arvore.filhos:
            self._analisar_funcao(funcao)
        return self.tabela

    def _no_funcao(self, nome):
        return next(no for no in self.arvore.filhos
                    if _partes(no, 'funcao', 3)[1] == nome)

    def _coletar_assinaturas(self):
        global_ = self.tabela.escopos[0]
        for no in self.arvore.filhos:
            nome, retorno = _partes(no, 'funcao', 3)[1:]
            parametros = no.filhos[0].filhos
            tipos = []
            for parametro in parametros:
                _, _, tipo = _partes(parametro, 'parametro', 3)
                if tipo == 'vazio':
                    _erro(parametro, 'parametro nao pode ter tipo vazio')
                tipos.append(tipo)
            simbolo = Simbolo(nome, 'funcao', retorno, no.linha, tipos)
            global_.declarar(simbolo, no)
            self.tabela.funcoes[nome] = simbolo

    def _analisar_funcao(self, no):
        nome, retorno = _partes(no, 'funcao', 3)[1:]
        parametros, bloco = no.filhos
        escopo_funcao = self.tabela.abrir_escopo(
            f'funcao {nome}', self.tabela.escopos[0])

        for parametro in parametros.filhos:
            _, nome_param, tipo = _partes(parametro, 'parametro', 3)
            escopo_funcao.declarar(
                Simbolo(nome_param, 'parametro', tipo, parametro.linha), parametro)

        retorna = self._analisar_bloco(bloco, escopo_funcao, retorno)
        if retorno != 'vazio' and not retorna:
            _erro(no, f"funcao '{nome}' pode terminar sem retornar um valor")

    def _analisar_bloco(self, no, pai, tipo_retorno):
        escopo = self.tabela.abrir_escopo('bloco', pai)
        garante_retorno = False
        for comando in no.filhos:
            comando_retorna = self._analisar_comando(
                comando, escopo, tipo_retorno)
            if comando_retorna:
                garante_retorno = True
        return garante_retorno

    def _analisar_comando(self, no, escopo, tipo_retorno):
        rotulo = no.rotulo

        if rotulo == 'bloco':
            return self._analisar_bloco(no, escopo, tipo_retorno)

        if rotulo.startswith('declaracao '):
            _, nome, tipo = _partes(no, 'declaracao', 3)
            if tipo == 'vazio':
                _erro(no, 'variavel nao pode ter tipo vazio')
            escopo.declarar(Simbolo(nome, 'variavel', tipo, no.linha), no)
            if no.filhos:
                inicializador = no.filhos[0]
                tipo_expr = self._expressao(inicializador, escopo)
                if not _compativel(tipo, tipo_expr):
                    _erro(no, f"nao e possivel inicializar {tipo} com {tipo_expr}")
            return False

        if rotulo.startswith('atribuicao '):
            _, nome = _partes(no, 'atribuicao', 2)
            simbolo = escopo.buscar(nome)
            if simbolo is None or simbolo.categoria == 'funcao':
                _erro(no, f"variavel '{nome}' nao declarada")
            tipo_expr = self._expressao(no.filhos[0], escopo)
            if not _compativel(simbolo.tipo, tipo_expr):
                _erro(no, f"nao e possivel atribuir {tipo_expr} a {simbolo.tipo}")
            return False

        if rotulo == 'se':
            if self._expressao(no.filhos[0], escopo) != 'logico':
                _erro(no.filhos[0], 'a condicao do se deve ser logica')
            retorna_entao = self._analisar_bloco(
                no.filhos[1], escopo, tipo_retorno)
            if len(no.filhos) == 3:
                retorna_senao = self._analisar_bloco(
                    no.filhos[2], escopo, tipo_retorno)
                return retorna_entao and retorna_senao
            return False

        if rotulo == 'enquanto':
            if self._expressao(no.filhos[0], escopo) != 'logico':
                _erro(no.filhos[0], 'a condicao do enquanto deve ser logica')
            self._analisar_bloco(no.filhos[1], escopo, tipo_retorno)
            return False

        if rotulo == 'escreva':
            self._expressao(no.filhos[0], escopo)
            return False

        if rotulo == 'retorne':
            if tipo_retorno == 'vazio':
                if no.filhos:
                    _erro(no, 'funcao vazio nao pode retornar um valor')
            elif not no.filhos:
                _erro(no, 'funcao deve retornar um valor')
            else:
                tipo_expr = self._expressao(no.filhos[0], escopo)
                if not _compativel(tipo_retorno, tipo_expr):
                    _erro(no, f"retorno {tipo_expr} incompativel com {tipo_retorno}")
            return True

        if rotulo.startswith('chamada '):
            self._chamada(no, escopo, como_comando=True)
            return False

        _erro(no, f"comando desconhecido '{rotulo}'")

    def _expressao(self, no, escopo):
        rotulo = no.rotulo

        if rotulo.startswith('literal '):
            partes = rotulo.split(maxsplit=2)
            if len(partes) != 3:
                _erro(no, 'arvore invalida: literal incompleto')
            tipo = partes[1]
            if tipo not in TIPOS_VALOR:
                _erro(no, f"tipo de literal invalido '{tipo}'")
            return tipo

        if rotulo.startswith('variavel '):
            _, nome = _partes(no, 'variavel', 2)
            simbolo = escopo.buscar(nome)
            if simbolo is None or simbolo.categoria == 'funcao':
                _erro(no, f"variavel '{nome}' nao declarada")
            return simbolo.tipo

        if rotulo.startswith('chamada '):
            return self._chamada(no, escopo, como_comando=False)

        if rotulo.startswith('unario '):
            operador = _partes(no, 'unario', 2)[1]
            tipo = self._expressao(no.filhos[0], escopo)
            if operador == 'nao' and tipo == 'logico':
                return 'logico'
            if operador == '-' and tipo in TIPOS_NUMERICOS:
                return tipo
            _erro(no, f"operador unario {operador} nao aceita {tipo}")

        if rotulo.startswith('binario '):
            operador = _partes(no, 'binario', 2)[1]
            esquerdo = self._expressao(no.filhos[0], escopo)
            direito = self._expressao(no.filhos[1], escopo)
            return self._tipo_binario(no, operador, esquerdo, direito)

        _erro(no, f"expressao desconhecida '{rotulo}'")

    def _tipo_binario(self, no, operador, esquerdo, direito):
        if operador == '+':
            if esquerdo == direito == 'texto':
                return 'texto'
            if esquerdo in TIPOS_NUMERICOS and direito in TIPOS_NUMERICOS:
                return 'real' if 'real' in (esquerdo, direito) else 'inteiro'
            _erro(no, f"operador + nao aceita {esquerdo} e {direito}")

        if operador in ('-', '*', '/'):
            if esquerdo in TIPOS_NUMERICOS and direito in TIPOS_NUMERICOS:
                return 'real' if 'real' in (esquerdo, direito) else 'inteiro'
            _erro(no, f"operador {operador} exige operandos numericos")

        if operador == '%':
            if esquerdo == direito == 'inteiro':
                return 'inteiro'
            _erro(no, 'operador % exige dois inteiros')

        if operador in ('==', '!='):
            if esquerdo == direito or {esquerdo, direito} <= TIPOS_NUMERICOS:
                return 'logico'
            _erro(no, f"nao e possivel comparar {esquerdo} e {direito}")

        if operador in ('<', '<=', '>', '>='):
            if esquerdo in TIPOS_NUMERICOS and direito in TIPOS_NUMERICOS:
                return 'logico'
            _erro(no, f"operador {operador} exige operandos numericos")

        if operador in ('e', 'ou'):
            if esquerdo == direito == 'logico':
                return 'logico'
            _erro(no, f"operador {operador} exige operandos logicos")

        _erro(no, f"operador desconhecido '{operador}'")

    def _chamada(self, no, escopo, como_comando):
        nome = _partes(no, 'chamada', 2)[1]
        funcao = self.tabela.funcoes.get(nome)
        if funcao is None:
            _erro(no, f"funcao '{nome}' nao declarada")

        if len(no.filhos) != len(funcao.parametros):
            _erro(no, f"funcao '{nome}' espera {len(funcao.parametros)} argumento(s)")

        for argumento, tipo_parametro in zip(no.filhos, funcao.parametros):
            tipo_argumento = self._expressao(argumento, escopo)
            if not _compativel(tipo_parametro, tipo_argumento):
                _erro(no, f"argumento {tipo_argumento} incompativel com {tipo_parametro}")

        if funcao.tipo == 'vazio' and not como_comando:
            _erro(no, f"funcao vazio '{nome}' nao pode ser usada em expressao")
        return funcao.tipo


def analisar(arvore):
    """Percorre a arvore, monta a tabela e confere os tipos. Devolve a tabela."""
    return Analisador(arvore).analisar()


def despejar(tabela):
    """Devolve as linhas do --tabela, no formato da secao 4 do contrato."""
    linhas = ['escopo 0 global']
    global_ = tabela.escopos[0]
    for simbolo in global_.simbolos:
        parametros = ','.join(simbolo.parametros)
        linhas.append(
            f'  {simbolo.nome}|funcao|{simbolo.tipo}({parametros})|{simbolo.linha}')

    for escopo in tabela.escopos[1:]:
        linhas.append(
            f'escopo {escopo.numero} {escopo.descricao} pai {escopo.pai.numero}')
        for simbolo in escopo.simbolos:
            linhas.append(
                f'  {simbolo.nome}|{simbolo.categoria}|{simbolo.tipo}|{simbolo.linha}')
    return linhas
