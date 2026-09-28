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
        self.consumir('FUNCAO')
        tipo = self.parse_tipo()
        nome = self.consumir('ID').lexema
        self.consumir('ABRE_PAR')
        parametros = self.parse_parametros()
        self.consumir('FECHA_PAR')
        bloco = self.parse_bloco()
        return No(f'funcao {nome} {tipo}', [parametros, bloco])

    def parse_parametros(self):
        parametros = []
        if self.atual().tipo == 'FECHA_PAR':
            return No('parametros', parametros)

        while True:
            tipo = self.parse_tipo()
            nome = self.consumir('ID').lexema
            parametros.append(No(f'parametro {nome} {tipo}'))
            if self.atual().tipo != 'VIRGULA':
                break
            self.consumir('VIRGULA')
        return No('parametros', parametros)

    def parse_bloco(self):
        self.consumir('ABRE_CHAVE')
        comandos = []
        while self.atual().tipo != 'FECHA_CHAVE':
            if self.atual().tipo == 'FIM_ARQUIVO':
                self.erro('bloco nao fechado', self.atual())
            comandos.append(self.parse_comando())
        self.consumir('FECHA_CHAVE')
        return No('bloco', comandos)

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
        tipo = self.parse_tipo()
        nome = self.consumir('ID').lexema
        no = No(f'declaracao {nome} {tipo}')
        if self.atual().tipo == 'ATRIBUI':
            self.consumir('ATRIBUI')
            no.filhos.append(self.parse_ou())
        self.consumir('PONTO_VIRGULA')
        return no

    def parse_atribuicao(self):
        nome = self.consumir('ID').lexema
        self.consumir('ATRIBUI')
        expr = self.parse_ou()
        self.consumir('PONTO_VIRGULA')
        return No(f'atribuicao {nome}', [expr])

    def parse_se(self):
        self.consumir('SE')
        self.consumir('ABRE_PAR')
        cond = self.parse_ou()
        self.consumir('FECHA_PAR')
        entao = self.parse_bloco()
        if self.atual().tipo == 'SENAO':
            self.consumir('SENAO')
            senao = self.parse_bloco()
            return No('se', [cond, entao, senao])
        return No('se', [cond, entao])

    def parse_enquanto(self):
        self.consumir('ENQUANTO')
        self.consumir('ABRE_PAR')
        cond = self.parse_ou()
        self.consumir('FECHA_PAR')
        bloco = self.parse_bloco()
        return No('enquanto', [cond, bloco])

    def parse_escreva(self):
        self.consumir('ESCREVA')
        self.consumir('ABRE_PAR')
        expr = self.parse_ou()
        self.consumir('FECHA_PAR')
        self.consumir('PONTO_VIRGULA')
        return No('escreva', [expr])

    def parse_retorne(self):
        self.consumir('RETORNE')
        if self.atual().tipo == 'PONTO_VIRGULA':
            self.consumir('PONTO_VIRGULA')
            return No('retorne')
        expr = self.parse_ou()
        self.consumir('PONTO_VIRGULA')
        return No('retorne', [expr])

    def parse_chamada_comando(self):
        nome = self.consumir('ID').lexema
        args = self.parse_argumentos()
        self.consumir('PONTO_VIRGULA')
        return No(f'chamada {nome}', args)

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
            self.consumir('OU')
            expr = No('binario ou', [expr, self.parse_e()])
        return expr

    def parse_e(self):
        expr = self.parse_igualdade()
        while self.atual().tipo == 'E':
            self.consumir('E')
            expr = No('binario e', [expr, self.parse_igualdade()])
        return expr

    def parse_igualdade(self):
        expr = self.parse_relacional()
        while self.atual().tipo in ('IGUAL', 'DIFERENTE'):
            op = self.atual().tipo
            self.consumir(op)
            expr = No(f'binario {OPERADORES[op]}', [expr, self.parse_relacional()])
        return expr

    def parse_relacional(self):
        expr = self.parse_soma()
        while self.atual().tipo in ('MENOR', 'MENOR_IGUAL', 'MAIOR', 'MAIOR_IGUAL'):
            op = self.atual().tipo
            self.consumir(op)
            expr = No(f'binario {OPERADORES[op]}', [expr, self.parse_soma()])
        return expr

    def parse_soma(self):
        expr = self.parse_multiplicacao()
        while self.atual().tipo in ('MAIS', 'MENOS'):
            op = self.atual().tipo
            self.consumir(op)
            expr = No(f'binario {OPERADORES[op]}', [expr, self.parse_multiplicacao()])
        return expr

    def parse_multiplicacao(self):
        expr = self.parse_unario()
        while self.atual().tipo in ('VEZES', 'DIVIDE', 'RESTO'):
            op = self.atual().tipo
            self.consumir(op)
            expr = No(f'binario {OPERADORES[op]}', [expr, self.parse_unario()])
        return expr

    def parse_unario(self):
        if self.atual().tipo == 'NAO':
            self.consumir('NAO')
            return No('unario nao', [self.parse_unario()])
        if self.atual().tipo == 'MENOS':
            self.consumir('MENOS')
            return No('unario -', [self.parse_unario()])
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
            return No(f'literal {tipo} {valor}')

        if tok.tipo == 'ID':
            nome = self.consumir('ID').lexema
            if self.atual().tipo == 'ABRE_PAR':
                args = self.parse_argumentos()
                return No(f'chamada {nome}', args)
            return No(f'variavel {nome}')

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
