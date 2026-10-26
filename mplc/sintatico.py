"""
Entrega 2 — analise sintatica.

Transformar a lista de tokens numa arvore.

Sugestao forte: descida recursiva, uma funcao por nivel de precedencia, na
ordem da secao 3.3 da especificacao. E como voces vao enxergar a precedencia
virar formato de arvore.

Gerador de parser (ANTLR, PLY, yacc) esta proibido nesta entrega e na
anterior — o objetivo e entender, e o gerador esconde exatamente a parte
que esta sendo ensinada.

Leiam antes: LINGUAGEM.md secoes 3 a 5, e CONTRATOS.md secao 3.
"""
from mplc.erros import ErroMPL


TIPOS = {
    'TIPO_INTEIRO': 'inteiro',
    'TIPO_REAL': 'real',
    'TIPO_LOGICO': 'logico',
    'TIPO_TEXTO': 'texto',
    'TIPO_VAZIO': 'vazio',
}

OPERADORES = {
    'MAIS': '+',
    'MENOS': '-',
    'VEZES': '*',
    'DIVIDE': '/',
    'RESTO': '%',
    'IGUAL': '==',
    'DIFERENTE': '!=',
    'MENOR': '<',
    'MENOR_IGUAL': '<=',
    'MAIOR': '>',
    'MAIOR_IGUAL': '>=',
    'E': 'e',
    'OU': 'ou',
    'NAO': 'nao',
}


