# Minha pequena linguagem

Trabalho semestral de **Compiladores** — Ciência da Computação, UNISAGRADO.
Prof. Luiz Ricardo Mantovani da Silva · 2026-2

Cada grupo escreve um **compilador completo** para a MPL, uma linguagem
pequena de palavras-chave em português. O compilador de vocês vai ler um
programa em `.mpl`, atravessar as quatro fases da disciplina e produzir um
arquivo que **roda de verdade** numa máquina virtual que vocês também vão
escrever.

No fim do semestre vocês executam um programa escrito por vocês, numa
linguagem compilada por vocês.

---

## Comece por aqui

```bash
git clone https://github.com/LuizRMSilva1973/compiladores-lab.git
cd compiladores-lab
```

```bash
make verificar E=1
```

Vai dar vermelho — é para dar. O esqueleto responde à linha de comando mas
ainda não tem nenhuma fase escrita. O vermelho é o seu ponto de partida, e
ele vai virando verde conforme vocês preenchem `mplc/`.

Não precisa instalar nada além do Python 3. Se o notebook de vocês der
trabalho, o [Google Cloud Shell](https://shell.cloud.google.com) já vem com
Python 3.12, Java 21 e git — e é o mesmo ambiente da correção.

---

## Os três documentos que mandam

| Arquivo | O que decide |
|---|---|
| [LINGUAGEM.md](LINGUAGEM.md) | **o que** o compilador aceita: a sintaxe e as regras de tipo da MPL |
| [CONTRATOS.md](CONTRATOS.md) | **como** ele se comunica: a linha de comando e o formato de cada despejo |
| [entregas/](entregas/) | o enunciado de cada entrega, com o que vale nota |

Quando a sua intuição discordar de um deles, é o arquivo que vale. Se o
arquivo estiver errado, me procurem — já aconteceu de eu escrever um exemplo
errado no contrato e só descobrir rodando.

---

## As entregas

| # | Entrega | Turma A (quarta) | Turma B (segunda) | Vale |
|---|---|---|---|---|
| [E1](entregas/E1.md) | Analisador léxico | 02/09 | 31/08 | 0,8 |
| [E2](entregas/E2.md) | Analisador sintático e árvore | 30/09 | 28/09 | 1,2 |
| [E3](entregas/E3.md) | Tabela de símbolos e tipos | 28/10 | 26/10 | 1,2 |
| [E4](entregas/E4.md) | Código intermediário, geração e VM | 18/11 | 16/11 | 1,8 |
| [Apres.](entregas/APRESENTACAO.md) | Demonstração e defesa | 25/11 | 23/11 | 1,0 |

São **quatro entregas sobre o mesmo compilador**, não quatro trabalhos. O que
vocês escreverem na E1 continua rodando na E4 — e o verificador da E4 confere
tudo o que veio antes. Deixar a E1 pela metade custa caro em novembro.

---

## Regras do jogo

**A entrega é o repositório, nunca a máquina de vocês.** A correção clona o
repositório numa máquina limpa e roda `make verificar E=n`. Se não passar
lá, não conta como entregue. Testem antes de entregar — de preferência na
Cloud Shell, que é o ambiente da correção.

**Grupos de até 3.** O mesmo grupo do começo ao fim. Mudança de grupo só até
a E1.

**Gerador de parser proibido nas Entregas 1 e 2.** ANTLR, PLY, yacc, lark e
parentes escondem exatamente a parte que está sendo ensinada. Da E3 em diante
o assunto é outro, e aí não faz diferença. Na apresentação vocês podem — e
devem — comparar o parser de vocês com o que um gerador produziria.

**A linguagem de implementação é de vocês, entre as que o ambiente da correção
já tem:** Python 3.12, Java 21, C e C++ (gcc 13), Ruby 3.2 ou PHP 8.3. O
verificador não olha para dentro — ele roda `./compilar` e `./executar` e
compara o que sai. O esqueleto em `mplc/` é Python porque é o caminho mais
curto, mas ninguém é obrigado a usá-lo.

A lista existe por um motivo prático: a correção roda numa Cloud Shell limpa, e
o que não estiver lá não roda. Querem outra linguagem? Falem comigo **antes** de
começar — o critério é ela existir no ambiente sem instalação. Em nenhum caso
dependam de biblioteca externa: só a biblioteca padrão.

**Escrever o compilador é a tarefa.** Usar IA para explicar um conceito,
revisar uma mensagem de erro ou entender um trecho é bem-vindo, e eu faço
isso também. Entregar um compilador que vocês não sabem alterar é outra
coisa — e a apresentação foi desenhada para separar os dois casos: cada grupo
recebe **uma alteração pequena na linguagem, na hora, com 10 minutos para
fazer**. Quem escreveu o compilador faz. Não é desconfiança; é o formato.

---

## O verificador

```bash
make verificar E=2      # confere a Entrega 2 e, junto, a 1
make verificar          # confere as quatro
make evidencias E=2     # grava evidencias/verificacao-2.txt, que vai na entrega
```

**Antes de entregar, rodem `make prova`.** Ele clona o repositório de vocês num
diretório limpo e verifica lá — que é exatamente o que a correção faz. É o
teste que pega o defeito mais comum de todos, e que não tem nada a ver com
compiladores: *funciona aqui e não no clone*. Arquivo esquecido fora do commit,
caminho absoluto, passo de compilação que ninguém roda. Vale para qualquer
linguagem, e é a única prova que realmente antecipa a correção.

Ele não lê o código de vocês. Ele roda o compilador e compara a saída com um
corpus de **10 programas válidos**, **26 programas que precisam ser
recusados na compilação** e **3 que precisam falhar na execução** — com a
fase e a linha do erro conferidas.

Os programas recusados são metade da nota escondida do trabalho. Um
compilador que aceita tudo passa em todos os testes positivos e não vale
nada: é por isso que o corpus tem mais programas errados do que certos.

**A correção usa um segundo corpus, que vocês não têm.** Mesma linguagem,
mesmas regras, programas diferentes. Um compilador de verdade passa nos dois
sem que vocês precisem fazer nada; um programa que apenas reproduza as saídas
esperadas deste corpus passa aqui e reprova lá. Estou dizendo isto abertamente
para ninguém perder tempo pelo caminho errado.

---

## Como entregar

1. `git push` no repositório do grupo.
2. Abram a [página do trabalho](https://profluiz.mantovanitec.com/disciplinas/aulas/compiladores/trabalho.html).
3. No formulário do fim da página: escolham a entrega, identifiquem os
   integrantes (nome, RA e e-mail), colem a URL do repositório e anexem o
   `evidencias/verificacao-N.txt`.
4. Cada integrante recebe uma cópia por e-mail. **Guardem esse e-mail**: é o
   comprovante.

## Tabela de tokens da Entrega 1

A análise léxica reconhece os seguintes grupos de token, em ordem de prioridade (operadores compostos antes dos simples):

| Categoria | Tokens | Reconhecimento |
|---|---|---|
| Palavras reservadas | `funcao`, `retorne`, `se`, `senao`, `enquanto`, `escreva`, `inteiro`, `real`, `logico`, `texto`, `vazio`, `verdadeiro`, `falso`, `e`, `ou`, `nao` | identificadores exatos do MPL |
| Identificador | `ID` | `[A-Za-z_][A-Za-z0-9_]*` |
| Literal inteiro | `INTEIRO` | `[0-9]+` |
| Literal real | `REAL` | `[0-9]+\.[0-9]+` (obrigatório dos dois lados) |
| Literal lógico | `LOGICO` | `verdadeiro` ou `falso` |
| Literal texto | `TEXTO` | `"(\\[nt\"\\]|[^\"\\\r\n])*"` |
| Comentários | `// ...` e `/* ... */` | ignorados, exceto erro se o bloco não fechar |
| Operadores compostos | `==`, `!=`, `<=`, `>=` | lidos antes dos simples |
| Operadores simples | `+`, `-`, `*`, `/`, `%`, `<`, `>`, `=` | mapeados para `MAIS`, `MENOS`, `VEZES`, `DIVIDE`, `RESTO`, `MENOR`, `MAIOR`, `ATRIBUI` |
| Delimitadores | `(`, `)`, `{`, `}`, `,`, `;` | `ABRE_PAR`, `FECHA_PAR`, `ABRE_CHAVE`, `FECHA_CHAVE`, `VIRGULA`, `PONTO_VIRGULA` |
| Espaços | ignorados | espaço, tabulação, `\r`, `\n` |

Regras importantes da implementação:

- `<=` e `>=` são testados antes de `<` e `>`.
- `==` e `!=` são testados antes de `=` e `!`.
- qualquer escape fora de `\n`, `\t`, `\"` e `\\` é erro léxico.
- `3.` e `.5` são erro léxico.
- `/* ... */` não aninha; o primeiro `*/` fecha e um bloco sem fechamento dispara erro na linha/coluna de abertura.
- o último token é sempre `FIM_ARQUIVO`, na linha seguinte ao fim do arquivo (ou na coluna 1 depois do último caractere, se não houver quebra de linha).

## Gramática implementada da Entrega 2

A gramática usada no parser recursivo descendente da Entrega 2 é a seguinte, em EBNF:

```ebnf
programa        ::= { funcao }
funcao          ::= "funcao" tipo ID "(" [ parametros ] ")" bloco
parametros      ::= parametro { "," parametro }
parametro       ::= tipo ID
bloco           ::= "{" { comando } "}"
comando         ::= declaracao
                 | atribuicao
                 | condicional
                 | repeticao
                 | escrita
                 | retorno
                 | chamada ";"

declaracao      ::= tipo ID [ "=" expressao ] ";"
atribuicao      ::= ID "=" expressao ";"
condicional     ::= "se" "(" expressao ")" bloco [ "senao" bloco ]
repeticao       ::= "enquanto" "(" expressao ")" bloco
escrita         ::= "escreva" "(" expressao ")" ";"
retorno         ::= "retorne" [ expressao ] ";"
chamada         ::= ID "(" [ expressao { "," expressao } ] ")"

tipo            ::= "inteiro" | "real" | "logico" | "texto" | "vazio"
expressao       ::= ou
ou              ::= e { "ou" e }
e               ::= igualdade { "e" igualdade }
igualdade       ::= relacional { ( "==" | "!=" ) relacional }
relacional       ::= soma { ( "<" | "<=" | ">" | ">=" ) soma }
soma            ::= produto { ( "+" | "-" ) produto }
produto         ::= unario { ( "*" | "/" | "%" ) unario }
unario          ::= [ "nao" | "-" ] unario
                 | primario
primario        ::= literal
                 | ID [ "(" [ expressao { "," expressao } ] ")" ]
                 | "(" expressao ")"
literal         ::= INTEIRO | REAL | LOGICO | TEXTO
```

A precedência está codificada por camadas recursivas na própria gramática: `ou` chama `e`, `e` chama `igualdade`, e assim por diante até `primario`. Cada nível resolve primeiro os operadores mais fortes e empilha os mais fracos acima deles, de modo que a árvore sintática sempre coloca o operador de menor precedência na raiz e os de maior precedência abaixo, como em `1 + 2 * 3` sendo `binario +` com filho `binario *`.