class No:
    """Um no da arvore. O rotulo e o que sai no --ast."""

    def __init__(self, rotulo, filhos=None, linha=0, coluna=0, **extra):
        self.rotulo = rotulo      # 'binario +', 'literal inteiro 1', 'bloco', ...
        self.filhos = filhos or []
        self.linha = linha
        self.coluna = coluna
        self.extra = extra        # o que a semantica quiser pendurar depois


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.indice = 0

    def atual(self):
        return self.tokens[self.indice]

    def anterior(self):
        return self.tokens[self.indice - 1]

    def consumir(self, *tipos):
        tok = self.atual()
        if tok.tipo not in tipos:
            esperados = ' ou '.join(tipos)
            raise ErroMPL('sintatico', tok.linha, tok.coluna, f'esperado {esperados}, mas veio {tok.tipo}')
        self.indice += 1
        return tok

    def erro(self, mensagem, tok=None):
        tok = tok if tok is not None else self.atual()
        raise ErroMPL('sintatico', tok.linha, tok.coluna, mensagem)

    def parse_programa(self):
        funcoes = []
        while self.atual().tipo != 'FIM_ARQUIVO':
            if self.atual().tipo != 'FUNCAO':
                self.erro('esperado funcao', self.atual())
            funcoes.append(self.parse_funcao())
        return No('programa', funcoes)

    def parse_funcao(self):
        inicio = self.consumir('FUNCAO')
        tipo = self.parse_tipo()
        nome = self.consumir('ID').lexema
        self.consumir('ABRE_PAR')
        parametros = self.parse_parametros()
        self.consumir('FECHA_PAR')
        bloco = self.parse_bloco()
        return No(f'funcao {nome} {tipo}', [parametros, bloco],
                  inicio.linha, inicio.coluna)

    def parse_parametros(self):
        parametros = []
        if self.atual().tipo == 'FECHA_PAR':
            return No('parametros', parametros)

        while True:
            inicio = self.atual()
            tipo = self.parse_tipo()
            nome = self.consumir('ID').lexema
            parametros.append(No(f'parametro {nome} {tipo}',
                                 linha=inicio.linha, coluna=inicio.coluna))
            if self.atual().tipo != 'VIRGULA':
                break
            self.consumir('VIRGULA')
        return No('parametros', parametros)

    def parse_bloco(self):
        inicio = self.consumir('ABRE_CHAVE')
        comandos = []
        while self.atual().tipo != 'FECHA_CHAVE':
            if self.atual().tipo == 'FIM_ARQUIVO':
                self.erro('bloco nao fechado', self.atual())
            comandos.append(self.parse_comando())
        self.consumir('FECHA_CHAVE')
        return No('bloco', comandos, inicio.linha, inicio.coluna)

    def parse_comando(self):
        tok = self.atual()

        if tok.tipo == 'ABRE_CHAVE':
            return self.parse_bloco()

        if tok.tipo in TIPOS:
            return self.parse_declaracao()

        if tok.tipo == 'SE':
            return self.parse_se()
        if tok.tipo == 'ENQUANTO':
            return self.parse_enquanto()
        if tok.tipo == 'ESCREVA':
            return self.parse_escreva()
        if tok.tipo == 'RETORNE':
            return self.parse_retorne()
        if tok.tipo == 'ID':
            if self.tokens[self.indice + 1].tipo == 'ATRIBUI':
                return self.parse_atribuicao()
            if self.tokens[self.indice + 1].tipo == 'ABRE_PAR':
                return self.parse_chamada_comando()
            self.erro('comando invalido', tok)

        self.erro('comando invalido', tok)

    def parse_tipo(self):
        tok = self.atual()
        if tok.tipo not in TIPOS:
            self.erro('esperado tipo', tok)
        self.indice += 1
        return TIPOS[tok.tipo]

    def parse_declaracao(self):
        inicio = self.atual()
        tipo = self.parse_tipo()
        nome = self.consumir('ID').lexema
        no = No(f'declaracao {nome} {tipo}', linha=inicio.linha,
                coluna=inicio.coluna)
        if self.atual().tipo == 'ATRIBUI':
            self.consumir('ATRIBUI')
            no.filhos.append(self.parse_ou())
        self.consumir('PONTO_VIRGULA')
        return no

    def parse_atribuicao(self):
        inicio = self.consumir('ID')
        nome = inicio.lexema
        self.consumir('ATRIBUI')
        expr = self.parse_ou()
        self.consumir('PONTO_VIRGULA')
        return No(f'atribuicao {nome}', [expr], inicio.linha, inicio.coluna)

    def parse_se(self):
        inicio = self.consumir('SE')
        self.consumir('ABRE_PAR')
        cond = self.parse_ou()
        self.consumir('FECHA_PAR')
        entao = self.parse_bloco()
        if self.atual().tipo == 'SENAO':
            self.consumir('SENAO')
            senao = self.parse_bloco()
            return No('se', [cond, entao, senao], inicio.linha, inicio.coluna)
        return No('se', [cond, entao], inicio.linha, inicio.coluna)

    def parse_enquanto(self):
        inicio = self.consumir('ENQUANTO')
        self.consumir('ABRE_PAR')
        cond = self.parse_ou()
        self.consumir('FECHA_PAR')
        bloco = self.parse_bloco()
        return No('enquanto', [cond, bloco], inicio.linha, inicio.coluna)

    def parse_escreva(self):
        inicio = self.consumir('ESCREVA')
        self.consumir('ABRE_PAR')
        expr = self.parse_ou()
        self.consumir('FECHA_PAR')
        self.consumir('PONTO_VIRGULA')
        return No('escreva', [expr], inicio.linha, inicio.coluna)

    def parse_retorne(self):
        inicio = self.consumir('RETORNE')
        if self.atual().tipo == 'PONTO_VIRGULA':
            self.consumir('PONTO_VIRGULA')
            return No('retorne', linha=inicio.linha, coluna=inicio.coluna)
        expr = self.parse_ou()
        self.consumir('PONTO_VIRGULA')
        return No('retorne', [expr], inicio.linha, inicio.coluna)

    def parse_chamada_comando(self):
        inicio = self.consumir('ID')
        nome = inicio.lexema
        args = self.parse_argumentos()
        self.consumir('PONTO_VIRGULA')
        return No(f'chamada {nome}', args, inicio.linha, inicio.coluna)

    def parse_argumentos(self):
        self.consumir('ABRE_PAR')
        args = []
        if self.atual().tipo != 'FECHA_PAR':
            while True:
                args.append(self.parse_ou())
                if self.atual().tipo != 'VIRGULA':
                    break
                self.consumir('VIRGULA')
        self.consumir('FECHA_PAR')
        return args

    def parse_ou(self):
        expr = self.parse_e()
        while self.atual().tipo == 'OU':
            op = self.consumir('OU')
            expr = No('binario ou', [expr, self.parse_e()], op.linha, op.coluna)
        return expr

    def parse_e(self):
        expr = self.parse_igualdade()
        while self.atual().tipo == 'E':
            op = self.consumir('E')
            expr = No('binario e', [expr, self.parse_igualdade()], op.linha, op.coluna)
        return expr

    def parse_igualdade(self):
        expr = self.parse_relacional()
        while self.atual().tipo in ('IGUAL', 'DIFERENTE'):
            operador = self.atual()
            self.consumir(operador.tipo)
            expr = No(f'binario {OPERADORES[operador.tipo]}',
                      [expr, self.parse_relacional()],
                      operador.linha, operador.coluna)
        return expr

    def parse_relacional(self):
        expr = self.parse_soma()
        while self.atual().tipo in ('MENOR', 'MENOR_IGUAL', 'MAIOR', 'MAIOR_IGUAL'):
            operador = self.atual()
            self.consumir(operador.tipo)
            expr = No(f'binario {OPERADORES[operador.tipo]}',
                      [expr, self.parse_soma()],
                      operador.linha, operador.coluna)
        return expr

    def parse_soma(self):
        expr = self.parse_multiplicacao()
        while self.atual().tipo in ('MAIS', 'MENOS'):
            operador = self.atual()
            self.consumir(operador.tipo)
            expr = No(f'binario {OPERADORES[operador.tipo]}',
                      [expr, self.parse_multiplicacao()],
                      operador.linha, operador.coluna)
        return expr

    def parse_multiplicacao(self):
        expr = self.parse_unario()
        while self.atual().tipo in ('VEZES', 'DIVIDE', 'RESTO'):
            operador = self.atual()
            self.consumir(operador.tipo)
            expr = No(f'binario {OPERADORES[operador.tipo]}',
                      [expr, self.parse_unario()],
                      operador.linha, operador.coluna)
        return expr

    def parse_unario(self):
        if self.atual().tipo == 'NAO':
            op = self.consumir('NAO')
            return No('unario nao', [self.parse_unario()], op.linha, op.coluna)
        if self.atual().tipo == 'MENOS':
            op = self.consumir('MENOS')
            return No('unario -', [self.parse_unario()], op.linha, op.coluna)
        return self.parse_primario()

    def parse_primario(self):
        tok = self.atual()

        if tok.tipo == 'ABRE_PAR':
            self.consumir('ABRE_PAR')
            expr = self.parse_ou()
            self.consumir('FECHA_PAR')
            return expr

        if tok.tipo in ('INTEIRO', 'REAL', 'LOGICO', 'TEXTO'):
            tipo = {'INTEIRO': 'inteiro', 'REAL': 'real', 'LOGICO': 'logico', 'TEXTO': 'texto'}[tok.tipo]
            self.indice += 1
            valor = tok.lexema
            if tok.tipo == 'REAL':
                valor = format(float(valor), '.6f')
            return No(f'literal {tipo} {valor}', linha=tok.linha, coluna=tok.coluna)

        if tok.tipo == 'ID':
            inicio = self.consumir('ID')
            nome = inicio.lexema
            if self.atual().tipo == 'ABRE_PAR':
                args = self.parse_argumentos()
                return No(f'chamada {nome}', args, inicio.linha, inicio.coluna)
            return No(f'variavel {nome}', linha=inicio.linha, coluna=inicio.coluna)

        self.erro('esperado expressao', tok)


def analisar(tokens):
    """Recebe a lista de Token. Devolve a raiz da arvore (um No 'programa')."""
    parser = Parser(tokens)
    return parser.parse_programa()


def despejar(no, nivel=0, saida=None):
    """Imprime a arvore no formato do --ast. Ja esta pronto: dois espacos por nivel."""
    saida = saida if saida is not None else []
    saida.append('  ' * nivel + no.rotulo)
    for f in no.filhos:
        despejar(f, nivel + 1, saida)
    return saida
